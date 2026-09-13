"""
NFL: 32 teams, and ESPN's own abbreviation routes directly to the right
schedule (no numeric-id detour needed, unlike NCAA). The one thing this
project can't fully resolve is Sunday's FOX/CBS window - see broadcast_note().
"""

from ..resolve import Team, resolve

SPORT, LEAGUE = "football", "nfl"

# Surfaced by cli.py for out-of-market listeners, every game, regardless
# of what ESPN's own (confirmed incomplete) audio data says. Every entry
# verified real and free before being wired in - SiriusXM/TuneIn Premium
# were checked too and deliberately left out: both require a paid
# subscription for out-of-market NFL games in the US, unlike these two.
#   - Westwood One: the NFL's own official national radio/audio partner
#     (confirmed via Cumulus Media's own announcement), one national call
#     per game, streamed through its own site/app.
#   - iHeartRadio: free access to each team's own local station stream,
#     not just one national call - a real complement to Westwood One, not
#     a duplicate of it.
OUT_OF_MARKET_AUDIO = [
    ("Westwood One (national call)", "https://westwoodonesports.com"),
    ("Westwood One - Android app", "https://play.google.com/store/apps/details?id=com.westwoodone.sports"),
    ("Westwood One - iOS app", "https://apps.apple.com/us/app/westwood-one-sports/id6743144592"),
    ("iHeartRadio (free, each team's own station)",
     "https://www.iheart.com/content/2025-07-31-live-nfl-radio-listen-to-every-game-free-on-iheartradio/"),
]

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


# Verified regional radio/audio flagships, keyed by team abbreviation.
# ESPN's own broadcasts data is CONFIRMED incomplete here - a real Bears
# game came back with no audio entry at all despite WBBM actively
# carrying every Bears game under a standing multi-year extension (checked
# by hand, not inferred). This is deliberately a small, honestly-partial
# table rather than either a blanket "check locally" shrug or a guess at
# all 32 teams - only entries verified via a real source are here. These
# ARE real contracts that get renegotiated every several years (the Cubs
# alone changed flagship stations three times in the last decade - see
# mlb.py's KNOWN_AUDIO), so each entry should be re-checked periodically,
# not treated as permanent once true.
KNOWN_AUDIO = {
    "CHI": ("WBBM Newsradio 780 AM / 105.9 FM",
            "https://www.chicagobears.com/audio/listen-live-on-wbbm-newsradio-780-105-9-fm"),
    "GB": ("95.7 BIG FM (WRIT), Packers Radio Network",
           "https://www.packers.com/video/radio-network"),
    "MIN": ("KFAN 100.3 FM (KFXN), Vikings Radio Network",
            "https://www.vikings.com/audio/radio-network"),
    "KC": ("96.5 The Fan (KFNZ)", "https://www.chiefs.com/listen/"),
    "DET": ("97.1 The Ticket (WXYT), Lions Radio Network",
            "https://www.detroitlions.com/tunein/lions-radio-network"),
}


def known_audio(team_id: str):
    return KNOWN_AUDIO.get(team_id)


def resolve_team(query: str) -> Team:
    return resolve(query, TEAMS, "NFL")


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
