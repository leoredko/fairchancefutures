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

`lookup` is a stand-in. The real thing is the USPS Tracking API, which needs a
registered application, an OAuth token and its own access request, none of
which this build has. It is one function with a fixed return shape, so
replacing it changes nothing else. The status and the expected date it returns
are invented from the mailing date and are never real USPS data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

from app.sources import fact

# What kind of thing was mailed. A name for what it is, not for who sent it.
REPORT_REQUEST = "report_request"
DISPUTE_LETTERS = "dispute_letters"

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
    """Where a piece of mail is. STUB: replace with the USPS Tracking API."""
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


def shipments_for_screen(client, today: date | None = None) -> list[dict]:
    """Each shipment with its status attached, newest first."""
    rows = []
    for s in reversed(client.shipments):
        rows.append({**s, "status": lookup(s["tracking_number"], s["mailed_on"], today)})
    return rows


def citations() -> list[str]:
    """The two DOCCS rules the advice rests on, for the screens that give it."""
    return [fact("certified_mail_is_at_own_expense").cite(),
            fact("special_handling_is_not_advanced").cite()]
