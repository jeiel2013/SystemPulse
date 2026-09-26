"""Evaluate sustained thresholds without claiming causes."""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from systempulse.domain.analysis import Alert, AlertState, MetricKey, Observation, Rule
from systempulse.domain.snapshots import SystemSnapshot


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    observations: tuple[Observation, ...]
    active_alerts: tuple[Alert, ...]
    new_alerts: tuple[Alert, ...]
    ended_alerts: tuple[Alert, ...]


class RuleEngine:
    """Require continuous fresh evidence before triggering each configured rule."""

    def __init__(
        self, rules: tuple[Rule, ...], *, max_gap: timedelta = timedelta(seconds=5)
    ) -> None:
        if len({rule.id for rule in rules}) != len(rules):
            raise ValueError("rule ids must be unique")
        self.rules = rules
        self.max_gap = max_gap
        self._started: dict[str, datetime] = {}
        self._last_seen: dict[str, datetime] = {}
        self._active: dict[str, Alert] = {}

    def evaluate(self, snapshot: SystemSnapshot) -> AnalysisResult:
        """Create alerts only after the threshold persisted for its full duration."""
        observations: list[Observation] = []
        new: list[Alert] = []
        ended: list[Alert] = []
        now = snapshot.created_at
        for rule in self.rules:
            reading = _reading(snapshot, rule.metric)
            valid = (
                reading is not None and timedelta(0) <= now - reading[1] <= self.max_gap
            )
            if not valid or reading is None or reading[0] <= rule.threshold_percent:
                self._started.pop(rule.id, None)
                self._last_seen.pop(rule.id, None)
                alert = self._active.pop(rule.id, None)
                if alert is not None:
                    ended.append(
                        replace(alert, state=AlertState.RESOLVED, ended_at=now)
                    )
                continue
            value, sampled_at = reading
            last_seen = self._last_seen.get(rule.id)
            if last_seen is None or sampled_at - last_seen > self.max_gap:
                self._started[rule.id] = sampled_at
            self._last_seen[rule.id] = sampled_at
            start = self._started[rule.id]
            duration = (sampled_at - start).total_seconds()
            if duration >= rule.for_seconds:
                message = (
                    f"{rule.metric.value} stayed above {rule.threshold_percent:g}% "
                    f"for {int(duration)}s (latest {value:.1f}%)."
                )
                observations.append(
                    Observation(sampled_at, rule.metric, value, message)
                )
                if rule.id not in self._active:
                    alert = Alert(rule.id, sampled_at, rule.severity, message)
                    self._active[rule.id] = alert
                    new.append(alert)
        return AnalysisResult(
            tuple(observations), tuple(self._active.values()), tuple(new), tuple(ended)
        )

    def dismiss(self, rule_id: str) -> Alert | None:
        """Hide an active alert until its condition ends and can re-arm."""
        alert = self._active.get(rule_id)
        if alert is None:
            return None
        dismissed = replace(alert, state=AlertState.DISMISSED)
        self._active[rule_id] = dismissed
        return dismissed


def _reading(
    snapshot: SystemSnapshot, metric: MetricKey
) -> tuple[float, datetime] | None:
    if metric == MetricKey.CPU_PERCENT:
        cpu = snapshot.metrics.cpu
        return (cpu.total_percent, cpu.sampled_at) if cpu is not None else None
    if metric == MetricKey.MEMORY_PERCENT:
        memory = snapshot.metrics.memory
        return (memory.percent, memory.sampled_at) if memory is not None else None
    disk = snapshot.metrics.disk
    return (disk.percent, disk.sampled_at) if disk is not None else None
