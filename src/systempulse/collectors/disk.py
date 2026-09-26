"""Home-volume capacity and system-wide disk I/O rates."""

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import monotonic

import psutil

from systempulse.collectors.base import CollectionResult, CollectorMetadata
from systempulse.domain.availability import Availability, CollectorStatus
from systempulse.domain.io import DiskMetrics


def home_mountpoint(home: Path) -> Path:
    """Find the filesystem containing home, including a separately mounted /home."""
    current = home.resolve()
    while not os.path.ismount(current):
        if current.parent == current:
            break
        current = current.parent
    return current


class DiskCollector:
    """Read disk usage and calculate rates only after a valid counter interval."""

    def __init__(self, sampling_interval: timedelta = timedelta(seconds=1)) -> None:
        self.metadata = CollectorMetadata("disk", sampling_interval)
        self._previous: tuple[float, int, int] | None = None
        self._mountpoint: Path | None = None

    def is_available(self) -> bool:
        return True

    def collect(self) -> CollectionResult[DiskMetrics]:
        if self._mountpoint is None:
            self._mountpoint = home_mountpoint(Path.home())
        mountpoint = str(self._mountpoint)
        usage = psutil.disk_usage(mountpoint)
        try:
            counters = psutil.disk_io_counters()
        except (OSError, psutil.Error, NotImplementedError):
            counters = None
        now = monotonic()
        previous = self._previous
        read = counters.read_bytes if counters is not None else None
        write = counters.write_bytes if counters is not None else None
        self._previous = (
            (now, read, write) if read is not None and write is not None else None
        )
        read_rate: float | None = None
        write_rate: float | None = None
        if previous is not None and read is not None and write is not None:
            seconds = now - previous[0]
            if seconds > 0 and read >= previous[1] and write >= previous[2]:
                read_rate = (read - previous[1]) / seconds
                write_rate = (write - previous[2]) / seconds
        sampled_at = datetime.now(UTC)
        metric = DiskMetrics(
            sampled_at,
            mountpoint,
            usage.total,
            usage.used,
            usage.free,
            usage.percent,
            read,
            write,
            read_rate,
            write_rate,
        )
        return CollectionResult(
            CollectorStatus("disk", Availability.AVAILABLE, sampled_at), metric
        )
