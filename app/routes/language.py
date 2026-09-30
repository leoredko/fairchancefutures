"""The language page, and the place to ask for one we do not have.

Reachable from every screen, signed in or not, for the same reason as the
accessibility page: the choice made at the sign-in door has to be changeable
afterwards, and a person who cannot read the screen in front of them cannot
be asked to sign out to find it. It touches nothing but the language cookie
and the list of requests, so there is no capability for `app/surfaces.py` to
withhold and no case data for it to leak.
"""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import i18n
from app.deps import templates
from app.routes.display import _back
from app.store import STATE, mutate

router = APIRouter()

# Free text from a screen anybody can reach, so it is kept short and the list
# is capped: nobody needs ten thousand copies of one language to count demand.
MAX_LENGTH = 60
MAX_REQUESTS = 1000


@router.get("/language", response_class=HTMLResponse)
def show(request: Request, back: str = "/", thanks: int = 0):
    back = _back(back)
    return templates.TemplateResponse(
        request, "language.html",
        {"back": back, "thanks": bool(thanks),
         "languages": [c for c in i18n.choices() if c["ready"]],
         "lang": i18n.from_request(request),
         "here": "/language?back=" + quote(back, safe="/")},
    )


@router.post("/language/request")
def request_language(request: Request, language: str = Form(""),
                     back: str = Form("/")):
    """Write down which language somebody asked for, then thank them.

    A blank box is not a request, so it goes back without the thanks.
    """
    wanted = " ".join(language.split())[:MAX_LENGTH]
    target = "/language?back=" + quote(_back(back), safe="/")
    if not wanted:
        return RedirectResponse(target + "#other", status_code=303)
    with mutate():
        if len(STATE.language_requests) < MAX_REQUESTS:
            STATE.language_requests.append({
                "language": wanted,
                "asked_in": i18n.from_request(request),
                "asked_on": datetime.now(timezone.utc).date().isoformat(),
            })
    return RedirectResponse(target + "&thanks=1", status_code=303)
