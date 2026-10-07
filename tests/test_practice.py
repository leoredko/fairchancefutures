"""Practice links for a room, kept apart from the product.

Three links, one per surface, each opening on the visitor's own practice case.
The real routes know nothing about them: delete app/routes/practice.py and its
line in app/main.py and everything here goes with it, and the product is
unchanged.
"""

import re
from urllib.parse import parse_qs, urlparse

from app.identifiers import parse
from app.store import STATE
from tests.conftest import PIN

BOX = re.compile(r'name="identifier"[^>]*value="([^"]*)"')
HELPER_BOX = re.compile(r'name="code"[^>]*value="([^"]*)"')


def target(response):
    assert response.status_code == 303, response.status_code
    return urlparse(response.headers["location"])


def number_from(response):
    return parse_qs(target(response).query)["identifier"][0]


def test_the_tablet_link_sends_you_to_the_sign_in_with_a_fresh_28_number(client):
    r = client.get("/try/tablet", follow_redirects=False)
    assert target(r).path == "/signin"
    assert parse(number_from(r)).normalized.startswith("28")


def test_the_number_arrives_in_the_box_on_the_real_sign_in(client):
    r = client.get("/try/tablet", follow_redirects=False)
    page = client.get(r.headers["location"]).text
    assert f'value="{number_from(r)}"' in page


def test_a_case_made_this_way_has_three_confirmed_reports_ready_to_read(client):
    r = client.get("/try/tablet", follow_redirects=False)
    key = parse(number_from(r)).normalized
    reports = STATE.reports[f"din-{key.lower()}"]
    assert sorted(x["bureau"] for x in reports) == ["Equifax", "Experian", "TransUnion"]
    assert all(x["confirmed"] for x in reports)
    client.post("/signin", data={"identifier": number_from(r)})
    client.post("/signin/enroll", data={"normalized": key, "pin": PIN, "confirm": PIN})
    assert client.get("/inside/report").status_code == 200


def test_a_reload_keeps_the_same_number_for_the_same_visitor(client):
    first = number_from(client.get("/try/tablet", follow_redirects=False))
    again = {number_from(client.get("/try/tablet", follow_redirects=False)) for _ in range(5)}
    assert again == {first}


def test_two_visitors_are_not_handed_the_same_number(client):
    seen = set()
    for _ in range(25):
        client.cookies.clear()                    # a new visitor, not a reload
        seen.add(number_from(client.get("/try/tablet", follow_redirects=False)))
    assert len(seen) > 20


def test_the_phone_link_opens_on_a_helper_code_for_the_visitors_own_case(client):
    number = number_from(client.get("/try/tablet", follow_redirects=False))
    r = client.get("/try/phone", follow_redirects=False)
    assert target(r).path == "/helper"
    code = parse_qs(target(r).query)["code"][0]
    assert code.startswith("BRIDGE-")
    family = [a for a in STATE.accounts.values()
              if a["role"] == "family" and a["login_key"] == code][0]
    assert family["subject_id"] == f"din-{parse(number).normalized.lower()}"
    assert f'value="{code}"' in client.get(r.headers["location"]).text


def test_the_helper_can_sign_in_with_that_code_and_the_page_names_somebody(client):
    r = client.get("/try/phone", follow_redirects=False)
    code = parse_qs(target(r).query)["code"][0]
    client.post("/helper", data={"code": code})
    done = client.post("/helper/enroll", follow_redirects=True,
                       data={"normalized": code, "pin": PIN, "confirm": PIN})
    assert done.status_code == 200
    assert "Sam asked you to help" in done.text


def test_the_desk_link_opens_that_visitors_own_case(client):
    number = number_from(client.get("/try/tablet", follow_redirects=False))
    r = client.get("/try/desk", follow_redirects=False)
    assert target(r).path == f"/staff/din-{parse(number).normalized.lower()}"
    assert client.get(r.headers["location"]).status_code == 200


def test_all_three_links_are_one_case_whatever_order_they_are_opened_in(client):
    before = {c for c in STATE.clients if c.startswith("din-")}
    client.get("/try/desk", follow_redirects=False)
    client.get("/try/phone", follow_redirects=False)
    tablet = client.get("/try/tablet", follow_redirects=False)
    made = {c for c in STATE.clients if c.startswith("din-")} - before
    assert made == {f"din-{parse(number_from(tablet)).normalized.lower()}"}


# --- the real routes are the real product -----------------------------------

def test_the_real_sign_in_arrives_empty_and_the_real_helper_door_asks_for_a_code(client):
    assert BOX.search(client.get("/signin").text).group(1) == ""
    assert HELPER_BOX.search(client.get("/helper").text).group(1) == ""


def test_a_case_opened_the_normal_way_starts_with_no_reports(client):
    key = "28Z0001"
    client.post("/signin", data={"identifier": key})
    assert not STATE.reports.get(f"din-{key.lower()}")


def test_a_code_in_the_link_fills_the_helper_box_and_nothing_else(client):
    page = client.get("/helper?code=BRIDGE-3306").text
    assert 'value="BRIDGE-3306"' in page
    assert "pin" not in HELPER_BOX.search(page).group(0).lower()
