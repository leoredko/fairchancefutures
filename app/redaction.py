"""Field-level minimization.

The compliance paperwork is assumed away for this build, the same way the
facility approvals are. What is not assumed away is the product behavior:
default deny, per field, per surface, with a named reason the UI can print.

This module used to withhold the Social Security number from the coordinator
as well, which was defending the wrong boundary. The coordinator works inside
the case plan system. They hold the sentence and commitment paperwork, they are
the one who requests the birth certificate, and the vital documents packet sits
in their file. An app that hides a number they are already holding is not
protecting anybody, it is performing.

The boundary that is real is physical. The tablet is issued to one person, so
nobody inherits their session, but it is read in common areas with other people
in line of sight, and it is a vendor device the facility administers and can
inspect. So the tablet never renders a Social Security number, a full account
number or a date of birth, and neither does a helper's phone, because a helper
was promised in the first ten seconds that they would never be asked to handle
those. The coordinator's desk is neither of those places.

Two protections survive that change and are not the same as this one. The
credit report is requested already truncated and masked again on the way in, so
even a coordinator reads XXX-XX-4417 off a scanned report, because that is what
the document itself says. And the printed dispute letter still leaves the
number blank for a pen, not because of what the coordinator knows but because
the envelope travels through the helper's hands.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.surfaces import Surface

# The fields worth naming out loud when a surface does not get them.
SENSITIVE = frozenset({"ssn", "full_account_number", "date_of_birth"})

# Which surfaces must never render them. Physical, not preferential: a screen
# read in common areas and a helper's phone are the two places these cannot
# appear.
# The coordinator's desk already holds the file, so withholding there is
# theater rather than protection.
WITHHELD_FROM: dict[Surface, frozenset[str]] = {
    Surface.INSIDE: SENSITIVE,
    Surface.FAMILY: SENSITIVE,
    Surface.STAFF: frozenset(),
}

# The tablet's rule, kept under its old name so anything still importing it
# gets the strict set rather than silently getting nothing.
NEVER_RENDERED = SENSITIVE

# Fields a surface may see, when consent covers them. Anything not listed is
# denied even to staff.
VISIBLE: dict[Surface, frozenset[str]] = {
    Surface.INSIDE: frozenset({
        "display_name", "release_date", "case_state", "plan_step", "din",
        "helper_first_name", "authorization_summary", "timeline",
        "lesson_progress",
    }),
    Surface.FAMILY: frozenset({
        "client_first_name", "task", "mailing_deadline", "authorization_summary",
    }),
    # The coordinator sees the file they already hold, including the Social
    # Security number a mailed dispute has to carry and the date of birth the
    # bureaus match on. Consent still narrows it: report sharing turned off
    # keeps the report fields out, because that is a decision the client made
    # rather than a boundary the room imposes.
    Surface.STAFF: frozenset({
        "display_name", "release_date", "case_state", "plan_step", "timeline",
        "din", "nysid", "facility",
        "ssn", "date_of_birth", "full_account_number",
        "helper_first_name", "authorization_summary", "flagged_items",
        "report_summary", "collections_count", "last_pulled",
    }),
}

WITHHELD_NOTE = (
    "You already hold this file, so Bridge does not pretend otherwise. What it "
    "does enforce: none of this reaches the tablet in a common area or a "
    "phone outside, and a scanned report stays truncated because that is how "
    "it arrived."
)


# Fields that are plumbing rather than content. They are dropped like anything
# else, but naming them in the "not shared with you" list would bury the real
# answer in noise.
PLUMBING = frozenset({
    "id", "clock", "clock_sort", "needs", "state_label", "case_state",
    "consent_scopes", "consent_recorded_on", "classification", "intake_answers",
    "family_task", "report_pages",
    "lesson_progress", "report_review", "doccs_record", "release_date_source",
    "first_name", "helper_name", "timeline", "plan_step", "release_date",
    "display_name", "authorization_summary", "task", "mailing_deadline",
    "client_first_name", "din", "nysid", "facility",
})


@dataclass(frozen=True)
class Redacted:
    """A client record, already filtered for one surface.

    withheld is the honest list: the sensitive things this surface did not get,
    in words a person would recognize. Internal plumbing is dropped silently.
    """

    fields: dict
    withheld: list[str]

    def __getitem__(self, key: str):
        return self.fields[key]

    def get(self, key: str, default=None):
        return self.fields.get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self.fields


def for_surface(record: dict, surface: Surface, consent_scopes: set[str] | None = None) -> Redacted:
    """Filter a raw client record down to what this surface may render.

    consent_scopes, when given, narrows further: a client who turned report
    sharing off keeps report fields out of the staff view even though the staff
    surface allows them in principle.
    """
    allowed = VISIBLE[Surface(surface)]
    report_fields = {"flagged_items", "report_summary", "collections_count", "last_pulled"}

    kept, withheld = {}, []

    def withhold(key: str) -> None:
        if key not in PLUMBING:
            withheld.append(key)

    denied = WITHHELD_FROM[Surface(surface)]
    for key, value in record.items():
        if key in denied:
            withhold(key)
            continue
        if key not in allowed:
            withhold(key)
            continue
        if (
            consent_scopes is not None
            and key in report_fields
            and "report_sharing" not in consent_scopes
        ):
            withhold(key)
            continue
        kept[key] = value
    return Redacted(fields=kept, withheld=sorted(set(withheld)))
