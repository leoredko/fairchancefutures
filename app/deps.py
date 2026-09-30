"""Shared plumbing for the routers."""

from __future__ import annotations

from fastapi import HTTPException
from fastapi.templating import Jinja2Templates

from app.store import STATE, Client

templates = Jinja2Templates(directory="app/templates")


from jinja2 import pass_context  # noqa: E402

from app import i18n as _i18n  # noqa: E402
from app import labels as _labels  # noqa: E402
from app import paths as _paths  # noqa: E402
from app import presentation as _presentation  # noqa: E402

templates.env.globals["labels"] = _labels
# A callable, not its result: the switch is read per render, so turning it on
# takes effect on the next page rather than the next restart.
templates.env.globals["tablet_only"] = _presentation.tablet_only
# The path a person chose, said the way a coordinator reads it.
templates.env.globals["queue_label_for"] = _paths.queue_label_for


# The language comes off the request, which every TemplateResponse already
# carries, so a screen can be translated without its route having to remember
# to pass a language in. A route that forgets is the failure this avoids.
@pass_context
def _t(context, key: str, **values) -> str:
    return _i18n.ui(key, _i18n.from_request(context["request"]), **values)


@pass_context
def _tr(context, message):
    """An error sentence raised somewhere that knows no language."""
    return _i18n.translate_error(message, _i18n.from_request(context["request"]))


@pass_context
def _lang(context) -> str:
    return _i18n.from_request(context["request"])


templates.env.globals["t"] = _t
templates.env.globals["tr"] = _tr
templates.env.globals["lang_code"] = _lang


def get_client(client_id: str) -> Client:
    client = STATE.clients.get(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="No such client.")
    return client
