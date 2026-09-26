"""The process tree command displays on-demand ancestry."""

from datetime import UTC, datetime

import pytest
from typer.testing import CliRunner

from systempulse.cli import app
from systempulse.services.process_tree import ProcessTreeEntry, ProcessTreeRow


def test_tree_command_indents_children(monkeypatch: pytest.MonkeyPatch) -> None:
    at = datetime.now(UTC)

    class FakeTreeService:
        async def read(self) -> tuple[ProcessTreeRow, ...]:
            return (
                ProcessTreeRow(ProcessTreeEntry(1, "parent", None, at), 0),
                ProcessTreeRow(ProcessTreeEntry(2, "child", 1, at), 1),
            )

    monkeypatch.setattr("systempulse.cli.ProcessTreeService", FakeTreeService)
    result = CliRunner().invoke(app, ["tree"])
    assert result.exit_code == 0
    assert "parent" in result.stdout
    assert "child" in result.stdout
