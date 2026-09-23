"""Scoped authorization.

Constraint two: a helper outside has no standing without a signed form. No
waiver makes that disappear, so it is modeled as data rather than assumed. An
Authorization is a scoped, expiring, revocable grant, checked on every
family-side action, so a client who cancels from the tablet cuts access off at
the next tap. A helper with no live grant can look at an invitation and nothing
else.

This module used to carry a four-rung access ladder as well, modeling what a
bureau would demand and climbing a rung each time one kicked a request back.
It is gone, and it is worth saying why, because it was a lot of code.

It rested on a question nobody can answer. How often a plain signed request
clears is not published by anybody, and Experian asks for an ID copy with every
mailed dispute as standard, which suggests rung one was fiction for at least
one of the three bureaus. A ladder whose first step may not exist is not an
optimization, it is a guess with a state machine around it.

What replaced it is a question that does have an answer, in `app/caseplan.py`:
which documents does this person actually have. That is tracked by their
Offender Rehabilitation Coordinator, reviewed quarterly, and has a real
deadline at 120 days before release. Same shape of decision, grounded in
something checkable instead of something assumed.

The one distinction from the ladder worth keeping is the genuinely different
legal posture of a helper acting alone, which needs a notarized power of
attorney rather than a signature. That is `Standing` below, and it is two
states rather than four because there were only ever two.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum


class Scope(str, Enum):
    """Deliberately narrow. Each one maps to a sentence a helper was shown."""

    RECEIVE_MAIL = "receive_mail"
    SUBMIT_REPORT_IMAGES = "submit_report_images"
    MAIL_DISPUTE_LETTER = "mail_dispute_letter"
    BE_CONTACTED_BY_STAFF = "be_contacted_by_staff"


# Things a helper can never be granted, no matter what anyone signs in this app.
# Screen 04 promises this in the first ten seconds. Keeping the promise is a
# list, checked, not a paragraph.
FORBIDDEN_SCOPES = frozenset({
    "open_account",
    "apply_for_credit",
    "move_money",
    "change_address",
    "view_ssn",
    "view_full_account_numbers",
})


class Standing(str, Enum):
    """What the helper is acting under. Two states, because there are two.

    A helper who carries paper and mails envelopes is doing so alongside the
    client, whose signature is on the request. A helper who has to act when the
    client cannot be reached is doing something else entirely, and that is the
    only situation that earns a notary trip.
    """

    SIGNED_FORM = "signed_form"
    NOTARIZED_POA = "notarized_poa"


STANDING_DETAIL: dict[Standing, dict[str, str]] = {
    Standing.SIGNED_FORM: {
        "label": "Signed form",
        "asks_for": "The client signs the request. The helper receives the "
                    "mail and posts the envelopes.",
        "cost": "One signature. No notary and no trip.",
    },
    Standing.NOTARIZED_POA: {
        "label": "Limited power of attorney",
        "asks_for": "Notarized, scoped to credit reports and disputes, twelve "
                    "months.",
        "cost": "A notary at the law library. Only when the helper has to act "
                "without the client in the room.",
    },
}

POA_TERM_DAYS = 365


@dataclass(frozen=True)
class Authorization:
    """A signed, scoped grant naming one helper for one client."""

    client_id: str
    helper_name: str
    scopes: frozenset[Scope]
    standing: Standing
    signed_on: date
    expires_on: date
    revoked_on: date | None = None

    def __post_init__(self) -> None:
        bad = {s for s in self.scopes if str(getattr(s, "value", s)) in FORBIDDEN_SCOPES}
        if bad:
            raise ValueError(f"scope is never grantable to a helper: {sorted(bad)}")
        if self.expires_on <= self.signed_on:
            raise ValueError("an authorization that never expires is not scoped")

    def is_live(self, on: date | None = None) -> bool:
        on = on or date.today()
        if self.revoked_on is not None and self.revoked_on <= on:
            return False
        return self.signed_on <= on < self.expires_on

    def permits(self, scope: Scope, on: date | None = None) -> bool:
        return self.is_live(on) and scope in self.scopes

    def revoked(self, on: date | None = None) -> "Authorization":
        """Revocation is a new record, not an edit. The client does this from
        the tablet, and does not have to tell the helper first."""
        from dataclasses import replace

        return replace(self, revoked_on=on or date.today())


class NotAuthorized(Exception):
    def __init__(self, scope: Scope, detail: str):
        self.scope = scope
        self.detail = detail
        super().__init__(f"{scope.value}: {detail}")


def require_scope(
    auth: Authorization | None, scope: Scope, on: date | None = None
) -> None:
    if auth is None:
        raise NotAuthorized(scope, "No signed authorization on file for this helper.")
    if auth.revoked_on is not None and auth.revoked_on <= (on or date.today()):
        raise NotAuthorized(scope, "The client revoked this authorization.")
    if not auth.is_live(on):
        raise NotAuthorized(scope, "The authorization has expired or has not started.")
    if scope not in auth.scopes:
        raise NotAuthorized(scope, "The signed form does not cover this action.")


def default_helper_authorization(
    client_id: str, helper_name: str, signed_on: date | None = None
) -> Authorization:
    """What the invitation screen creates when a helper taps 'Yes, I'll help'.

    A signed form, not a notarized one. Sending somebody to a notary before
    anybody has established that it is needed is how a tool gets abandoned at
    step one.
    """
    signed_on = signed_on or date.today()
    return Authorization(
        client_id=client_id,
        helper_name=helper_name,
        scopes=frozenset({
            Scope.RECEIVE_MAIL,
            Scope.SUBMIT_REPORT_IMAGES,
            Scope.MAIL_DISPUTE_LETTER,
            Scope.BE_CONTACTED_BY_STAFF,
        }),
        standing=Standing.SIGNED_FORM,
        signed_on=signed_on,
        expires_on=signed_on + timedelta(days=POA_TERM_DAYS),
    )
