"""The evidence registry, and the three kinds of evidence in it.

A statute, one practitioner, and thirteen people who have the problem are not
interchangeable, and the registry is only worth having if it keeps them apart.
These tests defend the arithmetic on the survey and the labelling around it.
"""

from app.sources import FACTS, INTERVIEWS, SURVEYS


def test_no_survey_finding_claims_more_people_than_answered():
    for survey in SURVEYS:
        for finding in survey.findings:
            assert 0 <= finding.count <= finding.of, finding.statement


def test_a_finding_counted_out_of_fewer_people_says_so_in_its_own_sentence():
    """A denominator that moves without explanation is how a number stops
    being checkable. One person skipped the question about wanting to see
    their report, so that finding is out of twelve and has to say why."""
    for survey in SURVEYS:
        for finding in survey.findings:
            if finding.of != survey.responses:
                assert "skipped" in finding.statement.lower(), finding.statement


def test_every_survey_says_who_ran_it_and_where():
    for survey in SURVEYS:
        assert survey.who_ran_it.strip()
        assert survey.where.strip()
        assert survey.responses > 0


def test_every_survey_carries_what_it_cannot_carry():
    """Thirteen people in one Maine facility cannot speak for a DOCCS
    population, and a finding shown without that line invites somebody to
    think it does."""
    for survey in SURVEYS:
        assert survey.limitations, survey.key
        assert any("Maine" in line for line in survey.limitations)


def test_a_survey_finding_cites_its_count_when_it_is_quoted():
    for survey in SURVEYS:
        for finding in survey.findings:
            cited = finding.cite()
            assert f"{finding.count} of {finding.of}" in cited


def test_field_evidence_is_not_mixed_into_the_legal_registry():
    """A survey answer is not a primary source and must never become one.
    FACTS is what the app is allowed to state as law; surveys live apart."""
    keys = set(FACTS)
    for survey in SURVEYS:
        assert survey.key not in keys


def test_the_practitioner_interview_is_still_labelled_as_an_interview():
    who = [i["who"] for i in INTERVIEWS if isinstance(i, dict)]
    assert any("FinEquity" in name for name in who)
