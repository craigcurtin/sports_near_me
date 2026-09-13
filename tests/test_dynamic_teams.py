from unittest.mock import patch

import pytest

from sports_near_me.dynamic_teams import fetch_all_teams
from sports_near_me.fetch import DataSourceError


def test_fetch_all_teams_happy_path():
    data = {
        "sports": [{"leagues": [{"teams": [
            {"team": {"id": "1", "abbreviation": "TST", "name": "Testers",
                      "location": "Test City", "displayName": "Test City Testers"}},
        ]}]}]
    }
    with patch("sports_near_me.dynamic_teams.fetch_json", return_value=data):
        teams = fetch_all_teams("__fake_sport_happy__", "__fake_league__")
    assert len(teams) == 1
    assert teams[0].id == "1"
    assert teams[0].display_name == "Test City Testers"


def test_fetch_all_teams_bad_shape_raises_data_source_error_with_breadcrumb():
    # A response that's valid JSON but missing the expected "sports" key -
    # exactly what an ESPN-side shape change would look like.
    with patch("sports_near_me.dynamic_teams.fetch_json", return_value={"unexpected": "shape"}):
        with pytest.raises(DataSourceError) as exc_info:
            fetch_all_teams("__fake_sport_badshape__", "__fake_league__")
    message = str(exc_info.value)
    assert "__fake_sport_badshape__" in message
    assert "KeyError" in message
