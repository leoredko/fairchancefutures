"""When something last got checked, and when that stops being good enough.

Four registries in this app carry a date somebody looked: the legal facts in
`app.sources`, the bureau dispute addresses in `app.bureaus`, the counseling
centers in `app.centers`, and the DOCCS facilities in `app.facilities`. Until
now that date was written down and then nothing read it. `docs/VERIFY.md` said "re-check anything older than six
months" in prose, which is a rule nobody is enforcing.

This module enforces it. It does not go and look, because looking is a person's
job: bureau addresses move without announcement, a center's hours change, and a
statute gets amended. What it does is say which entries are old enough that
somebody should.

The deliberate asymmetry: a stale legal fact and a stale address are not the
same failure. A statute that moved is usually still roughly right. An address
that moved sends an envelope into a void, and a center that closed sends a
person who just came home on a bus ride to a locked door. So addresses get the
shorter window.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app import bureaus, centers, facilities, sources

# Six months for anything with an address on it, which is the window
# docs/VERIFY.md already asked for out loud. A year for a statute, which is
# long enough to catch an amendment and short enough that nothing rots.
ADDRESS_WINDOW = timedelta(days=182)
STATUTE_WINDOW = timedelta(days=365)


@dataclass(frozen=True)
class Staleness:
    """One entry that has gone past its window, and by how much."""

    kind: str
    key: str
    label: str
    checked_on: date
    days_old: int
    window_days: int
    url: str

    @property
    def days_over(self) -> int:
        return self.days_old - self.window_days

    def line(self) -> str:
        return (f"{self.kind}: {self.label} last checked "
                f"{self.checked_on.isoformat()}, {self.days_old} days ago, "
                f"{self.days_over} past its {self.window_days} day window. "
                f"{self.url}")


def _age(checked_on: date, today: date) -> int:
    return (today - checked_on).days


def stale(today: date | None = None) -> tuple[Staleness, ...]:
    """Everything past its window, oldest first.

    Sorted by how far over it is rather than by kind, because the question a
    person actually has is what to re-check first.
    """
    today = today or date.today()
    out: list[Staleness] = []

    for fact in sources.FACTS.values():
        age = _age(fact.checked_on, today)
        if age > STATUTE_WINDOW.days:
            out.append(Staleness(
                kind="fact", key=fact.key, label=fact.source,
                checked_on=fact.checked_on, days_old=age,
                window_days=STATUTE_WINDOW.days, url=fact.url))

    # Bureaus carry one check date for the file rather than one each, because
    # all three were read in the same sitting.
    for bureau in bureaus.BUREAUS:
        age = _age(bureaus.CHECKED, today)
        if age > ADDRESS_WINDOW.days:
            out.append(Staleness(
                kind="bureau address", key=bureau.key, label=bureau.name,
                checked_on=bureaus.CHECKED, days_old=age,
                window_days=ADDRESS_WINDOW.days, url=bureau.source_url))

    for center in centers.CENTERS + centers.COMING:
        age = _age(center.checked_on, today)
        if age > ADDRESS_WINDOW.days:
            out.append(Staleness(
                kind="counseling center", key=center.key, label=center.name,
                checked_on=center.checked_on, days_old=age,
                window_days=ADDRESS_WINDOW.days, url=center.url))

    # One check date for the whole facility file, the same way the bureaus
    # carry one, because they were read in a single sitting off the DOCCS
    # pages. DOCCS has closed facilities steadily since 2021, so the list
    # going stale means names on envelopes that no longer exist.
    age = _age(facilities.CHECKED, today)
    if age > ADDRESS_WINDOW.days:
        out.append(Staleness(
            kind="facility list", key="doccs", label=facilities.SOURCE,
            checked_on=facilities.CHECKED, days_old=age,
            window_days=ADDRESS_WINDOW.days, url=facilities.SOURCE_URL))

    out.sort(key=lambda s: s.days_over, reverse=True)
    return tuple(out)


def report(today: date | None = None) -> str:
    """What a person reads when they want to know what needs re-checking."""
    rows = stale(today)
    unread = centers.needs_a_human_read()

    lines: list[str] = []
    if rows:
        lines.append(f"{len(rows)} entries are past their window:")
        lines.extend("  " + r.line() for r in rows)
    else:
        lines.append("Nothing is past its window.")

    if unread:
        lines.append("")
        lines.append(f"{len(unread)} entries were never read from the source "
                     f"by a person, whatever their date says:")
        for c in unread:
            lines.append(f"  counseling center: {c.name}. {c.url}")

    return "\n".join(lines)
