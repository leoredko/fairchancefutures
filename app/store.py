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
    Scope,
    Standing,
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
    # New York only. DIN is the number they are called by inside; NYSID is the
    # one that follows them out. Either one logs in.
    din: str = ""
    nysid: str = ""
    facility: str = ""
    case_state: str = "not_yet_triaged"
    state_label: str = "Not yet triaged"
    needs: str = "No report on file"
    clock: str = ""
    clock_sort: int = 9999
    consent_scopes: list[str] = field(default_factory=lambda: ["report_sharing"])
    consent_recorded_on: str = ""
    helper_name: str | None = None
    intake_answers: dict = field(default_factory=dict)
    classification: dict | None = None
    timeline: list[dict] = field(default_factory=list)
    flagged_items: list[dict] = field(default_factory=list)
    report_summary: str = ""
    collections_count: int = 0
    last_pulled: str = ""
    plan_step: str = ""
    family_task: dict = field(default_factory=dict)
    report_pages: list[str] = field(default_factory=list)
    # The record attached to this DIN, as the lookup returns it. Facility and
    # the sentence dates come from here rather than from a person retyping them
    # on a metered tablet. See app/doccs.py; note it carries no date of birth,
    # because the public lookup does not return one.
    doccs_record: dict = field(default_factory=dict)
    # Which field the release date was taken from, so a screen can say so
    # rather than implying somebody goes home on their parole eligibility date.
    release_date_source: str = ""
    # Where this person has got to reading each of their own reports, and what
    # they said about it. Keyed by the report's position. See app/walkthrough.py.
    report_review: dict = field(default_factory=dict)
    # Which of the two paths they chose on the way in, or "" for not yet
    # asked. It steers where /inside lands them and what the screens push
    # toward; it never decides what they are allowed to reach. See app/paths.py.
    path: str = ""
    # Where this person has got to in the credit course, per lesson.
    # A plain dict so it survives the JSON round trip without a schema.
    # See app/lessons.py.
    lesson_progress: dict = field(default_factory=dict)
    # Which vital documents the coordinator has on file, keyed by
    # `caseplan.Document` value. Empty means nobody recorded any, and the plan
    # falls back to its stand-in. Only the coordinator writes it: the tablet
    # cannot take delivery of a document, so it cannot say one arrived.
    documents: dict = field(default_factory=dict)
    # Never rendered by any surface. Present so the redaction tests have
    # something real to withhold.
    ssn: str = "***-**-****"
    full_account_number: str = "****"


@dataclass
class State:
    clients: dict[str, Client] = field(default_factory=dict)
    # Reports the coordinator scanned in, by client id.
    reports: dict[str, list[dict]] = field(default_factory=dict)
    accounts: dict[str, dict] = field(default_factory=dict)
    # Cookie signing key. From BRIDGE_SECRET in a real deployment; generated
    # here so a restart does not sign everyone out mid-demo.
    secret: str = ""
    authorizations: dict[str, dict] = field(default_factory=dict)
    drafts: dict[str, list[dict]] = field(default_factory=dict)
    review_log: dict = field(default_factory=lambda: {"reviewed": 0, "edited": 0})
    # Every answer, with what was saved and when. Not an offline queue: this
    # build assumes the tablet is online, which is a stated assumption rather
    # than a finding. The receipt for the promise intake makes on question one.
    write_log: list[dict] = field(default_factory=list)
    # Languages people asked for under "Other". Anonymous on purpose: it is
    # asked at the door, before anybody is known, and a name adds nothing.
    language_requests: list[dict] = field(default_factory=list)


STATE = State()


# --------------------------------------------------------------------------
# persistence
# --------------------------------------------------------------------------

def _serialize() -> dict:
    return {
        "clients": {k: asdict(v) for k, v in STATE.clients.items()},
        "accounts": STATE.accounts,
        "reports": STATE.reports,
        "secret": STATE.secret,
        "authorizations": STATE.authorizations,
        "drafts": STATE.drafts,
        "review_log": STATE.review_log,
        "write_log": STATE.write_log,
        "language_requests": STATE.language_requests,
    }


def save() -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(_serialize(), indent=2))
    tmp.replace(DATA_PATH)


