"""Reading your own credit report, one part at a time.

The report arriving is the biggest thing that happens on a case. It is the
first time in years that anybody has told this person the truth about their own
financial record, and until now the app rendered it as a table and moved on.

So this module turns the report into a walk rather than a dump. One section per
screen, matching the one-question-per-screen pattern the tablet already uses,
and every section carries the teaching that makes that part of the page mean
something. A lesson read cold is homework. The same lesson attached to a line
on your own report is the best teaching moment this product will ever get.

It ends on the question that decides the whole case: does anything here look
wrong to you. That field is `recognizes_everything` in `app/triage.py`, and it
is the only one that opens a statutory clock. It used to be answered on the
staff form, because the tablet could not pull a report and so could not show
one. Now it can, and the person looking at the account is the only human alive
who knows whether they opened it. Asking them is better data, better teaching
and better product at the same time.

What the person's answer does NOT do is send a letter. A flag raised here is a
claim, and it goes to the coordinator to confirm against the paper, the same
way anything else arriving from outside does. The client starts the
conversation; the coordinator still holds the deadline.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Section:
    """One screen of the walk: a slice of the report, and what it means."""

    key: str
    title: str
    teaching: str
    # The lesson that covers this in full, for somebody who wants more than the
    # two sentences that fit next to their own data.
    lesson_slug: str = ""
    lesson_label: str = ""


SECTIONS: tuple[Section, ...] = (
    Section(
        key="identity",
        title="Who they think you are",
        teaching="This is how a bureau decides a file belongs to you. It is "
                 "also where the damage starts: a wrong middle initial or an "
                 "address you never lived at can pull somebody else's "
                 "accounts onto your file, or hide yours. Read it like it "
                 "matters, because it does.",
        lesson_slug="what-a-report-is",
        lesson_label="What a credit report actually is",
    ),
    Section(
        key="score",
        title="The score, or the missing score",
        teaching="A file disclosure does not have to carry a number and most "
                 "mailed ones do not. If there is nothing here, nothing has "
                 "gone wrong. The file is the part that can be corrected, and "
                 "it is the part you are owed.",
        lesson_slug="report-and-score",
        lesson_label="The report and the score are different things",
    ),
    Section(
        key="accounts",
        title="Your accounts, one at a time",
        teaching="Every line is somebody claiming you owe them, or owed them. "
                 "Open means it is still running. Closed and paid is a good "
                 "line to have. A collection means the original lender gave "
                 "up and sold it on, which is also the kind of line that turns "
                 "out not to be yours.",
        lesson_slug="old-debt",
        lesson_label="Old debt does not last forever",
    ),
    Section(
        key="public_records",
        title="Public records",
        teaching="Court items sit apart from credit accounts. Civil judgments "
                 "largely came off credit reports in 2017, so this section is "
                 "often empty even for somebody with court debt. Empty here "
                 "does not mean the debt is gone, it means it is not being "
                 "reported as credit.",
        lesson_slug="old-debt",
        lesson_label="Old debt does not last forever",
    ),
    Section(
        key="missing",
        title="What is not here",
        teaching="Look at what is absent. Rent you paid for years. A phone "
                 "bill. Utilities. None of it is here, because nobody reported "
                 "it. That is not your failure, it is a gap in how the system "
                 "collects information, and it is one of the few gaps you can "
                 "close on purpose.",
        lesson_slug="building-from-nothing",
        lesson_label="Building a file from nothing",
    ),
)

BY_KEY: dict[str, Section] = {s.key: s for s in SECTIONS}

# The question the walk ends on, and the only one that opens a legal clock.
FINAL_QUESTION = "Does anything on here look wrong to you?"

FINAL_CHOICES: tuple[tuple[str, str], ...] = (
    ("all_mine", "No, I recognize all of it"),
    ("some_not_mine", "Yes, at least one of these is not mine"),
    ("not_sure", "I am not sure, I want to go through it with someone"),
)

# What each answer means next, said plainly rather than left to be guessed.
ANSWER_NEXT: dict[str, str] = {
    "all_mine":
        "Good. Nothing to dispute means the work is building the file rather "
        "than fixing it, which is the faster of the two jobs. Your coordinator "
        "will go through the plan with you.",
    "some_not_mine":
        "That is the sentence that starts the clock. Your coordinator checks "
        "what you flagged against the paper, and if it holds, three letters go "
        "out, one to each bureau, and each of them has 30 days from the day it "
        "lands to answer.",
    "not_sure":
        "Which is a real answer and a common one. Nobody expects you to know "
        "a 2016 account number off the top of your head. Your coordinator will "
        "sit down and go through it line by line with you.",
}


def sections_for(report) -> list[Section]:
    """The sections that apply to this document.

    Public records only shows when there are some. An empty section on a walk
    teaches nothing and makes the walk feel padded, which is how somebody
    decides to skip the rest of it.
    """
    out = []
    for section in SECTIONS:
        if section.key == "public_records" and not report.public_records:
            continue
        out.append(section)
    return out


def total_screens(report) -> int:
    """Sections plus the closing question."""
    return len(sections_for(report)) + 1


def _blank() -> dict:
    return {"section": 0, "done": False, "answer": "", "flagged": [],
            "reviewed_on": ""}


def review(client, index: int) -> dict:
    """Where this person has got to reading one report. Never returns None."""
    store = getattr(client, "report_review", None) or {}
    return {**_blank(), **store.get(str(index), {})}


def open_review(client, index: int) -> dict:
    if not hasattr(client, "report_review") or client.report_review is None:
        client.report_review = {}
    return client.report_review.setdefault(str(index), _blank())


def record_section(client, index: int, at: int) -> dict:
    """Furthest section reached, not latest, so going back to re-read a page of
    your own report does not cost you your place."""
    row = open_review(client, index)
    row["section"] = max(int(row.get("section", 0)), int(at))
    return row


def record_answer(client, index: int, answer: str, flagged: list[int],
                  on: str) -> dict:
    row = open_review(client, index)
    row["answer"] = answer
    row["flagged"] = sorted({int(f) for f in flagged})
    row["done"] = True
    row["reviewed_on"] = on
    return row


def has_been_read(client, index: int) -> bool:
    return bool(review(client, index)["done"])


def unread_indexes(client, reports) -> list[int]:
    """Confirmed reports this person has not yet walked.

    Drives the arrival moment: a report that has landed and not been read is
    the single most important thing on this person's case, and it should
    interrupt rather than sit in a list.
    """
    return [i for i, _ in enumerate(reports) if not has_been_read(client, i)]


def client_flags(client, reports) -> list[dict]:
    """What the person said was not theirs, for the coordinator to check.

    A claim, not a dispute. It carries the person's own words to the desk,
    where it is confirmed against the paper before it becomes a letter.
    """
    out = []
    for i, report in enumerate(reports):
        row = review(client, i)
        if row["answer"] not in ("some_not_mine", "not_sure"):
            continue
        for position in row["flagged"]:
            if 0 <= position < len(report.accounts):
                account = report.accounts[position]
                out.append({
                    "bureau": report.bureau,
                    "creditor": account.creditor,
                    "safe_number": account.safe_number,
                    "reviewed_on": row["reviewed_on"],
                    "unsure": row["answer"] == "not_sure",
                })
        if row["answer"] == "not_sure" and not row["flagged"]:
            out.append({
                "bureau": report.bureau,
                "creditor": "Whole report",
                "safe_number": "",
                "reviewed_on": row["reviewed_on"],
                "unsure": True,
            })
    return out
