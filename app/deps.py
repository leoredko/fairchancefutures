"""Shared plumbing for the routers."""

from __future__ import annotations

from fastapi import HTTPException
from fastapi.templating import Jinja2Templates

from app.store import STATE, Client

templates = Jinja2Templates(directory="app/templates")


from app import labels as _labels  # noqa: E402
from app import paths as _paths  # noqa: E402
from app import presentation as _presentation  # noqa: E402

templates.env.globals["labels"] = _labels
# A callable, not its result: the switch is read per render, so turning it on
# takes effect on the next page rather than the next restart.
templates.env.globals["tablet_only"] = _presentation.tablet_only
# The path a person chose, said the way a coordinator reads it.
templates.env.globals["queue_label_for"] = _paths.queue_label_for


def get_client(client_id: str) -> Client:
    client = STATE.clients.get(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="No such client.")
    return client
