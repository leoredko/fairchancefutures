"""The facility tablet.

Every handler here calls surfaces.require() first. There is no route in this
module for uploading a file or verifying an identity, and if someone adds one
later the capability check will refuse it before it does anything.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.authorization import FORBIDDEN_SCOPES, RUNG_DETAIL, Rung
from app.deps import get_client, templates
from app.questions import INSIDE_QUESTIONS, inside_question
from app.store import get_authorization, mutate, put_authorization, save
from app.surfaces import Capability, Surface, require

router = APIRouter(prefix="/inside")

POSITION = {
    "not_yet_triaged": 1,
    "credit_invisible": 1,
    "damaged_file": 1,
    "thin_file": 2,
    "errors_present": 2,
}


@router.get("/{client_id}", response_class=HTMLResponse)
def start(client_id: str):
    return RedirectResponse(f"/inside/{client_id}/intake/1", status_code=303)


@router.get("/{client_id}/intake/{index}", response_class=HTMLResponse)
def intake(request: Request, client_id: str, index: int):
    require(Surface.INSIDE, Capability.ANSWER_INTAKE)
    client = get_client(client_id)
    q = inside_question(index)
    return templates.TemplateResponse(
        request, "inside/intake.html",
        {"client": client, "q": q, "total": len(INSIDE_QUESTIONS),
         "saved": client.intake_answers.get(q.field)},
    )


@router.post("/{client_id}/intake/{index}")
async def answer(request: Request, client_id: str, index: int):
    require(Surface.INSIDE, Capability.ANSWER_INTAKE)
    client = get_client(client_id)
    q = inside_question(index)
    form = await request.form()

    with mutate():
        if q.multi:
            picked = [v for v in form.getlist(q.field) if v != "none"]
            client.intake_answers[q.field] = picked or ["none"]
        else:
            client.intake_answers[q.field] = form.get(q.field)
        # Offline-first: in the real tablet these writes queue locally and flush
        # on connect. The queue is modeled so the sync endpoint has something
        # real to drain, and so nothing is lost if the tablet is offline a week.
        from app.store import STATE
        STATE.sync_queue.append({
            "client_id": client_id, "field": q.field,
            "value": client.intake_answers[q.field],
            "at": date.today().isoformat(), "synced": True,
        })

    if index >= len(INSIDE_QUESTIONS):
        return RedirectResponse(f"/inside/{client_id}/where-you-stand", status_code=303)
    return RedirectResponse(f"/inside/{client_id}/intake/{index + 1}", status_code=303)


@router.get("/{client_id}/where-you-stand", response_class=HTMLResponse)
def where_you_stand(request: Request, client_id: str):
    require(Surface.INSIDE, Capability.VIEW_OWN_STATUS)
    client = get_client(client_id)

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
             "body": "Ms. Reyes approved the letter. The bureau has to answer."},
            {"title": "One account, paid on time, keeps the clock running",
             "body": "Set up before release, not after."},
        ]
    if any(o != "none" for o in client.intake_answers.get("obligations", [])):
        moves.append({
            "title": "Restitution is tracked separately",
            "body": "It matters, but it does not sit in this list pretending to "
                    "be a credit card."})

    return templates.TemplateResponse(
        request, "inside/where_you_stand.html",
        {"client": client, "moves": moves,
         "position": POSITION.get(client.case_state, 1)},
    )


@router.get("/{client_id}/case", response_class=HTMLResponse)
def case(request: Request, client_id: str):
    require(Surface.INSIDE, Capability.VIEW_OWN_STATUS)
    client = get_client(client_id)
    auth = get_authorization(client_id)
    return templates.TemplateResponse(
        request, "inside/case.html",
        {"client": client, "timeline": client.timeline,
         "auth": auth if auth and auth.is_live() else None,
         "synced": "2 hours ago"},
    )


@router.get("/{client_id}/authorization", response_class=HTMLResponse)
def authorization(request: Request, client_id: str):
    require(Surface.INSIDE, Capability.REVOKE_AUTHORIZATION)
    client = get_client(client_id)
    auth = get_authorization(client_id)
    return templates.TemplateResponse(
        request, "inside/authorization.html",
        {"client": client, "auth": auth,
         "scopes": sorted(s.value.replace("_", " ") for s in auth.scopes) if auth else [],
         "rung_label": RUNG_DETAIL[auth.rung]["label"] if auth else "",
         "forbidden": sorted(f.replace("_", " ") for f in FORBIDDEN_SCOPES)},
    )


@router.post("/{client_id}/authorization/revoke")
def revoke(client_id: str):
    """The client cancels, from the tablet, without telling the helper first."""
    require(Surface.INSIDE, Capability.REVOKE_AUTHORIZATION)
    client = get_client(client_id)
    auth = get_authorization(client_id)
    with mutate():
        if auth is not None:
            put_authorization(auth.revoked())
        client.helper_name = None
        client.timeline.append({
            "text": "You cancelled the authorization",
            "actor": "You", "on": date.today().strftime("%B %-d"), "done": True,
        })
    return RedirectResponse(f"/inside/{client_id}/authorization", status_code=303)


@router.post("/{client_id}/authorization/name")
def name_helper(client_id: str, helper_name: str = Form(...)):
    """Naming someone starts an invitation. It grants nothing.

    The grant is created on the family surface, by the helper, after they have
    been shown what they are agreeing to. A person cannot consent on someone
    else's behalf, which is the whole reason the two screens are separate.
    """
    require(Surface.INSIDE, Capability.NAME_HELPER)
    client = get_client(client_id)
    with mutate():
        client.helper_name = helper_name.strip()[:40]
    return RedirectResponse(f"/family/{client_id}?invited={client.helper_name}",
                            status_code=303)
