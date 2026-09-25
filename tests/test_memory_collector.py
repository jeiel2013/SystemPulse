"""Memory collection tests for complete and partial platform data."""

from collections import namedtuple

import psutil
import pytest

from systempulse.collectors.memory import MemoryCollector
from systempulse.domain.availability import Availability

VirtualMemory = namedtuple("VirtualMemory", "total used available percent")
SwapMemory = namedtuple("SwapMemory", "total used percent")


def test_memory_collects_bytes_and_swap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        psutil,
        "virtual_memory",
        lambda: VirtualMemory(16_000, 8_000, 8_000, 50.0),
    )
    monkeypatch.setattr(psutil, "swap_memory", lambda: SwapMemory(4_000, 500, 12.5))

    result = MemoryCollector().collect()

    assert result.status.availability == Availability.AVAILABLE
    assert result.metric is not None
    assert result.metric.total_bytes == 16_000
    assert result.metric.swap_used_bytes == 500
    assert result.metric.swap_percent == 12.5


def test_memory_remains_available_when_swap_is_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        psutil,
        "virtual_memory",
        lambda: VirtualMemory(16_000, 8_000, 8_000, 50.0),
    )

    def denied_swap() -> None:
        raise psutil.AccessDenied()

    monkeypatch.setattr(psutil, "swap_memory", denied_swap)

    result = MemoryCollector().collect()

    assert result.status.availability == Availability.AVAILABLE
    assert result.metric is not None
    assert result.metric.swap_total_bytes is None
