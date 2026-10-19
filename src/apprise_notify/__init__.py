"""Send a notification to an Apprise API server.

One function, standard library only, for small scripts and CronJobs that
report to an Apprise HTTP API (https://github.com/caronc/apprise-api)
endpoint, for example http://apprise:8000/notify/<tag>.
"""

import json
import sys
import urllib.error
import urllib.request

__all__ = ["notify"]


def notify(apprise_url, title, body, type_="info", timeout=15, format_=None):
    """POST one notification to apprise_url and return whether it was accepted.

    type_ is Apprise's severity: info, success, warning or failure. format_ is
    the body's format: text, markdown or html; None leaves it out, so Apprise
    treats the body as plain text. An empty
    apprise_url disables notifications and returns False. Failures are printed
    to stderr, never raised, so a notification problem can't crash the caller;
    callers that keep "already sent" state should record only what returned
    True.
    """
    if not apprise_url:
        return False
    payload = {"title": title, "body": body, "type": type_}
    if format_:
        payload["format"] = format_
    data = json.dumps(payload).encode()
    req = urllib.request.Request(apprise_url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except (urllib.error.URLError, OSError) as e:
        print(f"notify failed for {title!r}: {e}", file=sys.stderr)
        return False
