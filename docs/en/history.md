# Local metric history

[English](history.md) | [Português Brasileiro](../pt-BR/history.md)

SystemPulse writes CPU, memory, home-volume disk, and host network summaries to
SQLite in the operating system's per-user data directory. It does not retain
process names, command lines, or individual network destinations. No data leaves
the machine.

Run `systempulse history --range 1h` or press `4` in the TUI. Press `h` to cycle
through 10m, 30m, 1h, 6h, 24h, 7d, and 30d. The first reading of a rate is
unavailable until a second counter sample establishes an interval.

Raw samples are retained for 10 minutes. Older samples are averaged into
one-minute buckets for up to 24 hours and then 15-minute buckets for up to
30 days. Missing measurements are excluded from averages. Compaction runs at
most once a minute while monitoring; data is not collected while SystemPulse is
closed. The database uses SQLite WAL mode and is updated off the terminal UI
thread. A database error leaves live monitoring available.
