"""The course in Spanish.

The claim defended here is not "the translation is good", which no test can
check. It is that the Spanish is content rather than machinery: it falls back
per string, it never touches a citation, and one environment variable takes
the whole language back out if a line turns out to be wrong in front of
people.
"""

import subprocess
import sys
from pathlib import Path

import polib
import pytest

from app import i18n
from app.lessons import CURRICULUM

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def catalog_dir(tmp_path, monkeypatch):
    """A translations folder of our own, so tests never read the real file."""
    monkeypatch.setattr(i18n, "TRANSLATIONS", tmp_path)
    i18n.reload()
    yield tmp_path
    i18n.reload()


def write_po(folder: Path, entries, language="es"):
    """entries: (key, english, spanish, fuzzy)"""
    po = polib.POFile()
    po.metadata = {"Language": language, "MIME-Version": "1.0",
                   "Content-Type": "text/plain; charset=utf-8"}
    for key, english, spanish, fuzzy in entries:
        entry = polib.POEntry(msgctxt=key, msgid=english, msgstr=spanish)
        if fuzzy:
            entry.flags = ["fuzzy"]
        po.append(entry)
    po.save(str(folder / f"{language}.po"))
    i18n.reload()


FIRST = CURRICULUM[0]


# --------------------------------------------------------------------------
# the gate
# --------------------------------------------------------------------------

def test_a_signed_off_translation_reaches_the_screen(catalog_dir):
    write_po(catalog_dir, [
        (i18n.lesson_key(FIRST.slug, "title"), FIRST.title, "Los tres papeles", False),
    ])
    assert i18n.translate_lesson(FIRST, "es").title == "Los tres papeles"


def test_the_switch_takes_the_whole_language_back_out(catalog_dir, monkeypatch):
    """The rollback. A bilingual reader checked this course, not a certified
    translator, so the answer to "one line is wrong and we are on stage" has
    to be something you can do from the host in ten seconds."""
    write_po(catalog_dir, [
        (i18n.lesson_key(FIRST.slug, "title"), FIRST.title, "Los tres papeles", False),
    ])
    assert i18n.translate_lesson(FIRST, "es").title == "Los tres papeles"
    assert i18n.offered() is True

    monkeypatch.setenv("BRIDGE_SPANISH", "off")
    assert i18n.translate_lesson(FIRST, "es").title == FIRST.title
    assert i18n.offered() is False
    assert i18n.available() == ("en",)


def test_a_line_marked_needs_work_still_shows_while_somebody_checks_it(catalog_dir):
    """Fuzzy is informational now. It tells the reader in Poedit which lines
    nobody has been through yet; it does not hold the course back."""
    write_po(catalog_dir, [
        (i18n.lesson_key(FIRST.slug, "title"), FIRST.title, "Los tres papeles", True),
    ])
    assert i18n.translate_lesson(FIRST, "es").title == "Los tres papeles"


def test_an_empty_translation_falls_back_to_english(catalog_dir):
    write_po(catalog_dir, [
        (i18n.lesson_key(FIRST.slug, "title"), FIRST.title, "", False),
    ])
    assert i18n.translate_lesson(FIRST, "es").title == FIRST.title


def test_a_translation_approved_against_older_english_is_not_used(catalog_dir):
    """Somebody signed off Spanish for a sentence, then the English was
    reworded. The Spanish now reads fluently and says the wrong thing, which
    is the worst of the three failure modes because it looks finished."""
    write_po(catalog_dir, [
        (i18n.lesson_key(FIRST.slug, "title"),
         "Some wording this card no longer uses", "Traducción vieja", False),
    ])
    assert i18n.translate_lesson(FIRST, "es").title == FIRST.title


def test_a_missing_catalog_is_not_an_error(catalog_dir):
    """No es.po at all, for instance very early or in a stripped image. The
    course still runs, in English."""
    assert i18n.translate_lesson(FIRST, "es").title == FIRST.title
    assert i18n.catalog("es").is_empty


# --------------------------------------------------------------------------
# what the tablet offers
# --------------------------------------------------------------------------

