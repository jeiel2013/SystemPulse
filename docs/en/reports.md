# Local reports

[English](reports.md) | [Português Brasileiro](../pt-BR/reports.md)

Run `systempulse report --format json` to export one observed snapshot. Supported
formats are `json`, `csv`, `markdown`, and `html`. HTML is a static export, not a
web interface. The TUI shortcut `e` exports the latest snapshot as Markdown.

By default, files go to the `reports` folder in SystemPulse's per-user data
directory; the command prints the full destination. Use `--output PATH` to
choose a file. Existing files are never overwritten. Reports contain current
system metrics and the ten leading CPU processes, including their names, PIDs,
CPU, and resident memory when available. Review a report before sharing it:
process names and system metrics may reveal local activity.
