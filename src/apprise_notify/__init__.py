"""Send a notification to an Apprise API server.

One function, standard library only, for small scripts and CronJobs that
report to an Apprise HTTP API (https://github.com/caronc/apprise-api)
endpoint, for example http://apprise:8000/notify/<tag>. Several endpoints can
be given in order of preference: the first one that delivers wins.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

__all__ = ["notify"]

# Seconds to wait before the one retry of a URL that failed transiently
# (network error or HTTP 5xx). Module-level so tests can set it to 0.
RETRY_DELAY = 1.0


def _urls(apprise_url):
    """Return the list of URLs to try, in order.

    A string may hold several URLs separated by whitespace (the format a
    single environment variable carries); a list or tuple holds one URL per
    item. None falls back to the APPRISE_URLS environment variable.
    """
    if apprise_url is None:
        apprise_url = os.environ.get("APPRISE_URLS", "")
    if isinstance(apprise_url, str):
        return apprise_url.split()
    return [u.strip() for u in apprise_url if u and u.strip()]


def _post(url, data, title, timeout):
    """POST once. Return "ok", "skip" (don't retry this URL) or "retry"."""
    try:
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            # apprise-api answers 204 when the key has no configuration: the
            # request is "fine", but nothing was sent to anyone.
            if resp.status == 204:
                print(f"notify failed for {title!r}: no Apprise configuration for {url}", file=sys.stderr)
                return "skip"
            return "ok"
    except urllib.error.HTTPError as e:
        print(f"notify failed for {title!r}: {e}", file=sys.stderr)
        # 4xx is a request or configuration problem that a retry won't fix;
        # 5xx may be transient.
        return "retry" if e.code >= 500 else "skip"
    except (urllib.error.URLError, OSError) as e:
        print(f"notify failed for {title!r}: {e}", file=sys.stderr)
        return "retry"
    except ValueError as e:
        # A malformed URL (no scheme, bad port): a retry can't help.
        print(f"notify failed for {title!r}: {e}", file=sys.stderr)
        return "skip"


def notify(apprise_url, title, body, type_="info", timeout=15, format_=None):
    """POST one notification and return whether it was delivered.

    apprise_url is one Apprise API URL, several separated by whitespace, or a
    list of URLs. They are tried in order and the first that delivers wins,
    so the others are not called: an ordered failover, not a fan-out. A
    network error or HTTP 5xx is retried once after RETRY_DELAY seconds
    before moving on; HTTP 4xx and 204 move on at once. None reads the
    APPRISE_URLS environment variable instead.

    type_ is Apprise's severity: info, success, warning or failure. format_ is
    the body's format: text, markdown or html; None leaves it out, so Apprise
    treats the body as plain text. An empty apprise_url disables
    notifications and returns False, and so does a key with no configuration
    on the server (HTTP 204) when no other URL delivers. Failures are printed
    to stderr, never raised, so a notification problem can't crash the
    caller; callers that keep "already sent" state should record only what
    returned True.
    """
    try:
        urls = _urls(apprise_url)
    except (TypeError, AttributeError):
        print(f"notify failed for {title!r}: unsupported apprise_url {type(apprise_url).__name__}", file=sys.stderr)
        return False
    if not urls:
        return False
    payload = {"title": title, "body": body, "type": type_}
    if format_:
        payload["format"] = format_
    data = json.dumps(payload).encode()
    for url in urls:
        for attempt in range(2):
            result = _post(url, data, title, timeout)
            if result == "ok":
                return True
            if result == "skip" or attempt == 1:
                break
            time.sleep(RETRY_DELAY)
    return False
