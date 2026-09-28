"""Surface capabilities.

Constraint one: a person inside cannot verify identity online, take delivery of
a document, upload a file, or browse out to a bureau. That is not a policy we
chose and it is not a setting. It is where the tablet physically sits.

Say what the constraint is, and do not overstate it. This module used to claim
a person inside has no address that receives mail on their behalf. That is
false, and it is the kind of false a room full of counselors catches: people
inside receive their own mail, addressed to them at the facility under their
commitment name and DIN, opened and inspected but not generally read, and not
held more than 48 hours. See `incoming_mail_is_inspected_not_absent` in
`app.sources`. What the tablet cannot do is take delivery of a document. Paper
reaches a person's hands and stops there, because there is no camera and no
scanner on this surface, which is a fact about the device and not about the
mail.

Connectivity, and what this build assumes about it. Bridge treats the tablet as
online: a write lands when it is made, intake saves as it goes, the course
keeps a person's place. Real access is more limited than that and everything on
it is monitored, so a deployment would need the app shell cached and writes
replayed later. That is a stated assumption rather than a discovery, it is in
`SIMPLIFICATIONS` in `app.sources`, and it is not worth re-arguing here.

What is not an assumption: the device does not reach the open web, so no route
a bureau offers a free citizen is reachable from it. Every one of them runs
through a web page. See `the_tablet_has_no_internet`.

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
    # The one claim in this table that was right. Now sourced, so it stops
    # being an assertion: the vendor network "will not allow access to the
    # internet". See `the_tablet_has_no_internet` in app.sources.
    Capability.VERIFY_IDENTITY:
        "No identity verification happens on a facility tablet. The vendor "
        "network the tablet runs on does not reach the internet, so a bureau's "
        "knowledge-based authentication page cannot be opened, and there is no "
        "camera roll and no document scanner to answer it with.",
    Capability.RECEIVE_MAIL:
        "A credit report arrives on paper. The person receives their own mail "
        "at the facility and can hold that paper, but this screen cannot take "
        "delivery of a document: there is no camera and no scanner on the "
        "tablet, so paper in a person's hands does not become a record in "
        "their case file from here.",
    Capability.UPLOAD_FILE:
        "Bridge does not take a file from this screen, and does not put a "
        "camera on it. A report reaches the case file through the coordinator, "
        "who scans it at their desk, or through the person helping outside. "
        "The person inside reads; they never send.",
    Capability.MAIL_LETTER:
        "Bridge cannot print or post a letter from this screen. The person "
        "can: they send their own mail, to any person or business, with their "
        "own return address on it. What they need from somebody else is the "
        "paper and the postage.",
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
