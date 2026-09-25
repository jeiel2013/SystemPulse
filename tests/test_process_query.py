"""Process order and search are shared by CLI and TUI."""

from datetime import UTC, datetime

import pytest

from systempulse.domain.processes import ProcessMetrics
from systempulse.services.process_query import (
    ProcessQuery,
    ProcessSort,
    query_processes,
)


def _process(
    pid: int, name: str | None, cpu: float | None, memory: int | None
) -> ProcessMetrics:
    return ProcessMetrics(
        sampled_at=datetime.now(UTC),
        pid=pid,
        identity=None,
        name=name,
        cpu_percent=cpu,
        memory_rss_bytes=memory,
        status=None,
        user=None,
        threads=None,
        parent_pid=None,
    )


def test_query_sorts_rates_and_puts_missing_measurements_last() -> None:
    rows = (
        _process(3, "slow", None, None),
        _process(2, "Fast", 20.0, 200),
        _process(1, "fast helper", 20.0, 100),
    )

    assert [row.pid for row in query_processes(rows, ProcessQuery())] == [1, 2, 3]
    assert [
        row.pid for row in query_processes(rows, ProcessQuery(sort=ProcessSort.MEMORY))
    ] == [2, 1, 3]
    assert [
        row.pid for row in query_processes(rows, ProcessQuery(sort=ProcessSort.PID))
    ] == [1, 2, 3]


def test_query_filters_case_insensitively_then_limits_rows() -> None:
    rows = (
        _process(1, "Python", 10.0, 100),
        _process(2, "python worker", 20.0, 200),
        _process(3, "other", 30.0, 300),
    )

    result = query_processes(rows, ProcessQuery(search="PYTHON", limit=1))

    assert [row.pid for row in result] == [2]


def test_query_rejects_nonpositive_limit() -> None:
    with pytest.raises(ValueError, match="positive"):
        ProcessQuery(limit=0)
