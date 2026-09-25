"""Physical memory and optional swap collection."""

from datetime import UTC, datetime, timedelta

import psutil

from systempulse.collectors.base import CollectionResult, CollectorMetadata
from systempulse.domain.availability import Availability, CollectorStatus
from systempulse.domain.metrics import MemoryMetrics


class MemoryCollector:
    """Collect physical memory even when swap information is unavailable."""

    def __init__(self, sampling_interval: timedelta = timedelta(seconds=1)) -> None:
        self.metadata = CollectorMetadata("memory", sampling_interval)

    def is_available(self) -> bool:
        """Virtual memory is available on the supported psutil platforms."""
        return True

    def collect(self) -> CollectionResult[MemoryMetrics]:
        """Read one virtual-memory sample and optional swap fields."""
        memory = psutil.virtual_memory()
        try:
            swap = psutil.swap_memory()
        except (OSError, psutil.Error, NotImplementedError):
            swap = None
        sampled_at = datetime.now(UTC)
        metric = MemoryMetrics(
            sampled_at=sampled_at,
            total_bytes=memory.total,
            used_bytes=memory.used,
            available_bytes=memory.available,
            percent=memory.percent,
            swap_total_bytes=swap.total if swap is not None else None,
            swap_used_bytes=swap.used if swap is not None else None,
            swap_percent=swap.percent if swap is not None else None,
        )
        return CollectionResult(
            status=CollectorStatus(
                name=self.metadata.name,
                availability=Availability.AVAILABLE,
                checked_at=sampled_at,
            ),
            metric=metric,
        )
