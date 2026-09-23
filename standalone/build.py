"""Build the single-file, openable version of Bridge.

The product is a server app. This produces one HTML file that runs the same
product entirely in the browser: no install, no server, double-click to open,
and it works on a tablet from a USB stick or an email attachment.

Why generate it rather than hand-maintain it: the four triage states, their
paths, the verified facts and the bureau addresses come straight out of the
Python modules, so the file cannot quietly drift from the thing the tests
cover. Everything else, the screens and the flow, lives in shell.html.

    python3 standalone/build.py        ->  standalone/bridge.html
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def rules() -> dict:
    import sys

    sys.path.insert(0, str(ROOT))
    from app.bureaus import ANNUAL_REPORT_REQUEST, BUREAUS
    from app.letters import DISPUTE_TEMPLATE, REPORT_REQUEST_TEMPLATE
    from app.questions import INSIDE_QUESTIONS, STAFF_QUESTIONS
    from app.sources import FACTS, INTERVIEWS, OPEN_QUESTIONS
    from app.triage import PATH, STATE_LABEL, State

    def question(q):
        return {
            "index": getattr(q, "index", None),
            "field": q.field,
            "prompt": q.prompt,
            "helper": getattr(q, "helper", ""),
            "multi": getattr(q, "multi", False),
            "design_note": getattr(q, "design_note", ""),
            "constraint": getattr(q, "constraint", ""),
            "reassurance": getattr(q, "reassurance", None),
            "options": [
                {"value": o.value, "label": o.label, "note": getattr(o, "note", "")}
                for o in q.options
            ],
        }

    return {
        "built": date.today().isoformat(),
        "states": [
            {"key": s.value, "label": STATE_LABEL[s], **PATH[s]} for s in State
        ],
        "insideQuestions": [question(q) for q in INSIDE_QUESTIONS],
        "staffQuestions": [question(q) for q in STAFF_QUESTIONS],
        "facts": [
            {"source": f.source, "statement": f.statement, "url": f.url,
             "checked": f.checked_on.isoformat()}
            for f in FACTS.values()
        ],
        "open": list(OPEN_QUESTIONS),
        "interviews": [dict(i) for i in INTERVIEWS if isinstance(i, dict)],
        "bureaus": [
            {"name": b.name, "address": list(b.dispute_address),
             "note": b.note, "url": b.source_url}
            for b in BUREAUS
        ],
        "acr": {"name": ANNUAL_REPORT_REQUEST.name,
                "address": list(ANNUAL_REPORT_REQUEST.dispute_address)},
        "disputeTemplate": DISPUTE_TEMPLATE,
        "requestTemplate": REPORT_REQUEST_TEMPLATE,
    }


def build() -> Path:
    shell = (HERE / "shell.html").read_text()
    css = (ROOT / "app" / "static" / "bridge.css").read_text()
    icon = (ROOT / "app" / "static" / "icon-512.png").read_bytes()

    import base64

    payload = json.dumps(rules(), indent=1)
    out = (shell
           .replace("/*__BRIDGE_CSS__*/", css)
           .replace('"__BRIDGE_RULES__"', payload)
           .replace("__BRIDGE_ICON__",
                    "data:image/png;base64," + base64.b64encode(icon).decode()))

    target = HERE / "bridge.html"
    target.write_text(out)
    return target


if __name__ == "__main__":
    path = build()
    print(f"wrote {path} ({path.stat().st_size:,} bytes)")
