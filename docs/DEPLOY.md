# Deploying Bridge

Two things are set up here: a container that runs anywhere, and a web app
manifest so the inside surface installs to a tablet home screen.

Neither has been deployed from this repo yet. The Dockerfile has not been built
in CI (no Docker daemon in the environment it was written in), but the exact
file layout, start command, health check and data path were run and verified
outside a container. Expect the first `fly deploy` to work; do not be shocked
if it needs one nudge.

## Before anything: this app has no authentication

Anyone with the URL is whoever the URL says they are. `/inside/marcus-w` is a
guessable address and loading it makes you Marcus. That is fine for a demo with
seeded fake clients and disqualifying for anything else.

The Fly config sets `X-Robots-Tag: noindex, nofollow` so it at least stays out
of search results. Do not put a real person's data behind this URL.

## Fly.io

```bash
fly auth login
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

## Render

Point Render at the repo; it reads `render.yaml`. Same shape: Docker runtime,
health check on `/healthz`, 1 GB disk mounted at `/data`.

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
