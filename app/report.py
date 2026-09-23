"""The credit report, as something a person inside can actually read.

Nobody photographs anything. The reports come back on paper to the facility,
the person carries them to their coordinator, and the coordinator scans them
into the record. From then on the person reads their own report on the tablet.

The reason that is safe on a shared kiosk is statutory rather than a policy we
invented: on request, with proof of identity, a credit reporting agency SHALL
leave the first five digits of the Social Security number out of the consumer's
own file disclosure. The request goes out asking for exactly that, so the
document that comes back is already truncated, and this module masks whatever
arrives anyway. Two locks on the same door, because the failure here is
somebody's SSN on a screen in a dayroom.

    15 U.S.C. 1681g(a)(1)(A), checked 2026-09-23

One more thing worth saying to a person opening this for the first time: the
free disclosure does not have to include a credit score. The statute excludes
scores from what must be disclosed. Somebody expecting a number and finding a
list of accounts has not been cheated, and the app says so before they look.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class Source(str, Enum):
    """How the document got here, best route first.

    The order is not cosmetic. A PDF is the whole document, exact, and costs
    the helper one tap. Typed data is exact too but costs them twenty minutes
    and can carry a typo. A photograph is last because nothing in this build
    reads data out of a picture: somebody has to sit down and transcribe it,
    and that somebody is the coordinator.
    """

    PDF = "pdf"
    TYPED = "typed"
    PHOTO = "photo"
    SCAN = "scan"      # the coordinator's own scanner, at the desk


SOURCE_LABEL: dict[Source, str] = {
    Source.PDF: "PDF sent in by the helper",
    Source.TYPED: "Typed in by the helper",
    Source.PHOTO: "Photographed by the helper",
    Source.SCAN: "Scanned at the coordinator's desk",
}

# Which routes land finished, and which land on somebody's desk. A coordinator
# scanning at their own desk confirms as they go, so that one is done. Anything
# arriving from outside is checked by a human before it can become a dispute
# letter about an account number nobody verified.
SELF_CONFIRMING = frozenset({Source.SCAN})

SOURCE_NEXT_STEP: dict[Source, str] = {
    Source.PDF: "Your coordinator reads the fields off the PDF and confirms them.",
    Source.TYPED: "Your coordinator checks what you typed against the paper.",
    Source.PHOTO: "Your coordinator reads the photos with the person and types "
                  "the accounts in. This is the slowest route, which is why it "
                  "is the last one offered.",
    Source.SCAN: "Confirmed at the desk.",
}


def mask_ssn(value: str) -> str:
    """Leave the last four, take out everything before it.

    Defensive on purpose: the request already asks for a truncated disclosure,
    but this runs on whatever actually arrives. An unmasked number on a shared
    tablet is the worst thing this app could put on a screen.
    """
    digits = re.sub(r"\D", "", value or "")
    if not digits:
        return "XXX-XX-XXXX"
    return f"XXX-XX-{digits[-4:]}"


def mask_account(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    return f"ending {digits[-4:]}" if len(digits) >= 4 else "number withheld"


@dataclass
class Account:
    creditor: str
    number: str
    opened: str
    status: str
    balance: str = ""
    disputed: bool = False
    note: str = ""

    @property
    def safe_number(self) -> str:
        return mask_account(self.number)


@dataclass
class CreditReport:
    """One bureau's file, as scanned into the record by a coordinator."""

    bureau: str
    client_id: str
    pulled_on: str
    scanned_on: str
    scanned_by: str
    consumer_name: str
    ssn_on_document: str = ""
    date_of_birth: str = ""
    addresses: list[str] = field(default_factory=list)
    accounts: list[Account] = field(default_factory=list)
    inquiries: list[str] = field(default_factory=list)
    public_records: list[str] = field(default_factory=list)
    score: str = ""
    source: str = Source.SCAN.value
    # A report nobody has checked does not reach the person's tablet and does
    # not draft a letter. It sits on the coordinator's desk saying so.
    confirmed: bool = True
    pages: list[str] = field(default_factory=list)

    @property
    def source_label(self) -> str:
        return SOURCE_LABEL.get(Source(self.source), "Added to the record")

    @property
    def next_step(self) -> str:
        return SOURCE_NEXT_STEP.get(Source(self.source), "")

    @property
    def safe_ssn(self) -> str:
        return mask_ssn(self.ssn_on_document)

    @property
    def safe_dob(self) -> str:
        """Year only. A full date of birth is half of an identity theft."""
        match = re.search(r"(19|20)\d{2}", self.date_of_birth or "")
        return f"Born {match.group(0)}" if match else "Not shown"

    @property
    def disputed(self) -> list[Account]:
        return [a for a in self.accounts if a.disputed]

    @property
    def score_line(self) -> str:
        if self.score:
            return self.score
        return ("No score on this report. A file disclosure does not have to "
                "include one, and most mailed reports do not.")

    @property
    def summary(self) -> str:
        if not self.accounts:
            return "No accounts on file with this bureau."
        parts = [f"{len(self.accounts)} account"
                 f"{'' if len(self.accounts) == 1 else 's'}"]
        if self.disputed:
            parts.append(f"{len(self.disputed)} disputed")
        if self.public_records:
            parts.append(f"{len(self.public_records)} public record"
                         f"{'' if len(self.public_records) == 1 else 's'}")
        return ", ".join(parts)


