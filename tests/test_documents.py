"""Document readiness, which replaced the access ladder.

The ladder modelled what a credit bureau would demand and climbed a rung each
time one pushed back. Nobody publishes how often the cheapest route clears, and
Experian asks for an ID copy with every mailed dispute regardless, so the first
step may never have existed.

What is defended here is the thing that replaced it: a chain that is knowable,
already tracked quarterly by the coordinator, and with a real deadline on it.
"""

from datetime import date, timedelta

from app.caseplan import (
    SSN_CARD_TRIGGER_DAYS,
    Document,
    document_readiness,
    simulated_plan,
)


def _plan(**documents):
    return simulated_plan(
        "c1", "D. Reyes", (date.today() + timedelta(days=200)).isoformat(),
        documents={d.value: documents.get(d.name.lower(), False) for d in Document},
    )


def test_the_id_is_blocked_until_both_documents_are_on_file():
    """Order of operations, from the DOCCS legislative report: the birth
    certificate and the Social Security card have to be on file before the
    non-driver ID application can be submitted at all."""
    neither = _plan()
    out = document_readiness(neither, date.today() + timedelta(days=200))
    assert not out["ready"]
    assert Document.BIRTH_CERTIFICATE in out["blocking"]
    assert Document.SOCIAL_SECURITY_CARD in out["blocking"]

    both = _plan(birth_certificate=True, social_security_card=True)
    assert document_readiness(both, date.today() + timedelta(days=200))["ready"]


def test_the_photo_id_itself_does_not_block_the_application():
    """It is the output of the chain, not an input to it."""
    ready = _plan(birth_certificate=True, social_security_card=True)
    out = document_readiness(ready, date.today() + timedelta(days=200))
    assert out["ready"]
    assert not out["has_photo_id"]


def test_the_social_security_card_becomes_overdue_at_120_days():
    """The one deadline in this product that belongs to the person rather than
    to a bureau or a coordinator."""
    plan = _plan(birth_certificate=True)
    release = date.today() + timedelta(days=SSN_CARD_TRIGGER_DAYS - 1)
    out = document_readiness(plan, release)
    assert out["past_ssn_trigger"]
    assert any("overdue" in line for line in out["urgent"])


def test_before_the_120_day_mark_it_is_not_yet_shouting():
    plan = _plan(birth_certificate=True)
    release = date.today() + timedelta(days=SSN_CARD_TRIGGER_DAYS + 60)
    out = document_readiness(plan, release)
    assert not out["past_ssn_trigger"]
    assert not any("overdue" in line for line in out["urgent"])


def test_the_birth_certificate_is_urgent_whatever_the_date():
    """It has no deadline of its own, which is why it gets left, and it takes
    ten weeks or more while blocking everything downstream."""
    plan = _plan(social_security_card=True)
    far_off = document_readiness(plan, date.today() + timedelta(days=900))
    assert any("weeks" in line for line in far_off["urgent"])


def test_being_born_outside_new_york_is_called_out_rather_than_discovered_late():
    """The no-fee route runs on New York records. Somebody born in Ohio or
    Jamaica gets nothing from it, and theirs is slower and costs money."""
    plan = _plan(social_security_card=True)
    release = date.today() + timedelta(days=300)

    in_state = document_readiness(plan, release, born_in_new_york=True)
    out_of_state = document_readiness(plan, release, born_in_new_york=False)

    assert not any("outside New York" in line for line in in_state["urgent"])
    assert any("outside New York" in line for line in out_of_state["urgent"])


def test_somebody_who_already_has_the_certificate_is_not_warned_about_it():
    plan = _plan(birth_certificate=True, social_security_card=True)
    out = document_readiness(plan, date.today() + timedelta(days=300),
                             born_in_new_york=False)
    assert out["urgent"] == []
    assert out["ready"]