def _apply(raw: dict) -> None:
    """Put a serialized state back into STATE, in place.

    In place because every other module did `from app.store import STATE` and
    holds that object. Rebinding the name here would leave them all reading a
    state nothing writes to.
    """
    STATE.clients = {k: Client(**v) for k, v in raw.get("clients", {}).items()}
    STATE.accounts = raw.get("accounts", {})
    STATE.reports = raw.get("reports", {})
    STATE.secret = raw.get("secret", "")
    STATE.authorizations = raw.get("authorizations", {})
    STATE.drafts = raw.get("drafts", {})
    STATE.review_log = raw.get("review_log", {"reviewed": 0, "edited": 0})
    STATE.write_log = raw.get("write_log", raw.get("sync_queue", []))
    STATE.language_requests = raw.get("language_requests", [])


def load() -> bool:
    if not DATA_PATH.exists():
        return False
    _apply(json.loads(DATA_PATH.read_text()))
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
        standing=Standing(raw.get("standing", Standing.SIGNED_FORM.value)),
        signed_on=date.fromisoformat(raw["signed_on"]),
        expires_on=date.fromisoformat(raw["expires_on"]),
        revoked_on=date.fromisoformat(raw["revoked_on"]) if raw.get("revoked_on") else None,
    )


def put_authorization(auth: Authorization) -> None:
    STATE.authorizations[auth.client_id] = {
        "client_id": auth.client_id,
        "helper_name": auth.helper_name,
        "scopes": sorted(s.value for s in auth.scopes),
        "standing": auth.standing.value,
        "signed_on": auth.signed_on.isoformat(),
        "expires_on": auth.expires_on.isoformat(),
        "revoked_on": auth.revoked_on.isoformat() if auth.revoked_on else None,
    }


# --------------------------------------------------------------------------
# accounts
# --------------------------------------------------------------------------

def put_account(account) -> None:
    from dataclasses import asdict as _asdict

    STATE.accounts[account.account_id] = _asdict(account)


def find_account(role: str, login_key: str):
    """Look up by role and normalized key. One index, no cleverness."""
    from app.auth import Account

    for raw in STATE.accounts.values():
        if raw["role"] == role and raw["login_key"] == login_key.upper():
            return Account(**raw)
    return None


def stored_reports(client_id: str, *, confirmed_only: bool = False) -> list:
    """The reports on file, rebuilt as documents a person can read.

    confirmed_only is what the tablet asks for. A report a helper typed in or
    photographed has not been checked by anyone yet, and showing somebody an
    unverified list of their own debts is worse than showing them nothing.
    """
    from app.report import Account, CreditReport

    out = []
    for raw in STATE.reports.get(client_id, []):
        data = dict(raw)
        data["accounts"] = [Account(**a) for a in raw.get("accounts", [])]
        report = CreditReport(**data)
        if confirmed_only and not report.confirmed:
            continue
        out.append(report)
    return out


def pending_reports(client_id: str) -> list:
    """Waiting on a human. This is the coordinator's queue, not a status flag."""
    return [r for r in stored_reports(client_id) if not r.confirmed]


def put_report(report) -> None:
    from dataclasses import asdict as _asdict

    STATE.reports.setdefault(report.client_id, []).append(_asdict(report))


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


