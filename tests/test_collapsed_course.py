"""The course says less at a time and keeps the rest a tap away.

The index is eleven numbered tiles with the titles folded behind one tap, and a
long card shows its first few sentences and folds the rest. Nothing is removed:
the folded text is on the page, so it is read aloud and a tap finds it.
"""

import html as htmllib
import re

from app import lessons
from app.lessons import COLLAPSE_AFTER, lead_and_rest
from tests.conftest import sign_in_inside

SLUGS = [lesson.slug for lesson in lessons.CURRICULUM]


# --- the splitter -----------------------------------------------------------

def test_short_text_comes_back_whole_with_nothing_folded():
    assert lead_and_rest("One. Two. Three.") == ("One. Two. Three.", "")


def test_long_text_keeps_the_first_sentences_and_folds_the_rest():
    lead, rest = lead_and_rest("One. Two. Three. Four. Five.")
    assert lead == "One. Two. Three." and rest == "Four. Five."


def test_the_dial_is_one_number():
    assert lead_and_rest("A. B. C.", keep=1) == ("A.", "B. C.")
    assert COLLAPSE_AFTER >= 2


def test_an_abbreviation_is_not_the_end_of_a_sentence():
    lead, rest = lead_and_rest("Ask the U.S. Postal Service. Then wait. Then call. Then write.")
    assert lead.startswith("Ask the U.S. Postal Service.")
    assert "U.S." not in rest
    spanish, _ = lead_and_rest("Es de EE. UU. y llega pronto. Espera.", keep=1)
    assert spanish == "Es de EE. UU. y llega pronto."


def test_nothing_is_lost_by_folding_in_any_card_in_either_language():
    from app import i18n
    for language in ("en", "es"):
        for lesson in lessons.CURRICULUM:
            for card in i18n.translate_lesson(lesson, language).cards:
                lead, rest = lead_and_rest(card.body)
                assert " ".join([lead, rest]).strip() == " ".join(card.body.split())


# --- the course index ---------------------------------------------------------

def tiles(html):
    return re.findall(r'<a class="mod[^"]*"[^>]*href="/inside/learn/lesson/([^"]+)"', html)


def test_the_index_is_one_numbered_tile_per_module_in_order(client):
    sign_in_inside(client)
    html = client.get("/inside/learn").text
    assert tiles(html) == SLUGS
    assert len(SLUGS) == 11


def test_the_titles_and_summaries_are_folded_not_stacked(client):
    sign_in_inside(client)
    html = client.get("/inside/learn").text
    folded = html.split('<details class="more">')[-1]
    assert lessons.CURRICULUM[0].title in folded
    assert lessons.CURRICULUM[0].hook in folded
    before_the_fold = html.split('<details class="more">')[0] if html.count('<details class="more">') == 1 else html
    assert lessons.CURRICULUM[0].hook not in html.split('class="modules"')[0]


def test_only_the_first_sentence_of_the_intro_shows_until_asked(client):
    sign_in_inside(client)
    html = client.get("/inside/learn").text
    assert '<p class="lede">11 lessons, about 50 minutes in total.</p>' in html
    assert "pick it up tomorrow" in html          # still there, folded


def test_a_finished_module_and_one_in_progress_are_marked_on_their_tiles(client):
    from app.store import STATE
    sign_in_inside(client)
    me = STATE.clients["marcus-w"]
    lessons.record_answer(me, SLUGS[0], "a")
    lessons.record_card(me, SLUGS[1], 2)
    html = client.get("/inside/learn").text
    assert re.search(r'class="mod done[^"]*"[^>]*lesson/' + SLUGS[0], html)
    assert re.search(r'class="mod started[^"]*"[^>]*lesson/' + SLUGS[1], html)


def test_every_tile_has_a_name_a_screen_reader_can_say(client):
    sign_in_inside(client)
    html = client.get("/inside/learn").text
    assert 'aria-label="Module 1: ' + lessons.CURRICULUM[0].title in html


# --- a lesson card ------------------------------------------------------------

def find_long_card():
    for lesson in lessons.CURRICULUM:
        for index, card in enumerate(lesson.cards):
            if lead_and_rest(card.body)[1]:
                return lesson, index, card
    raise AssertionError("no long card to check")


def test_a_long_card_folds_its_tail_and_a_short_one_does_not(client):
    sign_in_inside(client)
    lesson, index, card = find_long_card()
    lead, rest = lead_and_rest(card.body)
    html = htmllib.unescape(client.get(f"/inside/learn/lesson/{lesson.slug}/{index}").text)
    assert f'<p class="lede">{lead}</p>' in html
    assert "Read more" in html and rest.split(".")[0][:30] in html
    short = next((l, i) for l in lessons.CURRICULUM for i, c in enumerate(l.cards)
                 if not lead_and_rest(c.body)[1] and not c.aside)
    page = client.get(f"/inside/learn/lesson/{short[0].slug}/{short[1]}").text
    assert "Read more" not in page


def test_the_folded_parts_are_in_spanish_too(client):
    client.post("/language", data={"lang": "es"})
    sign_in_inside(client)
    lesson, index, _ = find_long_card()
    assert "Leer más" in client.get(f"/inside/learn/lesson/{lesson.slug}/{index}").text
    assert "Módulo 1" in client.get("/inside/learn").text
