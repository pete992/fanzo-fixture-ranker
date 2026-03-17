"""
tests/test_enrichment.py
========================
Tests for enrichment.py — live standings scraping and live stakes calculation.

All ESPN network calls are mocked so tests run offline.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enrichment import get_team_standing, calculate_live_stakes


# ── Fixtures (test data, not football fixtures) ───────────────────────────────

def make_standings(entries):
    """
    Build a mock standings dict from a list of (name, position, points, total) tuples.
    Leader points is inferred from the team at position 1.
    """
    standings = {}
    # Find the leader's points
    leader_pts = max(pts for _, _, pts, _ in entries)
    total = entries[0][3] if entries else 20

    for name, position, points, total_teams in entries:
        standings[name.lower()] = {
            "position":    position,
            "points":      points,
            "played":      position * 2,     # Arbitrary for tests
            "total_teams": total_teams,
            "leader_pts":  leader_pts,
            "display_name": name,
        }
    return standings


# ── get_team_standing ─────────────────────────────────────────────────────────

class TestGetTeamStanding:

    def test_exact_match(self):
        standings = make_standings([("Arsenal", 1, 70, 20)])
        result = get_team_standing("Arsenal", standings)
        assert result is not None
        assert result["position"] == 1

    def test_case_insensitive(self):
        standings = make_standings([("Arsenal", 1, 70, 20)])
        result = get_team_standing("ARSENAL", standings)
        assert result is not None

    def test_partial_match(self):
        standings = make_standings([("Manchester City", 1, 70, 20)])
        # "manchester" is contained within "manchester city" — partial match
        result = get_team_standing("Manchester", standings)
        assert result is not None

    def test_returns_none_for_unknown_team(self):
        standings = make_standings([("Arsenal", 1, 70, 20)])
        result = get_team_standing("Obscure FC", standings)
        assert result is None

    def test_returns_none_for_empty_standings(self):
        result = get_team_standing("Arsenal", {})
        assert result is None

    def test_returns_none_for_empty_team_name(self):
        standings = make_standings([("Arsenal", 1, 70, 20)])
        result = get_team_standing("", standings)
        assert result is None


# ── calculate_live_stakes ─────────────────────────────────────────────────────

class TestCalculateLiveStakes:

    def test_title_decider(self):
        """First vs second, very tight — maximum league stakes."""
        standings = make_standings([
            ("Arsenal", 1, 70, 20),
            ("Manchester City", 2, 68, 20),
        ])
        score = calculate_live_stakes("Arsenal", "Manchester City", standings, "Premier League")
        assert score == 95.0

    def test_both_in_title_race(self):
        """Both in top 4, within 10 points."""
        standings = make_standings([
            ("Arsenal",  1, 70, 20),
            ("Liverpool", 4, 62, 20),
        ])
        score = calculate_live_stakes("Arsenal", "Liverpool", standings, "Premier League")
        assert score == 85.0

    def test_one_in_title_race(self):
        """Only one side chasing the title."""
        standings = make_standings([
            ("Arsenal",    1, 70, 20),
            ("Sunderland", 12, 38, 20),
        ])
        score = calculate_live_stakes("Arsenal", "Sunderland", standings, "Premier League")
        assert score == 75.0

    def test_both_in_relegation_fight(self):
        """Both teams in the bottom 6."""
        standings = make_standings([
            ("Team A", 1, 70, 20),   # leader (for leader_pts)
            ("Everton",  16, 26, 20),
            ("Wolves",   17, 24, 20),
        ])
        score = calculate_live_stakes("Everton", "Wolves", standings, "Premier League")
        assert score == 78.0

    def test_one_in_relegation_fight(self):
        """One side safe, one fighting relegation."""
        standings = make_standings([
            ("Team A",     1, 70, 20),
            ("Wolves",   17, 24, 20),
            ("Newcastle",  8, 45, 20),
        ])
        score = calculate_live_stakes("Wolves", "Newcastle", standings, "Premier League")
        assert score == 65.0

    def test_dead_rubber_mid_table(self):
        """Both teams safely mid-table — low stakes."""
        standings = make_standings([
            ("Team A",    1, 70, 20),
            ("Everton",  11, 40, 20),
            ("Sunderland", 12, 38, 20),
        ])
        score = calculate_live_stakes("Everton", "Sunderland", standings, "Premier League")
        assert score == 30.0

    def test_returns_none_for_european_competition(self):
        """Live stakes should not override CL knockout stage detection."""
        standings = make_standings([("Arsenal", 1, 70, 20)])
        score = calculate_live_stakes("Arsenal", "Real Madrid", standings, "UEFA Champions League")
        assert score is None

    def test_returns_none_for_unknown_teams(self):
        """Falls back gracefully if teams aren't in standings."""
        standings = make_standings([("Arsenal", 1, 70, 20)])
        score = calculate_live_stakes("Unknown FC", "Other FC", standings, "Premier League")
        assert score is None

    def test_returns_none_for_empty_standings(self):
        """Empty standings = fall back to keyword inference."""
        score = calculate_live_stakes("Arsenal", "Chelsea", {}, "Premier League")
        assert score is None
