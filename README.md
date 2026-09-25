[English](README.md) | [Português Brasileiro](README.pt-BR.md)

# SystemPulse

**Open-source real-time system monitoring and diagnostics for Windows, Linux and macOS.**

Know what your computer is doing, without leaving your terminal.

> **Development status:** One-shot CPU, memory, and process commands now work from
> a source checkout. The real-time Textual interface is still in development.
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
- `systempulse status` shows current CPU, memory, and leading processes.
- `systempulse processes` lists processes with CPU and memory sorting, name search,
  and a row limit. Unavailable process fields are labeled explicitly.

The v0.1 target also includes a live process explorer, recent terminal charts,
system information, and `top` and `doctor` commands. These remain planned.

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
uv run systempulse status
uv run systempulse processes --sort memory --limit 10
uv run systempulse processes --search python
uv run systempulse
```

The last command currently reports that the live terminal interface is under
development. `status` and `processes` take two samples about one second apart to
calculate CPU rates; they return a one-shot view and then exit.

## Keyboard shortcuts

There are no TUI shortcuts in this development build. Keyboard navigation will be
documented when the interface is implemented.

## Supported platforms

Windows, Linux, and macOS are planned targets. The current commands have been
executed on Windows; Linux and macOS validation is still pending. Python 3.12+
is required.

## Architecture

The current local pipeline is: typed collectors → sampling service → metric
aggregator → application state → CLI. The Textual interface and an internal event
bus for later history, rules, and alerts are planned. Widgets will not call
`psutil` directly.

The [process scan benchmark methodology](docs/en/benchmarking.md) records how
collector cost is measured during development.

## Privacy and safety

SystemPulse is local-first and read-only. No cloud account, telemetry, tracking,
or remote API is part of the default design. The current commands collect metrics
locally and do not transmit them.

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
