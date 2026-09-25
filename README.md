[English](README.md) | [Português Brasileiro](README.pt-BR.md)

# SystemPulse

**Know what your computer is doing without leaving the terminal.**

SystemPulse is an open-source, local, read-only system monitor. It shows live
CPU, memory, process, and available GPU readings in a keyboard-driven terminal
interface. It has no web dashboard, account, or telemetry. Evidence-based
diagnostics and alerts are planned; `doctor` currently checks SystemPulse itself.

> **Development preview:** Run from a source checkout. This project has not
> been published to PyPI. The planned distribution name is
> `systempulse-monitor`; its command is `systempulse`.

## Run it

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/). From the project
directory:

```sh
uv sync
uv run systempulse
```

The second command opens the TUI in an interactive terminal. No configuration
or elevated permissions are needed for the default experience.

## What you can see

- **Overview:** live CPU and RAM, a recent CPU chart, optional GPU load/VRAM/
  temperature, and separate Top CPU and Top RAM process lists.
- **Processes:** search, sort by CPU, memory, or PID, and open verified process
  details. Restricted fields appear as unavailable.
- **System:** operating system, uptime, CPU and memory information, and every
  GPU reported by the active provider.

GPU readings currently require NVIDIA's `nvidia-smi`. Without it, SystemPulse
continues running and marks GPU metrics unavailable. AMD and Intel providers
are not implemented yet. See [GPU collection](docs/en/gpu.md).

## Other commands

```sh
uv run systempulse status
uv run systempulse processes --sort memory --limit 10
uv run systempulse processes --search python
uv run systempulse doctor
uv run systempulse version
```

`status` prints one system snapshot. `processes` prints a filtered process
list. `doctor` checks the runtime, collectors, GPU provider, and terminal.
These commands exit after printing their result.

## Keyboard shortcuts

| Key | Action |
| --- | --- |
| `1` / `2` / `3` | Overview / Processes / System |
| `/` | Search processes |
| `c` / `m` / `p` | Sort processes by CPU / memory / PID |
| `Enter` | Return from search to the table, or open a selected process |
| `Esc` | Leave search or close process details |
| `PageUp` / `PageDown` | Scroll Overview on a short terminal |
| `t` | Switch dark/light theme for this session |
| `r` | Refresh all collectors |
| `q` / `Ctrl+C` | Quit (`q` closes process details first) |

## Current scope

The TUI and CLI have been run on Windows. Linux and macOS are target platforms;
their validation is pending. Disk, network, history, alerts, and the continuous
`top` command are not implemented yet. Cross-platform CI and `top` are next.

Typed collectors feed application state, then Textual and the CLI. Collection
runs outside the UI loop. SystemPulse keeps metrics on the machine and does not
perform destructive actions. See the [process scan benchmark](docs/en/benchmarking.md)
for the current measurement method.

## Contribute

Run `uv run pytest`, `uv run ruff check .`, and `uv run mypy` before proposing
changes. Code and canonical documentation are in English; public documentation
also has a pt-BR version. When translations differ, the English version prevails.

Licensed under [Apache 2.0](LICENSE).
