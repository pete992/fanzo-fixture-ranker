# PRD: FANZO Fixture Interest Ranker

**Version:** 1.0
**Status:** Draft for approval

---

## 1. Overview

The FANZO Fixture Interest Ranker is an internal web tool that identifies and ranks the top 20 UK-televised sports fixtures for the upcoming 7-day period by estimated UK fan interest.

FANZO editorial staff currently have no systematic way to quickly determine which fixtures matter most to UK fans across all sports. This tool solves that by running a data-driven ranking pipeline at the press of a button — pulling from FANZO's own fixture data and enriching it with competition tier, match stakes, rivalry status, team popularity, kick-off time, and betting market volume — so the team always knows which fixtures deserve priority attention.

---

## 2. Target User

FANZO editorial staff. Multiple users, non-technical. They need a tool that requires zero configuration, produces an immediately useful output, and gets out of the way.

---

## 3. Core Features

1. **One-button execution.** A single "Run" button triggers the full pipeline — fixture scraping, data enrichment, scoring, and ranking — with no configuration required.

2. **Top 20 ranked fixture list.** Results are displayed as a clean ranked list (1–20), showing team/competitor names, sport, competition, round/stage, kick-off date and time (UK), and broadcasting channel(s).

3. **Plain-English rationale per fixture.** Each fixture shows a short summary explaining why it ranked where it did (e.g. "Champions League semi-final between two top-10 most-followed UK clubs, prime-time kick-off").

4. **Toggleable score breakdown.** Each fixture can be expanded to reveal its six sub-scores (competition tier, match stakes, derby/rivalry, team popularity, kick-off time, betting volume) with individual values and the composite score out of 100.

5. **CSV export.** A single export button downloads the full ranked list — including sub-scores and rationale — as a CSV file.

---

## 4. User Flow

1. User opens the tool URL in a browser.
2. User presses the **Run** button.
3. A loading state indicates the pipeline is running (scraping, enriching, scoring).
4. The top 20 ranked fixtures appear on screen, ordered 1–20.
5. User reads the ranked list and plain-English rationale for each fixture.
6. User clicks any fixture row to expand and view the detailed sub-score breakdown.
7. User clicks **Export CSV** to download the list if needed.
8. To refresh with the latest data, user reloads the page and presses Run again.

---

## 5. Design Direction

- **Brand:** Follows FANZO brand guidelines — black, white, and `#FED900` yellow as the primary accent. The tool should feel like a natural extension of the FANZO product family, not a generic internal dashboard.
- **Tone:** Direct and functional. Sports-forward. No unnecessary decoration. Information density is appropriate — this is a working tool, not a marketing page.
- **Layout:** Single-page. Ranked list is the primary content. Expandable rows for detail. Run and Export buttons are prominent and clearly labelled.
- **Loading state:** Clear visual feedback while the pipeline runs — the user should know the tool is working, not frozen.

---

## 6. Out of Scope

- **User accounts or authentication** — the URL is the access control
- **Automatic or scheduled runs** — the tool only runs when a user presses the button
- **Push notifications or alerts** — no proactive communication
- **Mobile app** — web browser only
- **Automatic updates to any FANZO internal system** — editorial review and any downstream action is always manual
- **Non-televised fixtures** — if it's not on UK TV, it's not in scope
- **Fixtures beyond 7 days ahead** — the tool is optimised for the immediate upcoming week
- **Real-time or in-play data** — pre-match ranking only
- **Absolute audience size predictions** — the output is a relative ranking, not a viewership forecast
- **Configurable scoring weights** — the methodology is fixed; editorial judgement handles edge cases
