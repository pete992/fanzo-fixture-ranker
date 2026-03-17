# FANZO Fixture Interest Ranker

An internal web tool that identifies and ranks the top 20 UK-televised sports fixtures for the upcoming 7 days by estimated UK fan interest.

Press one button. Get a ranked list. Export to CSV if needed.

---

## What it does

1. Scrapes [fanzo.com/en](https://www.fanzo.com/en) for all UK-televised fixtures in the next 7 days
2. Scores each fixture across six factors (competition prestige, match stakes, rivalry status, team popularity, kick-off time, and betting interest proxy)
3. Returns a ranked list of the top 20 fixtures with scores and plain-English rationale
4. Lets you expand any fixture to see the full score breakdown
5. Lets you export the full list as a CSV

---

## Deploying to a hosted URL (recommended)

This is the easiest option. The app lives on the internet and you open it like any website — no software to install, no commands to run.

You need two free accounts: **GitHub** (stores the code) and **Render** (runs the app).

---

### Step 1 — Create a free GitHub account

Go to [github.com](https://github.com) and sign up. It's free.

---

### Step 2 — Upload the project to GitHub

1. Once logged in to GitHub, click the **+** button (top right) → **New repository**
2. Name it `fanzo-fixture-ranker`, leave everything else as default, click **Create repository**
3. On the next screen, click **uploading an existing file**
4. Drag the entire `fanzo-fixture-ranker` folder onto the upload area
5. Click **Commit changes**

---

### Step 3 — Create a free Render account

Go to [render.com](https://render.com) and sign up with your GitHub account. It's free.

---

### Step 4 — Deploy the app on Render

1. In Render, click **New** → **Web Service**
2. Click **Connect a repository** and select `fanzo-fixture-ranker`
3. Render will detect the settings automatically (the `render.yaml` file handles this)
4. Click **Create Web Service**
5. Wait ~2 minutes while it builds and deploys

Render will give you a permanent URL like:
```
https://fanzo-fixture-ranker.onrender.com
```

Bookmark that URL. Open it in any browser, press **Run**, and you're done.

> **Note on free tier:** Render's free tier spins down after 15 minutes of inactivity. The first visit after a period of no use may take 30–60 seconds to load. Subsequent uses are instant.

---

## Running locally (alternative)

If you'd prefer to run the app on your own Mac instead of hosting it online, you need Python 3.9 or later installed.

**Step 1 — Open a terminal and navigate to this folder:**

```bash
cd "fanzo-fixture-ranker"
```

**Step 2 — Install the dependencies:**

```bash
python3 -m pip install -r requirements.txt
```

**Step 3 — Start the app:**

```bash
python3 app.py
```

Then open your browser and go to `http://localhost:5000`

Press the **Run** button. The tool will fetch today's fixtures and rank them. This takes about 5–10 seconds.

---

## Using the results

- **Click any fixture row** to expand the detailed score breakdown
- **Export CSV** to download the full ranked list (rank, teams, competition, kick-off, channels, all sub-scores, rationale)

---

## How the scoring works

Each fixture is scored on six factors, each out of 100:

| Factor | Weight | How it's calculated |
|---|---|---|
| Competition tier | 25% | Static lookup table based on UK TV audience data |
| Match stakes | 20% | Inferred from competition stage (final, semi, group etc.) |
| Derby / rivalry | 15% | Pre-compiled UK rivalry lookup — 0 or 100 |
| Team popularity | 15% | Based on YouGov UK club popularity data |
| Kick-off time | 15% | UK viewing window convenience |
| Betting volume proxy | 10% | Competition tier + rivalry as a proxy for wagering interest |

The composite score is a weighted sum, capped at 100.

---

## Running the tests

```bash
python3 -m pytest tests/ -v
```

All 92 tests should pass.

---

## Project structure

```
fanzo-fixture-ranker/
├── app.py                      # Flask web app (routes)
├── scraper.py                  # FANZO website scraper
├── scorer.py                   # Six-factor scoring model
├── data/
│   ├── competition_tiers.py    # Competition prestige lookup table
│   ├── rivalries.py            # UK sports rivalry lookup table
│   └── team_popularity.py      # UK team popularity scores
├── templates/
│   └── index.html              # Single-page frontend
├── static/
│   ├── style.css               # FANZO-branded styles
│   ├── script.js               # Frontend interactivity + CSV export
│   └── fonts/                  # FANZO brand fonts
├── tests/
│   ├── test_scorer.py          # Scoring model unit tests
│   ├── test_scraper.py         # Scraper unit tests (mocked)
│   └── test_app.py             # Flask route integration tests
├── requirements.txt
├── README.md
└── DECISIONS.md
```

---

## Maintenance notes

Two components need occasional manual updates:

- **`data/competition_tiers.py`** — Review at the start of each season or when a major broadcast rights deal changes (e.g. a sport moving from Sky to free-to-air).
- **`data/rivalries.py`** — Check annually, and add any newly promoted clubs whose local derby is now a televised fixture.
- **`data/team_popularity.py`** — Update at the start of each season to reflect promotions, relegations, and shifts in national following.
