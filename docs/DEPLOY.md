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

## Installing on the tablet

Open the deployed URL in the tablet's browser and use "Add to Home Screen". It
installs standalone: no address bar, no browser chrome, its own icon.

- `app/static/manifest.webmanifest` — name, colors, icons, `display: standalone`
- `app/static/sw.js` — a service worker registered so browsers offer the install
- `scripts/make_icons.py` — regenerates the icons, so they are editable rather
  than a binary nobody can change

**The service worker does not cache anything.** It passes every request to the
network. This is deliberate and the file says so: the deck's offline-first
promise is a real feature, and a worker that quietly serves a stale case
timeline while a statutory deadline moves is worse than having none. Doing
offline properly means queueing writes in IndexedDB and replaying them on
reconnect. That work is not done, and pretending otherwise on a screen that
says "nothing is lost if you lose access for a week" would be the same kind of
lie the EN/ES pill was.

So: the tablet app assumes connectivity. Say that on the slide.
