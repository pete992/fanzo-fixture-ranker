"""
enrichment.py
=============
Scrapes live league standings from ESPN for use in match stakes scoring.

Why ESPN?
  - Renders standings as static HTML (no JavaScript required)
  - Covers all major UK-relevant leagues in a consistent URL format
  - No API key needed

Supported leagues and their ESPN league codes:
  Premier League   → eng.1
  Championship     → eng.2
  La Liga          → esp.1
  Bundesliga       → ger.1
  Serie A          → ita.1
  Ligue 1          → fra.1

Returns:
  A dict keyed by normalised team name, each value containing:
    position     (int)  — current league position (1 = top)
    points       (int)  — points accumulated
    played       (int)  — games played
    total_teams  (int)  — total teams in the division
    leader_pts   (int)  — points held by the current league leader

Falls back gracefully: if any league fails to scrape, it is skipped and
the scorer falls back to keyword-based stakes inference for that fixture.
"""

import logging
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Request settings
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}
REQUEST_TIMEOUT = 15

# ESPN standings URL template
ESPN_URL = "https://www.espn.co.uk/football/table/_/league/{league_code}"

# Leagues to fetch — extend this list to add more
LEAGUES_TO_FETCH = [
    "eng.1",   # Premier League
    "eng.2",   # Championship
    "esp.1",   # La Liga
    "ger.1",   # Bundesliga
    "ita.1",   # Serie A
    "fra.1",   # Ligue 1
]


def fetch_all_standings() -> Dict[str, Dict]:
    """
    Scrape standings from ESPN for all configured leagues.

    Returns a flat dict mapping normalised team names to their standing info.
    Team names are normalised to lowercase for case-insensitive matching.

    Example return value:
        {
            "arsenal": {"position": 1, "points": 70, "played": 31, "total_teams": 20, "leader_pts": 70},
            "manchester city": {"position": 2, "points": 61, ...},
            ...
        }
    """
    all_standings = {}

    for league_code in LEAGUES_TO_FETCH:
        try:
            standings = _fetch_league_standings(league_code)
            all_standings.update(standings)
            logger.info("Fetched %d teams from ESPN league %s", len(standings), league_code)
        except Exception as exc:
            # A failed league doesn't break the whole pipeline — scorer falls back
            logger.warning("Could not fetch standings for league %s: %s", league_code, exc)

    logger.info("Fetched standings for %d teams total", len(all_standings))
    return all_standings


def get_team_standing(team_name: str, standings: Dict) -> Optional[Dict]:
    """
    Look up a team's standing by name.

    Tries exact lowercase match first, then substring matching to handle
    variations like "Man City" vs "Manchester City".

    Returns None if the team cannot be found in the standings.
    """
    if not team_name or not standings:
        return None

    name_lower = team_name.strip().lower()

    # Exact match
    if name_lower in standings:
        return standings[name_lower]

    # Partial match — e.g. "man city" is in "manchester city" or vice versa
    for known_name, data in standings.items():
        if known_name in name_lower or name_lower in known_name:
            return data

    return None


