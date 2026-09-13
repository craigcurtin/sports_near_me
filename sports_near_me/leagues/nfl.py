"""
NFL: 32 teams, and ESPN's own abbreviation routes directly to the right
schedule (no numeric-id detour needed, unlike NCAA). The one thing this
project can't fully resolve is Sunday's FOX/CBS window - see broadcast_note().
"""

from ..resolve import Team, resolve

SPORT, LEAGUE = "football", "nfl"

# Surfaced by cli.py for out-of-market listeners when a game has an audio
# entry. Westwood One is the NFL's own official national radio/audio
# partner (confirmed via Cumulus Media's own announcement) and streams
# every game through its own site/app, not just over the air - all three
# links verified real before being wired in, same as MLB's.
AUDIO_INFO_URL = "https://westwoodonesports.com"
AUDIO_APP_ANDROID_URL = "https://play.google.com/store/apps/details?id=com.westwoodone.sports"
AUDIO_APP_IOS_URL = "https://apps.apple.com/us/app/westwood-one-sports/id6743144592"

# (abbreviation, location, nickname) - matches ESPN's own /teams list.
_RAW_TEAMS = [
    ("ARI", "Arizona", "Cardinals"), ("ATL", "Atlanta", "Falcons"),
    ("BAL", "Baltimore", "Ravens"), ("BUF", "Buffalo", "Bills"),
    ("CAR", "Carolina", "Panthers"), ("CHI", "Chicago", "Bears"),
    ("CIN", "Cincinnati", "Bengals"), ("CLE", "Cleveland", "Browns"),
    ("DAL", "Dallas", "Cowboys"), ("DEN", "Denver", "Broncos"),
    ("DET", "Detroit", "Lions"), ("GB", "Green Bay", "Packers"),
    ("HOU", "Houston", "Texans"), ("IND", "Indianapolis", "Colts"),
    ("JAX", "Jacksonville", "Jaguars"), ("KC", "Kansas City", "Chiefs"),
    ("LAC", "Los Angeles", "Chargers"), ("LAR", "Los Angeles", "Rams"),
    ("LV", "Las Vegas", "Raiders"), ("MIA", "Miami", "Dolphins"),
    ("MIN", "Minnesota", "Vikings"), ("NE", "New England", "Patriots"),
    ("NO", "New Orleans", "Saints"), ("NYG", "New York", "Giants"),
    ("NYJ", "New York", "Jets"), ("PHI", "Philadelphia", "Eagles"),
    ("PIT", "Pittsburgh", "Steelers"), ("SEA", "Seattle", "Seahawks"),
    ("SF", "San Francisco", "49ers"), ("TB", "Tampa Bay", "Buccaneers"),
    ("TEN", "Tennessee", "Titans"), ("WSH", "Washington", "Commanders"),
]

_ALIASES = {
    "niners": "SF", "9ers": "SF", "washington football team": "WSH",
    "redskins": "WSH", "oakland raiders": "LV", "san diego chargers": "LAC",
    "st louis rams": "LAR", "st. louis rams": "LAR",
}


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

# Reach every market, no affiliate map involved - flagship windows and
# streaming exclusives.
NATIONAL_NETWORKS = {
    "NBC", "ABC", "ESPN", "ESPN2", "ESPN+", "PRIME VIDEO",
    "AMAZON PRIME VIDEO", "AMAZON", "NFL NETWORK", "PEACOCK", "NETFLIX",
}
# Sunday afternoon windows - split regionally by affiliate. The only
# networks this tool can't give a definitive yes/no for.
REGIONAL_NETWORKS = {"FOX", "CBS"}


def resolve_team(query: str) -> Team:
    return resolve(query, TEAMS)


def broadcast_note(game) -> str:
    tv_or_stream = [b for b in game.broadcasts if b.medium != "Radio"]
    if not tv_or_stream:
        return "Network not yet announced."
    network = tv_or_stream[0].network
    key = network.strip().upper()
    if key in NATIONAL_NETWORKS:
        return f"{network} - national broadcast, every market gets this one."
    if key in REGIONAL_NETWORKS:
        return (f"{network} - regional Sunday window. This tool can't tell whether it reaches "
                f"you, but https://thesportsmaps.com/nfl/ has a real, current county/zip-level "
                f"coverage map (verified working, updated weekly) - or check the NFL app's Local tab.")
    return f"{network} - unrecognized network, can't classify national vs. regional."
