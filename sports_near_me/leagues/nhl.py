"""
NHL: 32 teams, abbreviations route cleanly. Unlike MLB, ESPN's schedule
data does NOT report regional-sports-network broadcasts for the NHL - most
non-national games come back with an empty broadcasts list, not a Home/Away
entry the way MLB gives you. So an empty list here means "probably a
regional-only game your team's local RSN/streaming app carries," not
"nothing airs" - broadcast_note() says that explicitly rather than
implying the game isn't televised at all.
"""

from ..resolve import Team, resolve

SPORT, LEAGUE = "hockey", "nhl"

_RAW_TEAMS = [
    ("ANA", "Anaheim", "Ducks"), ("BOS", "Boston", "Bruins"),
    ("BUF", "Buffalo", "Sabres"), ("CGY", "Calgary", "Flames"),
    ("CAR", "Carolina", "Hurricanes"), ("CHI", "Chicago", "Blackhawks"),
    ("COL", "Colorado", "Avalanche"), ("CBJ", "Columbus", "Blue Jackets"),
    ("DAL", "Dallas", "Stars"), ("DET", "Detroit", "Red Wings"),
    ("EDM", "Edmonton", "Oilers"), ("FLA", "Florida", "Panthers"),
    ("LA", "Los Angeles", "Kings"), ("MIN", "Minnesota", "Wild"),
    ("MTL", "Montreal", "Canadiens"), ("NSH", "Nashville", "Predators"),
    ("NJ", "New Jersey", "Devils"), ("NYI", "New York", "Islanders"),
    ("NYR", "New York", "Rangers"), ("OTT", "Ottawa", "Senators"),
    ("PHI", "Philadelphia", "Flyers"), ("PIT", "Pittsburgh", "Penguins"),
    ("SJ", "San Jose", "Sharks"), ("SEA", "Seattle", "Kraken"),
    ("STL", "St. Louis", "Blues"), ("TB", "Tampa Bay", "Lightning"),
    ("TOR", "Toronto", "Maple Leafs"), ("UTAH", "Utah", "Mammoth"),
    ("VAN", "Vancouver", "Canucks"), ("VGK", "Vegas", "Golden Knights"),
    ("WSH", "Washington", "Capitals"), ("WPG", "Winnipeg", "Jets"),
]


def _build_teams() -> list:
    return [
        Team(id=abbr, display_name=f"{loc} {nick}",
             search_keys=(abbr.lower(), nick.lower(), loc.lower(), f"{loc} {nick}".lower()))
        for abbr, loc, nick in _RAW_TEAMS
    ]


TEAMS = _build_teams()


def resolve_team(query: str) -> Team:
    return resolve(query, TEAMS)


def broadcast_note(game) -> str:
    tv_or_stream = [b for b in game.broadcasts if b.medium != "Radio"]
    if not tv_or_stream:
        return ("No national broadcast listed - likely a regional-only game. ESPN's schedule "
                "data doesn't include NHL regional sports networks, so check your team's own "
                "site/app (Bally Sports+, NHL.tv, etc.) directly.")
    network = tv_or_stream[0].network
    return f"{network} - national broadcast, every market gets this one."
