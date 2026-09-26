"""Optional local temperature and fan readings."""

from datetime import UTC, datetime, timedelta

import psutil

from systempulse.collectors.base import CollectionResult, CollectorMetadata
from systempulse.domain.availability import Availability, CollectorStatus
from systempulse.domain.hardware import SensorMetrics, SensorReading


class SensorCollector:
    def __init__(self, sampling_interval: timedelta = timedelta(seconds=5)) -> None:
        self.metadata = CollectorMetadata("sensors", sampling_interval)

    def is_available(self) -> bool:
        return callable(getattr(psutil, "sensors_temperatures", None)) or callable(
            getattr(psutil, "sensors_fans", None)
        )

    def collect(self) -> CollectionResult[SensorMetrics]:
        at = datetime.now(UTC)
        readings: list[SensorReading] = []
        temperature_reader = getattr(psutil, "sensors_temperatures", None)
        fan_reader = getattr(psutil, "sensors_fans", None)
        if callable(temperature_reader):
            try:
                temperatures = temperature_reader()
            except (OSError, psutil.Error, NotImplementedError):
                temperatures = {}
            for group, entries in temperatures.items():
                for entry in entries:
                    if entry.current is not None:
                        readings.append(
                            SensorReading(
                                group, entry.label or group, entry.current, "C"
                            )
                        )
        if callable(fan_reader):
            try:
                fans = fan_reader()
            except (OSError, psutil.Error, NotImplementedError):
                fans = {}
            for group, entries in fans.items():
                for entry in entries:
                    if entry.current is not None:
                        readings.append(
                            SensorReading(
                                group, entry.label or group, entry.current, "RPM"
                            )
                        )
        if not readings:
            return CollectionResult(
                CollectorStatus(
                    "sensors", Availability.UNAVAILABLE, at, "No sensor readings"
                )
            )
        return CollectionResult(
            CollectorStatus("sensors", Availability.AVAILABLE, at),
            SensorMetrics(at, tuple(readings)),
        )
