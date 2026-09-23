"""Labelled cases for the classifier.

This file is the accuracy claim. When somebody asks on demo day how we know
the triage is right, the answer is this list plus the edit rate on drafted
letters, not a confident tone of voice.

Add a case whenever a counselor disagrees with the output. That is how the
list earns its keep.
"""

from dataclasses import dataclass

import pytest

from app.triage import (
    AccountHistory,
    Answers,
    BankAccount,
    Collections,
    Obligation,
    Recognition,
    ReportResult,
    State,
    classify,
)


@dataclass(frozen=True)
class Case:
    name: str
    answers: Answers
    expect: State
    expect_review: bool = False


def a(**kw) -> Answers:
    base = dict(
        ever_had_account=AccountHistory.NO,
        report_result=ReportResult.NO_FILE_FOUND,
        collections=Collections.NONE_FOUND,
        has_bank_account=BankAccount.NO,
        obligations=(Obligation.NONE,),
        recognizes_everything=Recognition.NOT_REVIEWED_YET,
    )
    base.update(kw)
    return Answers(**base)


CASES = [
    Case(
        "J. Whitfield from the seeded caseload: no accounts, no file, nothing in "
        "collections, no bank account, restitution of unknown amount",
        a(obligations=(Obligation.RESTITUTION,)),
        State.CREDIT_INVISIBLE,
    ),
    Case(
        "report not pulled yet, so there is nothing to classify",
        a(report_result=ReportResult.NOT_PULLED),
        State.NOT_YET_TRIAGED,
    ),
    Case(
        "unsure about past accounts and no report yet: still nothing to classify",
        a(report_result=ReportResult.NOT_PULLED,
          ever_had_account=AccountHistory.UNSURE),
        State.NOT_YET_TRIAGED,
    ),
    Case(
        "recalls an account but the bureau found no file: flag it, a name or "
        "SSN mismatch can hide a real file",
        a(ever_had_account=AccountHistory.YES),
        State.CREDIT_INVISIBLE,
        expect_review=True,
    ),
    Case(
        "thin file, nothing in collections, everything recognized: boosters",
        a(report_result=ReportResult.THIN_OR_STALE,
          ever_had_account=AccountHistory.YES,
          recognizes_everything=Recognition.ALL_MINE),
        State.THIN_FILE,
    ),
    Case(
        "full clean file, nothing disputed: still the boosters path",
        a(report_result=ReportResult.FULL_FILE,
          ever_had_account=AccountHistory.YES,
          has_bank_account=BankAccount.YES,
          recognizes_everything=Recognition.ALL_MINE),
        State.THIN_FILE,
    ),
    Case(
        "collections present on a thin file: damaged, not thin. Pointing this "
        "client at rent reporting wastes months",
        a(report_result=ReportResult.THIN_OR_STALE,
          collections=Collections.SOME,
          ever_had_account=AccountHistory.YES,
          recognizes_everything=Recognition.ALL_MINE),
        State.DAMAGED_FILE,
    ),
    Case(
        "T. Brennan: full file, nine collections",
        a(report_result=ReportResult.FULL_FILE,
          collections=Collections.MANY,
          ever_had_account=AccountHistory.YES,
          has_bank_account=BankAccount.YES,
          recognizes_everything=Recognition.ALL_MINE),
        State.DAMAGED_FILE,
    ),
    Case(
        "M. Alvarez: two items she does not recognize",
        a(report_result=ReportResult.THIN_OR_STALE,
          ever_had_account=AccountHistory.YES,
          recognizes_everything=Recognition.SOME_NOT_MINE),
        State.ERRORS_PRESENT,
    ),
    Case(
        "errors AND collections: errors win, because only the dispute has a clock",
        a(report_result=ReportResult.FULL_FILE,
          collections=Collections.MANY,
          ever_had_account=AccountHistory.YES,
          recognizes_everything=Recognition.SOME_NOT_MINE),
        State.ERRORS_PRESENT,
    ),
    Case(
        "file exists, collections unknown: counselor reads the report first",
        a(report_result=ReportResult.THIN_OR_STALE,
          collections=Collections.UNKNOWN,
          ever_had_account=AccountHistory.YES,
          recognizes_everything=Recognition.ALL_MINE),
        State.THIN_FILE,
        expect_review=True,
    ),
    Case(
        "file exists, never walked line by line: an error finding is still "
        "possible, so flag it",
        a(report_result=ReportResult.THIN_OR_STALE,
          ever_had_account=AccountHistory.YES),
        State.THIN_FILE,
        expect_review=True,
    ),
]


@pytest.mark.parametrize("case", CASES, ids=[c.name[:48] for c in CASES])
def test_classification(case: Case):
    result = classify(case.answers)
    assert result.state is case.expect, case.name
    assert result.needs_human_review is case.expect_review, case.name


def test_every_state_has_a_path():
    from app.triage import PATH, STATE_LABEL

    for state in State:
        assert state in PATH
        assert state in STATE_LABEL
        assert PATH[state]["first_step"]


def test_errors_jump_the_queue_and_nothing_else_does():
    for case in CASES:
        result = classify(case.answers)
        assert result.jumps_queue is (result.state is State.ERRORS_PRESENT)


def test_restitution_never_lands_on_the_credit_path():
    result = classify(a(obligations=(Obligation.RESTITUTION,)))
    assert result.obligations_route
    assert "obligations list" in result.obligations_route[0]
    # And it does not change the credit classification.
    assert result.state is classify(a()).state


def test_every_result_explains_itself():
    """A classification with no reason attached cannot be argued with, which
    means a counselor cannot correct it."""
    for case in CASES:
        assert classify(case.answers).reasons, case.name


def test_restitution_says_what_it_does_to_credit_rather_than_shrugging():
    """This used to be the app's biggest open question and now it is answered.

    The answer is "no, not by itself", and the reasoning is in the note because
    each step of it could change independently: the 2017 public-record standards
    could be revised, or a county could designate a private collector.
    """
    from app.triage import Answers, Obligation, classify
    from app.triage import AccountHistory, BankAccount, Collections
    from app.triage import Recognition, ReportResult

    result = classify(Answers(
        ever_had_account=AccountHistory.YES,
        report_result=ReportResult.THIN_OR_STALE,
        collections=Collections.NONE_FOUND,
        has_bank_account=BankAccount.YES,
        obligations=(Obligation.RESTITUTION,),
        recognizes_everything=Recognition.ALL_MINE,
    ))
    note = " ".join(result.obligations_route)
    assert "does not by itself reach a credit report" in note
    assert "420.10" in note                 # the New York mechanism
    assert "collector can report it" in note  # and the route that stays open
    assert "open question" not in note


def test_every_restitution_fact_carries_a_primary_source():
    from app.sources import FACTS

    keys = [k for k in FACTS if "restitution" in k]
    assert len(keys) == 3, keys
    for key in keys:
        fact = FACTS[key]
        assert fact.url.startswith("https://"), key
        assert fact.source, key
