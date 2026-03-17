"""
scorer.py
=========
Applies the six-factor interest scoring model to each fixture and returns
a ranked list of the top 20 by composite score.

Scoring model (composite out of 100):
┌──────────────────────┬────────┬────────────────────────────────────────────┐
│ Factor               │ Weight │ Description                                │
├──────────────────────┼────────┼────────────────────────────────────────────┤
│ Competition tier     │  25%   │ Prestige of the competition                │
│ Match stakes         │  20%   │ How much is riding on this fixture         │
│ Derby / rivalry      │  15%   │ Established UK rivalry bonus               │
│ Team popularity      │  15%   │ Combined UK fan base of both teams         │
│ Kick-off time        │  15%   │ UK viewing convenience                     │
│ Betting volume proxy │  10%   │ Competition + rivalry proxy for interest   │
└──────────────────────┴────────┴────────────────────────────────────────────┘

All sub-scores are on a 0–100 scale. The composite is a weighted sum, capped
at 100. The top N fixtures by composite score are returned as the ranked list.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import pytz

from data.competition_tiers import get_competition_tier_score
from data.rivalries import is_rivalry
from data.team_popularity import get_team_popularity
from enrichment import calculate_live_stakes

logger = logging.getLogger(__name__)

# Scoring weights — must sum to 1.0
WEIGHTS = {
    "competition_tier": 0.25,
    "match_stakes": 0.20,
    "derby_rivalry": 0.15,
    "team_popularity": 0.15,
    "kickoff_time": 0.15,
    "betting_volume": 0.10,
}

UK_TIMEZONE = pytz.timezone("Europe/London")


# ── Public API ─────────────────────────────────────────────────────────────────

def rank_fixtures(fixtures: List[Dict], top_n: int = 20, standings: Optional[Dict] = None) -> List[Dict]:
    """
    Score every fixture in the list, sort by composite score descending,
    and return the top_n results with rank numbers attached.

    Args:
        fixtures:  List of fixture dicts from the scraper.
        top_n:     How many results to return (default 20).
        standings: Optional live league standings from enrichment.py.
                   If provided, match stakes are scored dynamically from
                   actual table positions rather than keyword inference.

    Each returned dict is the original fixture dict extended with:
        composite_score  (float)  — weighted composite out of 100
        sub_scores       (dict)   — individual factor scores (each 0–100)
        rationale        (str)    — plain-English explanation of the ranking
        rank             (int)    — 1-based position in the ranked list
    """
    if not fixtures:
        return []

    scored = [_score_fixture(f, standings=standings) for f in fixtures]
    scored.sort(key=lambda x: x["composite_score"], reverse=True)

    # Attach rank numbers
    for i, fixture in enumerate(scored[:top_n], start=1):
        fixture["rank"] = i

    return scored[:top_n]


# ── Scoring functions ──────────────────────────────────────────────────────────

def _score_fixture(fixture: Dict, standings: Optional[Dict] = None) -> Dict:
    """Score a single fixture across all six factors and generate a rationale."""
    competition = fixture.get("competition", "Unknown Competition")
    home = fixture.get("home_team", "")
    away = fixture.get("away_team", "")
    kickoff = fixture.get("kickoff")

    # ── Factor 1: Competition tier (25%) ──────────────────────────────────────
    tier_score = get_competition_tier_score(competition)

    # ── Factor 2: Match stakes (20%) ──────────────────────────────────────────
    # Use live standings if available; fall back to keyword inference.
    live_stakes = calculate_live_stakes(home, away, standings or {}, competition)
    stakes_score = live_stakes if live_stakes is not None else _get_stakes_score(fixture)

    # ── Factor 3: Derby / rivalry (15%) ───────────────────────────────────────
    rivalry_score = 100.0 if is_rivalry(home, away) else 0.0

    # ── Factor 4: Team popularity (15%) ───────────────────────────────────────
    popularity_score = _get_popularity_score(home, away)

    # ── Factor 5: Kick-off time convenience (15%) ─────────────────────────────
    kickoff_score = _get_kickoff_score(kickoff) if kickoff else 50.0

    # ── Factor 6: Betting volume proxy (10%) ──────────────────────────────────
    # Without real betting API data, we proxy using competition prestige
    # and rivalry — both strongly correlate with real-money wagering volumes.
    betting_score = min(100.0, tier_score * 0.8 + rivalry_score * 0.2)

    sub_scores = {
        "competition_tier": round(tier_score, 1),
        "match_stakes": round(stakes_score, 1),
        "derby_rivalry": round(rivalry_score, 1),
        "team_popularity": round(popularity_score, 1),
        "kickoff_time": round(kickoff_score, 1),
        "betting_volume": round(betting_score, 1),
    }

    # Weighted composite
    composite = (
        tier_score * WEIGHTS["competition_tier"]
        + stakes_score * WEIGHTS["match_stakes"]
        + rivalry_score * WEIGHTS["derby_rivalry"]
        + popularity_score * WEIGHTS["team_popularity"]
        + kickoff_score * WEIGHTS["kickoff_time"]
        + betting_score * WEIGHTS["betting_volume"]
    )
    composite = round(min(100.0, composite * _gender_multiplier(fixture)), 1)

    rationale = _generate_rationale(fixture, sub_scores, composite)

    return {
        **fixture,
        "composite_score": composite,
        "sub_scores": sub_scores,
        "rationale": rationale,
    }


def _get_stakes_score(fixture: Dict) -> float:
    """
    Infer match stakes from the competition name and fixture name.

    Without live standings data, we use stage/round keywords as signals.
    Cup finals always score highest; dead-rubber friendlies score lowest.
    """
    text = (
        fixture.get("competition", "").lower()
        + " "
        + fixture.get("name", "").lower()
    )

    # ── Knockout stages ───────────────────────────────────────────────────────
    if "final" in text and "semi" not in text and "quarter" not in text:
        return 95.0   # Final
    if "semi-final" in text or "semi final" in text:
        return 85.0
    if "quarter-final" in text or "quarter final" in text:
        return 70.0
    if "round of 16" in text or "last 16" in text:
        return 60.0
    if "round of 32" in text or "last 32" in text:
        return 50.0

    # ── Qualifying competitions — must be checked before tournament keywords ──
    # Stakes ARE genuinely high (qualify or go home), but below the tournament itself
    if "qualif" in text or "qualification" in text:
        return 65.0

    # ── Tournament round-robins (high stakes by nature) ───────────────────────
    if any(t in text for t in ["six nations", "autumn nations", "world cup", "euros"]):
        return 72.0

    # ── UEFA club competitions — every match matters, even the league phase ───
    # CL/EL knockout rounds are caught above; this covers the league phase and
    # any fixture where FANZO doesn't include the round in the name.
    if "champions league" in text:
        return 68.0
    if "europa league" in text:
        return 62.0
    if "conference league" in text:
        return 55.0

    # ── League football — moderate, stakes depend on table position ───────────
    if any(t in text for t in ["premier league", "championship", "serie a", "la liga", "bundesliga"]):
        return 55.0

    # ── Friendlies — low stakes ───────────────────────────────────────────────
    if "friendly" in text:
        return 20.0

    return 45.0   # Default moderate stakes


def _get_popularity_score(home: str, away: str) -> float:
    """
    Score the fixture by the combined UK popularity of both teams.
    Weighted 40/40/20 toward the average, with a 20% bonus for the
    higher-profile side to reward marquee matchups.
    """
    home_score = get_team_popularity(home)
    away_score = get_team_popularity(away)
    higher = max(home_score, away_score)
    return round(home_score * 0.4 + away_score * 0.4 + higher * 0.2, 1)


def _get_kickoff_score(kickoff_utc: datetime) -> float:
    """
    Score the kick-off time by UK viewing convenience.
    Converts the UTC kickoff to UK local time (handling GMT/BST automatically
    via the pytz Europe/London timezone).

    Scoring bands (UK local time):
        11:00–22:00 → 100  (prime viewing window)
        22:00–00:00 →  70  (late but watchable)
        06:00–11:00 →  50  (early morning, viable on weekends)
        00:00–03:00 →  20  (middle of the night)
        03:00–06:00 →  10  (near-unwatchable)
    """
    uk_time = kickoff_utc.astimezone(UK_TIMEZONE)
    hour = uk_time.hour + uk_time.minute / 60.0

    if 11.0 <= hour < 22.0:
        return 100.0
    if 22.0 <= hour < 24.0:
        return 70.0
    if 6.0 <= hour < 11.0:
        return 50.0
    if 0.0 <= hour < 3.0:
        return 20.0
    return 10.0   # 03:00–06:00


# ── Gender multiplier ──────────────────────────────────────────────────────────

def _is_womens(fixture: Dict) -> bool:
    text = f"{fixture.get('name', '')} {fixture.get('competition', '')}".lower()
    return "(w)" in text or "women" in text or " wsl" in text


def _gender_multiplier(fixture: Dict) -> float:
    if not _is_womens(fixture):
        return 1.0
    if "england" in fixture.get("name", "").lower():
        return 1.0   # England Women's national team — full score
    return 0.5       # All other women's fixtures


# ── Rationale generation ───────────────────────────────────────────────────────

def _generate_rationale(fixture: Dict, scores: Dict, composite: float) -> str:
    """
    Build a plain-English sentence explaining why this fixture ranked as it did.
    Highlights the two or three strongest scoring factors.
    """
    parts = []
    competition = fixture.get("competition", "this competition")
    home = fixture.get("home_team", "")
    away = fixture.get("away_team", "")

    # ── Competition context ────────────────────────────────────────────────────
    tier = scores["competition_tier"]
    if tier >= 85:
        parts.append(f"Top-tier {competition}")
    elif tier >= 68:
        parts.append(f"Major {competition} fixture")
    elif tier >= 50:
        parts.append(f"{competition} fixture")
    else:
        parts.append(f"Lower-profile {competition} match")

    # ── Match stage ───────────────────────────────────────────────────────────
    stakes = scores["match_stakes"]
    if stakes >= 90:
        parts.append("(final)")
    elif stakes >= 80:
        parts.append("(semi-final)")
    elif stakes >= 65:
        parts.append("(knockout stage)")
    elif stakes >= 70:
        parts.append("(tournament round)")

    # ── Derby/rivalry ──────────────────────────────────────────────────────────
    if scores["derby_rivalry"] == 100:
        parts.append("— a genuine derby/rivalry fixture")

    # ── Team popularity ────────────────────────────────────────────────────────
    pop = scores["team_popularity"]
    if pop >= 82:
        parts.append("between two of the UK's most-followed sides")
    elif pop >= 68:
        parts.append("featuring a highly popular club")

    # ── Kick-off time ──────────────────────────────────────────────────────────
    ko = scores["kickoff_time"]
    if ko == 100:
        parts.append("at a prime UK viewing time")
    elif ko == 70:
        parts.append("— late UK kick-off")
    elif ko == 50:
        parts.append("— early morning UK time")
    elif ko <= 20:
        parts.append("— difficult overnight UK viewing window")

    sentence = " ".join(parts)
    # Capitalise and ensure it ends with a full stop
    if sentence:
        sentence = sentence[0].upper() + sentence[1:]
        if not sentence.endswith("."):
            sentence += "."

    return sentence
