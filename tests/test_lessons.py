"""The credit course.

Education is the first priority of this product, so the claims defended here
are the ones that decide whether it is usable: it is always reachable, it never
loses somebody's place, and nothing in it states a rule without a source.
"""

import pytest

from app import lessons
from app.sources import FACTS
from conftest import sign_in_inside


# --------------------------------------------------------------------------
# the content itself
# --------------------------------------------------------------------------

def test_every_lesson_card_that_states_a_rule_names_its_source():
    """The house rule, enforced on the course rather than written about.

    A card may state no rule at all, but a card citing a key that is not in the
    registry would render a legal claim with a dead source line.
    """
    for lesson in lessons.CURRICULUM:
        for card in lesson.cards:
            if card.fact_key:
                assert card.fact_key in FACTS, f"{lesson.slug}: {card.fact_key}"
                assert card.cited
                assert card.source_url.startswith("https://")


def test_a_card_with_no_source_renders_no_citation_line():
    plain = lessons.Card(title="t", body="b")
    assert plain.cited == ""
    assert plain.source_url == ""


def test_every_lesson_has_a_check_whose_answer_is_one_of_its_choices():
    """A check whose answer matches no choice can never be the defensible one,
    so the done screen would tell everybody they got it wrong."""
    for lesson in lessons.CURRICULUM:
        values = {c.value for c in lesson.check.choices}
        assert lesson.check.answer in values, lesson.slug
        assert len(values) == len(lesson.check.choices), lesson.slug


def test_lesson_slugs_are_unique_and_url_safe():
    slugs = [l.slug for l in lessons.CURRICULUM]
    assert len(slugs) == len(set(slugs))
    for slug in slugs:
        assert slug == slug.lower()
        assert " " not in slug


def test_the_course_opens_with_the_lesson_that_has_a_deadline():
    """The documents lesson goes first because it is the only one somebody can
    act on the same day, which is what earns the second lesson."""
    assert lessons.CURRICULUM[0].slug == "three-papers"
    assert lessons.CURRICULUM[0].urgent_for


def test_screens_counts_the_cards_plus_the_check():
    for lesson in lessons.CURRICULUM:
        assert lesson.screens == len(lesson.cards) + 1


# --------------------------------------------------------------------------
# progress
# --------------------------------------------------------------------------

@pytest.fixture()
def person():
    from app.store import Client

    return Client(id="x", display_name="X", first_name="X",
                  release_date="2027-01-01")


def test_a_person_who_has_never_opened_a_lesson_has_no_stored_progress(person):
    assert person.lesson_progress == {}
    assert lessons.progress(person, "three-papers")["card"] == 0
    assert lessons.standing(person)["done"] == 0


def test_progress_remembers_the_furthest_card_not_the_latest(person):
    """Paging back to re-read card one must not throw away the fact that
    somebody had already got to card four."""
    lessons.record_card(person, "three-papers", 4)
    lessons.record_card(person, "three-papers", 1)
    assert lessons.progress(person, "three-papers")["card"] == 4


def test_answering_the_check_completes_the_lesson_whatever_the_answer(person):
    """Completion is for working through it, not for getting it right.

    Withholding the tick for a wrong answer would teach people to guess safely
    rather than to commit and then read the explanation.
    """
    lesson = lessons.lesson("three-papers")
    wrong = next(c.value for c in lesson.check.choices
                 if c.value != lesson.check.answer)
    lessons.record_answer(person, "three-papers", wrong)
    assert lessons.is_complete(person, "three-papers")


def test_re_reading_a_finished_lesson_keeps_it_finished(person):
    lessons.record_answer(person, "three-papers", "both")
    first_done_on = lessons.progress(person, "three-papers")["done_on"]
    lessons.open_at(person, "three-papers")
    lessons.record_card(person, "three-papers", 0)
    row = lessons.progress(person, "three-papers")
    assert row["done"]
    assert row["done_on"] == first_done_on


def test_standing_reaches_a_hundred_percent_only_when_every_lesson_is_done(person):
    for lesson in lessons.CURRICULUM[:-1]:
        lessons.record_answer(person, lesson.slug, lesson.check.answer)
    assert not lessons.finished_course(person)
    assert lessons.standing(person)["percent"] < 100

    last = lessons.CURRICULUM[-1]
    lessons.record_answer(person, last.slug, last.check.answer)
    assert lessons.finished_course(person)
    assert lessons.standing(person)["percent"] == 100
    assert lessons.standing(person)["minutes_left"] == 0


def test_an_unfinished_lesson_is_offered_before_an_unstarted_one(person):
    """The easiest thing to come back to is the thing already open."""
    lessons.record_card(person, "disputes", 2)
    assert lessons.next_up(person).slug == "disputes"


