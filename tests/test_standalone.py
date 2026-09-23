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
BUILT = ROOT / "standalone" / "bridge.html"


@pytest.fixture(scope="module")
def page() -> str:
    if not BUILT.exists():
        import subprocess, sys

        subprocess.run([sys.executable, "standalone/build.py"], cwd=ROOT, check=True)
    return BUILT.read_text()


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


def test_it_says_what_it_is(page: str):
    """It must not read as an official system. It names itself a prototype and
    disclaims any affiliation, on the first screen."""
    assert "prototype" in page
    assert "Not affiliated with" in page
    assert "made\n      up." in page or "made up" in page


def test_it_stays_small_enough_to_email(page: str):
    assert len(page.encode()) < 2_000_000
