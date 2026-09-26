[English](README.md) | [Português Brasileiro](README.pt-BR.md)

# SystemPulse

**Know what your computer is doing without leaving the terminal.**

SystemPulse is an open-source, local, read-only system monitor. It shows live
CPU, memory, process, and available GPU readings in a keyboard-driven terminal
interface. It has no web dashboard, account, or telemetry. Sustained threshold
rules produce factual observations and local alerts; `doctor` checks SystemPulse itself.

> **Development preview:** `0.1.0.dev1`.
> [PyPI package](https://pypi.org/project/systempulse-monitor/).
> Install `systempulse-monitor`; run `systempulse`. Python 3.12+ is required.

## Install and run

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) once:

**Windows (PowerShell)**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS or Linux**

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Open a new terminal, then install Python 3.12 with uv:

```sh
uv python install 3.12
```

Install the published preview and add uv's tool directory to your `PATH`:

```sh
uv tool install --python 3.12 "systempulse-monitor==0.1.0.dev1"
uv tool update-shell
```

Open a new terminal and run SystemPulse from any directory:

```sh
systempulse
```

The command opens the TUI in an interactive terminal. uv is only needed to
install or update SystemPulse; daily use does not require `uv run`. No
configuration or elevated permissions are needed for the default experience.

Already use pipx with Python 3.12+? Install with:

```sh
pipx install "systempulse-monitor==0.1.0.dev1"
systempulse
```

Use `systempulse-monitor` as the package name; `systempulse` on PyPI belongs to
another project. If you previously installed this project from a checkout,
add `--reinstall` to the uv install command to switch to the published package.

<details>
<summary>Install the latest source code</summary>

```sh
git clone https://github.com/jeiel2013/SystemPulse.git
cd SystemPulse
uv tool install --reinstall --python 3.12 .
uv tool update-shell
```

For development, use `uv sync --locked` followed by `uv run systempulse`.

</details>

## What you can see

- **Overview:** live CPU and RAM, home-volume disk usage, network transfer rates,
  a recent CPU chart, optional GPU load/VRAM/temperature, and separate Top CPU
  and Top RAM process lists. Disk and network rates need two samples.
- **Processes:** search, sort by CPU, memory, or PID, and open verified process
  details. Restricted fields appear as unavailable.
- **System:** operating system, uptime, CPU and memory information, every GPU
  reported by the active provider, and battery/sensor readings when available.
- **History:** local CPU, memory, disk, and network trends for 10 minutes through
  30 days. The database stores metric summaries, not process names or commands.
- **Alerts:** local CPU, memory, and disk threshold rules require continuous
  evidence before triggering. Dismissed and resolved alerts remain visible.
- **Process tree:** an on-demand parent/child scan, separate from the faster
  periodic process table.
- **Reports:** export a single observed snapshot as JSON, CSV, Markdown, or a
  static HTML file.

GPU readings use installed `nvidia-smi`, `rocm-smi`, or `xpu-smi` tools. Without a
supported source, SystemPulse marks GPU metrics unavailable. AMD and Intel
providers still need validation on physical hardware. Battery and sensor
availability depends on the host.
See [GPU collection](docs/en/gpu.md) and [hardware sources](docs/en/hardware.md).

## Other commands

```sh
systempulse status
systempulse top --sort memory --limit 10
systempulse processes --sort memory --limit 10
systempulse processes --search python
systempulse history --range 1h
systempulse alerts
systempulse tree --limit 100
systempulse report --format json
systempulse plugins
systempulse doctor
systempulse version
```

`status` prints one system snapshot. `top` refreshes a compact process monitor
every second; press `q` or `Ctrl+C` to leave it. It requires an interactive
terminal. `processes` prints a filtered list. `doctor` checks the runtime,
collectors, GPU provider, and terminal. The other commands exit after printing.

## Keyboard shortcuts

| Key | Action |
| --- | --- |
| `1` / `2` / `3` / `4` / `5` / `6` | Overview / Processes / System / History / Alerts / Tree |
| `h` | Cycle the History range |
| `d` | Dismiss a selected active alert |
| `e` | Export the current snapshot as Markdown |
| `Enter` in Tree | Open the selected process details |
| `/` | Search processes |
| `c` / `m` / `p` | Sort processes by CPU / memory / PID |
| `Enter` | Return from search to the table, or open a selected process |
| `Esc` | Leave search or close process details |
| `PageUp` / `PageDown` | Scroll Overview on a short terminal |
| `t` | Switch dark/light theme for this session |
| `r` | Refresh all collectors |
| `q` / `Ctrl+C` | Quit (`q` closes process details first) |

SystemPulse adapts both themes to the terminal's reported color support. On
Linux, `systempulse doctor` shows the detected color mode. If your terminal
supports truecolor but reports fewer colors, run
`TEXTUAL_COLOR_SYSTEM=truecolor systempulse` to use the full palette.

## Current scope

The maintainer has tested the TUI and CLI on Windows and Linux. CI has passed
tests, package builds, and isolated tool-install checks on Windows, Ubuntu,
and macOS. Interactive macOS validation remains pending. See
[alerts and configuration](docs/en/alerts.md), [history storage](docs/en/history.md) and
[release checks](docs/en/release.md).
See [reports](docs/en/reports.md) for export formats and locations.
Collector plugins are opt-in; see [plugin development](docs/en/plugins.md).

Typed collectors feed application state, then Textual and the CLI. Collection
runs outside the UI loop. SystemPulse keeps metrics on the machine and does not
perform destructive actions. See the [runtime benchmark](docs/en/benchmarking.md)
for measurements and current performance limits. The
[architecture](docs/en/architecture.md) and
[development](docs/en/development.md) guides explain the codebase.

## Contribute

Run `uv run pytest`, `uv run ruff check .`, and `uv run mypy` before proposing
changes. Code and canonical documentation are in English; public documentation
also has a pt-BR version. When translations differ, the English version prevails.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow, the
[roadmap](ROADMAP.md) for planned work, and the [changelog](CHANGELOG.md) for
shipped changes. Report vulnerabilities through the [security policy](SECURITY.md).
Licensed under [Apache 2.0](LICENSE).
