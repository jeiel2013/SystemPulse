# Roadmap

[English](ROADMAP.md) | [Português Brasileiro](ROADMAP.pt-BR.md)

This plan describes intended work, not shipped support. The current
`0.1.0.dev0` source preview includes live CPU, memory, processes, disk and
network summaries, optional hardware providers, local history, threshold
alerts, process tree, reports, CLI, and terminal UI. See the README for exact
behavior and limitations.

## Before the first published preview

- Confirm package ownership and publish the `systempulse-monitor` distribution
  after green CI on Windows, Ubuntu, and macOS.
- Interactively verify layout, themes, resize, keyboard input, and clean exit
  on Linux and macOS terminals.
- Repeat longer CPU/RAM measurements and reduce periodic process-scan cost.
- Review the built wheel and source archive, license, release notes, and
  installation instructions.

## Later milestones

- **0.2:** improve disk partition and network interface views; strengthen
  hardware provider coverage using real-device fixtures.
- **0.3:** introduce SQLite schema migration and refine long-term history and
  terminal charts.
- **0.4:** expand factual diagnostics and configurable rule actions.
- **1.0:** document a stable plugin API and validate supported terminal/OS
  combinations with an explicit compatibility matrix.

No date or version is promised until its acceptance criteria are met.
