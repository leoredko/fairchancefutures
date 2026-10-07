"""A key on the coordinator's desk, for when the link goes to a room.

The desk (/staff), the demo controls (/demo) and the metrics page have no
sign-in, because in the product the coordinator is already signed in to the
vendor case plan system. On a public link that means anybody can mark a
person's documents on file, approve a letter, or press Start over on the case
somebody is presenting. `app/presentation.py` takes the doors off the wall and
leaves the routes reachable; this is the lock.

Off unless `BRIDGE_DESK_KEY` is set. With it set, those paths need a cookie that
`/desk` hands out in exchange for the key. The cookie is signed with the same
key as a session, so it survives a restart, and it carries nothing about a
person. Everything else, the tablet and the helper's phone, is untouched.

This is a latch for a demo, not authentication. A real deployment replaces it
with whatever the vendor system already does.
"""

from __future__ import annotations

import hmac
import os

COOKIE = "bridge_desk"
GATED = ("/staff", "/demo", "/metrics")
MAX_AGE = 12 * 60 * 60
_PAYLOAD = b"desk"


def key() -> str:
    return os.environ.get("BRIDGE_DESK_KEY", "").strip()


def required() -> bool:
    return bool(key())


def gated(path: str) -> bool:
    return any(path == p or path.startswith(p + "/") for p in GATED)


def key_matches(supplied: str) -> bool:
    wanted = key()
    return bool(wanted) and hmac.compare_digest(
        (supplied or "").strip().encode(), wanted.encode())


def token() -> str:
    from app import auth

    return auth.sign_blob(_PAYLOAD)


def has_pass(request) -> bool:
    from app import auth

    return auth.read_blob(request.cookies.get(COOKIE)) == _PAYLOAD
