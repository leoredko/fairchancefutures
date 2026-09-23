"""What is already known about somebody from their DIN.

A person signing in types the number they are called by every day. Everything
attached to it is already recorded somewhere, and asking them to type their own
release date into a form is asking them to do a computer's job from memory, on
a metered tablet, with no way to check.

So: DIN in, the dates out.

Two sources, and keeping them apart is the whole point of this module.

The **public lookup** at nysdoccslookup.doccs.ny.gov answers on a DIN with
facility, the release dates and the sentence dates. Anybody can query it. It
does NOT return a date of birth: you can search by year of birth, but the
record that comes back has no DOB on it. So a DOB can never be said to have
come from here, and this module will not invent one.

The **coordinator's own record** holds what the lookup does not: date of birth,
Social Security number, the vital documents packet. That lives behind the case
plan integration in `app/caseplan.py`, and it is the coordinator's to hold.

That split decides what the tablet can fill in for somebody without asking a
human, and it is also why `date_of_birth` is not on `LookupRecord`.

Which date the product plans against
------------------------------------
DOCCS publishes several and they mean different things. Parole eligibility is
the earliest a board could act, not a date anybody goes home on. Maximum
expiration is the far end. The conditional release date is the one a reentry
plan is actually built around, so that is what Bridge plans against, falling
back to the earliest release date when there is no conditional one. Both are
stored either way, and the screen names which one it is using, because telling
somebody "you go home on the 14th" off the wrong field is the kind of mistake
that ends trust in one screen.

    Field names and definitions, checked 2026-09-23
    DOCCS, Inmate Information Data Definitions
    https://publicapps.doccs.ny.gov/ILookup/fpmsdoc.html

SIMULATED. Nothing here calls a real endpoint. `simulated_lookup()` is the one
function a real integration replaces, the same way `simulated_plan()` is in
app/caseplan.py.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from datetime import date, timedelta

SIMULATED = True

LOOKUP_URL = "https://nysdoccslookup.doccs.ny.gov/"
DEFINITIONS_URL = "https://publicapps.doccs.ny.gov/ILookup/fpmsdoc.html"


@dataclass(frozen=True)
class LookupRecord:
    """One record as the public lookup returns it.

    Field names follow the DOCCS labels rather than anything invented here, so
    a real integration is a mapping exercise and not a translation. Every one
    of these is a string in ISO form or empty; a date this person does not have
    is absent rather than guessed.
    """

    din: str
    housing_facility: str = ""
    date_received_original: str = ""
    date_received_current: str = ""
    earliest_release_date: str = ""
    parole_eligibility_date: str = ""
    conditional_release_date: str = ""
    maximum_expiration_date: str = ""
    post_release_supervision_max_expiration_date: str = ""

    @property
    def planning_date(self) -> str:
        """The date a reentry plan is built around, or empty if unknown.

        Conditional release first, then earliest release. Deliberately not
        parole eligibility, which is the earliest a board could act rather than
        a date anybody goes home on, and deliberately not maximum expiration.
        """
        return self.conditional_release_date or self.earliest_release_date

    @property
    def planning_date_label(self) -> str:
        """Which field the planning date came from, in words.

        The screen says this out loud. Telling somebody they go home on a date
        that turns out to be their parole eligibility is the kind of mistake
        that ends trust in a single screen.
        """
        if self.conditional_release_date:
            return "Conditional release date"
        if self.earliest_release_date:
            return "Earliest release date"
        return ""

    def as_dict(self) -> dict:
        return asdict(self)


# What a person may see of their own record on a shared tablet.
#
# All of it, and that is not a loophole. These are the dates this person is
# told at their own reception and can recite from memory; the lookup publishes
# them to the whole internet; and seeing them come back correct is how somebody
# knows the app has the right person before they trust it with anything else.
#
# The date of birth is the one field that would be wrong to show here, and it
# is not on this record at all, because the lookup does not return one. That is
# the dayroom rule holding by construction rather than by a check.
SHOWN_TO_THE_PERSON: tuple[str, ...] = (
    "housing_facility",
    "conditional_release_date",
    "earliest_release_date",
    "parole_eligibility_date",
    "maximum_expiration_date",
    "post_release_supervision_max_expiration_date",
    "date_received_original",
)


def _stable_offset(din: str, spread: int, floor: int = 0) -> int:
    """A deterministic pseudo-date offset from the DIN.

    Deterministic so a demo client's dates do not move between restarts, which
    would make the 120-day document trigger flap. Replaced wholesale by a real
    lookup.
    """
    digest = hashlib.sha256(din.encode()).hexdigest()
    return floor + int(digest[:6], 16) % max(spread, 1)


def simulated_lookup(din: str, today: date | None = None) -> LookupRecord:
    """Stand in for the query a real deployment would make.

    Everything returned is invented, and deliberately varied by DIN so that
    self-service sign-ins do not all land on the same release date. A real
    integration replaces this one function.

    Before this existed, a case opened from the tablet was given a release date
    of today plus 180 days and no facility at all. Both were fabrications that
    then drove the work queue's ordering, the quarterly review count and the
    120-day document deadline.
    """
    today = today or date.today()
    key = (din or "").upper().replace("-", "")

    # Somewhere between four months and six years out, so the caseload spans
    # people near the gate and people who are not.
    days_out = _stable_offset(key, spread=2000, floor=120)
    conditional = today + timedelta(days=days_out)

    return LookupRecord(
        din=key,
        housing_facility=_FACILITIES[_stable_offset(key, len(_FACILITIES))],
        date_received_original=(today - timedelta(
            days=_stable_offset(key, 2500, floor=400))).isoformat(),
        date_received_current=(today - timedelta(
            days=_stable_offset(key, 700, floor=60))).isoformat(),
        earliest_release_date=(conditional - timedelta(days=90)).isoformat(),
        parole_eligibility_date=(conditional - timedelta(days=210)).isoformat(),
        conditional_release_date=conditional.isoformat(),
        maximum_expiration_date=(conditional + timedelta(days=540)).isoformat(),
        post_release_supervision_max_expiration_date=(
            conditional + timedelta(days=540 + 1095)).isoformat(),
    )


# Real facility names, because the facility is the envelope return address on
# mail to a bureau and a made-up one would produce a letter that cannot arrive.
_FACILITIES: tuple[str, ...] = (
    "Sing Sing Correctional Facility",
    "Bedford Hills Correctional Facility",
    "Fishkill Correctional Facility",
    "Green Haven Correctional Facility",
    "Woodbourne Correctional Facility",
    "Otisville Correctional Facility",
)
