"""Small in-memory application state shared by terminal views."""

from collections import deque
from dataclasses import dataclass
from datetime import datetime

from systempulse.domain.analysis import Alert, AlertState, Observation
from systempulse.domain.availability import CollectorStatus
from systempulse.domain.processes import ProcessIdentity, ProcessMetrics
from systempulse.domain.snapshots import SystemSnapshot


@dataclass(frozen=True, slots=True)
class RecentMetricSample:
    """Small chart sample that does not retain a full process table."""

    sampled_at: datetime
    cpu_percent: float | None
    memory_percent: float | None


class ApplicationState:
    """Keep the latest snapshot and a bounded set of recent observations."""

    def __init__(self, history_limit: int = 60) -> None:
        if history_limit < 1:
            raise ValueError("history_limit must be positive")
        self._current: SystemSnapshot | None = None
        self._recent: deque[RecentMetricSample] = deque(maxlen=history_limit)
        self.selected_process: ProcessIdentity | None = None
        self._observations: deque[Observation] = deque(maxlen=100)
        self._alerts: deque[Alert] = deque(maxlen=100)

    @property
    def observations(self) -> tuple[Observation, ...]:
        return tuple(self._observations)

    @property
    def alerts(self) -> tuple[Alert, ...]:
        return tuple(self._alerts)

    @property
    def active_alerts(self) -> tuple[Alert, ...]:
        return tuple(
            alert for alert in self._alerts if alert.state == AlertState.ACTIVE
        )

    def add_analysis(
        self,
        observations: tuple[Observation, ...],
        new_alerts: tuple[Alert, ...],
        ended_alerts: tuple[Alert, ...],
    ) -> None:
        self._observations.extend(observations)
        for alert in (*new_alerts, *ended_alerts):
            self._replace_alert(alert)

    def update_alert(self, alert: Alert) -> None:
        self._replace_alert(alert)

    def _replace_alert(self, alert: Alert) -> None:
        self._alerts = deque(
            (
                existing
                for existing in self._alerts
                if (existing.rule_id, existing.triggered_at)
                != (alert.rule_id, alert.triggered_at)
            ),
            maxlen=100,
        )
        self._alerts.append(alert)

    @property
    def current_snapshot(self) -> SystemSnapshot | None:
        """Return the last complete snapshot, if collection has started."""
        return self._current

    @property
    def recent_samples(self) -> tuple[RecentMetricSample, ...]:
        """Return bounded CPU and memory readings oldest first for charts."""
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
        self._current = snapshot
        self._recent.append(
            RecentMetricSample(
                snapshot.created_at,
                snapshot.metrics.cpu.total_percent if snapshot.metrics.cpu else None,
                snapshot.metrics.memory.percent if snapshot.metrics.memory else None,
            )
        )
        if snapshot.processes is not None and self.selected_process_metrics is None:
            self.selected_process = None
