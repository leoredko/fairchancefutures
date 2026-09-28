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
