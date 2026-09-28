"""Every New York State correctional facility, as DOCCS currently lists them.

This is the envelope. A dispute goes to a bureau by mail, the bureaus ask for
the return address on mail from a prison, and `app.letters` prints whatever
this app believes the facility to be. A facility that closed four years ago
prints an envelope that comes back, and a facility that does not hold this
person prints one that says, to anybody reading it, that the sender does not
know who they are writing about.

So the same rule the counseling centers live under applies here, for the same
reason: an address nobody has read does not reach a screen, and it is more
dangerous, not less, when it arrives wearing the state's authority.

Why this exists as a list rather than a text box
------------------------------------------------
The facility used to be a free-text field with a datalist of eight names
beside it. Three of those eight were wrong in ways nobody caught: `Downstate
Correctional Facility` closed in 2022 and is not on the DOCCS list at all, and
the picker mixed facilities for men and facilities for women with nothing
marking which was which. Anything typed into the box was accepted, so a typo
became a return address.

The list is also what makes the `serves` field enforceable. `Bedford Hills`,
`Albion` and `Taconic` are the three facilities DOCCS operates for women. A
record that puts a man in one of them is not a cosmetic error: it is the app
announcing on a letter that its data is not about this person.

    Names, security levels, populations and mailing addresses read from the
    DOCCS facility pages, one page per facility, checked 2026-09-28.
    https://doccs.ny.gov/find-facility

Forty-one facilities. DOCCS has closed a number of them since 2021 and the
count is not stable, so `app.freshness` carries this date and says when
somebody should go and look again.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

CHECKED = date(2026, 9, 28)

SOURCE = "DOCCS, Find a facility"
SOURCE_URL = "https://doccs.ny.gov/find-facility"


@dataclass(frozen=True)
class Facility:
    """One facility, as DOCCS names it.

    `name` is the DOCCS spelling and nothing else, because it is what goes on
    an envelope and what a coordinator will be looking for in a list.

    `serves` is "males" or "females", in the DOCCS wording rather than a
    paraphrase. It is here so a record that contradicts it can be caught,
    which is the one thing the old free-text field could never do.
    """

    slug: str
    name: str
    level: str
    serves: str
    street: str
    city: str
    postal_code: str
    checked_on: date = CHECKED
    verified_by_hand: bool = True

    @property
    def mailing_address(self) -> tuple[str, ...]:
        """The return address block, as it goes on the envelope."""
        return (self.name, self.street, f"{self.city}, NY {self.postal_code}")

    @property
    def provenance(self) -> str:
        return f"{SOURCE}, checked {self.checked_on.isoformat()}"


FACILITIES: tuple[Facility, ...] = (
    Facility(slug='adirondack-correctional-facility',
             name='Adirondack Correctional Facility',
             level='medium', serves='males',
             street='196 Ray Brook Road, P.O. Box 110',
             city='Ray Brook', postal_code='12977-0110'),
    Facility(slug='albion-correctional-facility',
             name='Albion Correctional Facility',
             level='medium', serves='females',
             street='3595 State School Road',
             city='Albion', postal_code='14411-9399'),
    Facility(slug='altona-correctional-facility',
             name='Altona Correctional Facility',
             level='medium', serves='males',
             street='555 Devils Den Road, P.O. Box 3000',
             city='Altona', postal_code='12910-3000'),
    Facility(slug='attica-correctional-facility',
             name='Attica Correctional Facility',
             level='maximum', serves='males',
             street='639 Exchange St',
             city='Attica', postal_code='14011-0149'),
    Facility(slug='auburn-correctional-facility',
             name='Auburn Correctional Facility',
             level='maximum', serves='males',
             street='135 State Street, Incarcerated Individual Mail: P. O. Box 618, Zip 13021',
             city='Auburn', postal_code='13024-9000'),
    Facility(slug='bedford-hills-correctional-facility',
             name='Bedford Hills Correctional Facility',
             level='maximum', serves='females',
             street='247 Harris Road',
             city='Bedford Hills', postal_code='10507-2400'),
    Facility(slug='cape-vincent-correctional-facility',
             name='Cape Vincent Correctional Facility',
             level='medium', serves='males',
             street='36560 State Route 12E, P.O. Box 599',
             city='Cape Vincent', postal_code='13618-0599'),
    Facility(slug='cayuga-correctional-facility',
             name='Cayuga Correctional Facility',
             level='medium', serves='males',
             street='2202 State Route 38A, P.O. Box 1150 (Incarcerated Individual Mail: P.O. Box 1186, Zip 13118 )',
             city='Moravia', postal_code='13118-1150'),
    Facility(slug='clinton-correctional-facility',
             name='Clinton Correctional Facility',
             level='maximum', serves='males',
             street='1156 Rt. 374, P.O. Box 2000 (Incarcerated Individual Mail: P.O. Box 2001, Zip 12929)',
             city='Dannemora', postal_code='12929-2000'),
    Facility(slug='collins-correctional-facility',
             name='Collins Correctional Facility',
             level='medium', serves='males',
             street='Middle Road, P.O. Box 490 (Incarcerated Individual Mail: P.O. Box 340, Zip 14034-0340)',
             city='Collins', postal_code='14034-0490'),
    Facility(slug='coxsackie-correctional-facility',
             name='Coxsackie Correctional Facility',
             level='maximum', serves='males',
             street='11260 Route 9W, P.O. Box 200 (Incarcerated Individual Mail: P.O. Box 999, Zip 12051-0999)',
             city='Coxsackie', postal_code='12051-0200'),
    Facility(slug='eastern-ny-correctional-facility',
             name='Eastern NY Correctional Facility',
             level='maximum', serves='males',
             street='30 Institution Rd, P.O. Box 338',
             city='Napanoch', postal_code='12458-0338'),
    Facility(slug='edgecombe-residential-treatment-facility',
             name='Edgecombe Residential Treatment Facility',
             level='minimum', serves='males',
             street='611 Edgecombe Avenue',
             city='New York', postal_code='10032-4398'),
    Facility(slug='elmira-correctional-facility',
             name='Elmira Correctional Facility',
             level='maximum', serves='males',
             street='1879 Davis St, P.O. Box 500',
             city='Elmira', postal_code='14901-0500'),
    Facility(slug='fishkill-correctional-facility',
             name='Fishkill Correctional Facility',
             level='medium', serves='males',
             street='18 Strack Drive, (Incarcerated Individual Mail: 271 Matteawan Road, P.O. Box 1245)',
             city='Beacon', postal_code='12508-0307'),
    Facility(slug='five-points-correctional-facility',
             name='Five Points Correctional Facility',
             level='maximum', serves='males',
             street='6600 State Route 96, Caller Box 400 (Incarcerated Individual Mail: Caller Box 119)',
             city='Romulus', postal_code='14541'),
    Facility(slug='franklin-correctional-facility',
             name='Franklin Correctional Facility',
             level='medium', serves='males',
             street='62 Bare Hill Road , P.O. Box 10',
             city='Malone', postal_code='12953-0010'),
    Facility(slug='gouverneur-correctional-facility',
             name='Gouverneur Correctional Facility',
             level='medium', serves='males',
             street='112 Scotch Settlement Road, P.O. Box 370',
             city='Gouverneur', postal_code='13642-0370'),
    Facility(slug='green-haven-correctional-facility',
             name='Green Haven Correctional Facility',
             level='maximum', serves='males',
             street='594 Rt. 216',
             city='Stormville', postal_code='12582-0010'),
    Facility(slug='greene-correctional-facility',
             name='Greene Correctional Facility',
             level='medium', serves='males',
             street='165 Plank Road, P.O. Box 8 (Incarcerated Individual Mail: P.O. Box 975, Zip 12051-0975)',
             city='Coxsackie', postal_code='12051-0008'),
    Facility(slug='groveland-correctional-facility',
             name='Groveland Correctional Facility',
             level='medium', serves='males',
             street='7000 Sonyea Road, P.O. Box 50',
             city='Sonyea', postal_code='14556-0050'),
    Facility(slug='hale-creek-asactc',
             name='Hale Creek ASACTC',
             level='medium', serves='males',
             street='279 Maloney Road, (Incarcerated Individual Mail: P.O. Box 950)',
             city='Johnstown', postal_code='12095-3769'),
    Facility(slug='hudson-correctional-facility',
             name='Hudson Correctional Facility',
             level='medium', serves='males',
             street='50 East Court Street, P.O. Box 576',
             city='Hudson', postal_code='12534-0576'),
    Facility(slug='lakeview-shock-incarceration-correctional-facility',
             name='Lakeview Shock Incarceration Correctional Facility',
             level='medium', serves='males',
             street='9300 Lake Avenue, P.O. Box T',
             city='Brocton', postal_code='14716-9798'),
    Facility(slug='marcy-correctional-facility',
             name='Marcy Correctional Facility',
             level='medium', serves='males',
             street='9000 Old River Road, P.O. Box 5000 (Incarcerated Individual Mail: P.O. Box 3600)',
             city='Marcy', postal_code='13403-5000'),
    Facility(slug='mid-state-correctional-facility',
             name='Mid-State Correctional Facility',
             level='medium', serves='males',
             street='9005 Old River Road, P. O. Box 216, Incarcerated Individual Mail: P. O. Box 2500',
             city='Marcy', postal_code='13403-0216'),
    Facility(slug='mohawk-correctional-facility',
             name='Mohawk Correctional Facility',
             level='medium', serves='males',
             street='6514 Rt. 26, P.O. Box 8450 (Incarcerated Individual Mail: P.O. Box 8451)',
             city='Rome', postal_code='13442'),
    Facility(slug='orleans-correctional-facility',
             name='Orleans Correctional Facility',
             level='medium', serves='males',
             street='3531 Gaines Basin Road',
             city='Albion', postal_code='14411-9199'),
    Facility(slug='otisville-correctional-facility',
             name='Otisville Correctional Facility',
             level='medium', serves='males',
             street='57 Sanitorium Road',
             city='Otisville', postal_code='10963-0008'),
    Facility(slug='queensboro-correctional-facility',
             name='Queensboro Correctional Facility',
             level='minimum', serves='males',
             street='47-04 Van Dam Street',
             city='Long Island City', postal_code='11101-3081'),
    Facility(slug='riverview-correctional-facility',
             name='Riverview Correctional Facility',
             level='medium', serves='males',
             street='1110 Tibbits Drive, P.O. Box 158',
             city='Ogdensburg', postal_code='13669-0158'),
    Facility(slug='shawangunk-correctional-facility',
             name='Shawangunk Correctional Facility',
             level='maximum', serves='males',
             street='200 Quick Road. P. O. Box 750, Incarcerated Individual Mail: P. O. Box 700',
             city='Wallkill', postal_code='12589-0750'),
    Facility(slug='sing-sing-correctional-facility',
             name='Sing Sing Correctional Facility',
             level='maximum', serves='males',
             street='354 Hunter Street',
             city='Ossining', postal_code='10562-5442'),
    Facility(slug='taconic-correctional-facility',
             name='Taconic Correctional Facility',
             level='medium', serves='females',
             street='250 Harris Road',
             city='Bedford Hills', postal_code='10507-2497'),
    Facility(slug='ulster-correctional-facility',
             name='Ulster Correctional Facility',
             level='medium', serves='males',
             street='750 Berme Road, P.O. Box 800',
             city='Napanoch', postal_code='12458-0800'),
    Facility(slug='upstate-correctional-facility',
             name='Upstate Correctional Facility',
             level='maximum', serves='males',
             street='309 Bare Hill Road, P.O. Box 2000',
             city='Malone', postal_code='12953'),
    Facility(slug='wallkill-correctional-facility',
             name='Wallkill Correctional Facility',
             level='medium', serves='males',
             street='50 McKendrick Road, P.O. Box G',
             city='Wallkill', postal_code='12589-0286'),
    Facility(slug='washington-correctional-facility',
             name='Washington Correctional Facility',
             level='medium', serves='males',
             street='72 Lock Eleven Lane, P.O. Box 180',
             city='Comstock', postal_code='12821-0180'),
    Facility(slug='wende-correctional-facility',
             name='Wende Correctional Facility',
             level='maximum', serves='males',
             street='3040 Wende Road',
             city='Alden', postal_code='14004-1187'),
    Facility(slug='woodbourne-correctional-facility',
             name='Woodbourne Correctional Facility',
             level='medium', serves='males',
             street='99 Prison Road, P.O. Box 1000',
             city='Woodbourne', postal_code='12788-1000'),
    Facility(slug='wyoming-correctional-facility',
             name='Wyoming Correctional Facility',
             level='medium', serves='males',
             street='3203 Dunbar Road, P.O. Box 501',
             city='Attica', postal_code='14011-0501'),
)


BY_NAME: dict[str, Facility] = {f.name: f for f in FACILITIES}
BY_SLUG: dict[str, Facility] = {f.slug: f for f in FACILITIES}

NAMES: tuple[str, ...] = tuple(f.name for f in FACILITIES)


def get(name: str) -> Facility | None:
    """The facility with this exact DOCCS name, or nothing.

    Deliberately exact. A near miss is a name somebody typed, and the whole
    point of the list is that a typed name never becomes a return address.
    """
    return BY_NAME.get((name or "").strip())


def is_known(name: str) -> bool:
    return get(name) is not None


def serving(serves: str) -> tuple[Facility, ...]:
    """Every facility DOCCS operates for this population."""
    return tuple(f for f in FACILITIES if f.serves == serves)


def contradicts(name: str, serves: str) -> bool:
    """Whether this facility is one that does not hold this population.

    Used to catch the failure this module was written for: a record placing
    somebody in a facility that does not hold them. An unknown facility is not
    a contradiction, because there is nothing to contradict; `is_known` is the
    check for that.
    """
    found = get(name)
    if found is None or not serves:
        return False
    return found.serves != serves
