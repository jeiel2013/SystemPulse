# Benchmarking runtime cost

[English](benchmarking.md) | [Português Brasileiro](../pt-BR/benchmarking.md)

Process enumeration can dominate a monitoring cycle. The current benchmark
compares groups of attributes read through `psutil.process_iter(attrs=...,
ad_value=None)` on the host running the command:

```sh
uv run python scripts/benchmark_process_scan.py
```

The script clears psutil's process cache before each scan, runs each attribute
group three times, and prints the median elapsed wall time and process count.
It makes no network requests and writes no result files. Run it while the machine
is otherwise idle for a useful baseline, then repeat under normal workload.

The `core` group reads PID, name, creation time, CPU times, and resident memory.
The `table` group also reads user and thread count. Other groups isolate status
and parent PID. `full` reads all listed fields. Process counts can change during
the benchmark, so elapsed times are indicative rather than directly comparable
to a fixed-size synthetic dataset.

On a Windows development machine with Python 3.12.14 and 233 processes, a
recent `core` scan took 0.36 seconds median; `table` took 0.65 seconds. Adding
status or parent PID raised the median to 0.78 or 1.96 seconds; `full` took
2.71 seconds. These are local measurements, not cross-platform claims. The
periodic collector now reads only the `core` attributes. User, thread count,
status, and parent PID are read when process details or the tree are opened.
The process collector runs every two seconds; lighter collectors run every
second.

For a live cost estimate, run:

```sh
uv run python scripts/benchmark_runtime.py --seconds 10
```

The script runs the default collectors and then the real Textual app in
headless test mode, each for the requested duration. It uses disposable data
directories. It reports elapsed time, the process's CPU time as a percentage
of **one core**, end-of-phase resident memory, SQLite row count and file size,
and collector-cycle latency. These numbers include Python startup inside each
phase and benchmark instrumentation. Headless Textual rendering is not the
same as a physical terminal. End-of-phase RSS is not a peak measurement.

On the same Windows host, one 10-second run after the process-scan and state
changes measured 25.7% of one core and 79.1 MiB RSS for collectors, and 30.5%
of one core and 89.6 MiB RSS for the headless TUI. Each phase wrote 10 history
rows;
the SQLite files occupied about 20 KiB at measurement time. Collector cycles
had a 0.22-second median and a 0.70-second maximum. The CPU cost remains above
the initial low-overhead goal; longer runs and interactive Linux/macOS
measurements are needed before making a release-level performance claim.
