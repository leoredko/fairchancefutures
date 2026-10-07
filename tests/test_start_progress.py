"""The first screen says where a person is up to, not "start" every time.

Somebody who did half the course and came back to switch paths must not be
told to start what they have started. Both buttons read from what is saved.
"""

from app import lessons
from app.questions import INSIDE_QUESTIONS
from app.store import STATE
from tests.conftest import sign_in_inside

FRESH = "28A0931"          # D. Marsh, nothing started
SLUG = lessons.CURRICULUM[0].slug


def page(client):
    sign_in_inside(client, identifier=FRESH)
    return client.get("/inside/start").text


def person():
    return STATE.clients["d-marsh"]


def test_nothing_started_still_says_start(client):
    html = page(client)
    assert "Start learning" in html
    assert "Start on my credit" in html
    assert "Continue where you are up to" not in html
    assert "Continue my questions" not in html


def test_half_way_through_a_lesson_says_continue_not_start_learning(client):
    sign_in_inside(client, identifier=FRESH)
    lessons.record_card(person(), SLUG, 2)
    html = client.get("/inside/start").text
    assert "Continue where you are up to" in html
    assert "Carry on with" in html
    assert "0 of" not in html
    assert "Start learning" not in html


def test_finished_lessons_are_counted_on_the_button_card(client):
    sign_in_inside(client, identifier=FRESH)
    lessons.record_answer(person(), SLUG, "a")
    html = client.get("/inside/start").text
    total = len(lessons.CURRICULUM)
    assert f"1 of {total} done" in html
    assert "Continue where you are up to" in html


def test_the_whole_course_done_offers_a_way_back_over_it(client):
    sign_in_inside(client, identifier=FRESH)
    for lesson in lessons.CURRICULUM:
        lessons.record_answer(person(), lesson.slug, "a")
    html = client.get("/inside/start").text
    assert "Go back over the lessons" in html
    assert "Start learning" not in html
    assert "Continue where you are up to" not in html


def test_some_questions_answered_says_continue_with_the_count(client):
    sign_in_inside(client, identifier=FRESH)
    first = INSIDE_QUESTIONS[0]
    person().intake_answers[first.field] = first.options[0].value
    html = client.get("/inside/start").text
    assert "Continue my questions" in html
    assert f"1 of {len(INSIDE_QUESTIONS)} questions answered" in html
    assert "Start on my credit" not in html


def test_every_question_answered_says_see_where_i_stand(client):
    sign_in_inside(client, identifier=FRESH)
    for q in INSIDE_QUESTIONS:
        person().intake_answers[q.field] = q.options[0].value
    html = client.get("/inside/start").text
    assert "See where I stand" in html
    assert "Start on my credit" not in html
    assert "Continue my questions" not in html


def test_the_progress_lines_come_through_in_spanish(client):
    client.post("/language", data={"lang": "es"})
    sign_in_inside(client, identifier=FRESH)
    lessons.record_card(person(), SLUG, 2)
    html = client.get("/inside/start").text
    assert "Continuar donde te quedaste" in html
    assert "Continue where you are up to" not in html


def test_the_last_question_lands_on_a_summary_where_any_answer_can_be_changed(client):
    """Every answer in one place before it is used, and a change goes straight
    back to the summary rather than through the questions again."""
    sign_in_inside(client, identifier=FRESH)
    for q in INSIDE_QUESTIONS:
        last = client.post(f"/inside/intake/{q.index}",
                           data={q.field: q.options[0].value},
                           follow_redirects=False)
    assert last.headers["location"] == "/inside/review"

    html = client.get("/inside/review").text
    assert "Check your answers" in html
    for q in INSIDE_QUESTIONS:
        assert f'/inside/intake/{q.index}?from=review' in html
        assert q.prompt.replace("'", "&#39;") in html or q.prompt in html

    first = INSIDE_QUESTIONS[0]
    changed = client.post(f"/inside/intake/{first.index}?from=review",
                          data={first.field: first.options[-1].value},
                          follow_redirects=False)
    assert changed.headers["location"] == "/inside/review"
    assert person().intake_answers[first.field] == first.options[-1].value
