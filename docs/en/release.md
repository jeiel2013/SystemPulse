# Release checks

SystemPulse is a development preview. The package name is `systempulse-monitor`;
its installed command is `systempulse`. No PyPI release has been published.

The [CI workflow](../../.github/workflows/ci.yml) is configured for Ubuntu, Windows, and
macOS. Each job checks Ruff, mypy, the CLI and TUI test suite, builds the source
and wheel distributions, installs the wheel as an isolated uv tool, and runs
`systempulse version`, `status`, `top --help`, `processes`, and `doctor` outside
the checkout.
It also checks that the wheel includes the TUI stylesheet.

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

Publication requires green CI jobs on all three operating systems and a review
of the built artifacts and release notes. Automated TUI tests do not establish
that every terminal renders identically; interactive Linux and macOS validation
remains open. Do not describe that support as fully validated yet.
