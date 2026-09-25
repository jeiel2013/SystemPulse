"""Timestamped GPU measurements in core units."""

from dataclasses import dataclass
from datetime import datetime
from math import isfinite

from systempulse.domain._validation import (
    require_nonnegative,
    require_percent,
    require_utc,
)


@dataclass(frozen=True, slots=True)
class GpuMetrics:
    """One GPU; VRAM is in bytes and temperature is in degrees Celsius."""

    sampled_at: datetime
    index: int
    name: str
    utilization_percent: float | None
    vram_total_bytes: int | None
    vram_used_bytes: int | None
    temperature_celsius: float | None
    source: str

    def __post_init__(self) -> None:
        require_utc(self.sampled_at)
        require_nonnegative(self.index, "index")
        if not self.name or not self.source:
            raise ValueError("name and source must not be empty")
        if self.utilization_percent is not None:
            require_percent(self.utilization_percent, "utilization_percent")
        if self.vram_total_bytes is not None:
            require_nonnegative(self.vram_total_bytes, "vram_total_bytes")
        if self.vram_used_bytes is not None:
            require_nonnegative(self.vram_used_bytes, "vram_used_bytes")
        if (
            self.vram_total_bytes is not None
            and self.vram_used_bytes is not None
            and self.vram_used_bytes > self.vram_total_bytes
        ):
            raise ValueError("vram_used_bytes cannot exceed vram_total_bytes")
        if self.temperature_celsius is not None and not isfinite(
            self.temperature_celsius
        ):
            raise ValueError("temperature_celsius must be finite")


@dataclass(frozen=True, slots=True)
class GpuSnapshot:
    """All GPUs returned by a provider in one collection cycle."""

    sampled_at: datetime
    devices: tuple[GpuMetrics, ...]

    def __post_init__(self) -> None:
        require_utc(self.sampled_at)
        if not self.devices:
            raise ValueError("GPU snapshot requires at least one device")
        if any(device.sampled_at != self.sampled_at for device in self.devices):
            raise ValueError("all GPU devices must share the snapshot timestamp")
        indexes = [device.index for device in self.devices]
        if len(indexes) != len(set(indexes)):
            raise ValueError("GPU indexes must be unique")
