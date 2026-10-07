"""A practice number for everybody who opens the shared link.

A showcase link goes to a room, and a room is a lot of people on one server.
If they all signed in as the same seeded person they would share one case: one
person picks "Learn" and everybody's screen changes, and the first to set a PIN
locks the rest out. A PIN somebody else set is not a PIN, so the answer is not
a shared PIN, it is a case each.

Any DIN starting 28 already opens a case on the spot. All this does, when
`BRIDGE_PRACTICE=on`, is two things so nobody has to be told how:

  * the sign-in screen arrives with a fresh, unused 28 number already in the
    box, so the room does not type one or collide on one, and
  * a case opened that way starts with the three sample reports, so "My
    reports" has something to read without anybody being sent to a demo
    control.

Off by default, and off in tests. It is a switch for a room, not a property of
the product: a real person's case does not arrive with somebody else's credit
file on it. It is read on every call, so flipping it on the host takes effect
on the next request.
"""

from __future__ import annotations

import os
import secrets
import string
from datetime import date

_TRUE = ("on", "1", "true", "yes")


def enabled() -> bool:
    return os.environ.get("BRIDGE_PRACTICE", "off").strip().lower() in _TRUE


def fresh_number(taken: set[str]) -> str:
    """A 28 number nobody has used, in the form a person would type.

    The letter is random as well as the four digits, so two visitors loading the
    page in the same second are very unlikely to be handed the same number
    before either has signed in.
    """
    while True:
        letter = secrets.choice(string.ascii_uppercase)
        digits = f"{secrets.randbelow(10000):04d}"
        if f"28{letter}{digits}" not in taken:
            return f"28-{letter}-{digits}"


def preload(client) -> None:
    """The three sample reports, on a case that has just been opened."""
    from app.store import put_sample_reports

    put_sample_reports(
        date.today(), client.id, client.display_name,
        f"XXX-XX-{client.din[-4:]}", "1991-03-02",
        [f"{client.facility or 'New York'}, New York"],
    )
