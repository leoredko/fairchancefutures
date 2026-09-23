"""Bridge.

A reentry credit-repair workflow, split across three surfaces because the
people involved genuinely cannot do each other's jobs.

Run it:  uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)
from fastapi.staticfiles import StaticFiles

from app.authorization import FORBIDDEN_SCOPES, NotAuthorized
from app.bureaus import BUREAUS
from app.sources import FACTS, OPEN_QUESTIONS
from app import labels
from app.deps import templates
from app.routes import access, family, inside, staff
from app.store import STATE, boot, review_log
from app.session import NotSignedIn, current, redirect_to_signin
from app.surfaces import CAPABILITIES, DENIAL_REASON, Surface, SurfaceDenied

@asynccontextmanager
async def lifespan(_: FastAPI):
    boot()
    yield


app = FastAPI(title="Bridge", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(access.router)
app.include_router(inside.router)
app.include_router(family.router)
app.include_router(staff.router)


@app.exception_handler(NotSignedIn)
def not_signed_in(request: Request, exc: NotSignedIn):
    """Send them to the right door rather than explaining which doors exist."""
    return redirect_to_signin(exc)


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


# The manifest and the worker are served from the root, not from /static.
# A service worker can only control pages at or below its own path, so one
# parked under /static could never claim the app.
@app.get("/manifest.webmanifest", include_in_schema=False)
def manifest() -> FileResponse:
    return FileResponse(
        "app/static/manifest.webmanifest",
        media_type="application/manifest+json",
    )


@app.get("/sw.js", include_in_schema=False)
def service_worker() -> FileResponse:
    return FileResponse(
        "app/static/sw.js",
        media_type="text/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
    )


@app.get("/healthz", include_in_schema=False)
def healthz() -> JSONResponse:
    """What the host polls to decide the container is alive."""
    return JSONResponse({"ok": True, "clients": len(STATE.clients)})


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """The only page that does not need a session."""
    session = current(request)
    return templates.TemplateResponse(
        request, "index.html",
        {"session": session},
    )


@app.get("/citations", response_class=HTMLResponse)
def citations(request: Request):
    """What we checked, rendered from the same registry the letters cite."""
    return templates.TemplateResponse(
        request, "citations.html",
        {"facts": list(FACTS.values()), "open_questions": OPEN_QUESTIONS,
         "bureaus": BUREAUS},
    )


@app.get("/roles", response_class=HTMLResponse)
def roles(request: Request):
    """Who can do what, rendered from the capability table itself.

    The coordinator's queue has linked here since the first build and the route
    never existed, so it was a dead link on the main staff screen. Worth
    building rather than deleting: the capability table is the product spec, and
    a page generated from it cannot drift from the behaviour the router
    enforces.
    """
    from app import labels
    from app.authorization import FORBIDDEN_SCOPES
    from app.redaction import SENSITIVE

    rows = []
    for surface in Surface:
        allowed = CAPABILITIES[surface]
        rows.append({
            "role": labels.role(surface.value),
            "device": labels.device(surface.value),
            "can": sorted(labels.capability(c) for c in allowed),
            "cannot": sorted(
                ({"label": labels.capability(c), "reason": DENIAL_REASON[c]}
                 for c in DENIAL_REASON if c not in allowed),
                key=lambda row: row["label"],
            ),
        })
    return templates.TemplateResponse(
        request, "roles.html",
        {"surfaces": rows,
         "sensitive": sorted(labels.field(f) for f in SENSITIVE),
         "forbidden": sorted(labels.scope(f) for f in FORBIDDEN_SCOPES)},
    )


@app.get("/metrics", response_class=HTMLResponse)
def metrics(request: Request):
    log = review_log()
    return templates.TemplateResponse(
        request, "metrics.html",
        {"log": log, "summary": log.summary(), "triage_cases": _triage_case_count()},
    )


@app.get("/api/saves")
def saves() -> JSONResponse:
    """Every answer this build has written, and when.

    This used to be called a sync queue and it described an offline-first
    tablet flushing a local queue on reconnect. That is not what happens: the
    tablet is connected and a write lands immediately. Pretending otherwise
    made the endpoint a demo of a thing that never occurred, since every entry
    was marked synced in the same breath as it was created.

    What it is now is the receipt for the promise intake makes on question one,
    that every answer saves as it is given. That promise is true, and this is
    how you check it.
    """
    return JSONResponse({
        "saved": len(STATE.write_log),
        "writes": STATE.write_log[-25:],
    })


def _triage_case_count() -> int:
    from pathlib import Path
    import re

    path = Path("tests/test_triage.py")
    if not path.exists():
        return 0
    return len(re.findall(r"^\s*Case\(", path.read_text(), flags=re.M))