def from_scan(
    *,
    client_id: str,
    bureau: str,
    consumer_name: str,
    scanned_by: str,
    pulled_on: str = "",
    accounts: list[dict] | None = None,
    ssn_on_document: str = "",
    source: Source = Source.SCAN,
    pages: list[str] | None = None,
    today: date | None = None,
) -> CreditReport:
    """Build the record from what the coordinator's scan produced.

    The coordinator confirms the fields before they are saved. That confirmation
    step is not ceremony: it is the same accuracy check as the letter edit rate,
    on the input side instead of the output side.
    """
    today = today or date.today()
    return CreditReport(
        bureau=bureau,
        client_id=client_id,
        pulled_on=pulled_on or today.isoformat(),
        scanned_on=today.isoformat(),
        scanned_by=scanned_by,
        consumer_name=consumer_name,
        ssn_on_document=ssn_on_document,
        source=Source(source).value,
        confirmed=Source(source) in SELF_CONFIRMING,
        pages=list(pages or []),
        accounts=[
            Account(
                creditor=a.get("creditor", ""),
                number=a.get("number", ""),
                opened=a.get("opened", ""),
                status=a.get("status", ""),
                balance=a.get("balance", ""),
                disputed=bool(a.get("disputed")),
                note=a.get("note", ""),
            )
            for a in (accounts or [])
        ],
    )


# --------------------------------------------------------------------------
# what the coordinator's scanner hands over
# --------------------------------------------------------------------------

SCANNER_NOTE = (
    "The scanner reads the document and fills this form in. Nothing is saved "
    "until you confirm it, because an account number read wrong here becomes a "
    "dispute letter about the wrong account."
)

# One account per line, fields separated by a pipe. This is the shape the
# scanner emits and the shape the coordinator edits, which means the confirm
# step is editing the same text the machine produced rather than a translation
# of it.
LINE_FORMAT = "creditor | account number | opened | status | balance | dispute reason"


def parse_accounts(text: str) -> list[dict]:
    """Read the scanner's lines. Blank lines and short lines are skipped.

    Forgiving on purpose: a coordinator fixing a misread should not have to
    count pipes. Anything after the creditor is optional.
    """
    rows: list[dict] = []
    for line in (text or "").splitlines():
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split("|")]
        parts += [""] * (6 - len(parts))
        creditor, number, opened, status, balance, reason = parts[:6]
        if not creditor:
            continue
        rows.append({
            "creditor": creditor,
            "number": number,
            "opened": opened,
            "status": status,
            "balance": balance,
            "disputed": bool(reason),
            "note": reason,
        })
    return rows


def simulated_scan(client) -> dict:
    """Stand-in for the facility scanner's output.

    This is the one function a real integration replaces. Everything downstream
    of it, the confirm step, the masking, the storage, is real.
    """
    lines = [
        f"{item['creditor']} | xxxx{item['last_four']} |  | Open | "
        f"$0 | {item['reason']}"
        for item in getattr(client, "flagged_items", [])
    ]
    if not lines:
        lines = ["Cap One Platinum | xxxx2210 | 2016-04 | Closed, paid | $0 | "]
    return {
        "bureau": "Equifax",
        "consumer_name": client.display_name,
        "ssn_on_document": "XXX-XX-4417",
        "pulled_on": "",
        "accounts": "\n".join(lines),
    }
