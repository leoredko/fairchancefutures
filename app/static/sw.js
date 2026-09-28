// Minimal service worker.
//
// It exists so the tablet can install Bridge to the home screen: browsers want
// a registered worker before they offer an install. It deliberately does NOT
// cache or serve stale pages.
//
// This is not offline support, and it is a gap rather than a decision. The
// justification used to be that the tablet is a connected device and writes go
// to the server as they are made. That is not what a DOCCS tablet is: it
// connects to a kiosk and to nothing else, gets one 15-minute session a day,
// and stops working if it has not met a kiosk in 30 days. See
// `the_tablet_reaches_a_kiosk_not_a_network` in app/sources.py.
//
// Doing this properly means caching the app shell, queueing writes in
// IndexedDB and replaying them on the next kiosk session. That is real work
// and none of it is done. What has not changed is why this worker does not
// cache in the meantime: a worker that quietly serves a stale case timeline
// while a statutory deadline moves is worse than no worker at all. So it
// passes everything through to the network and says so, and the browser build
// is what this is honest about serving.

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (event) => {
  // Network only. No cache, no offline fallback, no stale reads.
  event.respondWith(fetch(event.request));
});
