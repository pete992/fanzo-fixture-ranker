"""
tests/test_scorer.py
====================
Unit tests for the scoring model in scorer.py.

Tests cover:
  - Competition tier lookup (exact and fuzzy)
  - Match stakes inference from competition/fixture text
  - Rivalry detection
  - Team popularity scoring
  - Kick-off time convenience scoring
  - Composite score calculation
  - Rationale generation
  - Full rank_fixtures() pipeline
"""

import sys
import os
from datetime import datetime, timezone

import pytest
import pytz

# Add the project root to the path so imports work from the tests directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scorer import (
    rank_fixtures,
    _score_fixture,
    _get_stakes_score,
    _get_popularity_score,
    _get_kickoff_score,
    _generate_rationale,
)
from data.competition_tiers import get_competition_tier_score
from data.rivalries import is_rivalry
from data.team_popularity import get_team_popularity


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_fixture(
    name="Team A vs Team B",
    home_team="Team A",
    away_team="Team B",
    competition="Premier League",
    sport="Football",
    kickoff=None,
    channels=None,
):
    """Build a minimal fixture dict for testing."""
    if kickoff is None:
        # Default to a Saturday 15:00 UTC (prime UK viewing time)
        kickoff = datetime(2026, 3, 21, 15, 0, 0, tzinfo=timezone.utc)
    return {
        "name": name,
        "home_team": home_team,
        "away_team": away_team,
        "competition": competition,
        "sport": sport,
        "kickoff": kickoff,
        "channels": channels or ["Sky Sports"],
        "fanzo_url": "",
    }


# ── Competition tier tests ────────────────────────────────────────────────────

class TestCompetitionTiers:
    def test_exact_match_premier_league(self):
        assert get_competition_tier_score("Premier League") == 85.0

    def test_exact_match_champions_league(self):
        assert get_competition_tier_score("UEFA Champions League") == 81.0

    def test_exact_match_world_cup(self):
        assert get_competition_tier_score("FIFA World Cup") == 100.0

    def test_fuzzy_match_barclays_premier_league(self):
        # "Premier League" is a substring of "Barclays Premier League"
        score = get_competition_tier_score("Barclays Premier League")
        assert score == 85.0

    def test_fuzzy_match_partial_champions_league(self):
        score = get_competition_tier_score("Champions League Quarter-Final")
        assert score == 81.0

    def test_unknown_competition_returns_default(self):
        score = get_competition_tier_score("Mystery Invitational Cup 2026")
        assert score == 30.0

    def test_empty_string_returns_default(self):
        score = get_competition_tier_score("")
        assert score == 30.0

    def test_six_nations_score(self):
        assert get_competition_tier_score("Six Nations") == 83.0

    def test_fa_cup_score(self):
        assert get_competition_tier_score("FA Cup") == 78.0


# ── Match stakes tests ────────────────────────────────────────────────────────

class TestMatchStakes:
    def test_final_scores_highest(self):
        f = make_fixture(competition="FA Cup Final")
        assert _get_stakes_score(f) == 95.0

    def test_semi_final(self):
        f = make_fixture(competition="Champions League Semi-Final")
        assert _get_stakes_score(f) == 85.0

    def test_quarter_final(self):
        f = make_fixture(competition="FA Cup Quarter-Final")
        assert _get_stakes_score(f) == 70.0

    def test_round_of_16(self):
        f = make_fixture(competition="Champions League Round of 16")
        assert _get_stakes_score(f) == 60.0

    def test_friendly_scores_low(self):
        f = make_fixture(competition="International Friendly")
        assert _get_stakes_score(f) == 20.0

    def test_six_nations_scores_tournament(self):
        f = make_fixture(competition="Guinness Six Nations")
        assert _get_stakes_score(f) == 72.0

    def test_premier_league_default(self):
        f = make_fixture(competition="Premier League")
        assert _get_stakes_score(f) == 55.0

    def test_unknown_competition_default(self):
        f = make_fixture(competition="Unknown Cup")
        assert _get_stakes_score(f) == 45.0


