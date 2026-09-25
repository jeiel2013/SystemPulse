"""Consistent, timestamped views of the latest collection cycle."""

from dataclasses import dataclass
from datetime import datetime

from systempulse.domain._validation import require_utc
from systempulse.domain.availability import CollectorStatus
from systempulse.domain.metrics import CpuMetrics, MemoryMetrics, SystemMetrics
from systempulse.domain.processes import ProcessSnapshot


@dataclass(frozen=True, slots=True)
class MetricSnapshot:
    """System-wide metrics observed in the current collection cycle."""

    created_at: datetime
    cpu: CpuMetrics | None
    memory: MemoryMetrics | None

    def __post_init__(self) -> None:
        require_utc(self.created_at, "created_at")


@dataclass(frozen=True, slots=True)
class SystemSnapshot:
    """A view whose members retain their own collection timestamps."""

    created_at: datetime
    metrics: MetricSnapshot
    processes: ProcessSnapshot | None
    system: SystemMetrics | None
    collector_statuses: tuple[CollectorStatus, ...]

    def __post_init__(self) -> None:
        require_utc(self.created_at, "created_at")
