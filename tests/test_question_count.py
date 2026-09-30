"""How many intake questions there are is a fact with one home.

The set has been six for a while and will not stay six. So nothing counts them
by hand: not a route deciding whether somebody is done, and not a sentence on a
screen promising a person a number before they start. A count written down in a
second place is a count that goes wrong quietly, which is how a screen ends up
telling somebody they answered everything while a question is still waiting.
"""

from pathlib import Path

import pytest

from app import routes
from app.questions import INSIDE_QUESTIONS
from tests.conftest import sign_in_inside

ROOT = Path(__file__).resolve().parents[1]

# Every word a person could read as a promise about how long this takes.
COUNTING_WORDS = ("six question", "six answer", "answer six", "six intake")


def screens():
    """What a person's eyes actually land on."""
    for path in sorted((ROOT / "app" / "templates").rglob("*.html")):
        yield path


def test_no_screen_promises_a_number_of_questions():
    said_it = [
        f"{path.relative_to(ROOT)}: {word}"
        for path in screens()
        for word in COUNTING_WORDS
        if word in path.read_text().lower()
    ]
    assert said_it == []


def test_finishing_intake_is_measured_against_the_question_set(client, monkeypatch):
    """Not against a literal, which is how this broke.

    `/inside/learn/scores` decides where its back link goes by asking whether
    intake is done. It counted to six on its own, so a seventh question would
    have sent a half-finished person to the case screen.
    """
    from app.routes import inside as inside_routes

    signed_in = sign_in_inside(client)
    for question in INSIDE_QUESTIONS:
        signed_in.post(f"/inside/intake/{question.index}",
                       data={question.field: _an_answer(question)})

    # Marcus has answered every question there is, so the back link is the case.
    assert 'href="/inside/case"' in signed_in.get("/inside/learn/scores").text

    # One more question exists and he has not seen it. He is not done.
    monkeypatch.setattr(inside_routes, "INSIDE_QUESTIONS",
                        tuple(INSIDE_QUESTIONS) + (INSIDE_QUESTIONS[0],))
    page = signed_in.get("/inside/learn/scores").text
    assert 'href="/inside/how-this-works"' in page
    assert 'href="/inside/case"' not in page


def _an_answer(question):
    return question.options[0].value
