import pytest

from sports_near_me.resolve import Team, resolve

TEAMS = [
    Team(id="CHI", display_name="Chicago Bears", search_keys=("chi", "bears", "chicago", "chicago bears")),
    Team(id="NYG", display_name="New York Giants", search_keys=("nyg", "giants", "new york", "new york giants")),
    Team(id="NYJ", display_name="New York Jets", search_keys=("nyj", "jets", "new york", "new york jets")),
]


def test_exact_match():
    assert resolve("bears", TEAMS, "NFL").id == "CHI"
    assert resolve("CHI", TEAMS, "NFL").id == "CHI"
    assert resolve("chicago bears", TEAMS, "NFL").id == "CHI"


def test_partial_match_unique():
    assert resolve("chi", TEAMS, "NFL").id == "CHI"


def test_ambiguous_exact_match_raises():
    with pytest.raises(ValueError, match="matches more than one team"):
        resolve("new york", TEAMS, "NFL")


def test_ambiguous_partial_match_raises():
    partial_teams = [
        Team(id="DUKE", display_name="Duke Blue Devils", search_keys=("duke", "blue devils")),
        Team(id="DUQ", display_name="Duquesne Dukes", search_keys=("duq", "dukes", "duquesne")),
        Team(id="JMU", display_name="James Madison Dukes", search_keys=("jmu", "dukes", "james madison")),
    ]
    # "duke" exact-matches only Duke itself (its own search key), so it
    # should resolve cleanly even though "dukes" is a substring collision.
    assert resolve("duke", partial_teams, "NCAA football").id == "DUKE"
    # But a genuine partial-only collision (no exact match anywhere) must raise.
    with pytest.raises(ValueError, match="matches more than one team"):
        resolve("dukes", partial_teams, "NCAA football")


def test_unknown_raises_with_sport_and_provider_named():
    # Specific enough to diagnose: which provider (ESPN), which sport
    # (NFL), and that the search term genuinely isn't a team there - not
    # just a generic "not recognized" that reads like a typo when it isn't.
    with pytest.raises(ValueError, match=r"ESPN's NFL data doesn't have a team called 'sasquatches'"):
        resolve("sasquatches", TEAMS, "NFL")


def test_unknown_uses_the_given_label_and_kind():
    with pytest.raises(ValueError, match=r"ESPN's NCAA men's hockey data doesn't have a team called 'Tennessee'"):
        resolve("Tennessee", TEAMS, "NCAA men's hockey")
    with pytest.raises(ValueError, match=r"doesn't have a conference called 'XYZ'"):
        resolve("XYZ", TEAMS, "NCAA football", kind="conference")
