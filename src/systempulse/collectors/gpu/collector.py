"""Expose vendor GPU providers through the typed collector interface."""

from datetime import UTC, datetime, timedelta

from systempulse.collectors.base import CollectionResult, CollectorMetadata
from systempulse.collectors.gpu.providers import (
    GpuProvider,
    GpuUnavailableError,
    select_gpu_provider,
)
from systempulse.domain.availability import Availability, CollectorStatus
from systempulse.domain.gpu import GpuSnapshot


class GpuCollector:
    """Collect supported GPU metrics at a lower rate than CPU and memory."""

    def __init__(
        self,
        provider: GpuProvider | None = None,
        sampling_interval: timedelta = timedelta(seconds=2),
    ) -> None:
        self.metadata = CollectorMetadata("gpu", sampling_interval)
        self.provider = provider or select_gpu_provider()

    def is_available(self) -> bool:
        return self.provider.is_available()

    def collect(self) -> CollectionResult[GpuSnapshot]:
        try:
            snapshot = self.provider.collect()
        except GpuUnavailableError as error:
            return CollectionResult(
                status=CollectorStatus(
                    name=self.metadata.name,
                    availability=Availability.UNAVAILABLE,
                    checked_at=datetime.now(UTC),
                    reason=str(error),
                )
            )
        return CollectionResult(
            status=CollectorStatus(
                name=self.metadata.name,
                availability=Availability.AVAILABLE,
                checked_at=snapshot.sampled_at,
            ),
            metric=snapshot,
        )
