"""
Resolves a conference name (SEC, Big Ten, ACC, ...) to its member teams,
for "follow this whole conference" instead of listing every school by hand.

A conference's numeric group id is DIFFERENT per sport - SEC is group 8 in
football but group 23 in men's basketball - so, same principle as
dynamic_teams.py, nothing is hardcoded or persisted: both the name->groupId
lookup and the groupId->member-teams lookup are fetched fresh each run.
"""

import json
import urllib.request

from .resolve import Team, resolve

CONFERENCES_URL = "https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard/conferences"
STANDINGS_URL = "https://site.api.espn.com/apis/v2/sports/{sport}/{league}/standings?group={group_id}"

# Per-process cache, same reasoning as dynamic_teams.py's - avoid refetching
# within one run, never persisted between runs.
_conference_cache = {}
_members_cache = {}


def _all_conferences(sport: str, league: str) -> list:
    key = (sport, league)
    if key not in _conference_cache:
        url = CONFERENCES_URL.format(sport=sport, league=league)
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.load(response)
        _conference_cache[key] = [
            Team(id=c["groupId"], display_name=c["name"],
                 search_keys=(c["name"].lower(), c.get("shortName", "").lower()))
            for c in data.get("conferences", [])
            if c.get("parentGroupId")  # skip the top-level "FBS"/"Division I" umbrella entries
        ]
    return _conference_cache[key]


def resolve_conference(query: str, sport: str, league: str) -> Team:
    """Returns a Team-shaped object whose id is actually the conference's
    group id - conferences and teams share the same resolve() ambiguity
    handling, so "ACC" is exactly as safe to type as "Duke" is."""
    return resolve(query, _all_conferences(sport, league))


def conference_members(conference_group_id: str, sport: str, league: str) -> list:
    """The actual member teams of a conference, as real Team objects (same
    shape fetch_schedule() needs) - this season's standings list, not a
    hardcoded membership table, so a realignment shows up automatically."""
    key = (sport, league, conference_group_id)
    if key not in _members_cache:
        url = STANDINGS_URL.format(sport=sport, league=league, group_id=conference_group_id)
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.load(response)
        entries = data.get("standings", {}).get("entries", [])
        _members_cache[key] = [
            Team(id=e["team"]["id"], display_name=e["team"]["displayName"],
                 search_keys=(e["team"].get("abbreviation", "").lower(), e["team"]["displayName"].lower()))
            for e in entries
        ]
    return _members_cache[key]
