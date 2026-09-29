"""Two ways in, chosen by the person rather than decided by the product.

Bridge does two things. It teaches credit, and it works a credit case. Until
now the tablet decided which one somebody was doing by dropping them straight
into intake, because that is the order the product thinks in. It is not the
order a person arrives in. The feedback from the field was blunt: make it
simpler. So the first screen after a PIN asks one question in plain words, and
the answer steers everything after it.

Steers, not gates. Both paths stay one tap from every screen and the switch
sits in the header, not somewhere a person has to remember. Somebody who picks
in ten seconds and picks wrong is two taps from the other one. A choice that
locked half the product away would be a rung, and the rungs came out for a
reason: read the docstring in `app/authorization.py` before adding one back.

So this is not a capability and it is not an authorization. Nothing here
decides what a surface can do, which is `app/surfaces.py`, or what a helper is
allowed to see, which is `app/authorization.py`. It decides where a person
lands and what the big button on the screen says. That is the whole of it.

The course is still never gated. A person with no path chosen at all reaches
every lesson, which is the rule in CLAUDE.md and the reason the chooser is a
screen a person can walk past rather than a door they have to open.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Path:
    """One of the two. Written in the words a person would use, not ours."""

    key: str
    label: str
    # What picking it actually gets them, said without product language.
    blurb: str
    # What the button says. A verb, because they are about to do the thing.
    cta: str
    # The same fact said to a coordinator scanning a queue. Not the same
    # sentence: "Learn how credit works" is an offer made to the person
    # choosing, and a row in somebody else's work queue is not an offer.
    queue_label: str


LEARN = Path(
    key="learn",
    label="Learn how credit works",
    blurb="Short lessons, one at a time. Nothing to fill in and no forms. "
          "It saves where you stop, so you can put the tablet down and come "
          "back to it.",
    cta="Start learning",
    queue_label="On the course",
)

CREDIT = Path(
    key="credit",
    label="Work on my credit",
    blurb="Answer some questions about your money, then a counselor picks it "
          "up and works your case with you. You can read the lessons any time "
          "while you wait.",
    cta="Start on my credit",
    queue_label="Working the case",
)

PATHS: tuple[Path, ...] = (LEARN, CREDIT)

BY_KEY: dict[str, Path] = {p.key: p for p in PATHS}


def get(key: str) -> Path | None:
    """The path, or None for anything that is not one. Never raises.

    A stored value that is no longer a path (a renamed key, a hand-edited data
    file) reads as no choice made, so the person gets asked again. That is a
    screen they know how to answer. A 500 is not.
    """
    return BY_KEY.get(key or "")


def queue_label_for(key: str) -> str:
    """What a coordinator's queue says, including for somebody who has not picked.

    "Has not chosen yet" is information a coordinator can act on, so it is said
    rather than left blank. A blank cell in a work queue reads as a bug.
    """
    path = get(key)
    return path.queue_label if path else "Has not chosen yet"
