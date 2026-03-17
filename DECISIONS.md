# DECISIONS.md

Technical and product decisions made during the build of the FANZO Fixture Ranker, with reasoning. This document exists so future agents or developers can understand _why_ the code is structured the way it is.

---

## Language and framework: Python + Flask

**Decision:** Python 3 with Flask as the web framework.

**Why:** The core work of this tool is scraping and data processing — areas where Python's ecosystem (requests, BeautifulSoup, pytz) is mature and well-documented. Flask is the simplest possible web framework for a single-page tool with two routes. A more complex framework (Django, FastAPI) would add unnecessary overhead for a tool of this scope.

---

## Data source: FANZO JSON-LD structured data

**Decision:** Parse the `<script type="application/ld+json">` block on `fanzo.com/en` rather than scraping HTML elements.

**Why:** FANZO embeds schema.org `SportsEvent` structured data on the page for search engine indexing. This structured JSON is far more reliable than scraping HTML classes or element positions, which change frequently. Structured data is maintained deliberately and is unlikely to break without warning.

---

## Fixture pool: Today + 6 date tabs (7-day window)

**Decision:** Filter all scraped events to those starting within the next 7 days (UTC). The "Big Fixtures" tab on FANZO is explicitly excluded.

**Why:** The product brief specifies starting from "Today" and going through the next 6 dated tabs. The "Big Fixtures" tab is FANZO's own editorial selection — using it would defeat the purpose of running our own independent ranking. Filtering by date range naturally ignores it while capturing the full raw fixture pool.

---

## No external API keys required

**Decision:** All scoring factors use either hardcoded lookup tables or pure logic — no third-party API keys are needed to run the tool.

**Why:** The user requirement was zero setup. API keys (Betfair, football-data.org, etc.) would require account creation and configuration that non-technical users shouldn't have to manage. The scoring model covers 5 of 6 factors (85% of the composite weight) entirely from built-in data. The betting volume factor uses competition prestige + rivalry as a proxy — both strongly correlate with real-money wagering and require no external data.

---

## Match stakes: keyword inference, not live standings

**Decision:** Match stakes are inferred from keywords in the competition name ("Final", "Semi-Final", "Round of 16", etc.) rather than fetching live league standings.

**Why:** Fetching live standings would require external APIs (football-data.org, API-Football) for each competition, adding setup complexity and multiple network calls per run. Keyword inference from the competition name covers the most important high-stakes signals (cup finals, knockout rounds) reliably. League mid-season stakes (relegation battles, title races) are harder to detect without standings, so they receive a moderate default score. This is a known limitation and a clear upgrade path for V2.

---

## Betting volume: proxy, not real data

**Decision:** The "betting volume" factor uses a formula derived from competition tier and rivalry status, rather than live Betfair Exchange API data.

**Why:** Betfair requires a verified account (ID check) which conflicts with the zero-setup requirement. High-prestige competitions and rivalry fixtures are demonstrably the highest-volume betting events anyway — the proxy captures the signal well for ranking purposes.

---

## Team popularity: hardcoded table, not live scrape

**Decision:** Team popularity scores come from a hardcoded lookup table rather than live-scraping YouGov's ratings page.

**Why:** YouGov's ratings site is a JavaScript-rendered React app, making it difficult to scrape reliably without a headless browser (Playwright/Selenium). A hardcoded table is stable, fast, and requires no additional dependencies. The data changes slowly (once per season at most) and is easy to update manually. See `data/team_popularity.py`.

---

## CSV export: client-side JavaScript

**Decision:** The CSV export is generated entirely in the browser using JavaScript's `Blob` API, with no server-side endpoint.

**Why:** The data is already in the browser after the `/run` response. Creating a server-side export endpoint would add unnecessary complexity and a second network round-trip. Client-side generation is simpler, faster, and works offline once the results are loaded.

---

## Score breakdown: toggleable rows, not a modal

**Decision:** Clicking a fixture row expands an inline breakdown row beneath it, rather than opening a modal overlay.

**Why:** Inline expansion keeps the user's place in the ranked list and allows multiple breakdowns to be open simultaneously for comparison. Modals interrupt the reading flow and make side-by-side comparison impossible.

---

## No database, no persistence

**Decision:** Results are computed on demand with no caching or storage layer.

**Why:** The PRD specifies a simple web URL the user refreshes daily. There is no requirement to persist results between sessions, compare historical runs, or serve multiple concurrent users. Adding a database would introduce infrastructure complexity with no user benefit at this stage.

---

## Fonts: local files, not Google Fonts CDN

**Decision:** FANZO brand fonts (Chakra Petch, Barlow Condensed) are served from the local `static/fonts/` directory, copied from the FANZO Brand Toolkit.

**Why:** The tool is internal and may be run on a local machine without internet access (except for the FANZO scrape itself). Relying on Google Fonts would add an external dependency and slow the initial page load.

---

## Python version compatibility: 3.9

**Decision:** All type hints use `typing.Dict`, `typing.List`, `typing.Optional` rather than the `dict | list` union syntax.

**Why:** The system running this tool is Python 3.9. The `X | Y` union syntax for type hints was introduced in Python 3.10. Using the `typing` module maintains compatibility without requiring a Python upgrade.
