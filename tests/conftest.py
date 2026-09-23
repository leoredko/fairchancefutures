import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

PIN = "834712"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """A fresh app with its own data file, seeded from scratch."""
    import app.store as store

    monkeypatch.setattr(store, "DATA_PATH", tmp_path / "bridge.json")
    monkeypatch.setenv("BRIDGE_SECRET", "test-secret-not-a-real-one")
    from starlette.testclient import TestClient

    from app.main import app as fastapi_app

    with TestClient(fastapi_app) as c:
        yield c


def _door(client, identify_url, identify_field, value, key, pin):
    """What a person actually does: identify, then either set a PIN or enter it.

    Enrolling twice is not a thing a real person can do, so this mirrors the
    app rather than assuming the account is always fresh.
    """
    client.post(identify_url, data={identify_field: value})
    enrolled = client.post(f"{identify_url}/enroll",
                           data={"normalized": key, "pin": pin, "confirm": pin},
                           follow_redirects=False)
    if enrolled.status_code != 303:
        client.post(f"{identify_url}/pin", data={"normalized": key, "pin": pin},
                    follow_redirects=False)
    return client


def sign_in_inside(client, identifier="28A1187", pin=PIN):
    return _door(client, "/signin", "identifier", identifier, _norm(identifier), pin)


def sign_in_helper(client, code="BRIDGE-4417", pin=PIN):
    return _door(client, "/helper", "code", code, code, pin)


def sign_in_staff(client, staff_id="REYES", pin=PIN):
    return _door(client, "/staff-signin", "staff_id", staff_id, staff_id, pin)


def _norm(raw):
    from app.identifiers import parse

    return parse(raw).normalized


@pytest.fixture()
def inside(client):
    return sign_in_inside(client)


@pytest.fixture()
def helper(client):
    return sign_in_helper(client)


@pytest.fixture()
def staff(client):
    return sign_in_staff(client)
