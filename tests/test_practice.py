"""A practice number for everybody who opens the shared link.

Off by default. With BRIDGE_PRACTICE on, the sign-in screen arrives with a fresh
28 number in the box and a case opened that way starts with its three reports,
so nobody in a room has to be told how.
"""

import re

from app.identifiers import parse
from app.store import STATE
from tests.conftest import PIN

BOX = re.compile(r'name="identifier"[^>]*value="([^"]*)"')


def box(client):
    return BOX.search(client.get("/signin").text).group(1)


def test_practice_is_off_unless_somebody_turns_it_on(client):
    assert box(client) == ""


def test_the_box_arrives_with_a_fresh_28_number_when_practice_is_on(client, monkeypatch):
    monkeypatch.setenv("BRIDGE_PRACTICE", "on")
    number = box(client)
    parsed = parse(number)
    assert parsed.normalized.startswith("28")


def test_two_visitors_are_not_handed_the_same_number(client, monkeypatch):
    monkeypatch.setenv("BRIDGE_PRACTICE", "on")
    seen = {box(client) for _ in range(25)}
    assert len(seen) > 20


def test_a_number_from_the_link_still_wins_over_a_practice_one(client, monkeypatch):
    monkeypatch.setenv("BRIDGE_PRACTICE", "on")
    page = client.get("/signin?identifier=28-E-3306").text
    assert 'value="28-E-3306"' in page


def test_the_practice_number_signs_in_and_the_case_has_three_reports(client, monkeypatch):
    monkeypatch.setenv("BRIDGE_PRACTICE", "on")
    number = box(client)
    key = parse(number).normalized
    client.post("/signin", data={"identifier": number})
    done = client.post("/signin/enroll", follow_redirects=False,
                       data={"normalized": key, "pin": PIN, "confirm": PIN})
    assert done.status_code == 303
    reports = STATE.reports[f"din-{key.lower()}"]
    assert sorted(r["bureau"] for r in reports) == ["Equifax", "Experian", "TransUnion"]
    assert all(r["confirmed"] for r in reports)
    assert client.get("/inside/report").status_code == 200


def test_a_case_opened_with_practice_off_starts_with_no_reports(client):
    key = "28Z0001"
    client.post("/signin", data={"identifier": key})
    assert not STATE.reports.get(f"din-{key.lower()}")


def test_the_screen_gets_no_extra_text_the_pin_rules_show_only_when_one_is_broken(client, monkeypatch):
    """Less on the screen, not more: no note about PINs on the sign-in. A weak
    PIN gets its reason on the screen where it was typed."""
    monkeypatch.setenv("BRIDGE_PRACTICE", "on")
    number = box(client)
    assert "PIN" not in client.get("/signin").text.split("<main")[-1].split("Next")[0]
    key = parse(number).normalized
    client.post("/signin", data={"identifier": number})
    for weak, reason in [("111111", "same number six times"),
                         ("123456", "counting up or down")]:
        r = client.post("/signin/enroll", data={"normalized": key, "pin": weak, "confirm": weak})
        assert reason in r.text
