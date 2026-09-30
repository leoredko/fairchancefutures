"""Claims about the pages themselves that no single route owns.

These began life in the tests for the single-file demo build, which is gone. The
claims outlived it, because each is about the product and not about that file,
so they are defended here against the pages the server actually sends.
"""

import re

from tests.conftest import sign_in_inside

EXTERNAL = re.compile(r"^(?:https?:)?//", re.I)


def _requests_off_the_app(html: str) -> list[str]:
    """Anything the browser would fetch on its own to draw the page.

    Anchors are not in this list: a link to a statute is wanted and only loads
    if somebody follows it. A script, stylesheet, image or frame is fetched
    without being asked.
    """
    found = []
    for tag in re.findall(r"<(?:script|link|img|iframe|source|video|audio)\b[^>]*>", html):
        for attr in re.findall(r'\b(?:src|href|srcset)="([^"]+)"', tag):
            if EXTERNAL.match(attr):
                found.append(tag)
    return found


def test_the_pages_load_nothing_from_anywhere_but_this_app(client):
    """The tablet is metered by the minute and sits behind a facility network.
    One remote font or script and a screen either fails to draw or spends a
    person's minutes on something they never asked for."""
    sign_in_inside(client)
    urls = ["/", "/signin", "/helper", "/display", "/citations", "/roles",
            "/inside/start", "/inside/learn", "/inside/learn/lesson/three-papers/0",
            "/inside/case", "/inside/request", "/inside/report", "/inside/after",
            "/staff", "/staff/new", "/staff/marcus-w"]
    checked = 0
    for url in urls:
        response = client.get(url)
        if response.status_code != 200:
            continue
        checked += 1
        assert _requests_off_the_app(response.text) == [], url
    assert checked >= 12, "too few pages were reachable to say anything"


def test_the_landing_page_says_it_is_not_a_state_system(client):
    """The one piece of small print that stays. It handles prison identifiers,
    so it says plainly that it is not affiliated with the state's corrections
    department."""
    page = client.get("/").text
    assert "not affiliated with" in page.lower()
    assert "Department of Corrections" in page


def test_the_facility_is_picked_from_a_list_and_never_typed(client, staff):
    """A box that accepts anything typed into it becomes the return address on a
    dispute letter. What is offered is the list in app/facilities.py."""
    page = client.get("/staff/new").text
    assert re.search(r'<select[^>]*name="facility"', page)
    assert not re.search(r'<input[^>]*name="facility"', page)
    assert "Downstate Correctional Facility" not in page
