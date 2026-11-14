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
dependencies = ["apprise-notify @ git+https://github.com/mbologna/apprise-notify-py@v1.1.1"]
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