def test_the_language_choice_does_not_appear_until_something_is_translated(catalog_dir):
    """The EN / ES pill was removed once already for being decoration over an
    English-only app. It comes back only when it does something, and it is
    gone again the moment the switch is thrown."""
    assert i18n.available() == ("en",)
    assert i18n.offered() is False

    write_po(catalog_dir, [
        (i18n.lesson_key(FIRST.slug, "title"), FIRST.title, "Los tres papeles", False),
    ])
    assert i18n.available() == ("en", "es")
    assert i18n.offered() is True


def test_a_language_nobody_serves_falls_back_to_english(catalog_dir):
    for asked in ("fr", "es-MX", "", None, "nonsense"):
        assert i18n.normalize(asked) == "en"


def test_a_served_language_is_accepted_with_or_without_a_region(catalog_dir):
    write_po(catalog_dir, [
        (i18n.lesson_key(FIRST.slug, "title"), FIRST.title, "Los tres papeles", False),
    ])
    assert i18n.normalize("es") == "es"
    assert i18n.normalize("es-MX") == "es"
    assert i18n.normalize("ES") == "es"


# --------------------------------------------------------------------------
# what translation must never touch
# --------------------------------------------------------------------------

def test_translating_a_lesson_leaves_its_citations_alone(catalog_dir):
    """The source line under a card is a statute and a URL out of
    app/sources.py. Somebody may carry 15 U.S.C. 1681i to a law library."""
    cited = next(c for lesson in CURRICULUM for c in lesson.cards if c.fact_key)
    lesson = next(l for l in CURRICULUM if cited in l.cards)
    write_po(catalog_dir, [
        (i18n.lesson_key(lesson.slug, "title"), lesson.title, "Título", False),
    ])
    translated = i18n.translate_lesson(lesson, "es")
    for before, after in zip(lesson.cards, translated.cards):
        assert after.fact_key == before.fact_key
        assert after.cited == before.cited
        assert after.source_url == before.source_url


def test_translating_a_lesson_does_not_change_its_slug_or_shape(catalog_dir):
    write_po(catalog_dir, [
        (i18n.lesson_key(FIRST.slug, "title"), FIRST.title, "Los tres papeles", False),
    ])
    translated = i18n.translate_lesson(FIRST, "es")
    assert translated.slug == FIRST.slug
    assert translated.screens == FIRST.screens
    assert len(translated.cards) == len(FIRST.cards)
    assert translated.check.answer == FIRST.check.answer
    assert {c.value for c in translated.check.choices} == \
           {c.value for c in FIRST.check.choices}


def test_english_is_returned_untouched_rather_than_looked_up(catalog_dir):
    """There is no en.po. Translating English into English is a file nobody
    would maintain and a class of bug for nothing."""
    assert i18n.translate_lesson(FIRST, "en") is FIRST


# --------------------------------------------------------------------------
# the file on disk
# --------------------------------------------------------------------------

def test_every_string_in_the_course_is_offered_to_a_translator():
    """A card added without re-running the extract script would be a screen
    that can never be translated, and nothing would say so."""
    result = subprocess.run(
        [sys.executable, "scripts/i18n_extract.py", "--check"],
        cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_shipped_catalog_names_only_strings_that_still_exist():
    """A key in the file that no card produces is a translation pointing at a
    screen that is gone. Obsolete entries are allowed, since they are kept on
    purpose in case a card comes back."""
    live = set()
    for lesson in CURRICULUM:
        for key, _english, _legal in i18n.strings_for(lesson):
            live.add(key)
    path = ROOT / "app" / "translations" / "es.po"
    for entry in polib.pofile(str(path)):
        if entry.obsolete or not entry.msgctxt:
            continue
        assert entry.msgctxt in live, entry.msgctxt


def test_every_card_that_cites_a_statute_is_flagged_for_the_reviewer():
    """A translator cannot know which lines carry legal weight by reading
    Spanish. The file has to tell them."""
    legal_keys = set()
    for lesson in CURRICULUM:
        for key, _english, is_legal in i18n.strings_for(lesson):
            if is_legal:
                legal_keys.add(key)
    assert legal_keys, "the course cites no sources, which cannot be right"

    path = ROOT / "app" / "translations" / "es.po"
    for entry in polib.pofile(str(path)):
        if entry.msgctxt in legal_keys:
            assert "LEGAL" in (entry.comment or ""), entry.msgctxt
