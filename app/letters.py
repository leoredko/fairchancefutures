"""Letter drafting.

Every letter is assembled from a fixed template plus named facts. There is no
free generation here, on purpose: the thing that goes in an envelope to a
credit bureau under a client's signature is not a place for a model to
improvise, and a template is the only version whose accuracy you can actually
report.

A dispute is drafted once per bureau, because an item removed at Equifax is
still sitting on the Experian and TransUnion files. Drafting one letter and
calling the job done was the single most misleading thing in the first build.

Every legal sentence in a template comes from app/sources.py, which carries the
primary source and the date somebody checked it. The client screen asks for one number:
how often does the reviewer edit before approving. ReviewLog is where it comes
from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.bureaus import ANNUAL_REPORT_REQUEST, BUREAUS, Bureau
from app.sources import fact

DISPUTE_TEMPLATE = """\
{today}

{address_block}

Re: Request to remove inaccurate information
Name: {client_name}
SSN: [client writes by hand on the printed copy]
Date of birth: [client writes by hand on the printed copy]
Addresses for the past two years: [client completes by hand]

I am writing to dispute the following information in my file. The item listed
below is not mine. I did not open this account and I request that it be
removed.

Item: {creditor}, account ending {last_four}
Reason: {reason}

Please investigate this item and send me the results in writing. If the item
cannot be verified, please delete it from my file.

I understand you have 30 days from the date you receive this letter to complete
your investigation, and that you must send me the results in writing within 5
business days of completing it.

Sincerely,


____________________________
{client_name}
"""

# Built to match what the bureaus actually ask for when the request comes from
# a prison or jail, which is not the same list as a request from a house. Note
# the addresses asked for are the two years BEFORE incarceration, not the two
# years before today, and the prisoner ID number is required twice: in the
# letter and on the envelope.
REPORT_REQUEST_TEMPLATE = """\
{today}

{address_block}

Re: Request for free annual credit reports, by mail

Please send copies of my credit file from all three nationwide credit
reporting companies: Equifax, Experian and TransUnion.

Full name (with any suffix): {client_name}
Prisoner identification number ({id_label}): {identification}
Current address:
{current_address}
Addresses during the two years preceding incarceration:
  [client completes by hand]
Social Security number: [client writes by hand on the printed copy]
Date of birth: [client writes by hand on the printed copy]

I am requesting these reports by mail because I do not have internet or phone
access to complete an identity check.

Sincerely,


____________________________
{client_name}

--------------------------------------------------------------------------
FOR WHOEVER ADDRESSES THE ENVELOPE

The return address on the envelope must be the correctional institution, and
the prisoner identification number must appear on the envelope. The bureaus
ask for this specifically on mail from a facility, and a request without it
can come back.

    Return address:  {client_name}, {identification}
                     {facility}

    Send to:         Annual Credit Report Request Service
                     P.O. Box 105281
                     Atlanta, GA 30348-5281
--------------------------------------------------------------------------
"""


@dataclass
class Draft:
    kind: str
    client_id: str
    bureau: str
    body: str
    citations: list[str] = field(default_factory=list)
    approved_on: date | None = None
    edited_before_approval: bool | None = None

    @property
    def status(self) -> str:
        return "awaiting approval" if self.approved_on is None else "approved"


def _dispute_citations(bureau: Bureau) -> list[str]:
    cites = [
        fact("reinvestigation_window").cite(),
        fact("reinvestigation_extension").cite(),
        fact("results_notice").cite(),
        fact("mailed_dispute_identity").cite(),
        f"Address from {bureau.source_url}",
    ]
    if bureau.note:
        cites.append(bureau.note)
    return cites


def draft_dispute(
    *,
    client_id: str,
    client_name: str,
    bureau: Bureau,
    creditor: str,
    last_four: str,
    reason: str,
    today: date | None = None,
) -> Draft:
    today = today or date.today()
    body = DISPUTE_TEMPLATE.format(
        today=today.strftime("%B %-d, %Y"),
        address_block=bureau.address_block,
        client_name=client_name,
        creditor=creditor,
        last_four=last_four,
        reason=reason,
    )
    return Draft(
        kind="dispute",
        client_id=client_id,
        bureau=bureau.name,
        body=body,
        citations=_dispute_citations(bureau),
    )


def draft_dispute_set(
    *,
    client_id: str,
    client_name: str,
    creditor: str,
    last_four: str,
    reason: str,
    today: date | None = None,
) -> list[Draft]:
    """One letter per bureau. An item removed at one is still live at the other two."""
    return [
        draft_dispute(
            client_id=client_id,
            client_name=client_name,
            bureau=bureau,
            creditor=creditor,
            last_four=last_four,
            reason=reason,
            today=today,
        )
        for bureau in BUREAUS
    ]


def draft_report_request(
    *,
    client_id: str,
    client_name: str,
    delivery_address: str,
    identification: str = "",
    id_label: str = "DIN",
    facility: str = "",
    today: date | None = None,
) -> Draft:
    """One request to the centralized source covers all three bureaus.

    This is the route that works with no internet, which is the whole reason it
    is the cheapest route in and the whole reason the inside surface
    exists.
    """
    today = today or date.today()
    body = REPORT_REQUEST_TEMPLATE.format(
        today=today.strftime("%B %-d, %Y"),
        address_block=ANNUAL_REPORT_REQUEST.address_block,
        client_name=client_name,
        identification=identification or "[client writes by hand]",
        id_label=id_label,
        facility=facility or "[correctional institution]",
        current_address=f"  {delivery_address}",
    )
    return Draft(
        kind="report_request",
        client_id=client_id,
        bureau=ANNUAL_REPORT_REQUEST.name,
        body=body,
        citations=[
            fact("mail_request_from_a_facility").cite(),
            fact("free_report_entitlement").cite(),
            fact("free_report_mail_route").cite(),
            fact("weekly_free_reports").cite(),
            fact("facility_record_rules").cite(),
        ],
    )


def dispute_deadline(received_on: date) -> date:
    """30 days from the day the bureau receives it. Not from the postmark.

    The distinction matters on the case timeline: a client watching a date is
    watching the wrong one if we count from the day the helper mailed it.
    """
    from datetime import timedelta

    return received_on + timedelta(days=30)


@dataclass
class ReviewLog:
    """The accuracy metric, kept honestly.

    Reporting this number when it is bad is the whole lesson from the DoNotPay
    enforcement action. A tool that claims accuracy it cannot show is the
    failure mode this project is trying not to repeat.
    """

    reviewed: int = 0
    edited: int = 0

    def record(self, *, edited: bool) -> None:
        self.reviewed += 1
        if edited:
            self.edited += 1

    @property
    def edit_rate(self) -> float | None:
        if self.reviewed == 0:
            return None
        return self.edited / self.reviewed

    def summary(self) -> str:
        if self.edit_rate is None:
            return "No letters reviewed yet."
        return (
            f"{self.edited} of {self.reviewed} drafts were edited before "
            f"approval ({self.edit_rate:.0%})."
        )
