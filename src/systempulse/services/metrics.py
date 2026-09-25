"""Run collectors without blocking the terminal event loop."""

import asyncio
from datetime import UTC, datetime
from time import monotonic

from systempulse.collectors.base import CollectionResult, Collector
from systempulse.collectors.registry import CollectorRegistry, RegisteredCollector
from systempulse.domain.availability import Availability, CollectorStatus


class MetricService:
    """Collect registered sources serially in a worker thread."""

    def __init__(self, registry: CollectorRegistry) -> None:
        self._registry = registry
        self._cycle_lock = asyncio.Lock()
        self._last_results: dict[str, CollectionResult[object]] = {}
        self._next_due: dict[str, float] = {}

    async def collect_all(self) -> tuple[CollectionResult[object], ...]:
        """Collect one cycle while keeping synchronous psutil calls off the UI loop."""
        async with self._cycle_lock:
            entries = self._registry.entries()
            return await asyncio.to_thread(self._collect_entries, entries)

    async def collect_due(self) -> tuple[CollectionResult[object], ...]:
        """Refresh collectors at their intervals and retain timestamped prior data."""
        async with self._cycle_lock:
            entries = self._registry.entries()
            started_at = monotonic()
            due = tuple(entry for entry in entries if self._is_due(entry, started_at))
            if due:
                refreshed = await asyncio.to_thread(self._collect_entries, due)
                for entry, result in zip(due, refreshed, strict=True):
                    name = entry.collector.metadata.name
                    self._last_results[name] = result
                    self._next_due[name] = (
                        started_at
                        + entry.collector.metadata.sampling_interval.total_seconds()
                    )
            return tuple(
                self._last_results[entry.collector.metadata.name] for entry in entries
            )

    def _is_due(self, entry: RegisteredCollector, now: float) -> bool:
        name = entry.collector.metadata.name
        previous = self._last_results.get(name)
        if previous is None or now >= self._next_due[name]:
            return True
        was_disabled = previous.status.availability == Availability.DISABLED
        return was_disabled != (not entry.enabled)

    @classmethod
    def _collect_entries(
        cls, entries: tuple[RegisteredCollector, ...]
    ) -> tuple[CollectionResult[object], ...]:
        return tuple(cls._collect_one(entry) for entry in entries)

    @staticmethod
    def _collect_one(entry: RegisteredCollector) -> CollectionResult[object]:
        collector: Collector[object] = entry.collector
        name = collector.metadata.name
        if not entry.enabled:
            return CollectionResult(
                status=CollectorStatus(
                    name=name,
                    availability=Availability.DISABLED,
                    checked_at=datetime.now(UTC),
                )
            )
        try:
            if not collector.is_available():
                return CollectionResult(
                    status=CollectorStatus(
                        name=name,
                        availability=Availability.UNAVAILABLE,
                        checked_at=datetime.now(UTC),
                    )
                )
            return collector.collect()
        except Exception as error:
            return CollectionResult(
                status=CollectorStatus(
                    name=name,
                    availability=Availability.ERROR,
                    checked_at=datetime.now(UTC),
                    reason=type(error).__name__,
                )
            )
