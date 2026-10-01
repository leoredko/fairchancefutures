"""The helper's phone.

Two gates here too, and a third that is specific to this surface: a signed,
scoped, unexpired, unrevoked authorization. Signing in with the code from the
letter proves which case you are here about. It does not grant you anything.
The grant is the form, and the form is checked on every request, so a client
who cancels from the tablet cuts access off at the next tap.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from app.authorization import (
    POA_TERM_DAYS,
    Scope,
    default_helper_authorization,
    require_scope,
)
from app import mailing
from app.deps import templates
from app.report import Source, from_scan, mask_ssn, parse_accounts
from app.session import require_role
from app.store import (
    drafts_for,
    get_authorization,
    mutate,
    put_authorization,
    put_report,
    stored_reports,
)
from app.surfaces import Capability, Surface, require

router = APIRouter(prefix="/family")


def _homecoming(iso: str) -> str:
    """Plain words, not a countdown. 'in about four months' is how a person
    would say it."""
    days = (date.fromisoformat(iso) - date.today()).days
    if days <= 0:
        return "He is home already"
    if days < 14:
        return f"He comes home in about {days} days"
    if days < 45:
        return "He comes home in about a month"
    return f"He comes home in about {round(days / 30)} months"


@router.get("", response_class=HTMLResponse)
def landing(request: Request):
    caller = require_role(request, "family")
    client = caller.client
    auth = get_authorization(client.id)
    if auth is not None and auth.is_live():
        return RedirectResponse("/family/task", status_code=303)

    return templates.TemplateResponse(
        request, "family/invitation.html",
        {"client": client,
         "homecoming": _homecoming(client.release_date),
         "term_days": POA_TERM_DAYS,
         "suggested_name": client.helper_name,
         "scopes": [
             "Receive his mail",
             "Send his reports in, however is easiest for you",
             "Mail a dispute letter we print for you",
             "Be contacted by his counselor",
         ]},
    )


@router.post("/accept")
def accept(request: Request, helper_name: str = Form(...)):
    """The signed form. This is the moment standing is created, and the only one."""
    caller = require_role(request, "family")
    client = caller.client
    auth = default_helper_authorization(client.id, helper_name.strip()[:40])
    with mutate():
        put_authorization(auth)
        client.helper_name = auth.helper_name
        client.timeline.append({
            "text": f"{auth.helper_name} agreed to help",
            "actor": "Your person outside",
            "on": date.today().strftime("%B %-d"),
            "done": True,
        })
    return RedirectResponse("/family/task", status_code=303)


@router.get("/task", response_class=HTMLResponse)
def task(request: Request):
    caller = require_role(request, "family")
    client = caller.client
    auth = get_authorization(client.id)
    # No live grant means no task surface at all. Back to the invitation.
    if auth is None or not auth.is_live():
        return RedirectResponse("/family", status_code=303)
    require_scope(auth, Scope.BE_CONTACTED_BY_STAFF)

    # One task on screen. Never two. A dispute letter waiting to be posted
    # comes first: the bureau's 30 days start when it receives the letter.
    waiting = _waiting_letters(client)
    if waiting:
        current = {
            "headline": f"Print the dispute letters, have {client.first_name} "
                        "sign them, and send each one certified.",
            "detail": f"{len(waiting)} letter{'s' if len(waiting) != 1 else ''} "
                      "approved, one envelope for each bureau. Keep every "
                      "receipt. If you cannot, the letters can go to Ms. "
                      "Reyes instead.",
            "action_url": "/family/disputes",
            "action_label": "Open the letters",
            "skip_url": None,
            "skip_label": "",
        }
    elif not client.report_pages and not client.family_task.get("done"):
        current = {
            "headline": client.family_task.get(
                "headline", "Print the request, have "
                f"{client.first_name} sign it, mail it."),
            "detail": client.family_task.get(
                "detail", "We filled in everything except the signature. The "
                          "envelope prints addressed. Send it certified, "
                          "with a return receipt, so you can prove it went."),
            "action_url": "/family/packet",
            "action_label": "Print the packet",
            "skip_url": "/family/mailed",
            "skip_label": "I mailed it",
        }
    elif not stored_reports(client.id):
        current = {
            "headline": "When the reports arrive, send them in.",
            "detail": "Three ways, and any of them works. The easiest is a PDF "
                      "if you have one.",
            "action_url": "/family/report",
            "action_label": "Send the reports in",
            "skip_url": None,
            "skip_label": "",
        }
    else:
        current = None

    done = [e for e in client.timeline if e.get("done")][:3]
    return templates.TemplateResponse(
        request, "family/task.html",
        {"client": client, "auth": auth, "task": current, "done": done},
    )


def _record_mailing(request, tracking_number: str):
    caller = require_role(request, "family")
    client = caller.client
    auth = get_authorization(client.id)
    require_scope(auth, Scope.MAIL_DISPUTE_LETTER)
    number = mailing.clean_tracking_number(tracking_number)
    with mutate():
        client.family_task["done"] = True
        mailing.record(client, what=mailing.REPORT_REQUEST,
                       mailed_by=auth.helper_name, tracking_number=number)
        client.timeline.append({
            "text": (f"Request mailed to the bureaus, certified, tracking "
                     f"number {number}" if number
                     else "Request mailed to the bureaus"),
            "actor": auth.helper_name, "on": date.today().strftime("%B %-d"),
            "done": True,
        })
    return client


@router.post("/task/done")
def task_done(request: Request):
    """Mailed, with no tracking number. Kept for a helper who already posted it."""
    _record_mailing(request, "")
    return RedirectResponse("/family/task", status_code=303)


@router.get("/mailed", response_class=HTMLResponse)
def mailed_form(request: Request, bad: int = 0):
    caller = require_role(request, "family")
    auth = get_authorization(caller.client.id)
    require_scope(auth, Scope.MAIL_DISPUTE_LETTER)
    return templates.TemplateResponse(
        request, "family/mailed.html",
        {"client": caller.client, "auth": auth, "bad": bool(bad),
         "rules": mailing.citations()},
    )


@router.post("/mailed")
def mailed(request: Request, tracking_number: str = Form("")):
    """Record the mailing, and the tracking number if there is one.

    A number that cannot be one sends the helper back to the form rather than
    saving a typo as proof: a wrong number is worse than none, because it looks
    like evidence.
    """
    if tracking_number.strip() and not mailing.clean_tracking_number(tracking_number):
        return RedirectResponse("/family/mailed?bad=1", status_code=303)
    _record_mailing(request, tracking_number)
    return RedirectResponse("/family/task", status_code=303)


def _waiting_letters(client) -> list[dict]:
    """Approved dispute letters not yet in the post."""
    return [l for l in mailing.letters_for_desk(client, drafts_for(client.id))
            if l["stage"] != "mailed"]


@router.get("/disputes", response_class=HTMLResponse)
def disputes(request: Request, bad: int = 0):
    """The approved dispute letters, to print, sign and post one by one.

    Three letters for one item, three envelopes, three receipts. Only approved
    letters are here: a draft the coordinator has not approved is not a letter
    yet.
    """
    caller = require_role(request, "family")
    require(Surface.FAMILY, Capability.PRINT_AND_POST)
    client = caller.client
    auth = get_authorization(client.id)
    require_scope(auth, Scope.MAIL_DISPUTE_LETTER)
    rows = mailing.letters_for_desk(client, drafts_for(client.id))
    return templates.TemplateResponse(
        request, "family/disputes.html",
        {"client": client, "auth": auth, "letters": rows, "bad": bool(bad),
         "today": date.today().isoformat(), "rules": mailing.citations()},
    )


@router.post("/disputes/{draft_id}/mailed")
def dispute_mailed(request: Request, draft_id: str, on_date: str = Form(""),
                   tracking_number: str = Form("")):
    caller = require_role(request, "family")
    require(Surface.FAMILY, Capability.PRINT_AND_POST)
    client = caller.client
    auth = get_authorization(client.id)
    require_scope(auth, Scope.MAIL_DISPUTE_LETTER)
    row = next((d for d in drafts_for(client.id)
                if d["id"] == draft_id and d.get("kind") == "dispute"
                and d.get("approved_on")), None)
    day = mailing.clean_day(on_date)
    bad_number = (tracking_number.strip()
                  and not mailing.clean_tracking_number(tracking_number))
    if row is None or not day or bad_number:
        return RedirectResponse("/family/disputes?bad=1", status_code=303)
    number = mailing.clean_tracking_number(tracking_number)
    with mutate():
        mailing.mark_mailed(client, draft_id=draft_id, bureau=row["bureau"],
                            mailed_by=auth.helper_name,
                            tracking_number=number, on=day)
        client.timeline.append({
            "text": (f"Your dispute letter to {row['bureau']} was mailed, "
                     f"certified, tracking number {number}" if number
                     else f"Your dispute letter to {row['bureau']} was mailed"),
            "actor": auth.helper_name,
            "on": date.fromisoformat(day).strftime("%B %-d"), "done": True,
        })
    return RedirectResponse("/family/disputes", status_code=303)


@router.get("/packet", response_class=HTMLResponse)
def packet(request: Request):
    """The request letter, ready to print. Signature by hand, SSN by hand."""
    from app.letters import draft_report_request

    caller = require_role(request, "family")
    client = caller.client
    auth = get_authorization(client.id)
    require_scope(auth, Scope.RECEIVE_MAIL)
    draft = draft_report_request(
        client_id=client.id,
        client_name=client.display_name,
        delivery_address=f"c/o {auth.helper_name}, on file with the program",
        identification=client.din,
        id_label="DIN",
        facility=client.facility,
    )
    return templates.TemplateResponse(
        request, "family/packet.html",
        {"client": client, "draft": draft, "rules": mailing.citations()},
    )

# --------------------------------------------------------------------------
# getting the report in
# --------------------------------------------------------------------------
#
# Three routes, offered in this order for a reason that is about cost to the
# helper and accuracy to the case, not about what is impressive.
#
#   PDF      one tap, the whole document, nothing lost. If a helper pulled the
#            report online they already have this.
#   Typed    exact, and twenty minutes of somebody's evening. It is the route
#            for a paper report and a helper who would rather type than fight
#            a scanner app.
#   Photo    last, and honestly labelled. Nothing in this build reads data out
#            of a picture. A photograph means a human transcribes it later,
#            which is the coordinator, which is slower for everyone.
#
# None of the three writes a confirmed record. Everything arriving from outside
# waits for a coordinator, because these fields become a dispute letter and a
# letter about the wrong account number is worse than no letter.


@router.get("/report", response_class=HTMLResponse)
def send_report_form(request: Request, how: str = ""):
    caller = require_role(request, "family")
    require(Surface.FAMILY, Capability.UPLOAD_FILE)
    client = caller.client
    require_scope(get_authorization(client.id), Scope.SUBMIT_REPORT_IMAGES)
    return templates.TemplateResponse(
        request, "family/send_report.html",
        {"client": client, "how": how,
         "sent": stored_reports(client.id)},
    )


@router.post("/report")
async def send_report(
    request: Request,
    how: str = Form("pdf"),
    bureau: str = Form(""),
    consumer_name: str = Form(""),
    accounts: str = Form(""),
    ssn_on_document: str = Form(""),
    pulled_on: str = Form(""),
    files: list[UploadFile] = None,
):
    """Take it however it comes, and be honest about what happens next."""
    caller = require_role(request, "family")
    require(Surface.FAMILY, Capability.UPLOAD_FILE)
    client = caller.client
    auth = get_authorization(client.id)
    require_scope(auth, Scope.SUBMIT_REPORT_IMAGES)

    source = {"pdf": Source.PDF, "typed": Source.TYPED,
              "photo": Source.PHOTO}.get(how, Source.PDF)

    # Filenames and a page count, never the bytes. This build does not hold a
    # picture of anybody's credit report on disk, which is a smaller promise
    # than it sounds and the only one it can actually keep.
    names = [f.filename for f in (files or []) if f and f.filename]
    pages = [f"Page {i}" for i, _ in enumerate(names, start=1)]

    report = from_scan(
        client_id=client.id,
        bureau=bureau or "Not stated on the copy",
        consumer_name=consumer_name or client.display_name,
        scanned_by=auth.helper_name,
        pulled_on=pulled_on,
        accounts=parse_accounts(accounts) if source is Source.TYPED else [],
        ssn_on_document=mask_ssn(ssn_on_document),
        source=source,
        pages=pages,
    )

    with mutate():
        put_report(report)
        for page in pages:
            client.report_pages.append(page)
        client.timeline.append({
            "text": {
                Source.PDF: "The report came in as a PDF",
                Source.TYPED: "They typed your report in by hand",
                Source.PHOTO: "They photographed your report and sent it in",
            }[source],
            "actor": auth.helper_name,
            "on": date.today().strftime("%B %-d"),
            "done": True,
        })

    return RedirectResponse("/family/report?how=done", status_code=303)
