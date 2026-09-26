# Architecture

[English](architecture.md) | [Português Brasileiro](../pt-BR/architecture.md)

SystemPulse is one local Python process. The CLI and Textual TUI share the
same typed collectors and `MonitorSession`; neither runs a web server. The
default session registers CPU, memory, disk, network, processes, system facts,
GPU, battery, and sensor collectors. Optional collector entry points are
disabled until named in local configuration.

```text
psutil / local vendor tools → CollectorRegistry → MetricService
    → MetricAggregator → SystemSnapshot → ApplicationState → Textual
                                    ↘ RuleEngine → alerts and observations
                                    ↘ HistoryStore → SQLite summaries
```

`MetricService` calls synchronous collectors in a worker thread. Each collector
declares its sampling interval; cached results retain their original UTC
timestamps between due cycles. One failed collector produces an unavailable or
error status while the remaining collectors continue. The aggregator publishes
one typed snapshot. Widgets read application state, never psutil directly.

The process table scans core fields every two seconds. Detailed status, user,
threads, executable, and command are read only when a process is selected. A
process instance is identified by PID plus creation time to guard against PID
reuse. The process tree is a separate on-demand scan.

`HistoryStore` writes summary metrics and alert lifecycle records to a per-user
SQLite database in WAL mode. Raw samples are retained for 10 minutes, minute
buckets for 24 hours, and 15-minute buckets for 30 days. Process names and
commands are not persisted. The current schema is created on first use; schema
migrations are still needed before a stable release.

Rules evaluate sustained, timestamped measurements. Observations describe
what was measured; they do not assert an unobserved cause. Reports export one
snapshot locally. Plugin hooks currently cover collectors only and remain
experimental. A general event bus is not implemented yet.
