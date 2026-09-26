# Development

[English](development.md) | [Português Brasileiro](../pt-BR/development.md)

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```sh
uv python install 3.12
uv sync --locked
uv run systempulse
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

`uv run systempulse` requires an interactive terminal. Use `uv run systempulse
status` in a non-interactive shell. Run `uv run python
scripts/benchmark_runtime.py --seconds 10` to measure your host; results vary
with process count, permissions, and workload. `uv build --no-sources` and
`uv run python scripts/smoke_install.py` verify the distribution and installed
command. The smoke test requires uv and may fetch Python or dependencies.

Keep domain models independent of Textual and psutil. Add a typed collector,
register it in the default session, handle unavailability, and test observable
behavior before exposing a new metric. Public behavior needs matching English
and pt-BR documentation. English is canonical. Use Conventional Commits.

The GitHub Actions matrix runs on Ubuntu, Windows, and macOS. Local headless
TUI tests verify interactions, but interactive terminal rendering must still
be checked on each platform before a stable support claim.
