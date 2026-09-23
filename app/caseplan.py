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
rung 2 of the credit bureau access ladder asks for. When the plan says the
documents are on file, the ladder does not have to treat rung 2 as a wall.

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
        "A free non-driver ID is available to people receiving public "
        "assistance, SNAP or Medicaid. This is what clears rung 2 when a "
        "bureau cannot match the file.",
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
        """Everything a bureau asks for at rung 2, already in one folder."""
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


def ladder_rung_available(plan: CasePlan, rung: int) -> tuple[bool, str]:
    """Does the case plan already satisfy this rung of the access ladder?

    This is the whole point of the integration. Rung 2 asks for an ID copy and
    proof of address, and the vital documents packet is exactly that. If the
    coordinator already has it, nobody needs a notary and nobody waits.
    """
    if rung == 1:
        return True, "A signature is all rung 1 needs."
    if rung == 2:
        if plan.identity_packet_complete:
            return True, (
                "The vital documents packet is complete in the case plan, so "
                "rung 2 needs no new paperwork."
            )
        missing = ", ".join(DOCUMENT_LABEL[d] for d in plan.missing_documents)
        return False, f"Still needed for rung 2: {missing}."
    if rung == 3:
        return True, "Requires a notary at the law library and a named helper."
    return True, "The program acts under its own release form."
