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
    live.update(key for key, _english, _legal in i18n.ui_strings())
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


# --------------------------------------------------------------------------
# the screens around the course
#
# The lessons were translated first, and choosing Español at the door then
# changed nothing anybody could see: the door, the PIN screen and every button
# stayed English. These defend the claim that the language is on all the way
# from the door to the end of the course.
# --------------------------------------------------------------------------

import re  # noqa: E402

from app import challenge  # noqa: E402
from app.auth import AuthError, check_pin_strength  # noqa: E402
from app.identifiers import InvalidIdentifier, parse  # noqa: E402
from app.paths import PATHS  # noqa: E402
from app.ui_strings import UI  # noqa: E402
from tests.conftest import sign_in_inside  # noqa: E402


def _spanish(client):
    client.post("/language", data={"lang": "es", "back": "/signin"})
    return client


def test_choosing_espanol_changes_the_door_itself(client):
    _spanish(client)
    door = client.get("/signin").text
    assert "Número DIN o NYS ID" in door
    assert "Siguiente" in door
    assert 'lang="es"' in door
    assert "DIN number or NYS ID" not in door


def test_english_is_still_english_when_nobody_chose(client):
    door = client.get("/signin").text
    assert "DIN number or NYS ID" in door
    assert 'lang="en"' in door


def test_the_course_screens_are_spanish_from_the_first_question_to_the_last(client):
    _spanish(client)
    sign_in_inside(client)
    for url, expected, english in [
        ("/inside/start", "¿Qué quieres hacer primero?", "What do you want to do first?"),
        ("/inside/learn", "Aprende sobre el crédito.", "Learn about credit."),
        ("/inside/learn/lesson/three-papers/0", "Se guarda sobre la marcha",
         "Saved as you go"),
    ]:
        page = client.get(url).text
        assert expected in page, url
        assert english not in page, url
        assert "Cerrar sesión" in page, url
        assert "Sign out" not in page, url


def test_a_person_can_be_signed_in_and_in_english_after_switching_back(client):
    _spanish(client)
    client.post("/language", data={"lang": "en", "back": "/signin"})
    sign_in_inside(client)
    assert "Learn about credit." in client.get("/inside/learn").text


def test_the_switch_takes_the_screens_back_to_english_too(client, monkeypatch):
    _spanish(client)
    monkeypatch.setenv("BRIDGE_SPANISH", "off")
    door = client.get("/signin").text
    assert "DIN number or NYS ID" in door
    assert "Español" not in door
    sign_in_inside(client)
    assert "Learn about credit." in client.get("/inside/learn").text


def test_the_paths_have_words_in_both_languages(client):
    """The start screen builds its keys from the path, so a path added without
    its three strings would show a raw key."""
    for path in PATHS:
        for part in ("label", "blurb", "cta"):
            assert f"path.{path.key}.{part}" in UI, (path.key, part)


def test_every_string_a_template_asks_for_exists():
    """A misspelt key is a KeyError on a person's screen."""
    asked = set()
    for template in (ROOT / "app" / "templates").rglob("*.html"):
        asked.update(re.findall(r"\bt\(\s*'(\w+(?:\.\w+)+)'", template.read_text()))
    assert asked, "no template asks for a translated string, which cannot be right"
    assert asked <= set(UI), sorted(asked - set(UI))


def test_every_screen_string_has_a_spanish_line_that_keeps_its_blanks():
    """`{n}` is a number the screen fills in. A translation that loses or
    renames one is thrown away at render time, so a translator's typo shows up
    here first, as English on a Spanish screen."""
    i18n.reload()
    book = i18n.catalog("es")
    for key, english in UI.items():
        spanish = book.get(key, english)
        # "No" is the same word in both languages, so it cannot tell a
        # translated line from a missing one.
        if english == "No":
            continue
        assert spanish != english, f"{key} is still English"
        assert i18n._fields(spanish) == i18n._fields(english), key


def test_a_translation_that_lost_its_blank_falls_back_to_english(catalog_dir):
    write_po(catalog_dir, [("learn.finished", UI["learn.finished"],
                            "Terminaste todas.", False)])
    assert i18n.ui("learn.finished", "es", total=11) == "You have finished all 11."


