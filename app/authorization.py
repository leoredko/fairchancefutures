"""Scoped authorization, and the access ladder.

Constraint two, from the design deck: a helper outside has no standing without
a signed form. No waiver makes that disappear, so it is modeled as data rather
than assumed.

Two ideas live here.

1. An Authorization is a scoped, expiring, revocable grant. Every family-side
   action is checked against one. A helper with no live grant can look at an
   invitation and nothing else.

2. The access ladder. What a bureau demands varies per person and cannot be
   known in advance, so we start at rung 1 and climb only on a kickback. Never
   make everyone pay the cost of the hardest case.
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


class Rung(int, Enum):
    PLAIN_REQUEST = 1
    IDENTITY_DOCUMENTS = 2
    LIMITED_POA = 3
    PROGRAM_RELEASE = 4


RUNG_DETAIL: dict[Rung, dict[str, str]] = {
    Rung.PLAIN_REQUEST: {
        "label": "Plain request",
        "asks_for": "Name, SSN, date of birth, address history. Signed by the client.",
        "cost": "One signature. No notary, no trip, no helper required.",
    },
    Rung.IDENTITY_DOCUMENTS: {
        "label": "Identity documents",
        "asks_for": "Copy of ID, proof of address.",
        "cost": "Sent when a bureau cannot match the file.",
    },
    Rung.LIMITED_POA: {
        "label": "Limited power of attorney",
        "asks_for": "Notarized form, scoped to credit reports and disputes, twelve months.",
        "cost": "A notary trip at the law library. Only when the helper must act alone.",
    },
    Rung.PROGRAM_RELEASE: {
        "label": "Program release",
        "asks_for": "The org's own release form, signed by the client.",
        "cost": "No outside helper at all. Slower, but nothing stops.",
    },
}

POA_TERM_DAYS = 365


@dataclass(frozen=True)
class Authorization:
    """A signed, scoped grant naming one helper for one client."""

    client_id: str
    helper_name: str
    scopes: frozenset[Scope]
    rung: Rung
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
    """What screen 04 actually creates when a helper taps 'Yes, I'll help'.

    Note the rung: 1, not 3. The notarized POA is not the front door. It is
    where we go if a bureau kicks the plain request back.
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
        rung=Rung.PLAIN_REQUEST,
        signed_on=signed_on,
        expires_on=signed_on + timedelta(days=POA_TERM_DAYS),
    )


def next_rung(current: Rung, helper_present: bool) -> Rung | None:
    """Climb one rung after a bureau kickback.

    With no helper outside, rung 3 is meaningless: there is nobody to hold the
    power of attorney. Skip straight to the program release.
    """
    if current is Rung.PLAIN_REQUEST:
        return Rung.IDENTITY_DOCUMENTS
    if current is Rung.IDENTITY_DOCUMENTS:
        return Rung.LIMITED_POA if helper_present else Rung.PROGRAM_RELEASE
    if current is Rung.LIMITED_POA:
        return Rung.PROGRAM_RELEASE
    return None
