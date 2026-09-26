"""History retention preserves observed values without keeping process details."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from systempulse.domain.analysis import Alert, AlertState, Severity
from systempulse.domain.metrics import CpuMetrics, MemoryMetrics
from systempulse.domain.snapshots import MetricSnapshot, SystemSnapshot
from systempulse.history.store import HistoryStore


def snapshot(at: datetime, cpu_percent: float) -> SystemSnapshot:
    cpu = CpuMetrics(at, cpu_percent, (cpu_percent,), 1, 1, None, None)
    memory = MemoryMetrics(at, 1000, 500, 500, 50.0, None, None, None)
    return SystemSnapshot(at, MetricSnapshot(at, cpu, memory), None, None, ())


def test_history_compacts_to_minute_then_quarter_hour_and_expires(
    tmp_path: Path,
) -> None:
    store = HistoryStore(tmp_path / "history.sqlite3")
    start = datetime(2026, 1, 1, 12, tzinfo=UTC)
    store.record(snapshot(start, 20.0))
    store.record(snapshot(start + timedelta(seconds=1), 40.0))
    assert len(store.query(timedelta(minutes=2), now=start + timedelta(seconds=2))) == 2

    store.compact(now=start + timedelta(minutes=11))
    minute = store.query(timedelta(minutes=12), now=start + timedelta(minutes=11))
    assert len(minute) == 1
    assert minute[0].cpu_percent == 30.0
    assert minute[0].memory_percent == 50.0

    store.compact(now=start + timedelta(days=2))
    quarter = store.query(timedelta(days=3), now=start + timedelta(days=2))
    assert len(quarter) == 1
    assert quarter[0].cpu_percent == 30.0

    store.compact(now=start + timedelta(days=31))
    assert store.query(timedelta(days=32), now=start + timedelta(days=31)) == ()
    store.close()


def test_history_rejects_nonpositive_range(tmp_path: Path) -> None:
    import pytest

    store = HistoryStore(tmp_path / "history.sqlite3")
    with pytest.raises(ValueError, match="positive"):
        store.query(timedelta(0))


def test_alert_lifecycle_persists_locally(tmp_path: Path) -> None:
    store = HistoryStore(tmp_path / "history.sqlite3")
    at = datetime(2026, 1, 1, tzinfo=UTC)
    alert = Alert("high-cpu", at, Severity.WARNING, "CPU stayed above 90%")
    store.save_alert(alert)
    assert store.query_alerts()[0] == alert
    dismissed = Alert(
        alert.rule_id,
        alert.triggered_at,
        alert.severity,
        alert.message,
        AlertState.DISMISSED,
    )
    store.save_alert(dismissed)
    assert store.query_alerts()[0].state == AlertState.DISMISSED
    store.close()
