"""Common typed contract for synchronous collectors."""

from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol

from systempulse.domain.availability import Availability, CollectorStatus


@dataclass(frozen=True, slots=True)
class CollectorMetadata:
    """Stable scheduling information for a collector."""

    name: str
    sampling_interval: timedelta

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("collector name must not be empty")
        if self.sampling_interval <= timedelta(0):
            raise ValueError("sampling_interval must be positive")


@dataclass(frozen=True, slots=True)
class CollectionResult[T]:
    """A collector's metric or an explicit non-data state."""

    status: CollectorStatus
    metric: T | None = None

    def __post_init__(self) -> None:
        available = self.status.availability == Availability.AVAILABLE
        if (available and self.metric is None) or (
            not available and self.metric is not None
        ):
            raise ValueError("available status requires a metric, and vice versa")


class Collector[T](Protocol):
    """The read-only contract implemented by metric collectors."""

    @property
    def metadata(self) -> CollectorMetadata: ...

    def is_available(self) -> bool: ...

    def collect(self) -> CollectionResult[T]: ...
