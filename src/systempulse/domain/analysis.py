"""Evidence-based observations and threshold alerts."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from systempulse.domain._validation import require_percent, require_utc


class MetricKey(StrEnum):
    CPU_PERCENT = "cpu.percent"
    MEMORY_PERCENT = "memory.percent"
    DISK_PERCENT = "disk.percent"


class Severity(StrEnum):
    WARNING = "warning"
    CRITICAL = "critical"


class AlertState(StrEnum):
    ACTIVE = "active"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"


@dataclass(frozen=True, slots=True)
class Rule:
    """A sustained, observable threshold condition."""

    id: str
    metric: MetricKey
    threshold_percent: float
    for_seconds: float
    severity: Severity = Severity.WARNING

    def __post_init__(self) -> None:
        if not self.id or self.for_seconds < 0:
            raise ValueError("rule id must be set and duration nonnegative")
        require_percent(self.threshold_percent, "threshold_percent")


@dataclass(frozen=True, slots=True)
class Observation:
    """A fact derived directly from a timestamped metric."""

    observed_at: datetime
    metric: MetricKey
    value_percent: float
    message: str

    def __post_init__(self) -> None:
        require_utc(self.observed_at)
        require_percent(self.value_percent, "value_percent")


@dataclass(frozen=True, slots=True)
class Alert:
    """A rule match with a lifecycle, without an unsupported diagnosis."""

    rule_id: str
    triggered_at: datetime
    severity: Severity
    message: str
    state: AlertState = AlertState.ACTIVE
    ended_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.rule_id or not self.message:
            raise ValueError("alert id and message must be set")
        require_utc(self.triggered_at)
        if self.ended_at is not None:
            require_utc(self.ended_at, "ended_at")
