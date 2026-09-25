"""Application state remains bounded and respects process identity."""

from datetime import UTC, datetime, timedelta

import pytest

from systempulse.domain.processes import (
    ProcessIdentity,
    ProcessMetrics,
    ProcessSnapshot,
)
from systempulse.domain.snapshots import MetricSnapshot, SystemSnapshot
from systempulse.services.state import ApplicationState


def _snapshot(at: datetime, process: ProcessMetrics | None = None) -> SystemSnapshot:
    return SystemSnapshot(
        created_at=at,
        metrics=MetricSnapshot(created_at=at, cpu=None, memory=None),
        processes=ProcessSnapshot(at, (process,) if process is not None else (), 0),
        system=None,
        collector_statuses=(),
    )


def _process(at: datetime, identity: ProcessIdentity) -> ProcessMetrics:
    return ProcessMetrics(
        sampled_at=at,
        pid=identity.pid,
        identity=identity,
        name="example",
        cpu_percent=None,
        memory_rss_bytes=None,
        status=None,
        user=None,
        threads=None,
        parent_pid=None,
    )


def test_state_keeps_only_configured_history() -> None:
    state = ApplicationState(history_limit=2)
    start = datetime.now(UTC)
    for offset in range(3):
        state.update(_snapshot(start + timedelta(seconds=offset)))

    assert len(state.recent_snapshots) == 2
    assert state.recent_snapshots[0].created_at == start + timedelta(seconds=1)
    assert state.current_snapshot == state.recent_snapshots[-1]


def test_selection_does_not_follow_reused_pid() -> None:
    state = ApplicationState()
    at = datetime.now(UTC)
    old_identity = ProcessIdentity(42, at - timedelta(hours=1))
    new_identity = ProcessIdentity(42, at)
    old_process = _process(at, old_identity)
    new_process = _process(at + timedelta(seconds=1), new_identity)
    state.update(_snapshot(at, old_process))
    state.selected_process = old_identity
    assert state.selected_process_metrics == old_process

    state.update(_snapshot(at + timedelta(seconds=1), new_process))
    assert state.selected_process is None
    assert state.selected_process_metrics is None


def test_state_rejects_backwards_snapshot() -> None:
    state = ApplicationState()
    at = datetime.now(UTC)
    state.update(_snapshot(at))
    with pytest.raises(ValueError, match="backwards"):
        state.update(_snapshot(at - timedelta(seconds=1)))
