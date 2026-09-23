"""Shared plumbing for the routers."""

from __future__ import annotations

from fastapi import HTTPException
from fastapi.templating import Jinja2Templates

from app.store import STATE, Client

templates = Jinja2Templates(directory="app/templates")


from app import labels as _labels  # noqa: E402

templates.env.globals["labels"] = _labels


def get_client(client_id: str) -> Client:
    client = STATE.clients.get(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="No such client.")
    return client
