"""Doctor reports observed capabilities and signals broken required collectors."""

from datetime import UTC, datetime

import pytest
from typer.testing import CliRunner

from systempulse.cli import app
from systempulse.domain.availability import Availability, CollectorStatus
from systempulse.domain.snapshots import MetricSnapshot, SystemSnapshot
from systempulse.services.doctor import (
    CheckState,
    DoctorCheck,
    DoctorReport,
    assess_environment,
)


def _snapshot(cpu_state: Availability = Availability.AVAILABLE) -> SystemSnapshot:
    at = datetime.now(UTC)
    statuses = tuple(
        CollectorStatus(
            name, cpu_state if name == "cpu" else Availability.AVAILABLE, at
        )
        for name in ("cpu", "memory", "processes", "system")
    )
    return SystemSnapshot(at, MetricSnapshot(at, None, None), None, None, statuses)


def test_doctor_accepts_healthy_collectors_without_interactive_terminal() -> None:
    report = assess_environment(
        _snapshot(),
        python_version=(3, 12, 14),
        platform_tag="win32",
        interactive_terminal=False,
        color_system=None,
        version="0.1.0.dev0",
    )

    assert report.exit_code == 0
    assert len(report.checks) == 7
    assert report.checks[-1].state == CheckState.WARN
    assert "requires an interactive terminal" in report.checks[-1].detail


def test_doctor_distinguishes_warmup_and_collector_failure() -> None:
    warmup = assess_environment(
        _snapshot(Availability.WARMING_UP),
        python_version=(3, 12, 14),
        platform_tag="linux",
        interactive_terminal=True,
        color_system="standard",
        version="0.1.0.dev0",
    )
    failed = assess_environment(
        _snapshot(Availability.ERROR),
        python_version=(3, 12, 14),
        platform_tag="linux",
        interactive_terminal=True,
        color_system="standard",
        version="0.1.0.dev0",
    )

    assert warmup.exit_code == 0
    assert warmup.checks[2].state == CheckState.WARN
    assert failed.exit_code == 1
    assert failed.checks[2].state == CheckState.FAIL
    assert warmup.checks[-1] == DoctorCheck(
        "Terminal colors", CheckState.PASS, "standard"
    )


def test_doctor_flags_missing_collector_and_unsupported_python() -> None:
    snapshot = _snapshot()
    snapshot = SystemSnapshot(
        snapshot.created_at,
        snapshot.metrics,
        None,
        None,
        snapshot.collector_statuses[:-1],
    )
    report = assess_environment(
        snapshot,
        python_version=(3, 11, 9),
        platform_tag="other",
        interactive_terminal=False,
        color_system=None,
        version="0.1.0.dev0",
    )

    assert report.exit_code == 1
    assert report.checks[0].state == CheckState.FAIL
    assert report.checks[1].state == CheckState.WARN
    assert report.checks[5] == DoctorCheck(
        "system collector", CheckState.FAIL, "Not registered"
    )


def test_doctor_treats_optional_gpu_absence_as_warning() -> None:
    snapshot = _snapshot()
    snapshot = SystemSnapshot(
        snapshot.created_at,
        snapshot.metrics,
        None,
        None,
        (
            *snapshot.collector_statuses,
            CollectorStatus("gpu", Availability.UNAVAILABLE, snapshot.created_at),
        ),
    )
    report = assess_environment(
        snapshot,
        python_version=(3, 12, 14),
        platform_tag="linux",
        interactive_terminal=True,
        color_system="standard",
        version="0.1.0.dev0",
    )

    assert report.exit_code == 0
    assert DoctorCheck("GPU provider", CheckState.WARN, "unavailable") in report.checks


def test_doctor_command_reports_results_and_failure_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = DoctorReport(
        version="0.1.0.dev0",
        checks=(DoctorCheck("CPU collector", CheckState.FAIL, "error (OSError)"),),
    )
    monkeypatch.setattr("systempulse.cli.run_doctor", lambda **_kwargs: report)

    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "SystemPulse doctor" in result.stdout
    assert "CPU collector" in result.stdout
    assert "OSError" in result.stdout
