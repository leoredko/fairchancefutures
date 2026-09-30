"""The course in Spanish, as content rather than as a running translator.

Nothing here calls a model, a service, or the network. The lessons are fixed
text: the same eleven lessons say the same thing to everybody, so translating
them is a thing you do once and commit, not a thing the app does per request.
The Spanish ships inside the image alongside the English and cannot fail on the
day, because there is nothing to fail.

The catalog is a gettext `.po` file, which is the format translators already
have tools for. A person reviewing the Spanish opens `app/translations/es.po`
in Poedit, sees the English beside the Spanish, and saves. No JSON, no code.

Two properties fall out of gettext that we would otherwise have had to
invent, which is the reason for using it rather than a dictionary of our own:

    msgctxt     the stable key, so a card can be reworded without the
                translation silently attaching to the wrong screen
    msgid       the English the translation was made against. When the English
                changes the msgid no longer matches, and that entry alone
                falls back to English, so a reworded card cannot keep showing
                Spanish for a sentence the product no longer says.

An empty entry falls back to English too. Fallback is per string, so a course
that is nine tenths translated shows nine tenths in Spanish rather than
waiting for the last line.

**The switch.** Set `BRIDGE_SPANISH=off` and the whole language disappears:
no toggle on the tablet, everything in English, no deploy and no code change
needed. It is there because the Spanish is checked by a bilingual reader
rather than a certified translator, and the honest answer to "what if a line
turns out to be wrong in front of people" is one environment variable rather
than a rollback.
"""

from __future__ import annotations

import dataclasses
import os
import re
import string
from pathlib import Path

import polib

# The languages the tablet offers. English is the source and is never looked
# up: there is no en.po, because translating English into English is a file
# nobody would maintain and a whole class of bug for nothing.
SOURCE_LANGUAGE = "en"
LANGUAGES: tuple[str, ...] = ("en", "es")

LANGUAGE_NAME: dict[str, str] = {
    # Each language is named in itself. Somebody looking for Spanish is not
    # helped by the word "Spanish".
    "en": "English",
    "es": "Español",
}

TRANSLATIONS = Path(__file__).parent / "translations"


class Catalog:
    """One language's reviewed translations, keyed by msgctxt.

    Only entries a human has signed off are kept. Everything else is dropped
    on load rather than filtered at render time, so there is exactly one place
    the rule lives and no route can forget to apply it.
    """

    def __init__(self, language: str, entries: dict[str, tuple[str, str]]):
        self.language = language
        # key -> (english it was translated from, spanish)
        self._entries = entries

    def get(self, key: str, english: str) -> str:
        """The reviewed translation, or the English.

        The English is passed in and checked rather than trusted, because a
        translation made against an older wording is worse than no
        translation: it reads fluent and says something the product no longer
        says. A mismatch means the card was edited after it was signed off,
        so the entry is stale and English wins until somebody looks again.
        """
        found = self._entries.get(key)
        if found is None:
            return english
        source, target = found
        if source != english:
            return english
        return target

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def is_empty(self) -> bool:
        return not self._entries


def enabled() -> bool:
    """The switch. `BRIDGE_SPANISH=off` takes the language out entirely.

    Read on every call rather than cached at import, so flipping it on the
    host takes effect on the next request instead of on the next deploy.
    """
    return os.environ.get("BRIDGE_SPANISH", "on").strip().lower() not in (
        "off", "0", "false", "no")


def _load(language: str) -> Catalog:
    path = TRANSLATIONS / f"{language}.po"
    if language == SOURCE_LANGUAGE or not path.exists():
        return Catalog(language, {})

    entries: dict[str, tuple[str, str]] = {}
    for entry in polib.pofile(str(path)):
        # Nothing typed, or the string it belonged to is gone from the course.
        # Either way there is nothing to show but the English.
        if not entry.msgstr.strip():
            continue
        if entry.obsolete:
            continue
        if not entry.msgctxt:
            continue
        entries[entry.msgctxt] = (entry.msgid, entry.msgstr)
    return Catalog(language, entries)


_CATALOGS: dict[str, Catalog] = {}


def catalog(language: str) -> Catalog:
    """Loaded once and held. The file does not change while the app runs."""
    if language not in _CATALOGS:
        _CATALOGS[language] = _load(language)
    return _CATALOGS[language]


def reload() -> None:
    """Drop the cache. For tests and for the extract script."""
    _CATALOGS.clear()


