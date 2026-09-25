# Benchmarking process scans

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

On one Windows development machine with Python 3.12.14 and 213 processes,
the median `core` scan was approximately 0.52 seconds, and `table` took 0.73
seconds. Adding status or parent PID separately raised the medians to
approximately 1.24 and 1.60 seconds; the `full` scan took 2.35 seconds. These
are local measurements, not cross-platform performance claims. The periodic
collector therefore reads
the inexpensive table fields and leaves status and parent PID for process
details. Its declared default interval is two seconds; interval scheduling is
not implemented yet.

This script currently measures **wall time only**. CPU usage, peak memory,
database writes, and TUI overhead require separate benchmarks before v0.1.
