# Deploying Bridge

Two things are set up here: a container that runs anywhere, and a web app
manifest so the inside surface installs to a tablet home screen.

Not deployed from this repo yet, but no longer untested. There is still no
Docker daemon in the environment this was written in, so the image has never
been built. What has been done instead is a faithful rehearsal of it: a clean
directory holding only what the Dockerfile copies, a fresh virtual environment
with only what `requirements.txt` lists, and then the Dockerfile's own start
command against a stand-in for the mounted volume.

    /healthz  /  /signin  /citations  /staff      all 200
    /data/bridge.json                             written on first boot
    app/translations/es.po                        inside the image, 63 KB
    startup log                                   no errors

That rules out the things a first deploy usually dies on: a missing
dependency, a file the Dockerfile forgot to copy, a path that only resolves on
a developer's machine, a volume that never gets written. What it cannot rule
out is the base image itself, since the rehearsal ran on 3.11 and the
Dockerfile pins 3.12. CI runs the full suite on both, so that gap is covered
from the other side.

Expect the first deploy to work. Do not be shocked if it needs one nudge.

## Before anything: this app has no authentication

Anyone with the URL is whoever the URL says they are. `/inside/marcus-w` is a
guessable address and loading it makes you Marcus. That is fine for a demo with
seeded fake clients and disqualifying for anything else.

Every response carries `X-Robots-Tag: noindex, nofollow` and `/robots.txt`
disallows everything, so it at least stays out of search results. With
`BRIDGE_CAPTCHA` set, the sign-in doors also ask a written-out arithmetic
question, which stops crawlers and scripted sign-ins. Neither is
authentication: somebody with the link can read Marcus's DIN off the
walkthrough and be Marcus. That lives in
`app/main.py` rather than in a host's config, so it holds wherever this runs
rather than only where somebody remembered to set it. Do not put a real
person's data behind this URL.

## Render, which is where this deploys

The one hosted path. No CLI to install, no local clone, no account beyond
GitHub.

There used to be a `fly.toml` beside `render.yaml` and a section here for it.
Both are gone. Two deploy configs meant two places to change a port or an
environment variable and one of them silently going stale, and only one of
them was ever deployed from.

1. Sign in at [render.com](https://render.com) with GitHub.
2. **New**, then **Blueprint**.
3. Pick this repository. Render reads `render.yaml` and does the rest.

**Free instances cannot have a persistent disk.** Render rejects a blueprint
that asks for `plan: free` and a disk together, which is what this file used to
do. It now asks for neither, so the JSON store is container-local and resets
whenever the service restarts, which on the free plan it does after a spell
with no traffic.

For a demo that is survivable and sometimes what you want: a restart reseeds
the caseload, so Marcus is back with his three reports and a clean stage. What
it costs is anything not in the seed. A PIN somebody set, a lesson they
finished, a county they picked. To keep those, the service has to be paid:
move off `plan: free` and add the `disk:` block that `render.yaml` carries in
a comment.

`BRIDGE_SECRET` is set by the blueprint rather than left to the app. Without a
disk, the app's own generated key would live in the store that resets, so
everybody would be signed out on every restart rather than only losing data.

**The other cost of free:** an instance with no traffic spins down, and the
next request waits for it to come back. Open the URL a few minutes before
presenting so the first person to see it is you, not the room.

## Anywhere else

```bash
docker build -t bridge .
docker run -p 8000:8000 -v bridge_data:/data bridge
```

Environment:

- `BRIDGE_DATA` — path to the JSON store. Default `data/bridge.json`, relative
  to the working directory. The parent directory is created on first write.
- `BRIDGE_SECRET` — session signing key. Generated at boot if unset, which
  means it changes on every restart and signs everybody out.
- `PORT` — the port to bind. Default 8000. Render assigns this, so the
  container reads it rather than hardcoding a port Render is not expecting.
- `BRIDGE_CAPTCHA` — set it to anything truthy and both sign-in doors ask an
  arithmetic question first. On in `render.yaml`, off everywhere else. See
  below.

## Getting onto the tablet

The destination is a progressive web app that arrives **already on the tablet**,
provisioned by whoever manages the facility's devices. Not something a person
discovers in a browser and installs themselves: nobody inside is going to be
handed a URL and told to tap Add to Home Screen, and a product that depends on
them doing so does not get used.

That is a distribution question rather than a code one, and the code is the same
either way. What it changes is the copy: nothing in this app should ever tell a
person to install it.

- `app/static/manifest.webmanifest` — name, colors, icons, `display: standalone`
- `app/static/sw.js` — the service worker, registered so the app runs as an app
- `scripts/make_icons.py` — regenerates the icons, so they are editable rather
  than a binary nobody can change

To try the installed experience during development, open the deployed URL in a
browser and use Add to Home Screen. That is a development convenience and not
the shipping path.

**The service worker does not cache anything.** It passes every request to the
network, deliberately. A worker that quietly serves a stale case timeline while
a statutory deadline moves is worse than having none.

That is the right call while the tablet is connected, which it is: Bridge
reaches the person's own record and nothing else. If a facility turns out to
have genuinely intermittent connectivity, the fix is caching the app shell so it
launches instantly, plus queueing writes in IndexedDB and replaying them on
reconnect. Both are real work and neither is done, so the worker says so rather
than implying otherwise.

So: the tablet app assumes connectivity. Say that on the slide.
