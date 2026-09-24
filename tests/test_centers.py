"""What the counseling registry promises, and what it refuses to promise."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app import bureaus, centers, freshness, sources


def test_every_center_carries_a_source_and_a_date_somebody_looked():
    # Same rule the legal facts live under. An address with no provenance is
    # the thing this registry exists to avoid.
    for center in centers.CENTERS + centers.COMING:
        assert center.url.startswith("https://"), center.key
        assert center.source, center.key
        assert isinstance(center.checked_on, date), center.key


def test_a_county_with_no_center_gets_nothing_rather_than_the_nearest_city():
    # Sending somebody two hundred miles because the list looked empty is the
    # failure mode here, so the honest answer is no answer.
    assert centers.for_county("Erie") is None
    assert centers.for_county("Clinton") is None
    assert centers.for_county("Franklin") is None


def test_the_five_new_york_city_counties_all_resolve():
    for county in ("Bronx", "Kings", "New York", "Queens", "Richmond"):
        found = centers.for_county(county)
        assert found is not None, county
        assert found.key == "nyc"


def test_a_county_resolves_whatever_case_or_suffix_it_arrives_in():
    # A release plan may say "Monroe County" or "monroe". Both are the county.
    for spelling in ("Monroe", "monroe", "MONROE", "Monroe County",
                     "  monroe county  "):
        found = centers.for_county(spelling)
        assert found is not None, spelling
        assert found.key == "rochester"


def test_an_empty_county_resolves_to_nothing_rather_than_the_first_row():
    assert centers.for_county("") is None
    assert centers.for_county("   ") is None
    assert centers.opening_in("") is None


def test_buffalo_is_reported_as_opening_rather_than_as_open():
    # A city building one is a different answer from a city with none, and
    # neither of them is an address a person should travel to.
    assert centers.for_county("Erie") is None
    coming = centers.opening_in("Erie")
    assert coming is not None
    assert coming.key == "buffalo"
    assert "Do not send anybody" in coming.note


def test_an_entry_nobody_read_from_the_source_is_flagged_as_such():
    # Rochester's site refuses automated fetching and Mount Vernon's wording
    # was never read, so both have to announce that rather than look checked.
    unread = {c.key for c in centers.needs_a_human_read()}
    assert "rochester" in unread
    assert "mount-vernon" in unread
    assert "nyc" not in unread


def test_an_eligibility_sentence_is_left_blank_rather_than_guessed():
    # Who qualifies cannot be inferred from the fact that a center exists.
    mount_vernon = next(c for c in centers.CENTERS if c.key == "mount-vernon")
    assert mount_vernon.eligibility == ""
    assert not mount_vernon.verified_by_hand


def test_a_center_a_person_can_be_sent_to_says_who_qualifies_and_how_to_book():
    for center in centers.CENTERS:
        if not center.verified_by_hand:
            continue
        assert center.eligibility, center.key
        assert center.booking, center.key


def test_nothing_in_the_registry_is_fetched_at_import_time():
    # The city's data is read by a script a person runs, never by the app.
    source = (centers.__file__ and open(centers.__file__).read()) or ""
    for forbidden in ("urllib", "requests", "httpx", "socket"):
        assert forbidden not in source


# ---------------------------------------------------------------- freshness


def test_nothing_is_stale_on_the_day_everything_was_checked():
    assert freshness.stale(today=sources.CHECKED) == ()


def test_an_address_goes_stale_sooner_than_a_statute():
    # A statute that moved is usually still roughly right. An address that
    # moved sends somebody to a locked door.
    assert freshness.ADDRESS_WINDOW < freshness.STATUTE_WINDOW


def test_a_bureau_address_is_flagged_once_it_passes_six_months():
    day = bureaus.CHECKED + freshness.ADDRESS_WINDOW + timedelta(days=1)
    flagged = freshness.stale(today=day)
    kinds = {s.kind for s in flagged}
    assert "bureau address" in kinds
    assert {s.key for s in flagged if s.kind == "bureau address"} == {
        b.key for b in bureaus.BUREAUS}


def test_a_statute_is_not_flagged_at_six_months_but_is_at_a_year():
    six_months = sources.CHECKED + freshness.ADDRESS_WINDOW + timedelta(days=1)
    assert not [s for s in freshness.stale(today=six_months) if s.kind == "fact"]

    a_year = sources.CHECKED + freshness.STATUTE_WINDOW + timedelta(days=1)
    assert [s for s in freshness.stale(today=a_year) if s.kind == "fact"]


def test_a_center_is_flagged_on_the_same_clock_as_a_bureau_address():
    day = centers.CHECKED + freshness.ADDRESS_WINDOW + timedelta(days=1)
    flagged = {s.key for s in freshness.stale(today=day)
               if s.kind == "counseling center"}
    assert flagged == {c.key for c in centers.CENTERS + centers.COMING}


def test_the_most_overdue_entry_is_reported_first():
    # The question somebody actually has is what to re-check first.
    day = sources.CHECKED + timedelta(days=800)
    rows = freshness.stale(today=day)
    assert len(rows) > 1
    assert [r.days_over for r in rows] == sorted(
        (r.days_over for r in rows), reverse=True)


def test_the_report_names_the_unread_entries_whatever_their_date_says():
    # A fresh date on something nobody read is the trap this closes.
    text = freshness.report(today=centers.CHECKED)
    assert "Nothing is past its window" in text
    assert "never read from the source" in text
    assert "Rochester" in text


@pytest.mark.parametrize("kind", ["fact", "bureau address", "counseling center"])
def test_every_registry_with_a_check_date_is_covered_by_the_sweep(kind):
    # The point of one function is that adding a fourth registry and forgetting
    # to wire it in is the bug. This fails if a kind stops being reported.
    day = sources.CHECKED + timedelta(days=800)
    assert any(s.kind == kind for s in freshness.stale(today=day))


def test_a_staleness_line_says_what_to_look_at_and_where():
    day = sources.CHECKED + timedelta(days=800)
    line = freshness.stale(today=day)[0].line()
    assert "last checked" in line
    assert "https://" in line
