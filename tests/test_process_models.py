"""Process identity and metric validation tests."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from systempulse.domain.processes import ProcessIdentity, ProcessMetrics


def process_metric() -> ProcessMetrics:
    identity = ProcessIdentity(pid=42, created_at=datetime.now(UTC))
    return ProcessMetrics(
        sampled_at=datetime.now(UTC),
        pid=42,
        identity=identity,
        name="worker",
        cpu_percent=None,
        memory_rss_bytes=None,
        status=None,
        user=None,
        threads=None,
        parent_pid=None,
    )


def test_pid_reuse_has_distinct_process_identity() -> None:
    first = ProcessIdentity(42, datetime(2026, 1, 1, tzinfo=UTC))
    second = ProcessIdentity(42, first.created_at + timedelta(seconds=1))

    assert first != second


def test_process_cpu_may_exceed_one_hundred_percent() -> None:
    metric = replace(process_metric(), cpu_percent=175.0)

    assert metric.cpu_percent == 175.0


def test_process_metric_rejects_identity_with_different_pid() -> None:
    other = ProcessIdentity(43, datetime.now(UTC))

    with pytest.raises(ValueError, match="identity PID"):
        replace(process_metric(), identity=other)


def test_process_metric_keeps_protected_fields_unavailable() -> None:
    metric = process_metric()

    assert metric.name == "worker"
    assert metric.memory_rss_bytes is None
    assert metric.user is None
