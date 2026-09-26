# Release checks

SystemPulse is a development preview. The package name is `systempulse-monitor`;
its installed command is `systempulse`. No PyPI release has been published.

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
that every terminal renders identically; interactive Linux and macOS validation
remains open. Do not describe that support as fully validated yet.

Before publishing, confirm the `systempulse-monitor` name can be used by this
project on PyPI and configure a trusted publishing identity. Review the
[changelog](../../CHANGELOG.md) and [security policy](../../SECURITY.md), run
the wheel smoke test, then exercise the installed `systempulse` command in a
physical Windows, Linux, and macOS terminal. Check both themes, terminal
resize, process search/details, `q`/`Ctrl+C` exit, and the terminal state after
exit. The current Windows benchmark exceeds the initial idle CPU goal; repeat
longer measurements before stating a performance guarantee. Publishing and
pushing the current local commits are separate maintainer actions.

After these checks, create a tag matching `pyproject.toml` exactly, such as
`v0.1.0.dev0`, and manually dispatch
[Publish to PyPI](../../.github/workflows/publish.yml) from that tag. The
workflow rejects a mismatched tag, reruns quality checks, builds and tests the
distribution, then publishes through PyPI Trusted Publishing. Configure the
GitHub `pypi` environment with a required reviewer and register this workflow
as a [PyPI trusted publisher](https://docs.pypi.org/trusted-publishers/)
before dispatch. No workflow runs publication on a normal push.
