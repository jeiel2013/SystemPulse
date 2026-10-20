# Changelog

[English](CHANGELOG.md) | [Português Brasileiro](CHANGELOG.pt-BR.md)

Changes are grouped by release. SystemPulse follows Semantic Versioning.

## Unreleased

- Remove the always-empty `USER` and `THREADS` columns from the process
  explorer. They were rendered without data because the periodic psutil scan
  intentionally avoids expensive fields; `username` and `num_threads` roughly
  double the cost of every scan on a typical host. Press Enter on a row to see
  them via the on-demand process details screen.

## 0.1.0.dev1 — Documentation update

- Document installation from PyPI using uv or pipx and running `systempulse`
  directly, with source installation as an alternative.
- Update the English and Brazilian Portuguese documentation with publication
  status, Windows/Linux manual testing, and successful CI on all three systems.
- Explain how to publish subsequent versions and update the README on PyPI.

## 0.1.0.dev0 — Development preview

- Live terminal overview, process explorer, details, tree, theme switching,
  keyboard navigation, and responsive layout.
- CPU, memory, disk, network, system, battery, and sensor collectors; optional
  NVIDIA, AMD ROCm, and Intel XPU GPU providers. AMD/Intel hardware validation
  remains open.
- Local SQLite metric history and alert lifecycle; sustained threshold rules
  with evidence-based observations.
- One-shot CLI commands, compact `top`, self-diagnostic `doctor`, static report
  export, and opt-in experimental collector entry points.
- Cross-platform CI configuration and isolated wheel-install smoke checks.

Available on [PyPI](https://pypi.org/project/systempulse-monitor/0.1.0.dev0/).
Interactive macOS validation and CPU cost reduction remain open work before
a stable release.
