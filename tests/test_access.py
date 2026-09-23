"""Signing in.

The threat here is not a remote attacker. It is the next person to pick up the
tablet, and a person locking themselves out of their own case ten minutes
before a counselor visit. Both of those are what these test.
"""

import time
from datetime import datetime, timedelta, timezone

import pytest

from app.auth import (
    MAX_ATTEMPTS,
    AuthError,
    Account,
    Session,
    authenticate,
    check_pin_strength,
    enroll,
    hash_pin,
    read,
    reset_pin,
    verify_pin,
)
from app.identifiers import IdKind, InvalidIdentifier, parse

from tests.conftest import PIN, sign_in_helper, sign_in_inside, sign_in_staff


# --- identifiers -----------------------------------------------------------

@pytest.mark.parametrize("raw", ["28A1187", "28-A-1187", "28 a 1187", "28a1187"])
def test_a_din_is_read_however_it_is_typed(raw):
    """Somebody is copying this off a printed sheet onto a shared tablet."""
    parsed = parse(raw)
    assert parsed.kind is IdKind.DIN
    assert parsed.normalized == "28A1187"
    assert parsed.display == "28-A-1187"


@pytest.mark.parametrize("raw", ["00000011L", "04418823", "044-188-23 l"])
def test_a_nysid_is_accepted_with_or_without_the_check_letter(raw):
    """Which letters are valid is NOT confirmed, so we never reject on it.
    A real number refused at a kiosk is the worst outcome available here."""
    assert parse(raw).kind is IdKind.NYSID


def test_a_din_missing_its_letter_says_so_specifically():
    with pytest.raises(InvalidIdentifier) as caught:
        parse("221187")
    assert "facility letter" in str(caught.value)


def test_nonsense_gets_a_sentence_not_a_code():
    with pytest.raises(InvalidIdentifier) as caught:
        parse("hello there")
    assert "98-A-0004" in str(caught.value)


# --- PINs ------------------------------------------------------------------

def test_the_pin_is_never_stored_in_the_clear():
    stored = hash_pin("834712")
    assert "834712" not in stored
    assert stored.startswith("pbkdf2_sha256$")
    assert verify_pin("834712", stored)
    assert not verify_pin("834713", stored)


def test_two_people_with_the_same_pin_get_different_hashes():
    assert hash_pin("834712") != hash_pin("834712")


@pytest.mark.parametrize("weak", ["111111", "123456", "654321"])
def test_the_obvious_pins_are_refused(weak):
    with pytest.raises(AuthError):
        check_pin_strength(weak)


def test_a_pin_taken_from_your_own_number_is_refused():
    """Anyone holding the paperwork can read it."""
    with pytest.raises(AuthError) as caught:
        check_pin_strength("000001", identifier="00000011L")
    assert "your own number" in str(caught.value)


def test_a_reasonable_pin_is_accepted():
    check_pin_strength("834712", identifier="00000011L")


def test_enrolment_needs_the_two_entries_to_match():
    account = Account("a", "inside", "c", "28A1187")
    with pytest.raises(AuthError):
        enroll(account, "834712", "834713")
    assert not account.enrolled


# --- lockout ---------------------------------------------------------------

def _enrolled():
    account = Account("a", "inside", "c", "28A1187")
    enroll(account, PIN, PIN)
    return account


def test_wrong_pins_count_down_out_loud():
    """Telling somebody how many tries are left stops them locking themselves
    out of their own case by accident."""
    account = _enrolled()
    with pytest.raises(AuthError) as caught:
        authenticate(account, "000000")
    assert f"{MAX_ATTEMPTS - 1} tries left" in str(caught.value)


def test_enough_wrong_pins_locks_it():
    account = _enrolled()
    for _ in range(MAX_ATTEMPTS):
        with pytest.raises(AuthError):
            authenticate(account, "000000")
    assert account.locked_until is not None

    with pytest.raises(AuthError) as caught:
        authenticate(account, PIN)          # even the right one
    assert "Try again in about" in str(caught.value)


def test_a_lockout_lets_go_on_its_own():
    account = _enrolled()
    for _ in range(MAX_ATTEMPTS):
        with pytest.raises(AuthError):
            authenticate(account, "000000")
    account.locked_until = (
        datetime.now(timezone.utc) - timedelta(minutes=1)
    ).isoformat()
    authenticate(account, PIN)
    assert account.locked_until is None


def test_the_right_pin_clears_the_counter():
    account = _enrolled()
    with pytest.raises(AuthError):
        authenticate(account, "000000")
    authenticate(account, PIN)
    assert account.failed_attempts == 0


def test_a_counselor_clears_a_pin_but_never_sets_one():
    """If staff chose it, it would be something staff knows, which defeats it."""
    account = _enrolled()
    reset_pin(account)
    assert not account.enrolled
    assert account.pin_hash is None


# --- sessions --------------------------------------------------------------

