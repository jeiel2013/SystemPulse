"""Efficient process scans with stable identity and safe missing fields."""

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from math import isfinite
from time import monotonic
from typing import cast

import psutil

from systempulse.collectors.base import CollectionResult, CollectorMetadata
from systempulse.domain.availability import Availability, CollectorStatus
from systempulse.domain.processes import (
    ProcessIdentity,
    ProcessMetrics,
    ProcessSnapshot,
)

_SCAN_ATTRIBUTES = (
    "pid",
    "name",
    "create_time",
    "cpu_times",
    "memory_info",
    "username",
    "num_threads",
)


def _optional_text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _optional_nonnegative_int(value: object) -> int | None:
    return value if isinstance(value, int) and value >= 0 else None


def _process_identity(pid: int, created: object) -> ProcessIdentity | None:
    if not isinstance(created, int | float) or not isfinite(created):
        return None
    try:
        return ProcessIdentity(pid, datetime.fromtimestamp(created, UTC))
    except (OSError, OverflowError, ValueError):
        return None


def _cpu_seconds(value: object) -> float | None:
    if value is None:
        return None
    user = getattr(value, "user", None)
    system = getattr(value, "system", None)
    if not isinstance(user, int | float) or not isinstance(system, int | float):
        return None
    total = user + system
    return total if isfinite(total) and total >= 0 else None


def _rss_bytes(value: object) -> int | None:
    return _optional_nonnegative_int(getattr(value, "rss", None))


class ProcessCollector:
    """Scan process rows every two seconds without expensive detail fields."""

    def __init__(self, sampling_interval: timedelta = timedelta(seconds=2)) -> None:
        self.metadata = CollectorMetadata("processes", sampling_interval)
        self._previous_cpu: dict[ProcessIdentity, tuple[float, float]] = {}

    def is_available(self) -> bool:
        """Process enumeration is supported by psutil on target platforms."""
        return True

    def collect(self) -> CollectionResult[ProcessSnapshot]:
        """Read process attributes once and compute CPU from prior process times."""
        sampled_at = datetime.now(UTC)
        elapsed_at = monotonic()
        current_cpu: dict[ProcessIdentity, tuple[float, float]] = {}
        processes: list[ProcessMetrics] = []
        skipped_count = 0

        # psutil does not check PID reuse when serving cached Process objects.
        psutil.process_iter.cache_clear()
        iterator = iter(psutil.process_iter(attrs=_SCAN_ATTRIBUTES, ad_value=None))
        while True:
            try:
                process = next(iterator)
            except StopIteration:
                break
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                skipped_count += 1
                continue

            try:
                info = cast("Mapping[str, object]", process.info)
            except psutil.AccessDenied:
                info = {}
            except psutil.NoSuchProcess:
                skipped_count += 1
                continue

            identity = _process_identity(process.pid, info.get("create_time"))
            cpu_seconds = _cpu_seconds(info.get("cpu_times"))
            cpu_percent: float | None = None
            if identity is not None and cpu_seconds is not None:
                previous = self._previous_cpu.get(identity)
                if previous is not None:
                    previous_elapsed, previous_cpu = previous
                    elapsed = elapsed_at - previous_elapsed
                    used = cpu_seconds - previous_cpu
                    if elapsed > 0 and used >= 0:
                        cpu_percent = round(used * 100.0 / elapsed, 1)
                current_cpu[identity] = (elapsed_at, cpu_seconds)

            processes.append(
                ProcessMetrics(
                    sampled_at=sampled_at,
                    pid=process.pid,
                    identity=identity,
                    name=_optional_text(info.get("name")),
                    cpu_percent=cpu_percent,
                    memory_rss_bytes=_rss_bytes(info.get("memory_info")),
                    status=None,
                    user=_optional_text(info.get("username")),
                    threads=_optional_nonnegative_int(info.get("num_threads")),
                    parent_pid=None,
                )
            )

        self._previous_cpu = current_cpu
        snapshot = ProcessSnapshot(
            sampled_at=sampled_at,
            processes=tuple(processes),
            skipped_count=skipped_count,
        )
        return CollectionResult(
            status=CollectorStatus(
                name=self.metadata.name,
                availability=Availability.AVAILABLE,
                checked_at=sampled_at,
            ),
            metric=snapshot,
        )
