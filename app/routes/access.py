"""Signing in, and staying signed in.

Three doors, because the three roles arrive with different things in hand. A
person inside has a DIN or a NYSID. A helper has a code printed on the letter
that came in the mail. A counselor has a staff ID.

Nobody is issued a PIN. Everybody sets their own at first use, and a counselor
resetting a PIN clears it rather than choosing a new one, so the only person
who ever knows a client's PIN is the client.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.auth import (
    COOKIE_NAME,
    PIN_LENGTH,
    AuthError,
    Session,
    authenticate,
    enroll,
    issue,
)
from app.deps import templates
from app.identifiers import InvalidIdentifier, is_self_service, parse
from app.store import STATE, find_account, mutate, put_account

router = APIRouter()

HOME = {"inside": "/inside", "family": "/family", "staff": "/staff"}


def _start(account, response: RedirectResponse) -> RedirectResponse:
    session = Session(
        account_id=account.account_id,
        role=account.role,
        subject_id=account.subject_id,
    )
    response.set_cookie(
        COOKIE_NAME, issue(session),
        httponly=True, samesite="lax", path="/",
        # secure would be set behind TLS in a real deployment; left off so the
        # demo works over plain http on a tablet on a local network.
    )
    return response


# --------------------------------------------------------------------------
# inside
# --------------------------------------------------------------------------

@router.get("/signin", response_class=HTMLResponse)
def signin(request: Request, error: str | None = None):
    return templates.TemplateResponse(
        request, "access/signin.html", {"error": error},
    )


@router.post("/signin", response_class=HTMLResponse)
def signin_identify(request: Request, identifier: str = Form("")):
    """Step one: which number. Step two happens on the next screen.

    Two screens instead of one because a six-digit PIN typed on the same screen
    as the number you just read off a printed sheet is how people mistype both.
    """
    try:
        parsed = parse(identifier)
    except InvalidIdentifier as exc:
        return templates.TemplateResponse(
            request, "access/signin.html",
            {"error": str(exc), "identifier": identifier}, status_code=400,
        )

    account = find_account("inside", parsed.normalized)
    if account is None:
        if is_self_service(parsed):
            account = _open_a_case(parsed)
        else:
            return templates.TemplateResponse(
                request, "access/signin.html",
                {"error": f"No record here for {parsed.display}. Check the "
                          f"number, or ask your counselor to add you.",
                 "identifier": identifier},
                status_code=404,
            )

    page = "access/enroll.html" if not account.enrolled else "access/pin.html"
    return templates.TemplateResponse(
        request, page,
        {"account": account, "identifier": parsed.display,
         "normalized": parsed.normalized, "label": parsed.label,
         "pin_length": PIN_LENGTH, "role": "inside"},
    )


@router.post("/signin/pin")
def signin_pin(
    request: Request, normalized: str = Form(...), pin: str = Form("")
):
    account = find_account("inside", normalized)
    if account is None:
        return RedirectResponse("/signin", status_code=303)

    try:
        authenticate(account, pin)
    except AuthError as exc:
        with mutate():
            put_account(account)
        return _retry(request, "inside", account, normalized, str(exc))

    with mutate():
        put_account(account)
    return _start(account, RedirectResponse("/inside", status_code=303))


@router.post("/signin/enroll")
def signin_enroll(
    request: Request, normalized: str = Form(...), pin: str = Form(""), confirm: str = Form("")
):
    account = find_account("inside", normalized)
    if account is None:
        return RedirectResponse("/signin", status_code=303)

    try:
        enroll(account, pin, confirm)
    except AuthError as exc:
        return _retry(request, "inside", account, normalized, str(exc), enrolling=True)

    with mutate():
        # A client can sign in with either number, so both accounts for that
        # person take the same PIN. Otherwise a client who enrolled with their
        # DIN would be told to enrol again when they typed their NYSID.
        for raw in list(STATE.accounts.values()):
            if raw["role"] == "inside" and raw["subject_id"] == account.subject_id:
                raw["pin_hash"] = account.pin_hash
                raw["failed_attempts"] = 0
                raw["locked_until"] = None
    return _start(account, RedirectResponse("/inside", status_code=303))


def _retry(request: Request, role: str, account, normalized: str, error: str,
           *, enrolling: bool = False):
    """Back to the PIN screen with the reason, keeping the number they typed."""
    page = "access/enroll.html" if enrolling else "access/pin.html"
    return templates.TemplateResponse(
        request, page,
        {"account": account, "normalized": normalized, "error": error,
         "identifier": normalized, "label": "number", "pin_length": PIN_LENGTH,
         "role": role},
        status_code=400,
    )


def _open_a_case(parsed):
    """Create a case on the spot for a number in the self-service range.

    The number is the only thing typed. Everything already attached to it is
    looked up, because asking somebody to retype their own release date from
    memory on a metered tablet is asking them to do a computer's job.

    This used to invent a release date of today plus 180 days and leave the
    facility blank. Both were fabrications, and both then drove real things:
    the work queue's ordering, the count of quarterly reviews left, and the
    120-day document deadline.
    """
    from datetime import date

    from app.auth import Account
    from app.doccs import simulated_lookup
    from app.intake import helper_code
    from app.store import Client, put_account

    client_id = f"din-{parsed.normalized.lower()}"
    with mutate():
        if client_id not in STATE.clients:
            record = simulated_lookup(parsed.normalized)
            planning = record.planning_date
            days = ((date.fromisoformat(planning) - date.today()).days
                    if planning else 0)
            STATE.clients[client_id] = Client(
                id=client_id,
                display_name=parsed.display,
                first_name="",
                din=parsed.normalized,
                facility=record.housing_facility,
                release_date=planning,
                release_date_source=record.planning_date_label,
                doccs_record=record.as_dict(),
                clock=(f"Releases in {days} days" if days >= 0
                       else f"Home {abs(days)} days ago"),
                clock_sort=days,
                consent_recorded_on=date.today().isoformat(),
                plan_step="Intake not finished yet.",
                needs="Opened from the tablet, intake not finished",
            )
            put_account(Account(
                account_id=f"inside-{client_id}", role="inside",
                subject_id=client_id, login_key=parsed.normalized,
                display_name=parsed.display,
            ))
            put_account(Account(
                account_id=f"family-{client_id}", role="family",
                subject_id=client_id,
                login_key=helper_code(
                    {a["login_key"] for a in STATE.accounts.values()}),
            ))
    return find_account("inside", parsed.normalized)


# --------------------------------------------------------------------------
# family
# --------------------------------------------------------------------------

@router.get("/helper", response_class=HTMLResponse)
def helper_signin(request: Request, error: str | None = None):
    return templates.TemplateResponse(request, "access/helper.html", {"error": error})


@router.post("/helper", response_class=HTMLResponse)
def helper_identify(request: Request, code: str = Form("")):
    account = find_account("family", (code or "").strip().upper())
    if account is None:
        return templates.TemplateResponse(
            request, "access/helper.html",
            {"error": "That code is not one of ours. It is printed on the "
                      "letter that came in the mail.", "code": code},
            status_code=404,
        )
    page = "access/enroll.html" if not account.enrolled else "access/pin.html"
    return templates.TemplateResponse(
        request, page,
        {"account": account, "identifier": account.login_key,
         "normalized": account.login_key, "label": "code",
         "pin_length": PIN_LENGTH, "role": "family"},
    )


@router.post("/helper/pin")
def helper_pin(
    request: Request, normalized: str = Form(...), pin: str = Form("")):
    account = find_account("family", normalized)
    if account is None:
        return RedirectResponse("/helper", status_code=303)
    try:
        authenticate(account, pin)
    except AuthError as exc:
        with mutate():
            put_account(account)
        return _retry(request, "family", account, normalized, str(exc))
    with mutate():
        put_account(account)
    return _start(account, RedirectResponse("/family", status_code=303))


@router.post("/helper/enroll")
def helper_enroll(
    request: Request, normalized: str = Form(...), pin: str = Form(""), confirm: str = Form("")
):
    account = find_account("family", normalized)
    if account is None:
        return RedirectResponse("/helper", status_code=303)
    try:
        enroll(account, pin, confirm)
    except AuthError as exc:
        return _retry(request, "family", account, normalized, str(exc), enrolling=True)
    with mutate():
        put_account(account)
    return _start(account, RedirectResponse("/family", status_code=303))


# --------------------------------------------------------------------------

@router.post("/signout")
@router.get("/signout")
def signout():
    """Big, always reachable, one tap. A tablet read in a common area needs a way out that
    nobody has to look for."""
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(COOKIE_NAME, path="/")
    return response
