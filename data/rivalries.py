# =============================================================================
# UK Sports Rivalry Lookup Table
# =============================================================================
# A pre-compiled list of established UK sports rivalries.
# Any fixture between two teams in this list receives a full rivalry bonus
# in the scoring model (15% weight).
#
# Sources:
#   - Wikipedia: List of association football rivalries in the United Kingdom
#   - Wikipedia: List of sports rivalries in the United Kingdom
#   - Wikipedia: Derbies in the Rugby Football League
#   - Derbyist project: derby.ist
#
# Maintenance: Review annually, and add any newly promoted clubs whose
# local derby is now a televised fixture.
# =============================================================================

# Each entry is a frozenset of two team names — order doesn't matter.
# Matching is case-insensitive (see is_rivalry() below).

_FOOTBALL_RIVALRIES = {
    # ── European Super Fixtures — UK clubs with recurring CL/European history ─
    # Qualifying criteria: met 2+ times in UEFA knockout rounds in the last decade
    # and generated significant UK TV audiences. These carry as much intensity
    # for UK fans as domestic derbies.
    frozenset({"Manchester City", "Real Madrid"}),         # CL QF/SF 2022, 2023, 2024
    frozenset({"Man City", "Real Madrid"}),
    frozenset({"Liverpool", "Real Madrid"}),               # CL Final 2018, 2022; QF 2023
    frozenset({"Manchester City", "Bayern Munich"}),       # CL QF 2023
    frozenset({"Man City", "Bayern Munich"}),
    frozenset({"Manchester City", "Paris Saint-Germain"}), # CL SF 2021
    frozenset({"Man City", "Paris Saint-Germain"}),
    frozenset({"Manchester City", "PSG"}),
    frozenset({"Man City", "PSG"}),
    frozenset({"Liverpool", "Bayern Munich"}),             # CL R16 2019
    frozenset({"Liverpool", "Barcelona"}),                 # CL SF 2019 (4-0 comeback)
    frozenset({"Liverpool", "Atletico Madrid"}),           # CL R16 2020
    frozenset({"Liverpool", "AC Milan"}),                  # CL Final 2005, 2007
    frozenset({"Chelsea", "Real Madrid"}),                 # CL SF 2021, QF 2022, QF 2024
    frozenset({"Chelsea", "Bayern Munich"}),               # CL Final 2012
    frozenset({"Chelsea", "Barcelona"}),                   # CL SF 2012
    frozenset({"Chelsea", "Paris Saint-Germain"}),         # CL R16 2015, 2016
    frozenset({"Chelsea", "PSG"}),
    frozenset({"Chelsea", "Atletico Madrid"}),             # CL R16 2022
    frozenset({"Arsenal", "Bayern Munich"}),               # CL R16 2005, 2013, 2014, 2015; QF 2024
    frozenset({"Arsenal", "Barcelona"}),                   # CL multiple encounters
    frozenset({"Arsenal", "Real Madrid"}),                 # CL R16 2006, 2023
    frozenset({"Manchester United", "Real Madrid"}),       # CL multiple historic
    frozenset({"Man Utd", "Real Madrid"}),
    frozenset({"Manchester United", "Barcelona"}),         # CL Final 2009, 2011
    frozenset({"Man Utd", "Barcelona"}),
    frozenset({"Manchester United", "Bayern Munich"}),     # CL Final 1999; multiple since
    frozenset({"Man Utd", "Bayern Munich"}),
    frozenset({"Manchester United", "Juventus"}),          # CL Final 1999; multiple
    frozenset({"Man Utd", "Juventus"}),
    frozenset({"Manchester United", "Paris Saint-Germain"}), # CL R16 2019 comeback
    frozenset({"Man Utd", "Paris Saint-Germain"}),
    frozenset({"Manchester United", "PSG"}),
    frozenset({"Man Utd", "PSG"}),
    frozenset({"Tottenham", "Ajax"}),                      # CL SF 2019 (Spurs comeback)
    frozenset({"Spurs", "Ajax"}),
    frozenset({"Tottenham", "Juventus"}),                  # CL R16 2018
    frozenset({"Spurs", "Juventus"}),
    frozenset({"Manchester City", "Atletico Madrid"}),     # CL QF 2022, SF 2016
    frozenset({"Man City", "Atletico Madrid"}),
    frozenset({"Manchester City", "Dortmund"}),            # CL QF 2021
    frozenset({"Man City", "Dortmund"}),
    frozenset({"Manchester City", "Borussia Dortmund"}),
    frozenset({"Man City", "Borussia Dortmund"}),
    frozenset({"Liverpool", "Inter Milan"}),               # CL R16 2022
    frozenset({"Liverpool", "Benfica"}),                   # CL QF 2022

    # ── Premier League / Top Flight ──────────────────────────────────────────
    frozenset({"Manchester United", "Manchester City"}),   # Manchester Derby
    frozenset({"Man Utd", "Man City"}),
    frozenset({"Man Utd", "Manchester City"}),
    frozenset({"Manchester United", "Man City"}),
    frozenset({"Liverpool", "Manchester United"}),          # North West Derby
    frozenset({"Liverpool", "Man Utd"}),
    frozenset({"Liverpool", "Everton"}),                    # Merseyside Derby
    frozenset({"Arsenal", "Tottenham"}),                    # North London Derby
    frozenset({"Arsenal", "Spurs"}),
    frozenset({"Arsenal", "Chelsea"}),                      # London Derby
    frozenset({"Chelsea", "Tottenham"}),                    # London Derby
    frozenset({"Chelsea", "Spurs"}),
    frozenset({"Arsenal", "Manchester City"}),              # Title rivalry 2023, 2024, 2025
    frozenset({"Arsenal", "Man City"}),
    frozenset({"Manchester City", "Liverpool"}),
    frozenset({"Man City", "Liverpool"}),
    frozenset({"Chelsea", "Arsenal"}),
    frozenset({"Chelsea", "Liverpool"}),
    frozenset({"Arsenal", "Liverpool"}),
    frozenset({"Newcastle", "Sunderland"}),                 # Tyne-Wear Derby
    frozenset({"Leeds", "Manchester United"}),              # Yorkshire-Lancashire
    frozenset({"Leeds United", "Manchester United"}),
    frozenset({"Aston Villa", "Birmingham"}),               # Second City Derby
    frozenset({"Aston Villa", "Birmingham City"}),
    frozenset({"Wolves", "West Brom"}),                     # Black Country Derby
    frozenset({"Wolverhampton", "West Brom"}),
    frozenset({"Wolverhampton Wanderers", "West Bromwich Albion"}),
    frozenset({"Sheffield United", "Sheffield Wednesday"}), # Steel City Derby
    frozenset({"Derby", "Nottingham Forest"}),              # East Midlands Derby
    frozenset({"Derby County", "Nottingham Forest"}),
    frozenset({"Leicester", "Nottingham Forest"}),
    frozenset({"Leicester City", "Nottingham Forest"}),
    frozenset({"Southampton", "Portsmouth"}),               # South Coast Derby
    frozenset({"Millwall", "West Ham"}),                    # South London Derby
    frozenset({"Millwall", "West Ham United"}),
    frozenset({"Crystal Palace", "Brighton"}),              # M23 Derby
    frozenset({"Crystal Palace", "Brighton & Hove Albion"}),
    frozenset({"West Ham", "Tottenham"}),                   # East London / Spurs
    frozenset({"West Ham United", "Tottenham"}),
    frozenset({"Brentford", "QPR"}),
    frozenset({"Fulham", "Chelsea"}),
    frozenset({"Fulham", "QPR"}),
    frozenset({"Watford", "Luton"}),                        # Hertfordshire Derby
    frozenset({"Watford", "Luton Town"}),
    frozenset({"Luton", "MK Dons"}),
    frozenset({"Ipswich", "Norwich"}),                      # East Anglian Derby
    frozenset({"Ipswich Town", "Norwich City"}),

    # ── Scottish Football ────────────────────────────────────────────────────
    frozenset({"Rangers", "Celtic"}),                       # Old Firm
    frozenset({"Hearts", "Hibernian"}),                     # Edinburgh Derby
    frozenset({"Aberdeen", "Dundee United"}),
    frozenset({"Aberdeen", "Inverness"}),

    # ── Welsh Football ───────────────────────────────────────────────────────
    frozenset({"Cardiff", "Swansea"}),                      # South Wales Derby
    frozenset({"Cardiff City", "Swansea City"}),

    # ── International ────────────────────────────────────────────────────────
    frozenset({"England", "Scotland"}),                     # Oldest international
    frozenset({"England", "Germany"}),
    frozenset({"England", "Argentina"}),
    frozenset({"England", "France"}),
    frozenset({"England", "Italy"}),
}

