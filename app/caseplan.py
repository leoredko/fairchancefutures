"""Integration with the DOCCS Offender Case Plan.

New York already has the thing Bridge would otherwise reinvent. At the initial
interview an Offender Rehabilitation Coordinator establishes a program plan of
goals and tasks; that plan follows the person through incarceration and out
into community supervision, and the ORC reviews it at scheduled quarterly
reviews. It was called the Transitional Accountability Plan and is now the
Offender Case Plan.

So Bridge is not a separate case management system. It is one domain inside the
plan the ORC is already keeping: it reads the person's plan, contributes credit
goals and tasks to it, and reports progress back on the ORC's own quarterly
cadence rather than on a cadence of its own invention.

Two things fall out of that, and both make the product better:

Vital documents. Reentry staff already assemble Social Security cards, birth
certificates and non-driver ID, and the state can pull a birth certificate at
no cost using sentence and commitment paperwork. That packet is exactly what
the ID application needs. Both the birth certificate and the Social Security
card have to be on file before that application can be submitted at all, the
coordinator reviews the status quarterly, and the Social Security card goes in
at 120 days before release. `document_readiness` below models that chain, and
it is what replaced the old four-rung access ladder.

Timing. Reentry planning intensifies in the six months before release, which is
the same window in which a credit file can realistically be moved. Bridge sorts
by it rather than inventing a separate clock.

    Sources, checked 2026-09-23
    DOCCS, Legislative Report on Reentry Planning and Access to Social Services
    DOCCS, Transitional Services Program
    DOCCS, Re-Entry Services

Assumed for this build, with the team's sign-off: that DOCCS grants Bridge
read and write access to the case plan through an API. Nothing here calls a
real endpoint. `SIMULATED` marks every value that a real integration would
fetch instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum

SIMULATED = True

# The person who owns the plan. Ms. Reyes is one of these.
COORDINATOR_TITLE = "Offender Rehabilitation Coordinator"
PLAN_NAME = "Offender Case Plan"
PLAN_FORMER_NAME = "Transitional Accountability Plan"

# Reentry planning intensifies in the six months before release.
INTENSIVE_WINDOW_DAYS = 182


class Document(str, Enum):
    """The vital documents packet reentry staff already assemble."""

    SOCIAL_SECURITY_CARD = "social_security_card"
    BIRTH_CERTIFICATE = "birth_certificate"
    PHOTO_ID = "non_driver_id"


DOCUMENT_LABEL: dict[Document, str] = {
    Document.SOCIAL_SECURITY_CARD: "Social Security card",
    Document.BIRTH_CERTIFICATE: "Birth certificate",
    Document.PHOTO_ID: "Non-driver ID",
}

DOCUMENT_NOTE: dict[Document, str] = {
    Document.SOCIAL_SECURITY_CARD:
        "Needed for every credit report request and every dispute.",
    Document.BIRTH_CERTIFICATE:
        "The state can request a certified copy at no cost using sentence and "
        "commitment paperwork.",
    Document.PHOTO_ID:
        "Produced before release through the DOCCS and DMV program, but only "
        "once the birth certificate and Social Security card are both on file. "
        "The release ID a person walks out with expires 120 days later, which "
        "is the window to exchange it at a DMV office for the real one.",
}


class Domain(str, Enum):
    """Plan domains. Bridge owns exactly one of them and touches no others."""

    HOUSING = "housing"
    EMPLOYMENT = "employment"
    EDUCATION = "education"
    TREATMENT = "treatment"
    FINANCIAL = "financial"


@dataclass
class PlanTask:
    """One task inside the plan, in the plan's own shape."""

    domain: Domain
    text: str
    owner: str
    due: str = ""
    done: bool = False
    source: str = "Bridge"

    @property
    def label(self) -> str:
        return self.text


@dataclass
class CasePlan:
    """What Bridge reads from, and writes one domain back into."""

    client_id: str
    coordinator: str
    opened_on: str
    last_reviewed: str
    next_review: str
    documents: dict[str, bool] = field(default_factory=dict)
    tasks: list[PlanTask] = field(default_factory=list)

    def has(self, doc: Document) -> bool:
        return bool(self.documents.get(doc.value))

    @property
    def missing_documents(self) -> list[Document]:
        return [d for d in Document if not self.has(d)]

    @property
    def identity_packet_complete(self) -> bool:
        """The whole packet on file, ID included."""
        return all(self.has(d) for d in Document)

    def financial_tasks(self) -> list[PlanTask]:
        return [t for t in self.tasks if t.domain is Domain.FINANCIAL]

    def contribute(self, task: PlanTask) -> None:
        """Write a credit task into the plan.

        Bridge only ever writes into the financial domain. Housing, employment,
        education and treatment belong to the coordinator, and an app that
        started editing those would be a different and much worse idea.
        """
        if task.domain is not Domain.FINANCIAL:
            raise ValueError(
                "Bridge contributes to the financial domain only. "
                f"{task.domain.value} belongs to the coordinator."
            )
        self.tasks.append(task)


