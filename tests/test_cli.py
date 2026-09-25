"""Tests for the initial command-line entry point."""

from importlib.metadata import version

from typer.testing import CliRunner

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
