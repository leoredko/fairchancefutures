"""Two paths, chosen by the person, steering rather than gating.

The claims defended here are the ones the feedback asked for and the ones the
house rules will not bend on. A person is asked what they want to do before
anything else. The answer changes where they land and what the screens push
toward. It never takes anything away, and the course stays reachable from
every screen including the one doing the asking.
"""

from app import paths
from app.store import STATE
from tests.conftest import sign_in_inside, sign_in_staff

FRESH = "28A0931"     # J. Whitfield, the seeded person with nothing started
MID_CASE = "28A1187"  # Marcus W., mid-dispute


def choose(signed_in, key):
    return signed_in.post("/inside/start", data={"path": key},
                          follow_redirects=False)


def test_a_new_person_is_asked_what_they_want_before_anything_else(client):
    signed_in = sign_in_inside(client, identifier=FRESH)
    assert signed_in.get("/inside", follow_redirects=False
                         ).headers["location"] == "/inside/start"


def test_the_question_is_asked_in_two_choices_and_no_more(client):
    """A third option dressed up as help is a third thing to read."""
    signed_in = sign_in_inside(client, identifier=FRESH)
    page = signed_in.get("/inside/start").text
    for path in paths.PATHS:
        assert path.label in page
    assert page.count('name="path"') == len(paths.PATHS)


def test_picking_the_course_lands_on_the_course(client):
    signed_in = sign_in_inside(client, identifier=FRESH)
    choose(signed_in, paths.LEARN.key)
    assert signed_in.get("/inside", follow_redirects=False
                         ).headers["location"] == "/inside/learn"


def test_picking_credit_lands_on_the_question_they_stopped_on(client):
    signed_in = sign_in_inside(client, identifier=FRESH)
    choose(signed_in, paths.CREDIT.key)
    assert "/inside/intake/" in signed_in.get(
        "/inside", follow_redirects=False).headers["location"]


def test_a_person_mid_case_is_not_asked_again(client):
    """Being asked "what do you want to do" mid-dispute reads as a lost file."""
    signed_in = sign_in_inside(client, identifier=MID_CASE)
    assert signed_in.get("/inside", follow_redirects=False
                         ).headers["location"] == "/inside/case"


def test_the_choice_steers_and_never_gates(client):
    """The whole difference between a path and a rung.

    Somebody who picked the course still reaches intake, the case and their
    reports. Nothing is locked behind a choice made in ten seconds.
    """
    signed_in = sign_in_inside(client, identifier=MID_CASE)
    choose(signed_in, paths.LEARN.key)
    for url in ("/inside/intake/1", "/inside/case", "/inside/report",
                "/inside/where-you-stand"):
        assert signed_in.get(url).status_code == 200, url


def test_the_course_is_reachable_from_the_screen_doing_the_asking(client):
    """The chooser is a tablet screen, so the house rule applies to it too."""
    signed_in = sign_in_inside(client, identifier=FRESH)
    assert 'href="/inside/learn"' in signed_in.get("/inside/start").text


def test_the_switch_is_on_every_tablet_screen(inside):
    """A person who wants the other path should not have to go looking."""
    for url in ("/inside/case", "/inside/learn", "/inside/intake/1",
                "/inside/report", "/inside/where-you-stand",
                "/inside/authorization", "/inside/after",
                "/inside/learn/scores", "/inside/how-this-works"):
        page = inside.get(url, follow_redirects=True)
        assert page.status_code == 200, url
        assert 'href="/inside/start"' in page.text, f"no switch on {url}"


def test_switching_back_is_two_taps_and_says_where_you_are(client):
    signed_in = sign_in_inside(client, identifier=MID_CASE)
    choose(signed_in, paths.LEARN.key)
    page = signed_in.get("/inside/start").text
    assert "What you are doing now" in page

    choose(signed_in, paths.CREDIT.key)
    assert signed_in.get("/inside", follow_redirects=False
                         ).headers["location"] == "/inside/case"


def test_the_course_does_not_nag_somebody_who_never_asked_for_intake(client):
    """The guiding hand stays invisible by not pointing at unasked-for work."""
    signed_in = sign_in_inside(client, identifier=FRESH)
    choose(signed_in, paths.LEARN.key)
    assert "Back to my questions" not in signed_in.get("/inside/learn").text


def test_a_value_that_is_not_a_path_leaves_the_question_unanswered(client):
    """Not a 500, and not a silent write of nonsense into the case file."""
    signed_in = sign_in_inside(client, identifier=FRESH)
    assert choose(signed_in, "everything").status_code == 303
    assert STATE.clients["j-whitfield"].path == ""
    assert signed_in.get("/inside", follow_redirects=False
                         ).headers["location"] == "/inside/start"


def test_the_queue_says_what_each_person_chose(client):
    """So a quiet row reads as somebody taking their time, not a stalled intake."""
    page = sign_in_staff(client).get("/staff").text
    assert paths.CREDIT.queue_label in page
    assert "Has not chosen yet" in page


def test_the_queue_never_shows_the_stored_key(client):
    """No column name and no enum value reaches a screen."""
    page = sign_in_staff(client).get("/staff").text
    assert ">credit<" not in page
    assert ">learn<" not in page
