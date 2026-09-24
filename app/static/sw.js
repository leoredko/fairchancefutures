// Minimal service worker.
//
// It exists so the tablet can install Bridge to the home screen: browsers want
// a registered worker before they offer an install. It deliberately does NOT
// cache or serve stale pages.
//
// This is not offline support, and the tablet does not need it to be: Bridge
// is loaded onto a connected device and writes go to the server as they are
// made. Doing offline properly would mean queueing writes in IndexedDB and
// replaying them on reconnect, and a worker that quietly serves a stale case
// timeline while a deadline moves is worse than no worker at all. So this one
// passes everything through to the network and says so.

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (event) => {
  // Network only. No cache, no offline fallback, no stale reads.
  event.respondWith(fetch(event.request));
});
