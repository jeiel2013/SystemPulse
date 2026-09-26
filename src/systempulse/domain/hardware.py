"""Optional battery and sensor measurements with explicit timestamps."""

from dataclasses import dataclass
from datetime import datetime
from math import isfinite

from systempulse.domain._validation import (
    require_nonnegative,
    require_percent,
    require_utc,
)


@dataclass(frozen=True, slots=True)
class BatteryMetrics:
    sampled_at: datetime
    percent: float
    power_plugged: bool
    seconds_left: int | None
    source: str = "psutil"

    def __post_init__(self) -> None:
        require_utc(self.sampled_at)
        require_percent(self.percent, "percent")
        if self.seconds_left is not None:
            require_nonnegative(self.seconds_left, "seconds_left")


@dataclass(frozen=True, slots=True)
class SensorReading:
    group: str
    label: str
    value: float
    unit: str

    def __post_init__(self) -> None:
        if not self.group or not self.unit or not isfinite(self.value):
            raise ValueError("sensor reading needs a source, unit and finite value")


@dataclass(frozen=True, slots=True)
class SensorMetrics:
    sampled_at: datetime
    readings: tuple[SensorReading, ...]
    source: str = "psutil"

    def __post_init__(self) -> None:
        require_utc(self.sampled_at)
        if not self.readings:
            raise ValueError("sensor snapshot must contain observed readings")
