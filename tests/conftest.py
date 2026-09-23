import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """A fresh app with its own data file, seeded from scratch."""
    import app.store as store

    monkeypatch.setattr(store, "DATA_PATH", tmp_path / "bridge.json")
    from starlette.testclient import TestClient

    from app.main import app as fastapi_app

    with TestClient(fastapi_app) as c:
        yield c