def calculate_live_stakes(
    home_team: str,
    away_team: str,
    standings: Dict,
    competition: str,
) -> Optional[float]:
    """
    Determine match stakes (0–100) using live league standings.

    Returns None if either team cannot be found — the scorer then falls
    back to keyword-based stakes inference.

    Scoring logic:
        - Title decider (1st vs 2nd, both within 5 pts)  → 95
        - Both teams in title race (top 4, gap ≤ 10)     → 85
        - One team in title race                         → 75
        - Both fighting for European spots (4–8, gap ≤ 8)→ 70
        - Both in relegation battle (bottom 6, gap ≤ 8)  → 78
        - One team in relegation battle                  → 65
        - Dead rubber (both safely mid-table)            → 30
        - Default (one team slightly involved)           → 50
    """
    # Only apply live stakes to league competitions — knockout rounds are
    # already handled by keyword detection (Final, Semi-Final, etc.)
    comp_lower = competition.lower()
    league_keywords = [
        "premier league", "championship", "la liga",
        "bundesliga", "serie a", "ligue 1",
    ]
    if not any(k in comp_lower for k in league_keywords):
        return None

    home = get_team_standing(home_team, standings)
    away = get_team_standing(away_team, standings)

    if not home or not away:
        return None

    pos_h = home["position"]
    pts_h = home["points"]
    pos_a = away["position"]
    pts_a = away["points"]
    total  = home.get("total_teams", 20)
    leader = home.get("leader_pts", max(pts_h, pts_a))

    safe_zone_cutoff = total - 3     # Below this = relegation zone
    close_gap = 8                    # Points gap still considered "in a fight"

    # ── Classify each team's situation ────────────────────────────────────────

    def in_title_race(pos, pts):
        """Top 4, within 10 points of the leader."""
        return pos <= 4 and (leader - pts) <= 10

    def in_euro_fight(pos, pts):
        """Positions 4–8, within 8 points of 4th place."""
        return 4 <= pos <= 8

    def in_relegation_fight(pos, pts):
        """Bottom 6, or within 8 points of the relegation zone."""
        return pos > (total - 6) or pos >= safe_zone_cutoff

    h_title   = in_title_race(pos_h, pts_h)
    a_title   = in_title_race(pos_a, pts_a)
    h_euro    = in_euro_fight(pos_h, pts_h)
    a_euro    = in_euro_fight(pos_a, pts_a)
    h_rel     = in_relegation_fight(pos_h, pts_h)
    a_rel     = in_relegation_fight(pos_a, pts_a)

    # ── Score the fixture ──────────────────────────────────────────────────────

    # Title decider — top two, very tight
    if h_title and a_title and pos_h <= 2 and pos_a <= 2:
        return 95.0

    # Both in title race
    if h_title and a_title:
        return 85.0

    # One side chasing the title
    if h_title or a_title:
        return 75.0

    # Both fighting for European spots
    if h_euro and a_euro:
        return 70.0

    # Both in relegation danger
    if h_rel and a_rel:
        return 78.0

    # One side in relegation trouble
    if h_rel or a_rel:
        return 65.0

    # One side in European fight
    if h_euro or a_euro:
        return 60.0

    # Neither side has much at stake — dead rubber
    return 30.0


# ── Private helpers ────────────────────────────────────────────────────────────

def _fetch_league_standings(league_code: str) -> Dict[str, Dict]:
    """
    Fetch and parse standings for a single ESPN league.
    Returns a dict keyed by lowercased team name.
    """
    url = ESPN_URL.format(league_code=league_code)
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    return _parse_espn_standings(soup)


def _parse_espn_standings(soup: BeautifulSoup) -> Dict[str, Dict]:
    """
    Parse ESPN's standings page HTML into a standings dict.

    ESPN renders two side-by-side tables:
      - Left table:  team names (with club abbreviation + full name links)
      - Right table: statistics (GP, W, D, L, F, A, GD, P)

    We zip the rows from both tables to build the full standings.
    """
    standings = {}

    # ESPN uses two adjacent tables — find all Table__tbody elements
    tables = soup.find_all("tbody", class_=lambda c: c and "Table__tbody" in c)

    if len(tables) < 2:
        logger.debug("Could not find ESPN standings tables in HTML")
        return standings

    name_rows = tables[0].find_all("tr")
    stat_rows = tables[1].find_all("tr")

    if not name_rows or not stat_rows:
        return standings

    total_teams = len(name_rows)
    leader_pts = None

    rows = list(zip(name_rows, stat_rows))
    for i, (name_row, stat_row) in enumerate(rows):
        position = i + 1

        # Extract team name — ESPN has two <a> tags per row: short code and full name
        # We want the full name (second link, or the one with longer text)
        links = name_row.find_all("a")
        team_name = None
        for link in links:
            text = link.get_text(strip=True)
            # Skip abbreviations (usually 3 chars like "ARS", "MCI")
            if len(text) > 4:
                team_name = text
                break

        if not team_name:
            # Fall back to any text in the row
            team_name = name_row.get_text(separator=" ", strip=True)
            if not team_name:
                continue

        # Extract statistics — columns: GP, W, D, L, F, A, GD, P
        cells = stat_row.find_all("td")
        if len(cells) < 8:
            continue

        try:
            played = int(cells[0].get_text(strip=True))
            points = int(cells[7].get_text(strip=True))
        except (ValueError, IndexError):
            continue

        if leader_pts is None:
            leader_pts = points  # First row is the leader

        standings[team_name.lower()] = {
            "position":    position,
            "points":      points,
            "played":      played,
            "total_teams": total_teams,
            "leader_pts":  leader_pts,
            # Keep original casing for display/debugging
            "display_name": team_name,
        }

    return standings
