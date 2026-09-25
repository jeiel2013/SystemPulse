"""Host facts are typed, timestamped, and tolerant of missing boot time."""

from datetime import UTC, datetime, timedelta

import psutil
import pytest

from systempulse.collectors.system import SystemCollector
from systempulse.domain.availability import Availability


def test_system_collector_reads_local_host() -> None:
    collector = SystemCollector()
    result = collector.collect()

    assert collector.metadata.sampling_interval == timedelta(minutes=1)
    assert result.status.availability == Availability.AVAILABLE
    assert result.metric is not None
    assert result.metric.platform_name
    assert result.metric.sampled_at.tzinfo == UTC
    assert result.metric.boot_time is None or result.metric.boot_time.tzinfo == UTC


def test_system_collector_keeps_host_when_boot_time_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable() -> float:
        raise psutil.AccessDenied()

    monkeypatch.setattr(psutil, "boot_time", unavailable)
    result = SystemCollector().collect()

    assert result.status.availability == Availability.AVAILABLE
    assert result.metric is not None
    assert result.metric.boot_time is None
    assert result.metric.sampled_at <= datetime.now(UTC)