def test_what_is_offered_next_follows_the_case_the_person_is_actually_in(person):
    person.case_state = "errors_present"
    # The documents lesson is urgent for everybody, so clear it first to see
    # the state-specific pick.
    lessons.record_answer(person, "three-papers", "both")
    assert person.case_state in lessons.next_up(person).urgent_for


def test_nothing_is_ever_hidden_from_the_index(person):
    """next_up picks what to put in front of somebody. It never gates."""
    person.case_state = "errors_present"
    rows = lessons.index_rows(person)
    assert len(rows) == len(lessons.CURRICULUM)


# --------------------------------------------------------------------------
# the surface
# --------------------------------------------------------------------------

def test_the_course_is_reachable_from_every_tablet_screen(inside):
    """Always present is the whole design, and it means every screen.

    This test used to leave out the intake flow, and so did the template, on
    the theory that a second exit next to a question loses somebody's place.
    That was wrong twice over: every answer is saved as it is given, so
    stepping out costs nothing, and a person part way through a set of
    questions about credit has more reason to reach an explanation than less.
    """
    for url in ("/inside/intake/1", "/inside/intake/4", "/inside/how-this-works",
                "/inside/case", "/inside/report", "/inside/where-you-stand",
                "/inside/authorization", "/inside/learn/scores"):
        page = inside.get(url).text
        assert 'href="/inside/learn"' in page, url


def test_stepping_out_of_intake_comes_back_to_the_question(client):
    """Not to a case screen with nothing on it yet."""
    signed_in = sign_in_inside(client, identifier="28A0931")   # no intake yet
    course = signed_in.get("/inside/learn").text
    assert 'href="/inside"' in course
    assert "Back to my questions" in course

    landed = signed_in.get("/inside", follow_redirects=False)
    assert "/inside/intake/" in landed.headers["location"]


def test_a_finished_client_gets_the_case_link_instead(inside):
    course = inside.get("/inside/learn").text
    assert "My case" in course


def test_the_course_opens_without_finishing_intake(client):
    """Somebody who signs in and reads two lessons has got something out of
    this. Gating the course behind a form loses exactly the people it is for."""
    signed_in = sign_in_inside(client, identifier="28A0931")
    page = signed_in.get("/inside/learn")
    assert page.status_code == 200
    assert "Learn about credit" in page.text


def test_a_lesson_reopens_where_it_was_left(inside):
    inside.get("/inside/learn/lesson/three-papers/3")
    landed = inside.get("/inside/learn/lesson/three-papers",
                        follow_redirects=False)
    assert landed.headers["location"] == "/inside/learn/lesson/three-papers/3"


def test_progress_survives_signing_out_and_back_in(inside):
    """A tablet session ends without warning. Losing four screens of
    reading to that is how somebody decides the app is not worth starting."""
    inside.get("/inside/learn/lesson/disputes/2")
    inside.get("/signout")
    sign_in_inside(inside)
    landed = inside.get("/inside/learn/lesson/disputes", follow_redirects=False)
    assert landed.headers["location"] == "/inside/learn/lesson/disputes/2"


def test_the_last_card_leads_to_the_check_rather_than_off_the_end(inside):
    lesson = lessons.lesson("scams")
    page = inside.get(f"/inside/learn/lesson/scams/{len(lesson.cards)}")
    assert page.status_code == 200
    assert lesson.check.prompt[:40] in page.text


def test_an_index_past_the_end_lands_on_the_check_rather_than_erroring(inside):
    lesson = lessons.lesson("scams")
    page = inside.get("/inside/learn/lesson/scams/99")
    assert page.status_code == 200
    assert lesson.check.prompt[:40] in page.text


def test_an_unknown_lesson_goes_back_to_the_course_rather_than_500ing(inside):
    landed = inside.get("/inside/learn/lesson/not-a-lesson",
                        follow_redirects=False)
    assert landed.status_code == 303
    assert landed.headers["location"] == "/inside/learn"


def test_finishing_a_lesson_puts_a_named_dated_event_on_the_timeline(inside):
    """House rule: an event with nobody attached does not go on this timeline.
    The person did this one, so they are the actor."""
    from app.store import STATE

    inside.post("/inside/learn/lesson/three-papers/check", data={"choice": "both"})
    events = STATE.clients["marcus-w"].timeline
    finished = [e for e in events if "finished the lesson" in e["text"]]
    assert len(finished) == 1
    assert finished[0]["actor"] == "You"
    assert finished[0]["on"]


def test_re_answering_does_not_stack_a_second_timeline_event(inside):
    from app.store import STATE

    for _ in range(3):
        inside.post("/inside/learn/lesson/three-papers/check",
                    data={"choice": "both"})
    events = STATE.clients["marcus-w"].timeline
    assert sum("finished the lesson" in e["text"] for e in events) == 1


