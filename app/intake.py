"""Adding a person to the caseload.

A counselor does this, not the person themselves. That distinction is the whole
reason there is no public signup: somebody inside does not enrol into a reentry
program from their tablet, a counselor puts them on the list after a
conversation.

What creating a client actually makes:

  the client record
  two sign-in accounts, one for the DIN and one for the NYSID, both PIN-less
  a helper code, printed on the letter that goes out to whoever is helping

None of the three accounts gets a PIN here. Every one of them is set by the
person it belongs to, the first time they sign in. A counselor who could set a
client's PIN would be a counselor who knows it.
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass
from datetime import date

from app.identifiers import IdKind, InvalidIdentifier, parse

# New York State reception centers and the facilities this build knows about.
# Not exhaustive, and not verified against a DOCCS list: it is a picker for a
# demo, and the field accepts anything typed into it.
FACILITIES: tuple[str, ...] = (
    "Sing Sing Correctional Facility",
    "Bedford Hills Correctional Facility",
    "Fishkill Correctional Facility",
    "Woodbourne Correctional Facility",
    "Green Haven Correctional Facility",
    "Albion Correctional Facility",
    "Clinton Correctional Facility",
    "Downstate Correctional Facility",
)


class IntakeProblem(ValueError):
    """One sentence, naming the field, written for the person typing."""

    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(message)


@dataclass(frozen=True)
class NewClient:
    display_name: str
    first_name: str
    din: str
    nysid: str
    facility: str
    release_date: str


def helper_code(existing: set[str] | None = None) -> str:
    """The code printed on the letter that reaches whoever is helping.

    Four digits, no letters, because it gets read down a phone line and typed
    by somebody who did not ask to be doing paperwork. Ambiguity between O and
    0 is not worth the extra entropy when the code only ever identifies which
    case a helper is calling about, and a PIN still stands behind it.
    """
    existing = existing or set()
    for _ in range(200):
        code = "BRIDGE-" + "".join(random.choices(string.digits, k=4))
        if code not in existing:
            return code
    raise IntakeProblem("code", "Could not find a free sign-in code. Try again.")


def _clean_name(raw: str) -> str:
    """Title case the parts, leave initials and suffixes alone.

    "marcus w." becomes "Marcus W.", "MARIA ALVAREZ" becomes "Maria Alvarez".
    A name typed in a hurry should not end up shouting on the tablet.
    """
    # Roman numerals shout, name suffixes do not: "Andre Quinones Jr. III".
    numerals = {"II", "III", "IV", "V", "VI"}
    suffixes = {"JR", "SR"}
    parts = []
    for word in (raw or "").split():
        bare = word.rstrip(".").upper()
        if bare in numerals:
            parts.append(bare)
        elif bare in suffixes:
            parts.append(bare.capitalize() + ".")
        elif len(word.rstrip(".")) == 1:
            parts.append(word.upper())
        else:
            parts.append(_capitalize_word(word))
    return " ".join(parts)


def _capitalize_word(word: str) -> str:
    """Title case, with the two patterns that are common in New York.

    O'Brien and McDonald both need a second capital, and getting them wrong on
    somebody's own name on their own screen is the kind of small disrespect
    people notice.
    """
    lowered = word.lower()
    out = lowered[:1].upper() + lowered[1:]
    if "'" in out:
        head, _, tail = out.partition("'")
        if len(head) <= 2 and tail:
            out = head + "'" + tail[:1].upper() + tail[1:]
    for prefix in ("Mc", "Mac"):
        if out.startswith(prefix) and len(out) > len(prefix) + 1:
            out = prefix + out[len(prefix):len(prefix) + 1].upper() + out[len(prefix) + 1:]
            break
    return out


def validate(
    *,
    display_name: str,
    din: str,
    nysid: str,
    facility: str,
    release_date: str,
    known_dins: set[str] | None = None,
    known_nysids: set[str] | None = None,
    today: date | None = None,
) -> NewClient:
    known_dins = known_dins or set()
    known_nysids = known_nysids or set()
    today = today or date.today()

    name = _clean_name(display_name)
    if len(name) < 2:
        raise IntakeProblem("display_name", "Enter the person's name.")

    # At least one identifier, and whichever is given has to parse. A counselor
    # often has only one of the two in front of them.
    if not (din or "").strip() and not (nysid or "").strip():
        raise IntakeProblem("din", "Enter a DIN, a NYSID, or both.")

    din_key = ""
    if (din or "").strip():
        try:
            parsed = parse(din)
        except InvalidIdentifier as exc:
            raise IntakeProblem("din", str(exc)) from exc
        if parsed.kind is not IdKind.DIN:
            raise IntakeProblem(
                "din", "That is a NYSID. Put it in the NYSID box instead.")
        din_key = parsed.normalized
        if din_key in known_dins:
            raise IntakeProblem("din", f"{parsed.display} is already on the caseload.")

    nysid_key = ""
    if (nysid or "").strip():
        try:
            parsed = parse(nysid)
        except InvalidIdentifier as exc:
            raise IntakeProblem("nysid", str(exc)) from exc
        if parsed.kind is not IdKind.NYSID:
            raise IntakeProblem(
                "nysid", "That is a DIN. Put it in the DIN box instead.")
        nysid_key = parsed.normalized
        if nysid_key in known_nysids:
            raise IntakeProblem("nysid", f"{nysid_key} is already on the caseload.")

    if not (facility or "").strip():
        raise IntakeProblem(
            "facility",
            "Name the facility. It goes on the envelope as the return address, "
            "and the bureaus ask for it on mail from a prison.")

    try:
        release = date.fromisoformat(release_date)
    except (ValueError, TypeError) as exc:
        raise IntakeProblem("release_date", "Enter the release date.") from exc
    if release < today.replace(year=today.year - 5):
        raise IntakeProblem(
            "release_date", "That release date is more than five years ago. "
                            "Check the year.")

    return NewClient(
        display_name=name,
        first_name=name.split()[0],
        din=din_key,
        nysid=nysid_key,
        facility=facility.strip(),
        release_date=release.isoformat(),
    )


def client_id_for(name: str, din: str, taken: set[str]) -> str:
    """A stable, readable id. Falls back to the DIN when names collide."""
    base = "".join(
        ch.lower() if ch.isalnum() else "-" for ch in name
    ).strip("-").replace("--", "-") or "client"
    if base not in taken:
        return base
    with_din = f"{base}-{din.lower()}" if din else base
    if with_din not in taken:
        return with_din
    n = 2
    while f"{base}-{n}" in taken:
        n += 1
    return f"{base}-{n}"
