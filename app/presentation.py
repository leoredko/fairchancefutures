"""What the room sees.

Bridge is three surfaces, and the argument is that they cannot do each other's
jobs. A presentation is not always that argument. Sometimes the five minutes
are the tablet and the course, and a landing page offering a coordinator queue
and a helper door is an invitation to open the wrong one on a projector.

`BRIDGE_TABLET_ONLY=on` takes the other two doors off every screen the room
sees. Nothing else changes.

It hides doors, not people. The coordinator is still named on the timeline and
the helper is still named where the course explains who sends what, because an
event with nobody attached reads as an automated nudge, and the Cornish
interview is clear that those read as scams inside. A tablet that stopped
naming the people working the case would be a different product, not a shorter
demo of this one.

The routes stay reachable by URL. Whoever is driving can still open /staff in
a window the room does not see, run triage, and let the tablet show the result,
which is the whole reason this is a door taken off the wall rather than a
locked one. It is also why this module holds no capability: the enforcement
lives in `app.surfaces`, and a presentation setting that could deny a request
would be a second, weaker copy of that table.

Read on every call rather than at import, so flipping it on the host takes
effect on the next request instead of the next deploy.
"""

from __future__ import annotations

import os


def tablet_only() -> bool:
    """The switch. Off unless somebody deliberately turns it on."""
    return os.environ.get("BRIDGE_TABLET_ONLY", "off").strip().lower() in (
        "on", "1", "true", "yes")
