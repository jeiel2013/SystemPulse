"""Tests for the initial command-line entry point."""

from importlib.metadata import version

from typer.testing import CliRunner

from systempulse.cli import app


def test_version_matches_installed_metadata() -> None:
    result = CliRunner().invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == f"SystemPulse {version('systempulse-monitor')}"


def test_default_command_describes_development_state() -> None:
    result = CliRunner().invoke(app, [])

    assert result.exit_code == 0
    assert "not available" in result.stdout
