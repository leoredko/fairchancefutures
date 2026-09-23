"""Letter drafting.

Every letter is assembled from a fixed template plus named facts. There is no
free generation here, on purpose: the thing that goes in an envelope to a
credit bureau under a client's signature is not a place for a model to
improvise, and a template is the only version whose accuracy you can actually
report.

Screen 09 asks for one number: how often does the reviewer edit before
approving. record_review() is where that number comes from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


DISPUTE_TEMPLATE = """\
{today}

{bureau}
Dispute Department

Re: Request to remove inaccurate information
Name: {client_name}
SSN: [client writes by hand on the printed copy]
Date of birth: [client writes by hand on the printed copy]

I am writing to dispute the following information in my file. The item listed
below is not mine. I did not open this account and I request that it be
removed.

Item: {creditor}, account ending {last_four}
Reason: {reason}

Please investigate this item and send me the results in writing. If the item
cannot be verified, please delete it from my file.

Sincerely,


____________________________
{client_name}
"""

# Rung 1 of the access ladder. The cheapest thing that often just works.
REPORT_REQUEST_TEMPLATE = """\
{today}

{bureau}
Consumer Report Request

Please send a copy of my credit file to the address below.

Name: {client_name}
SSN: [client writes by hand on the printed copy]
Date of birth: [client writes by hand on the printed copy]
Current address for delivery: {delivery_address}
Previous addresses: [client completes by hand]

I am requesting this report by mail because I do not have internet access to
complete an online identity check.

Sincerely,


____________________________
{client_name}
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
        if self.approved_on is None:
            return "awaiting approval"
        return "approved"


def draft_dispute(
    *,
    client_id: str,
    client_name: str,
    bureau: str,
    creditor: str,
    last_four: str,
    reason: str,
    today: date | None = None,
) -> Draft:
    today = today or date.today()
    body = DISPUTE_TEMPLATE.format(
        today=today.strftime("%B %-d, %Y"),
        bureau=bureau,
        client_name=client_name,
        creditor=creditor,
        last_four=last_four,
        reason=reason,
    )
    return Draft(
        kind="dispute",
        client_id=client_id,
        bureau=bureau,
        body=body,
        citations=[
            "Reinvestigation window and clock start: UNVERIFIED, on the "
            "verify-before-demo list.",
            "Template contains no statutory citation until a primary source is "
            "checked. An unchecked citation on a real letter is worse than none.",
        ],
    )


def draft_report_request(
    *,
    client_id: str,
    client_name: str,
    bureau: str,
    delivery_address: str,
    today: date | None = None,
) -> Draft:
    today = today or date.today()
    body = REPORT_REQUEST_TEMPLATE.format(
        today=today.strftime("%B %-d, %Y"),
        bureau=bureau,
        client_name=client_name,
        delivery_address=delivery_address,
    )
    return Draft(
        kind="report_request",
        client_id=client_id,
        bureau=bureau,
        body=body,
        citations=[
            "Free report entitlement and the mail-in route: UNVERIFIED, on the "
            "verify-before-demo list.",
        ],
    )


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
