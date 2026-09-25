"""Boundary tests for measured values."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone

import pytest

from systempulse.domain.metrics import CpuMetrics, MemoryMetrics


def cpu_metrics() -> CpuMetrics:
    return CpuMetrics(
        sampled_at=datetime.now(UTC),
        total_percent=42.0,
        per_core_percent=(20.0, 64.0),
        physical_cores=1,
        logical_cores=2,
        frequency_mhz=3400.0,
        load_average=None,
    )


def memory_metrics() -> MemoryMetrics:
    return MemoryMetrics(
        sampled_at=datetime.now(UTC),
        total_bytes=16_000,
        used_bytes=8_000,
        available_bytes=8_000,
        percent=50.0,
        swap_total_bytes=None,
        swap_used_bytes=None,
        swap_percent=None,
    )


def test_cpu_allows_unavailable_optional_values() -> None:
    sample = replace(cpu_metrics(), physical_cores=None, frequency_mhz=None)

    assert sample.physical_cores is None
    assert sample.frequency_mhz is None


@pytest.mark.parametrize("value", [-1.0, 101.0, float("nan"), float("inf")])
def test_cpu_rejects_invalid_percentages(value: float) -> None:
    with pytest.raises(ValueError, match="total_percent"):
        replace(cpu_metrics(), total_percent=value)


def test_cpu_requires_utc_timestamp() -> None:
    with pytest.raises(ValueError, match="UTC"):
        replace(
            cpu_metrics(),
            sampled_at=datetime.now(timezone(timedelta(hours=-3))),
        )


def test_memory_keeps_optional_swap_unavailable() -> None:
    sample = memory_metrics()

    assert sample.swap_total_bytes is None
    assert sample.swap_percent is None


def test_memory_rejects_impossible_capacity() -> None:
    with pytest.raises(ValueError, match="total_bytes"):
        replace(memory_metrics(), total_bytes=0)


def test_memory_requires_complete_swap_sample() -> None:
    with pytest.raises(ValueError, match="swap values"):
        replace(memory_metrics(), swap_percent=25.0)
