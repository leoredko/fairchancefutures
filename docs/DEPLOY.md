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

Expect the first `fly deploy` to work. Do not be shocked if it needs one
nudge.

## Before anything: this app has no authentication

Anyone with the URL is whoever the URL says they are. `/inside/marcus-w` is a
guessable address and loading it makes you Marcus. That is fine for a demo with
seeded fake clients and disqualifying for anything else.

The Fly config sets `X-Robots-Tag: noindex, nofollow` so it at least stays out
of search results. Do not put a real person's data behind this URL.

## Fly.io, which is faster to wake and costs a couple of dollars

Worth it if a spin-down mid-demo would be fatal, or if you want the data to
survive. Needs the CLI, so it needs a terminal and a local clone of the repo.

**Install flyctl** ([docs](https://fly.io/docs/flyctl/install/)). On Windows,
in PowerShell:

```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

Close and reopen PowerShell afterwards so the new command is found. Then:

```bash
fly auth signup      # or: fly auth login, if you already have an account
fly launch --copy-config --no-deploy      # pick a name nobody has taken
fly volumes create bridge_data --size 1 --region ewr
fly deploy
fly open
```

The volume matters. The store is a JSON file at `/data/bridge.json`, so without
a mounted volume every deploy resets the caseload to the seed. Which, for a
demo, is occasionally what you want: `fly ssh console -C "rm /data/bridge.json"`
then restart, and you are back to a clean stage.

Keep it to one machine. A second machine gets its own volume and would serve a
different caseload depending on which one answered.

## Render, which needs no terminal

The shortest path to a URL, and the one to take first. No CLI to install, no
local clone, no account beyond GitHub.

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

Environment: `BRIDGE_DATA` is the only variable, and it is the path to the JSON
store. Default is `data/bridge.json` relative to the working directory.

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
