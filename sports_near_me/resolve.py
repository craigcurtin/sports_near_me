"""
Shared "turn whatever a person typed into one specific team" logic, used by
every league. A static list (NFL/MLB - 32/30 teams, no name collisions) and
a dynamically-fetched list (NCAA - hundreds of schools, real collisions
like Duke Blue Devils vs. Duquesne Dukes vs. James Madison Dukes all
matching a bare "duke") both resolve through the same exact-match-first,
flag-ambiguity-second path - NCAA's much bigger, collision-prone name space
gets the same safety NFL/MLB already had, for free.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Team:
    id: str             # what fetch_schedule() needs - an abbreviation for
                         # NFL/MLB, an ESPN numeric team id for NCAA
    display_name: str
    search_keys: tuple  # lowercase strings this team should match on


def resolve(query: str, teams: list) -> Team:
    """Exact match on a search key wins outright. Falling back to a
    substring match only happens when there's no exact match, and is
    itself still subject to the ambiguity check - "duke" partially matches
    three teams' nicknames/locations, so it must raise, not guess."""
    key = query.strip().lower()

    exact = _unique(t for t in teams if key in t.search_keys)
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        _raise_ambiguous(query, exact)

    partial = _unique(t for t in teams if any(key in sk for sk in t.search_keys))
    if len(partial) == 1:
        return partial[0]
    if partial:
        _raise_ambiguous(query, partial)

    raise ValueError(f"'{query}' isn't a team I recognize.")


def _unique(teams) -> list:
    return list({t.id: t for t in teams}.values())


def _raise_ambiguous(query: str, teams: list) -> None:
    options = ", ".join(sorted(t.display_name for t in teams))
    raise ValueError(f"'{query}' matches more than one team: {options}. Be more specific.")
