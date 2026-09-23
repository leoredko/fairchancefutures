"""The helper's phone.

Constraint two lives in this module. Every handler past the invitation calls
require_scope() against a live, signed, unexpired, unrevoked authorization. A
helper with no grant gets the invitation and nothing else, and a helper whose
grant the client cancelled from the tablet loses access on the next request.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from app.authorization import (
    NotAuthorized,
    POA_TERM_DAYS,
    Scope,
    default_helper_authorization,
    require_scope,
)
from app.deps import get_client, templates
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


@router.get("/{client_id}", response_class=HTMLResponse)
def landing(request: Request, client_id: str, invited: str | None = None):
    client = get_client(client_id)
    auth = get_authorization(client_id)
    if auth is not None and auth.is_live():
        return RedirectResponse(f"/family/{client_id}/task", status_code=303)

    return templates.TemplateResponse(
        request, "family/invitation.html",
        {"client": client,
         "homecoming": _homecoming(client.release_date),
         "term_days": POA_TERM_DAYS,
         "suggested_name": invited or client.helper_name,
         "scopes": [
             "Receive his mail",
             "Add photos of the report",
             "Mail a dispute letter we print for you",
             "Be contacted by his counselor",
         ]},
    )


@router.post("/{client_id}/accept")
def accept(client_id: str, helper_name: str = Form(...)):
    """The signed form. This is the moment standing is created, and the only one."""
    client = get_client(client_id)
    auth = default_helper_authorization(client_id, helper_name.strip()[:40])
    with mutate():
        put_authorization(auth)
        client.helper_name = auth.helper_name
        client.timeline.append({
            "text": f"{auth.helper_name} agreed to help",
            "actor": "Your helper",
            "on": date.today().strftime("%B %-d"),
            "done": True,
        })
    return RedirectResponse(f"/family/{client_id}/task", status_code=303)


@router.get("/{client_id}/task", response_class=HTMLResponse)
def task(request: Request, client_id: str):
    client = get_client(client_id)
    auth = get_authorization(client_id)
    # No live grant means no task surface at all. Back to the invitation.
    if auth is None or not auth.is_live():
        return RedirectResponse(f"/family/{client_id}", status_code=303)
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
            "action_url": f"/family/{client_id}/packet",
            "action_label": "Print the packet",
            "skip_url": f"/family/{client_id}/task/done",
            "skip_label": "I already mailed it",
        }
    elif not client.report_pages:
        current = {
            "headline": "The report should be arriving. Photograph it when it does.",
            "detail": "Flat on a table, good light, one page per photo.",
            "action_url": f"/family/{client_id}/report",
            "action_label": "Add the report",
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


@router.post("/{client_id}/task/done")
def task_done(client_id: str):
    client = get_client(client_id)
    auth = get_authorization(client_id)
    require_scope(auth, Scope.MAIL_DISPUTE_LETTER)
    with mutate():
        client.family_task["done"] = True
        client.timeline.append({
            "text": "Request mailed to the bureau",
            "actor": auth.helper_name, "on": date.today().strftime("%B %-d"),
            "done": True,
        })
    return RedirectResponse(f"/family/{client_id}/task", status_code=303)


@router.get("/{client_id}/packet", response_class=HTMLResponse)
def packet(request: Request, client_id: str):
    """The rung 1 request letter, ready to print. Signature by hand, SSN by hand."""
    from app.letters import draft_report_request

    client = get_client(client_id)
    auth = get_authorization(client_id)
    require_scope(auth, Scope.RECEIVE_MAIL)
    draft = draft_report_request(
        client_id=client_id,
        client_name=client.display_name,
        delivery_address=f"c/o {auth.helper_name}, on file with the program",
    )
    return HTMLResponse(
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>Print the packet</title>"
        "<link rel='stylesheet' href='/static/bridge.css'></head><body>"
        "<div class='desk' style='padding-top:32px;max-width:720px'>"
        f"<h1>Print this, get it signed, mail it</h1>"
        f"<pre class='letter' style='margin-top:16px'>{draft.body}</pre>"
        "<p class='tiny' style='margin-top:12px'>The SSN and date of birth lines "
        "are blank on purpose. They are filled in by hand on the paper copy and "
        "never typed into this app.</p>"
        f"<p style='margin-top:16px'><a class='btn' href='/family/{client_id}/task'>Back</a></p>"
        "</div></body></html>"
    )


@router.get("/{client_id}/report", response_class=HTMLResponse)
def add_report_form(request: Request, client_id: str):
    require(Surface.FAMILY, Capability.UPLOAD_FILE)
    client = get_client(client_id)
    auth = get_authorization(client_id)
    require_scope(auth, Scope.SUBMIT_REPORT_IMAGES)
    return templates.TemplateResponse(
        request, "family/add_report.html",
        {"client": client, "pages": client.report_pages},
    )


@router.post("/{client_id}/report")
async def add_report(client_id: str, pages: list[UploadFile] = None):
    """Filenames only.

    Photo-to-text extraction is the one genuinely hard engineering piece and it
    is out of scope here. The deck already named the fallback: the caseworker
    enters the findings. So the image bytes are counted and discarded rather
    than stored, which also means this build never holds a picture of somebody's
    credit report on disk.
    """
    require(Surface.FAMILY, Capability.UPLOAD_FILE)
    client = get_client(client_id)
    auth = get_authorization(client_id)
    require_scope(auth, Scope.SUBMIT_REPORT_IMAGES)

    names = [p.filename for p in (pages or []) if p and p.filename]
    with mutate():
        for i, _ in enumerate(names, start=len(client.report_pages) + 1):
            client.report_pages.append(f"Page {i}")
        if names:
            client.timeline.append({
                "text": f"{len(names)} page(s) of the report added",
                "actor": auth.helper_name,
                "on": date.today().strftime("%B %-d"),
                "done": True,
            })
    return RedirectResponse(f"/family/{client_id}/task", status_code=303)
