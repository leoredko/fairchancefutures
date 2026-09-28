"""The facility list, and the failure it was written to make unrepresentable.

A facility is the return address on a dispute letter. A closed one prints an
envelope that comes back; one that does not hold this person prints an envelope
announcing that the sender does not know who they are writing about.
"""

from datetime import date

import pytest

from app import facilities, freshness
from app.intake import IntakeProblem, validate


def test_every_facility_carries_the_population_it_holds():
    """This is the field the old free-text box could never have.

    Without it there is nothing to check a record against, which is how a man
    ended up recorded at Bedford Hills.
    """
    for f in facilities.FACILITIES:
        assert f.serves in ("males", "females"), f.name
        assert f.level in ("maximum", "medium", "minimum"), f.name


def test_the_three_facilities_for_women_are_the_three_doccs_operates():
    """Named rather than counted, because the count is what went unnoticed."""
    assert {f.name for f in facilities.serving("females")} == {
        "Albion Correctional Facility",
        "Bedford Hills Correctional Facility",
        "Taconic Correctional Facility",
    }


def test_every_facility_has_an_address_an_envelope_could_reach():
    for f in facilities.FACILITIES:
        assert f.street and f.city and f.postal_code, f.name
        assert len(f.mailing_address) == 3
        assert f.mailing_address[0] == f.name
        assert f.mailing_address[2].startswith(f"{f.city}, NY ")


def test_a_facility_that_closed_is_not_on_the_list():
    """Downstate closed in 2022 and was still in the picker until now.

    It is the specific reason the eight hand-typed names were replaced with the
    DOCCS list rather than extended.
    """
    assert not facilities.is_known("Downstate Correctional Facility")
    assert not facilities.is_known("Great Meadow Correctional Facility")


def test_a_near_miss_is_not_a_match():
    """A name that is nearly right is a name somebody typed."""
    assert facilities.is_known("Sing Sing Correctional Facility")
    assert not facilities.is_known("Sing Sing")
    assert not facilities.is_known("sing sing correctional facility")


def test_a_man_recorded_at_a_facility_for_women_is_a_contradiction():
    assert facilities.contradicts("Bedford Hills Correctional Facility", "males")
    assert facilities.contradicts("Sing Sing Correctional Facility", "females")
    assert not facilities.contradicts("Sing Sing Correctional Facility", "males")


def test_an_unknown_facility_is_not_called_a_contradiction():
    """There is nothing to contradict. `is_known` is the check for that, and
    conflating the two would report one problem as the other."""
    assert not facilities.contradicts("Somewhere Else", "males")
    assert not facilities.contradicts("Sing Sing Correctional Facility", "")


def test_intake_refuses_a_facility_that_is_not_on_the_list():
    with pytest.raises(IntakeProblem) as caught:
        validate(display_name="Test P.", din="28-A-9999", nysid="",
                 facility="Downstate Correctional Facility",
                 release_date="2027-01-01")
    assert caught.value.field == "facility"
    assert "not on the DOCCS list" in str(caught.value)


def test_intake_accepts_a_facility_that_is_on_the_list():
    made = validate(display_name="Test P.", din="28-A-9999", nysid="",
                    facility="Sing Sing Correctional Facility",
                    release_date="2027-01-01")
    assert made.facility == "Sing Sing Correctional Facility"


def test_the_facility_list_is_watched_for_going_stale():
    """DOCCS has closed facilities steadily since 2021, so a list nobody
    re-reads becomes names on envelopes that no longer exist."""
    later = date.fromordinal(facilities.CHECKED.toordinal() + 400)
    kinds = {s.kind for s in freshness.stale(later)}
    assert "facility list" in kinds

    fresh = date.fromordinal(facilities.CHECKED.toordinal() + 10)
    assert "facility list" not in {s.kind for s in freshness.stale(fresh)}
