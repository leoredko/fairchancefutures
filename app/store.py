"""Storage.

A JSON file, loaded at startup and written on every change. Not a database,
deliberately: the whole point of this build is that a reader can open
data/bridge.json and see exactly what the app knows about a person. When the
data is this sensitive, inspectable beats clever.

Swapping this for Postgres later touches this file and nothing else.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path

from app.authorization import (
    Authorization,
    Rung,
    Scope,
    default_helper_authorization,
)
from app.letters import Draft, ReviewLog

DATA_PATH = Path(os.environ.get("BRIDGE_DATA", "data/bridge.json"))
_lock = threading.Lock()


@dataclass
class TimelineEvent:
    """Every event carries a person's name and a real date.

    From the Cornish interview, Sep 21: automated nudges read as scams inside.
    An event with no human attached does not go on this timeline.
    """

    text: str
    actor: str
    on: str
    done: bool = True


@dataclass
class Client:
    id: str
    display_name: str
    first_name: str
    release_date: str
    case_state: str = "not_yet_triaged"
    state_label: str = "Not yet triaged"
    needs: str = "No report on file"
    clock: str = ""
    clock_sort: int = 9999
    consent_scopes: list[str] = field(default_factory=lambda: ["report_sharing"])
    consent_recorded_on: str = ""
    helper_name: str | None = None
    ladder_rung: int = 1
    ladder_status: dict[str, str] = field(default_factory=dict)
    intake_answers: dict = field(default_factory=dict)
    classification: dict | None = None
    timeline: list[dict] = field(default_factory=list)
    flagged_items: list[dict] = field(default_factory=list)
    report_summary: str = ""
    collections_count: int = 0
    last_pulled: str = ""
    plan_step: str = ""
    lesson: str = ""
    family_task: dict = field(default_factory=dict)
    report_pages: list[str] = field(default_factory=list)
    # Never rendered by any surface. Present so the redaction tests have
    # something real to withhold.
    ssn: str = "***-**-****"
    full_account_number: str = "****"


@dataclass
class State:
    clients: dict[str, Client] = field(default_factory=dict)
    authorizations: dict[str, dict] = field(default_factory=dict)
    drafts: dict[str, list[dict]] = field(default_factory=dict)
    review_log: dict = field(default_factory=lambda: {"reviewed": 0, "edited": 0})
    sync_queue: list[dict] = field(default_factory=list)


STATE = State()


# --------------------------------------------------------------------------
# persistence
# --------------------------------------------------------------------------

def _serialize() -> dict:
    return {
        "clients": {k: asdict(v) for k, v in STATE.clients.items()},
        "authorizations": STATE.authorizations,
        "drafts": STATE.drafts,
        "review_log": STATE.review_log,
        "sync_queue": STATE.sync_queue,
    }


def save() -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(_serialize(), indent=2))
    tmp.replace(DATA_PATH)


def load() -> bool:
    if not DATA_PATH.exists():
        return False
    raw = json.loads(DATA_PATH.read_text())
    STATE.clients = {k: Client(**v) for k, v in raw.get("clients", {}).items()}
    STATE.authorizations = raw.get("authorizations", {})
    STATE.drafts = raw.get("drafts", {})
    STATE.review_log = raw.get("review_log", {"reviewed": 0, "edited": 0})
    STATE.sync_queue = raw.get("sync_queue", [])
    return True


def mutate():
    """Use as `with mutate():` around any change. Saves on exit."""

    class _Ctx:
        def __enter__(self):
            _lock.acquire()
            return STATE

        def __exit__(self, *exc):
            try:
                if exc[0] is None:
                    save()
            finally:
                _lock.release()
            return False

    return _Ctx()


# --------------------------------------------------------------------------
# authorization helpers
# --------------------------------------------------------------------------

def get_authorization(client_id: str) -> Authorization | None:
    raw = STATE.authorizations.get(client_id)
    if raw is None:
        return None
    return Authorization(
        client_id=raw["client_id"],
        helper_name=raw["helper_name"],
        scopes=frozenset(Scope(s) for s in raw["scopes"]),
        rung=Rung(raw["rung"]),
        signed_on=date.fromisoformat(raw["signed_on"]),
        expires_on=date.fromisoformat(raw["expires_on"]),
        revoked_on=date.fromisoformat(raw["revoked_on"]) if raw.get("revoked_on") else None,
    )


def put_authorization(auth: Authorization) -> None:
    STATE.authorizations[auth.client_id] = {
        "client_id": auth.client_id,
        "helper_name": auth.helper_name,
        "scopes": sorted(s.value for s in auth.scopes),
        "rung": int(auth.rung),
        "signed_on": auth.signed_on.isoformat(),
        "expires_on": auth.expires_on.isoformat(),
        "revoked_on": auth.revoked_on.isoformat() if auth.revoked_on else None,
    }


def review_log() -> ReviewLog:
    return ReviewLog(**STATE.review_log)


def put_review_log(log: ReviewLog) -> None:
    STATE.review_log = {"reviewed": log.reviewed, "edited": log.edited}


def drafts_for(client_id: str) -> list[dict]:
    return STATE.drafts.setdefault(client_id, [])


def add_draft(draft: Draft) -> dict:
    row = {
        "id": f"{draft.client_id}-{len(drafts_for(draft.client_id)) + 1}",
        "kind": draft.kind,
        "bureau": draft.bureau,
        "body": draft.body,
        "citations": draft.citations,
        "approved_on": None,
        "edited_before_approval": None,
    }
    drafts_for(draft.client_id).append(row)
    return row


# --------------------------------------------------------------------------
# seed
# --------------------------------------------------------------------------

def _ladder(cleared_at: int) -> dict[str, str]:
    labels = {
        1: "Worked" if cleared_at >= 1 else "Not needed",
        2: "Not needed",
        3: "Not needed",
        4: "Not needed",
    }
    for rung in range(1, cleared_at):
        labels[rung] = "Kicked back"
    labels[cleared_at] = "Worked"
    return {str(k): v for k, v in labels.items()}


def seed() -> None:
    """The caseload from screens 07 through 09, as data."""
    today = date.today()

    marcus = Client(
        id="marcus-w",
        display_name="Marcus W.",
        first_name="Marcus",
        release_date=(today + timedelta(days=118)).isoformat(),
        case_state="errors_present",
        state_label="Errors on the report",
        needs="Dispute letter to approve",
        clock="Releases in 118 days",
        clock_sort=118,
        consent_recorded_on=(today - timedelta(days=205)).isoformat(),
        helper_name="Denise",
        ladder_rung=1,
        ladder_status=_ladder(1),
        report_summary="Thin file, two disputed items",
        collections_count=0,
        last_pulled=(today - timedelta(days=186)).isoformat(),
        plan_step="Dispute letter mailed, waiting on the bureau",
        lesson="Lesson 3, what a secured card actually is. Four minutes.",
        flagged_items=[
            {"creditor": "Midland Funding", "last_four": "4471",
             "reason": "never opened this account"},
            {"creditor": "Second Chance Auto", "last_four": "0912",
             "reason": "paid in full, still showing open"},
        ],
        timeline=[
            asdict(TimelineEvent("Denise mailed the request for your report",
                                 "Your sister", "March 1")),
            asdict(TimelineEvent("It came back. Two things look wrong.",
                                 "Denise added it", "March 18")),
            asdict(TimelineEvent("Ms. Reyes approved your dispute letter",
                                 "Your counselor", "March 20")),
            asdict(TimelineEvent("Waiting on their answer, due April 3",
                                 "This part is slow. Nothing is wrong.",
                                 "", done=False)),
        ],
        family_task={
            "headline": "Print the request, have Marcus sign it, mail it.",
            "detail": "We filled in everything except his signature. The "
                      "envelope prints addressed. One stamp.",
            "done": False,
        },
    )

    others = [
        Client(
            id="m-alvarez", display_name="M. Alvarez", first_name="Maria",
            release_date=(today + timedelta(days=9)).isoformat(),
            case_state="errors_present", state_label="Errors present",
            needs="Dispute letter to approve", clock="Releases in 9 days",
            clock_sort=9, helper_name="Rosa",
            consent_recorded_on=(today - timedelta(days=21)).isoformat(),
            ladder_rung=1, ladder_status=_ladder(1),
            report_summary="Thin file, two disputed items",
            last_pulled=(today - timedelta(days=22)).isoformat(),
            collections_count=0,
            flagged_items=[
                {"creditor": "Midland Funding", "last_four": "4471",
                 "reason": "never opened this account"},
                {"creditor": "Cavalry SPV", "last_four": "8802",
                 "reason": "not mine, wrong middle initial"},
            ],
            plan_step="Two items flagged. Dispute letter not drafted yet.",
        ),
        Client(
            id="j-whitfield", display_name="J. Whitfield", first_name="James",
            release_date=(today + timedelta(days=21)).isoformat(),
            case_state="not_yet_triaged", state_label="Not yet triaged",
            needs="No report on file", clock="Releases in 21 days",
            clock_sort=21, helper_name=None,
            consent_recorded_on=(today - timedelta(days=4)).isoformat(),
            ladder_rung=1, ladder_status=_ladder(1),
            plan_step="Triage session not yet held",
        ),
        Client(
            id="r-osei", display_name="R. Osei", first_name="Rashid",
            release_date=(today + timedelta(days=64)).isoformat(),
            case_state="credit_invisible", state_label="Credit invisible",
            needs="Bureau answer overdue", clock="4 days past due",
            clock_sort=-4, helper_name="Ama",
            consent_recorded_on=(today - timedelta(days=90)).isoformat(),
            ladder_rung=2, ladder_status=_ladder(2),
            report_summary="No file found on two of three bureaus",
            last_pulled=(today - timedelta(days=40)).isoformat(),
            plan_step="Builder loan opens after the third bureau answers",
        ),
        Client(
            id="t-brennan", display_name="T. Brennan", first_name="Tom",
            release_date=(today - timedelta(days=42)).isoformat(),
            case_state="damaged_file", state_label="Damaged file",
            needs="Missed 2 check-ins", clock="Out 6 weeks",
            clock_sort=200, helper_name=None,
            consent_recorded_on=(today - timedelta(days=160)).isoformat(),
            ladder_rung=4, ladder_status=_ladder(4),
            report_summary="Full file, nine collections accounts",
            collections_count=9,
            last_pulled=(today - timedelta(days=70)).isoformat(),
            plan_step="Debt triage, then boosters. Expectation set in years.",
        ),
    ]

    STATE.clients = {c.id: c for c in [marcus, *others]}
    STATE.authorizations = {}
    put_authorization(
        default_helper_authorization("marcus-w", "Denise", today - timedelta(days=209))
    )
    put_authorization(
        default_helper_authorization("m-alvarez", "Rosa", today - timedelta(days=21))
    )
    STATE.drafts = {}
    STATE.review_log = {"reviewed": 0, "edited": 0}
    STATE.sync_queue = []


def boot() -> None:
    if not load():
        seed()
        save()
