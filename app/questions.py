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


INSIDE_QUESTIONS: tuple[Question, ...] = (
    Question(
        index=1,
        field="has_bank_account",
        prompt="Do you have a bank account right now?",
        helper="Open, closed, frozen, joint with someone. Any of it counts as a yes.",
        options=(
            Option("yes", "Yes"),
            Option("no", "No"),
        ),
        design_note="the easiest question first. The first screen is where "
                    "people decide whether this is worth their time.",
        reassurance=OFFLINE_NOTE,
    ),
    Question(
        index=2,
        field="ever_had_account",
        prompt="Have you ever had a credit card, loan, or account in your name?",
        helper="Before you came in counts. A guess is fine, we check it later.",
        options=(
            Option("yes", "Yes, at some point"),
            Option("no", "No, never"),
            Option("unsure", "I'm not sure"),
        ),
        design_note="one question per screen, offline-first, large targets. "
                    "Facility tablets are slow, shared, and often metered by the minute.",
        constraint="no file upload and no identity verification happen on this "
                   "surface. Both are physically impossible from inside, so "
                   "neither is designed here.",
        reassurance=OFFLINE_NOTE,
    ),
    Question(
        index=3,
        field="collections",
        prompt="Is anyone chasing you for money you owe?",
        helper="A collector, a hospital, an old landlord. Not court fines, those "
               "come next.",
        options=(
            Option("none_found", "Not that I know of"),
            Option("some", "One or two"),
            Option("many", "More than a few"),
            Option("unknown", "I have no idea"),
        ),
        design_note="'I have no idea' is a real answer and the most common one. "
                    "Forcing a guess here produces bad data and a worse path.",
    ),
    Question(
        index=4,
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
                    "path. Different mechanism, different screen. They matter, "
                    "and they do not sit in a list pretending to be a credit card.",
    ),
    Question(
        index=5,
        field="helper_available",
        prompt="Is there someone outside who can get your mail?",
        helper="Your report comes on paper, to an address. Somebody has to be "
               "there when it lands.",
        options=(
            Option("yes", "Yes, someone I trust",
                   "They get the mail and send us photos. Most of the time that's "
                   "all that's needed. If a bureau asks for more, Ms. Reyes "
                   "handles it from there."),
            Option("no", "No, or I'd rather not ask anyone",
                   "Ms. Reyes handles it through the program instead, using the "
                   "same form you already signed with her. A few steps run "
                   "slower. Nothing stops."),
            Option("later", "I'll decide later",
                   "Nothing is waiting on this answer."),
        ),
        design_note="this screen asks who receives the mail. It does NOT ask for "
                    "a power of attorney. What the bureaus require varies per "
                    "person and is unknowable until you try, so the paperwork "
                    "question is handled later, by the caseworker, only for the "
                    "people who hit it.",
        constraint="a helper outside has no standing without a signed form. "
                   "Answering yes here starts an invitation, it does not grant "
                   "anything.",
    ),
    Question(
        index=6,
        field="wants_line_by_line",
        prompt="When the report comes back, do you want to go through it line by line?",
        helper="It takes about twenty minutes with Ms. Reyes. It is how errors "
               "get found.",
        options=(
            Option("yes", "Yes, go through it with me"),
            Option("summary", "Just tell me what matters"),
        ),
        design_note="an error finding requires a person who recognizes their own "
                    "accounts. Nobody else can do this step, which is why it is "
                    "asked rather than assumed.",
    ),
)


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
