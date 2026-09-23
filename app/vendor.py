"""Single sign-on from the vendor case plan system.

A coordinator does not sign in to Bridge. They are already signed in to the
system they spend their day in, the one that holds the case plan, and Bridge
opens inside it. Asking them for a second credential would be asking them to
remember a password for a tab they never deliberately opened.

So the coordinator surface has no sign-in screen, no PIN and no enrolment. It
opens on the queue. Identity comes from the vendor's assertion.

That is the opposite of the other two surfaces, and deliberately so. A person
on a facility tablet has no other system to be signed in to, and a helper on
their phone has no institutional identity at all. Those two authenticate here
because there is nowhere else for them to have done it.

    Assumed for this build, with the team's sign-off: that the vendor system
    passes a signed assertion identifying the coordinator. Nothing here
    verifies a real signature. `assertion_from` is the one function a real
    integration replaces, and it is the only place a coordinator identity
    enters the app.
"""

from __future__ import annotations

from dataclasses import dataclass

SIMULATED = True

# What the vendor system would assert. In a real deployment this arrives as a
# signed token and is verified before anything else happens.
DEMO_ASSERTION = {
    "staff_id": "REYES",
    "display_name": "D. Reyes",
    "title": "Offender Rehabilitation Coordinator",
    "facility": "Sing Sing Correctional Facility",
}


@dataclass(frozen=True)
class Coordinator:
    staff_id: str
    display_name: str
    title: str
    facility: str

    @property
    def short(self) -> str:
        return self.display_name


def assertion_from(request) -> dict:
    """Read the vendor system's identity assertion.

    A real integration verifies a signature here and returns the claims. This
    build accepts a header when one is present, so the handoff can be
    exercised, and otherwise falls back to the demo coordinator.
    """
    header = None
    try:
        header = request.headers.get("X-Vendor-Coordinator")
    except AttributeError:
        header = None

    if header:
        # Deliberately minimal: the point is that identity arrives from
        # outside, not that this build parses a real token format.
        return {**DEMO_ASSERTION, "staff_id": header.upper(),
                "display_name": header.title()}
    return dict(DEMO_ASSERTION)


def current_coordinator(request) -> Coordinator:
    claims = assertion_from(request)
    return Coordinator(
        staff_id=claims["staff_id"],
        display_name=claims["display_name"],
        title=claims.get("title", "Offender Rehabilitation Coordinator"),
        facility=claims.get("facility", ""),
    )