_RUGBY_UNION_RIVALRIES = {
    # Six Nations rivalries
    frozenset({"England", "Wales"}),
    frozenset({"England", "Ireland"}),
    frozenset({"England", "Scotland"}),
    frozenset({"Wales", "Ireland"}),
    frozenset({"England", "France"}),
    frozenset({"Ireland", "Scotland"}),
    frozenset({"Wales", "Scotland"}),
    frozenset({"France", "Ireland"}),
    # Club
    frozenset({"Saracens", "Northampton"}),
    frozenset({"Saracens", "Northampton Saints"}),
    frozenset({"Harlequins", "Saracens"}),
    frozenset({"Bath", "Bristol"}),
    frozenset({"Bath Rugby", "Bristol Rugby"}),
    frozenset({"Leinster", "Munster"}),
    frozenset({"Leinster", "Ulster"}),
}

_RUGBY_LEAGUE_RIVALRIES = {
    frozenset({"Leeds Rhinos", "Bradford Bulls"}),
    frozenset({"St Helens", "Wigan Warriors"}),
    frozenset({"St Helens", "Wigan"}),
    frozenset({"Warrington", "Widnes"}),
    frozenset({"Warrington Wolves", "Widnes Vikings"}),
    frozenset({"Hull FC", "Hull KR"}),                      # Hull Derby
    frozenset({"Castleford", "Featherstone"}),
    frozenset({"Leeds", "Bradford"}),
}

