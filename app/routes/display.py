"""The display settings page.

Reachable from every screen, signed in or not, because somebody who cannot read
the sign-in screen cannot sign in to change how it reads. It touches nothing
but its cookies, so there is no capability for `app/surfaces.py` to
withhold and no case data for it to leak.
"""

from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import display
from app.deps import templates

router = APIRouter()


def _back(value: str | None) -> str:
    """Kept to this app. An open redirect on a page every screen links to is
    somebody else's phishing page wearing our address."""
    if value and value.startswith("/") and not value.startswith("//") \
            and "\\" not in value and "\n" not in value:
        return value
    return "/"


@router.get("/display", response_class=HTMLResponse)
def show(request: Request, back: str = "/"):
    return templates.TemplateResponse(
        request, "display.html",
        {"back": _back(back), "current": display.from_request(request)},
    )


@router.post("/display")
def choose(request: Request,
           theme: str | None = Form(None),
           size: str | None = Form(None),
           motion: str | None = Form(None),
           read: str | None = Form(None),
           dictate: str | None = Form(None),
           back: str = Form("/")):
    """Take whichever of the settings arrived and leave the others as they were.

    Back to the settings page rather than to where they came from, so the
    change is in front of them the moment they make it. The way out is the
    Done button, which goes where they were.
    """
    response = RedirectResponse(
        "/display?back=" + _quote(_back(back)), status_code=303)
    for setting, value in (("theme", theme), ("size", size), ("motion", motion),
                           ("read", read), ("dictate", dictate)):
        if value is None:
            continue
        response.set_cookie(
            display.COOKIES[setting], display.normalize(setting, value),
            max_age=display.COOKIE_MAX_AGE, path="/", samesite="lax")
    return response


def _quote(path: str) -> str:
    from urllib.parse import quote
    return quote(path, safe="/")
