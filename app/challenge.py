"""A human check on the way in, for a demo that lives on a public URL.

Off unless BRIDGE_CAPTCHA is set, because the product it is protecting runs on
a facility tablet where it would be pure obstruction: nobody is crawling a
device that cannot reach the open web.

It is one box to tick. It stops crawlers and scripts that post to the door
without ever loading it, and nothing else. It does not stop a person, and a
script that loads the page first gets through. The demo has no authentication;
this is a speed bump on the door, not a lock.

No third party. reCAPTCHA, hCaptcha and Turnstile all mean a script from
somebody else's domain and a request to their servers on every sign-in. The
box is plain HTML, so a screen reader reads it as the checkbox it is.

The page carries a signed, dated token, so there is nothing to keep
server-side and a restart mid-demo does not invalidate a form somebody has
already got open.
"""

from __future__ import annotations

import json
import os
import time

from app.auth import read_blob, sign_blob

# Long enough that reading the page slowly is not a failure, short enough that
# a harvested token is not reusable all afternoon.
LIFETIME_SECONDS = 20 * 60


def enabled() -> bool:
    return os.environ.get("BRIDGE_CAPTCHA", "").strip().lower() not in (
        "", "0", "false", "no", "off"
    )


def issue() -> dict:
    """A signed token proving the page was loaded, and when."""
    body = json.dumps({"at": time.time()}, separators=(",", ":")).encode()
    return {"token": sign_blob(body)}


def verify(token: str | None, ticked: str | None) -> bool:
    """Unticked, tampered and expired all read the same here.

    Telling them apart would only help the thing this is for.
    """
    if not token or not ticked:
        return False
    body = read_blob(token)
    if body is None:
        return False
    try:
        issued_at = float(json.loads(body)["at"])
    except (ValueError, KeyError, TypeError):
        return False
    return time.time() - issued_at <= LIFETIME_SECONDS
