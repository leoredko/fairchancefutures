const send = (msg) => chrome.runtime.sendMessage(msg);
const $ = (sel) => document.querySelector(sel);
const el = (tag, props = {}, kids = []) => {
  const n = Object.assign(document.createElement(tag), props);
  kids.forEach((k) => n.append(k));
  return n;
};

const ACTION_LABELS = {
  dedupe: 'Close duplicates',
  discard: 'Unload cold tabs',
  archive: 'Archive stale tabs',
  group: 'Group by domain'
};

let state = null;

function ago(ts) {
  if (!ts) return 'never';
  const m = Math.round((Date.now() - ts) / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.round(m / 60);
  return h < 48 ? `${h}h ago` : `${Math.round(h / 24)}d ago`;
}

async function refresh() {
  state = await send({ type: 'getState' });
  $('#status').textContent =
    `${state.tabCount} tabs open | swept ${ago(state.lastSweepAt)} | ${state.sampleCount} samples logged`;
  renderProposals();
  renderArchive();
  renderSettings();
}

function renderProposals() {
  const box = $('#proposals');
  box.textContent = '';
  const list = state.proposals || [];
  $('#applyAll').hidden = list.length < 2;
  if (!list.length) {
    box.append(el('p', { className: 'empty', textContent: 'Nothing to review. Tabs are behaving.' }));
    return;
  }
  for (const p of list) {
    const apply = el('button', { className: 'primary', textContent: 'Apply' });
    apply.onclick = async () => { await send({ type: 'apply', id: p.id }); refresh(); };
    const skip = el('button', { className: 'ghost', textContent: 'Dismiss' });
    skip.onclick = async () => { await send({ type: 'dismiss', id: p.id }); refresh(); };
    box.append(el('div', { className: 'card' }, [
      el('span', { className: 'kind', textContent: p.kind }),
      el('h2', { textContent: p.title }),
      el('p', { textContent: p.detail, title: p.items.map((i) => i.url).join('\n') }),
      el('div', { className: 'acts' }, [apply, skip])
    ]));
  }
}

function renderArchive() {
  const box = $('#archiveList');
  const q = $('#search').value.trim().toLowerCase();
  box.textContent = '';
  const rows = (state.archive || []).filter(
    (a) => !q || `${a.title} ${a.url}`.toLowerCase().includes(q)
  );
  if (!rows.length) {
    box.append(el('p', { className: 'empty', textContent: 'Archive is empty.' }));
    return;
  }
  for (const a of rows) {
    const open = el('button', { className: 'ghost', textContent: 'Open' });
    open.onclick = () => send({ type: 'restore', url: a.url });
    box.append(el('div', { className: 'arc' }, [
      el('div', {}, [
        el('a', { href: a.url, target: '_blank', textContent: a.title || a.url, title: a.url }),
        el('small', { textContent: ago(a.archivedAt) })
      ]),
      open
    ]));
  }
}

function renderSettings() {
  const s = state.settings;
  const box = $('#actionSettings');
  box.textContent = '';
  for (const [key, label] of Object.entries(ACTION_LABELS)) {
    const sel = el('select', { id: `mode-${key}` });
    for (const [val, text] of [['off', 'Off'], ['propose', 'Ask me'], ['auto', 'Automatic']]) {
      sel.append(el('option', { value: val, textContent: text, selected: s.actions[key] === val }));
    }
    box.append(el('label', { className: 'row' }, [el('span', { textContent: label }), sel]));
  }
  $('#sweepMinutes').value = s.sweepMinutes;
  $('#discardAfterMinutes').value = s.discardAfterMinutes;
  $('#archiveAfterHours').value = s.archiveAfterHours;
  $('#minGroupSize').value = s.minGroupSize;
  $('#protectedPatterns').value = (s.protectedPatterns || []).join('\n');

  const st = state.stats || {};
  $('#stats').textContent = [
    `Duplicates closed: ${st.duplicatesClosed || 0}`,
    `Tabs unloaded: ${st.tabsDiscarded || 0}`,
    `Tabs archived: ${st.tabsArchived || 0}  (${state.archiveCount} kept)`,
    `Tabs grouped: ${st.tabsGrouped || 0}`
  ].join('\n');
}

// --- events ---

document.querySelectorAll('nav.tabs button').forEach((btn) => {
  btn.onclick = () => {
    document.querySelectorAll('nav.tabs button').forEach((b) => b.classList.toggle('active', b === btn));
    document.querySelectorAll('.view').forEach((v) => { v.hidden = v.id !== btn.dataset.view; });
  };
});

$('#sweep').onclick = async () => { await send({ type: 'sweepNow' }); refresh(); };
$('#applyAll').onclick = async () => { await send({ type: 'apply', id: 'all' }); refresh(); };
$('#search').oninput = renderArchive;
$('#clearArchive').onclick = async () => { await send({ type: 'clearArchive' }); refresh(); };

$('#save').onclick = async () => {
  const settings = {
    ...state.settings,
    sweepMinutes: +$('#sweepMinutes').value,
    discardAfterMinutes: +$('#discardAfterMinutes').value,
    archiveAfterHours: +$('#archiveAfterHours').value,
    minGroupSize: +$('#minGroupSize').value,
    protectedPatterns: $('#protectedPatterns').value.split('\n').map((s) => s.trim()).filter(Boolean),
    actions: Object.fromEntries(
      Object.keys(ACTION_LABELS).map((k) => [k, $(`#mode-${k}`).value])
    )
  };
  await send({ type: 'saveSettings', settings });
  await send({ type: 'sweepNow' });
  refresh();
};

$('#export').onclick = async () => {
  const data = await send({ type: 'exportData' });
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
  const a = el('a', { href: url, download: `tab-wrangler-${new Date().toISOString().slice(0, 10)}.json` });
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
};

refresh();
