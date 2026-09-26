"""Typed storage and network observations in bytes and bytes per second."""

from dataclasses import dataclass
from datetime import datetime

from systempulse.domain._validation import (
    require_nonnegative,
    require_percent,
    require_utc,
)


@dataclass(frozen=True, slots=True)
class DiskMetrics:
    """Usage of the home volume and optional system-wide I/O counters."""

    sampled_at: datetime
    mountpoint: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float
    read_bytes: int | None
    write_bytes: int | None
    read_bytes_per_second: float | None
    write_bytes_per_second: float | None
    source: str = "psutil"

    def __post_init__(self) -> None:
        require_utc(self.sampled_at)
        if not self.mountpoint or self.total_bytes <= 0:
            raise ValueError("disk mountpoint and capacity must be available")
        for name in (
            "used_bytes",
            "free_bytes",
            "read_bytes",
            "write_bytes",
            "read_bytes_per_second",
            "write_bytes_per_second",
        ):
            value = getattr(self, name)
            if value is not None:
                require_nonnegative(value, name)
        require_percent(self.percent, "percent")


@dataclass(frozen=True, slots=True)
class NetworkInterfaceMetrics:
    """Cumulative traffic for one interface, without inferred process ownership."""

    name: str
    received_bytes: int
    sent_bytes: int

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("interface name must not be empty")
        require_nonnegative(self.received_bytes, "received_bytes")
        require_nonnegative(self.sent_bytes, "sent_bytes")


@dataclass(frozen=True, slots=True)
class NetworkMetrics:
    """Host traffic totals and rates derived from successive counter readings."""

    sampled_at: datetime
    received_bytes: int
    sent_bytes: int
    download_bytes_per_second: float | None
    upload_bytes_per_second: float | None
    interfaces: tuple[NetworkInterfaceMetrics, ...]
    source: str = "psutil"

    def __post_init__(self) -> None:
        require_utc(self.sampled_at)
        for name in (
            "received_bytes",
            "sent_bytes",
            "download_bytes_per_second",
            "upload_bytes_per_second",
        ):
            value = getattr(self, name)
            if value is not None:
                require_nonnegative(value, name)
