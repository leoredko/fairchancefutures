// Minimal service worker.
//
// It exists so the tablet can install Bridge to the home screen: browsers want
// a registered worker before they offer an install. It deliberately does NOT
// cache or serve stale pages.
//
// This is not offline support. Bridge assumes the tablet is online, which is a
// stated assumption of this build rather than a finding: see SIMPLIFICATIONS
// in app/sources.py. Doing offline properly means caching the app shell,
// queueing writes in IndexedDB and replaying them later, and none of that is
// built.
//
// Why it does not cache in the meantime, which has not changed: a worker that
// quietly serves a stale case timeline while a statutory deadline moves is
// worse than no worker at all. So it passes everything through to the network
// and says so.

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (event) => {
  // Network only. No cache, no offline fallback, no stale reads.
  event.respondWith(fetch(event.request));
});
