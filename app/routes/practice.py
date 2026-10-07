"""Practice links for a room. Delete this file and its one line in app/main.py
and they are gone; nothing else in the app knows they exist.

A link that goes to a room is a lot of people on one server. If they all signed
in as the same seeded person they would share one case: one picks "Learn" and
everybody's screen changes, and the first to set a PIN locks the rest out. A PIN
somebody else set is not a PIN, so each visitor gets a case of their own.

Three links, one per surface, and each opens on that visitor's own practice
case, the same case in all three:

  /try/tablet   the tablet's sign-in with a fresh 28 number already in the box
  /try/phone    the helper's phone with that case's code already in the box
  /try/desk     the coordinator's page for that case

Each one only sets a case up and redirects. The real routes (/signin, /helper,
/staff) are untouched and know nothing about this, so what is demonstrated is
the product and not a mode of it. A case made here starts with the three sample
reports and a first name, so "My reports" has something to read and the helper's
page has somebody to be helping. The browser remembers which case is its own for
twelve hours, so a reload does not hand out a new number.
"""

from __future__ import annotations

import secrets
import string
from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.identifiers import InvalidIdentifier, is_self_service, parse
from app.routes.access import _open_a_case
from app.store import STATE, find_account, mutate, put_sample_reports

router = APIRouter(prefix="/try")

COOKIE = "bridge_practice"
MAX_AGE = 12 * 60 * 60


def _fresh_number() -> str:
    """A 28 number nobody has used, in the form a person would type.

    The letter is random as well as the digits, so two visitors loading a link in
    the same second are very unlikely to be handed the same number.
    """
    taken = {a["login_key"] for a in STATE.accounts.values()}
    while True:
        letter = secrets.choice(string.ascii_uppercase)
        digits = f"{secrets.randbelow(10000):04d}"
        if f"28{letter}{digits}" not in taken:
            return f"28-{letter}-{digits}"


def _number(request: Request) -> str:
    """This visitor's practice number: the one they already have, else a new one."""
    try:
        parsed = parse(request.cookies.get(COOKIE, ""))
    except InvalidIdentifier:
        parsed = None
    if parsed is not None and is_self_service(parsed):
        return parsed.display
    return _fresh_number()


def _case(request: Request):
    """The visitor's practice case, made the first time. Returns (display, client_id)."""
    number = _number(request)
    parsed = parse(number)
    account = find_account("inside", parsed.normalized)
    if account is None:
        account = _open_a_case(parsed)
        client = STATE.clients[account.subject_id]
        with mutate():
            client.first_name = client.first_name or "Sam"
            put_sample_reports(
                date.today(), client.id, client.display_name,
                f"XXX-XX-{client.din[-4:]}", "1991-03-02",
                [f"{client.facility or 'New York'}, New York"],
            )
    return number, account.subject_id


def _helper_code(client_id: str) -> str:
    for raw in STATE.accounts.values():
        if raw["role"] == "family" and raw["subject_id"] == client_id:
            return raw["login_key"]
    raise LookupError(client_id)


def _go(number: str, target: str) -> RedirectResponse:
    """Redirect, and remember which case is this browser's. The number is the
    one the case was just made for, never a second pick."""
    response = RedirectResponse(target, status_code=303)
    response.set_cookie(
        COOKIE, parse(number).normalized, max_age=MAX_AGE,
        samesite="lax", path="/",
    )
    return response


@router.get("/tablet")
def tablet(request: Request):
    number, _ = _case(request)
    return _go(number, f"/signin?identifier={number}")


@router.get("/phone")
def phone(request: Request):
    number, client_id = _case(request)
    return _go(number, f"/helper?code={_helper_code(client_id)}")


@router.get("/desk")
def desk(request: Request):
    number, client_id = _case(request)
    return _go(number, f"/staff/{client_id}")
