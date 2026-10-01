"""Proof that something was sent, and where it is now.

Anything Bridge asks a person to mail goes certified, with a return receipt and
a tracking number, because the only defence against "we never got it" is a
record you did not write yourself. That is the default, recommended as strongly
as the product can say it, and it is a choice: it costs money and a person can
decline it.

Who pays depends on who posts it. A helper outside pays at the counter. A
person inside pays from their own account, and DOCCS will not advance the
money for certified service unless a statute or court rule requires it. Both
halves are in `app/sources.py` and the screens say so before anybody commits.

`lookup` is a stand-in. The real thing is live tracking from the major
carriers, and that integration is pending. USPS's own API, for one, needs a
registered application, an OAuth token and a separate access request, none of
which this build has. It is one function with a fixed return shape, so
replacing it changes nothing else. The status and the expected date it returns
are invented from the mailing date and are never real carrier data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

from app.sources import fact

# What kind of thing was mailed. A name for what it is, not for who sent it.
REPORT_REQUEST = "report_request"
DISPUTE_LETTER = "dispute_letter"

# Stand-in timings for the stub. Not a USPS service standard.
_STUB_TRANSIT_AFTER = 2
_STUB_DELIVERED_AFTER = 5

_TRACKING = re.compile(r"[A-Z0-9]{8,34}")


@dataclass(frozen=True)
class TrackingStatus:
    state: str            # accepted | transit | delivered
    expected_on: str      # ISO date, invented by the stub
    real: bool = False    # True only once the USPS API is behind `lookup`


def clean_tracking_number(raw: str) -> str:
    """Spaces and dashes removed, upper case, or "" for something that cannot
    be one. Receipts print the number in groups, so people type it in groups."""
    compact = re.sub(r"[\s\-]", "", raw or "").upper()
    return compact if _TRACKING.fullmatch(compact) else ""


def lookup(tracking_number: str, mailed_on: str,
           today: date | None = None) -> TrackingStatus | None:
    """Where a piece of mail is. STUB: replace with live carrier tracking."""
    if not tracking_number:
        return None
    today = today or date.today()
    sent = date.fromisoformat(mailed_on)
    age = (today - sent).days
    if age >= _STUB_DELIVERED_AFTER:
        state = "delivered"
    elif age >= _STUB_TRANSIT_AFTER:
        state = "transit"
    else:
        state = "accepted"
    expected = sent + timedelta(days=_STUB_DELIVERED_AFTER)
    return TrackingStatus(state=state, expected_on=expected.isoformat())


def record(client, *, what: str, mailed_by: str, tracking_number: str = "",
           today: date | None = None) -> dict:
    """Write one shipment onto the case. The caller holds `mutate()`."""
    shipment = {
        "what": what,
        "mailed_on": (today or date.today()).isoformat(),
        "mailed_by": mailed_by,
        "tracking_number": clean_tracking_number(tracking_number),
    }
    client.shipments.append(shipment)
    return shipment


def clean_day(raw: str, today: date | None = None) -> str:
    """The day something happened, as an ISO date, or "" when it cannot be one.

    Blank means today, because most people mark it the day it happens. A day
    in the future is refused: a mailing date is evidence, and a date that has
    not come yet is not.
    """
    today = today or date.today()
    if not (raw or "").strip():
        return today.isoformat()
    try:
        day = date.fromisoformat(raw.strip())
    except ValueError:
        return ""
    return day.isoformat() if day <= today else ""


def _letter(client, draft_id: str) -> dict | None:
    return next((s for s in client.shipments
                 if s.get("what") == DISPUTE_LETTER
                 and s.get("draft_id") == draft_id), None)


def letter_shipment(client, draft_id: str) -> dict | None:
    return _letter(client, draft_id)


def hand_in(client, *, draft_id: str, bureau: str, handed_to: str,
            on: str) -> dict:
    """The signed letter reached the coordinator's hands. Not mailed yet.

    A second step follows when the coordinator posts it and has the receipt,
    so the file can say where the letter was on every day between approval and
    the post office. Marking it twice changes nothing.
    """
    existing = _letter(client, draft_id)
    if existing:
        return existing
    shipment = {
        "what": DISPUTE_LETTER, "draft_id": draft_id, "bureau": bureau,
        "handed_on": on, "handed_to": handed_to,
        "mailed_on": "", "mailed_by": "", "tracking_number": "",
    }
    client.shipments.append(shipment)
    return shipment


def mark_mailed(client, *, draft_id: str, bureau: str, mailed_by: str,
                tracking_number: str, on: str) -> dict:
    """It went into the post. Straight from the helper, or after a hand-in."""
    shipment = _letter(client, draft_id)
    if shipment is None:
        shipment = {"what": DISPUTE_LETTER, "draft_id": draft_id,
                    "bureau": bureau, "handed_on": "", "handed_to": ""}
        client.shipments.append(shipment)
    shipment.update(mailed_on=on, mailed_by=mailed_by,
                    tracking_number=clean_tracking_number(tracking_number))
    return shipment


def letters_for_desk(client, drafts: list[dict]) -> list[dict]:
    """Each approved dispute letter and the stage it is at, for either desk.

    Stage is one of `approved` (nothing recorded yet), `with_coordinator`
    (handed in, not posted) or `mailed`.
    """
    rows = []
    for d in drafts:
        if d.get("kind") != "dispute" or not d.get("approved_on"):
            continue
        s = _letter(client, d["id"]) or {}
        stage = ("mailed" if s.get("mailed_on")
                 else "with_coordinator" if s.get("handed_on") else "approved")
        rows.append({"draft": d, "shipment": s, "stage": stage,
                     "status": lookup(s.get("tracking_number", ""),
                                      s["mailed_on"]) if s.get("mailed_on") else None})
    return rows


def shipments_for_screen(client, today: date | None = None) -> list[dict]:
    """Each shipment with its status attached, newest first."""
    rows = []
    for s in reversed(client.shipments):
        status = (lookup(s["tracking_number"], s["mailed_on"], today)
                  if s.get("mailed_on") else None)
        rows.append({**s, "status": status})
    return rows


def citations() -> list[str]:
    """The two DOCCS rules the advice rests on, for the screens that give it."""
    return [fact("certified_mail_is_at_own_expense").cite(),
            fact("special_handling_is_not_advanced").cite()]
