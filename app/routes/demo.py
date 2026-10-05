"""Demo controls, kept apart from the product on purpose.

Bridge is walked through more than once: by the team, by a room, by whoever
opens the link next. The second walk needs the first one gone, and the only
way back used to be restarting the container, which resets everybody and
buys a cold start with an audience waiting.

So: put one person back to the day the seed describes. One person rather than
the caseload, because two people are usually on the URL at once.

This is not a product capability and it is not in `app/surfaces.py`. A real
case file holds a coordinator's work and a person cannot erase it from their
tablet. Saying otherwise in the capability table would be a lie about the
product to make a demo convenient, so the control lives here, labelled as
what it is, and the table stays honest.
"""

from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.auth import COOKIE_NAME
from app.deps import templates
from app.session import current
from datetime import date

from app.store import STATE, mutate, put_sample_reports, restart_person

router = APIRouter()


def _people() -> list[dict]:
    """Everybody who can be restarted, with what a restart would throw away."""
    rows = []
    for client in STATE.clients.values():
        has_pin = any(
            raw.get("subject_id") == client.id and raw.get("pin_hash")
            for raw in STATE.accounts.values()
        )
        rows.append({
            "id": client.id,
            "name": client.display_name,
            "din": client.din,
            "has_pin": has_pin,
            "answers": len(client.intake_answers),
            "lessons": len(client.lesson_progress),
        })
    return sorted(rows, key=lambda r: r["name"])


@router.get("/demo/restart", response_class=HTMLResponse)
def restart_form(request: Request):
    """Reachable signed out, because a forgotten PIN is the usual reason to be
    here and the PIN is the thing being cleared."""
    session = current(request)
    return templates.TemplateResponse(
        request, "demo_restart.html",
        {"session": session, "people": _people(), "done": None},
    )


@router.post("/demo/restart", response_class=HTMLResponse)
def restart_do(request: Request, client_id: str = Form(...)):
    session = current(request)
    with mutate():
        ok = restart_person(client_id)
    if not ok:
        return templates.TemplateResponse(
            request, "demo_restart.html",
            {"session": session, "people": _people(), "done": None,
             "error": "Nobody here has that id."},
            status_code=404,
        )

    response = templates.TemplateResponse(
        request, "demo_restart.html",
        {"session": session, "people": _people(), "done": client_id,
         "done_din": STATE.clients[client_id].din if client_id in STATE.clients else ""},
    )
    # Whoever did this is very likely signed in as the person they just
    # rewound, and that person no longer has a PIN. Leaving the cookie in
    # place would put them back on a case that has forgotten them.
    if session and session.subject_id == client_id:
        response.delete_cookie(COOKIE_NAME, path="/")
    return response


@router.post("/demo/sample-report", response_class=HTMLResponse)
def sample_report(request: Request, client_id: str = Form(...)):
    """Three sample files for one person, so "view report" has something to open.

    A demo control and not the product: in the product a report reaches the
    person only after a coordinator has read the paper and confirmed it, and
    that is the route the walkthrough shows. This is the shortcut for a room
    that wants to see the reading screens without waiting for the paper. A
    restart takes the reports away again, because they are not in the seed.
    """
    session = current(request)
    client = STATE.clients.get(client_id)
    if client is None:
        return templates.TemplateResponse(
            request, "demo_restart.html",
            {"session": session, "people": _people(), "done": None,
             "error": "Nobody here has that id."},
            status_code=404,
        )
    # Pressed twice, the second press would stack a second set of three files
    # on the first, so a person who already has reports is left alone.
    with mutate():
        if not STATE.reports.get(client.id):
            put_sample_reports(
                date.today(), client.id, client.display_name,
                f"XXX-XX-{client.din[-4:]}", "1991-03-02",
                [f"{client.facility}, New York"],
            )
    return templates.TemplateResponse(
        request, "demo_restart.html",
        {"session": session, "people": _people(), "done": None,
         "sampled": client.display_name},
    )
