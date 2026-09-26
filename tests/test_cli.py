"""Tests for the initial command-line entry point."""

from importlib.metadata import version

import pytest
from typer.testing import CliRunner

from systempulse import cli
from systempulse.cli import app


def test_version_matches_installed_metadata() -> None:
    result = CliRunner().invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == f"SystemPulse {version('systempulse-monitor')}"


def test_default_command_requires_interactive_terminal() -> None:
    result = CliRunner().invoke(app, [])

    assert result.exit_code == 1
    assert "interactive terminal" in result.output
    assert "systempulse status" in result.output


def test_one_shot_sample_closes_session(monkeypatch: pytest.MonkeyPatch) -> None:
    marker = object()
    closed = False

    class Session:
        async def sample_after_warmup(self) -> object:
            return marker

        async def close(self) -> None:
            nonlocal closed
            closed = True

    monkeypatch.setattr(cli, "create_default_session", Session)

    assert cli._sample() is marker
    assert closed
