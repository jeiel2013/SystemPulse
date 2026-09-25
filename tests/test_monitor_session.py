"""The monitoring session connects service, aggregator, and state."""

import asyncio
from datetime import timedelta

import pytest

from systempulse.collectors.base import CollectionResult, CollectorMetadata
from systempulse.collectors.registry import CollectorRegistry
from systempulse.domain.availability import Availability
from systempulse.services.monitor import MonitorSession


class BrokenCollector:
    metadata = CollectorMetadata("cpu", timedelta(seconds=1))

    def is_available(self) -> bool:
        return True

    def collect(self) -> CollectionResult[object]:
        raise OSError("unavailable source")


@pytest.mark.asyncio
async def test_session_publishes_failed_collector_status() -> None:
    registry = CollectorRegistry()
    registry.register(BrokenCollector())
    session = MonitorSession(registry)

    snapshot = await session.sample()

    assert session.state.current_snapshot == snapshot
    assert session.state.collector_statuses[0].availability == Availability.ERROR
    assert snapshot.metrics.cpu is None


@pytest.mark.asyncio
async def test_session_retains_recent_snapshots() -> None:
    registry = CollectorRegistry()
    session = MonitorSession(registry)

    first = await session.sample()
    second = await session.sample()

    assert session.state.recent_snapshots == (first, second)
    assert second.created_at >= first.created_at


def test_warmup_requires_positive_delay() -> None:
    registry = CollectorRegistry()
    session = MonitorSession(registry)
    with pytest.raises(ValueError, match="positive"):
        asyncio.run(session.sample_after_warmup(delay_seconds=0))
