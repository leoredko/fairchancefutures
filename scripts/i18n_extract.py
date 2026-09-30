#!/usr/bin/env python3
"""Build the file a translator fills in, without ever losing their work.

    python3 scripts/i18n_extract.py            # update app/translations/es.po
    python3 scripts/i18n_extract.py --check    # fail if it is out of date

Run it after editing a lesson. It reads the course out of `app/lessons.py` and
writes every translatable string into the `.po` file as an entry to be filled
in, merging with what is already there.

The merge is the whole point, and it follows what gettext has done for thirty
years:

    new string          a fresh empty entry, waiting for somebody
    unchanged string    left exactly alone, signed off stays signed off
    reworded English    the Spanish is kept but flagged fuzzy, because a
                        translation of a sentence we no longer say is worse
                        than no translation. A reviewer sees it again.
    deleted string      marked obsolete, kept at the bottom of the file, so
                        that work comes back if the card comes back

Nothing here contacts a network or a model. It moves strings between two files
on disk.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import polib  # noqa: E402

from app import i18n  # noqa: E402
from app.lessons import CURRICULUM  # noqa: E402

HEADER = """Bridge, the credit course, Spanish.

Every entry below is a screen a person reads on a facility tablet.

How to work on this file:
  1. Open it in Poedit (poedit.net, free) or any translation tool.
  2. The English is on the left. Type the Spanish on the right.
  3. Entries marked "fuzzy" or "needs review" are drafts. Clear that flag
     only when you have read the line and you are happy with it.
  4. Save. Commit the file. That is the whole deployment.

An entry that is empty shows in English instead, and so does one whose English
has changed since it was translated. A flagged entry still shows: the flag is
a bookmark for the next reader, not a gate. That fallback is deliberate: these
lessons state law, and a confident Spanish sentence about somebody's rights
that says something the product no longer says is worse than the English.

Lines marked LEGAL sit on a card that cites a statute. Slow down on those.
Numbers, deadlines and the phrase "120 days" carry weight: there are two
different 120-day clocks in this course and they are on opposite sides of
release.

Do not translate: names of agencies (Equifax, Experian, TransUnion, DOCCS,
DMV), and statute references like 15 U.S.C. 1681i. Somebody may carry those
to a law library and they have to read the way they read on the shelf.
"""


def wanted() -> list[tuple[str, str, bool]]:
    """Every translatable string, lessons first, then the screens around them."""
    out: list[tuple[str, str, bool]] = []
    for lesson in CURRICULUM:
        out.extend(i18n.strings_for(lesson))
    # The screens between the door and the end of the course, so a person who
    # picks Español is not handed Spanish lessons behind English buttons.
    out.extend(i18n.ui_strings())
    return out


def build(language: str) -> tuple[polib.POFile, dict]:
    path = i18n.TRANSLATIONS / f"{language}.po"
    existing = polib.pofile(str(path)) if path.exists() else polib.POFile()

    # Everything we already hold, by key, including entries previously retired.
    held: dict[str, polib.POEntry] = {}
    for entry in existing:
        if entry.msgctxt:
            held[entry.msgctxt] = entry

    out = polib.POFile()
    out.header = HEADER
    out.metadata = {
        "Project-Id-Version": "Bridge",
        "Language": language,
        "MIME-Version": "1.0",
        "Content-Type": "text/plain; charset=utf-8",
        "Content-Transfer-Encoding": "8bit",
        "PO-Revision-Date": date.today().isoformat(),
    }

    counts = {"new": 0, "kept": 0, "stale": 0, "retired": 0}
    live_keys = set()

    for key, english, is_legal in wanted():
        live_keys.add(key)
        comment = "LEGAL: cites a statute, read this one twice." if is_legal else ""
        previous = held.get(key)

        entry = polib.POEntry(msgctxt=key, msgid=english, msgstr="", comment=comment)

        if previous is None:
            counts["new"] += 1
        elif not previous.msgstr.strip():
            # Known but never filled in. Carry nothing, count it as waiting.
            counts["new"] += 1
        elif previous.msgid == english:
            # The English has not moved, so the sign-off still stands.
            entry.msgstr = previous.msgstr
            entry.flags = [f for f in previous.flags if f != "obsolete"]
            counts["kept"] += 1
        else:
            # Reworded since somebody approved it. Keep the Spanish so nobody
            # retypes it from scratch, but it goes back in the review queue.
            entry.msgstr = previous.msgstr
            entry.flags = list(dict.fromkeys([*previous.flags, "fuzzy"]))
            entry.comment = (comment + "\nThe English changed since this was "
                                       "approved. Check it still matches.").strip()
            counts["stale"] += 1

        out.append(entry)

    # Anything we used to ask for and no longer do. Kept rather than dropped:
    # a card that comes back should not cost somebody the same work twice.
    for key, entry in held.items():
        if key in live_keys or not entry.msgstr.strip():
            continue
        retired = polib.POEntry(
            msgctxt=key, msgid=entry.msgid, msgstr=entry.msgstr,
            obsolete=True,
            comment="No longer in the course. Kept in case the card returns.")
        out.append(retired)
        counts["retired"] += 1

    return out, counts


def main() -> int:
    check_only = "--check" in sys.argv
    language = "es"
    path = i18n.TRANSLATIONS / f"{language}.po"
    path.parent.mkdir(parents=True, exist_ok=True)

    built, counts = build(language)
    rendered = str(built)

    if check_only:
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        # The revision date moves every run, so it cannot be part of the
        # comparison or --check would fail on a day nobody touched anything.
        if _without_date(current) != _without_date(rendered):
            print("app/translations/es.po is out of date.")
            print("Run: python3 scripts/i18n_extract.py")
            return 1
        print("app/translations/es.po is up to date.")
        return 0

    path.write_text(rendered, encoding="utf-8")

    i18n.reload()
    cover = i18n.coverage(language)
    print(f"wrote {path}")
    print(f"  {counts['new']} waiting for a translator")
    print(f"  {counts['kept']} already signed off")
    print(f"  {counts['stale']} went back to review, the English changed")
    print(f"  {counts['retired']} retired, kept in the file")
    print(f"reviewed and showing: {cover['reviewed']}/{cover['total']} "
          f"({cover['percent']}%), of which {cover['legal_reviewed']}"
          f"/{cover['legal_total']} cite a statute")
    return 0


def _without_date(text: str) -> str:
    return "\n".join(line for line in text.splitlines()
                     if not line.startswith('"PO-Revision-Date'))


if __name__ == "__main__":
    raise SystemExit(main())
