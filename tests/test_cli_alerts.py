"""Alert command shows persisted lifecycle without starting collectors."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from systempulse.cli import app
from systempulse.domain.analysis import Alert, Severity
from systempulse.history.store import HistoryStore


def test_alerts_command_reads_local_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "history.sqlite3"
    store = HistoryStore(path)
    store.save_alert(
        Alert("high-memory", datetime.now(UTC), Severity.WARNING, "Memory above 90%")
    )
    store.close()
    monkeypatch.setattr("systempulse.cli.history_database_path", lambda: path)

    result = CliRunner().invoke(app, ["alerts"])

    assert result.exit_code == 0
    assert "Memory above 90%" in result.stdout
    assert "active" in result.stdout
