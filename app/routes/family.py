"""The helper's phone.

Two gates here too, and a third that is specific to this surface: a signed,
scoped, unexpired, unrevoked authorization. Signing in with the code from the
letter proves which case you are here about. It does not grant you anything.
The grant is the form, and the form is checked on every request, so a client
who cancels from the tablet cuts access off at the next tap.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.authorization import (
    POA_TERM_DAYS,
    Scope,
    default_helper_authorization,
    require_scope,
)
from app.deps import templates
from app.session import require_role
from app.store import get_authorization, mutate, put_authorization
from app.surfaces import Capability, Surface, require

router = APIRouter(prefix="/family")


def _homecoming(iso: str) -> str:
    """Plain words, not a countdown. 'in about four months' is how a person
    would say it."""
    days = (date.fromisoformat(iso) - date.today()).days
    if days <= 0:
        return "He is home already"
    if days < 14:
        return f"He comes home in about {days} days"
    if days < 45:
        return "He comes home in about a month"
    return f"He comes home in about {round(days / 30)} months"


@router.get("", response_class=HTMLResponse)
def landing(request: Request):
    caller = require_role(request, "family")
    client = caller.client
    auth = get_authorization(client.id)
    if auth is not None and auth.is_live():
        return RedirectResponse("/family/task", status_code=303)

    return templates.TemplateResponse(
        request, "family/invitation.html",
        {"client": client,
         "homecoming": _homecoming(client.release_date),
         "term_days": POA_TERM_DAYS,
         "suggested_name": client.helper_name,
         "scopes": [
             "Receive his mail",
             "Mail a dispute letter we print for you",
             "Be contacted by his counselor",
         ]},
    )


@router.post("/accept")
def accept(request: Request, helper_name: str = Form(...)):
    """The signed form. This is the moment standing is created, and the only one."""
    caller = require_role(request, "family")
    client = caller.client
    auth = default_helper_authorization(client.id, helper_name.strip()[:40])
    with mutate():
        put_authorization(auth)
        client.helper_name = auth.helper_name
        client.timeline.append({
            "text": f"{auth.helper_name} agreed to help",
            "actor": "Your helper",
            "on": date.today().strftime("%B %-d"),
            "done": True,
        })
    return RedirectResponse("/family/task", status_code=303)


@router.get("/task", response_class=HTMLResponse)
def task(request: Request):
    caller = require_role(request, "family")
    client = caller.client
    auth = get_authorization(client.id)
    # No live grant means no task surface at all. Back to the invitation.
    if auth is None or not auth.is_live():
        return RedirectResponse("/family", status_code=303)
    require_scope(auth, Scope.BE_CONTACTED_BY_STAFF)

    # One task on screen. Never two.
    if not client.report_pages and not client.family_task.get("done"):
        current = {
            "headline": client.family_task.get(
                "headline", "Print the request, have "
                f"{client.first_name} sign it, mail it."),
            "detail": client.family_task.get(
                "detail", "We filled in everything except his signature. The "
                          "envelope prints addressed. One stamp."),
            "action_url": "/family/packet",
            "action_label": "Print the packet",
            "skip_url": "/family/task/done",
            "skip_label": "I already mailed it",
        }
    elif not client.report_pages:
        current = {
            "headline": "Nothing to do until the mail comes back.",
            "detail": f"When the report arrives, send it in to {client.first_name} "
                      "at the facility. He walks it to his counselor, who scans "
                      "it into the record. You do not photograph anything.",
            "action_url": None,
            "action_label": "",
            "skip_url": None,
            "skip_label": "",
        }
    else:
        current = None

    done = [e for e in client.timeline if e.get("done")][:3]
    return templates.TemplateResponse(
        request, "family/task.html",
        {"client": client, "auth": auth, "task": current, "done": done},
    )


@router.post("/task/done")
def task_done(request: Request):
    caller = require_role(request, "family")
    client = caller.client
    auth = get_authorization(client.id)
    require_scope(auth, Scope.MAIL_DISPUTE_LETTER)
    with mutate():
        client.family_task["done"] = True
        client.timeline.append({
            "text": "Request mailed to the bureaus",
            "actor": auth.helper_name, "on": date.today().strftime("%B %-d"),
            "done": True,
        })
    return RedirectResponse("/family/task", status_code=303)


@router.get("/packet", response_class=HTMLResponse)
def packet(request: Request):
    """The rung 1 request letter, ready to print. Signature by hand, SSN by hand."""
    from app.letters import draft_report_request

    caller = require_role(request, "family")
    client = caller.client
    auth = get_authorization(client.id)
    require_scope(auth, Scope.RECEIVE_MAIL)
    draft = draft_report_request(
        client_id=client.id,
        client_name=client.display_name,
        delivery_address=f"c/o {auth.helper_name}, on file with the program",
        identification=client.din,
        id_label="DIN",
        facility=client.facility,
    )
    return templates.TemplateResponse(
        request, "family/packet.html",
        {"client": client, "draft": draft},
    )
