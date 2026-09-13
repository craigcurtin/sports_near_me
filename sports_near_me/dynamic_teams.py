"""
Team resolution for leagues with too many schools to hand-maintain a table
for (NCAA: 300-400+ teams per sport) and real abbreviation-routing
collisions (confirmed: .../teams/osu/schedule silently answers with a small
branch-campus team, not Ohio State) - so every NCAA lookup goes through the
numeric team id from ESPN's own live team list, fetched fresh each run.

That "fetched fresh each run, nothing persisted" part matters: this module
never writes a name->id mapping to disk or the config file. If ESPN ever
changed a school's id, the next run just resolves the name against
whatever id is current - there's no stale mapping anywhere to go wrong.
"""

from .fetch import fetch_json, parse_error
from .resolve import Team

TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams?limit=1000"

# Per-process cache (sport, league) -> list[Team] - avoids refetching a
# 300+ team list once per followed team in the same run, without ever
# persisting it between runs.
_cache = {}


def fetch_all_teams(sport: str, league: str) -> list:
    """Every team in this sport/league, fetched fresh (subject to the
    per-process cache above). Any failure - unreachable URL, non-2xx
    response, invalid JSON, or JSON missing the shape expected below -
    raises fetch.DataSourceError naming the URL and what was being
    attempted, rather than a bare KeyError with no indication of where
    to look."""
    key = (sport, league)
    if key not in _cache:
        url = TEAMS_URL.format(sport=sport, league=league)
        context = f"fetching {sport}/{league} team list"
        data = fetch_json(url, context)
        try:
            raw = data["sports"][0]["leagues"][0]["teams"]
            _cache[key] = [
                Team(
                    id=t["team"]["id"],
                    display_name=t["team"]["displayName"],
                    search_keys=(
                        t["team"].get("abbreviation", "").lower(),
                        t["team"].get("name", "").lower(),
                        t["team"].get("location", "").lower(),
                        t["team"]["displayName"].lower(),
                    ),
                )
                for t in raw
            ]
        except (KeyError, IndexError, TypeError) as e:
            raise parse_error(context, url, e) from e
    return _cache[key]
