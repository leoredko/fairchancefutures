"""Letters, bureaus, and the sourcing rule.

The rule these defend: a dispute goes to all three bureaus, and no legal
sentence ships without a primary source and a date.
"""

from datetime import date

import pytest

from app.bureaus import ANNUAL_REPORT_REQUEST, BUREAUS
from app.letters import (
    ReviewLog,
    dispute_deadline,
    draft_dispute_set,
    draft_report_request,
)
from app.sources import FACTS, OPEN_QUESTIONS


def _set():
    return draft_dispute_set(
        client_id="c1", client_name="M. Alvarez", creditor="Midland Funding",
        last_four="4471", reason="never opened this account",
        today=date(2026, 3, 2),
    )


def test_one_dispute_letter_per_bureau():
    """An item deleted at Equifax is still live at the other two."""
    drafts = _set()
    assert len(drafts) == 3
    assert {d.bureau for d in drafts} == {b.name for b in BUREAUS}


def test_each_letter_carries_that_bureau_own_address():
    for draft in _set():
        bureau = next(b for b in BUREAUS if b.name == draft.bureau)
        assert bureau.address_block in draft.body


def test_no_bureau_address_leaks_into_another_letter():
    for draft in _set():
        for other in BUREAUS:
            if other.name == draft.bureau:
                continue
            assert other.dispute_address[1] not in draft.body


def test_letters_never_carry_the_ssn():
    """It is written by hand on the paper copy. The app never holds it."""
    everything = _set() + [draft_report_request(
        client_id="c1", client_name="M. Alvarez", delivery_address="c/o Rosa")]
    for draft in everything:
        assert "[client writes by hand on the printed copy]" in draft.body


def test_every_dispute_letter_cites_a_checked_source():
    for draft in _set():
        assert draft.citations
        assert any("1681i" in c for c in draft.citations)


def test_the_report_request_goes_to_the_centralized_source_not_a_bureau():
    """One request covers all three, and it is the only route with no internet."""
    draft = draft_report_request(
        client_id="c1", client_name="M. Alvarez", delivery_address="c/o Rosa")
    assert ANNUAL_REPORT_REQUEST.address_block in draft.body
    for bureau in BUREAUS:
        assert bureau.dispute_address[1] not in draft.body


def test_the_deadline_counts_from_receipt_not_from_the_postmark():
    """A client watching the wrong date is the point of getting this right."""
    assert dispute_deadline(date(2026, 3, 2)) == date(2026, 4, 1)


@pytest.mark.parametrize("key", sorted(FACTS))
def test_every_fact_has_a_source_a_url_and_a_date(key):
    fact = FACTS[key]
    assert fact.url.startswith("https://")
    assert fact.source
    assert fact.checked_on <= date.today()
    assert "checked" in fact.cite()


def test_open_questions_are_not_silently_empty():
    """If this list ever empties, somebody deleted the honesty rather than
    doing the research."""
    assert len(OPEN_QUESTIONS) >= 3


def test_edit_rate_is_none_before_any_review():
    log = ReviewLog()
    assert log.edit_rate is None
    assert "No letters reviewed" in log.summary()


def test_the_request_letter_matches_what_a_facility_mail_request_needs():
    """The bureaus ask for a different list from a prison than from a house.
    Getting this wrong means the envelope comes back and three weeks are gone.
    """
    draft = draft_report_request(
        client_id="marcus-w", client_name="Marcus W.",
        delivery_address="c/o Denise", identification="22A1187",
        facility="Sing Sing Correctional Facility",
    )
    body = draft.body

    # The prisoner ID, in the letter and again for the envelope.
    assert body.count("22A1187") >= 2
    assert "Sing Sing Correctional Facility" in body

    # Addresses from BEFORE incarceration, not from the last two years.
    assert "two years preceding incarceration" in body

    # One letter, all three bureaus named.
    for name in ("Equifax", "Experian", "TransUnion"):
        assert name in body

    # And the envelope instruction, which is the part that gets forgotten.
    assert "return address on the envelope must be the correctional" in body


def test_a_request_with_no_din_still_prints_something_usable():
    """A client whose DIN is missing gets a line to write on, not a crash."""
    draft = draft_report_request(
        client_id="x", client_name="A. Person", delivery_address="c/o Someone")
    assert "[client writes by hand]" in draft.body
    assert "[correctional institution]" in draft.body
