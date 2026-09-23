"""Question definitions for both intake surfaces.

Two sets, and the split between them is the whole point.

The tablet asks what a person knows about their own life. The staff screen asks
that plus one thing nobody inside can answer: what the bureau actually sent
back. A client cannot pull their own report from a facility tablet, so the
field that decides the classification is structurally staff-side. The
capability table is not a UI preference, it shows up here as a missing question.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Option:
    value: str
    label: str
    note: str = ""


@dataclass(frozen=True)
class Question:
    index: int
    field: str
    prompt: str
    options: tuple[Option, ...]
    helper: str = ""
    design_note: str = ""
    constraint: str = ""
    reassurance: dict | None = None
    multi: bool = False


OFFLINE_NOTE = {
    "title": "Nothing here needs the internet.",
    "body": "Your answers save on the tablet and sync whenever it connects. "
            "Nothing is lost if you lose access for a week.",
}


# The tablet asks what a person knows before it asks what they have. Somebody
# who has never seen a credit report is not served by a form that assumes they
# have; and the two questions that open this flow are the ones most people can
# actually answer honestly.
INSIDE_QUESTIONS: tuple[Question, ...] = (
    Question(
        index=1,
        field="knows_score",
        prompt="Do you know what your credit score is?",
        helper="Most people don't. There is no wrong answer here.",
        options=(
            Option("no", "No"),
            Option("roughly", "Roughly, but not exactly"),
            Option("yes", "Yes"),
        ),
        design_note="starting with what somebody knows rather than what they "
                    "have. A form that assumes you have seen a credit report "
                    "is useless to somebody who never has.",
        reassurance=OFFLINE_NOTE,
    ),
    Question(
        index=2,
        field="knows_how",
        prompt="Do you know how to find out?",
        helper="Again, no wrong answer. Most people outside don't either.",
        options=(
            Option("no", "No"),
            Option("some_idea", "I have some idea"),
            Option("yes", "Yes"),
        ),
        design_note="the answer to this decides how much explaining the next "
                    "screen does. It is the only question here whose purpose "
                    "is teaching rather than triage.",
    ),
    Question(
        index=3,
        field="ever_had_account",
        prompt="Have you ever had a credit card, loan, or account in your name?",
        helper="Before you came in counts. A guess is fine, the report settles it.",
        options=(
            Option("yes", "Yes, at some point"),
            Option("no", "No, never"),
            Option("unsure", "I'm not sure"),
        ),
        design_note="one question per screen, large targets. Facility tablets "
                    "are slow, shared, and often metered by the minute.",
        constraint="no camera and no identity check on this surface. The "
                   "reports come back on paper and the coordinator scans them.",
    ),
    Question(
        index=4,
        field="has_bank_account",
        prompt="Do you have a bank account right now?",
        helper="Open, closed, frozen, joint with someone. Any of it is a yes.",
        options=(
            Option("yes", "Yes"),
            Option("no", "No"),
        ),
        design_note="this decides whether the first step is opening an account "
                    "or using one. It is not a blocker either way.",
    ),
    Question(
        index=5,
        field="collections",
        prompt="Is anyone chasing you for money you owe?",
        helper="A collector, a hospital, an old landlord. Not court fines, "
               "those are next.",
        options=(
            Option("none_found", "Not that I know of"),
            Option("some", "One or two"),
            Option("many", "More than a few"),
            Option("unknown", "I have no idea"),
        ),
        design_note="'I have no idea' is a real answer and the most common "
                    "one. Forcing a guess produces bad data and a worse path.",
    ),
    Question(
        index=6,
        field="obligations",
        prompt="Do you owe anything the court ordered?",
        helper="Restitution, child support, fines and fees. Pick all that apply.",
        multi=True,
        options=(
            Option("none", "None that I know of"),
            Option("restitution", "Restitution"),
            Option("child_support", "Child support"),
            Option("court_fines", "Court fines or fees"),
        ),
        design_note="these route to the obligations list, never to the credit "
                    "path. They matter, and they do not sit in a list "
                    "pretending to be a credit card.",
    ),
)

# Shown after question 2, and written to match the answer given there. Somebody
# who said they know how this works does not need the long version.
def teaching_for(knows_how: str | None) -> dict:
    short = knows_how == "yes"
    return {
        "headline": ("Here is the part most people have not been told."
                     if not short else "Quick confirmation, then we start."),
        "points": [
            {
                "title": "You can get all three reports free, by mail",
                "body": "One letter to one address covers Equifax, Experian "
                        "and TransUnion. No internet, no phone, no fee. We "
                        "fill it in and your coordinator sends it.",
            },
            {
                "title": "You can have your Social Security number blacked out",
                "body": "You can require them to leave out the first five "
                        "digits of your Social when they send your own file. "
                        "That is the law, not a favour, and it is why you can "
                        "read the report on this tablet at all.",
            },
            {
                "title": "It may not come with a score, and that is normal",
                "body": "A free report has to show your file. It does not have "
                        "to show a number. What matters here is what is on the "
                        "file, not the number somebody puts on it.",
            },
            {
                "title": "When it arrives, bring it to your coordinator",
                "body": "The reports come back on paper. Your coordinator "
                        "scans them into your record, and then you can read "
                        "them right here.",
            },
        ] if not short else [
            {
                "title": "One letter, all three bureaus, free",
                "body": "We fill it in and your coordinator sends it.",
            },
            {
                "title": "Your Social will be blacked out",
                "body": "We ask them to leave out the first five digits, which "
                        "the law lets you require.",
            },
            {
                "title": "Bring the paper to your coordinator",
                "body": "They scan it in and then you can read it here.",
            },
        ],
    }


# The staff form. Same six fields, plus the one the tablet cannot know.
@dataclass(frozen=True)
class StaffQuestion:
    field: str
    prompt: str
    options: tuple[Option, ...]
    multi: bool = False


STAFF_QUESTIONS: tuple[StaffQuestion, ...] = (
    StaffQuestion("ever_had_account", "Any account in your name, ever?", (
        Option("no", "Not that he knows of"),
        Option("yes", "Yes"),
        Option("unsure", "Unsure"),
    )),
    StaffQuestion("report_result", "Report came back as?", (
        Option("not_pulled", "Not pulled yet"),
        Option("no_file_found", "No file found"),
        Option("thin_or_stale", "Thin or stale"),
        Option("full_file", "Full file"),
    )),
    StaffQuestion("collections", "Anything in collections?", (
        Option("none_found", "None found"),
        Option("some", "One or two"),
        Option("many", "More than a few"),
        Option("unknown", "Unknown"),
    )),
    StaffQuestion("has_bank_account", "Bank account right now?", (
        Option("no", "No"),
        Option("yes", "Yes"),
    )),
    StaffQuestion("obligations", "Court-ordered obligations?", (
        Option("none", "None"),
        Option("restitution", "Restitution"),
        Option("child_support", "Child support"),
        Option("court_fines", "Court fines"),
    ), multi=True),
    StaffQuestion("recognizes_everything", "Does he recognize every item on the report?", (
        Option("not_reviewed_yet", "Not walked through yet"),
        Option("all_mine", "Yes, all his"),
        Option("some_not_mine", "No, at least one is not his"),
    )),
)


def inside_question(index: int) -> Question:
    for q in INSIDE_QUESTIONS:
        if q.index == index:
            return q
    raise KeyError(index)
