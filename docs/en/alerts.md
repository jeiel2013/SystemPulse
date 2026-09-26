# Threshold alerts and local configuration

[English](alerts.md) | [Português Brasileiro](../pt-BR/alerts.md)

SystemPulse currently evaluates sustained CPU, memory, and home-volume disk
percentage thresholds. The default rules trigger when CPU or memory stays above
90%, or disk usage stays above 95%, for 120 seconds. A missing or stale metric
resets the timer. The alert describes only the observed threshold; it does not
claim a cause. Press `5` in the TUI to see alerts and `d` to dismiss the selected
active alert. `systempulse alerts` lists locally stored alerts. A dismissed alert
can trigger again only after its condition ends and later recurs.

Configuration is optional. Run `systempulse doctor` to find the per-user
`config.toml` path on your operating system. To replace the default rules, create
that file with entries such as:

```toml
[[rules]]
id = "high-memory"
metric = "memory.percent"
threshold_percent = 85
for_seconds = 60
severity = "warning"
enabled = true
```

Supported metrics are `cpu.percent`, `memory.percent`, and `disk.percent`.
Severity is `warning` or `critical`. A `rules` list replaces the defaults; an
empty list disables threshold alerts. Invalid TOML or invalid values fall back
to defaults, and `systempulse doctor` reports the error. Rules are loaded at
startup, so restart SystemPulse after editing the file.

Alert lifecycle records live in the same local SQLite database as metric
history. There are no notifications or network requests. More diagnostic
observations and rule actions are planned.
