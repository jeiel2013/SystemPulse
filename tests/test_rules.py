"""Alert rules require sustained, fresh, observed metrics."""

from datetime import UTC, datetime, timedelta

from systempulse.domain.analysis import AlertState, MetricKey, Rule
from systempulse.domain.metrics import CpuMetrics
from systempulse.domain.snapshots import MetricSnapshot, SystemSnapshot
from systempulse.rules.engine import RuleEngine


def snapshot(at: datetime, value: float) -> SystemSnapshot:
    cpu = CpuMetrics(at, value, (value,), 1, 1, None, None)
    return SystemSnapshot(at, MetricSnapshot(at, cpu, None), None, None, ())


def test_rule_requires_full_duration_and_resolves_when_condition_ends() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    engine = RuleEngine((Rule("cpu", MetricKey.CPU_PERCENT, 90, 2),))
    assert engine.evaluate(snapshot(start, 95)).new_alerts == ()
    assert engine.evaluate(snapshot(start + timedelta(seconds=1), 96)).new_alerts == ()
    result = engine.evaluate(snapshot(start + timedelta(seconds=2), 97))
    assert len(result.new_alerts) == 1
    assert "97.0%" in result.new_alerts[0].message
    assert "above 90%" in result.observations[0].message
    assert engine.evaluate(snapshot(start + timedelta(seconds=3), 98)).new_alerts == ()
    ended = engine.evaluate(snapshot(start + timedelta(seconds=4), 50)).ended_alerts
    assert ended[0].state == AlertState.RESOLVED


def test_rule_resets_after_gap_and_dismisses_until_rearmed() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    engine = RuleEngine((Rule("cpu", MetricKey.CPU_PERCENT, 90, 1),))
    engine.evaluate(snapshot(start, 95))
    assert engine.evaluate(snapshot(start + timedelta(seconds=10), 95)).new_alerts == ()
    alert = engine.evaluate(snapshot(start + timedelta(seconds=11), 95)).new_alerts[0]
    assert alert.state == AlertState.ACTIVE
    dismissed = engine.dismiss("cpu")
    assert dismissed is not None and dismissed.state == AlertState.DISMISSED
    assert engine.evaluate(snapshot(start + timedelta(seconds=12), 95)).new_alerts == ()
    engine.evaluate(snapshot(start + timedelta(seconds=13), 50))
    engine.evaluate(snapshot(start + timedelta(seconds=14), 95))
    assert (
        len(engine.evaluate(snapshot(start + timedelta(seconds=15), 95)).new_alerts)
        == 1
    )
