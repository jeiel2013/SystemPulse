# Release checks

SystemPulse is a development preview. The package name is `systempulse-monitor`;
its installed command is `systempulse`. Version `0.1.0.dev0` is available on
[PyPI](https://pypi.org/project/systempulse-monitor/0.1.0.dev0/).

The [CI workflow](../../.github/workflows/ci.yml) is configured for Ubuntu, Windows, and
macOS. Each job checks Ruff, mypy, the CLI and TUI test suite, builds the source
and wheel distributions, installs the wheel as an isolated uv tool, and runs
`systempulse version`, `status`, `top --help`, `processes`, `doctor`, `history`,
`alerts`, `tree`, `report`, and `plugins` outside the checkout. It also checks
that the wheel includes the TUI stylesheet, the source archive includes the
license, and an exported report lands in isolated user data.

Run the same checks locally before a release:

```sh
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest -q
uv build --no-sources
uv run --locked python scripts/smoke_install.py
```

For isolated development and smoke tests, `SYSTEMPULSE_DATA_DIR` and
`SYSTEMPULSE_CONFIG_DIR` override the default per-user data and configuration
directories. Normal operation uses platform-appropriate paths when these
variables are unset.

Publication requires green CI jobs on all three operating systems and a review
of the built artifacts and release notes. Automated TUI tests do not establish
that every terminal renders identically. The maintainer has reported successful
interactive runs on Windows and Linux; macOS interactive validation remains
open. Do not describe all terminal/OS combinations as fully validated yet.

Before each release, verify the trusted publishing configuration for
`systempulse-monitor` on PyPI. Review the
[changelog](../../CHANGELOG.md) and [security policy](../../SECURITY.md), run
the wheel smoke test, then exercise the installed `systempulse` command in a
physical Windows, Linux, and macOS terminal. Check both themes, terminal
resize, process search/details, `q`/`Ctrl+C` exit, and the terminal state after
exit. The current Windows benchmark exceeds the initial idle CPU goal; repeat
longer measurements before stating a performance guarantee. Publishing and
pushing the current local commits are separate maintainer actions.

For a new release, first choose an unused version, update `pyproject.toml`,
run `uv lock`, and update both changelogs. Complete the checks above and commit
the changes. Create and push a tag matching `pyproject.toml` exactly, such as
`v0.1.0.dev1` if the new version is `0.1.0.dev1`.
In the repository's GitHub **Actions** tab, open
**Publish to PyPI**, click **Run workflow**, leave the branch as `main`, and
enter the tag in **Release tag**. Click **Run workflow** to start publication;
approve the `pypi` environment if required. No GitHub CLI is needed.

The [workflow](../../.github/workflows/publish.yml) checks out the requested
tag, rejects a version mismatch, reruns quality checks, builds and tests the
distribution, then publishes through PyPI Trusted Publishing. A missing tag
fails checkout. Configure the
GitHub `pypi` environment with a required reviewer and register this workflow
as a [PyPI trusted publisher](https://docs.pypi.org/trusted-publishers/)
before dispatch. No workflow runs publication on a normal push.

A README change pushed to GitHub updates the repository page only. PyPI uses
the README packaged with the release; publish a new version to update it.
Do not reuse the already published `v0.1.0.dev0` tag for new contents.
