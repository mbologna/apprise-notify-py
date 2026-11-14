# apprise-notify-py

[![CI](https://github.com/mbologna/apprise-notify-py/actions/workflows/ci.yml/badge.svg)](https://github.com/mbologna/apprise-notify-py/actions/workflows/ci.yml)

Send a notification to an [Apprise API](https://github.com/caronc/apprise-api)
server from a small Python script or CronJob. One function, standard library
only, no dependencies.

```python
from apprise_notify import notify

if not notify("http://apprise:8000/notify/alerts", "Backup failed", "restic exited 1", "failure"):
    ...  # not delivered: don't record it as sent
```

`notify(apprise_url, title, body, type_="info", timeout=15, format_=None)`
POSTs `{"title", "body", "type"}` as JSON and returns whether it was
delivered. A key with no configuration on the server (apprise-api's HTTP 204)
counts as not delivered. `type_` is Apprise's severity: `info`, `success`, `warning` or
`failure`. `format_` (`text`, `markdown` or `html`) adds Apprise's `format`
field, for example to send links; left out, the body is plain text. An
empty URL turns notifications off and returns `False`. Errors are printed to
stderr and never raised, so a notification problem can't crash the caller.

## Several Apprise servers

`apprise_url` can also name several servers, in order of preference: a list,
or one string with the URLs separated by spaces (handy for a single
environment variable).

```python
notify(
    ["http://apprise.local:8000/notify/alerts", "https://apprise.example.org/notify/alerts"],
    "Backup failed",
    "restic exited 1",
    "failure",
)
```

The URLs are tried in order and the first one that delivers wins; the rest
are not called. This is a failover, not a fan-out, so two servers that share
the same Telegram bot don't send the message twice.

| Answer from a URL | What happens |
| --- | --- |
| 2xx (not 204) | delivered: return `True` |
| network error, timeout or 5xx | retry that URL once after one second, then move to the next |
| 4xx, or 204 (no configuration for the key) | move to the next URL at once; a retry wouldn't change the answer |

`notify` returns `False` when no URL delivers. `timeout` applies to each
attempt, so the worst case is about `2 × timeout` per URL.

Passing `None` reads the URLs from the `APPRISE_URLS` environment variable
(same space-separated format); an unset or empty variable turns
notifications off. An empty string still turns them off without looking at
the environment.

```python
notify(None, "Backup failed", "restic exited 1", "failure")  # APPRISE_URLS="http://a/notify/k http://b/notify/k"
```

A single URL behaves as in 1.1.x, except that a network error or 5xx is now
retried once.

## Install

From PyPI (1.2.0 and later):

```sh
pip install apprise-notify
```

```toml
# pyproject.toml
dependencies = ["apprise-notify>=1.2"]
```

Release tags keep working for callers that pin one:

```toml
dependencies = ["apprise-notify @ git+https://github.com/mbologna/apprise-notify-py@v1.2.0"]
```

## Releases

[auto-release](https://github.com/mbologna/auto-release) tags each release
from the Conventional Commits on `main` (Monday's scheduled CI run, or a
manual run) and starts `publish.yml` on the new tag. That workflow builds the
package with the tag's version and uploads it to PyPI through
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/): no PyPI
token is stored in the repository. The version in `pyproject.toml` is not
bumped by the release.

## Development

`uv.lock` only takes releases at least 7 days old (`exclude-newer` in
`pyproject.toml`), so a freshly published, compromised package can't land in
the lock. A CVE fix released less than 7 days ago needs a temporary
`exclude-newer-package = { <package> = false }` override in `[tool.uv]`
followed by `uv lock --upgrade-package <package>`; drop the override once
the release is a week old.
