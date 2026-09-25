"""Process identity and timestamped process observations."""

from dataclasses import dataclass
from datetime import datetime

from systempulse.domain._validation import require_nonnegative, require_utc


@dataclass(frozen=True, slots=True)
class ProcessIdentity:
    """A process instance, distinct from a later process reusing its PID."""

    pid: int
    created_at: datetime

    def __post_init__(self) -> None:
        require_nonnegative(self.pid, "pid")
        require_utc(self.created_at, "created_at")


@dataclass(frozen=True, slots=True)
class ProcessMetrics:
    """One process row; CPU percent is relative to one logical CPU."""

    sampled_at: datetime
    pid: int
    identity: ProcessIdentity | None
    name: str | None
    cpu_percent: float | None
    memory_rss_bytes: int | None
    status: str | None
    user: str | None
    threads: int | None
    parent_pid: int | None
    source: str = "psutil"

    def __post_init__(self) -> None:
        require_utc(self.sampled_at)
        require_nonnegative(self.pid, "pid")
        if self.identity is not None and self.identity.pid != self.pid:
            raise ValueError("identity PID must match process PID")
        for name, value in (
            ("cpu_percent", self.cpu_percent),
            ("memory_rss_bytes", self.memory_rss_bytes),
            ("threads", self.threads),
            ("parent_pid", self.parent_pid),
        ):
            if value is not None:
                require_nonnegative(value, name)
        if not self.source:
            raise ValueError("source must not be empty")


@dataclass(frozen=True, slots=True)
class ProcessSnapshot:
    """A scan of observable processes at one UTC instant."""

    sampled_at: datetime
    processes: tuple[ProcessMetrics, ...]
    skipped_count: int = 0

    def __post_init__(self) -> None:
        require_utc(self.sampled_at)
        require_nonnegative(self.skipped_count, "skipped_count")


@dataclass(frozen=True, slots=True)
class ProcessDetails:
    """Additional facts read only when a process instance is selected."""

    sampled_at: datetime
    identity: ProcessIdentity
    name: str | None
    status: str | None
    user: str | None
    threads: int | None
    parent_pid: int | None
    executable: str | None
    command_line: tuple[str, ...] | None

    def __post_init__(self) -> None:
        require_utc(self.sampled_at)
        if self.threads is not None:
            require_nonnegative(self.threads, "threads")
        if self.parent_pid is not None:
            require_nonnegative(self.parent_pid, "parent_pid")
