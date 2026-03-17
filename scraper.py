"""
scraper.py
==========
Fetches the fixture pool from https://www.fanzo.com/en.

FANZO embeds a JSON-LD (schema.org) block in the page containing all upcoming
UK-televised fixtures as SportsEvent objects. This is much more reliable than
HTML scraping — it's structured data intended for search engines, so it's
unlikely to change format without notice.

The scraper:
  1. GETs https://www.fanzo.com/en
  2. Finds the <script type="application/ld+json"> tag(s)
  3. Parses any ItemList or SportsEvent objects
  4. Filters to events starting within the next 7 days (Today + 6 date tabs)
  5. Ignores the "Big Fixtures" editorial selection — we rank everything ourselves

Returns a list of fixture dicts ready for the scoring pipeline.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Union

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# The FANZO page to scrape
FANZO_URL = "https://www.fanzo.com/en"

# Mimic a real browser so we don't get blocked
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}

# Request timeout in seconds
REQUEST_TIMEOUT = 20


def fetch_fanzo_fixtures() -> List[Dict]:
    """
    Scrape FANZO and return a list of fixture dicts for the next 7 days.

    Each dict contains:
        name         (str)       — e.g. "Arsenal vs Leverkusen"
        home_team    (str)       — e.g. "Arsenal"
        away_team    (str)       — e.g. "Leverkusen"
        competition  (str)       — e.g. "UEFA Champions League"
        sport        (str)       — e.g. "Football"
        kickoff      (datetime)  — timezone-aware UTC datetime
        channels     (list[str]) — e.g. ["TNT Sports", "TNT Sports 1"]
        fanzo_url    (str)       — full URL to the FANZO fixture page

    Raises:
        requests.RequestException — if the page cannot be fetched
        ValueError                — if no JSON-LD data can be found on the page
    """
    logger.info("Fetching fixtures from %s", FANZO_URL)
    response = requests.get(FANZO_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    events = _extract_events_from_json_ld(soup)

    if not events:
        raise ValueError(
            "No SportsEvent data found in FANZO page JSON-LD. "
            "The page structure may have changed."
        )

    # Filter to the next 7 days starting from now (UTC)
    # This corresponds to the "Today" tab plus the next 6 date tabs on FANZO,
    # deliberately excluding the "Big Fixtures" editorial tab.
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=7)

    fixtures = []
    for event in events:
        fixture = _parse_event(event)
        if fixture and now <= fixture["kickoff"] <= window_end:
            fixtures.append(fixture)

    logger.info("Found %d fixtures in the next 7 days", len(fixtures))
    return fixtures


# ── Private helpers ────────────────────────────────────────────────────────────

def _extract_events_from_json_ld(soup: BeautifulSoup) -> List[Dict]:
    """
    Find all <script type="application/ld+json"> tags and extract
    every SportsEvent object from them, whether they appear directly
    or nested inside an ItemList.
    """
    events = []
    scripts = soup.find_all("script", type="application/ld+json")

    for script in scripts:
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            logger.debug("Skipping malformed JSON-LD block")
            continue

        events.extend(_collect_sports_events(data))

    return events


def _collect_sports_events(data: Union[Dict, List]) -> List[Dict]:
    """
    Recursively collect all SportsEvent objects from a JSON-LD structure.
    Handles top-level SportsEvent, ItemList containing SportsEvents,
    and nested graph structures.
    """
    found = []

    if isinstance(data, list):
        for item in data:
            found.extend(_collect_sports_events(item))
        return found

    if not isinstance(data, dict):
        return found

    schema_type = data.get("@type", "")

    if schema_type == "SportsEvent":
        found.append(data)

    elif schema_type == "ItemList":
        for list_item in data.get("itemListElement", []):
            if isinstance(list_item, dict):
                # Items may be wrapped in a ListItem with an "item" key
                inner = list_item.get("item", list_item)
                found.extend(_collect_sports_events(inner))

    elif schema_type == "@graph" or "@graph" in data:
        for node in data.get("@graph", []):
            found.extend(_collect_sports_events(node))

    return found


def _parse_event(event: Dict) -> Optional[Dict]:
    """
    Convert a raw SportsEvent JSON-LD dict into a clean fixture dict.
    Returns None if essential fields (kickoff time) are missing.
    """
    try:
        kickoff = _parse_datetime(event.get("startDate", ""))
        if kickoff is None:
            return None

        home_team = _extract_team_name(event.get("homeTeam"))
        away_team = _extract_team_name(event.get("awayTeam"))
        name = event.get("name") or f"{home_team} vs {away_team}"
        sport = event.get("sport", "Unknown")
        competition = _extract_competition(event.get("description", ""), name)
        channels = _extract_channels(event)

        # Build the FANZO fixture URL
        raw_url = event.get("url", "")
        fanzo_url = (
            "https://www.fanzo.com{}".format(raw_url)
            if raw_url.startswith("/")
            else raw_url
        )

        return {
            "name": name,
            "home_team": home_team,
            "away_team": away_team,
            "competition": competition,
            "sport": sport,
            "kickoff": kickoff,
            "channels": channels,
            "fanzo_url": fanzo_url,
        }

    except Exception as exc:
        logger.debug("Failed to parse event %s: %s", event.get("name", "?"), exc)
        return None


def _extract_team_name(team_data) -> str:
    """Extract a team name from a homeTeam/awayTeam field (string or dict)."""
    if isinstance(team_data, dict):
        return team_data.get("name", "Unknown")
    if isinstance(team_data, str):
        return team_data
    return "Unknown"


def _extract_competition(description: str, name: str) -> str:
    """
    Parse the competition name from the FANZO description string.

    FANZO description format:
        "Team A vs Team B, Competition Name - Day DD Mon - HH:MM"

    Example:
        "Arsenal vs Leverkusen, UEFA Champions League - Tue 17 Mar - 20:00"
        → "UEFA Champions League"
    """
    if description and "," in description:
        # Everything after the first comma, before the first " - "
        after_comma = description.split(",", 1)[1].strip()
        if " - " in after_comma:
            competition = after_comma.split(" - ")[0].strip()
            if competition:
                return competition

    return "Unknown Competition"


def _extract_channels(event: Dict) -> List[str]:
    """
    Extract broadcast channel names from a SportsEvent JSON-LD dict.

    Channels are nested under event → subEvent → publishedOn[].broadcastDisplayName.
    Handles both single objects and lists at each level.
    """
    channels = []

    sub_event = event.get("subEvent")
    if not sub_event:
        return channels

    # subEvent may be a single dict or a list
    sub_events = sub_event if isinstance(sub_event, list) else [sub_event]

    for se in sub_events:
        if not isinstance(se, dict):
            continue
        published_on = se.get("publishedOn", [])
        if isinstance(published_on, dict):
            published_on = [published_on]
        for service in published_on:
            if isinstance(service, dict):
                display_name = service.get("broadcastDisplayName", "").strip()
                if display_name and display_name not in channels:
                    channels.append(display_name)

    return channels


def _parse_datetime(dt_string: str) -> Optional[datetime]:
    """
    Parse an ISO 8601 datetime string into a timezone-aware UTC datetime.
    Returns None if the string is empty or unparseable.
    """
    if not dt_string:
        return None
    try:
        # Python's fromisoformat handles "+00:00" but not "Z" before 3.11
        normalised = dt_string.replace("Z", "+00:00")
        return datetime.fromisoformat(normalised)
    except ValueError:
        logger.debug("Could not parse datetime string: %s", dt_string)
        return None
