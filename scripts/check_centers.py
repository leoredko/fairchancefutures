#!/usr/bin/env python3
"""Read the city's Financial Empowerment Centers data and diff it against ours.

This is the whole of Bridge's relationship with that API. It runs here, on
somebody's terminal or on a schedule, and it prints. Nothing it fetches is
served to a person, and `app/centers.py` does not import it.

That is deliberate rather than lazy. NYC Open Data `dt2z-amuf` responds, and
its rows have not changed since November 2017. One of its five providers, The
Financial Clinic, now operates as Change Machine. Meanwhile the city stopped
publishing a location list on its own pages and routes people to 311 or the
booking portal instead, so there is no current official list to reconcile
against. The dataset is not a live feed running behind; it is an old snapshot
with a JSON endpoint and nothing checking it.

An address nobody has verified is more dangerous coming from a government API
than from a guess, because it arrives carrying the city's authority. So the
API's job here is to raise its hand when something changes, and a person's job
is to go look. That is the same division of labour as `app/sources.py`: the
registry holds what somebody read, and this says when to read again.

    python3 scripts/check_centers.py            # diff, and the freshness report
    python3 scripts/check_centers.py --json     # the rows, for eyeballing

Exit status is 1 when the diff finds something or an entry is past its window,
so a scheduled run can fail loudly instead of printing into a log nobody opens.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import centers, freshness  # noqa: E402

DATASET = "dt2z-amuf"
ROWS_URL = f"https://data.cityofnewyork.us/resource/{DATASET}.json?$limit=500"
META_URL = f"https://data.cityofnewyork.us/api/views/{DATASET}.json"
TIMEOUT = 30


def fetch(url: str) -> object:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.load(resp)


def rows_last_changed(meta: dict) -> str:
    """When the data itself last moved, which is not when the page did.

    The catalog's `updatedAt` ticks when anybody edits the description. Only
    `rowsUpdatedAt` says when a row changed, and that is the number that
    matters for whether an address is current.
    """
    import datetime

    stamp = meta.get("rowsUpdatedAt")
    if not stamp:
        return "unknown"
    return datetime.datetime.fromtimestamp(
        stamp, datetime.timezone.utc).date().isoformat()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true",
                    help="print the fetched rows instead of the diff")
    args = ap.parse_args()

    print("Freshness")
    print("---------")
    print(freshness.report())
    print()

    print(f"NYC Open Data {DATASET}")
    print("-" * (14 + len(DATASET)))
    try:
        rows = fetch(ROWS_URL)
        meta = fetch(META_URL)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        # Not reaching the city is not a finding about the data. Say which it
        # is, so a scheduled failure is not read as an address having changed.
        print(f"  Could not reach the dataset: {exc}")
        print("  This says nothing about whether our entries are right.")
        return 1

    if args.json:
        print(json.dumps(rows, indent=2)[:20000])
        return 0

    changed = rows_last_changed(meta)
    print(f"  rows: {len(rows)}")
    print(f"  rows last changed: {changed}")

    providers = sorted({r.get("provider", "") for r in rows if r.get("provider")})
    boroughs = sorted({r.get("borough", "") for r in rows if r.get("borough")})
    print(f"  providers: {', '.join(providers)}")
    print(f"  boroughs: {', '.join(boroughs)}")

    findings: list[str] = []

    nyc = next((c for c in centers.CENTERS if c.key == "nyc"), None)
    if nyc is None:
        findings.append("We no longer carry a NYC entry, but the city still "
                        "publishes this dataset.")
    else:
        ours = {b.casefold() for b in nyc.counties}
        # The dataset speaks in boroughs, our registry in counties, because a
        # county is what a release plan names. Map before comparing.
        borough_to_county = {
            "bronx": "bronx", "brooklyn": "kings", "manhattan": "new york",
            "queens": "queens", "staten island": "richmond",
        }
        theirs = {borough_to_county.get(b.casefold(), b.casefold())
                  for b in boroughs}
        missing = theirs - ours
        if missing:
            findings.append(f"The dataset covers counties we do not list: "
                            f"{', '.join(sorted(missing))}")

    if changed != "unknown":
        import datetime

        age = (datetime.date.today()
               - datetime.date.fromisoformat(changed)).days
        if age > freshness.ADDRESS_WINDOW.days:
            findings.append(
                f"The city's own rows are {age} days old, past the "
                f"{freshness.ADDRESS_WINDOW.days} day window. Treat every "
                f"address in it as unverified, including any that match ours.")

    print()
    if findings:
        print("Findings, for a person to look at:")
        for f in findings:
            print(f"  - {f}")
    else:
        print("No differences worth a person's time.")

    print()
    print("Nothing fetched here is served to anybody. app/centers.py is what "
          "reaches a screen.")

    return 1 if (findings or freshness.stale()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
