"""The two constraints, tested.

The deck is explicit that these are not assumed away with the rest of the red
tape: a person inside cannot verify identity online, and a helper outside has
no standing without a signed form. If these tests ever go green by accident,
the product has quietly become something else.
"""

from datetime import date, timedelta

import pytest

from app.authorization import (
    Authorization,
    FORBIDDEN_SCOPES,
    NotAuthorized,
    Rung,
    Scope,
    default_helper_authorization,
    next_rung,
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
        rung=Rung.PLAIN_REQUEST,
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
                rung=Rung.PLAIN_REQUEST,
                signed_on=date.today(),
                expires_on=date.today() + timedelta(days=30),
            )


def test_an_authorization_that_never_expires_is_rejected():
    with pytest.raises(ValueError):
        Authorization(
            client_id="c1", helper_name="D",
            scopes=frozenset({Scope.RECEIVE_MAIL}),
            rung=Rung.PLAIN_REQUEST,
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


# --- the ladder ------------------------------------------------------------

def test_the_ladder_starts_at_the_cheapest_rung():
    """Never make everyone pay the cost of the hardest case."""
    assert default_helper_authorization("c1", "D").rung is Rung.PLAIN_REQUEST


def test_the_ladder_climbs_one_rung_at_a_time():
    assert next_rung(Rung.PLAIN_REQUEST, helper_present=True) is Rung.IDENTITY_DOCUMENTS
    assert next_rung(Rung.IDENTITY_DOCUMENTS, helper_present=True) is Rung.LIMITED_POA
    assert next_rung(Rung.LIMITED_POA, helper_present=True) is Rung.PROGRAM_RELEASE
    assert next_rung(Rung.PROGRAM_RELEASE, helper_present=True) is None


def test_no_helper_skips_the_poa_rung():
    """A power of attorney with nobody to hold it is a notary trip for nothing."""
    assert next_rung(Rung.IDENTITY_DOCUMENTS, helper_present=False) is Rung.PROGRAM_RELEASE
