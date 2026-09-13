import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from sports_near_me.fetch import DataSourceError, fetch_json, parse_error


def _mock_response(body: bytes):
    cm = MagicMock()
    cm.__enter__.return_value.read.return_value = body
    return cm


def test_fetch_json_success():
    with patch("sports_near_me.fetch.urllib.request.urlopen", return_value=_mock_response(b'{"ok": true}')):
        assert fetch_json("https://example.test/x", "testing") == {"ok": True}


def test_fetch_json_http_error_names_url_and_context():
    err = urllib.error.HTTPError("https://example.test/x", 404, "Not Found", {}, None)
    with patch("sports_near_me.fetch.urllib.request.urlopen", side_effect=err):
        with pytest.raises(DataSourceError) as exc_info:
            fetch_json("https://example.test/x", "fetching team_id=999")
    message = str(exc_info.value)
    assert "https://example.test/x" in message
    assert "fetching team_id=999" in message
    assert "404" in message
    # The breadcrumb should point somewhere actionable, not just state the failure.
    assert "leagues/*.py" in message or "dynamic_teams.py" in message or "conferences.py" in message


def test_fetch_json_url_error_names_url_and_context():
    err = urllib.error.URLError("nowhere to be found")
    with patch("sports_near_me.fetch.urllib.request.urlopen", side_effect=err):
        with pytest.raises(DataSourceError) as exc_info:
            fetch_json("https://example.test/x", "testing")
    message = str(exc_info.value)
    assert "https://example.test/x" in message
    assert "testing" in message


def test_fetch_json_invalid_json_names_url_and_context():
    with patch("sports_near_me.fetch.urllib.request.urlopen", return_value=_mock_response(b"<html>not json</html>")):
        with pytest.raises(DataSourceError) as exc_info:
            fetch_json("https://example.test/x", "testing")
    message = str(exc_info.value)
    assert "https://example.test/x" in message
    assert "wasn't valid JSON" in message


def test_fetch_json_original_exception_is_chained():
    # The breadcrumb message matters, but the original exception must
    # still be reachable (via __cause__) for anyone who wants the raw
    # traceback, not just the summary.
    err = urllib.error.HTTPError("https://example.test/x", 500, "Server Error", {}, None)
    with patch("sports_near_me.fetch.urllib.request.urlopen", side_effect=err):
        with pytest.raises(DataSourceError) as exc_info:
            fetch_json("https://example.test/x", "testing")
    assert exc_info.value.__cause__ is err


def test_parse_error_names_url_context_and_field():
    original = KeyError("groupId")
    e = parse_error("fetching conferences", "https://example.test/conf", original)
    message = str(e)
    assert "https://example.test/conf" in message
    assert "fetching conferences" in message
    assert "KeyError" in message
    assert "groupId" in message
