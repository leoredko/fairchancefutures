# Getting Bridge running on your own machine

One page. Clone it, run it, make a change, open a pull request. Fifteen minutes
if nothing fights you.

## 1. Get access

The repository is `leoredko/fairchancefutures`. You are both already added as
collaborators with write access, so there is nothing to request.

If GitHub has not already put you on the repository, the invite is sitting in
your email or at `https://github.com/leoredko/fairchancefutures/invitations`.
Accept it *before* you clone. Cloning without it returns a confusing
"repository not found" rather than a permission error.

## 2. What you need installed

- **Python 3.11 or 3.12.** Nothing older. CI runs both, so either is fine.
  Check with `python3 --version`.
- **Git.** `git --version`. Mac has it after `xcode-select --install`.
  Windows: install Git for Windows, then do everything below in Git Bash.
- That is the whole list. No database, no Docker, no Node. Data is a JSON file.

## 3. Clone it

```bash
git clone https://github.com/leoredko/fairchancefutures.git
cd fairchancefutures
```

If GitHub asks for a password and rejects the one you type, it wants a personal
access token, not your account password. Easier fix: install the GitHub CLI and
run `gh auth login`, or use SSH.

## 4. Run it

```bash
./run.sh
```

That installs the dependencies, runs the tests, and serves the app on
http://127.0.0.1:8000. If the tests fail, it stops before serving, which is
deliberate: you should never be looking at a build whose tests are red.

By hand, if you would rather see the steps:

```bash
python3 -m venv .venv && source .venv/bin/activate   # optional but tidy
pip install -r requirements.txt
pytest -q                                            # 297 tests, all should pass
uvicorn app.main:app --reload
```

Windows note: `./run.sh` needs Git Bash or WSL. From PowerShell, run the three
commands above instead and activate with `.venv\Scripts\activate`.

## 5. Look at the three surfaces

Bridge is three surfaces over one case, and they are three URLs:

| Who | URL | Sign in with |
| --- | --- | --- |
| Person inside, tablet | http://127.0.0.1:8000/inside | Any DIN starting `28`, e.g. `28-A-1187`, then a PIN you choose |
| Helper outside, phone | http://127.0.0.1:8000/family | A helper code, e.g. `BRIDGE-4417`, then a PIN |
| Coordinator, desktop | http://127.0.0.1:8000/staff | Nothing. It opens on the caseload queue |

Any DIN starting `28` opens a case on the spot, because 2028 has not happened
and those cannot belong to a real person. The rest of the seeded logins and a
five-minute walkthrough are in [DEMO.md](DEMO.md).

Start at **Learn** on the tablet surface. The credit course is the part of the
product that matters most and it needs no setup.

## 6. Read these before changing anything

- **[../CLAUDE.md](../CLAUDE.md)** — the house rules, and the shortest thing
  here. Read it first. It is written for AI sessions but it is the real list of
  what breaks the product.
- **[SCOPE.md](SCOPE.md)** — what each surface can and cannot do.
- **[VERIFY.md](VERIFY.md)** — every legal claim with its primary source.
- **[DESIGN-NOTES.md](DESIGN-NOTES.md)** — why things are the way they are.
- `app/surfaces.py` — read this as the product spec.

The four that will bite you fastest:

1. **No legal sentence without a primary source.** Add it to `app/sources.py`
   with a URL and the date you checked, or write it as an open question.
2. **No camera on the tablet surface.** A test fails if an upload route appears.
3. **Sentence case everywhere**, and no raw column name reaches a screen.
   `app/labels.py` is the registry and a test enforces it.

## 7. Make a change and send it

```bash
git checkout main && git pull                 # start from current main
git checkout -b yourname/short-description    # never commit straight to main
# ... edit ...
pytest -q                                     # must be green
git add -A
git commit -m "Say what changed and why, in a sentence"
git push -u origin yourname/short-description
```

Then open a pull request on GitHub. CI runs pytest on 3.11 and 3.12 on every
pull request, and a red check means it does not merge. Somebody else reviews
it. Main stays green.

## 8. When something goes wrong

| Symptom | Fix |
| --- | --- |
| `permission denied: ./run.sh` | `chmod +x run.sh` |
| `No module named pytest` | You skipped `pip install -r requirements.txt`, or your virtualenv is not active |
| `Address already in use` | Something is on port 8000. `uvicorn app.main:app --reload --port 8001` |
| Tests pass locally, CI is red | You are on a different Python. Check `python3 --version` against 3.11 / 3.12 |
| The app looks stale after an edit | `--reload` watches `app/`. Templates do not always trigger it. Restart |
| Weird state in the app | The store is a JSON file under `data/`, gitignored. Delete it and it reseeds |

Stuck for more than twenty minutes: say so in the group chat rather than
burning an evening. Somebody has already hit it.
