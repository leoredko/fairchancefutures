"""Surface capabilities.

Constraint one: a person inside cannot verify identity online, receive mail,
upload a file, or browse out to a bureau. That is not a policy we chose and it
is not a setting. It is where the tablet physically sits.

The tablet is not offline. Bridge is loaded onto it and reaches the person's
own record, which is why intake saves as it goes and why the course keeps a
person's place. What it cannot do is reach out to the open web, which is the
part that matters here: every route a bureau offers a free citizen runs through
a web page, and none of those pages are reachable from this device.

So capability lives here, in one table, and the router asks this module before
it does anything. Hiding a button in a template is decoration. This is the
enforcement.
"""

from __future__ import annotations

from enum import Enum


class Surface(str, Enum):
    INSIDE = "inside"       # facility tablet, offline-first, metered
    FAMILY = "family"       # helper's phone or laptop
    STAFF = "staff"         # caseworker desktop


class Capability(str, Enum):
    ANSWER_INTAKE = "answer_intake"
    VIEW_OWN_STATUS = "view_own_status"
    VIEW_LESSON = "view_lesson"
    REVOKE_AUTHORIZATION = "revoke_authorization"
    NAME_HELPER = "name_helper"

    VERIFY_IDENTITY = "verify_identity"
    RECEIVE_MAIL = "receive_mail"
    UPLOAD_FILE = "upload_file"
    MAIL_LETTER = "mail_letter"

    TRIAGE_CLIENT = "triage_client"
    READ_FULL_REPORT = "read_full_report"
    APPROVE_LETTER = "approve_letter"
    MANAGE_CASELOAD = "manage_caseload"


# Read this as the product spec. Anything not listed is denied.
CAPABILITIES: dict[Surface, frozenset[Capability]] = {
    Surface.INSIDE: frozenset({
        Capability.ANSWER_INTAKE,
        Capability.VIEW_OWN_STATUS,
        Capability.VIEW_LESSON,
        Capability.REVOKE_AUTHORIZATION,
        Capability.NAME_HELPER,
    }),
    Surface.FAMILY: frozenset({
        Capability.VERIFY_IDENTITY,
        Capability.RECEIVE_MAIL,
        Capability.UPLOAD_FILE,
        Capability.MAIL_LETTER,
    }),
    Surface.STAFF: frozenset({
        Capability.TRIAGE_CLIENT,
        Capability.READ_FULL_REPORT,
        Capability.APPROVE_LETTER,
        Capability.MANAGE_CASELOAD,
        Capability.VERIFY_IDENTITY,
        Capability.RECEIVE_MAIL,
        Capability.UPLOAD_FILE,
        Capability.MAIL_LETTER,
    }),
}

# Why a capability is missing from INSIDE, in words a demo audience understands.
# Every one of these is physics or law, not a preference we could toggle.
DENIAL_REASON: dict[Capability, str] = {
    Capability.VERIFY_IDENTITY:
        "No identity verification happens on a facility tablet. The tablet is "
        "connected, but only to the applications loaded onto it: there is no "
        "open web, so a bureau's knowledge-based authentication page cannot be "
        "reached, and there is no camera roll and no document scanner to "
        "answer it with.",
    Capability.RECEIVE_MAIL:
        "Credit reports arrive on paper, to a street address. A person inside "
        "does not have one that receives mail on their behalf.",
    Capability.UPLOAD_FILE:
        "The tablet cannot take or send a file. This is why the family surface "
        "exists at all.",
    Capability.MAIL_LETTER:
        "Outgoing mail is handled by a family member, a friend, or the program, "
        "never from "
        "this screen.",
    Capability.READ_FULL_REPORT:
        "Full report contents are staff-side. The client sees findings and "
        "approves what is said about them, which is a different thing.",
    Capability.APPROVE_LETTER:
        "A dispute letter is approved by the counselor who holds the deadline.",
    Capability.TRIAGE_CLIENT: "Triage is a 30 to 45 minute staff session.",
    Capability.MANAGE_CASELOAD: "Caseload belongs to the counselor.",
}


class SurfaceDenied(Exception):
    """Raised when a surface reaches for something it structurally cannot do."""

    def __init__(self, surface: Surface, capability: Capability):
        self.surface = surface
        self.capability = capability
        self.reason = DENIAL_REASON.get(
            capability, "This surface does not have that capability."
        )
        super().__init__(
            f"{surface.value} cannot {capability.value}: {self.reason}"
        )


def can(surface: Surface, capability: Capability) -> bool:
    return capability in CAPABILITIES[Surface(surface)]


def require(surface: Surface, capability: Capability) -> None:
    if not can(surface, capability):
        raise SurfaceDenied(Surface(surface), Capability(capability))
