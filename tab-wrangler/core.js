// Pure planning logic. No chrome.* calls in here on purpose, so it can be
// unit-tested with plain node and reasoned about without a browser.

export const DEFAULT_SETTINGS = {
  sweepMinutes: 5,
  discardAfterMinutes: 30,
  archiveAfterHours: 72,
  minGroupSize: 3,
  // Per-action mode: "propose" queues it for review, "auto" applies on sweep,
  // "off" skips it entirely.
  actions: {
    dedupe: 'propose',
    discard: 'auto',
    archive: 'propose',
    group: 'off'
  },
  // Substring match against the URL. Anything matching is never touched.
  protectedPatterns: ['localhost', '127.0.0.1', 'mail.google.com', 'calendar.google.com']
};

const TRACKING_PARAMS = [
  'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
  'gclid', 'fbclid', 'mc_cid', 'mc_eid', 'ref_src', 'igshid'
];

const UNTOUCHABLE_SCHEMES = ['chrome:', 'chrome-extension:', 'devtools:', 'edge:', 'about:'];

export function normalizeUrl(raw) {
  try {
    const u = new URL(raw);
    u.hash = '';
    for (const p of TRACKING_PARAMS) u.searchParams.delete(p);
    let s = u.toString();
    if (s.endsWith('/') && u.pathname !== '/') s = s.slice(0, -1);
    return s;
  } catch {
    return raw || '';
  }
}

export function domainOf(raw) {
  try {
    return new URL(raw).hostname.replace(/^www\./, '');
  } catch {
    return 'unknown';
  }
}

/** Tabs we never close, discard, or regroup regardless of age. */
export function isProtected(tab, settings) {
  if (!tab || !tab.url) return true;
  if (tab.pinned || tab.active || tab.audible) return true;
  if (UNTOUCHABLE_SCHEMES.some((s) => tab.url.startsWith(s))) return true;
  return (settings.protectedPatterns || []).some((p) => p && tab.url.includes(p));
}

/**
 * Age of a tab in ms. Chrome 121+ gives us tab.lastAccessed for free; the
 * activity map is our own fallback for older Chrome and for tabs we have
 * watched since startup.
 */
export function idleMs(tab, activity, now) {
  const seen = Math.max(tab.lastAccessed || 0, activity[String(tab.id)] || 0);
  if (!seen) return 0; // unknown age: treat as fresh, never punish a mystery tab
  return Math.max(0, now - seen);
}

function label(tab) {
  const t = (tab.title || tab.url || '').trim();
  return t.length > 70 ? `${t.slice(0, 67)}...` : t;
}

/**
 * Build the full set of proposed actions. Each stage claims tabs so no tab
 * ever appears in two proposals in the same sweep.
 */
export function plan(tabs, activity, settings, now) {
  const claimed = new Set();
  const proposals = [];
  const live = tabs.filter((t) => !isProtected(t, settings));
  const mode = (k) => (settings.actions && settings.actions[k]) || 'off';

  // 1. Duplicates. Nothing is lost: an identical tab stays open.
  if (mode('dedupe') !== 'off') {
    const byUrl = new Map();
    for (const tab of live) {
      const key = normalizeUrl(tab.url);
      if (!key) continue;
      if (!byUrl.has(key)) byUrl.set(key, []);
      byUrl.get(key).push(tab);
    }
    for (const [url, group] of byUrl) {
      if (group.length < 2) continue;
      // Keep the most recently touched copy, close the rest.
      const sorted = [...group].sort((a, b) => idleMs(a, activity, now) - idleMs(b, activity, now));
      const losers = sorted.slice(1).filter((t) => !claimed.has(t.id));
      if (!losers.length) continue;
      losers.forEach((t) => claimed.add(t.id));
      proposals.push({
        id: `dedupe:${url}`,
        kind: 'dedupe',
        mode: mode('dedupe'),
        title: `${losers.length} duplicate${losers.length > 1 ? 's' : ''} of ${domainOf(url)}`,
        detail: label(sorted[0]),
        tabIds: losers.map((t) => t.id),
        items: losers.map((t) => ({ url: t.url, title: t.title }))
      });
    }
  }

  // 2. Stale tabs: archive the URL somewhere searchable, then close.
  if (mode('archive') !== 'off') {
    const cutoff = settings.archiveAfterHours * 3600 * 1000;
    const stale = live.filter((t) => !claimed.has(t.id) && idleMs(t, activity, now) >= cutoff);
    if (stale.length) {
      stale.forEach((t) => claimed.add(t.id));
      proposals.push({
        id: 'archive:stale',
        kind: 'archive',
        mode: mode('archive'),
        title: `Archive ${stale.length} tab${stale.length > 1 ? 's' : ''} untouched for ${settings.archiveAfterHours}h+`,
        detail: stale.slice(0, 3).map(label).join(' | '),
        tabIds: stale.map((t) => t.id),
        items: stale.map((t) => ({ url: t.url, title: t.title }))
      });
    }
  }

  // 3. Cold tabs: unload from memory. The tab stays in the strip.
  if (mode('discard') !== 'off') {
    const cutoff = settings.discardAfterMinutes * 60 * 1000;
    const cold = live.filter(
      (t) => !claimed.has(t.id) && !t.discarded && idleMs(t, activity, now) >= cutoff
    );
    if (cold.length) {
      cold.forEach((t) => claimed.add(t.id));
      proposals.push({
        id: 'discard:cold',
        kind: 'discard',
        mode: mode('discard'),
        title: `Unload ${cold.length} cold tab${cold.length > 1 ? 's' : ''} from memory`,
        detail: 'Reversible: they reload when you click them',
        tabIds: cold.map((t) => t.id),
        items: cold.map((t) => ({ url: t.url, title: t.title }))
      });
    }
  }

  // 4. Grouping by domain. Only tabs that are not already in a group.
  if (mode('group') !== 'off') {
    const byDomain = new Map();
    for (const tab of tabs) {
      if (tab.pinned || !tab.url) continue;
      if (UNTOUCHABLE_SCHEMES.some((s) => tab.url.startsWith(s))) continue;
      if (tab.groupId !== undefined && tab.groupId > -1) continue;
      if (claimed.has(tab.id)) continue;
      const d = domainOf(tab.url);
      if (!byDomain.has(d)) byDomain.set(d, []);
      byDomain.get(d).push(tab);
    }
    for (const [domain, group] of byDomain) {
      if (group.length < settings.minGroupSize) continue;
      // Tab groups cannot span windows, so split by window.
      const byWindow = new Map();
      for (const t of group) {
        if (!byWindow.has(t.windowId)) byWindow.set(t.windowId, []);
        byWindow.get(t.windowId).push(t);
      }
      for (const [windowId, wtabs] of byWindow) {
        if (wtabs.length < settings.minGroupSize) continue;
        wtabs.forEach((t) => claimed.add(t.id));
        proposals.push({
          id: `group:${domain}:${windowId}`,
          kind: 'group',
          mode: mode('group'),
          title: `Group ${wtabs.length} tabs under "${domain}"`,
          detail: wtabs.slice(0, 3).map(label).join(' | '),
          groupTitle: domain,
          tabIds: wtabs.map((t) => t.id),
          items: wtabs.map((t) => ({ url: t.url, title: t.title }))
        });
      }
    }
  }

  return proposals;
}

const GROUP_COLORS = ['blue', 'cyan', 'green', 'yellow', 'orange', 'red', 'pink', 'purple', 'grey'];

export function colorFor(name) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return GROUP_COLORS[h % GROUP_COLORS.length];
}
