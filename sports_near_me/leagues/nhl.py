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

# Surfaced by cli.py for out-of-market listeners, every game, regardless
# of what ESPN's own (confirmed incomplete) audio data says. Verified
# real and working before wiring in - free, every team, home/away call
# options - with one caveat worth keeping in mind: not available to
# listeners in Canada (rights restriction), which this tool has no way
# to flag per-listener.
OUT_OF_MARKET_AUDIO = [
    ("TuneIn NHL Radio (free)", "https://tunein.com/radio/NHL-Radio--Stream-Hockey-Radio-c393481/"),
]

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

# Verified regional radio/audio flagships, keyed by team abbreviation - see
# nfl.py's KNOWN_AUDIO for why this is small and honestly partial rather
# than a guess at all 32 teams. Particularly worth checking periodically
# here: WGN lost the Cubs' radio rights back in 2014 but holds the
# Blackhawks' under a separate, current multi-year extension - the same
# station name can be right for one team and wrong for another in the
# same city, and wrong again after the next renewal.
KNOWN_AUDIO = {
    "CHI": ("WGN Radio 720 AM", "https://wgnradio.com/blackhawks/blackhawks-live/"),
}


def known_audio(team_id: str):
    return KNOWN_AUDIO.get(team_id)


def resolve_team(query: str) -> Team:
    return resolve(query, TEAMS, "NHL")


def broadcast_note(game) -> str:
    tv_or_stream = [b for b in game.broadcasts if b.medium != "Radio"]
    if not tv_or_stream:
        return ("No national broadcast listed - likely a regional-only game. ESPN's schedule "
                "data doesn't include NHL regional sports networks, so check your team's own "
                "site/app (Bally Sports+, NHL.tv, etc.) directly.")
    network = tv_or_stream[0].network
    return f"{network} - national broadcast, every market gets this one."
