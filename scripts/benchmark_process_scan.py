"""Measure psutil process scan cost on the current machine.

Run with ``uv run python scripts/benchmark_process_scan.py``. Results depend on
the host, process count, permissions, Python build, and background load.
"""

from statistics import median
from time import perf_counter

import psutil

ATTRIBUTE_GROUPS = {
    "core": ("pid", "name", "create_time", "cpu_times", "memory_info"),
    "status": ("pid", "name", "create_time", "cpu_times", "memory_info", "status"),
    "parent": ("pid", "name", "create_time", "cpu_times", "memory_info", "ppid"),
    "threads": (
        "pid",
        "name",
        "create_time",
        "cpu_times",
        "memory_info",
        "num_threads",
    ),
    "user": ("pid", "name", "create_time", "cpu_times", "memory_info", "username"),
    "table": (
        "pid",
        "name",
        "create_time",
        "cpu_times",
        "memory_info",
        "username",
        "num_threads",
    ),
    "full": (
        "pid",
        "name",
        "create_time",
        "cpu_times",
        "memory_info",
        "status",
        "ppid",
        "num_threads",
        "username",
    ),
}


def measure(attributes: tuple[str, ...]) -> tuple[float, int]:
    """Time one scan with a fresh psutil process cache."""
    psutil.process_iter.cache_clear()
    started = perf_counter()
    count = sum(1 for _ in psutil.process_iter(attrs=attributes, ad_value=None))
    return perf_counter() - started, count


def main() -> None:
    """Print median wall time over three scans for each attribute set."""
    for name, attributes in ATTRIBUTE_GROUPS.items():
        runs = [measure(attributes) for _ in range(3)]
        print(
            f"{name:>6}: {median(seconds for seconds, _ in runs):.3f}s, "
            f"{runs[-1][1]} processes"
        )


if __name__ == "__main__":
    main()
