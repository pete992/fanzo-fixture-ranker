"""
tests/test_scraper.py
=====================
Unit tests for scraper.py.

We test the parsing and filtering logic using mocked HTML responses —
no real network calls are made. This keeps the tests fast and reliable.
"""

import sys
import os
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import (
    fetch_fanzo_fixtures,
    _extract_events_from_json_ld,
    _parse_event,
    _extract_competition,
    _extract_channels,
    _parse_datetime,
)
from bs4 import BeautifulSoup


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_sports_event(
    name="Arsenal vs Leverkusen",
    start_date="2026-03-17T20:00:00+00:00",
    sport="Football",
    home_team="Arsenal",
    away_team="Leverkusen",
    description=None,
    channels=None,
    url="/en/bars-showing/12345/arsenal-vs-leverkusen",
):
    """Build a minimal SportsEvent JSON-LD dict."""
    if description is None:
        description = f"{name}, UEFA Champions League - Tue 17 Mar - 20:00"
    if channels is None:
        channels = ["TNT Sports", "TNT Sports 1"]

    return {
        "@type": "SportsEvent",
        "name": name,
        "description": description,
        "startDate": start_date,
        "sport": sport,
        "homeTeam": {"@type": "SportsTeam", "name": home_team},
        "awayTeam": {"@type": "SportsTeam", "name": away_team},
        "url": url,
        "subEvent": {
            "@type": "BroadcastEvent",
            "publishedOn": [
                {"@type": "BroadcastService", "broadcastDisplayName": ch}
                for ch in channels
            ],
        },
    }


def make_html_with_json_ld(data: dict) -> str:
    """Wrap a JSON-LD dict in a minimal HTML page."""
    return f"""
    <html><head>
    <script type="application/ld+json">{json.dumps(data)}</script>
    </head><body></body></html>
    """


# ── _parse_datetime tests ─────────────────────────────────────────────────────

class TestParseDatetime:
    def test_parses_utc_plus_zero(self):
        dt = _parse_datetime("2026-03-17T20:00:00+00:00")
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 3
        assert dt.day == 17
        assert dt.hour == 20

    def test_parses_z_suffix(self):
        dt = _parse_datetime("2026-03-17T20:00:00Z")
        assert dt is not None
        assert dt.tzinfo is not None

    def test_returns_none_for_empty_string(self):
        assert _parse_datetime("") is None

    def test_returns_none_for_invalid_string(self):
        assert _parse_datetime("not-a-date") is None

    def test_datetime_is_timezone_aware(self):
        dt = _parse_datetime("2026-03-17T20:00:00+00:00")
        assert dt.tzinfo is not None


# ── _extract_competition tests ─────────────────────────────────────────────────

class TestExtractCompetition:
    def test_standard_fanzo_format(self):
        desc = "Arsenal vs Leverkusen, UEFA Champions League - Tue 17 Mar - 20:00"
        comp = _extract_competition(desc, "Arsenal vs Leverkusen")
        assert comp == "UEFA Champions League"

    def test_premier_league(self):
        desc = "Brighton vs Liverpool, Premier League - Fri 21 Mar - 12:30"
        comp = _extract_competition(desc, "Brighton vs Liverpool")
        assert comp == "Premier League"

    def test_no_comma_falls_back(self):
        comp = _extract_competition("No comma here", "Some Match")
        assert comp == "Unknown Competition"

    def test_empty_description_falls_back(self):
        comp = _extract_competition("", "Some Match")
        assert comp == "Unknown Competition"


# ── _extract_channels tests ───────────────────────────────────────────────────

class TestExtractChannels:
    def test_extracts_multiple_channels(self):
        event = make_sports_event(channels=["TNT Sports", "TNT Sports 1"])
        channels = _extract_channels(event)
        assert "TNT Sports" in channels
        assert "TNT Sports 1" in channels

    def test_no_sub_event_returns_empty(self):
        event = {"@type": "SportsEvent", "name": "Test"}
        assert _extract_channels(event) == []

    def test_deduplicates_channels(self):
        event = make_sports_event(channels=["Sky Sports", "Sky Sports", "BBC"])
        channels = _extract_channels(event)
        assert channels.count("Sky Sports") == 1

    def test_single_channel(self):
        event = make_sports_event(channels=["ITV 1"])
        channels = _extract_channels(event)
        assert channels == ["ITV 1"]


# ── _parse_event tests ────────────────────────────────────────────────────────

