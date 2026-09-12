# Tab Wrangler

A local Chrome extension that keeps a runaway tab strip under control. Everything
runs in your browser: no server, no API key, no data leaves the machine.

## Install (30 seconds)

1. `chrome://extensions`
2. Toggle **Developer mode** on, top right.
3. **Load unpacked**, pick this `tab-wrangler/` folder.
4. Pin the icon. The badge shows how many actions are waiting on your review.

## What it does

Every sweep (default: 5 minutes) it looks at every tab and plans four kinds of action.
Each one is independently set to **Off**, **Ask me**, or **Automatic** in Settings.

| Action | What happens | Reversible? |
| --- | --- | --- |
| **Close duplicates** | Same URL open twice, keeps the copy you touched last. Fragments and `utm_*` junk are ignored when comparing. | The surviving copy is still open |
| **Unload cold tabs** | Untouched 30 min+ gets dropped from memory. Tab stays in the strip and reloads on click. | Fully, by clicking it |
| **Archive stale tabs** | Untouched 72 h+ gets saved to a searchable archive, then closed. | Yes, from the Archive tab |
| **Group by domain** | 3+ ungrouped tabs on one domain get a collapsed, colored tab group. | Yes, ungroup normally |

Defaults are deliberately timid: unloading is automatic (nothing is lost), everything
else asks first. Once you trust it, flip archive to Automatic and stop thinking about tabs.

### Never touched, ever

Pinned tabs, the active tab in each window, anything playing audio, `chrome://` pages,
and any URL matching your protected patterns (`localhost`, Gmail and Calendar by default).

## The sensor layer

Every sweep also logs a row: tab count, window count, how many are discarded, how many
are audible. **Export data (JSON)** in Settings dumps those samples plus your archive and
stats. That file is the interesting part: a few weeks of it tells you what your tab habits
actually are, rather than what you assume they are. It is also the training/eval material
if you later want an LLM layer that groups tabs by *project* instead of by domain.

## Architecture

```
core.js        pure planning logic, zero chrome.* calls  <- all the decisions live here
background.js  service worker: alarms, tab events, storage, applying plans
popup.js/html  review queue, archive search, settings
tests/         node --test over core.js
```

`core.js` deciding and `background.js` acting are kept apart on purpose: the rules are
testable without a browser, and a future LLM-backed planner can be swapped in behind the
same `plan()` signature.

Run the tests:

```bash
npm test
```

## Known limits

- Tab ids do not survive a browser restart. Chrome 121+ exposes `tab.lastAccessed`, which
  does, and that is the primary age signal; the in-session activity map is the fallback.
  A tab whose age cannot be determined is treated as fresh and is never acted on.
- Tab groups cannot span windows, so grouping is planned per window.
- Archive is capped at 2000 entries, samples at 5000, oldest dropped first.
