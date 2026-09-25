"""CPU collector based on deltas between cumulative processor times."""

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import cast

import psutil

from systempulse.collectors.base import CollectionResult, CollectorMetadata
from systempulse.domain.availability import Availability, CollectorStatus
from systempulse.domain.metrics import CpuMetrics
from systempulse.platform.load import get_load_average

_DOUBLE_COUNTED_TIMES = frozenset({"guest", "guest_nice"})
_IDLE_TIMES = frozenset({"idle", "iowait"})


def _percent_from_times(
    previous: Mapping[str, float], current: Mapping[str, float]
) -> float | None:
    """Calculate busy time, ignoring guest time already counted in user time."""
    if previous.keys() != current.keys():
        return None
    deltas = {name: value - previous[name] for name, value in current.items()}
    if any(delta < 0 for delta in deltas.values()):
        return None
    total = sum(
        delta for name, delta in deltas.items() if name not in _DOUBLE_COUNTED_TIMES
    )
    if total <= 0:
        return None
    idle = sum(delta for name, delta in deltas.items() if name in _IDLE_TIMES)
    return round(min(100.0, max(0.0, (total - idle) * 100.0 / total)), 1)


class CpuCollector:
    """Collect nonblocking CPU samples without relying on thread-local baselines."""

    def __init__(self, sampling_interval: timedelta = timedelta(seconds=1)) -> None:
        self.metadata = CollectorMetadata("cpu", sampling_interval)
        self._previous_total: Mapping[str, float] | None = None
        self._previous_cores: tuple[Mapping[str, float], ...] | None = None

    def is_available(self) -> bool:
        """CPU time counters are available on the supported psutil platforms."""
        return True

    def collect(self) -> CollectionResult[CpuMetrics]:
        """Return a sample after the first call establishes a time baseline."""
        total_times = cast("Mapping[str, float]", psutil.cpu_times()._asdict())
        core_times = tuple(
            cast("Mapping[str, float]", times._asdict())
            for times in psutil.cpu_times(percpu=True)
        )
        sampled_at = datetime.now(UTC)
        previous_total = self._previous_total
        previous_cores = self._previous_cores
        self._previous_total = total_times
        self._previous_cores = core_times

        total_percent = (
            _percent_from_times(previous_total, total_times)
            if previous_total is not None
            else None
        )
        per_core_percent = (
            tuple(
                _percent_from_times(before, after)
                for before, after in zip(previous_cores, core_times, strict=True)
            )
            if previous_cores is not None and len(previous_cores) == len(core_times)
            else ()
        )
        if (
            total_percent is None
            or not per_core_percent
            or any(percent is None for percent in per_core_percent)
        ):
            return CollectionResult(
                status=CollectorStatus(
                    name=self.metadata.name,
                    availability=Availability.WARMING_UP,
                    checked_at=sampled_at,
                    reason="Waiting for a CPU time interval",
                )
            )

        try:
            frequency = psutil.cpu_freq()
        except (OSError, psutil.Error, NotImplementedError):
            frequency = None
        metric = CpuMetrics(
            sampled_at=sampled_at,
            total_percent=total_percent,
            per_core_percent=cast("tuple[float, ...]", per_core_percent),
            physical_cores=psutil.cpu_count(logical=False),
            logical_cores=psutil.cpu_count(logical=True),
            frequency_mhz=frequency.current if frequency is not None else None,
            load_average=get_load_average(),
        )
        return CollectionResult(
            status=CollectorStatus(
                name=self.metadata.name,
                availability=Availability.AVAILABLE,
                checked_at=sampled_at,
            ),
            metric=metric,
        )
