"""Human labels for machine names.

Internal keys are snake_case because that is what Python wants. None of them
should ever reach a screen. Before this module, the client detail page listed
what staff could not see as `ssn` and `full_account_number`, sitting next to
carefully written sentences, which makes the whole page look unfinished and
makes a reader wonder what else was left half done.

The house style, applied everywhere:

  Sentence case for labels and headings. "Where you stand", not "Where You
  Stand" and not "where you stand".

  Proper nouns keep their capitals: Equifax, Experian, TransUnion, New York,
  Social Security. So do the initialisms people actually use: DIN, NYSID, SSN,
  PIN, POA, ID.

  No underscores, no camelCase, no raw keys, ever.
"""

from __future__ import annotations

# Fields, as a person would name them.
FIELD: dict[str, str] = {
    "ssn": "Social Security number",
    "full_account_number": "Full account numbers",
    "date_of_birth": "Date of birth",
    "report_summary": "Report summary",
    "flagged_items": "Flagged items",
    "collections_count": "Collections",
    "last_pulled": "Date the report was pulled",
    "address_history": "Address history",
    "employer_records": "Employer records",
    "display_name": "Name",
    "release_date": "Release date",
    "din": "DIN",
    "nysid": "NYSID",
    "facility": "Facility",
    "housing_facility": "Facility",
    "date_received_original": "Date first received",
    "date_received_current": "Date received here",
    "earliest_release_date": "Earliest release date",
    "parole_eligibility_date": "Parole eligibility date",
    "conditional_release_date": "Conditional release date",
    "maximum_expiration_date": "Maximum expiration date",
    "post_release_supervision_max_expiration_date":
        "Post-release supervision ends",
}

# What a surface can and cannot do, in words rather than enum values.
CAPABILITY: dict[str, str] = {
    "answer_intake": "Answer the intake questions",
    "view_own_status": "See where their case stands",
    "view_lesson": "Work through a lesson",
    "revoke_authorization": "Cancel a helper's authorization",
    "name_helper": "Name someone to help",
    "verify_identity": "Verify identity online",
    "receive_mail": "Receive mail",
    "upload_file": "Upload a file",
    "mail_letter": "Mail a letter",
    "triage_client": "Run a triage session",
    "read_full_report": "Read the full credit report",
    "approve_letter": "Approve a letter before it is sent",
    "manage_caseload": "Manage a caseload",
}

# What a helper is granted, and what nobody is ever granted.
SCOPE: dict[str, str] = {
    "receive_mail": "Receive the mail",
    "submit_report_images": "Add photos of the reports",
    "mail_dispute_letter": "Mail a letter we print",
    "be_contacted_by_staff": "Be contacted by the counselor",
    "open_account": "Open an account",
    "apply_for_credit": "Apply for credit",
    "move_money": "Move money",
    "change_address": "Change the address on file",
    "view_ssn": "See the Social Security number",
    "view_full_account_numbers": "See full account numbers",
}

# Device names, for the role cards.
DEVICE: dict[str, str] = {
    "inside": "Facility tablet",
    "family": "Phone",
    "staff": "Desktop",
}

ROLE: dict[str, str] = {
    "inside": "Inside",
    "family": "Family or friend",
    "staff": "Caseworker",
}


def _fallback(key: str) -> str:
    """Last resort for a key nobody has written a label for.

    Sentence case with the underscores gone. Still not good enough to ship, but
    better than printing a column name, and obvious enough in review that
    somebody adds the real label.
    """
    words = str(key).replace("_", " ").strip()
    return words[:1].upper() + words[1:] if words else ""


def field(key: str) -> str:
    return FIELD.get(key, _fallback(key))


def capability(key: str) -> str:
    return CAPABILITY.get(getattr(key, "value", key), _fallback(key))


def scope(key: str) -> str:
    return SCOPE.get(getattr(key, "value", key), _fallback(key))


def device(role: str) -> str:
    return DEVICE.get(getattr(role, "value", role), _fallback(role))


def role(name: str) -> str:
    return ROLE.get(getattr(name, "value", name), _fallback(name))


def fields(keys) -> list[str]:
    return [field(k) for k in keys]
