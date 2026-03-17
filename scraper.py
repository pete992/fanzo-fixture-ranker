"""
scraper.py
==========
Fetches the fixture pool from the official FANZO API.

Calls https://api.fanzo.com/v1/fixtures with pagination, collecting all
fixtures kicking off within the next 14 days. The API returns every sport
globally — the scoring model handles ranking, so no pre-filtering by channel
or country is needed. Unimportant fixtures (Turkish league, League Two etc.)
will naturally score low and won't appear in the top 20.

The FANZO_API_KEY is read from the FANZO_API_KEY environment variable.
Never hardcode the key in this file.
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

FANZO_API_URL = "https://api.fanzo.com/v1/fixtures"
WINDOW_DAYS = 14
REQUEST_TIMEOUT = 20

# Fixture names to exclude — broadcast formats, not real sporting events
_EXCLUDED_NAMES = {"multiplex"}


def fetch_fanzo_fixtures() -> List[Dict]:
    """
    Call the FANZO fixtures API and return all fixtures in the next 14 days.

    Paginates automatically until all pages are exhausted or we pass the
    14-day window, whichever comes first.

    Each returned dict contains:
        name         (str)       — e.g. "Arsenal vs Leverkusen"
        home_team    (str)       — e.g. "Arsenal"
        away_team    (str)       — e.g. "Leverkusen"
        competition  (str)       — e.g. "UEFA Champions League"
        sport        (str)       — e.g. "Football"
        kickoff      (datetime)  — timezone-aware UTC datetime
        channels     (list[str]) — broadcast channels (may be empty)
        fanzo_url    (str)       — link to the FANZO fixture page

    Raises:
        requests.RequestException — if the API cannot be reached
        ValueError                — if no fixtures are found
    """
    api_key = os.getenv("FANZO_API_KEY")
    if not api_key:
        raise ValueError(
            "FANZO_API_KEY environment variable is not set. "
            "Add it to your .env file or Render environment variables."
        )

    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=WINDOW_DAYS)
    fixtures: List[Dict] = []
    page = 1

    logger.info("Fetching fixtures from FANZO API (next %d days)", WINDOW_DAYS)

    while True:
        params = {
            "apiKey": api_key,
            "limit": 50,
            "page": page,
            "localTimezone": "Europe/London",
        }
        response = requests.get(FANZO_API_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        items = data.get("data", [])
        meta = data.get("meta", {})

        for item in items:
            kickoff = _parse_datetime(item.get("schedule", {}).get("start", ""))
            if kickoff is None:
                continue
            # Past the window — API is chronological, so we can stop
            if kickoff > window_end:
                logger.info("Reached end of %d-day window at page %d", WINDOW_DAYS, page)
                return fixtures
            # Skip fixtures that have already kicked off
            if kickoff < now:
                continue
            # Skip non-fixture broadcast formats
            name = item.get("name") or ""
            if name.lower() in _EXCLUDED_NAMES:
                continue
            teams = item.get("teams") or {}
            fixtures.append({
                "name":        item.get("name") or "Unknown",
                "home_team":   (teams.get("home") or {}).get("name") or "Unknown",
                "away_team":   (teams.get("away") or {}).get("name") or "Unknown",
                "competition": (item.get("competition") or {}).get("name") or "Unknown Competition",
                "sport":       (item.get("sport") or {}).get("name") or "Unknown",
                "kickoff":     kickoff,
                "channels":    item.get("channels") or [],
                "fanzo_url":   f"https://www.fanzo.com/en/fixture/{item.get('id', '')}",
            })

        last_page = meta.get("last_page", 1)
        logger.info("Fetched page %d/%d — %d fixtures so far", page, last_page, len(fixtures))

        if page >= last_page:
            break
        page += 1

    if not fixtures:
        raise ValueError(
            "No upcoming fixtures found in the FANZO API response. "
            "The API may be unavailable or have no fixtures in the next "
            f"{WINDOW_DAYS} days."
        )

    logger.info("Total fixtures fetched: %d", len(fixtures))
    return fixtures


def _parse_datetime(dt_string: str) -> Optional[datetime]:
    """
    Parse an ISO 8601 datetime string into a timezone-aware UTC datetime.
    Returns None if the string is empty or unparseable.
    """
    if not dt_string:
        return None
    try:
        normalised = dt_string.replace("Z", "+00:00")
        return datetime.fromisoformat(normalised)
    except ValueError:
        logger.debug("Could not parse datetime string: %s", dt_string)
        return None
