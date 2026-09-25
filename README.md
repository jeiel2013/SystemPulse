[English](README.md) | [Português Brasileiro](README.pt-BR.md)

# SystemPulse

**Open-source real-time system monitoring and diagnostics for Windows, Linux and macOS.**

Know what your computer is doing, without leaving your terminal.

> **Development status:** This repository is at the package foundation stage. Live
> monitoring, the Textual interface, and process inspection are not implemented yet.
> No release of this project has been published to PyPI.

SystemPulse is designed as a local, read-only terminal application. Its three guiding
principles are **Measure. Understand. Inform.** Future observations and diagnostics
must be grounded in observable metrics; the application will not infer causality
without evidence.

## Screenshots and terminal recordings

None yet. Recordings will be added when the terminal interface is functional.

## Features

Currently available:

- Installable Python package with a `systempulse` command.
- `systempulse version` reports the installed package version.

The v0.1 target includes live CPU and memory metrics, a process explorer, recent
terminal charts, system information, and `status`, `top`, `processes`, and `doctor`
commands. These are planned features, not current commands.

## Installation

This unreleased development version requires Python 3.12+ and
[uv](https://docs.astral.sh/uv/). From a checkout:

```sh
uv sync
```

The planned distribution name is `systempulse-monitor`, with `systempulse` as the
installed command. Once published, the intended installation is
`pipx install systempulse-monitor`. The `systempulse` distribution name on PyPI
belongs to a separate project.

## Usage

```sh
uv run systempulse version
uv run systempulse
```

The second command currently reports that live monitoring is under development.
It does not open a monitoring interface yet.

## Keyboard shortcuts

There are no TUI shortcuts in this development build. Keyboard navigation will be
documented when the interface is implemented.

## Supported platforms

Windows, Linux, and macOS are planned targets. Cross-platform behavior has not yet
been validated. Python 3.12+ is required.

## Architecture

The intended local pipeline is: typed collectors → sampling service → metric
aggregator → application state → Textual interface and CLI. An internal event bus
will support later history, rules, and alerts. Widgets will not call `psutil`
directly. Components will be added when they have working behavior.

## Privacy and safety

SystemPulse will be local-first and read-only initially. No cloud account,
telemetry, tracking, or remote API is part of the default design. The current
development command does not collect or transmit system metrics.

## Roadmap

| Version | Planned focus |
| --- | --- |
| v0.1 | CPU, memory, processes, real-time TUI, basic CLI |
| v0.2 | Disk, network, process tree |
| v0.3 | SQLite history, terminal charts, reports |
| v0.4 | Rules, alerts, evidence-based observations |
| v0.5 | GPU, battery, sensors |
| v1.0 | Stable cross-platform support and documented plugin API |

## Contributing

Contributions will follow English source code and English-first documentation,
with equivalent pt-BR documentation for public features. The contributing guide
and issue templates are planned before v0.1. For now, run `uv run pytest`,
`uv run ruff check .`, and `uv run mypy` before proposing changes.

## License

SystemPulse is licensed under the [Apache License 2.0](LICENSE).

English documentation is canonical. Portuguese documentation is maintained as a
corresponding translation; when versions diverge, the English version prevails.
