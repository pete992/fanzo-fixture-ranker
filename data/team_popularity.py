# =============================================================================
# UK Team Popularity Scores
# =============================================================================
# Each team is assigned a popularity score (0–100) reflecting its estimated
# UK fan base size.
#
# Source basis: YouGov UK Sport and Football Club popularity rankings
#   (yougov.co.uk/ratings/sport/popularity/sport/all)
# Supplemented by historic TV audience figures and social media following.
#
# Maintenance: Review at the start of each season to reflect promotions,
# relegations, and any significant shifts in national following.
# =============================================================================

from typing import Dict

TEAM_POPULARITY = {  # type: Dict[str, float]
    # ── England National Teams ──────────────────────────────────────────────
    # Separate entries for men's, women's, and rugby to avoid ambiguity
    "England": 95,
    "England Women": 80,

    # ── Other Home Nations ───────────────────────────────────────────────────
    "Wales": 76,
    "Scotland": 73,
    "Ireland": 69,
    "Northern Ireland": 65,
    "Republic of Ireland": 65,

    # ── Premier League — Big Six ─────────────────────────────────────────────
    "Manchester United": 88,
    "Liverpool": 87,
    "Arsenal": 85,
    "Chelsea": 82,
    "Manchester City": 80,
    "Tottenham": 78,
    "Tottenham Hotspur": 78,

    # ── Premier League — Other clubs ─────────────────────────────────────────
    "Newcastle": 73,
    "Newcastle United": 73,
    "Aston Villa": 71,
    "Everton": 69,
    "West Ham": 67,
    "West Ham United": 67,
    "Leicester": 65,
    "Leicester City": 65,
    "Leeds": 63,
    "Leeds United": 63,
    "Wolves": 61,
    "Wolverhampton Wanderers": 61,
    "Southampton": 59,
    "Brighton": 59,
    "Brighton & Hove Albion": 59,
    "Crystal Palace": 57,
    "Fulham": 55,
    "Brentford": 53,
    "Nottingham Forest": 59,
    "Burnley": 52,
    "Bournemouth": 52,
    "AFC Bournemouth": 52,
    "Ipswich": 54,
    "Ipswich Town": 54,

    # ── Championship ─────────────────────────────────────────────────────────
    "Sunderland": 56,
    "Sheffield United": 55,
    "Sheffield Wednesday": 54,
    "Derby": 53,
    "Derby County": 53,
    "Stoke": 52,
    "Stoke City": 52,
    "Middlesbrough": 51,
    "Birmingham": 50,
    "Birmingham City": 50,
    "QPR": 48,
    "Queens Park Rangers": 48,
    "Millwall": 47,
    "Cardiff": 51,
    "Cardiff City": 51,
    "Swansea": 50,
    "Swansea City": 50,
    "Norwich": 52,
    "Norwich City": 52,
    "Watford": 50,
    "Luton": 48,
    "Luton Town": 48,

    # ── Scottish Clubs ───────────────────────────────────────────────────────
    "Celtic": 70,
    "Rangers": 68,
    "Hearts": 50,
    "Hibernian": 49,
    "Aberdeen": 46,

    # ── Major European Club Football — UK fan interest is high for these sides ─
    # Scores reflect UK following via TV audiences, social media, and shirt sales.
    # Champions/Europa League regulars that UK fans actively follow.
    "Real Madrid": 76,
    "Barcelona": 74,
    "Bayern Munich": 72,
    "Bayern": 72,
    "Paris Saint-Germain": 70,
    "PSG": 70,
    "Paris": 70,                    # FANZO may abbreviate to "Paris"
    "Juventus": 67,
    "AC Milan": 65,
    "Milan": 65,
    "Inter Milan": 65,
    "Inter": 65,
    "Atletico Madrid": 63,
    "Atletico": 63,
    "Borussia Dortmund": 62,
    "Dortmund": 62,
    "Bayer Leverkusen": 60,
    "Leverkusen": 60,
    "Ajax": 58,
    "Porto": 56,
    "Benfica": 55,
    "Sporting CP": 53,
    "Sporting": 53,
    "Napoli": 55,
    "Roma": 54,
    "AS Roma": 54,
    "Sevilla": 52,
    "Villarreal": 50,
    "RB Leipzig": 52,
    "Leipzig": 52,
    "Feyenoord": 50,
    "Club Brugge": 48,
    "Shakhtar Donetsk": 46,
    "Shakhtar": 46,

    # ── International Football — Popular with UK audiences ───────────────────
    "Germany": 71,
    "France": 69,
    "Spain": 67,
    "Brazil": 66,
    "Argentina": 63,
    "Portugal": 62,
    "Italy": 59,
    "Netherlands": 57,
    "Belgium": 55,
    "USA": 51,
    "Australia": 51,
    "New Zealand": 53,
    "South Africa": 58,
    "Uruguay": 50,
    "Colombia": 49,

    # ── Rugby Union — Clubs ──────────────────────────────────────────────────
    "Saracens": 56,
    "Harlequins": 53,
    "Bath": 51,
    "Bath Rugby": 51,
    "Northampton": 50,
    "Northampton Saints": 50,
    "Leicester Tigers": 56,
    "Gloucester": 48,
    "Wasps": 47,
    "Sale Sharks": 46,
    "Exeter Chiefs": 51,
    "Bristol Bears": 49,
    "Leinster": 57,
    "Munster": 53,
    "Ulster": 49,
    "Connacht": 46,
    "Glasgow Warriors": 47,
    "Edinburgh": 45,

    # ── Rugby League — Clubs ─────────────────────────────────────────────────
    "St Helens": 55,
    "Wigan Warriors": 54,
    "Leeds Rhinos": 53,
    "Warrington Wolves": 50,
    "Hull FC": 49,
    "Hull KR": 48,
    "Castleford Tigers": 47,
    "Catalans Dragons": 44,

    # ── Default ───────────────────────────────────────────────────────────────
    "_default": 25,
}


def get_team_popularity(team_name: str) -> float:
    """
    Return the popularity score for a team.
    Tries exact match first, then case-insensitive substring match.
    Falls back to the default score for unknown teams.
    """
    if not team_name:
        return TEAM_POPULARITY["_default"]

    # Exact match
    if team_name in TEAM_POPULARITY:
        return TEAM_POPULARITY[team_name]

    # Case-insensitive substring match
    name_lower = team_name.lower()
    for known, score in TEAM_POPULARITY.items():
        if known == "_default":
            continue
        if known.lower() in name_lower or name_lower in known.lower():
            return score

    return TEAM_POPULARITY["_default"]
