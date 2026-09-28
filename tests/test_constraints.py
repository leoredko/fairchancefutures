"""The two constraints, tested.

These two are not assumed away with the rest of the red tape, because no
waiver makes them disappear: a person inside cannot verify identity online,
and a helper outside has no standing without a signed form. `app/surfaces.py`
and `app/authorization.py` enforce them. If these tests ever go green by
accident, the product has quietly become something else.
"""

from datetime import date, timedelta

import pytest

from app.authorization import (
    Authorization,
    STANDING_DETAIL,
    FORBIDDEN_SCOPES,
    NotAuthorized,
    Scope,
    Standing,
    default_helper_authorization,
    require_scope,
)
from app.surfaces import CAPABILITIES, Capability, Surface, SurfaceDenied, can, require


# --- constraint one: the tablet -------------------------------------------

IMPOSSIBLE_FROM_INSIDE = [
    Capability.VERIFY_IDENTITY,
    Capability.RECEIVE_MAIL,
    Capability.UPLOAD_FILE,
    Capability.MAIL_LETTER,
]


@pytest.mark.parametrize("capability", IMPOSSIBLE_FROM_INSIDE)
def test_inside_cannot_do_the_physically_impossible(capability):
    assert not can(Surface.INSIDE, capability)
    with pytest.raises(SurfaceDenied):
        require(Surface.INSIDE, capability)


@pytest.mark.parametrize("capability", IMPOSSIBLE_FROM_INSIDE)
def test_every_denial_explains_itself_in_plain_words(capability):
    with pytest.raises(SurfaceDenied) as caught:
        require(Surface.INSIDE, capability)
    assert len(caught.value.reason) > 40


def test_inside_can_still_do_its_own_job():
    for capability in [Capability.ANSWER_INTAKE, Capability.VIEW_OWN_STATUS,
                       Capability.REVOKE_AUTHORIZATION]:
        require(Surface.INSIDE, capability)


def test_family_never_sees_the_caseload():
    assert not can(Surface.FAMILY, Capability.MANAGE_CASELOAD)
    assert not can(Surface.FAMILY, Capability.READ_FULL_REPORT)
    assert not can(Surface.FAMILY, Capability.APPROVE_LETTER)


def test_no_surface_holds_every_capability():
    """If one ever did, the split that justifies the product would be gone."""
    every = set().union(*CAPABILITIES.values())
    for surface, allowed in CAPABILITIES.items():
        assert set(allowed) != every, surface


# --- constraint two: standing ----------------------------------------------

def test_no_form_means_no_standing():
    with pytest.raises(NotAuthorized):
        require_scope(None, Scope.RECEIVE_MAIL)


def test_a_grant_is_scoped_not_general():
    """A helper signed up to fetch mail has not signed up for everything else."""
    mail_only = Authorization(
        client_id="c1", helper_name="Denise",
        scopes=frozenset({Scope.RECEIVE_MAIL}),
        standing=Standing.SIGNED_FORM,
        signed_on=date.today(),
        expires_on=date.today() + timedelta(days=30),
    )
    require_scope(mail_only, Scope.RECEIVE_MAIL)
    for other in (Scope.SUBMIT_REPORT_IMAGES, Scope.MAIL_DISPUTE_LETTER,
                  Scope.BE_CONTACTED_BY_STAFF):
        with pytest.raises(NotAuthorized):
            require_scope(mail_only, other)


def test_forbidden_scopes_cannot_be_constructed():
    class Sneaky(str):
        pass

    for forbidden in FORBIDDEN_SCOPES:
        with pytest.raises(ValueError):
            Authorization(
                client_id="c1", helper_name="D",
                scopes=frozenset({Sneaky(forbidden)}),
                standing=Standing.SIGNED_FORM,
                signed_on=date.today(),
                expires_on=date.today() + timedelta(days=30),
            )


def test_an_authorization_that_never_expires_is_rejected():
    with pytest.raises(ValueError):
        Authorization(
            client_id="c1", helper_name="D",
            scopes=frozenset({Scope.RECEIVE_MAIL}),
            standing=Standing.SIGNED_FORM,
            signed_on=date.today(),
            expires_on=date.today(),
        )


def test_revocation_takes_effect_immediately():
    auth = default_helper_authorization("c1", "Denise")
    assert auth.permits(Scope.RECEIVE_MAIL)
    revoked = auth.revoked()
    assert not revoked.is_live()
    with pytest.raises(NotAuthorized):
        require_scope(revoked, Scope.RECEIVE_MAIL)


def test_expiry_takes_effect_on_its_own():
    signed = date.today() - timedelta(days=400)
    auth = default_helper_authorization("c1", "Denise", signed)
    assert not auth.is_live()


# --- standing, which is what survived the ladder ---------------------------

def test_a_helper_starts_on_a_signed_form_not_a_notarized_one():
    """Sending somebody to a notary before anybody has established that it is
    needed is how a tool gets abandoned at step one."""
    assert default_helper_authorization("c1", "D").standing is Standing.SIGNED_FORM


def test_there_are_two_kinds_of_standing_because_there_were_only_ever_two():
    """The four-rung ladder modelled what a bureau would demand, which nobody
    publishes. The distinction that is real is whether the helper has to act
    without the client, and that is the only one that earns a notary."""
    assert len(list(Standing)) == 2
    for standing in Standing:
        assert STANDING_DETAIL[standing]["label"]
        assert STANDING_DETAIL[standing]["cost"]


def test_the_ladder_is_gone():
    """Kept as a test so nobody quietly reintroduces it. If a rung is needed
    again, the reason has to be written down somewhere other than here."""
    import app.authorization as authorization

    for name in ("Rung", "RUNG_DETAIL", "next_rung"):
        assert not hasattr(authorization, name), name


