[English](README.md) | [Português Brasileiro](README.pt-BR.md)

# SystemPulse

**Open-source real-time system monitoring and diagnostics for Windows, Linux and macOS.**

Know what your computer is doing, without leaving your terminal.

> **Development status:** The live Textual overview, interactive process
> explorer, and one-shot CLI commands work from a source checkout. No release
> of this project has been published to PyPI.

SystemPulse is designed as a local, read-only terminal application. Its three guiding
principles are **Measure. Understand. Inform.** Future observations and diagnostics
must be grounded in observable metrics; the application will not infer causality
without evidence.

## Screenshots and terminal recordings

None yet. Recordings are planned before the first release.

## Features

Currently available:

- Installable Python package with a `systempulse` command.
- `systempulse` opens a live overview with CPU, memory, recent CPU activity, and
  leading CPU processes in an interactive terminal.
- The Processes view provides live search, CPU/memory/PID sorting, keyboard
  selection, and verified details for a selected process. Fields blocked by
  the operating system are marked unavailable.
- `systempulse version` reports the installed package version.
- `systempulse status` shows current CPU, memory, and leading processes.
- `systempulse processes` lists processes with CPU and memory sorting, name search,
  and a row limit. Unavailable process fields are labeled explicitly.

The remaining v0.1 target includes system information and `top` and `doctor`
commands. These remain planned.

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
uv run systempulse
uv run systempulse version
uv run systempulse status
uv run systempulse processes --sort memory --limit 10
uv run systempulse processes --search python
```

The first command requires an interactive terminal. `status` and `processes` take
two samples about one second apart to calculate CPU rates; they return a one-shot
view and then exit.

## Keyboard shortcuts

| Key | Action |
| --- | --- |
| `q`, `Ctrl+C` | Quit |
| `r` | Request a full refresh |
| `1` | Open Overview |
| `2` | Open Processes |
| `/` | Focus process search in Processes |
| `c`, `m`, `p` | Sort processes by CPU, memory, or PID |
| `Enter` | Open selected process details |
| `Esc` | Return from search to the table, or close details |

Type a search term to filter process names. Press `Enter` in the search field
to return to the table. While details are open, `q` closes the details view.

## Supported platforms

Windows, Linux, and macOS are planned targets. The commands and TUI have been
executed on Windows; Linux and macOS validation is still pending. Python 3.12+
is required. The overview scrolls vertically when the terminal is too small to
show every panel at once.

## Architecture

The current local pipeline is: typed collectors → sampling service → metric
aggregator → application state → Textual interface and CLI. Collectors run outside
the TUI event loop and have independent sampling intervals. An internal event bus
for later history, rules, and alerts is planned. Widgets do not call `psutil`
directly. Detailed process facts are read on demand after checking the process
identity with both PID and creation time.

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