def available() -> tuple[str, ...]:
    """Languages with something in them, English always included.

    This is what decides whether the tablet shows a language choice at all. A
    toggle that switches to an untranslated app is the decoration this product
    removed once already, so the control does not exist until the content
    does, and it disappears again the moment the switch is thrown.
    """
    ready = [SOURCE_LANGUAGE]
    if not enabled():
        return tuple(ready)
    for language in LANGUAGES:
        if language == SOURCE_LANGUAGE:
            continue
        if not catalog(language).is_empty:
            ready.append(language)
    return tuple(ready)


def offered() -> bool:
    return len(available()) > 1


def normalize(language: str | None) -> str:
    """Whatever arrived, turned into a language this app actually serves."""
    if not language:
        return SOURCE_LANGUAGE
    code = language.split("-")[0].strip().lower()
    return code if code in available() else SOURCE_LANGUAGE


# --------------------------------------------------------------------------
# keys
#
# Positional, because the alternative is a hand-assigned id on every card and
# a second thing to keep in step. A card that moves gets a new key and its
# translation goes fuzzy, which is the correct outcome: somebody reordered the
# lesson and a reviewer should see it again.
# --------------------------------------------------------------------------

def lesson_key(slug: str, *parts) -> str:
    return ".".join(["lesson", slug, *(str(p) for p in parts)])


def strings_for(lesson) -> list[tuple[str, str, bool]]:
    """Every translatable string in one lesson, as (key, english, is_legal).

    `is_legal` marks a string that sits on a card citing a source. It does not
    change what renders, because the fuzzy rule already covers everything. It
    is here so the extract script can tell a reviewer which lines to slow down
    on, and so a future check can require a named reviewer on those.
    """
    out: list[tuple[str, str, bool]] = [
        (lesson_key(lesson.slug, "title"), lesson.title, False),
        (lesson_key(lesson.slug, "hook"), lesson.hook, False),
    ]
    for index, card in enumerate(lesson.cards):
        legal = bool(card.fact_key)
        out.append((lesson_key(lesson.slug, "card", index, "title"), card.title, legal))
        out.append((lesson_key(lesson.slug, "card", index, "body"), card.body, legal))
        if card.aside:
            out.append(
                (lesson_key(lesson.slug, "card", index, "aside"), card.aside, legal))
    out.append((lesson_key(lesson.slug, "check", "prompt"), lesson.check.prompt, False))
    out.append((lesson_key(lesson.slug, "check", "why"), lesson.check.why, False))
    for choice in lesson.check.choices:
        out.append(
            (lesson_key(lesson.slug, "check", "choice", choice.value),
             choice.label, False))
    return out


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

def translate_lesson(lesson, language: str):
    """A copy of the lesson in `language`, falling back per string.

    Per string rather than per lesson on purpose. A lesson where ten cards are
    signed off and one is not shows ten in Spanish and one in English, which is
    honest and still useful. Holding the whole lesson back until the last card
    lands would mean the course arrives in one lump or not at all.

    `fact_key` is carried across untouched. The citation line under a card is
    built from `app/sources.py`, which holds a statute and a URL, and those do
    not get translated: a person taking 15 U.S.C. 1681i to a law library needs
    it to read the way it reads on the shelf.
    """
    if language == SOURCE_LANGUAGE or not enabled():
        return lesson
    book = catalog(language)
    if book.is_empty:
        return lesson

    def look(key: str, english: str) -> str:
        return book.get(key, english)

    slug = lesson.slug
    cards = []
    for index, card in enumerate(lesson.cards):
        cards.append(dataclasses.replace(
            card,
            title=look(lesson_key(slug, "card", index, "title"), card.title),
            body=look(lesson_key(slug, "card", index, "body"), card.body),
            aside=(look(lesson_key(slug, "card", index, "aside"), card.aside)
                   if card.aside else card.aside),
        ))

    choices = tuple(
        dataclasses.replace(
            choice,
            label=look(lesson_key(slug, "check", "choice", choice.value), choice.label),
        )
        for choice in lesson.check.choices
    )
    check = dataclasses.replace(
        lesson.check,
        prompt=look(lesson_key(slug, "check", "prompt"), lesson.check.prompt),
        why=look(lesson_key(slug, "check", "why"), lesson.check.why),
        choices=choices,
    )
    return dataclasses.replace(
        lesson,
        title=look(lesson_key(slug, "title"), lesson.title),
        hook=look(lesson_key(slug, "hook"), lesson.hook),
        cards=tuple(cards),
        check=check,
    )


