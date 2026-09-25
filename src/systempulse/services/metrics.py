"""Run collectors without blocking the terminal event loop."""

import asyncio
from datetime import UTC, datetime

from systempulse.collectors.base import CollectionResult, Collector
from systempulse.collectors.registry import CollectorRegistry, RegisteredCollector
from systempulse.domain.availability import Availability, CollectorStatus


class MetricService:
    """Collect registered sources serially in a worker thread."""

    def __init__(self, registry: CollectorRegistry) -> None:
        self._registry = registry
        self._cycle_lock = asyncio.Lock()

    async def collect_all(self) -> tuple[CollectionResult[object], ...]:
        """Collect one cycle while keeping synchronous psutil calls off the UI loop."""
        async with self._cycle_lock:
            entries = self._registry.entries()
            return await asyncio.to_thread(self._collect_entries, entries)

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