def test_the_errors_people_actually_hit_are_translated():
    """The messages come out of auth.py and identifiers.py, which know no
    language, so the screen matches them by their English. If somebody rewords
    one over there, this is where it stops matching."""
    raised = []
    for attempt in ["12", "123456", "111111", "834712"]:
        try:
            check_pin_strength(attempt, identifier="28-A-1187")
        except AuthError as exc:
            raised.append(str(exc))
    for typed in ["", "28A", "98A", "hello there"]:
        try:
            parse(typed)
        except InvalidIdentifier as exc:
            raised.append(str(exc))
    assert len(raised) >= 5, raised
    for message in raised:
        assert i18n.translate_error(message, "es") != message, message


def test_an_error_keeps_the_numbers_it_was_carrying():
    out = i18n.translate_error("That PIN is not right. 3 tries left before it locks.", "es")
    assert "3" in out and "PIN" in out and "tries" not in out


def test_an_error_nobody_wrote_a_translation_for_stays_as_it_was():
    assert i18n.translate_error("Something else entirely.", "es") == "Something else entirely."
    assert i18n.translate_error("That PIN is not right. 3 tries left before it locks.", "en") \
        == "That PIN is not right. 3 tries left before it locks."


def test_the_human_check_is_asked_and_answered_in_the_language_of_the_door():
    ask = challenge.issue("es")
    assert ask["question"].startswith("¿Cuánto es")
    left, right = re.findall(r"es (\w+) más (\w+)\?", ask["question"])[0]
    total = challenge.WORDS_ES.index(left) + challenge.WORDS_ES.index(right)
    assert challenge.verify(ask["token"], str(total))
    assert challenge.verify(ask["token"], challenge.WORDS_ES[total])
    assert challenge.verify(ask["token"], challenge.WORDS[total])


def test_the_language_page_is_reachable_and_changes_the_language(client):
    page = client.get("/language", params={"back": "/inside"}).text
    assert "Español" in page and 'href="/inside"' in page
    out = client.post("/language", data={"lang": "es", "back": "/language"},
                      follow_redirects=False)
    assert out.status_code == 303
    assert "Idioma" in client.get("/language").text


def test_asking_for_another_language_is_recorded_and_thanked(client):
    from app.store import STATE

    out = client.post("/language/request", data={"language": "  Haitian   Creole ", "back": "/inside"},
                      follow_redirects=True)
    assert "Thank you for the feedback" in out.text
    assert STATE.language_requests[-1]["language"] == "Haitian Creole"


def test_a_blank_language_request_is_not_a_request(client):
    from app.store import STATE

    before = len(STATE.language_requests)
    out = client.post("/language/request", data={"language": "   "}, follow_redirects=True)
    assert "Thank you for the feedback" not in out.text
    assert len(STATE.language_requests) == before


def test_the_other_button_at_the_door_leads_to_the_request_form(client):
    assert 'href="/language?back=/signin#other"' in client.get("/signin").text


def test_the_intake_questions_follow_the_language_chosen_at_the_door(client):
    from tests.conftest import sign_in_inside

    client.post("/language", data={"lang": "es", "back": "/signin"})
    sign_in_inside(client, "28A1967")
    page = client.get("/inside/intake/1").text
    assert "¿Sabes cuál es tu puntaje de crédito?" in page
    assert "Cerrar sesión" in page and "1 de 6" in page
    assert "Do you know" not in page and "Sign out" not in page

    client.post("/language", data={"lang": "en", "back": "/signin"})
    assert "Do you know what your credit score is?" in client.get("/inside/intake/1").text


def test_the_explanation_where_you_stand_and_case_screens_follow_the_language(client):
    from tests.conftest import sign_in_inside

    client.post("/language", data={"lang": "es", "back": "/signin"})
    sign_in_inside(client, "28E3306")
    explain = client.get("/inside/how-this-works").text
    assert "Entendido, sigamos" in explain and "Got it" not in explain
    stand = client.get("/inside/where-you-stand").text
    assert "Aquí es donde estás empezando." in stand and "starting" not in stand
    case = client.get("/inside/case").text
    assert "Tus documentos" in case and "Todavía no" in case
    assert "Your papers" not in case and "Open my reports" not in case