def test_a_tampered_cookie_is_not_a_session(monkeypatch):
    monkeypatch.setenv("BRIDGE_SECRET", "test-secret-not-a-real-one")
    from app.auth import issue

    token = issue(Session("a", "inside", "marcus-w"))
    body, mac = token.rsplit(".", 1)
    assert read(token) is not None
    assert read(body + "." + mac[::-1]) is None
    assert read("garbage") is None
    assert read(None) is None


def test_a_session_that_sat_idle_is_gone(monkeypatch):
    """A shared tablet with somebody's case left open is the whole problem."""
    monkeypatch.setenv("BRIDGE_SECRET", "test-secret-not-a-real-one")
    from app.auth import IDLE_TIMEOUT, issue

    stale = Session("a", "inside", "marcus-w")
    stale.seen_at = time.time() - IDLE_TIMEOUT.total_seconds() - 5
    assert read(issue(stale)) is None


def test_staff_sessions_last_a_shift_and_kiosk_sessions_do_not():
    from app.auth import IDLE_TIMEOUT, STAFF_IDLE_TIMEOUT

    assert Session("a", "staff", "").idle_limit() == STAFF_IDLE_TIMEOUT
    assert Session("a", "inside", "c").idle_limit() == IDLE_TIMEOUT
    assert IDLE_TIMEOUT < STAFF_IDLE_TIMEOUT


# --- the doors, end to end -------------------------------------------------

@pytest.mark.parametrize("url,expect", [
    ("/inside", "Your number"),
    ("/inside/case", "Your number"),
    ("/family", "Your code"),
    ("/family/task", "Your code"),
    ("/staff", "Counselor sign in"),
])
def test_no_session_means_no_surface(client, url, expect):
    """Each door sends you to its own sign-in, not to a page that tells you
    which other doors exist."""
    assert expect in client.get(url).text


def test_the_url_no_longer_carries_identity(client):
    """Before this, /inside/marcus-w made you Marcus. Now there is nothing in
    the URL to guess at."""
    from app.routes.inside import router

    assert not any("{client_id}" in r.path for r in router.routes)


def test_a_client_signs_in_with_either_of_their_numbers(client):
    sign_in_inside(client, identifier="28A1187")
    assert "Marcus" in client.get("/inside/case").text
    client.get("/signout")

    # The NYSID reaches the same account, already enrolled, same PIN.
    sign_in_inside(client, identifier="00000011L")
    assert "Marcus" in client.get("/inside/case").text


def test_one_person_cannot_reach_another_persons_case(client):
    sign_in_inside(client, identifier="28A0931")       # J. Whitfield
    page = client.get("/inside/case").text
    assert "Whitfield" in page or "James" in page
    assert "Marcus" not in page


def test_a_helper_cannot_walk_into_the_staff_surface(client):
    sign_in_helper(client, code="BRIDGE-4417")
    landed = client.get("/staff")
    # Sent to their own door, not told that a staff surface exists.
    assert "Signed in as" not in landed.text
    assert "34 clients" not in landed.text


def test_signing_out_ends_it(client):
    sign_in_inside(client)
    assert client.get("/inside/case").status_code == 200
    client.get("/signout")
    assert "Your number" in client.get("/inside/case").text


def test_an_unknown_number_does_not_pretend_to_work(client):
    response = client.post("/signin", data={"identifier": "99Z9999"})
    assert response.status_code == 404
    assert "No record here" in response.text


def test_staff_get_their_own_door(client):
    sign_in_staff(client)
    assert "Needs you this week" in client.get("/staff").text


# --- the self-service range -------------------------------------------------

def test_any_28_number_opens_a_case_on_the_spot(client):
    """2028 has not happened, so a DIN starting 28 cannot be a real person.
    That makes it the safe range for anyone trying the app."""
    response = client.post("/signin", data={"identifier": "28Z4242"})
    assert response.status_code == 200
    assert "Pick a PIN" in response.text          # straight to enrolment

    import app.store as store
    assert store.find_account("inside", "28Z4242") is not None


def test_a_number_outside_that_range_still_needs_a_counselor(client):
    """Anything that could belong to a real person is never auto-created."""
    response = client.post("/signin", data={"identifier": "19Z4242"})
    assert response.status_code == 404
    assert "ask your counselor" in response.text

    import app.store as store
    assert store.find_account("inside", "19Z4242") is None


def test_a_self_opened_case_works_all_the_way_through(client):
    client.post("/signin", data={"identifier": "28Z4242"})
    client.post("/signin/enroll",
                data={"normalized": "28Z4242", "pin": PIN, "confirm": PIN})
    assert client.get("/inside/intake/1").status_code == 200
    client.post("/inside/intake/1", data={"has_bank_account": "no"})
    assert client.get("/inside/case").status_code == 200

    # And the counselor sees them in the queue like anybody else.
    sign_in_staff(client)
    assert "28-Z-4242" in client.get("/staff").text
