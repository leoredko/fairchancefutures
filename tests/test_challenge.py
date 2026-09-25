"""The human check on the door.

It is off unless a deployment asks for it, and when it is on it has to be
answerable by a person and not by a script that never loads the page.
"""

import pytest

from conftest import PIN


@pytest.fixture()
def guarded(client, monkeypatch):
    monkeypatch.setenv("BRIDGE_CAPTCHA", "1")
    return client


def _answer_from(page_text: str) -> str:
    """Read the question the way a person does, and work it out."""
    from app.challenge import WORDS

    line = [l for l in page_text.splitlines() if "What is" in l][0]
    words = line.replace("?", " ").split()
    numbers = [WORDS.index(w) for w in words if w in WORDS]
    return str(sum(numbers))


def _token_from(page_text: str) -> str:
    line = [l for l in page_text.splitlines() if "challenge_token" in l][0]
    return line.split('value="')[1].split('"')[0]


def test_the_door_asks_nothing_extra_by_default(client):
    """On a facility tablet this would be obstruction with no upside: nothing
    is crawling a device that cannot reach the open web."""
    assert "challenge_token" not in client.get("/signin").text
    assert client.post("/signin", data={"identifier": "28A1187"}).status_code == 200


def test_a_deployment_can_turn_it_on(guarded):
    assert "challenge_token" in guarded.get("/signin").text


def test_a_right_answer_gets_through(guarded):
    page = guarded.get("/signin").text
    landed = guarded.post("/signin", data={
        "identifier": "28A1187",
        "challenge_token": _token_from(page),
        "challenge_answer": _answer_from(page),
    })
    assert landed.status_code == 200
    assert "challenge_token" not in landed.text      # past the door


def test_the_word_counts_as_much_as_the_digit(guarded):
    """It is a speed bump, not a spelling test."""
    from app.challenge import WORDS, issue, verify

    made = issue()
    digits = _answer_from(made["question"])
    assert verify(made["token"], digits)
    assert verify(made["token"], WORDS[int(digits)])


def test_a_wrong_answer_is_turned_away_with_a_new_question(guarded):
    page = guarded.get("/signin").text
    again = guarded.post("/signin", data={
        "identifier": "28A1187",
        "challenge_token": _token_from(page),
        "challenge_answer": "99",
    })
    assert again.status_code == 400
    assert _token_from(again.text) != _token_from(page)


def test_a_script_that_never_loaded_the_page_is_turned_away(guarded):
    """The whole point. No token, no entry."""
    assert guarded.post("/signin", data={"identifier": "28A1187"}).status_code == 400


def test_a_token_somebody_edited_is_turned_away(guarded):
    page = guarded.get("/signin").text
    token = _token_from(page)
    body, mac = token.rsplit(".", 1)
    forged = body[:-2] + "AA." + mac
    assert not __import__("app.challenge", fromlist=["verify"]).verify(forged, "3")


def test_a_stale_token_is_turned_away(client):
    """Twenty minutes is for somebody reading slowly. It is not a token worth
    harvesting and coming back to."""
    import json
    import time

    from app import challenge
    from app.auth import sign_blob

    stale = json.dumps({
        "sum": 7, "at": time.time() - challenge.LIFETIME_SECONDS - 60,
    }).encode()
    assert not challenge.verify(sign_blob(stale), "7")


def test_the_helper_door_asks_too(guarded):
    """A public URL is a public URL whichever door you come in by."""
    assert "challenge_token" in guarded.get("/helper").text
    assert guarded.post("/helper", data={"code": "BRIDGE-4417"}).status_code == 400


def test_it_says_why_it_is_asking(guarded):
    """A captcha with no sentence under it reads as suspicion of the person."""
    assert "public demonstration link" in guarded.get("/signin").text
