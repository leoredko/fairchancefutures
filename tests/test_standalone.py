"""The single-file build.

Two things worth defending. That it stays in step with the Python rules, since
a demo file quoting a different reinvestigation window from the server app is
exactly the sort of thing somebody catches on stage. And that it really is
self-contained, because its whole reason to exist is being openable with no
server and no network.
"""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
APPS = ("inside", "family", "staff")


def _build_if_needed() -> None:
    if all((ROOT / "standalone" / f"bridge-{a}.html").exists() for a in APPS):
        return
    import subprocess
    import sys

    subprocess.run([sys.executable, "standalone/build.py"], cwd=ROOT, check=True)


@pytest.fixture(scope="module")
def pages() -> dict:
    """One file per surface, so a tablet gets the tablet app."""
    _build_if_needed()
    return {a: (ROOT / "standalone" / f"bridge-{a}.html").read_text()
            for a in APPS}


@pytest.fixture(scope="module")
def page(pages) -> str:
    """Anything true of one build is true of all three."""
    return pages["staff"]


@pytest.fixture(scope="module")
def payload(page: str) -> dict:
    """The generated block the page reads its rules from."""
    m = re.search(r"const RULES = (\{.*?\n\});", page, re.S)
    assert m, "the build did not inject the rules payload"
    return json.loads(m.group(1))


def test_the_four_states_match_the_python_ones(payload):
    from app.triage import PATH, STATE_LABEL, State

    built = {s["key"]: s for s in payload["states"]}
    assert set(built) == {s.value for s in State}
    for state in State:
        assert built[state.value]["label"] == STATE_LABEL[state]
        assert built[state.value]["plan"] == PATH[state]["plan"]
        assert built[state.value]["first_step"] == PATH[state]["first_step"]


def test_every_verified_fact_made_it_across(payload):
    from app.sources import FACTS

    built = {f["statement"] for f in payload["facts"]}
    for fact in FACTS.values():
        assert fact.statement in built, fact.key


def test_the_open_questions_made_it_across(payload):
    from app.sources import OPEN_QUESTIONS

    assert list(payload["open"]) == list(OPEN_QUESTIONS)


def test_all_three_bureau_addresses_made_it_across(payload):
    from app.bureaus import BUREAUS

    built = {b["name"]: b["address"] for b in payload["bureaus"]}
    assert set(built) == {b.name for b in BUREAUS}
    for bureau in BUREAUS:
        assert built[bureau.name] == list(bureau.dispute_address)


def test_the_letter_templates_are_the_python_ones(payload):
    from app.letters import DISPUTE_TEMPLATE, REPORT_REQUEST_TEMPLATE

    assert payload["disputeTemplate"] == DISPUTE_TEMPLATE
    assert payload["requestTemplate"] == REPORT_REQUEST_TEMPLATE


def test_the_intake_questions_are_the_python_ones(payload):
    from app.questions import INSIDE_QUESTIONS

    built = payload["insideQuestions"]
    assert len(built) == len(INSIDE_QUESTIONS)
    for got, want in zip(built, INSIDE_QUESTIONS):
        assert got["prompt"] == want.prompt
        assert [o["value"] for o in got["options"]] == [o.value for o in want.options]


def test_it_reaches_the_network_for_nothing(page: str):
    """It has to work from a USB stick, an email attachment, and a tablet with
    no signal. One remote script or font and it does not."""
    for tag in re.findall(r"<(?:script|link|img|iframe)[^>]*>", page):
        for attr in re.findall(r'(?:src|href)="([^"]+)"', tag):
            assert not attr.startswith(("http://", "https://", "//")), tag


def test_outbound_links_are_only_the_citations(page: str):
    """Anchor links to sources are fine and wanted; anything else loading from
    the network is not."""
    hrefs = set(re.findall(r'href="(https?://[^"]+)"', page))
    for href in hrefs:
        assert any(d in href for d in (
            "law.cornell.edu", "consumerfinance.gov", "consumer.ftc.gov",
            "equifax.com", "experian.com", "transunion.com")), href


def test_it_is_one_file(page: str):
    assert "__BRIDGE_CSS__" not in page
    assert "__BRIDGE_RULES__" not in page
    assert "__BRIDGE_ICON__" not in page
    assert "data:image/png;base64," in page