def test_no_surface_claims_a_person_inside_cannot_receive_mail():
    """They can. It is opened and inspected, not absent.

    Bridge told an audience that a person inside "does not have a street
    address that receives mail on their behalf". That is false: mail is
    addressed to them at the facility under their commitment name and DIN, and
    DOCCS Directive 4422 governs how it is opened, inspected and delivered. The
    claim was wrong in front of exactly the people who would know.

    What the tablet cannot do is take delivery of a document, which is a fact
    about the device rather than about the mail.
    """
    from app.surfaces import Capability, DENIAL_REASON

    reason = DENIAL_REASON[Capability.RECEIVE_MAIL]
    assert "on their behalf" not in reason
    assert "does not have" not in reason
    assert "receives their own mail" in reason
    # The true reason is named, so deleting the false one did not leave a hole.
    assert "no camera and no scanner" in reason


def test_the_mail_correction_is_a_sourced_fact_like_any_other():
    """A sentence about how mail works inside is a claim about a rule, so it
    carries its primary source like every other one."""
    from app.sources import FACTS

    fact = FACTS["incoming_mail_is_inspected_not_absent"]
    assert "Directive 4422" in fact.source
    assert fact.url.startswith("https://doccs.ny.gov/")
    assert "opened and inspected" in fact.statement


def test_no_surface_claims_a_person_inside_cannot_send_mail():
    """They can, to any person or business.

    The same error as the incoming-mail one, one line down in the same table:
    Bridge said outgoing mail "is handled by a family member, a friend, or the
    program". Directive 4422 IV-B-1 says an incarcerated individual may submit
    correspondence to be sent to any person or business, and they print their
    own return address on it.

    What they need from somebody else is paper and postage, which is a cost and
    not a prohibition. Free postage runs to five one-ounce letters a week, at
    reception only, for four weeks.
    """
    from app.surfaces import Capability, DENIAL_REASON

    reason = DENIAL_REASON[Capability.MAIL_LETTER]
    assert "handled by a family member" not in reason
    assert "they send their own mail" in reason
    assert "postage" in reason


def test_the_capability_table_states_what_bridge_cannot_do_not_what_people_cannot():
    """The failure mode this table kept falling into.

    Twice it described a limit of the application as a limit on the person.
    Both mail capabilities now name the screen, not the human, and both say
    what the person can in fact do.
    """
    from app.surfaces import Capability, DENIAL_REASON

    for capability in (Capability.RECEIVE_MAIL, Capability.MAIL_LETTER,
                       Capability.UPLOAD_FILE):
        reason = DENIAL_REASON[capability]
        assert "screen" in reason, capability


def test_the_tablet_is_not_described_as_continuously_connected():
    """A DOCCS tablet meets a kiosk for 15 minutes a day and nothing else.

    "The tablet is connected and a write lands immediately" was the reason
    given for removing the sync queue and for a service worker that caches
    nothing. Removing the pretend queue was right; the reason was not, and it
    is the premise most of this app's storage behaviour was argued from.
    """
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for rel in ("app/surfaces.py", "app/store.py", "app/main.py",
                "app/static/sw.js"):
        text = (root / rel).read_text()
        assert "the tablet is connected and writes land immediately" not in text.lower(), rel
        assert "loaded onto a connected device and writes go to the server" not in text.lower(), rel


def test_what_the_build_assumes_is_separated_from_what_it_establishes():
    """Two registries, because they answer different questions.

    An open question is something nobody has answered and somebody should. A
    simplification is something the team looked at, decided not to model, and
    carried anyway. Collapsing them would let an assumption read as a finding,
    which is the failure this whole sweep was about.
    """
    from app.sources import FACTS, OPEN_QUESTIONS, SIMPLIFICATIONS

    assert SIMPLIFICATIONS, "a build that assumes nothing is a build nobody checked"
    joined = " ".join(SIMPLIFICATIONS)
    assert "assumes the tablet is online" in joined
    assert "monitored" in joined

    # A simplification is not a fact and not a question.
    statements = {f.statement for f in FACTS.values()}
    for assumed in SIMPLIFICATIONS:
        assert assumed not in statements
        assert assumed not in OPEN_QUESTIONS


def test_the_identity_constraint_is_the_one_device_claim_still_sourced():
    """It is a real constraint the demo shows, not a simplification, so it
    keeps its citation while the operational detail around it went away."""
    from app.sources import FACTS

    fact = FACTS["the_tablet_has_no_internet"]
    assert fact.url.startswith("https://doccs.ny.gov/")
    assert "internet" in fact.statement


def test_a_number_that_gates_the_document_plan_carries_its_source():
    """Ten weeks gates document readiness, so it is a claim about the world
    rather than a design choice, and the rule in CLAUDE.md covers it.

    It is the fast end of the state's ten-to-twelve, which is worth knowing
    before anybody reads a date off it out loud.
    """
    from app.caseplan import BIRTH_CERTIFICATE_WEEKS
    from app.sources import FACTS

    fact = FACTS["birth_certificate_takes_ten_to_twelve_weeks"]
    assert fact.url.startswith("https://www.health.ny.gov/")
    assert str(BIRTH_CERTIFICATE_WEEKS) == "10"
    assert "ten to twelve weeks" in fact.statement


def test_the_two_score_scales_are_sourced_because_a_range_is_a_claim():
    """A person told two different scores has been told the truth twice. That
    is a credit-reporting fact, so it carries a citation."""
    from app.sources import FACTS

    fact = FACTS["fico_ranges_are_not_one_scale"]
    assert "300 to 850" in fact.statement
    assert "250 to 900" in fact.statement
    assert fact.url.startswith("https://www.myfico.com/")
