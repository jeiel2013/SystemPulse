"""Low-frequency, portable host facts for the System view."""

import platform
import sys
from datetime import UTC, datetime, timedelta

import psutil

from systempulse.collectors.base import CollectionResult, CollectorMetadata
from systempulse.domain.availability import Availability, CollectorStatus
from systempulse.domain.metrics import SystemMetrics


class SystemCollector:
    """Read host identity and boot time without platform-specific shell commands."""

    def __init__(self, sampling_interval: timedelta = timedelta(minutes=1)) -> None:
        self.metadata = CollectorMetadata("system", sampling_interval)

    def is_available(self) -> bool:
        """Python exposes host identity on all supported platforms."""
        return True

    def collect(self) -> CollectionResult[SystemMetrics]:
        """Keep a useful host sample even when boot time is inaccessible."""
        host = platform.uname()
        sampled_at = datetime.now(UTC)
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time(), UTC)
        except (psutil.Error, OSError, OverflowError, ValueError):
            boot_time = None

        return CollectionResult(
            status=CollectorStatus(
                name=self.metadata.name,
                availability=Availability.AVAILABLE,
                checked_at=sampled_at,
            ),
            metric=SystemMetrics(
                sampled_at=sampled_at,
                platform_name=host.system or sys.platform,
                platform_release=host.release,
                architecture=host.machine,
                hostname=host.node or None,
                boot_time=boot_time,
            ),
        )
