"""Who is asking.

Before this existed, the client was whatever the URL said: /inside/marcus-w
made you Marcus. Now the client comes from the signed session cookie and the
URL carries no identity at all, so there is nothing to guess at.

Two separate gates, and both have to pass:

  current()   who you are      — the signed cookie
  surfaces    what you can do  — the capability table

A counselor signed in as staff still cannot upload a file from the inside
surface, because the second gate does not care who you are.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request
from fastapi.responses import RedirectResponse

from app.auth import COOKIE_NAME, Session, read
from app.store import STATE, Client

SIGNIN_FOR = {
    "inside": "/signin",
    "family": "/helper",
}


class NotSignedIn(Exception):
    """Raised instead of guessing. The handler turns it into a redirect."""

    def __init__(self, role: str, reason: str = ""):
        self.role = role
        self.reason = reason
        super().__init__(reason or f"Sign in to use the {role} surface.")


@dataclass(frozen=True)
class Caller:
    session: Session
    client: Client | None

    @property
    def role(self) -> str:
        return self.session.role


def current(request: Request) -> Session | None:
    return read(request.cookies.get(COOKIE_NAME))


def require_coordinator(request: Request):
    """The coordinator is already signed in to the vendor case plan system.

    No PIN, no enrolment, no sign-in screen. Bridge opens inside the system
    they already spend their day in, and identity arrives with the request.
    """
    from app.vendor import current_coordinator

    return current_coordinator(request)


def require_role(request: Request, role: str) -> Caller:
    """The session must exist, be unexpired, and be for this surface.

    A helper who finds the staff URL gets sent to the helper sign-in, not to a
    403 that tells them a staff surface exists.
    """
    session = current(request)
    if session is None:
        raise NotSignedIn(role)
    if session.role != role:
        raise NotSignedIn(session.role, "That is not your part of the app.")

    client = STATE.clients.get(session.subject_id) if session.subject_id else None
    if role in ("inside", "family") and client is None:
        raise NotSignedIn(role, "That case is no longer on this tablet.")
    return Caller(session=session, client=client)


def redirect_to_signin(exc: NotSignedIn) -> RedirectResponse:
    target = SIGNIN_FOR.get(exc.role, "/")
    response = RedirectResponse(target, status_code=303)
    if exc.reason:
        response.delete_cookie(COOKIE_NAME, path="/")
    return response
