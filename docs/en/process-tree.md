# Process tree

[English](process-tree.md) | [Português Brasileiro](../pt-BR/process-tree.md)

Press `6` in the TUI or run `systempulse tree` to scan parent relationships on
demand. The periodic process table does not read parent IDs, keeping its normal
scan lighter. The tree view can be navigated with the arrow keys; `Enter` opens
the selected process details and `r` rescans. The CLI accepts `--limit`.

The tree uses one best-effort snapshot of PID, name, parent PID, and creation
time. It rejects a parent whose creation time is later than the child's, which
can happen after PID reuse. Protected or disappearing processes are skipped.
The tree is not historical and can change between scans.
