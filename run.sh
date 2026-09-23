#!/usr/bin/env bash
set -euo pipefail
python3 -m pip install -q -r requirements.txt
python3 -m pytest -q
exec python3 -m uvicorn app.main:app --reload --port 8000
