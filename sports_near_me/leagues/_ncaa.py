"""
Shared implementation for every NCAA sport (football, both basketball
genders, baseball, men's hockey, both volleyball genders): identical team/
conference resolution (dynamic - too many schools, and real name/
abbreviation collisions, to hand-maintain a table - see dynamic_teams.py
and conferences.py) and identical broadcast classification.

That classification is genuinely the same across every NCAA sport: a
conference TV/streaming deal (BTN, ACCN, SECN, ESPN+, etc.) is one single
nationally-distributed feed of that specific game - not NFL's regional-
affiliate-map situation - so "national" here just means "you need the
right cable/streaming package," never "check a coverage map."
"""

from ..conferences import conference_members, resolve_conference
from ..dynamic_teams import fetch_all_teams
from ..resolve import resolve


class NcaaLeague:
    def __init__(self, sport: str, league: str):
        self.SPORT = sport
        self.LEAGUE = league

    def resolve_team(self, query: str):
        return resolve(query, fetch_all_teams(self.SPORT, self.LEAGUE))

    def resolve_conf(self, query: str):
        return resolve_conference(query, self.SPORT, self.LEAGUE)

    def conf_members(self, conference_id: str) -> list:
        return conference_members(conference_id, self.SPORT, self.LEAGUE)

    def broadcast_note(self, game) -> str:
        tv_or_stream = [b for b in game.broadcasts if b.medium != "Radio"]
        if not tv_or_stream:
            return "Network not yet announced."
        b = tv_or_stream[0]
        return (f"{b.network} ({b.medium}) - a single national telecast/stream of this specific "
                f"game. Unlike NFL Sunday, there's no regional affiliate split here - you just "
                f"need the right cable/streaming access to that channel.")
