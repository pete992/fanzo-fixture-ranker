"""
tests/test_scraper.py
=====================
Unit tests for scraper.py.

All tests mock the FANZO API — no real network calls are made.
"""

import sys
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import fetch_fanzo_fixtures, _parse_datetime


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_api_item(
    fixture_id=12345,
    name="Arsenal vs Leverkusen",
    start="2026-03-17T20:00:00.000000Z",
    home="Arsenal",
    away="Leverkusen",
    competition="UEFA Champions League",
    sport="Football",
):
    """Build a minimal FANZO API fixture item."""
    return {
        "id": fixture_id,
        "name": name,
        "schedule": {"start": start, "end": start},
        "sport": {"id": 21, "name": sport},
        "competition": {"id": 1, "name": competition},
        "teams": {
            "home": {"id": 1, "name": home},
            "away": {"id": 2, "name": away},
        },
        "channels": [],
    }


def make_api_response(items, current_page=1, last_page=1, total=None):
    """Build a minimal FANZO API paginated response."""
    if total is None:
        total = len(items)
    return {
        "data": items,
        "meta": {
            "current_page": current_page,
            "last_page": last_page,
            "per_page": 50,
            "total": total,
        },
        "links": {},
    }


def make_mock_response(items, current_page=1, last_page=1):
    """Create a mock requests.Response returning a FANZO API JSON payload."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = make_api_response(items, current_page, last_page)
    return mock_resp


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

    def test_parses_fractional_seconds(self):
        dt = _parse_datetime("2026-03-17T20:00:00.000000Z")
        assert dt is not None
        assert dt.hour == 20

    def test_returns_none_for_empty_string(self):
        assert _parse_datetime("") is None

    def test_returns_none_for_invalid_string(self):
        assert _parse_datetime("not-a-date") is None

    def test_datetime_is_timezone_aware(self):
        dt = _parse_datetime("2026-03-17T20:00:00+00:00")
        assert dt.tzinfo is not None


# ── fetch_fanzo_fixtures tests ─────────────────────────────────────────────────

class TestFetchFanzoFixtures:

    def _future(self, days=2):
        return (datetime.now(timezone.utc) + timedelta(days=days)).strftime(
            "%Y-%m-%dT%H:%M:%S.000000Z"
        )

    def _past(self, days=1):
        return (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
            "%Y-%m-%dT%H:%M:%S.000000Z"
        )

    def test_returns_upcoming_fixtures(self):
        item = make_api_item(start=self._future(2))
        with patch.dict(os.environ, {"FANZO_API_KEY": "test-key"}):
            with patch("scraper.requests.get", return_value=make_mock_response([item])):
                fixtures = fetch_fanzo_fixtures()
        assert len(fixtures) == 1
        assert fixtures[0]["name"] == "Arsenal vs Leverkusen"

    def test_excludes_past_fixtures(self):
        item = make_api_item(start=self._past(1))
        with patch.dict(os.environ, {"FANZO_API_KEY": "test-key"}):
            with patch("scraper.requests.get", return_value=make_mock_response([item])):
                with pytest.raises(ValueError):
                    fetch_fanzo_fixtures()

    def test_stops_at_window_end(self):
        near = make_api_item(fixture_id=1, name="Near Match", start=self._future(2))
        far = make_api_item(fixture_id=2, name="Far Match", start=self._future(25))
        with patch.dict(os.environ, {"FANZO_API_KEY": "test-key"}):
            with patch("scraper.requests.get", return_value=make_mock_response([near, far])):
                fixtures = fetch_fanzo_fixtures()
        assert len(fixtures) == 1
        assert fixtures[0]["name"] == "Near Match"

    def test_fixture_has_correct_fields(self):
        item = make_api_item(start=self._future(2))
        with patch.dict(os.environ, {"FANZO_API_KEY": "test-key"}):
            with patch("scraper.requests.get", return_value=make_mock_response([item])):
                fixtures = fetch_fanzo_fixtures()
        f = fixtures[0]
        assert f["name"] == "Arsenal vs Leverkusen"
        assert f["home_team"] == "Arsenal"
        assert f["away_team"] == "Leverkusen"
        assert f["competition"] == "UEFA Champions League"
        assert f["sport"] == "Football"
        assert isinstance(f["kickoff"], datetime)
        assert isinstance(f["channels"], list)
        assert "fanzo_url" in f

    def test_fanzo_url_contains_fixture_id(self):
        item = make_api_item(fixture_id=99999, start=self._future(2))
        with patch.dict(os.environ, {"FANZO_API_KEY": "test-key"}):
            with patch("scraper.requests.get", return_value=make_mock_response([item])):
                fixtures = fetch_fanzo_fixtures()
        assert "99999" in fixtures[0]["fanzo_url"]

    def test_raises_when_no_api_key(self):
        env = os.environ.copy()
        env.pop("FANZO_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="FANZO_API_KEY"):
                fetch_fanzo_fixtures()

    def test_raises_when_no_fixtures_found(self):
        with patch.dict(os.environ, {"FANZO_API_KEY": "test-key"}):
            with patch("scraper.requests.get", return_value=make_mock_response([])):
                with pytest.raises(ValueError):
                    fetch_fanzo_fixtures()

    def test_paginates_multiple_pages(self):
        item1 = make_api_item(fixture_id=1, name="Match A", start=self._future(2))
        item2 = make_api_item(fixture_id=2, name="Match B", start=self._future(3))
        responses = [
            make_mock_response([item1], current_page=1, last_page=2),
            make_mock_response([item2], current_page=2, last_page=2),
        ]
        with patch.dict(os.environ, {"FANZO_API_KEY": "test-key"}):
            with patch("scraper.requests.get", side_effect=responses):
                fixtures = fetch_fanzo_fixtures()
        assert len(fixtures) == 2

    def test_kickoff_is_timezone_aware(self):
        item = make_api_item(start=self._future(2))
        with patch.dict(os.environ, {"FANZO_API_KEY": "test-key"}):
            with patch("scraper.requests.get", return_value=make_mock_response([item])):
                fixtures = fetch_fanzo_fixtures()
        assert fixtures[0]["kickoff"].tzinfo is not None

    def test_skips_item_with_missing_kickoff(self):
        bad_item = make_api_item(start="not-a-date")
        good_item = make_api_item(fixture_id=2, name="Good Match", start=self._future(2))
        with patch.dict(os.environ, {"FANZO_API_KEY": "test-key"}):
            with patch("scraper.requests.get", return_value=make_mock_response([bad_item, good_item])):
                fixtures = fetch_fanzo_fixtures()
        assert len(fixtures) == 1
        assert fixtures[0]["name"] == "Good Match"
