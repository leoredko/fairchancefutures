"""Shared plumbing for the routers."""

from __future__ import annotations

from fastapi import HTTPException
from fastapi.templating import Jinja2Templates

from app.store import STATE, Client

templates = Jinja2Templates(directory="app/templates")


def _show_notes(request) -> dict:
    """Design notes are off unless the cookie says otherwise."""
    return {"show_notes": request.cookies.get("bridge_notes") == "1"}


templates.env.globals["labels"] = None  # replaced below, keeps import order simple
templates.context_processors.append(_show_notes)

from app import labels as _labels  # noqa: E402

templates.env.globals["labels"] = _labels


def get_client(client_id: str) -> Client:
    client = STATE.clients.get(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="No such client.")
    return client
