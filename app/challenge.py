"""A human check on the way in, for a demo that lives on a public URL.

Off unless BRIDGE_CAPTCHA is set, because the product it is protecting runs on
a facility tablet where it would be pure obstruction: nobody is crawling a
device that cannot reach the open web, and a person answering an arithmetic
question to look at their own credit file is an insult with no upside.

What it is, and is not:

  It stops crawlers, scrapers and drive-by bots on the deployed demo.
  It does not stop a person. Anybody who has the URL can read a DIN off the
  walkthrough and sign in as that person. The demo has no authentication;
  this is a speed bump on the door, not a lock, and the fix for the other
  thing is not putting real people's data behind that URL.

No third party. reCAPTCHA, hCaptcha and Turnstile all mean a script from
somebody else's domain and a request to their servers on every sign-in, which
is a tracking dependency the product's own premise rules out and a blank box
on any network that blocks them. This ships a question the server asks and
the server marks, in words rather than a picture, so a screen reader can read
it out.

The challenge carries its own answer, signed, so there is nothing to keep
server-side and a restart mid-demo does not invalidate a form somebody has
already got open.
"""

from __future__ import annotations

import json
import os
import secrets
import time

from app.auth import read_blob, sign_blob

# Long enough that reading the page slowly is not a failure, short enough that
# a harvested token is not reusable all afternoon.
LIFETIME_SECONDS = 20 * 60

WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
         "eight", "nine", "ten", "eleven", "twelve", "thirteen"]


# Spanish for the same numbers. Both spellings are accepted whatever language
# the question was asked in, so somebody who switches language halfway through
# is not failed for it.
WORDS_ES = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete",
            "ocho", "nueve", "diez", "once", "doce", "trece"]


def enabled() -> bool:
    return os.environ.get("BRIDGE_CAPTCHA", "").strip().lower() not in (
        "", "0", "false", "no", "off"
    )


def issue(language: str = "en") -> dict:
    """A question, and a signed token that knows the answer.

    Small numbers and written-out words: the point is to cost a script a
    round trip, not to test anybody's arithmetic.
    """
    left = secrets.randbelow(6) + 2        # 2 to 7
    right = secrets.randbelow(5) + 1       # 1 to 5
    body = json.dumps(
        {"sum": left + right, "at": time.time()}, separators=(",", ":")
    ).encode()
    return {
        "question": (f"¿Cuánto es {WORDS_ES[left]} más {WORDS_ES[right]}?"
                     if language == "es"
                     else f"What is {WORDS[left]} plus {WORDS[right]}?"),
        "token": sign_blob(body),
    }


def verify(token: str | None, answer: str | None) -> bool:
    """Wrong answer, tampered token and expired token all read the same here.

    Telling them apart would only help the thing this is for.
    """
    if not token or answer is None:
        return False
    body = read_blob(token)
    if body is None:
        return False
    try:
        data = json.loads(body)
        expected = int(data["sum"])
        issued_at = float(data["at"])
    except (ValueError, KeyError, TypeError):
        return False
    if time.time() - issued_at > LIFETIME_SECONDS:
        return False

    given = answer.strip().lower()
    if given in WORDS:
        given = str(WORDS.index(given))
    elif given in WORDS_ES:
        given = str(WORDS_ES.index(given))
    try:
        return int(given) == expected
    except ValueError:
        return False