def quarterly_reviews_left(release: date, today: date | None = None) -> int:
    """How many scheduled reviews remain before release.

    This is the real deadline a counselor works to. Bridge shows it because a
    plan that needs three reviews' worth of work and has one left is a plan
    that has to change now, not in April.
    """
    today = today or date.today()
    days = (release - today).days
    return max(0, days // 91)


def in_intensive_window(release: date, today: date | None = None) -> bool:
    today = today or date.today()
    return 0 <= (release - today).days <= INTENSIVE_WINDOW_DAYS


def simulated_plan(
    client_id: str,
    coordinator: str,
    release_date: str,
    *,
    documents: dict[str, bool] | None = None,
    today: date | None = None,
) -> CasePlan:
    """Stand in for the API call a real deployment would make.

    Everything returned here is invented. A real integration replaces this one
    function and nothing else.
    """
    today = today or date.today()
    release = date.fromisoformat(release_date)
    opened = min(today - timedelta(days=400), release - timedelta(days=900))
    last = today - timedelta(days=today.day % 60)
    return CasePlan(
        client_id=client_id,
        coordinator=coordinator,
        opened_on=opened.isoformat(),
        last_reviewed=last.isoformat(),
        next_review=(last + timedelta(days=91)).isoformat(),
        documents=documents if documents is not None else {
            Document.SOCIAL_SECURITY_CARD.value: True,
            Document.BIRTH_CERTIFICATE.value: False,
            Document.PHOTO_ID.value: False,
        },
        tasks=[
            PlanTask(Domain.HOUSING, "Confirm approved residence",
                     coordinator, source="DOCCS"),
            PlanTask(Domain.EMPLOYMENT, "Complete vocational assessment",
                     coordinator, done=True, source="DOCCS"),
            PlanTask(Domain.TREATMENT, "Continue scheduled programming",
                     coordinator, source="DOCCS"),
        ],
    )


# At 120 days before release the Social Security card application goes in.
# That is the one deadline in this whole product that belongs to the person
# rather than to a bureau or a coordinator.
SSN_CARD_TRIGGER_DAYS = 120

# The birth certificate is the slow one, and it gates the ID application.
BIRTH_CERTIFICATE_WEEKS = 10


def days_to_release(release: date, today: date | None = None) -> int:
    return (release - (today or date.today())).days


def document_readiness(
    plan: CasePlan, release: date, today: date | None = None,
    born_in_new_york: bool = True,
) -> dict:
    """What is missing, what is urgent, and what it blocks.

    This replaced the four-rung access ladder. The ladder modelled what a
    bureau would demand, which nobody can establish: no public source says how
    often a plain signed request clears, and Experian asks for an ID copy with
    every mailed dispute regardless. A ladder whose first step may not exist is
    a guess with a state machine around it.

    Document status is the same decision grounded in something checkable. The
    coordinator already tracks it, reviews it quarterly, and works to a real
    deadline. Nothing here is inferred: the trigger, the review cadence and the
    order of operations are all in the DOCCS legislative report.
    """
    left = days_to_release(release, today)
    missing = plan.missing_documents
    blocking = [d for d in (Document.BIRTH_CERTIFICATE,
                            Document.SOCIAL_SECURITY_CARD) if not plan.has(d)]

    urgent: list[str] = []
    if not plan.has(Document.SOCIAL_SECURITY_CARD) and left <= SSN_CARD_TRIGGER_DAYS:
        urgent.append(
            f"Social Security card: {left} days to release, past the "
            f"{SSN_CARD_TRIGGER_DAYS}-day mark. This one is overdue."
        )
    if not plan.has(Document.BIRTH_CERTIFICATE):
        urgent.append(
            f"Birth certificate: allow {BIRTH_CERTIFICATE_WEEKS} weeks or more. "
            f"It has no deadline of its own, which is why it gets left, and it "
            f"blocks the ID application."
        )
    # The fee waiver runs on New York records. Somebody born elsewhere is not
    # covered by it and their request is slower and costs money, so it has to
    # be started earlier rather than discovered later.
    if not born_in_new_york and not plan.has(Document.BIRTH_CERTIFICATE):
        urgent.append(
            "Born outside New York, so the no-fee route does not apply. This "
            "one goes to another state or country and needs starting now."
        )

    if not blocking:
        summary = ("Birth certificate and Social Security card are both on "
                   "file, so the ID application is not waiting on paperwork.")
    else:
        names = ", ".join(DOCUMENT_LABEL[d] for d in blocking)
        summary = (f"The ID application cannot be submitted yet. Still needed: "
                   f"{names}.")

    return {
        "days_to_release": left,
        "missing": missing,
        "blocking": blocking,
        "urgent": urgent,
        "summary": summary,
        "ready": not blocking,
        "has_photo_id": plan.has(Document.PHOTO_ID),
        "past_ssn_trigger": left <= SSN_CARD_TRIGGER_DAYS,
    }
