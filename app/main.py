"""Bridge.

A reentry credit-repair workflow, split across three surfaces because the
people involved genuinely cannot do each other's jobs.

Run it:  uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.authorization import FORBIDDEN_SCOPES, NotAuthorized, RUNG_DETAIL, Rung
from app.deps import templates
from app.routes import family, inside, staff
from app.store import STATE, boot, review_log
from app.surfaces import CAPABILITIES, DENIAL_REASON, Surface, SurfaceDenied

@asynccontextmanager
async def lifespan(_: FastAPI):
    boot()
    yield


app = FastAPI(title="Bridge", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(inside.router)
app.include_router(family.router)
app.include_router(staff.router)


@app.exception_handler(SurfaceDenied)
def surface_denied(request: Request, exc: SurfaceDenied):
    """A surface reached for something it structurally cannot do.

    403, with the reason, because the honest answer is not 'you lack permission'
    but 'this is not possible from where you are sitting'.
    """
    return templates.TemplateResponse(
        request, "denied.html",
        {"headline": f"A {exc.surface.value} surface cannot "
                     f"{exc.capability.value.replace('_', ' ')}",
         "reason": exc.reason,
         "footnote": "This is a server-side refusal, not a hidden button. The "
                     "capability table in app/surfaces.py is the product spec, "
                     "and the router checks it before doing anything."},
        status_code=403,
    )


@app.exception_handler(NotAuthorized)
def not_authorized(request: Request, exc: NotAuthorized):
    return templates.TemplateResponse(
        request, "denied.html",
        {"headline": "Nobody has authorized this",
         "reason": exc.detail,
         "footnote": "A helper outside has no standing without a signed, scoped "
                     "form. The grant is checked on every request, so a "
                     "cancellation from the tablet takes effect immediately."},
        status_code=403,
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/roles", response_class=HTMLResponse)
def roles(request: Request):
    """Generated from the capability table, not from a copy of it.

    If somebody widens what the tablet can do, this page changes on the next
    reload. A scope slide that drifts from the code is worse than no slide.
    """
    titles = {Surface.INSIDE: ("Inside", "facility tablet",
                               "Offline-first. Metered by the minute. One question per screen."),
              Surface.FAMILY: ("Family or friend", "phone, web",
                               "One task on screen at a time. Long silences between tasks, by design."),
              Surface.STAFF: ("Caseworker", "desktop",
                              "Work queue sorted by what expires first. Never a roster.")}

    every = set().union(*CAPABILITIES.values())
    surfaces = []
    for surface, (title, device, rule) in titles.items():
        allowed = CAPABILITIES[surface]
        surfaces.append({
            "title": title, "device": device, "rule": rule,
            "can": [c.value.replace("_", " ") for c in sorted(allowed, key=lambda c: c.value)],
            "cannot": [
                f"{c.value.replace('_', ' ')} — {DENIAL_REASON.get(c, '')}"
                for c in sorted(every - allowed, key=lambda c: c.value)
            ],
        })

    ladder = [{"n": int(r), **RUNG_DETAIL[r]} for r in Rung]
    verify = [
        "Dispute and reinvestigation window, and what starts the clock",
        "Whether court fines, restitution and child support report, and when",
        "Free report entitlement and the mail-in route",
        "What actually triggers a bureau to escalate past rung 1",
        "Which ID documents each bureau accepts at rung 2",
    ]
    return templates.TemplateResponse(
        request, "roles.html",
        {"surfaces": surfaces, "ladder": ladder, "verify": verify,
         "forbidden": sorted(f.replace("_", " ") for f in FORBIDDEN_SCOPES)},
    )


@app.get("/metrics", response_class=HTMLResponse)
def metrics(request: Request):
    log = review_log()
    return templates.TemplateResponse(
        request, "metrics.html",
        {"log": log, "summary": log.summary(), "triage_cases": _triage_case_count()},
    )


@app.get("/api/sync")
def sync() -> JSONResponse:
    """What the tablet flushes when it finds a connection.

    Real offline-first would queue on the device. This endpoint exists so the
    demo can show the queue draining rather than describing it.
    """
    return JSONResponse({
        "pending": [q for q in STATE.sync_queue if not q.get("synced")],
        "synced": len([q for q in STATE.sync_queue if q.get("synced")]),
    })


def _triage_case_count() -> int:
    from pathlib import Path
    import re

    path = Path("tests/test_triage.py")
    if not path.exists():
        return 0
    return len(re.findall(r"^\s*Case\(", path.read_text(), flags=re.M))
