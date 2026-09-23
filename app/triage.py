"""The classifier. Six answers in, one of four states out, with a path attached.

Screen 10 of the deck: this is the only screen where the app does something a
person could not do on paper, and the only one whose output can be scored for
accuracy. Everything else is a list, a letter, or a status.

Two design rules are load-bearing here.

Errors jump the queue. A dispute has a statutory reinvestigation clock; a thin
file does not. So an error finding outranks every other signal even on a client
who also has collections.

Restitution is not credit. Court obligations route to a separate list. They
matter enormously to the person and they do not belong in a list pretending to
be a credit card.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AccountHistory(str, Enum):
    YES = "yes"
    NO = "no"
    UNSURE = "unsure"


class ReportResult(str, Enum):
    NOT_PULLED = "not_pulled"
    NO_FILE_FOUND = "no_file_found"
    THIN_OR_STALE = "thin_or_stale"
    FULL_FILE = "full_file"


class Collections(str, Enum):
    NONE_FOUND = "none_found"
    SOME = "some"
    MANY = "many"
    UNKNOWN = "unknown"


class BankAccount(str, Enum):
    YES = "yes"
    NO = "no"


class Recognition(str, Enum):
    """Question six. The one that opens a legal clock."""

    ALL_MINE = "all_mine"
    SOME_NOT_MINE = "some_not_mine"
    NOT_REVIEWED_YET = "not_reviewed_yet"


class Obligation(str, Enum):
    NONE = "none"
    RESTITUTION = "restitution"
    CHILD_SUPPORT = "child_support"
    COURT_FINES = "court_fines"


class State(str, Enum):
    CREDIT_INVISIBLE = "credit_invisible"
    THIN_FILE = "thin_file"
    DAMAGED_FILE = "damaged_file"
    ERRORS_PRESENT = "errors_present"
    NOT_YET_TRIAGED = "not_yet_triaged"


STATE_LABEL: dict[State, str] = {
    State.CREDIT_INVISIBLE: "No file. Credit invisible.",
    State.THIN_FILE: "Thin or stale file",
    State.DAMAGED_FILE: "Damaged file, real debt",
    State.ERRORS_PRESENT: "Errors on the report",
    State.NOT_YET_TRIAGED: "Not yet triaged",
}

PATH: dict[State, dict[str, str]] = {
    State.CREDIT_INVISIBLE: {
        "plan": "Builder loan or secured card, then one on-time payment stream.",
        "horizon": "Roughly 6 to 9 months to a usable file.",
        "source": "Cornish interview, Sep 21. Unverified against a primary source.",
        "first_step": "Open the account before release, with the counselor.",
    },
    State.THIN_FILE: {
        "plan": "Low-effort boosters first: rent reporting, utility and phone reporting.",
        "horizon": "Months, and most of the work is not the client's.",
        "source": "Least work for the client, which is why it goes first.",
        "first_step": "Enroll the boosters that need no new account.",
    },
    State.DAMAGED_FILE: {
        "plan": "Debt triage before credit building.",
        "horizon": "Set the expectation in years rather than months.",
        "source": "Telling someone the truth here beats selling them a quick fix.",
        "first_step": "Inventory the debts and sort by what is collectible.",
    },
    State.ERRORS_PRESENT: {
        "plan": "Dispute flow, one letter to each of the three bureaus. Counselor "
                "approves, helper mails.",
        "horizon": "30 days from the day each bureau receives the letter, "
                   "extendable to 45 if the client sends more information "
                   "mid-dispute. This is the only state with a statutory clock, "
                   "which is why it jumps the queue.",
        "source": "15 U.S.C. 1681i(a)(1), checked 2026-09-23.",
        "first_step": "Draft the three dispute letters for the first flagged item.",
    },
    State.NOT_YET_TRIAGED: {
        "plan": "Pull the report first. There is nothing to classify yet.",
        "horizon": "The bureaus must deliver within 15 days of receiving the "
                   "request. Add mail time in both directions.",
        "source": "15 U.S.C. 1681j(a), checked 2026-09-23.",
        "first_step": "Mail the Annual Credit Report Request Form at rung 1.",
    },
}


@dataclass(frozen=True)
class Answers:
    """The six questions, exactly as the triage screen asks them."""

    ever_had_account: AccountHistory
    report_result: ReportResult
    collections: Collections
    has_bank_account: BankAccount
    obligations: tuple[Obligation, ...] = (Obligation.NONE,)
    recognizes_everything: Recognition = Recognition.NOT_REVIEWED_YET

    @staticmethod
    def from_form(form: dict) -> "Answers":
        obligations = tuple(
            Obligation(o) for o in form.getlist("obligations")
        ) if hasattr(form, "getlist") else tuple(
            Obligation(o) for o in form.get("obligations", [Obligation.NONE.value])
        )
        return Answers(
            ever_had_account=AccountHistory(form["ever_had_account"]),
            report_result=ReportResult(form["report_result"]),
            collections=Collections(form["collections"]),
            has_bank_account=BankAccount(form["has_bank_account"]),
            obligations=obligations or (Obligation.NONE,),
            recognizes_everything=Recognition(form["recognizes_everything"]),
        )


@dataclass(frozen=True)
class Classification:
    state: State
    label: str
    path: dict[str, str]
    reasons: list[str] = field(default_factory=list)
    needs_human_review: bool = False
    obligations_route: list[str] = field(default_factory=list)

    @property
    def jumps_queue(self) -> bool:
        return self.state is State.ERRORS_PRESENT


def _obligation_notes(answers: Answers) -> list[str]:
    """Court obligations leave the credit path here and do not come back."""
    notes = []
    for ob in answers.obligations:
        if ob is Obligation.NONE:
            continue
        if ob is Obligation.RESTITUTION:
            notes.append(
                "Restitution goes to the obligations list, not the credit path. "
                "Different mechanism, different screen. Whether restitution is "
                "ever furnished to a bureau is still an open question, so the "
                "app does not claim either way."
            )
        elif ob is Obligation.CHILD_SUPPORT:
            notes.append(
                "Child support arrears do reach credit reports: states are "
                "required to report delinquencies to the bureaus periodically, "
                "after notice and a chance to contest. Expect this one on the "
                "file. (42 U.S.C. 666(a)(7), checked 2026-09-23.)"
            )
        elif ob is Obligation.COURT_FINES:
            notes.append(
                "Court fines are tracked as an obligation. Civil judgments "
                "largely vanished from credit reports after July 2017, so do not "
                "assume a fine is on the file, but whether fines are furnished "
                "at all is still open. (CFPB public-records research, checked "
                "2026-09-23.)"
            )
    return notes


def classify(answers: Answers) -> Classification:
    reasons: list[str] = []
    review = False

    # Nothing to classify until the report is in hand. Say so rather than
    # guessing from the intake answers, which are memory, not evidence.
    if answers.report_result is ReportResult.NOT_PULLED:
        reasons.append("No report on file yet, so there is nothing to classify.")
        if answers.ever_had_account is AccountHistory.UNSURE:
            reasons.append(
                "Client is unsure whether they ever had an account. Common, and "
                "not a problem. The report settles it."
            )
        return Classification(
            state=State.NOT_YET_TRIAGED,
            label=STATE_LABEL[State.NOT_YET_TRIAGED],
            path=PATH[State.NOT_YET_TRIAGED],
            reasons=reasons,
            needs_human_review=False,
            obligations_route=_obligation_notes(answers),
        )

    # Errors outrank everything. A dispute carries a legal clock and no other
    # state does, so a client with both errors and collections is an errors
    # client until the dispute resolves.
    if answers.recognizes_everything is Recognition.SOME_NOT_MINE:
        reasons.append("Client does not recognize at least one item on the report.")
        if answers.collections in (Collections.SOME, Collections.MANY):
            reasons.append(
                "Collections are also present. Dispute first, because it is the "
                "only part with a deadline; debt triage follows."
            )
        return Classification(
            state=State.ERRORS_PRESENT,
            label=STATE_LABEL[State.ERRORS_PRESENT],
            path=PATH[State.ERRORS_PRESENT],
            reasons=reasons,
            needs_human_review=False,
            obligations_route=_obligation_notes(answers),
        )

    if answers.report_result is ReportResult.NO_FILE_FOUND:
        reasons.append("Bureau returned no file. Empty, not damaged.")
        if answers.ever_had_account is AccountHistory.YES:
            reasons.append(
                "Client recalls an account but the bureau found no file. Worth a "
                "second look: a name or SSN mismatch can hide a real file."
            )
            review = True
        if answers.has_bank_account is BankAccount.NO:
            reasons.append(
                "No bank account, so the builder loan or secured card needs one "
                "opened first. That is the first step, not a blocker."
            )
        return Classification(
            state=State.CREDIT_INVISIBLE,
            label=STATE_LABEL[State.CREDIT_INVISIBLE],
            path=PATH[State.CREDIT_INVISIBLE],
            reasons=reasons,
            needs_human_review=review,
            obligations_route=_obligation_notes(answers),
        )

    # Real debt outranks thinness. A thin file with collections on it is a
    # damaged file, and pointing that client at rent reporting wastes months.
    if answers.collections in (Collections.SOME, Collections.MANY):
        reasons.append("Collections present on the report. Real debt, not a gap.")
        if answers.collections is Collections.MANY:
            reasons.append("Volume is high enough that debt triage comes first.")
        return Classification(
            state=State.DAMAGED_FILE,
            label=STATE_LABEL[State.DAMAGED_FILE],
            path=PATH[State.DAMAGED_FILE],
            reasons=reasons,
            needs_human_review=False,
            obligations_route=_obligation_notes(answers),
        )

    if answers.collections is Collections.UNKNOWN:
        reasons.append(
            "Collections status unknown on a file that exists. Counselor reads "
            "the report before the path is set."
        )
        review = True

    if answers.recognizes_everything is Recognition.NOT_REVIEWED_YET:
        reasons.append(
            "Nobody has walked the report with the client line by line yet, so "
            "an error finding is still possible."
        )
        review = True

    # A full, clean, recognized file lands here too: nothing to dispute and
    # nothing to repair, so the work is adding on-time signals. Four states,
    # not five, is what keeps this measurable.
    state = State.THIN_FILE
    if answers.report_result is ReportResult.THIN_OR_STALE:
        reasons.append("File exists but is thin or stale. Boosters before new credit.")
    else:
        reasons.append(
            "Full file, nothing in collections, nothing disputed. Boosters and "
            "on-time signals are the remaining work."
        )

    return Classification(
        state=state,
        label=STATE_LABEL[state],
        path=PATH[state],
        reasons=reasons,
        needs_human_review=review,
        obligations_route=_obligation_notes(answers),
    )
