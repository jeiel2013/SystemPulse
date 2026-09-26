# Contributing

[English](CONTRIBUTING.md) | [Português Brasileiro](CONTRIBUTING.pt-BR.md)

Thanks for helping improve SystemPulse. Start with an issue for a bug, a
platform-specific observation, or a focused feature proposal. Good first
issues include improving empty states, adding collector fixtures from real
platform output with private details removed, and clarifying documentation.

Set up the project with `uv sync --locked`. Before a pull request, run
`uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, and
`uv run mypy`. For installation changes, also run `uv build --no-sources` and
`uv run python scripts/smoke_install.py`. See the
[development guide](docs/en/development.md).

Keep changes small and describe what was measured or tested. Include the host
OS and terminal when reporting visual or platform bugs. Avoid claims of cause
without evidence. New collectors must fail independently and preserve UTC
timestamps. Do not add network access or destructive process actions by
default. Keep code and canonical documentation in English; update the
corresponding pt-BR document for public changes. Use Conventional Commits.

Security issues should follow the [security policy](SECURITY.md), not public
issues. All participants follow the [code of conduct](CODE_OF_CONDUCT.md).
