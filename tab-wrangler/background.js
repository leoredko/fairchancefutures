import { DEFAULT_SETTINGS, plan, colorFor } from './core.js';

const ALARM = 'tab-wrangler-sweep';
const MAX_ARCHIVE = 2000;
const MAX_SAMPLES = 5000;

// ---------- storage helpers ----------

async function getSettings() {
  const { settings } = await chrome.storage.local.get('settings');
  return {
    ...DEFAULT_SETTINGS,
    ...(settings || {}),
    actions: { ...DEFAULT_SETTINGS.actions, ...((settings || {}).actions || {}) }
  };
}

async function getActivity() {
  const { activity } = await chrome.storage.session.get('activity');
  return activity || {};
}

async function touch(tabId) {
  const activity = await getActivity();
  activity[String(tabId)] = Date.now();
  await chrome.storage.session.set({ activity });
}

async function forget(tabId) {
  const activity = await getActivity();
  delete activity[String(tabId)];
  await chrome.storage.session.set({ activity });
}

// ---------- sensor layer ----------

/** One row per sweep: the raw material for figuring out what your tab habits actually are. */
async function recordSample(tabs) {
  const { samples = [] } = await chrome.storage.local.get('samples');
  const windows = new Set(tabs.map((t) => t.windowId));
  samples.push({
    t: Date.now(),
    tabs: tabs.length,
    windows: windows.size,
    discarded: tabs.filter((t) => t.discarded).length,
    audible: tabs.filter((t) => t.audible).length
  });
  await chrome.storage.local.set({ samples: samples.slice(-MAX_SAMPLES) });
}

async function bumpStats(patch) {
  const { stats = {} } = await chrome.storage.local.get('stats');
  for (const [k, v] of Object.entries(patch)) stats[k] = (stats[k] || 0) + v;
  stats.lastSweepAt = Date.now();
  await chrome.storage.local.set({ stats });
}

// ---------- actions ----------

async function archiveTabs(items) {
  const { archive = [] } = await chrome.storage.local.get('archive');
  const now = Date.now();
  for (const it of items) archive.unshift({ url: it.url, title: it.title, archivedAt: now });
  await chrome.storage.local.set({ archive: archive.slice(0, MAX_ARCHIVE) });
}

async function safeRemove(tabIds) {
  // Tabs vanish between planning and applying all the time. Remove one at a
  // time so a single stale id does not sink the whole batch.
  let closed = 0;
  for (const id of tabIds) {
    try {
      await chrome.tabs.remove(id);
      closed++;
    } catch { /* tab already gone */ }
  }
  return closed;
}

async function applyProposal(p) {
  if (p.kind === 'dedupe') {
    const n = await safeRemove(p.tabIds);
    await bumpStats({ duplicatesClosed: n });
    return n;
  }
  if (p.kind === 'archive') {
    await archiveTabs(p.items);
    const n = await safeRemove(p.tabIds);
    await bumpStats({ tabsArchived: n });
    return n;
  }
  if (p.kind === 'discard') {
    let n = 0;
    for (const id of p.tabIds) {
      try {
        await chrome.tabs.discard(id);
        n++;
      } catch { /* active, already discarded, or gone */ }
    }
    await bumpStats({ tabsDiscarded: n });
    return n;
  }
  if (p.kind === 'group') {
    try {
      const groupId = await chrome.tabs.group({ tabIds: p.tabIds });
      await chrome.tabGroups.update(groupId, {
        title: p.groupTitle,
        color: colorFor(p.groupTitle),
        collapsed: true
      });
      await bumpStats({ tabsGrouped: p.tabIds.length });
      return p.tabIds.length;
    } catch {
      return 0;
    }
  }
  return 0;
}

// ---------- the sweep ----------

async function setBadge(pending) {
  await chrome.action.setBadgeText({ text: pending ? String(pending) : '' });
  await chrome.action.setBadgeBackgroundColor({ color: '#c2410c' });
}

