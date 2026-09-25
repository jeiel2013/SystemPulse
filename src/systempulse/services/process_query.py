"""Shared sorting and filtering for process views."""

from dataclasses import dataclass
from enum import StrEnum

from systempulse.domain.processes import ProcessMetrics


class ProcessSort(StrEnum):
    """Supported orderings for process listings."""

    CPU = "cpu"
    MEMORY = "memory"
    PID = "pid"


@dataclass(frozen=True, slots=True)
class ProcessQuery:
    """A case-insensitive name search and stable process ordering."""

    sort: ProcessSort = ProcessSort.CPU
    search: str = ""
    limit: int | None = None

    def __post_init__(self) -> None:
        if self.limit is not None and self.limit < 1:
            raise ValueError("limit must be positive")


def query_processes(
    processes: tuple[ProcessMetrics, ...], query: ProcessQuery
) -> tuple[ProcessMetrics, ...]:
    """Put missing rates last and use PID to break equal values."""
    needle = query.search.casefold()
    filtered = (
        process for process in processes if needle in (process.name or "").casefold()
    )
    if query.sort == ProcessSort.PID:
        rows = sorted(filtered, key=lambda process: process.pid)
    elif query.sort == ProcessSort.MEMORY:
        rows = sorted(
            filtered,
            key=lambda process: (
                process.memory_rss_bytes is None,
                -(process.memory_rss_bytes or 0),
                process.pid,
            ),
        )
    else:
        rows = sorted(
            filtered,
            key=lambda process: (
                process.cpu_percent is None,
                -(process.cpu_percent or 0),
                process.pid,
            ),
        )
    return tuple(rows[: query.limit])
