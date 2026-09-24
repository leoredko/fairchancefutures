"""Free financial counseling a person can walk into after release.

This is the first thing in Bridge that reaches past the gate. Everything else
stops at release, which is a problem the product has rather than one it solves:
a dispute has 30 days from receipt, the coordinator loses standing the moment
somebody is no longer in custody, and a helper's authorization was scoped and
expiring on purpose. So a live clock can be running on day one outside with
nobody holding it. A counselor who does credit work for free is the successor.

The Financial Empowerment Center model is municipal and free, and the
counselors do credit reports, debt and disputes rather than general social
services, so a person continues the same work with a human. Pair it with
15 U.S.C. 1679b, already in `app.sources`: here is a free one, and here is the
law that says anybody charging you up front is breaking it.

Why this is a hand-kept registry rather than a live feed
--------------------------------------------------------
New York City publishes a Financial Empowerment Centers dataset on NYC Open
Data, and `scripts/check_centers.py` does read it. It is not served to anybody.
Its rows have not changed since 2017, one of its providers has since been
renamed, and the city no longer publishes a current list anywhere else: both
DCWP pages route a person to 311 or to the booking portal instead. So the
dataset is not a live source running behind. It is a 2017 snapshot that happens
to have a JSON endpoint, and there is nothing authoritative to reconcile it
against.

An address nobody has checked is worse coming from a government API than from
a guess, because it arrives wearing the city's authority. So the same rule the
legal facts live under applies here: every entry carries where it came from and
the date somebody looked. `app.freshness` is what notices when that date gets
old, and the script diffs the city's rows against this file so a human is told
to go look rather than the app quietly serving 2017.

Coverage is honest rather than complete
---------------------------------------
Bridge is a New York State product and this model does not cover the state.
Buffalo is standing one up and has not opened it. Most of the state has no
municipal center at all. `for_county` returns nothing rather than the nearest
big city, and the caller is expected to say so plainly: sending somebody two
hundred miles because the list looked empty is the failure this avoids.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

CHECKED = date(2026, 9, 24)


@dataclass(frozen=True)
class Center:
    """One place, and the sentence that says whether it is for you.

    `eligibility` is quoted from the operator's own page wherever possible,
    because a paraphrase of who qualifies is how somebody gets turned away at
    a desk they travelled to reach.
    """

    key: str
    name: str
    city: str
    counties: tuple[str, ...]
    eligibility: str
    booking: tuple[str, ...]
    source: str
    url: str
    checked_on: date
    verified_by_hand: bool = True
    note: str = ""

    def cite(self) -> str:
        return f"{self.source}, checked {self.checked_on.isoformat()}"


CENTERS: tuple[Center, ...] = (
    Center(
        key="nyc",
        name="NYC Financial Empowerment Centers",
        city="New York City",
        counties=("Bronx", "Kings", "New York", "Queens", "Richmond"),
        eligibility="You qualify for free counseling if you're at least age 18 "
                    "and live or work in NYC.",
        booking=(
            "Call 311 and say financial counseling",
            "Book at nyc.gov/talkmoney",
            "Walk in, though an appointment means a shorter wait",
        ),
        source="NYC, Access NYC program page",
        url="https://access.nyc.gov/programs/nyc-financial-empowerment-centers/",
        checked_on=CHECKED,
        note="The page states no income test and no immigration requirement. "
             "Counselors are available in languages other than English. The "
             "centers do not make loans or grants.",
    ),
    Center(
        key="syracuse",
        name="Syracuse Financial Empowerment Center",
        city="Syracuse",
        counties=("Onondaga",),
        eligibility="The Syracuse Financial Empowerment Center (FEC) provides "
                    "free, one-on-one professional financial counseling to all "
                    "City of Syracuse residents.",
        booking=(
            "Call 315-428-2224",
            "Email info@syracusefec.org",
            "Book through the FEC client portal",
        ),
        source="City of Syracuse, Neighborhood and Business Development",
        url="https://www.syr.gov/Departments/NBD/Syracuse-FEC",
        checked_on=CHECKED,
        note="Run by Home HeadQuarters with the City. Eligibility reads as "
             "city residents rather than the whole county, so somebody in "
             "Onondaga County outside the city should call before travelling.",
    ),
    Center(
        key="rochester",
        name="Rochester Financial Empowerment Center",
        city="Rochester",
        counties=("Monroe",),
        eligibility="Open to people 18 and over who live, work, worship or go "
                    "to school in Monroe County.",
        booking=("Contact the City of Rochester Office of Financial "
                 "Empowerment",),
        source="City of Rochester, Office of Financial Empowerment",
        url="https://www.cityofrochester.gov/departments/"
            "office-financial-empowerment/financial-empowerment-center",
        checked_on=CHECKED,
        verified_by_hand=False,
        note="NOT READ FIRST HAND. The city's site refuses automated fetching, "
             "so this wording came from search results rather than from the "
             "page. Same situation as the TransUnion address in docs/VERIFY.md: "
             "somebody has to open it in a browser before this goes in front of "
             "a person.",
    ),
    Center(
        key="mount-vernon",
        name="Mount Vernon Financial Empowerment Center",
        city="Mount Vernon",
        counties=("Westchester",),
        eligibility="",
        booking=("See mountvernonfec.org",),
        source="FEC Public, implementation partners",
        url="https://fecpublic.org/about/",
        checked_on=CHECKED,
        verified_by_hand=False,
        note="Listed as an operating partner, but the eligibility sentence has "
             "not been read from Mount Vernon's own page. Left blank rather "
             "than guessed, because who qualifies is the one thing that cannot "
             "be inferred from the fact that a center exists.",
    ),
)


# Not open yet, and worth saying so rather than showing a person an empty
# screen. A city building one is a different answer from a city with none.
COMING: tuple[Center, ...] = (
    Center(
        key="buffalo",
        name="Buffalo Financial Empowerment Center",
        city="Buffalo",
        counties=("Erie",),
        eligibility="",
        booking=(),
        source="City of Buffalo, Financial Empowerment Center RFP",
        url="https://www.buffalony.gov/m/newsflash/home/detail/1584",
        checked_on=CHECKED,
        verified_by_hand=False,
        note="Buffalo entered the CFE Fund's FEC Academy in December 2022 and "
             "issued the operator RFP in 2025. Not open. Do not send anybody.",
    ),
)


def for_county(county: str) -> Center | None:
    """The center serving a county, or nothing.

    Nothing is a real answer here. Most of New York State has no municipal
    center, and offering the nearest one anyway sends somebody on a journey
    they cannot afford to a desk that will turn them away.
    """
    wanted = county.strip().casefold().removesuffix(" county").strip()
    if not wanted:
        return None
    for center in CENTERS:
        if any(c.casefold() == wanted for c in center.counties):
            return center
    return None


def opening_in(county: str) -> Center | None:
    """A center being built there, so the answer can be 'not yet' not 'no'."""
    wanted = county.strip().casefold().removesuffix(" county").strip()
    if not wanted:
        return None
    for center in COMING:
        if any(c.casefold() == wanted for c in center.counties):
            return center
    return None


def needs_a_human_read() -> tuple[Center, ...]:
    """Entries carrying a claim nobody has read from the source page.

    These are the ones that must not reach a screen yet. `/citations` renders
    the open questions next to the checked facts for the same reason.
    """
    return tuple(c for c in CENTERS + COMING if not c.verified_by_hand)


# Every county Bridge can answer for, with the ones it cannot named as such.
# A picker built from this cannot offer a county the registry has no honest
# answer for, and cannot quietly drop one either.
NY_COUNTIES: tuple[str, ...] = (
    "Albany", "Allegany", "Bronx", "Broome", "Cattaraugus", "Cayuga",
    "Chautauqua", "Chemung", "Chenango", "Clinton", "Columbia", "Cortland",
    "Delaware", "Dutchess", "Erie", "Essex", "Franklin", "Fulton", "Genesee",
    "Greene", "Hamilton", "Herkimer", "Jefferson", "Kings", "Lewis",
    "Livingston", "Madison", "Monroe", "Montgomery", "Nassau", "New York",
    "Niagara", "Oneida", "Onondaga", "Ontario", "Orange", "Orleans", "Oswego",
    "Otsego", "Putnam", "Queens", "Rensselaer", "Richmond", "Rockland",
    "St. Lawrence", "Saratoga", "Schenectady", "Schoharie", "Schuyler",
    "Seneca", "Steuben", "Suffolk", "Sullivan", "Tioga", "Tompkins", "Ulster",
    "Warren", "Washington", "Wayne", "Westchester", "Wyoming", "Yates",
)

# The five boroughs under their county names, because a person going home to
# Brooklyn does not think of it as Kings and should not have to.
BOROUGH_NAME: dict[str, str] = {
    "Bronx": "the Bronx",
    "Kings": "Brooklyn",
    "New York": "Manhattan",
    "Queens": "Queens",
    "Richmond": "Staten Island",
}


def answer_for(county: str) -> dict:
    """What this county gets, including the honest nothing.

    Only entries a person on this team has read from the source reach a
    screen. An address arriving from a government dataset nobody opened is
    worse than a guess, because it wears the city's authority, and a center
    that closed sends somebody who just came home on a bus ride to a locked
    door. `needs_a_human_read()` is the list this refuses to serve.
    """
    found = for_county(county)
    if found is not None and found.verified_by_hand:
        return {"county": county, "center": found, "state": "open"}

    # Named rather than hidden: somebody who lives there should be told the
    # work is pending, not shown an empty page that reads like a dead end.
    if found is not None:
        return {"county": county, "center": None, "state": "unchecked"}

    coming = opening_in(county)
    if coming is not None and coming.verified_by_hand:
        return {"county": county, "center": coming, "state": "coming"}
    if coming is not None:
        return {"county": county, "center": None, "state": "unchecked"}

    return {"county": county, "center": None, "state": "none"}
