"""
Shared HTTP+JSON fetch for every ESPN endpoint this project calls
(espn.py, dynamic_teams.py, conferences.py). ESPN's API is not under this
project's control - ids get renumbered, paths get renamed, response
shapes change (all three have already happened once during this
project's own development: NCAA abbreviation routing collisions, the
season-parameter inconsistency, a school's id differing per sport). When
that happens again, a bare urllib/json/KeyError traceback three stack
frames deep is a bad way to find out - DataSourceError exists so every
failure instead names the URL, what was being attempted, and where in
the source to look, on the way out.
"""

import json
import urllib.error
import urllib.request


class DataSourceError(RuntimeError):
    """Raised for any failure fetching or parsing an ESPN endpoint -
    network failure, non-2xx response, invalid JSON, or JSON that parsed
    fine but didn't have the shape this code expects. Always carries a
    breadcrumb (the URL, what was being attempted, and a pointer to which
    file/function built the request) in its message, so catching and
    printing str(exc) is itself a useful error report - see cli.py's
    top-level handling."""


def fetch_json(url: str, context: str):
    """Fetches one URL and parses it as JSON, with every failure mode
    wrapped to name `context` (what this call was trying to do - the
    caller supplies this, e.g. "fetching NFL schedule for team CHI") and
    `url` (exactly what was requested) in the resulting DataSourceError.
    Callers still need to wrap their OWN parsing of the returned dict
    (KeyError/IndexError/TypeError if ESPN's shape changed) - this only
    covers getting valid JSON back at all."""
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            raw = response.read()
    except urllib.error.HTTPError as e:
        raise DataSourceError(
            f"{context}: ESPN returned HTTP {e.code} ({e.reason}) for {url}\n"
            f"  Likely cause: a stale id/slug baked into this URL - a team or "
            f"conference numeric id, or the sport/league path segment. Check "
            f"whichever leagues/*.py module, dynamic_teams.py, or conferences.py "
            f"built this request."
        ) from e
    except TimeoutError as e:
        raise DataSourceError(f"{context}: timed out reaching {url} - ESPN's API may be slow or down.") from e
    except urllib.error.URLError as e:
        raise DataSourceError(f"{context}: couldn't reach {url} ({e.reason}) - network issue, or ESPN's API is down.") from e

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise DataSourceError(
            f"{context}: ESPN's response for {url} wasn't valid JSON - the API "
            f"likely changed shape, or returned an HTML error page instead of JSON."
        ) from e


def parse_error(context: str, url: str, error: Exception) -> DataSourceError:
    """Wraps a KeyError/IndexError/TypeError hit while walking an
    already-parsed JSON response - the "valid JSON, but not the shape we
    expected" failure mode, distinct from fetch_json()'s "didn't get
    valid JSON at all." Use as `raise parse_error(...) from e` right where
    the shape assumption broke, so the message names the exact field."""
    return DataSourceError(
        f"{context}: ESPN's response for {url} had an unexpected shape "
        f"({type(error).__name__}: {error}) - likely a field renamed, moved, or "
        f"removed on ESPN's side. Compare against a fresh `curl {url}` and the "
        f"parsing code at the point this was raised."
    )