class TestParseEvent:
    def test_parses_standard_event(self):
        event = make_sports_event()
        fixture = _parse_event(event)
        assert fixture is not None
        assert fixture["name"] == "Arsenal vs Leverkusen"
        assert fixture["home_team"] == "Arsenal"
        assert fixture["away_team"] == "Leverkusen"
        assert fixture["sport"] == "Football"
        assert fixture["competition"] == "UEFA Champions League"
        assert len(fixture["channels"]) == 2

    def test_kickoff_is_datetime(self):
        event = make_sports_event()
        fixture = _parse_event(event)
        assert isinstance(fixture["kickoff"], datetime)

    def test_fanzo_url_constructed_correctly(self):
        event = make_sports_event(url="/en/bars-showing/12345/test")
        fixture = _parse_event(event)
        assert fixture["fanzo_url"] == "https://www.fanzo.com/en/bars-showing/12345/test"

    def test_returns_none_for_missing_start_date(self):
        event = make_sports_event()
        del event["startDate"]
        assert _parse_event(event) is None

    def test_returns_none_for_invalid_start_date(self):
        event = make_sports_event(start_date="not-a-date")
        assert _parse_event(event) is None

    def test_handles_string_team_names(self):
        """homeTeam/awayTeam can be plain strings instead of dicts."""
        event = make_sports_event()
        event["homeTeam"] = "Arsenal"
        event["awayTeam"] = "Leverkusen"
        fixture = _parse_event(event)
        assert fixture["home_team"] == "Arsenal"
        assert fixture["away_team"] == "Leverkusen"


# ── _extract_events_from_json_ld tests ───────────────────────────────────────

class TestExtractEvents:
    def test_extracts_from_item_list(self):
        event = make_sports_event()
        data = {
            "@type": "ItemList",
            "itemListElement": [event],
        }
        html = make_html_with_json_ld(data)
        soup = BeautifulSoup(html, "html.parser")
        events = _extract_events_from_json_ld(soup)
        assert len(events) == 1
        assert events[0]["name"] == "Arsenal vs Leverkusen"

    def test_extracts_direct_sports_event(self):
        event = make_sports_event()
        html = make_html_with_json_ld(event)
        soup = BeautifulSoup(html, "html.parser")
        events = _extract_events_from_json_ld(soup)
        assert len(events) == 1

    def test_handles_malformed_json(self):
        html = '<html><head><script type="application/ld+json">{invalid json</script></head></html>'
        soup = BeautifulSoup(html, "html.parser")
        # Should not raise — just returns empty list
        events = _extract_events_from_json_ld(soup)
        assert events == []

    def test_handles_no_json_ld_tags(self):
        soup = BeautifulSoup("<html><body>No data</body></html>", "html.parser")
        events = _extract_events_from_json_ld(soup)
        assert events == []

    def test_extracts_multiple_events(self):
        events_data = [make_sports_event(name=f"Match {i}") for i in range(3)]
        data = {
            "@type": "ItemList",
            "itemListElement": events_data,
        }
        html = make_html_with_json_ld(data)
        soup = BeautifulSoup(html, "html.parser")
        events = _extract_events_from_json_ld(soup)
        assert len(events) == 3


# ── fetch_fanzo_fixtures integration test (mocked) ───────────────────────────

class TestFetchFanzoFixtures:
    def _make_mock_response(self, events: list, status_code=200):
        """Create a mock requests.Response containing the given events."""
        data = {"@type": "ItemList", "itemListElement": events}
        html = make_html_with_json_ld(data)
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    def test_returns_fixtures_in_next_7_days(self):
        now = datetime.now(timezone.utc)
        future = (now + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        event = make_sports_event(start_date=future)

        with patch("scraper.requests.get", return_value=self._make_mock_response([event])):
            fixtures = fetch_fanzo_fixtures()

        assert len(fixtures) == 1

    def test_excludes_fixtures_beyond_7_days(self):
        now = datetime.now(timezone.utc)
        far_future = (now + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        event = make_sports_event(start_date=far_future)

        with patch("scraper.requests.get", return_value=self._make_mock_response([event])):
            fixtures = fetch_fanzo_fixtures()

        assert len(fixtures) == 0

    def test_excludes_past_fixtures(self):
        now = datetime.now(timezone.utc)
        past = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        event = make_sports_event(start_date=past)

        with patch("scraper.requests.get", return_value=self._make_mock_response([event])):
            fixtures = fetch_fanzo_fixtures()

        assert len(fixtures) == 0

    def test_raises_value_error_when_no_events(self):
        """Should raise ValueError if the page has no JSON-LD event data."""
        mock_resp = MagicMock()
        mock_resp.text = "<html><body>No data</body></html>"
        mock_resp.raise_for_status = MagicMock()

        with patch("scraper.requests.get", return_value=mock_resp):
            with pytest.raises(ValueError, match="No SportsEvent data found"):
                fetch_fanzo_fixtures()
