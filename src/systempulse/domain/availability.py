"""Availability and health information for local metric sources."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from systempulse.domain._validation import require_utc


class Availability(StrEnum):
    """The outcome of a collector attempt."""

    AVAILABLE = "available"
    WARMING_UP = "warming_up"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class CollectorStatus:
    """A timestamped collector state for the application and TUI."""

    name: str
    availability: Availability
    checked_at: datetime
    reason: str | None = None

    def __post_init__(self) -> None:
        require_utc(self.checked_at)
        if not self.name:
            raise ValueError("collector name must not be empty")


@dataclass(frozen=True, slots=True)
class Capability:
    """A feature's observed availability on the current machine."""

    name: str
    availability: Availability
    checked_at: datetime
    reason: str | None = None

    def __post_init__(self) -> None:
        require_utc(self.checked_at)
        if not self.name:
            raise ValueError("capability name must not be empty")
