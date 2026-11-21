# AGENTS.md: apprise-notify

Send a notification to an Apprise API server: one function, standard
library only. User-facing docs: [README.md](README.md).

## Layout

- `src/apprise_notify/`: the package, a library with no console script.
  It imports only the standard library; keep `dependencies` empty.
- `tests/`: pytest. Keep I/O out of the logic so it tests without mocks.

## Conventions

- Conventional Commits, header at most 72 characters. The commit subjects
  that reach main are the release notes: `feat`/`fix`/`perf` release, `refactor`,
  `test`, `docs`, `ci`, `chore` don't (a dependency update to runtime files
  ships in the weekly maintenance release). CI lints every commit with
  [commitlint-config-mbologna](https://github.com/mbologna/commitlint-config)
  and rejects `fixup!` commits; pull requests merge with a merge commit.
- Coverage may not drop below `fail_under` in `pyproject.toml`; raise it
  when tests are added.
- Dependencies: `uv add <pkg>`; uv.lock is committed and CI installs it
  with `--locked`. `exclude-newer` keeps releases younger than 7 days out.
- `requires-python` is `>=3.10`, and ruff's `target-version` matches it.
  CI tests on Python 3.15 only: keep syntax and standard library features
  newer than 3.10 out of the code.

## Versioning

Plain SemVer: `vX.Y.Z` tags with a GitHub Release each, which
`publish.yml` builds and publishes to PyPI with the tag's version, per the
[versioning standard](https://github.com/mbologna/.github/blob/main/VERSIONING.md).

- Never create, move or delete tags, and never edit a version number to cut
  a release: auto-release tags from the commit types (`feat` minor; `fix`,
  `perf`, `revert` patch; `!` or a `BREAKING CHANGE:` footer major).
- Write Conventional Commit subjects; they decide the next version.
- `version` in `pyproject.toml` is a placeholder and stays `0.0.0`; the
  build sets the tag's version. A published version can't be replaced on
  PyPI, so a broken release is fixed by the next one.
- `publish.yml` keeps its name: PyPI's trusted publisher names this
  repository, that workflow file and the `pypi` environment.

## Template

The skeleton comes from https://github.com/mbologna/python-app-template
(`.copier-answers.yml`). Renovate's copier manager opens a pull request
for each template release; resolve conflicts in favour of this project's
code. By hand: `uvx copier update`, then `uv lock` if dependencies changed.
To change an answer: `uvx copier update -d <question>=<value>`.
