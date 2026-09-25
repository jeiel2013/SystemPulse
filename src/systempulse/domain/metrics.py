"""System-wide metric values in stable core units."""

from dataclasses import dataclass
from datetime import datetime

from systempulse.domain._validation import (
    require_nonnegative,
    require_percent,
    require_utc,
)


@dataclass(frozen=True, slots=True)
class CpuMetrics:
    """One CPU sample; frequency is MHz and load is platform dependent."""

    sampled_at: datetime
    total_percent: float
    per_core_percent: tuple[float, ...]
    physical_cores: int | None
    logical_cores: int | None
    frequency_mhz: float | None
    load_average: tuple[float, float, float] | None
    source: str = "psutil"

    def __post_init__(self) -> None:
        require_utc(self.sampled_at)
        require_percent(self.total_percent, "total_percent")
        for percent in self.per_core_percent:
            require_percent(percent, "per_core_percent")
        for name, count in (
            ("physical_cores", self.physical_cores),
            ("logical_cores", self.logical_cores),
        ):
            if count is not None and count < 1:
                raise ValueError(f"{name} must be positive when available")
        if self.frequency_mhz is not None:
            require_nonnegative(self.frequency_mhz, "frequency_mhz")
        if self.load_average is not None:
            for load in self.load_average:
                require_nonnegative(load, "load_average")
        if not self.source:
            raise ValueError("source must not be empty")


@dataclass(frozen=True, slots=True)
class MemoryMetrics:
    """One memory sample; capacity values are bytes."""

    sampled_at: datetime
    total_bytes: int
    used_bytes: int
    available_bytes: int
    percent: float
    swap_total_bytes: int | None
    swap_used_bytes: int | None
    swap_percent: float | None
    source: str = "psutil"

    def __post_init__(self) -> None:
        require_utc(self.sampled_at)
        if self.total_bytes <= 0:
            raise ValueError("total_bytes must be positive")
        require_nonnegative(self.used_bytes, "used_bytes")
        require_nonnegative(self.available_bytes, "available_bytes")
        require_percent(self.percent, "percent")
        if self.swap_total_bytes is not None:
            require_nonnegative(self.swap_total_bytes, "swap_total_bytes")
        if self.swap_used_bytes is not None:
            require_nonnegative(self.swap_used_bytes, "swap_used_bytes")
        if self.swap_percent is not None:
            require_percent(self.swap_percent, "swap_percent")
        swap_values = (
            self.swap_total_bytes,
            self.swap_used_bytes,
            self.swap_percent,
        )
        if any(value is None for value in swap_values) and not all(
            value is None for value in swap_values
        ):
            raise ValueError("swap values must be available together")
        if not self.source:
            raise ValueError("source must not be empty")
