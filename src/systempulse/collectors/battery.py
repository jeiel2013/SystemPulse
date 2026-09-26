"""Optional battery readings across supported psutil platforms."""

from datetime import UTC, datetime, timedelta

import psutil

from systempulse.collectors.base import CollectionResult, CollectorMetadata
from systempulse.domain.availability import Availability, CollectorStatus
from systempulse.domain.hardware import BatteryMetrics


class BatteryCollector:
    def __init__(self, sampling_interval: timedelta = timedelta(seconds=5)) -> None:
        self.metadata = CollectorMetadata("battery", sampling_interval)

    def is_available(self) -> bool:
        return callable(getattr(psutil, "sensors_battery", None))

    def collect(self) -> CollectionResult[BatteryMetrics]:
        at = datetime.now(UTC)
        battery = psutil.sensors_battery()
        if battery is None:
            return CollectionResult(
                CollectorStatus(
                    "battery", Availability.UNAVAILABLE, at, "No battery detected"
                )
            )
        unknown = {psutil.POWER_TIME_UNKNOWN, psutil.POWER_TIME_UNLIMITED}
        seconds_left = battery.secsleft
        metric = BatteryMetrics(
            at,
            battery.percent,
            battery.power_plugged,
            seconds_left
            if seconds_left is not None
            and seconds_left not in unknown
            and seconds_left >= 0
            else None,
        )
        return CollectionResult(
            CollectorStatus("battery", Availability.AVAILABLE, at), metric
        )