def seed() -> None:
    """The caseload from screens 07 through 09, as data.

    Everyone here is invented. The DINs all start 28, meaning a 2028 intake,
    which has not happened yet, so none of them can collide with a real
    person's number in the public DOCCS lookup. The NYSIDs are obviously
    sequential for the same reason.
    """
    today = date.today()

    marcus = Client(
        id="marcus-w",
        din="28A1187",
        nysid="00000011L",
        facility="Sing Sing Correctional Facility",
        display_name="Marcus W.",
        first_name="Marcus",
        # A person mid-dispute chose to work their credit a long time ago.
        path="credit",
        release_date=(today + timedelta(days=118)).isoformat(),
        case_state="errors_present",
        state_label="Errors on the report",
        needs="Dispute letter to approve",
        clock="Releases in 118 days",
        clock_sort=118,
        consent_recorded_on=(today - timedelta(days=205)).isoformat(),
        helper_name="Denise",
report_summary="Thin file, two disputed items",
        collections_count=0,
        last_pulled=(today - timedelta(days=186)).isoformat(),
        plan_step="Dispute letter mailed, waiting on the bureau",
        # Answered on the tablet months ago. Without these he signs in to a
        # live dispute and lands on intake question one.
        intake_answers={
            "knows_score": "no", "knows_how": "no",
            "ever_had_account": "yes", "has_bank_account": "no",
            "collections": "none_found", "obligations": ["none"],
        },
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
            id="m-alvarez", din="28B0042", nysid="00000022K", path="credit",
            facility="Bedford Hills Correctional Facility", display_name="M. Alvarez", first_name="Maria",
            release_date=(today + timedelta(days=9)).isoformat(),
            case_state="errors_present", state_label="Errors present",
            needs="Dispute letter to approve", clock="Releases in 9 days",
            clock_sort=9, helper_name="Rosa",
            consent_recorded_on=(today - timedelta(days=21)).isoformat(),
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
            intake_answers={
                "knows_score": "roughly", "knows_how": "some_idea",
                "ever_had_account": "yes", "has_bank_account": "yes",
                "collections": "none_found", "obligations": ["child_support"],
            },
        ),
        Client(
            id="j-whitfield", din="28A0931", nysid="00000033M",
            facility="Sing Sing Correctional Facility", display_name="J. Whitfield", first_name="James",
            release_date=(today + timedelta(days=21)).isoformat(),
            case_state="not_yet_triaged", state_label="Not yet triaged",
            needs="No report on file", clock="Releases in 21 days",
            clock_sort=21, helper_name=None,
            consent_recorded_on=(today - timedelta(days=4)).isoformat(),
plan_step="Triage session not yet held",
        ),
        Client(
            id="r-osei", din="28C2204", nysid="00000044J", path="credit",
            facility="Fishkill Correctional Facility", display_name="R. Osei", first_name="Rashid",
            release_date=(today + timedelta(days=64)).isoformat(),
            case_state="credit_invisible", state_label="Credit invisible",
            needs="Bureau answer overdue", clock="4 days past due",
            clock_sort=-4, helper_name="Ama",
            consent_recorded_on=(today - timedelta(days=90)).isoformat(),
report_summary="No file found on two of three bureaus",
            last_pulled=(today - timedelta(days=40)).isoformat(),
            plan_step="Builder loan opens after the third bureau answers",
            intake_answers={
                "knows_score": "no", "knows_how": "no",
                "ever_had_account": "no", "has_bank_account": "no",
                "collections": "unknown", "obligations": ["restitution"],
            },
        ),
        Client(
            id="t-brennan", din="28D0775", nysid="00000055H", path="credit",
            facility="Woodbourne Correctional Facility", display_name="T. Brennan", first_name="Tom",
            release_date=(today - timedelta(days=42)).isoformat(),
            case_state="damaged_file", state_label="Damaged file",
            needs="Missed 2 check-ins", clock="Out 6 weeks",
            clock_sort=200, helper_name=None,
            consent_recorded_on=(today - timedelta(days=160)).isoformat(),
report_summary="Full file, nine collections accounts",
            collections_count=9,
            last_pulled=(today - timedelta(days=70)).isoformat(),
            plan_step="Debt triage, then boosters. Expectation set in years.",
            intake_answers={
                "knows_score": "roughly", "knows_how": "yes",
                "ever_had_account": "yes", "has_bank_account": "yes",
                "collections": "many", "obligations": ["court_fines"],
            },
        ),
    ]

    STATE.clients = {c.id: c for c in [marcus, *others, _demo_persona(today)]}
    STATE.authorizations = {}
    put_authorization(
        default_helper_authorization("marcus-w", "Denise", today - timedelta(days=209))
    )
    put_authorization(
        default_helper_authorization("m-alvarez", "Rosa", today - timedelta(days=21))
    )
    STATE.drafts = {}
    STATE.reports = {}
    STATE.review_log = {"reviewed": 0, "edited": 0}
    STATE.write_log = []
    _seed_accounts()
    _seed_reports(today)


