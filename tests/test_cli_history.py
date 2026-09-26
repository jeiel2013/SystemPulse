"""History command reads only local stored measurements."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from systempulse.cli import app
from systempulse.domain.metrics import CpuMetrics
from systempulse.domain.snapshots import MetricSnapshot, SystemSnapshot
from systempulse.history.store import HistoryStore


def test_history_command_shows_recorded_cpu(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "history.sqlite3"
    at = datetime.now(UTC)
    cpu = CpuMetrics(at, 37.0, (37.0,), 1, 1, None, None)
    store = HistoryStore(path)
    store.record(SystemSnapshot(at, MetricSnapshot(at, cpu, None), None, None, ()))
    store.close()
    monkeypatch.setattr("systempulse.cli.history_database_path", lambda: path)

    result = CliRunner().invoke(app, ["history", "--range", "10m"])

    assert result.exit_code == 0
    assert "37.0%" in result.stdout
    assert "SystemPulse history" in result.stdout
