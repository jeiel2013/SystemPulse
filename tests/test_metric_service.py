"""Collector isolation, enablement, and worker execution tests."""

from datetime import UTC, datetime, timedelta
from threading import get_ident

import pytest

from systempulse.collectors.base import CollectionResult, CollectorMetadata
from systempulse.collectors.registry import CollectorRegistry
from systempulse.domain.availability import Availability, CollectorStatus
from systempulse.services.metrics import MetricService


class StubCollector:
    def __init__(self, name: str, *, available: bool = True, fails: bool = False):
        self.metadata = CollectorMetadata(name, timedelta(seconds=1))
        self.available = available
        self.fails = fails
        self.calls = 0
        self.thread_id: int | None = None

    def is_available(self) -> bool:
        return self.available

    def collect(self) -> CollectionResult[int]:
        self.calls += 1
        self.thread_id = get_ident()
        if self.fails:
            raise RuntimeError("collector failure")
        return CollectionResult(
            status=CollectorStatus(
                name=self.metadata.name,
                availability=Availability.AVAILABLE,
                checked_at=datetime.now(UTC),
            ),
            metric=self.calls,
        )


@pytest.mark.asyncio
async def test_one_collector_failure_does_not_stop_others() -> None:
    registry = CollectorRegistry()
    registry.register(StubCollector("broken", fails=True))
    registry.register(StubCollector("healthy"))

    results = await MetricService(registry).collect_all()

    assert results[0].status.availability == Availability.ERROR
    assert results[0].status.reason == "RuntimeError"
    assert results[1].status.availability == Availability.AVAILABLE
    assert results[1].metric == 1


@pytest.mark.asyncio
async def test_disabled_and_unavailable_collectors_are_not_read() -> None:
    disabled = StubCollector("disabled")
    unavailable = StubCollector("unavailable", available=False)
    registry = CollectorRegistry()
    registry.register(disabled, enabled=False)
    registry.register(unavailable)

    results = await MetricService(registry).collect_all()

    assert [result.status.availability for result in results] == [
        Availability.DISABLED,
        Availability.UNAVAILABLE,
    ]
    assert disabled.calls == unavailable.calls == 0


@pytest.mark.asyncio
async def test_collection_runs_outside_event_loop_thread() -> None:
    collector = StubCollector("cpu")
    registry = CollectorRegistry()
    registry.register(collector)
    event_loop_thread = get_ident()

    await MetricService(registry).collect_all()

    assert collector.thread_id is not None
    assert collector.thread_id != event_loop_thread


def test_registry_rejects_duplicate_names_and_can_disable() -> None:
    registry = CollectorRegistry()
    registry.register(StubCollector("cpu"))

    with pytest.raises(ValueError, match="already registered"):
        registry.register(StubCollector("cpu"))

    registry.set_enabled("cpu", False)
    assert registry.entries()[0].enabled is False