async function sweep() {
  const settings = await getSettings();
  const tabs = await chrome.tabs.query({});
  const activity = await getActivity();
  await recordSample(tabs);

  const proposals = plan(tabs, activity, settings, Date.now());
  const pending = [];
  for (const p of proposals) {
    if (p.mode === 'auto') await applyProposal(p);
    else pending.push(p);
  }
  await chrome.storage.local.set({ proposals: pending, lastSweepAt: Date.now() });
  await setBadge(pending.length);
  return pending;
}

// ---------- wiring ----------

async function ensureAlarm() {
  const settings = await getSettings();
  await chrome.alarms.create(ALARM, { periodInMinutes: Math.max(1, settings.sweepMinutes) });
}

chrome.runtime.onInstalled.addListener(async () => {
  const { settings } = await chrome.storage.local.get('settings');
  if (!settings) await chrome.storage.local.set({ settings: DEFAULT_SETTINGS });
  await ensureAlarm();
  await sweep();
});

chrome.runtime.onStartup.addListener(async () => {
  await ensureAlarm();
  await sweep();
});

chrome.alarms.onAlarm.addListener((a) => {
  if (a.name === ALARM) sweep();
});

chrome.tabs.onActivated.addListener(({ tabId }) => touch(tabId));
chrome.tabs.onCreated.addListener((tab) => touch(tab.id));
chrome.tabs.onUpdated.addListener((tabId, info) => {
  // Only a real navigation counts as attention. Favicon and title churn on a
  // background tab does not mean you looked at it.
  if (info.status === 'loading' && info.url) touch(tabId);
});
chrome.tabs.onRemoved.addListener((tabId) => forget(tabId));

chrome.runtime.onMessage.addListener((msg, _sender, respond) => {
  (async () => {
    switch (msg.type) {
      case 'getState': {
        const data = await chrome.storage.local.get([
          'proposals', 'archive', 'stats', 'settings', 'samples', 'lastSweepAt'
        ]);
        const tabs = await chrome.tabs.query({});
        respond({
          proposals: data.proposals || [],
          archive: (data.archive || []).slice(0, 100),
          archiveCount: (data.archive || []).length,
          stats: data.stats || {},
          settings: await getSettings(),
          sampleCount: (data.samples || []).length,
          lastSweepAt: data.lastSweepAt || 0,
          tabCount: tabs.length
        });
        break;
      }
      case 'sweepNow':
        respond({ proposals: await sweep() });
        break;
      case 'apply': {
        const { proposals = [] } = await chrome.storage.local.get('proposals');
        const target = proposals.filter((p) => msg.id === 'all' || p.id === msg.id);
        for (const p of target) await applyProposal(p);
        const rest = proposals.filter((p) => !target.includes(p));
        await chrome.storage.local.set({ proposals: rest });
        await setBadge(rest.length);
        respond({ ok: true });
        break;
      }
      case 'dismiss': {
        const { proposals = [] } = await chrome.storage.local.get('proposals');
        const rest = proposals.filter((p) => p.id !== msg.id);
        await chrome.storage.local.set({ proposals: rest });
        await setBadge(rest.length);
        respond({ ok: true });
        break;
      }
      case 'saveSettings': {
        await chrome.storage.local.set({ settings: msg.settings });
        await ensureAlarm();
        respond({ ok: true });
        break;
      }
      case 'restore': {
        await chrome.tabs.create({ url: msg.url, active: false });
        respond({ ok: true });
        break;
      }
      case 'clearArchive':
        await chrome.storage.local.set({ archive: [] });
        respond({ ok: true });
        break;
      case 'exportData': {
        const data = await chrome.storage.local.get(['samples', 'archive', 'stats', 'settings']);
        respond(data);
        break;
      }
      default:
        respond({ error: `unknown message: ${msg.type}` });
    }
  })();
  return true; // keep the channel open for the async work above
});
