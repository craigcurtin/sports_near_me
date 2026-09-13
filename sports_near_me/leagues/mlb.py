"""
MLB: 30 teams, abbreviations route cleanly like NFL. Unlike NFL, ESPN
reports each game's REAL national/home/away broadcast split directly on
every game - no affiliate-map guessing needed, just read market_type off
each entry. That's a strictly better answer than NFL gets: "national
streaming on MLB.TV" plus "home broadcast: Marquee Sports Net" plus "away
broadcast: Nationals.TV" is the actual, complete picture, not a guess.
"""

from ..resolve import Team, resolve

SPORT, LEAGUE = "baseball", "mlb"

# Surfaced by cli.py for out-of-market listeners, every game, regardless
# of what ESPN's own (confirmed incomplete) audio data says. All three
# verified directly (not guessed) before being wired in: the subscription
# page, and both app-store listings since the audio product is consumed
# through the MLB App on a phone as much as the web.
OUT_OF_MARKET_AUDIO = [
    ("MLB Audio subscription", "https://www.mlb.com/live-stream-games/subscribe/mlb-audio"),
    ("MLB App - Android", "https://play.google.com/store/apps/details?id=com.bamnetworks.mobile.android.gameday.atbat"),
    ("MLB App - iOS", "https://apps.apple.com/us/app/mlb/id493619333"),
]

_RAW_TEAMS = [
    ("ARI", "Arizona", "Diamondbacks"), ("ATL", "Atlanta", "Braves"),
    ("BAL", "Baltimore", "Orioles"), ("BOS", "Boston", "Red Sox"),
    ("CHC", "Chicago", "Cubs"), ("CWS", "Chicago", "White Sox"),
    ("CIN", "Cincinnati", "Reds"), ("CLE", "Cleveland", "Guardians"),
    ("COL", "Colorado", "Rockies"), ("DET", "Detroit", "Tigers"),
    ("HOU", "Houston", "Astros"), ("KC", "Kansas City", "Royals"),
    ("LAA", "Los Angeles", "Angels"), ("LAD", "Los Angeles", "Dodgers"),
    ("MIA", "Miami", "Marlins"), ("MIL", "Milwaukee", "Brewers"),
    ("MIN", "Minnesota", "Twins"), ("NYM", "New York", "Mets"),
    ("NYY", "New York", "Yankees"), ("OAK", "Athletics", "Athletics"),
    ("PHI", "Philadelphia", "Phillies"), ("PIT", "Pittsburgh", "Pirates"),
    ("SD", "San Diego", "Padres"), ("SEA", "Seattle", "Mariners"),
    ("SF", "San Francisco", "Giants"), ("STL", "St. Louis", "Cardinals"),
    ("TB", "Tampa Bay", "Rays"), ("TEX", "Texas", "Rangers"),
    ("TOR", "Toronto", "Blue Jays"), ("WSH", "Washington", "Nationals"),
]

_ALIASES = {"chisox": "CWS", "chi sox": "CWS", "nats": "WSH", "d-backs": "ARI", "dbacks": "ARI"}


def _build_teams() -> list:
    by_abbr = {}
    for abbr, location, nickname in _RAW_TEAMS:
        full = f"{location} {nickname}"
        by_abbr[abbr] = {abbr.lower(), nickname.lower(), location.lower(), full.lower()}
    for alias, abbr in _ALIASES.items():
        by_abbr[abbr].add(alias)
    return [
        Team(id=abbr, display_name=f"{loc} {nick}", search_keys=tuple(by_abbr[abbr]))
        for abbr, loc, nick in _RAW_TEAMS
    ]


TEAMS = _build_teams()

_MARKET_LABELS = {"National": "National", "Home": "Home broadcast", "Away": "Away broadcast"}

# Verified regional radio/audio flagships, keyed by team abbreviation - see
# nfl.py's KNOWN_AUDIO for why this is small and honestly partial rather
# than a guess at all 30 teams. The Cubs specifically illustrate why this
# needs periodic re-verification, not a "set once" table: their flagship
# moved WGN -> WBBM -> WSCR across roughly the last decade of real
# contract changes.
KNOWN_AUDIO = {
    "CHC": ("WSCR 670 The Score", "https://www.audacy.com/670thescore"),
    "CWS": ("ESPN 1000 AM / 100.3 FM (WMVP)", "https://tunein.com/radio/ESPN-Chicago-1000-s21297/"),
    "MIL": ("WTMJ 620 AM / 103.3 FM", "https://www.audacy.com/620wtmj/listen"),
}


def known_audio(team_id: str):
    return KNOWN_AUDIO.get(team_id)


def resolve_team(query: str) -> Team:
    return resolve(query, TEAMS, "MLB")


def broadcast_note(game) -> str:
    tv_or_stream = [b for b in game.broadcasts if b.medium != "Radio"]
    if not tv_or_stream:
        return "Network not yet announced."
    parts = [
        f"{_MARKET_LABELS.get(b.market_type, b.market_type)}: {b.network} ({b.medium})"
        for b in tv_or_stream
    ]
    note = " | ".join(parts)
    if any("MLB.TV" in b.network for b in tv_or_stream):
        note += ("  [MLB.TV blacks out both teams' home markets - if you're in one of those "
                 "two, use the Home/Away channel listed instead.]")
    return note
