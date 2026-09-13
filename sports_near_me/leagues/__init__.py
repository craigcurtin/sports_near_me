from . import mlb, nfl, nhl
from ._ncaa import NcaaLeague

ncaaf = NcaaLeague("football", "college-football")
ncaamb = NcaaLeague("basketball", "mens-college-basketball")
ncaawb = NcaaLeague("basketball", "womens-college-basketball")
ncaabsb = NcaaLeague("baseball", "college-baseball")
ncaamh = NcaaLeague("hockey", "mens-college-hockey")
ncaavbw = NcaaLeague("volleyball", "womens-college-volleyball")
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
