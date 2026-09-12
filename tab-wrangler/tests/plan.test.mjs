import test from 'node:test';
import assert from 'node:assert/strict';
import { plan, normalizeUrl, isProtected, DEFAULT_SETTINGS } from '../core.js';

const NOW = Date.now();
const mins = (n) => NOW - n * 60 * 1000;
const hours = (n) => NOW - n * 3600 * 1000;
const settings = { ...DEFAULT_SETTINGS, actions: { dedupe: 'propose', discard: 'propose', archive: 'propose', group: 'propose' } };
const find = (ps, kind) => ps.find((p) => p.kind === kind);

test('normalizeUrl strips fragments and tracking params', () => {
  assert.equal(normalizeUrl('https://a.com/p?utm_source=x#top'), 'https://a.com/p');
  assert.equal(normalizeUrl('https://a.com/p?id=1'), 'https://a.com/p?id=1');
});

test('pinned, active, audible and chrome:// tabs are protected', () => {
  for (const tab of [
    { url: 'https://a.com', pinned: true },
    { url: 'https://a.com', active: true },
    { url: 'https://a.com', audible: true },
    { url: 'chrome://settings' },
    { url: 'http://localhost:3000' }
  ]) assert.equal(isProtected(tab, settings), true, tab.url);
  assert.equal(isProtected({ url: 'https://a.com' }, settings), false);
});

test('dedupe keeps the most recently used copy', () => {
  const tabs = [
    { id: 1, url: 'https://a.com/x', lastAccessed: mins(50) },
    { id: 2, url: 'https://a.com/x#frag', lastAccessed: mins(1) },
    { id: 3, url: 'https://a.com/x?utm_source=n', lastAccessed: mins(90) }
  ];
  const p = find(plan(tabs, {}, settings, NOW), 'dedupe');
  assert.deepEqual(p.tabIds.sort(), [1, 3]);
});

test('a tab is claimed by at most one proposal per sweep', () => {
  const tabs = [
    { id: 1, url: 'https://a.com/x', lastAccessed: hours(200) },
    { id: 2, url: 'https://a.com/x', lastAccessed: hours(300) },
    { id: 3, url: 'https://b.com/1', lastAccessed: hours(200) }
  ];
  const ids = plan(tabs, {}, settings, NOW).flatMap((p) => p.tabIds);
  assert.equal(new Set(ids).size, ids.length);
});

test('stale beats cold: an old tab is archived, not merely unloaded', () => {
  const tabs = [{ id: 1, url: 'https://a.com/1', lastAccessed: hours(100) }];
  const ps = plan(tabs, {}, settings, NOW);
  assert.ok(find(ps, 'archive'));
  assert.equal(find(ps, 'discard'), undefined);
});

test('unknown age is treated as fresh, never punished', () => {
  const tabs = [{ id: 1, url: 'https://a.com/1' }];
  assert.deepEqual(plan(tabs, {}, settings, NOW), []);
});

test('the activity map fills in for missing lastAccessed', () => {
  const tabs = [{ id: 7, url: 'https://a.com/1' }];
  const ps = plan(tabs, { 7: mins(120) }, settings, NOW);
  assert.deepEqual(find(ps, 'discard').tabIds, [7]);
});

test('grouping needs the minimum count and never spans windows', () => {
  const mk = (id, windowId) => ({ id, windowId, groupId: -1, url: `https://a.com/${id}`, lastAccessed: mins(1) });
  const ps = plan([mk(1, 1), mk(2, 1), mk(3, 1), mk(4, 2)], {}, settings, NOW);
  const groups = ps.filter((p) => p.kind === 'group');
  assert.equal(groups.length, 1);
  assert.deepEqual(groups[0].tabIds, [1, 2, 3]);
});

test('actions set to off produce nothing', () => {
  const off = { ...settings, actions: { dedupe: 'off', discard: 'off', archive: 'off', group: 'off' } };
  const tabs = [
    { id: 1, url: 'https://a.com/x', lastAccessed: hours(500) },
    { id: 2, url: 'https://a.com/x', lastAccessed: hours(500) }
  ];
  assert.deepEqual(plan(tabs, {}, off, NOW), []);
});
