"""A key on the coordinator desk, for when the link goes to a room.

With BRIDGE_DESK_KEY set, /staff, /demo and /metrics need a cookie that /desk
hands out for the key. Everything else is untouched. Unset, nothing changes.
"""

import pytest

KEY = "a-long-desk-key"
GATED = ["/staff", "/staff/m-alvarez", "/demo/restart", "/metrics"]
OPEN = ["/", "/signin", "/helper", "/citations", "/roles", "/language"]


@pytest.fixture()
def locked(client, monkeypatch):
    monkeypatch.setenv("BRIDGE_DESK_KEY", KEY)
    return client


def test_with_no_key_set_the_desk_is_open_as_before(client):
    for url in GATED:
        assert client.get(url).status_code == 200


def test_with_a_key_set_the_desk_asks_for_it(locked):
    for url in GATED:
        r = locked.get(url)
        assert r.status_code == 401, url
        assert "desk key" in r.text.lower()
        assert "M. Alvarez" not in r.text


def test_the_tablet_and_the_phone_are_not_behind_the_key(locked):
    for url in OPEN:
        assert locked.get(url).status_code == 200, url


def test_a_post_to_the_desk_is_refused_without_the_key(locked):
    r = locked.post("/demo/restart", data={"client_id": "a-torres"})
    assert r.status_code == 401
    r = locked.post("/staff/a-torres/documents/birth_certificate/on-file")
    assert r.status_code == 401


def test_the_wrong_key_gets_no_cookie(locked):
    r = locked.post("/desk", data={"key": "nope", "next": "/staff"})
    assert r.status_code == 401
    assert "not the desk key" in r.text
    assert locked.get("/staff").status_code == 401


def test_the_right_key_opens_the_desk_and_sends_you_where_you_were_going(locked):
    r = locked.post("/desk", data={"key": KEY, "next": "/demo/restart"},
                    follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/demo/restart"
    for url in GATED:
        assert locked.get(url).status_code == 200, url


def test_the_door_will_not_send_you_off_the_site(locked):
    for target in ["https://evil.example", "//evil.example", "/inside/case"]:
        r = locked.post("/desk", data={"key": KEY, "next": target},
                        follow_redirects=False)
        assert r.headers["location"] == "/staff", target


def test_a_cookie_that_was_not_signed_here_does_not_pass(locked):
    locked.cookies.set("bridge_desk", "desk.forged")
    assert locked.get("/staff").status_code == 401