# Combined rivalry set across all sports
ALL_RIVALRIES = _FOOTBALL_RIVALRIES | _RUGBY_UNION_RIVALRIES | _RUGBY_LEAGUE_RIVALRIES


def is_rivalry(team_a: str, team_b: str) -> bool:
    """
    Return True if the two teams are established rivals.

    Matching strategy (in order):
      1. Exact match (case-insensitive)
      2. Partial match — FANZO sometimes uses full names ("Newcastle United")
         where the rivalry table stores short names ("Newcastle"). We check
         whether each side of a stored rivalry is contained within the
         provided team name, or vice versa.
    """
    if not team_a or not team_b:
        return False

    a = team_a.strip().lower()
    b = team_b.strip().lower()

    for rivalry in ALL_RIVALRIES:
        r = [t.lower() for t in rivalry]
        r0, r1 = r[0], r[1]

        # Exact match
        if {a, b} == {r0, r1}:
            return True

        # Partial match: stored name is a substring of provided name, or vice versa
        # e.g. "newcastle" in "newcastle united", or "tottenham" in "tottenham hotspur"
        a_matches = (r0 in a or a in r0)
        b_matches = (r1 in b or b in r1)
        if a_matches and b_matches:
            return True

        a_matches_alt = (r1 in a or a in r1)
        b_matches_alt = (r0 in b or b in r0)
        if a_matches_alt and b_matches_alt:
            return True

    return False
