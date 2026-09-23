"""Field-level minimization.

The compliance paperwork is assumed away for this build, the same way the
facility approvals are. What is not assumed away is the product behavior: a
caseworker approving a dispute letter sees the two flagged items and not the
Social Security number, the full account numbers, the address history or the
employer records.

Screen 09 puts that on the slide. This module is what makes the slide true.
Default deny, per field, per surface, with a named reason the UI can print.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.surfaces import Surface

# Fields nobody sees through this app, on any surface, ever. The dispute letter
# leaves a blank line and the client writes the number by hand on the printed
# copy. That is not a limitation, it is the design.
NEVER_RENDERED = frozenset({"ssn", "full_account_number", "date_of_birth"})

# Fields a surface may see, when consent covers them. Anything not listed is
# denied even to staff.
VISIBLE: dict[Surface, frozenset[str]] = {
    Surface.INSIDE: frozenset({
        "display_name", "release_date", "case_state", "plan_step", "din",
        "helper_first_name", "authorization_summary", "timeline",
    }),
    Surface.FAMILY: frozenset({
        "client_first_name", "task", "mailing_deadline", "authorization_summary",
    }),
    Surface.STAFF: frozenset({
        "display_name", "release_date", "case_state", "plan_step", "timeline",
        "din", "nysid", "facility",
        "helper_first_name", "authorization_summary", "flagged_items",
        "report_summary", "collections_count", "last_pulled", "ladder_status",
    }),
}

WITHHELD_NOTE = (
    "Full account numbers, SSN, address history, employer records. You see "
    "what you need to act. Nothing else."
)


# Fields that are plumbing rather than content. They are dropped like anything
# else, but naming them in the "not shared with you" list would bury the real
# answer in noise.
PLUMBING = frozenset({
    "id", "clock", "clock_sort", "needs", "state_label", "case_state",
    "consent_scopes", "consent_recorded_on", "classification", "intake_answers",
    "ladder_rung", "ladder_status", "family_task", "report_pages", "lesson",
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

    for key, value in record.items():
        if key in NEVER_RENDERED:
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
