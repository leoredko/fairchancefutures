"""The facility tablet.

Two gates on every handler. require_role says who is asking, from the signed
cookie; surfaces.require says what this surface can do, from the capability
table. The URL carries no identity, so there is nothing in it to guess at.

There is no route here for uploading a file or verifying an identity, and if
someone adds one later the capability check refuses it before it does anything.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.authorization import FORBIDDEN_SCOPES, RUNG_DETAIL
from app.deps import templates
from app.questions import INSIDE_QUESTIONS, inside_question
from app.session import require_role
from app.store import STATE, get_authorization, mutate, put_authorization
from app.surfaces import Capability, Surface, require

router = APIRouter(prefix="/inside")

POSITION = {
    "not_yet_triaged": 1,
    "credit_invisible": 1,
    "damaged_file": 1,
    "thin_file": 2,
    "errors_present": 2,
}


@router.get("", response_class=HTMLResponse)
def home(request: Request):
    """Straight to the case if intake is done, otherwise pick up where they left off."""
    caller = require_role(request, "inside")
    answered = caller.client.intake_answers
    if len(answered) >= len(INSIDE_QUESTIONS):
        return RedirectResponse("/inside/case", status_code=303)
    for question in INSIDE_QUESTIONS:
        if question.field not in answered:
            return RedirectResponse(f"/inside/intake/{question.index}", status_code=303)
    return RedirectResponse("/inside/case", status_code=303)


@router.get("/intake/{index}", response_class=HTMLResponse)
def intake(request: Request, index: int):
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.ANSWER_INTAKE)
    question = inside_question(index)
    return templates.TemplateResponse(
        request, "inside/intake.html",
        {"client": caller.client, "q": question, "total": len(INSIDE_QUESTIONS),
         "saved": caller.client.intake_answers.get(question.field)},
    )


@router.post("/intake/{index}")
async def answer(request: Request, index: int):
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.ANSWER_INTAKE)
    client = caller.client
    question = inside_question(index)
    form = await request.form()

    with mutate():
        if question.multi:
            picked = [v for v in form.getlist(question.field) if v != "none"]
            client.intake_answers[question.field] = picked or ["none"]
        else:
            client.intake_answers[question.field] = form.get(question.field)
        # Offline-first in the real tablet means queueing locally and flushing
        # on connect. The queue is modelled so /api/sync has something real to
        # drain rather than a claim in a docstring.
        STATE.sync_queue.append({
            "client_id": client.id, "field": question.field,
            "value": client.intake_answers[question.field],
            "at": date.today().isoformat(), "synced": True,
        })

    if index >= len(INSIDE_QUESTIONS):
        return RedirectResponse("/inside/where-you-stand", status_code=303)
    return RedirectResponse(f"/inside/intake/{index + 1}", status_code=303)


@router.get("/where-you-stand", response_class=HTMLResponse)
def where_you_stand(request: Request):
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.VIEW_OWN_STATUS)
    client = caller.client

    if client.case_state == "credit_invisible" or not client.classification:
        moves = [
            {"title": "You don't have a file yet",
             "body": "That is not the same as bad credit. Empty moves faster "
                     "than damaged does."},
            {"title": "One account, paid on time, starts the clock",
             "body": "Ms. Reyes will set this up with you before you go home."},
        ]
    else:
        moves = [
            {"title": "Your file exists and two items are disputed",
             "body": "Ms. Reyes approved the letter. The bureaus have to answer."},
            {"title": "One account, paid on time, keeps the clock running",
             "body": "Set up before release, not after."},
        ]
    if any(o != "none" for o in client.intake_answers.get("obligations", [])):
        moves.append({
            "title": "What the court ordered is tracked separately",
            "body": "It matters, and it does not sit in this list pretending to "
                    "be a credit card."})

    return templates.TemplateResponse(
        request, "inside/where_you_stand.html",
        {"client": client, "moves": moves,
         "position": POSITION.get(client.case_state, 1)},
    )


@router.get("/case", response_class=HTMLResponse)
def case(request: Request):
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.VIEW_OWN_STATUS)
    auth = get_authorization(caller.client.id)
    return templates.TemplateResponse(
        request, "inside/case.html",
        {"client": caller.client, "timeline": caller.client.timeline,
         "auth": auth if auth and auth.is_live() else None,
         "synced": "just now"},
    )


@router.get("/authorization", response_class=HTMLResponse)
def authorization(request: Request):
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.REVOKE_AUTHORIZATION)
    auth = get_authorization(caller.client.id)
    return templates.TemplateResponse(
        request, "inside/authorization.html",
        {"client": caller.client, "auth": auth,
         "scopes": sorted(s.value.replace("_", " ") for s in auth.scopes) if auth else [],
         "rung_label": RUNG_DETAIL[auth.rung]["label"] if auth else "",
         "forbidden": sorted(f.replace("_", " ") for f in FORBIDDEN_SCOPES)},
    )


@router.post("/authorization/revoke")
def revoke(request: Request):
    """The client cancels, from the tablet, without telling the helper first."""
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.REVOKE_AUTHORIZATION)
    auth = get_authorization(caller.client.id)
    with mutate():
        if auth is not None:
            put_authorization(auth.revoked())
        caller.client.helper_name = None
        caller.client.timeline.append({
            "text": "You cancelled the authorization",
            "actor": "You", "on": date.today().strftime("%B %-d"), "done": True,
        })
    return RedirectResponse("/inside/authorization", status_code=303)


@router.post("/authorization/name")
def name_helper(request: Request, helper_name: str = Form(...)):
    """Naming someone starts an invitation. It grants nothing.

    The grant is created on the family surface, by the helper, after they have
    been shown what they are agreeing to. A person cannot consent on someone
    else's behalf, which is the whole reason the two screens are separate.
    """
    caller = require_role(request, "inside")
    require(Surface.INSIDE, Capability.NAME_HELPER)
    with mutate():
        caller.client.helper_name = helper_name.strip()[:40]
    return RedirectResponse("/inside/authorization", status_code=303)