def test_each_surface_is_its_own_application(pages: dict):
    """A tablet gets the tablet app. No role switcher, no chooser screen."""
    for role, html in pages.items():
        assert f'const APP = "{role}"' in html, role
        assert "demo-bar" not in html, role


def test_the_three_apps_share_one_caseload_but_not_one_session(page: str):
    """A client the coordinator adds shows up on the tablet. Signing in on one
    app must not sign you out of another."""
    assert 'const KEY = "bridge.v1"' in page
    assert 'const SESSION_KEY = "bridge.session." + APP' in page


def test_nothing_calls_itself_a_prototype(pages: dict):
    """It is an application. The demo framing lives in docs/DEMO.md."""
    for role, html in pages.items():
        lowered = html.lower()
        for banned in ("prototype", "fictional caseload", "demo login",
                       "wireframe", "design note:"):
            assert banned not in lowered, f"{role}: {banned}"


def test_it_still_disclaims_any_official_affiliation(pages: dict):
    """The one piece of small print that stays. It handles prison identifiers,
    so it says plainly that it is not a state system."""
    for role, html in pages.items():
        assert "not affiliated with" in html.lower(), role
        assert "Department of Corrections" in html, role


def test_they_stay_small_enough_to_email(pages: dict):
    for role, html in pages.items():
        assert len(html.encode()) < 2_000_000, role


def test_the_coordinator_app_has_no_sign_in_at_all(pages: dict):
    """They are already signed in to the vendor case plan system. Asking for a
    second credential would be asking them to remember a password for a tab
    they never deliberately opened."""
    staff = pages["staff"]
    assert 'staff: "#/staff"' in staff          # the door is the queue itself
    assert "staff-signin" not in staff
    assert "VENDOR_COORDINATOR" in staff


def test_only_the_two_surfaces_without_another_system_ask_for_a_pin(pages: dict):
    """A person on a facility tablet has no other system to be signed in to,
    and a helper has no institutional identity at all. Those two authenticate
    here because there is nowhere else they could have."""
    for role in ("inside", "family"):
        assert "#/enroll" in pages[role], role
    assert 'if (role === "staff")' in pages["staff"]


def test_the_three_titles_are_not_confusable(pages: dict):
    import re

    titles = {role: re.search(r"<title>(.*?)</title>", html).group(1)
              for role, html in pages.items()}
    assert len(set(titles.values())) == 3, titles
    assert titles["staff"] == "Bridge for coordinators"


def test_the_teaching_screen_is_the_python_one(payload):
    from app.questions import teaching_for

    for answer in ("no", "some_idea", "yes"):
        built = payload["teaching"][answer]
        want = teaching_for(answer)
        assert built["headline"] == want["headline"]
        assert [p["title"] for p in built["points"]] == \
            [p["title"] for p in want["points"]]


def test_the_score_models_are_the_python_ones(payload):
    from app.scores import MODELS, summary_line

    built = payload["scores"]
    assert built["summary"] == summary_line()
    assert [m["name"] for m in built["models"]] == [m.name for m in MODELS]
    # The single most confusing fact in the subject, and the reason this screen
    # exists: auto and card scores are not on the 300 to 850 scale at all.
    ranges = {m["name"]: m["range"] for m in built["models"]}
    assert ranges["FICO Auto Score"] == "250 to 900"
    assert ranges["FICO Score 8"] == "300 to 850"


def test_the_tablet_build_cannot_reach_the_helper_routes(pages: dict):
    """All three builds share one shell, so the tablet file does contain the
    helper's source. What stops it is the role constant and the guard: APP is
    "inside", so guard("family") bounces every one of those routes back to the
    tablet's own door. That is the control, not the absence of the text."""
    inside = pages["inside"]
    assert 'const APP = "inside"' in inside
    assert 'if (!s || s.role !== role) { go(DOOR[APP]); return null; }' in inside
    # Reading is the tablet's own route, and it is the only one it has.
    assert "#/inside/report" in inside


def test_only_the_desk_scan_lands_confirmed(page: str):
    """Everything arriving from outside waits for a human, because these
    fields become a dispute letter."""
    assert 'function selfConfirming(source) { return source === "scan"; }' in page
    assert "const ready = confirmedReports(c);" in page
