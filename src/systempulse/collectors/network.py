"""Local network interface counters and measured transfer rates."""

from datetime import UTC, datetime, timedelta
from time import monotonic

import psutil

from systempulse.collectors.base import CollectionResult, CollectorMetadata
from systempulse.domain.availability import Availability, CollectorStatus
from systempulse.domain.io import NetworkInterfaceMetrics, NetworkMetrics


class NetworkCollector:
    """Treat counter resets and first observations as unknown rates."""

    def __init__(self, sampling_interval: timedelta = timedelta(seconds=1)) -> None:
        self.metadata = CollectorMetadata("network", sampling_interval)
        self._previous: tuple[float, int, int] | None = None

    def is_available(self) -> bool:
        return True

    def collect(self) -> CollectionResult[NetworkMetrics]:
        totals = psutil.net_io_counters(nowrap=True)
        if totals is None:
            return CollectionResult(
                CollectorStatus(
                    "network",
                    Availability.UNAVAILABLE,
                    datetime.now(UTC),
                    "Network counters unavailable",
                )
            )
        interfaces = psutil.net_io_counters(pernic=True, nowrap=True) or {}
        now = monotonic()
        previous = self._previous
        received, sent = totals.bytes_recv, totals.bytes_sent
        self._previous = (now, received, sent)
        download: float | None = None
        upload: float | None = None
        if previous is not None:
            seconds = now - previous[0]
            if seconds > 0 and received >= previous[1] and sent >= previous[2]:
                download = (received - previous[1]) / seconds
                upload = (sent - previous[2]) / seconds
        sampled_at = datetime.now(UTC)
        metric = NetworkMetrics(
            sampled_at,
            received,
            sent,
            download,
            upload,
            tuple(
                NetworkInterfaceMetrics(name, counters.bytes_recv, counters.bytes_sent)
                for name, counters in sorted(interfaces.items())
            ),
        )
        return CollectionResult(
            CollectorStatus("network", Availability.AVAILABLE, sampled_at), metric
        )