def _demo_persona(today: date) -> Client:
    """Armando Torres, who starts with nothing done, so the journey can be walked.

    Everything else in the seed is somewhere in the middle of its story. This
    one is at the front of it: no path chosen, no intake, no reports, no helper
    signed up, and none of the three vital documents on file. The Social
    Security card deadline is still ahead, so the room sees it as something to
    act on rather than something already missed.

    Open on purpose. Nothing here is pre-answered, so whoever drives can take
    Armando from the first screen to a report reviewed on the tablet, by either
    route: a helper sends it in, or the coordinator scans the paper because
    there is nobody outside. The helper has a code and no authorization yet,
    which is the day before she signs the form.
    """
    return Client(
        id="a-torres", din="28E3306", nysid="00000066G",
        facility="Fishkill Correctional Facility",
        display_name="A. Torres", first_name="Armando",
        release_date=(today + timedelta(days=140)).isoformat(),
        case_state="not_yet_triaged", state_label="Not yet triaged",
        needs="No report on file", clock="Releases in 140 days",
        clock_sort=140, helper_name=None,
        consent_recorded_on=(today - timedelta(days=6)).isoformat(),
        plan_step="Triage session not yet held",
        documents={
            "social_security_card": False,
            "birth_certificate": False,
            "non_driver_id": False,
        },
        timeline=[
            asdict(TimelineEvent("Ms. Reyes opened your case",
                                 "Your counselor", today.strftime("%B %-d"))),
        ],
    )


def _seed_reports(today: date) -> None:
    """Three files back for one person, and they do not agree.

    Without these the product could show somebody asking for a report and
    never show one arriving, which is a demo of a waiting room. Everything
    downstream of this point already worked and had nothing to work on.

    The disagreement is the content, not set dressing. Marcus has two problems
    and neither is on all three files: Second Chance Auto is reported open and
    past due at Equifax and TransUnion and correctly closed at Experian, and
    the Midland collection he never opened is missing from TransUnion
    altogether. That is why a dispute goes to all three, and it is why the
    three scores below are three different numbers on the same day.
    """
    from app.report import Account, CreditReport, Source

    pulled = (today - timedelta(days=4)).isoformat()
    scanned = (today - timedelta(days=2)).isoformat()

    # Reported the same way everywhere. An old card, closed and paid, which is
    # the one good thing on this file and the reason it is not empty.
    def cap_one():
        return Account(
            creditor="Capital One Platinum", number="xxxx2210",
            opened="2016-04", status="Closed, paid as agreed", balance="$0",
        )

    def store_card():
        return Account(
            creditor="Fingerhut / WebBank", number="xxxx8830",
            opened="2018-02", status="Closed, paid as agreed", balance="$0",
        )

    # Paid in full before he went in, still being reported open and past due.
    def auto_wrong():
        return Account(
            creditor="Second Chance Auto Finance", number="xxxx0912",
            opened="2017-08", status="Open, 120+ days past due", balance="$4,180",
        )

    def auto_right():
        return Account(
            creditor="Second Chance Auto Finance", number="xxxx0912",
            opened="2017-08", status="Closed, paid in full", balance="$0",
        )

    # Never his. Bought and resold debt attached to the wrong file, which is
    # the single most common thing that happens to somebody whose Social
    # Security number has been on paperwork in a lot of hands.
    def midland():
        return Account(
            creditor="Midland Funding LLC", number="xxxx4471",
            opened="2019-11", status="Collection, open", balance="$1,247",
            note="Original creditor listed as Comenity Bank",
        )

    files = [
        # bureau, score, accounts, inquiries, public records
        ("Equifax", 583, [cap_one(), store_card(), auto_wrong(), midland()],
         ["Second Chance Auto Finance, 2017-08"], []),
        ("Experian", 601, [cap_one(), store_card(), auto_right(), midland()],
         ["Second Chance Auto Finance, 2017-08"], []),
        ("TransUnion", 594, [cap_one(), store_card(), auto_wrong()],
         [], []),
    ]

    for bureau, score, accounts, inquiries, records in files:
        put_report(CreditReport(
            bureau=bureau,
            client_id="marcus-w",
            pulled_on=pulled,
            scanned_on=scanned,
            # A person, because a report that arrived from nobody is the kind
            # of event the timeline rule exists to keep off a screen.
            scanned_by="D. Reyes",
            consumer_name="Marcus W.",
            ssn_on_document="XXX-XX-4417",
            date_of_birth="1988-06-14",
            addresses=[
                "Sing Sing Correctional Facility, Ossining NY",
                "1194 E 224th St, Bronx NY 10466",
            ],
            accounts=accounts,
            inquiries=inquiries,
            public_records=records,
            score=score,
            source=Source.CLIENT_DELIVERED.value,
            confirmed=True,
        ))


