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
    from app import facilities as facilities_module
    from app.bureaus import ANNUAL_REPORT_REQUEST, BUREAUS
    from app.letters import DISPUTE_TEMPLATE, REPORT_REQUEST_TEMPLATE
    from app.paths import PATHS
    from app.questions import INSIDE_QUESTIONS, STAFF_QUESTIONS, teaching_for
    from app.report import LINE_FORMAT, SCANNER_NOTE
    from app.lessons import CURRICULUM, TOTAL_MINUTES
    from app.scores import EXPLAINERS, MODELS, USE_LABEL, summary_line
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
        "paths": [
            {"key": p.key, "label": p.label, "blurb": p.blurb,
             "cta": p.cta, "queueLabel": p.queue_label} for p in PATHS
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
        # Written from the answer to "do you know how to find out". Somebody
        # who said yes does not need the long version read to them.
        "teaching": {answer: teaching_for(answer)
                     for answer in ("no", "some_idea", "yes")},
        "scores": {
            "summary": summary_line(),
            "models": [
                {"name": m.name, "use": USE_LABEL[m.use], "range": m.range_label,
                 "note": m.note}
                for m in MODELS
            ],
            "explainers": [dict(e) for e in EXPLAINERS],
        },
        # The credit course, generated rather than retyped, so the single
        # file cannot drift from the tested one. A card's citation is resolved
        # here rather than in the browser: the shell should never have to know
        # what a fact key is.
        "lessons": [
            {
                "slug": l.slug,
                "title": l.title,
                "minutes": l.minutes,
                "hook": l.hook,
                "urgentFor": list(l.urgent_for),
                "cards": [
                    {"title": c.title, "body": c.body, "aside": c.aside,
                     "cited": c.cited, "url": c.source_url}
                    for c in l.cards
                ],
                "check": {
                    "prompt": l.check.prompt,
                    "choices": [{"value": ch.value, "label": ch.label}
                                for ch in l.check.choices],
                    "answer": l.check.answer,
                    "why": l.check.why,
                },
            }
            for l in CURRICULUM
        ],
        "courseMinutes": TOTAL_MINUTES,
        "scan": {"lineFormat": LINE_FORMAT, "note": SCANNER_NOTE},
        # The DOCCS facility list, generated rather than retyped, so the
        # single file cannot offer a facility the tested build rejects. Each
        # entry carries the population it holds, because the picker groups by
        # it: that grouping is what stops a man being recorded at a facility
        # for women, which is the bug this list was written for.
        "facilities": [
            {"name": f.name, "serves": f.serves, "level": f.level}
            for f in facilities_module.FACILITIES
        ],
    }


# One file per surface. A tablet gets the tablet app and a helper gets the
# helper app, the way they would be deployed separately in the real thing.
# All three read the same storage key, so served from one folder or one host
# they share a caseload; published to three different origins they do not.
APPS = {
    "inside": "Bridge for the tablet",
    "family": "Bridge for helpers",
    "staff": "Bridge for coordinators",
}


def build() -> list[Path]:
    import base64

    shell = (HERE / "shell.html").read_text()
    css = (ROOT / "app" / "static" / "bridge.css").read_text()
    icon = base64.b64encode(
        (ROOT / "app" / "static" / "icon-512.png").read_bytes()).decode()
    payload = json.dumps(rules(), indent=1)

    written = []
    for role, title in APPS.items():
        out = (shell
               .replace("/*__BRIDGE_CSS__*/", css)
               .replace('"__BRIDGE_RULES__"', payload)
               .replace('"__BRIDGE_ROLE__"', json.dumps(role))
               .replace("<title>Bridge</title>", f"<title>{title}</title>")
               .replace("__BRIDGE_ICON__", "data:image/png;base64," + icon))
        target = HERE / f"bridge-{role}.html"
        target.write_text(out)
        written.append(target)
    return written


if __name__ == "__main__":
    for path in build():
        print(f"wrote {path.name} ({path.stat().st_size:,} bytes)")
