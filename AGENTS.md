# AGENTS.md

Notes for coding agents working in this repository. [README.md](README.md) covers what it does and how to use it.

## Versioning

Plain SemVer: `vX.Y.Z` tags, each publishing `apprise-notify` `X.Y.Z` to
PyPI (`publish.yml`) and a GitHub Release, per the
[versioning standard](https://github.com/mbologna/.github/blob/main/VERSIONING.md).

- Never create, move or delete tags, and never edit a version number to cut
  a release: auto-release tags from the commit types (`feat` minor; `fix`,
  `perf`, `revert` patch; `!` or a `BREAKING CHANGE:` footer major).
- Write Conventional Commit subjects; they decide the next version.
- Leave `version` in `pyproject.toml` alone: `publish.yml` sets it from the
  tag (`uv version`) before building, so the committed value only matters
  for a build from a checkout and may lag the tags.