# ── Rivalry tests ─────────────────────────────────────────────────────────────

class TestRivalries:
    def test_north_london_derby(self):
        assert is_rivalry("Arsenal", "Tottenham") is True

    def test_north_london_derby_reversed(self):
        assert is_rivalry("Tottenham", "Arsenal") is True

    def test_old_firm(self):
        assert is_rivalry("Celtic", "Rangers") is True

    def test_merseyside_derby(self):
        assert is_rivalry("Liverpool", "Everton") is True

    def test_six_nations_england_wales(self):
        assert is_rivalry("England", "Wales") is True

    def test_not_a_rivalry(self):
        assert is_rivalry("Bournemouth", "Brentford") is False

    def test_empty_team_names(self):
        assert is_rivalry("", "Arsenal") is False

    def test_case_insensitive(self):
        assert is_rivalry("arsenal", "tottenham") is True


# ── Team popularity tests ─────────────────────────────────────────────────────

class TestTeamPopularity:
    def test_manchester_united_high_score(self):
        assert get_team_popularity("Manchester United") >= 85

    def test_england_national_team_highest(self):
        assert get_team_popularity("England") >= 90

    def test_unknown_team_returns_default(self):
        assert get_team_popularity("FC Obscura") == 40.0

    def test_empty_string_returns_default(self):
        assert get_team_popularity("") == 40.0

    def test_popularity_score_range(self):
        for team in ["Liverpool", "Arsenal", "Chelsea", "Wales", "Celtic"]:
            score = get_team_popularity(team)
            assert 0 <= score <= 100, f"{team} score {score} out of range"

    def test_combined_popularity_score(self):
        # A fixture between two popular teams should score higher than one with unknowns
        popular_score = _get_popularity_score("Manchester United", "Liverpool")
        obscure_score = _get_popularity_score("FC Obscura", "FC Unknown")
        assert popular_score > obscure_score


# ── Kick-off time tests ───────────────────────────────────────────────────────

class TestKickoffTime:
    def _utc(self, hour, minute=0, month=3, day=21):
        """Create a UTC datetime for a given hour (March = GMT, no BST offset)."""
        return datetime(2026, month, day, hour, minute, 0, tzinfo=timezone.utc)

    def test_prime_time_saturday_afternoon(self):
        # 15:00 UTC = 15:00 UK (GMT in March) — prime window
        assert _get_kickoff_score(self._utc(15)) == 100.0

    def test_prime_time_evening(self):
        # 20:00 UTC = 20:00 UK — prime window
        assert _get_kickoff_score(self._utc(20)) == 100.0

    def test_late_kickoff(self):
        # 22:30 UTC = 22:30 UK — late but watchable
        assert _get_kickoff_score(self._utc(22, 30)) == 70.0

    def test_early_morning(self):
        # 08:00 UTC = 08:00 UK — early morning
        assert _get_kickoff_score(self._utc(8)) == 50.0

    def test_middle_of_night(self):
        # 02:00 UTC = 02:00 UK — middle of night
        assert _get_kickoff_score(self._utc(2)) == 20.0

    def test_near_unwatchable(self):
        # 04:00 UTC = 04:00 UK — near-unwatchable
        assert _get_kickoff_score(self._utc(4)) == 10.0

    def test_bst_adjustment(self):
        # In June (BST = UTC+1), 21:00 UTC = 22:00 UK — still watchable
        june_kickoff = datetime(2026, 6, 20, 21, 0, 0, tzinfo=timezone.utc)
        score = _get_kickoff_score(june_kickoff)
        assert score == 70.0  # 22:00 UK = late but watchable


# ── Composite score tests ─────────────────────────────────────────────────────