def _seed_accounts() -> None:
    """One login per person. No PINs are set: everybody enrolls at first use.

    Seeding a PIN would mean somebody other than the client knew it, which is
    the thing a PIN is for.
    """
    from app.auth import Account

    STATE.accounts = {}

    for client in STATE.clients.values():
        # A client can log in with either number, so both point at one account.
        put_account(Account(
            account_id=f"inside-{client.id}",
            role="inside",
            subject_id=client.id,
            login_key=client.din,
            display_name=client.display_name,
        ))
        put_account(Account(
            account_id=f"inside-{client.id}-nysid",
            role="inside",
            subject_id=client.id,
            login_key=client.nysid,
            display_name=client.display_name,
        ))

    # Helpers get a code on the letter that arrives in the mail. They do not
    # have a DIN and must never be asked for one.
    for client_id, code, name in [
        ("marcus-w", "BRIDGE-4417", "Denise"),
        ("m-alvarez", "BRIDGE-8802", "Rosa"),
        ("j-whitfield", "BRIDGE-2231", ""),
        ("a-torres", "BRIDGE-3306", ""),
    ]:
        put_account(Account(
            account_id=f"family-{client_id}",
            role="family",
            subject_id=client_id,
            login_key=code,
            display_name=name,
        ))

    put_account(Account(
        account_id="staff-reyes",
        role="staff",
        subject_id="",
        login_key="REYES",
        display_name="D. Reyes",
    ))


def restart_person(client_id: str) -> bool:
    """Put one person back to the day the seed describes. Nobody else moves.

    A demo gets walked more than once, and the second walk needs the first
    one gone: the PIN somebody set, the intake they answered, the lessons they
    finished, the letters drafted about them. Without this the only way back
    is restarting the container, which resets everybody and takes a cold start
    with a room watching.

    One person rather than the whole caseload, because two people are usually
    on this URL at once and rewinding the one who wandered off should not take
    the other one with them.

    The signing key is deliberately untouched, so everybody else stays signed
    in. This person does not: their account is seeded back to having no PIN,
    which is the point, and their old cookie names an account that no longer
    has one.
    """
    if client_id not in STATE.clients:
        return False

    live = _serialize()
    seed()
    fresh = _serialize()
    _apply(live)

    if client_id in fresh["clients"]:
        STATE.clients[client_id] = Client(**fresh["clients"][client_id])
        STATE.reports[client_id] = fresh["reports"].get(client_id, [])
        STATE.drafts[client_id] = fresh["drafts"].get(client_id, [])
    else:
        # Somebody who typed their own 28 DIN was never in the seed, so the day
        # the seed describes is the day before they existed. Remove the case and
        # the next sign-in opens a fresh one, the same as the first time.
        STATE.clients.pop(client_id, None)
        STATE.reports.pop(client_id, None)
        STATE.drafts.pop(client_id, None)
    if client_id in fresh["authorizations"]:
        STATE.authorizations[client_id] = fresh["authorizations"][client_id]
    else:
        STATE.authorizations.pop(client_id, None)

    # Accounts are keyed by account id, not by person, so this is a swap of
    # every row pointing at them: the seeded rows carry no pin_hash, and any
    # row the seed does not know about goes.
    seeded = {k: v for k, v in fresh["accounts"].items()
              if v.get("subject_id") == client_id}
    for key in [k for k, v in STATE.accounts.items()
                if v.get("subject_id") == client_id and k not in seeded]:
        del STATE.accounts[key]
    STATE.accounts.update(seeded)

    STATE.write_log = [w for w in STATE.write_log
                       if w.get("client_id") != client_id]
    return True


def boot() -> None:
    if not load():
        seed()
        save()
