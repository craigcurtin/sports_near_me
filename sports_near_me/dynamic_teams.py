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

import json
import urllib.request

from .resolve import Team

TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams?limit=1000"

# Per-process cache (sport, league) -> list[Team] - avoids refetching a
# 300+ team list once per followed team in the same run, without ever
# persisting it between runs.
_cache = {}


def fetch_all_teams(sport: str, league: str) -> list:
    key = (sport, league)
    if key not in _cache:
        url = TEAMS_URL.format(sport=sport, league=league)
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.load(response)
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
    return _cache[key]
