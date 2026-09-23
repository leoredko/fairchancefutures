"""The caseworker desktop.

Two screens in scope, per the deck: the triage session and the client detail
with letter approval. Referrals and outcomes are not built.

Note what staff do NOT get: the raw client record never reaches a template.
Everything goes through redaction.for_surface() first, so the SSN and full
account numbers are absent from the rendered HTML rather than merely hidden by
CSS.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.authorization import RUNG_DETAIL, Rung, next_rung
from app.deps import get_client, templates
from app.letters import draft_dispute
from app.questions import STAFF_QUESTIONS
from app.redaction import WITHHELD_NOTE, for_surface
from app.store import (
    STATE,
    add_draft,
    drafts_for,
    get_authorization,
    mutate,
    put_review_log,
    review_log,
)
from app.surfaces import Capability, Surface, require
from app.triage import PATH, STATE_LABEL, Answers, Classification, State, classify

router = APIRouter(prefix="/staff")


def _ladder_rows(client) -> list[dict]:
    rows = []
    for rung in Rung:
        detail = RUNG_DETAIL[rung]
        rows.append({
            "n": int(rung),
            "label": f"{int(rung)} · {detail['label']}",
            "asks_for": detail["asks_for"],
            "cost": detail["cost"],
            "status": client.ladder_status.get(str(int(rung)), "Not needed"),
        })
    return rows


@router.get("", response_class=HTMLResponse)
def queue(request: Request):
    """A work queue, not a roster. Sorted by what expires soonest."""
    require(Surface.STAFF, Capability.MANAGE_CASELOAD)
    clients = sorted(STATE.clients.values(), key=lambda c: c.clock_sort)
    return templates.TemplateResponse(request, "staff/queue.html", {"clients": clients})


@router.get("/{client_id}/triage", response_class=HTMLResponse)
def triage_form(request: Request, client_id: str):
    require(Surface.STAFF, Capability.TRIAGE_CLIENT)
    client = get_client(client_id)
    return templates.TemplateResponse(
        request, "staff/triage.html",
        {"client": client, "questions": STAFF_QUESTIONS,
         "answers": _prefill(client), "result": _stored_result(client),
         "all_states": _all_states()},
    )


@router.post("/{client_id}/triage", response_class=HTMLResponse)
async def triage_run(request: Request, client_id: str):
    require(Surface.STAFF, Capability.TRIAGE_CLIENT)
    client = get_client(client_id)
    form = await request.form()

    answers = Answers(
        ever_had_account=_enum("ever_had_account", form),
        report_result=_enum("report_result", form),
        collections=_enum("collections", form),
        has_bank_account=_enum("has_bank_account", form),
        obligations=_obligations(form),
        recognizes_everything=_enum("recognizes_everything", form),
    )
    result = classify(answers)

    with mutate():
        client.intake_answers.update({
            "ever_had_account": answers.ever_had_account.value,
            "report_result": answers.report_result.value,
            "collections": answers.collections.value,
            "has_bank_account": answers.has_bank_account.value,
            "obligations": [o.value for o in answers.obligations],
            "recognizes_everything": answers.recognizes_everything.value,
        })
        client.case_state = result.state.value
        client.state_label = result.label
        client.classification = {
            "state": result.state.value,
            "reasons": result.reasons,
            "needs_human_review": result.needs_human_review,
            "obligations_route": result.obligations_route,
            "classified_on": date.today().isoformat(),
        }
        client.plan_step = result.path["first_step"]
        # Errors carry a legal clock, so they jump the queue. Everything else
        # keeps its release-date ordering.
        if result.jumps_queue:
            client.clock_sort = min(client.clock_sort, -1)
            client.needs = "Dispute letter to approve"
        elif result.state is State.NOT_YET_TRIAGED:
            client.needs = "No report on file"
        else:
            client.needs = result.path["first_step"]

    return templates.TemplateResponse(
        request, "staff/triage.html",
        {"client": client, "questions": STAFF_QUESTIONS,
         "answers": _prefill(client), "result": result,
         "all_states": _all_states()},
    )


@router.get("/{client_id}", response_class=HTMLResponse)
def client_detail(request: Request, client_id: str):
    require(Surface.STAFF, Capability.MANAGE_CASELOAD)
    client = get_client(client_id)

    view = for_surface(asdict(client), Surface.STAFF, set(client.consent_scopes))
    drafts = drafts_for(client_id)
    pending = next((d for d in drafts if d["approved_on"] is None), None)
    approved = [d for d in drafts if d["approved_on"]]

    caption = ""
    if pending and client.flagged_items:
        caption = (
            f"Item 1 of {len(client.flagged_items)} · reason: "
            f"{client.flagged_items[0]['reason']}"
        )

    return templates.TemplateResponse(
        request, "staff/client.html",
        {"client": client, "view": view, "withheld_note": WITHHELD_NOTE,
         "ladder": _ladder_rows(client), "draft": pending,
         "draft_caption": caption, "approved": approved,
         "flagged": client.flagged_items if "flagged_items" in view else [],
         "review_summary": review_log().summary()},
    )


@router.post("/{client_id}/letters/draft")
def draft_letter(client_id: str, item: int = Form(0)):
    require(Surface.STAFF, Capability.APPROVE_LETTER)
    client = get_client(client_id)
    if not client.flagged_items:
        return RedirectResponse(f"/staff/{client_id}", status_code=303)
    flagged = client.flagged_items[min(item, len(client.flagged_items) - 1)]
    draft = draft_dispute(
        client_id=client_id,
        client_name=client.display_name,
        bureau="Equifax Information Services LLC",
        creditor=flagged["creditor"],
        last_four=flagged["last_four"],
        reason=flagged["reason"],
    )
    with mutate():
        add_draft(draft)
    return RedirectResponse(f"/staff/{client_id}", status_code=303)


@router.post("/{client_id}/letters/{draft_id}/approve")
def approve_letter(client_id: str, draft_id: str, body: str = Form(...)):
    """Approval records whether the reviewer edited first. That is the metric."""
    require(Surface.STAFF, Capability.APPROVE_LETTER)
    client = get_client(client_id)
    row = next((d for d in drafts_for(client_id) if d["id"] == draft_id), None)
    if row is None:
        return RedirectResponse(f"/staff/{client_id}", status_code=303)

    edited = body.strip() != row["body"].strip()
    log = review_log()
    log.record(edited=edited)

    with mutate():
        row["body"] = body
        row["approved_on"] = date.today().isoformat()
        row["edited_before_approval"] = edited
        put_review_log(log)
        client.timeline.append({
            "text": "Ms. Reyes approved your dispute letter",
            "actor": "Your counselor",
            "on": date.today().strftime("%B %-d"),
            "done": True,
        })
    return RedirectResponse(f"/staff/{client_id}", status_code=303)


@router.post("/{client_id}/ladder/escalate")
def escalate(client_id: str):
    """A bureau kicked the request back. Climb exactly one rung, not four."""
    require(Surface.STAFF, Capability.MANAGE_CASELOAD)
    client = get_client(client_id)
    auth = get_authorization(client_id)
    helper_present = auth is not None and auth.is_live()
    nxt = next_rung(Rung(client.ladder_rung), helper_present)
    if nxt is None:
        return RedirectResponse(f"/staff/{client_id}", status_code=303)
    with mutate():
        client.ladder_status[str(client.ladder_rung)] = "Kicked back"
        client.ladder_rung = int(nxt)
        client.ladder_status[str(int(nxt))] = "In progress"
    return RedirectResponse(f"/staff/{client_id}", status_code=303)


# --------------------------------------------------------------------------

def _enum(field: str, form):
    from app import triage

    mapping = {
        "ever_had_account": triage.AccountHistory,
        "report_result": triage.ReportResult,
        "collections": triage.Collections,
        "has_bank_account": triage.BankAccount,
        "recognizes_everything": triage.Recognition,
    }
    raw = form.get(field)
    enum_cls = mapping[field]
    try:
        return enum_cls(raw)
    except ValueError:
        return list(enum_cls)[0]


def _obligations(form):
    from app.triage import Obligation

    picked = []
    for raw in form.getlist("obligations"):
        try:
            picked.append(Obligation(raw))
        except ValueError:
            continue
    # "None" plus something else is a mis-click, not a contradiction to honor.
    real = [o for o in picked if o is not Obligation.NONE]
    return tuple(real) or (Obligation.NONE,)


def _prefill(client) -> dict:
    """The tablet answers pre-fill the staff form.

    Not report_result: there is no tablet answer for it, because a person
    inside cannot pull their own report. That gap is the constraint showing up
    in the UI rather than being written about.
    """
    answers = dict(client.intake_answers)
    answers.setdefault("obligations", ["none"])
    return answers


def _stored_result(client) -> Classification | None:
    stored = client.classification
    if not stored:
        return None
    state = State(stored["state"])
    return Classification(
        state=state, label=STATE_LABEL[state], path=PATH[state],
        reasons=stored.get("reasons", []),
        needs_human_review=stored.get("needs_human_review", False),
        obligations_route=stored.get("obligations_route", []),
    )


def _all_states() -> list[dict]:
    order = [State.CREDIT_INVISIBLE, State.THIN_FILE, State.DAMAGED_FILE,
             State.ERRORS_PRESENT]
    return [{"key": s.value, "label": STATE_LABEL[s], "plan": PATH[s]["plan"]}
            for s in order]
