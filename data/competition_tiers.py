# =============================================================================
# Competition Tier Lookup Table
# =============================================================================
# Each competition is assigned a baseline interest score (0–100) reflecting
# its prestige and typical UK audience size.
#
# Tier 1 (90–100): Global mega-events — World Cup, Olympics, Wimbledon finals
# Tier 2 (75–89): Premier League, Six Nations, Champions League knockouts
# Tier 3 (55–74): Championship, Europa League, major combat sports, F1
# Tier 4 (35–54): Lower leagues, Conference League, minor internationals
# Tier 5 (10–34): Non-league, minor cups, low-interest friendlies
#
# Source basis: BARB/Ofcom viewership data, YouGov sport popularity ratings.
# Review at the start of each season or when major broadcast rights change.
# =============================================================================

COMPETITION_TIERS = {
    # ── TIER 1 ── Global mega-events ────────────────────────────────────────
    "FIFA World Cup": 100,
    "World Cup": 100,
    "Olympics": 95,
    "Wimbledon": 92,
    "Rugby World Cup": 90,
    "The Ashes": 90,

    # ── TIER 2 ── Top UK competitions ───────────────────────────────────────
    "Premier League": 85,
    "Six Nations": 83,
    "TikTok Six Nations": 83,
    "Guinness Six Nations": 83,
    "UEFA Champions League": 81,
    "Champions League": 81,
    "FA Cup": 78,
    "Grand National": 78,
    "British & Irish Lions": 77,
    "EFL Cup": 75,
    "Carabao Cup": 75,
    "League Cup": 75,

    # ── TIER 3 ── Major competitions ────────────────────────────────────────
    "Championship": 70,
    "EFL Championship": 70,
    "UEFA Europa League": 68,
    "Europa League": 68,
    "PDC World Darts Championship": 66,
    "World Darts Championship": 66,
    "World Snooker Championship": 65,
    "Formula 1": 63,
    "F1": 63,
    "UFC": 63,
    "Boxing": 65,
    "World Boxing": 65,
    "Super League": 60,
    "Betfred Super League": 60,
    "Women's Super League": 59,
    "WSL": 59,
    "Premiership Rugby": 59,
    "Gallagher Premiership": 59,
    "United Rugby Championship": 57,
    "URC": 57,
    "European Rugby Champions Cup": 66,
    "Heineken Champions Cup": 66,
    "Challenge Cup": 59,
    "Cricket": 58,
    "The Hundred": 60,
    "Test Cricket": 63,
    "Golf": 55,
    "The Masters": 72,
    "The Open": 75,
    "Ryder Cup": 78,
    "ATP Tour": 58,
    "WTA Tour": 55,
    "NBA": 50,
    "NFL": 52,

    # ── TIER 4 ── Secondary competitions ────────────────────────────────────
    "League One": 45,
    "EFL League One": 45,
    "League Two": 40,
    "EFL League Two": 40,
    "UEFA Europa Conference League": 50,
    "Conference League": 50,
    "Autumn Nations Series": 53,
    "Autumn Internationals": 53,
    "International Friendly": 48,
    "Friendly": 48,
    "County Cricket": 42,
    "National League": 35,
    "FA Trophy": 35,
    "FA Vase": 32,

    # ── DEFAULT ─────────────────────────────────────────────────────────────
    "Unknown Competition": 30,
}


def get_competition_tier_score(competition_name: str) -> float:
    """
    Return the tier score for a competition.
    First tries an exact match, then a case-insensitive substring match.
    Falls back to the default score if nothing matches.
    """
    if not competition_name:
        return COMPETITION_TIERS["Unknown Competition"]

    # Exact match
    if competition_name in COMPETITION_TIERS:
        return float(COMPETITION_TIERS[competition_name])

    # Case-insensitive substring match — e.g. "Barclays Premier League" → "Premier League"
    comp_lower = competition_name.lower()
    for known_comp, score in COMPETITION_TIERS.items():
        if known_comp.lower() in comp_lower:
            return float(score)

    return float(COMPETITION_TIERS["Unknown Competition"])
