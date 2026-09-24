"""The course in Spanish, as content rather than as a running translator.

Nothing here calls a model, a service, or the network. The lessons are fixed
text: the same eleven lessons say the same thing to everybody, so translating
them is a thing you do once and commit, not a thing the app does per request.
The Spanish ships inside the image alongside the English and cannot fail on the
day, because there is nothing to fail.

The catalog is a gettext `.po` file, which is the format translators already
have tools for. A person reviewing the Spanish opens `app/translations/es.po`
in Poedit, sees the English beside the Spanish, and saves. No JSON, no code.

Three properties fall out of gettext that we would otherwise have had to
invent, which is the reason for using it rather than a dictionary of our own:

    msgctxt     the stable key, so a card can be reworded without the
                translation silently attaching to the wrong screen
    msgid       the English the translation was made against. When the English
                changes the msgid no longer matches, and the entry is stale by
                construction rather than by somebody remembering.
    fuzzy       the standard flag for "not signed off". It is how every
                translation tool in the world marks a draft.

**The rule this module exists to enforce: a fuzzy entry never reaches a
screen.** These lessons state law. A machine-drafted sentence about a 30-day
dispute clock that no Spanish speaker has read is the same failure as a legal
sentence with no source, and `app/sources.py` already refuses that one. So an
entry that is missing, empty, or fuzzy falls back to English. English is not
the failure case here: it is what the person gets today, and it is correct.

Which means the drafting tool does not matter much and is deliberately not
named in this module. Argos Translate, Poedit's own suggestions, or a person
typing from scratch all arrive at the same place: a `.po` file that a human
has signed off. `scripts/i18n_extract.py` builds the file to be filled in.
"""

from __future__ import annotations

import dataclasses
import os
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


def _load(language: str) -> Catalog:
    path = TRANSLATIONS / f"{language}.po"
    if language == SOURCE_LANGUAGE or not path.exists():
        return Catalog(language, {})

    entries: dict[str, tuple[str, str]] = {}
    for entry in polib.pofile(str(path)):
        # Three ways an entry is not ready, and all three mean English:
        # nobody has typed anything, somebody typed a draft and flagged it, or
        # the entry is marked obsolete because the source string is gone.
        if not entry.msgstr.strip():
            continue
        if "fuzzy" in entry.flags:
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
    """Languages with at least one reviewed string, English always included.

    This is what decides whether the tablet shows a language choice at all. A
    toggle that switches to an untranslated app is the decoration this product
    removed once already, so the control does not exist until the content does.
    """
    ready = [SOURCE_LANGUAGE]
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
    if language == SOURCE_LANGUAGE:
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
    """How much of the course is signed off, for the team rather than a screen.

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
    for lesson in CURRICULUM:
        for key, english, is_legal in strings_for(lesson):
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