def test_a_wrong_answer_is_never_called_wrong_on_screen(inside):
    """A verdict in front of whoever is waiting for the tablet teaches people
    to stop answering. The explanation is the same either way."""
    lesson = lessons.lesson("three-papers")
    wrong = next(c.value for c in lesson.check.choices
                 if c.value != lesson.check.answer)
    inside.post("/inside/learn/lesson/three-papers/check", data={"choice": wrong})
    page = inside.get("/inside/learn/lesson/three-papers/done").text
    assert "wrong" not in page.lower()
    assert "incorrect" not in page.lower()
    assert lesson.check.why[:40] in page


def test_the_celebration_cannot_be_reached_without_finishing(inside):
    landed = inside.get("/inside/learn/finished", follow_redirects=False)
    assert landed.status_code == 303
    assert landed.headers["location"] == "/inside/learn"


def test_finishing_every_lesson_earns_the_celebration(inside):
    for lesson in lessons.CURRICULUM:
        inside.post(f"/inside/learn/lesson/{lesson.slug}/check",
                    data={"choice": lesson.check.answer})
    page = inside.get("/inside/learn/finished")
    assert page.status_code == 200
    assert "finished the whole course" in page.text.lower()


def test_the_last_lesson_sends_the_person_to_the_celebration(inside):
    for lesson in lessons.CURRICULUM[:-1]:
        inside.post(f"/inside/learn/lesson/{lesson.slug}/check",
                    data={"choice": lesson.check.answer})
    last = lessons.CURRICULUM[-1]
    inside.post(f"/inside/learn/lesson/{last.slug}/check",
                data={"choice": last.check.answer})
    landed = inside.get(f"/inside/learn/lesson/{last.slug}/done",
                        follow_redirects=False)
    assert landed.headers["location"] == "/inside/learn/finished"


def test_the_course_is_not_offered_to_a_helper_or_a_coordinator(client, helper):
    """The course belongs to the person whose credit it is. A helper opening it
    would be reading the tablet surface with somebody else's session."""
    assert helper.get("/inside/learn", follow_redirects=False).status_code in (303, 403)


def test_the_case_screen_no_longer_promises_a_lesson_that_does_not_exist(inside):
    """It used to advertise 'Lesson 3, what a secured card actually is' from a
    seeded string, and there was no lesson 3 and no lesson 1 or 2 either."""
    page = inside.get("/inside/case").text
    assert "Lesson 3" not in page
    assert "/inside/learn" in page


# --------------------------------------------------------------------------
# people who are not near release
# --------------------------------------------------------------------------

def test_somebody_years_out_is_not_led_with_a_release_deadline(person):
    """From a comment on the walkthrough: this applies to people 120 days from
    release, what about people doing 10 years who just want to educate
    themselves or get their report.

    Opening the course with a deadline nine years away says this product is
    for people on their way out. Reading your own report, learning what a
    score is, and the free report you are owed every 12 months are all
    available on day one of a long sentence.
    """
    from datetime import date, timedelta

    person.release_date = (date.today() + timedelta(days=9 * 365)).isoformat()
    assert lessons.far_from_release(person)
    first = lessons.next_up(person)
    assert not first.release_dependent, first.slug


def test_somebody_near_release_still_gets_the_documents_lesson_first(person):
    from datetime import date, timedelta

    person.release_date = (date.today() + timedelta(days=100)).isoformat()
    assert not lessons.far_from_release(person)
    assert lessons.next_up(person).slug == "three-papers"


def test_the_deadline_lesson_is_offered_but_never_hidden(person):
    """Not first, still listed, still openable. Somebody nine years out who
    wants it can have it."""
    from datetime import date, timedelta

    person.release_date = (date.today() + timedelta(days=9 * 365)).isoformat()
    rows = lessons.index_rows(person)
    assert len(rows) == len(lessons.CURRICULUM)
    documents = next(r for r in rows if r["lesson"].slug == "three-papers")
    assert not documents["for_you"]


def test_a_long_sentence_still_finishes_the_whole_course(person):
    """Stepping the deadline lesson aside must not make it unreachable, or
    somebody far out could never reach 100 percent."""
    from datetime import date, timedelta

    person.release_date = (date.today() + timedelta(days=9 * 365)).isoformat()
    for _ in range(len(lessons.CURRICULUM) + 2):
        nxt = lessons.next_up(person)
        if nxt is None:
            break
        lessons.record_answer(person, nxt.slug, nxt.check.answer)
    assert lessons.finished_course(person)


def test_a_missing_or_broken_release_date_is_treated_as_near(person):
    """Fail toward the deadline rather than away from it."""
    person.release_date = ""
    assert not lessons.far_from_release(person)
    person.release_date = "not a date"
    assert not lessons.far_from_release(person)
