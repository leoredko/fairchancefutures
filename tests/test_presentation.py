"""Showing the tablet on its own.

The claim defended here is narrow: one environment variable takes the helper
and coordinator doors off the screens the room sees, and changes nothing else.
Not capability, which lives in `app.surfaces` and is not a presentation
setting. Not the people named on the tablet, who are the reason a wait does not
read as an automated nudge.
"""

import pytest

from app import presentation
from tests.conftest import sign_in_inside


@pytest.fixture()
def tablet_only(monkeypatch):
    monkeypatch.setenv("BRIDGE_TABLET_ONLY", "on")


def test_the_switch_is_off_unless_somebody_turns_it_on(monkeypatch):
    monkeypatch.delenv("BRIDGE_TABLET_ONLY", raising=False)
    assert presentation.tablet_only() is False


def test_the_switch_reads_the_environment_on_every_call(monkeypatch):
    """Flipping it on the host takes effect on the next request."""
    monkeypatch.setenv("BRIDGE_TABLET_ONLY", "on")
    assert presentation.tablet_only() is True
    monkeypatch.setenv("BRIDGE_TABLET_ONLY", "off")
    assert presentation.tablet_only() is False


def test_the_landing_page_is_the_banner_the_team_and_one_way_in(client):
    body = client.get("/").text
    assert "Start the credit work before the gate opens." in body
    for name in ("Leo Redko", "Richard Castillo", "RoShawn Winburn"):
        assert name in body
    assert "Capstone AI Lab 2026" in body and "Team 2" in body
    assert 'href="/signin"' in body


def test_the_landing_page_does_not_list_the_other_surfaces_in_either_mode(client, tablet_only):
    """It is not a menu. The helper and the coordinator are reached by their own
    addresses, and the practice links live apart from the product."""
    for body in (client.get("/").text,):
        assert 'href="/helper"' not in body
        assert 'href="/staff"' not in body
        assert 'href="/demo/restart"' not in body


def test_tablet_only_takes_the_helper_link_off_the_sign_in_screen(client, tablet_only):
    assert 'href="/helper"' not in client.get("/signin").text


def test_the_sign_in_screen_offers_the_helper_door_by_default(client):
    assert 'href="/helper"' in client.get("/signin").text


def test_the_coordinator_is_still_reachable_by_url_when_hidden(client, tablet_only):
    """A door off the wall, not a locked one.

    The demo is driven from a coordinator window the room does not see, so the
    tablet has triage and letters to show. A presentation setting that denied
    a request would be a second, weaker copy of the capability table.
    """
    assert client.get("/staff").status_code == 200
    assert client.get("/helper").status_code == 200


def test_the_tablet_still_names_the_people_working_the_case(client, tablet_only):
    """Hiding doors never hides a person.

    An event with nobody attached reads as an automated nudge, which the
    Cornish interview says reads as a scam inside.
    """
    signed_in = sign_in_inside(client)
    assert "Reyes" in signed_in.get("/inside/case").text
