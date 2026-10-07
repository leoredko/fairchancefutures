"""Adding somebody to the caseload.

A counselor types this while the person is sitting across from them, so the
validation has to catch the mistakes that get made in that situation and say
something useful rather than "invalid input".
"""

from datetime import date, timedelta

import pytest

from app.intake import IntakeProblem, _clean_name, client_id_for, helper_code, validate

from tests.conftest import sign_in_staff


def ok(**over):
    args = dict(
        display_name="Andre Quinones",
        din="28E0114",
        nysid="",
        facility="Green Haven Correctional Facility",
        release_date=(date.today() + timedelta(days=120)).isoformat(),
    )
    args.update(over)
    return validate(**args)


# --- names ------------------------------------------------------------------

@pytest.mark.parametrize("raw,want", [
    ("andre  QUINONES", "Andre Quinones"),
    ("MARIA ALVAREZ", "Maria Alvarez"),
    ("marcus w.", "Marcus W."),
    ("daniel marsh iii", "Daniel Marsh III"),
    ("tom o'brien sr", "Tom O'Brien Sr."),
    ("SEAN MCDONALD", "Sean McDonald"),
    ("ana macgregor", "Ana MacGregor"),
])
def test_a_name_typed_in_a_hurry_comes_out_right(raw, want):
    """Roman numerals shout, suffixes do not, and O'Brien keeps both capitals.
    Getting somebody's own name wrong on their own screen is a small
    disrespect people notice."""
    assert _clean_name(raw) == want


def test_a_blank_name_is_refused():
    with pytest.raises(IntakeProblem) as caught:
        ok(display_name="  ")
    assert caught.value.field == "display_name"


# --- identifiers ------------------------------------------------------------

def test_either_identifier_is_enough():
    """A counselor often has only one of the two in front of them."""
    assert ok(din="28E0114", nysid="").din == "28E0114"
    assert ok(din="", nysid="00000099L").nysid == "00000099L"


def test_neither_identifier_is_not_enough():
    with pytest.raises(IntakeProblem) as caught:
        ok(din="", nysid="")
    assert "DIN, a NYSID, or both" in str(caught.value)


def test_the_numbers_in_the_wrong_boxes_say_which_box():
    with pytest.raises(IntakeProblem) as caught:
        ok(din="00000099L")
    assert "NYSID box" in str(caught.value)

    with pytest.raises(IntakeProblem) as caught:
        ok(din="", nysid="28E0114")
    assert "DIN box" in str(caught.value)


def test_a_duplicate_is_caught_before_it_is_created():
    with pytest.raises(IntakeProblem) as caught:
        ok(known_dins={"28E0114"})
    assert "already on the caseload" in str(caught.value)


def test_the_din_is_normalized_however_it_is_typed():
    assert ok(din="28-e-0114").din == "28E0114"


# --- the other fields -------------------------------------------------------

def test_the_facility_is_required_and_says_why():
    """It goes on the envelope, and the bureaus ask for it on prison mail."""
    with pytest.raises(IntakeProblem) as caught:
        ok(facility="")
    assert "envelope" in str(caught.value)


def test_a_release_date_far_in_the_past_is_probably_a_typo():
    with pytest.raises(IntakeProblem) as caught:
        ok(release_date="1998-04-02")
    assert "Check the year" in str(caught.value)


def test_a_release_date_already_passed_is_fine():
    """People come home and stay on the caseload."""
    assert ok(release_date=(date.today() - timedelta(days=40)).isoformat())


# --- ids and codes ----------------------------------------------------------

def test_helper_codes_do_not_collide():
    taken = {helper_code() for _ in range(50)}
    assert helper_code(taken) not in taken


def test_two_people_with_the_same_name_get_different_ids():
    first = client_id_for("Andre Quinones", "28E0114", set())
    second = client_id_for("Andre Quinones", "28F0220", {first})
    assert first != second


# --- through the app --------------------------------------------------------

def test_a_counselor_adds_somebody_and_they_can_sign_in(client):
    staff = sign_in_staff(client)
    assert staff.get("/staff/new").status_code == 200

    staff.post("/staff/new", data={
        "display_name": "andre quinones",
        "din": "28-E-0114",
        "nysid": "",
        "facility": "Green Haven Correctional Facility",
        "release_date": (date.today() + timedelta(days=120)).isoformat(),
    })

    import app.store as store
    created = [c for c in store.STATE.clients.values() if c.din == "28E0114"]
    assert len(created) == 1
    assert created[0].display_name == "Andre Quinones"

    # The sign-in exists and has no PIN, so the person sets their own.
    account = store.find_account("inside", "28E0114")
    assert account is not None
    assert not account.enrolled

    # And a helper code was issued for the letter going out.
    codes = [a for a in store.STATE.accounts.values()
             if a["role"] == "family" and a["subject_id"] == created[0].id]
    assert len(codes) == 1
    assert codes[0]["login_key"].startswith("BRIDGE-")


def test_a_counselor_never_sets_the_clients_pin(client):
    """A PIN somebody else chose is not a PIN."""
    staff = sign_in_staff(client)
    staff.post("/staff/new", data={
        "display_name": "Andre Quinones", "din": "28E0114", "nysid": "",
        "facility": "Green Haven Correctional Facility",
        "release_date": (date.today() + timedelta(days=90)).isoformat(),
    })
    import app.store as store
    for account in store.STATE.accounts.values():
        if account["subject_id"] and account["subject_id"].startswith("andre"):
            assert account["pin_hash"] is None


def test_a_bad_intake_comes_back_with_the_field_marked(client):
    staff = sign_in_staff(client)
    response = staff.post("/staff/new", data={
        "display_name": "Andre Quinones", "din": "nonsense", "nysid": "",
        "facility": "Green Haven Correctional Facility",
        "release_date": (date.today() + timedelta(days=90)).isoformat(),
    })
    assert response.status_code == 400
    assert "98-A-0004" in response.text          # the message explains the shape
    assert 'value="Andre Quinones"' in response.text   # and keeps what was typed


def test_the_queue_links_to_the_intake_screen(client):
    """A coordinator can add somebody by hand from the caseload queue."""
    assert "/staff/new" in sign_in_staff(client).get("/staff").text
