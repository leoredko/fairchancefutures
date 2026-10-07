"""The human check on the door.

It is off unless a deployment asks for it, and when it is on it is one box a
person ticks, backed by a token that proves the page was loaded.
"""

import pytest


@pytest.fixture()
def guarded(client, monkeypatch):
    monkeypatch.setenv("BRIDGE_CAPTCHA", "1")
    return client


def _token_from(page_text: str) -> str:
    line = [l for l in page_text.splitlines() if "challenge_token" in l][0]
    return line.split('value="')[1].split('"')[0]


def test_the_door_asks_nothing_extra_by_default(client):
    """On a facility tablet this would be obstruction with no upside: nothing
    is crawling a device that cannot reach the open web."""
    assert "challenge_token" not in client.get("/signin").text
    assert client.post("/signin", data={"identifier": "28A1187"}).status_code == 200


def test_a_deployment_can_turn_it_on(guarded):
    page = guarded.get("/signin").text
    assert "challenge_token" in page
    assert "Click if you are human" in page


def test_a_ticked_box_gets_through(guarded):
    page = guarded.get("/signin").text
    landed = guarded.post("/signin", data={
        "identifier": "28A1187",
        "challenge_token": _token_from(page),
        "challenge_human": "1",
    })
    assert landed.status_code == 200
    assert "challenge_token" not in landed.text      # past the door


def test_an_unticked_box_is_turned_away_with_a_new_token(guarded):
    page = guarded.get("/signin").text
    again = guarded.post("/signin", data={
        "identifier": "28A1187",
        "challenge_token": _token_from(page),
    })
    assert again.status_code == 400
    assert _token_from(again.text) != _token_from(page)


def test_a_script_that_never_loaded_the_page_is_turned_away(guarded):
    """The whole point. No token, no entry, ticked or not."""
    assert guarded.post("/signin", data={"identifier": "28A1187"}).status_code == 400
    assert guarded.post("/signin", data={
        "identifier": "28A1187", "challenge_human": "1",
    }).status_code == 400


def test_a_token_somebody_edited_is_turned_away(guarded):
    from app.challenge import verify

    token = _token_from(guarded.get("/signin").text)
    body, mac = token.rsplit(".", 1)
    forged = body[:-2] + "AA." + mac
    assert not verify(forged, "1")


def test_a_stale_token_is_turned_away(client):
    """Twenty minutes is for somebody reading slowly. It is not a token worth
    harvesting and coming back to."""
    import json
    import time

    from app import challenge
    from app.auth import sign_blob

    stale = json.dumps({
        "at": time.time() - challenge.LIFETIME_SECONDS - 60,
    }).encode()
    assert not challenge.verify(sign_blob(stale), "1")


def test_the_helper_door_asks_too(guarded):
    """A public URL is a public URL whichever door you come in by."""
    assert "challenge_token" in guarded.get("/helper").text
    assert guarded.post("/helper", data={"code": "BRIDGE-4417"}).status_code == 400
