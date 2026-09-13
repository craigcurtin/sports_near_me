from . import mlb, nfl, nhl
from ._ncaa import NcaaLeague

# Verified NCAA audio flagships, one dict per sport - a school's ESPN team
# id is specific to the (sport, league) pair (see dynamic_teams.py), so
# Tennessee is "2633" in football/men's/women's basketball but "199" in
# baseball; these can't be merged into one shared table. The Vol Network
# itself (confirmed via utsports.com, Tennessee's own athletics site)
# covers all four of these sports for Tennessee, which is why it repeats
# below rather than appearing once - each entry is still the same real
# fact, just keyed to that sport's own id.
_NCAAF_KNOWN_AUDIO = {
    "2633": ("Vol Network (Tennessee)", "https://utsports.com/sports/vol-network"),  # Tennessee Volunteers
    # Wisconsin: multiple market-specific stations (Madison: WIBA/FOX
    # Sports 1070; Milwaukee: WTMJ/ESPN Milwaukee), not one clean flagship
    # brand the way Tennessee's Vol Network is - and the specific station
    # URLs churn (one redirected through two rebrands while checking this
    # one). Linking the athletics department's own page instead, for the
    # same reason as everywhere else here: more durable than a third-party
    # station URL.
    "275": ("Wisconsin Badgers Sports Network", "https://uwbadgers.com/coverage"),  # Wisconsin Badgers
}
_NCAAMB_KNOWN_AUDIO = {
    "2633": ("Vol Network (Tennessee)", "https://utsports.com/sports/vol-network"),  # Tennessee Volunteers
    "275": ("Wisconsin Badgers Sports Network", "https://uwbadgers.com/coverage"),  # Wisconsin Badgers - Matt Lepay calls football + men's basketball, same network as ncaaf's entry
}
_NCAAWB_KNOWN_AUDIO = {
    "2633": ("Vol Network (Tennessee)", "https://utsports.com/sports/vol-network"),  # Tennessee Lady Volunteers
    "275": ("Wisconsin Badgers Sports Network", "https://uwbadgers.com/coverage"),  # Wisconsin Badgers - Jon Arias calls women's basketball + volleyball
}
_NCAABSB_KNOWN_AUDIO = {
    "199": ("Vol Network (Tennessee)", "https://utsports.com/sports/vol-network"),  # Tennessee Volunteers - different id than football/basketball
}
_NCAAMH_KNOWN_AUDIO = {
    "275": ("Wisconsin Badgers Sports Network", "https://uwbadgers.com/coverage"),  # Wisconsin Badgers - Brian Posick calls men's hockey
}
_NCAAVBW_KNOWN_AUDIO = {
    "275": ("Wisconsin Badgers Sports Network", "https://uwbadgers.com/coverage"),  # Wisconsin Badgers - Jon Arias calls volleyball (same network as ncaawb's entry)
}
# No _NCAAVBM_KNOWN_AUDIO: Wisconsin has no men's volleyball program at
# all (confirmed - absent from ESPN's 75-team mens-college-volleyball
# list; it's a niche varsity sport most Big Ten schools, including
# Wisconsin, don't sponsor - the Badgers are a women's volleyball power,
# not a men's program).

ncaaf = NcaaLeague("football", "college-football", known_audio=_NCAAF_KNOWN_AUDIO)
ncaamb = NcaaLeague("basketball", "mens-college-basketball", known_audio=_NCAAMB_KNOWN_AUDIO)
ncaawb = NcaaLeague("basketball", "womens-college-basketball", known_audio=_NCAAWB_KNOWN_AUDIO)
ncaabsb = NcaaLeague("baseball", "college-baseball", known_audio=_NCAABSB_KNOWN_AUDIO)
ncaamh = NcaaLeague("hockey", "mens-college-hockey", known_audio=_NCAAMH_KNOWN_AUDIO)
ncaavbw = NcaaLeague("volleyball", "womens-college-volleyball", known_audio=_NCAAVBW_KNOWN_AUDIO)
ncaavbm = NcaaLeague("volleyball", "mens-college-volleyball")

# Registry every CLI subcommand and the follow-list config resolve against.
# Order here is the order subcommands are listed in --help.
LEAGUES = {
    "nfl": nfl,
    "mlb": mlb,
    "nhl": nhl,
    "ncaaf": ncaaf,
    "ncaamb": ncaamb,     # NCAA men's basketball
    "ncaawb": ncaawb,     # NCAA women's basketball
    "ncaabsb": ncaabsb,   # NCAA baseball
    "ncaamh": ncaamh,     # NCAA men's hockey
    "ncaavbw": ncaavbw,   # NCAA women's volleyball
    "ncaavbm": ncaavbm,   # NCAA men's volleyball
}
