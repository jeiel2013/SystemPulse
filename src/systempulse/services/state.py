"""Small in-memory application state shared by terminal views."""

from collections import deque

from systempulse.domain.availability import CollectorStatus
from systempulse.domain.processes import ProcessIdentity, ProcessMetrics
from systempulse.domain.snapshots import SystemSnapshot


class ApplicationState:
    """Keep the latest snapshot and a bounded set of recent observations."""

    def __init__(self, history_limit: int = 60) -> None:
        if history_limit < 1:
            raise ValueError("history_limit must be positive")
        self._recent: deque[SystemSnapshot] = deque(maxlen=history_limit)
        self.selected_process: ProcessIdentity | None = None

    @property
    def current_snapshot(self) -> SystemSnapshot | None:
        """Return the last complete snapshot, if collection has started."""
        return self._recent[-1] if self._recent else None

    @property
    def recent_snapshots(self) -> tuple[SystemSnapshot, ...]:
        """Return recent snapshots oldest first for charts."""
        return tuple(self._recent)

    @property
    def collector_statuses(self) -> tuple[CollectorStatus, ...]:
        """Expose status from the latest snapshot without a second state copy."""
        snapshot = self.current_snapshot
        return snapshot.collector_statuses if snapshot is not None else ()

    @property
    def selected_process_metrics(self) -> ProcessMetrics | None:
        """Resolve selection by PID and creation time to avoid PID reuse."""
        snapshot = self.current_snapshot
        if (
            snapshot is None
            or snapshot.processes is None
            or self.selected_process is None
        ):
            return None
        return next(
            (
                process
                for process in snapshot.processes.processes
                if process.identity == self.selected_process
            ),
            None,
        )

    def update(self, snapshot: SystemSnapshot) -> None:
        """Publish a new snapshot and clear a process that has disappeared."""
        current = self.current_snapshot
        if current is not None and snapshot.created_at < current.created_at:
            raise ValueError("snapshot time moved backwards")
        self._recent.append(snapshot)
        if snapshot.processes is not None and self.selected_process_metrics is None:
            self.selected_process = None