def coverage(language: str) -> dict:
    """How much of the course is translated, for the team rather than a screen.

    Counted against what is actually translatable right now, so the number
    moves when a reviewer saves the file and not when somebody edits this
    module. `scripts/i18n_extract.py` prints it.
    """
    from app.lessons import CURRICULUM

    book = catalog(language)
    total = 0
    done = 0
    legal_total = 0
    legal_done = 0
    every = [s for lesson in CURRICULUM for s in strings_for(lesson)]
    every.extend(ui_strings())
    for key, english, is_legal in every:
        total += 1
        legal_total += 1 if is_legal else 0
        if book.get(key, english) != english:
            done += 1
            legal_done += 1 if is_legal else 0
    return {
        "language": language,
        "total": total,
        "reviewed": done,
        "percent": round(100 * done / total) if total else 0,
        "legal_total": legal_total,
        "legal_reviewed": legal_done,
    }


# --------------------------------------------------------------------------
# the request
# --------------------------------------------------------------------------

COOKIE = "bridge_lang"

# A year. The choice is made once, at the door, by somebody who is not going
# to want to make it again every time the tablet locks.
COOKIE_MAX_AGE = 60 * 60 * 24 * 365


def from_request(request) -> str:
    """Which language this tablet is set to.

    A cookie rather than anything on the case file, because the choice is made
    at the sign-in door before anybody knows who is holding the tablet, and
    because it is a property of the device in front of a person rather than a
    fact about them.
    """
    return normalize(request.cookies.get(COOKIE))


def choices() -> list[dict]:
    """What the door offers.

    `Other` is listed and cannot be picked. Somebody who reads neither English
    nor Spanish should find out here, from a screen that admits it, rather
    than by working through a course in a language they do not read. Naming
    the gap is the honest version of not having filled it.
    """
    ready = available()
    out = [{"code": code, "name": LANGUAGE_NAME[code], "ready": True}
           for code in ready]
    out.append({"code": "other", "name": "Other", "ready": False,
                "note": "Other languages are coming. For now this app is in "
                        "English" + (" and Spanish." if "es" in ready else ".")})
    return out


def translate_rows(rows: list[dict], language: str) -> list[dict]:
    """The course index, translated. Each row wraps one lesson."""
    if language == SOURCE_LANGUAGE or not enabled():
        return rows
    return [{**row, "lesson": translate_lesson(row["lesson"], language)}
            for row in rows]


# --------------------------------------------------------------------------
# the screens around the course
# --------------------------------------------------------------------------

def ui_strings() -> list[tuple[str, str, bool]]:
    """Every screen string that is not a lesson, as (key, english, is_legal).

    Same shape as `strings_for` so the extract script and the coverage count
    treat them alike. None is legal: a sentence that states a right or a
    deadline belongs on a lesson card, with a source.
    """
    from app.ui_strings import UI

    return [(key, english, False) for key, english in UI.items()]


def _fields(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def ui(key: str, language: str, **values) -> str:
    """A screen string in `language`, English when there is nothing safe to show.

    Three ways to land on English, all deliberate: the language is English or
    switched off, the entry is empty or its English has moved, or the Spanish
    dropped or renamed a `{value}` the screen fills in. That last one is a
    translator's typo, and a sentence with a hole in it reads as broken while
    English reads as merely English.
    """
    from app.ui_strings import UI

    english = UI[key]
    text = english
    if language != SOURCE_LANGUAGE and enabled():
        found = catalog(language).get(key, english)
        if _fields(found) == _fields(english):
            text = found
    return text.format(**values)


def translate_error(message: str | None, language: str) -> str | None:
    """A finished error sentence, put into `language` when we know it.

    The sentences are raised in modules that have no idea what language the
    tablet is set to (`app/auth.py`, `app/identifiers.py`), and threading a
    language through every raise would put display concerns into the checks.
    So the screen matches the English it was handed against `error.*` and
    says the same thing in the other language, pulling the numbers back out.
    A sentence it does not recognise comes back untouched.
    """
    if not message or language == SOURCE_LANGUAGE or not enabled():
        return message
    from app.ui_strings import UI

    for key, english in UI.items():
        if not key.startswith("error."):
            continue
        pattern = "".join(
            re.escape(literal) + (f"(?P<{name}>.+?)" if name else "")
            for literal, name, _, _ in string.Formatter().parse(english))
        found = re.fullmatch(pattern, message)
        if found:
            return ui(key, language, **found.groupdict())
    return message