class TestCompositeScore:
    def test_composite_is_within_range(self):
        f = make_fixture()
        result = _score_fixture(f)
        assert 0 <= result["composite_score"] <= 100

    def test_champions_league_final_scores_high(self):
        f = make_fixture(
            name="Arsenal vs Manchester United",
            home_team="Arsenal",
            away_team="Manchester United",
            competition="UEFA Champions League Final",
        )
        result = _score_fixture(f)
        assert result["composite_score"] >= 70

    def test_derby_boosts_score(self):
        """A rivalry fixture should outscore a comparable non-rivalry fixture."""
        derby = make_fixture(
            name="Arsenal vs Tottenham",
            home_team="Arsenal",
            away_team="Tottenham",
            competition="Premier League",
        )
        non_derby = make_fixture(
            name="Arsenal vs Bournemouth",
            home_team="Arsenal",
            away_team="Bournemouth",
            competition="Premier League",
        )
        derby_result = _score_fixture(derby)
        non_derby_result = _score_fixture(non_derby)
        assert derby_result["composite_score"] > non_derby_result["composite_score"]

    def test_sub_scores_present(self):
        f = make_fixture()
        result = _score_fixture(f)
        expected_keys = {
            "competition_tier",
            "match_stakes",
            "derby_rivalry",
            "team_popularity",
            "kickoff_time",
            "betting_volume",
        }
        assert expected_keys == set(result["sub_scores"].keys())

    def test_all_sub_scores_in_range(self):
        f = make_fixture()
        result = _score_fixture(f)
        for key, val in result["sub_scores"].items():
            assert 0 <= val <= 100, f"Sub-score {key} = {val} is out of range"

    def test_rationale_is_non_empty_string(self):
        f = make_fixture()
        result = _score_fixture(f)
        assert isinstance(result["rationale"], str)
        assert len(result["rationale"]) > 0


# ── rank_fixtures() integration tests ────────────────────────────────────────

class TestRankFixtures:
    def _make_fixtures(self):
        """A small set of varied fixtures for ranking tests."""
        return [
            make_fixture(
                name="Arsenal vs Tottenham",
                home_team="Arsenal",
                away_team="Tottenham",
                competition="Premier League",
            ),
            make_fixture(
                name="England vs France",
                home_team="England",
                away_team="France",
                competition="FIFA World Cup Final",
            ),
            make_fixture(
                name="FC Obscura vs FC Unknown",
                home_team="FC Obscura",
                away_team="FC Unknown",
                competition="Unknown Cup",
                kickoff=datetime(2026, 3, 21, 3, 0, 0, tzinfo=timezone.utc),  # 03:00 UK
            ),
        ]

    def test_returns_correct_number(self):
        fixtures = self._make_fixtures()
        ranked = rank_fixtures(fixtures, top_n=20)
        # top_n=20 but we only have 3 fixtures
        assert len(ranked) == 3

    def test_top_n_respected(self):
        fixtures = self._make_fixtures()
        ranked = rank_fixtures(fixtures, top_n=1)
        assert len(ranked) == 1

    def test_world_cup_final_ranks_first(self):
        fixtures = self._make_fixtures()
        ranked = rank_fixtures(fixtures)
        assert ranked[0]["name"] == "England vs France"

    def test_obscure_fixture_ranks_last(self):
        fixtures = self._make_fixtures()
        ranked = rank_fixtures(fixtures)
        assert ranked[-1]["name"] == "FC Obscura vs FC Unknown"

    def test_ranks_are_sequential(self):
        fixtures = self._make_fixtures()
        ranked = rank_fixtures(fixtures)
        for i, f in enumerate(ranked, start=1):
            assert f["rank"] == i

    def test_scores_are_descending(self):
        fixtures = self._make_fixtures()
        ranked = rank_fixtures(fixtures)
        scores = [f["composite_score"] for f in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_empty_input_returns_empty_list(self):
        assert rank_fixtures([]) == []

    def test_fixture_retains_original_fields(self):
        fixtures = self._make_fixtures()
        ranked = rank_fixtures(fixtures)
        for f in ranked:
            assert "name" in f
            assert "home_team" in f
            assert "away_team" in f
            assert "competition" in f
            assert "kickoff" in f
