"""New York State identifiers.

This build is New York only, so the login takes the two numbers a person
actually has: a DIN or a NYSID.

The DIN format is confirmed from DOCCS's own glossary. The NYSID format is not.
The one document that would settle it could not be read directly, and the
secondary summary of it contradicted its own example, so this module accepts
NYSIDs leniently and says why.

That asymmetry is deliberate. At a kiosk, rejecting a number a person actually
holds is the worst thing this code can do: they have no second channel, no help
desk, and quite possibly one shot before the next person needs the tablet. When
in doubt, let it through and let the lookup fail with a sentence they can act
on.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class IdKind(str, Enum):
    DIN = "din"
    NYSID = "nysid"


# 2-digit year, facility letter, 4-digit sequence. Printed as 98-A-0004 but
# people type it every which way, so punctuation and spacing are stripped first.
# Confirmed: DOCCS Parolee Lookup glossary, checked 2026-09-23.
DIN_RE = re.compile(r"^(\d{2})([A-Z])(\d{4})$")

# Eight digits and, usually, a trailing check letter. Which letters are valid
# is NOT confirmed, so the letter is accepted and never validated against a
# list. A real number rejected by a guess would be unforgivable here.
NYSID_RE = re.compile(r"^(\d{8})([A-Z]?)$")


class InvalidIdentifier(ValueError):
    """Carries a sentence a person at a kiosk can act on."""


@dataclass(frozen=True)
class Identifier:
    kind: IdKind
    normalized: str

    @property
    def display(self) -> str:
        if self.kind is IdKind.DIN:
            m = DIN_RE.match(self.normalized)
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        return self.normalized

    @property
    def label(self) -> str:
        return "DIN" if self.kind is IdKind.DIN else "NYSID"


def _strip(raw: str) -> str:
    """Dashes, spaces, dots, whatever. People copy these off a printed sheet."""
    return re.sub(r"[^A-Za-z0-9]", "", raw or "").upper()


def parse(raw: str) -> Identifier:
    cleaned = _strip(raw)
    if not cleaned:
        raise InvalidIdentifier("Enter your DIN or your NYSID.")

    m = DIN_RE.match(cleaned)
    if m:
        return Identifier(IdKind.DIN, cleaned)

    m = NYSID_RE.match(cleaned)
    if m:
        return Identifier(IdKind.NYSID, cleaned)

    # Say what shape each one is rather than "invalid input". A person who
    # mistyped one character should be able to see which.
    if cleaned.isdigit() and len(cleaned) == 6:
        raise InvalidIdentifier(
            "That looks like a DIN with the facility letter missing. A DIN is "
            "two digits, a letter, then four digits, like 98-A-0004."
        )
    if len(cleaned) < 7:
        raise InvalidIdentifier(
            "That is too short. A DIN looks like 98-A-0004. A NYSID is eight "
            "digits, sometimes with a letter on the end."
        )
    raise InvalidIdentifier(
        "That is not a DIN or a NYSID. A DIN is two digits, a letter, then four "
        "digits, like 98-A-0004. A NYSID is eight digits, sometimes with a "
        "letter on the end."
    )


# Numbers starting 28 mean a 2028 intake, which has not happened, so they
# cannot belong to a real person in the public DOCCS lookup. That makes them
# the safe range for anyone trying the app out: sign in with any of them and
# an account is created on the spot.
SELF_SERVICE_YEAR = "28"


def is_self_service(identifier: "Identifier") -> bool:
    return (identifier.kind is IdKind.DIN
            and identifier.normalized.startswith(SELF_SERVICE_YEAR))


def looks_like(raw: str) -> IdKind | None:
    """Non-raising check, for deciding what to show before someone submits."""
    try:
        return parse(raw).kind
    except InvalidIdentifier:
        return None
