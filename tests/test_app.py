"""
tests/test_app.py
=================
Integration tests for the Flask application routes.

Tests the /run endpoint with mocked pipeline functions to verify:
  - Correct HTTP status codes
  - Response JSON structure
  - Error handling
"""

import sys
import os
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app


@pytest.fixture
def client():
    """Create a Flask test client."""
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


def make_ranked_fixture(rank=1, name="Arsenal vs Tottenham", score=82.5):
    """Build a minimal ranked fixture dict (as returned by rank_fixtures)."""
    return {
        "rank": rank,
        "name": name,
        "home_team": "Arsenal",
        "away_team": "Tottenham",
        "competition": "Premier League",
        "sport": "Football",
        "kickoff": datetime(2026, 3, 21, 15, 0, 0, tzinfo=timezone.utc),
        "channels": ["Sky Sports Premier League"],
        "composite_score": score,
        "sub_scores": {
            "competition_tier": 85.0,
            "match_stakes": 55.0,
            "derby_rivalry": 100.0,
            "team_popularity": 84.0,
            "kickoff_time": 100.0,
            "betting_volume": 68.0,
        },
        "rationale": "Top-tier Premier League fixture — a genuine derby/rivalry fixture.",
        "fanzo_url": "https://www.fanzo.com/en/bars-showing/12345/arsenal-vs-tottenham",
    }


# ── Index route tests ─────────────────────────────────────────────────────────

class TestIndexRoute:
    def test_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_returns_html(self, client):
        response = client.get("/")
        assert b"FANZO" in response.data

    def test_contains_run_button(self, client):
        response = client.get("/")
        assert b"run-btn" in response.data or b"runPipeline" in response.data


# ── /run route tests ──────────────────────────────────────────────────────────

class TestRunRoute:
    def test_returns_200_on_success(self, client):
        fixtures = [make_ranked_fixture()]
        with patch("app.fetch_fanzo_fixtures", return_value=[{}]):
            with patch("app.rank_fixtures", return_value=fixtures):
                response = client.post("/run")
        assert response.status_code == 200

    def test_response_has_fixtures_key(self, client):
        fixtures = [make_ranked_fixture()]
        with patch("app.fetch_fanzo_fixtures", return_value=[{}]):
            with patch("app.rank_fixtures", return_value=fixtures):
                response = client.post("/run")
        data = response.get_json()
        assert "fixtures" in data

    def test_fixture_has_required_fields(self, client):
        fixtures = [make_ranked_fixture()]
        with patch("app.fetch_fanzo_fixtures", return_value=[{}]):
            with patch("app.rank_fixtures", return_value=fixtures):
                response = client.post("/run")
        data = response.get_json()
        f = data["fixtures"][0]
        required = [
            "rank", "name", "home_team", "away_team", "competition",
            "sport", "kickoff_display", "channels", "composite_score",
            "sub_scores", "rationale",
        ]
        for field in required:
            assert field in f, f"Missing field: {field}"

    def test_kickoff_is_formatted_string(self, client):
        fixtures = [make_ranked_fixture()]
        with patch("app.fetch_fanzo_fixtures", return_value=[{}]):
            with patch("app.rank_fixtures", return_value=fixtures):
                response = client.post("/run")
        data = response.get_json()
        kickoff = data["fixtures"][0]["kickoff_display"]
        assert isinstance(kickoff, str)
        assert "UK" in kickoff

    def test_returns_500_when_scraper_fails(self, client):
        with patch("app.fetch_fanzo_fixtures", side_effect=Exception("Scrape failed")):
            response = client.post("/run")
        assert response.status_code == 500

    def test_error_response_has_error_key(self, client):
        with patch("app.fetch_fanzo_fixtures", side_effect=Exception("Scrape failed")):
            response = client.post("/run")
        data = response.get_json()
        assert "error" in data

    def test_returns_500_when_no_fixtures_found(self, client):
        with patch("app.fetch_fanzo_fixtures", return_value=[]):
            response = client.post("/run")
        assert response.status_code == 500

    def test_multiple_fixtures_returned(self, client):
        fixtures = [make_ranked_fixture(rank=i, name=f"Match {i}") for i in range(1, 6)]
        with patch("app.fetch_fanzo_fixtures", return_value=[{}] * 5):
            with patch("app.rank_fixtures", return_value=fixtures):
                response = client.post("/run")
        data = response.get_json()
        assert len(data["fixtures"]) == 5

    def test_only_post_method_accepted(self, client):
        """The /run endpoint should not respond to GET requests."""
        response = client.get("/run")
        assert response.status_code == 405  # Method Not Allowed
