from unittest.mock import patch

import pytest

from sports_near_me.conferences import conference_members, resolve_conference
from sports_near_me.fetch import DataSourceError


def test_resolve_conference_happy_path():
    data = {"conferences": [
        {"groupId": "8", "name": "Southeastern Conference", "shortName": "SEC", "parentGroupId": "80"},
        {"groupId": "80", "name": "FBS", "shortName": "FBS"},  # no parentGroupId - filtered out
    ]}
    with patch("sports_near_me.conferences.fetch_json", return_value=data):
        conf = resolve_conference("SEC", "__fake_sport_conf_happy__", "__fake_league__")
    assert conf.id == "8"
    assert conf.display_name == "Southeastern Conference"


def test_resolve_conference_missing_top_level_key_is_empty_not_an_error():
    # "conferences" is read via .get() with a [] default, so a response
    # missing that key entirely resolves to zero conferences (and a plain
    # ValueError from resolve() - "doesn't have a conference called")
    # rather than a DataSourceError. What DOES raise DataSourceError is a
    # conference entry that's present but missing an expected field - see
    # the next test - which is the shape of a real ESPN-side rename,
    # unlike a wholesale missing top-level key.
    with patch("sports_near_me.conferences.fetch_json", return_value={"unexpected": "shape"}):
        with pytest.raises(ValueError, match="doesn't have a conference called"):
            resolve_conference("SEC", "__fake_sport_conf_badshape__", "__fake_league__")


def test_resolve_conference_missing_field_in_entry_raises():
    with patch("sports_near_me.conferences.fetch_json",
               return_value={"conferences": [{"parentGroupId": "80"}]}):  # missing groupId/name
        with pytest.raises(DataSourceError) as exc_info:
            resolve_conference("SEC", "__fake_sport_conf_missingfield__", "__fake_league__")
    assert "KeyError" in str(exc_info.value)


def test_conference_members_happy_path():
    data = {"standings": {"entries": [
        {"team": {"id": "333", "abbreviation": "ALA", "displayName": "Alabama Crimson Tide"}},
    ]}}
    with patch("sports_near_me.conferences.fetch_json", return_value=data):
        members = conference_members("8", "__fake_sport_members_happy__", "__fake_league__")
    assert len(members) == 1
    assert members[0].display_name == "Alabama Crimson Tide"


def test_conference_members_bad_shape_raises_data_source_error_with_breadcrumb():
    with patch("sports_near_me.conferences.fetch_json",
               return_value={"standings": {"entries": [{"team": {"id": "1"}}]}}):  # missing displayName
        with pytest.raises(DataSourceError) as exc_info:
            conference_members("8", "__fake_sport_members_badshape__", "__fake_league__")
    message = str(exc_info.value)
    assert "group_id=8" in message
    assert "KeyError" in message
