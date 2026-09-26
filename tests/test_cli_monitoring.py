"""CLI output uses observed snapshots and predictable process ordering."""

from dataclasses import replace
from datetime import UTC, datetime
from io import StringIO

import pytest
from rich.console import Console
from typer.testing import CliRunner

from systempulse.cli import app
from systempulse.cli_top import render_top
from systempulse.domain.availability import Availability, CollectorStatus
from systempulse.domain.gpu import GpuMetrics, GpuSnapshot
from systempulse.domain.io import DiskMetrics, NetworkMetrics
from systempulse.domain.metrics import CpuMetrics, MemoryMetrics, SystemMetrics
from systempulse.domain.processes import ProcessMetrics, ProcessSnapshot
from systempulse.domain.snapshots import MetricSnapshot, SystemSnapshot
from systempulse.presentation import format_bytes, format_percent
from systempulse.services.process_query import ProcessQuery, ProcessSort


def _process(at: datetime, pid: int, name: str, cpu: float, rss: int) -> ProcessMetrics:
    return ProcessMetrics(
        sampled_at=at,
        pid=pid,
        identity=None,
        name=name,
        cpu_percent=cpu,
        memory_rss_bytes=rss,
        status=None,
        user=None,
        threads=None,
        parent_pid=None,
    )


@pytest.fixture
def observed_snapshot(monkeypatch: pytest.MonkeyPatch) -> SystemSnapshot:
    at = datetime.now(UTC)
    cpu = CpuMetrics(at, 37.5, (37.5,), 1, 1, None, None)
    memory = MemoryMetrics(at, 1024, 512, 512, 50.0, None, None, None)
    processes = ProcessSnapshot(
        at,
        (
            _process(at, 11, "Fast", 40.0, 100 * 1024 * 1024),
            _process(at, 22, "Heavy", 5.0, 200 * 1024 * 1024),
        ),
    )
    statuses = tuple(
        CollectorStatus(name, Availability.AVAILABLE, at)
        for name in ("cpu", "memory", "processes")
    )
    snapshot = SystemSnapshot(
        at,
        MetricSnapshot(
            at,
            cpu,
            memory,
            DiskMetrics(at, "/", 1000, 400, 600, 40.0, 100, 200, 50.0, 20.0),
            NetworkMetrics(at, 1000, 2000, 100.0, 25.0, ()),
        ),
        processes,
        SystemMetrics(at, "Test OS", "1.0", "test64", "host", at),
        statuses,
        GpuSnapshot(
            at,
            (
                GpuMetrics(
                    at, 0, "Test GPU", 38.0, 6 * 1024**3, 2 * 1024**3, 51.0, "test"
                ),
            ),
        ),
    )
    monkeypatch.setattr("systempulse.cli._sample", lambda: snapshot)
    return snapshot


def test_status_shows_measured_values_and_distinct_process_leaders(
    observed_snapshot: SystemSnapshot,
) -> None:
    result = CliRunner().invoke(app, ["status"])

    assert result.exit_code == 0
    assert "37.5%" in result.stdout
    assert "50.0%" in result.stdout
    assert "Fast (PID 11)" in result.stdout
    assert "Heavy (PID 22)" in result.stdout
    assert "Test OS 1.0" in result.stdout
    assert "0h 0m" in result.stdout
    assert "Test GPU" in result.stdout
    assert "38.0%" in result.stdout
    assert "2.0 GiB / 6.0 GiB" in result.stdout
    assert "51 C" in result.stdout
    assert "Home disk" in result.stdout
    assert "40.0%" in result.stdout
    assert "Network download" in result.stdout
    assert "100 B/s" in result.stdout


def test_processes_sort_filter_and_limit(observed_snapshot: SystemSnapshot) -> None:
    runner = CliRunner()
    by_memory = runner.invoke(app, ["processes", "--sort", "memory", "--limit", "1"])
    filtered = runner.invoke(app, ["processes", "--search", "fast"])

    assert by_memory.exit_code == 0
    assert "Heavy" in by_memory.stdout
    assert "Fast" not in by_memory.stdout
    assert filtered.exit_code == 0
    assert "Fast" in filtered.stdout
    assert "Heavy" not in filtered.stdout


def test_failed_collectors_do_not_invent_metrics(
    observed_snapshot: SystemSnapshot, monkeypatch: pytest.MonkeyPatch
) -> None:
    at = observed_snapshot.created_at
    missing = replace(
        observed_snapshot,
        metrics=MetricSnapshot(at, None, None),
        processes=None,
        system=None,
        gpu=None,
        collector_statuses=(CollectorStatus("cpu", Availability.ERROR, at, "OSError"),),
    )
    monkeypatch.setattr("systempulse.cli._sample", lambda: missing)

    status = CliRunner().invoke(app, ["status"])
    processes = CliRunner().invoke(app, ["processes"])

    assert status.exit_code == 0
    assert "Unavailable" in status.stdout
    assert "cpu (error)" in status.stdout
    assert "Uptime" in status.stdout
    assert "GPU" in status.stdout
    assert "Fast" not in status.stdout
    assert processes.exit_code == 1
    assert "Process metrics are unavailable." in processes.stdout


def test_formatting_marks_missing_values() -> None:
    assert format_bytes(None) == "Unavailable"
    assert format_percent(None) == "Unavailable"
    assert format_bytes(1024**2) == "1.0 MiB"


def test_top_renders_memory_order_and_missing_process_state(
    observed_snapshot: SystemSnapshot,
) -> None:
    output = StringIO()
    display = Console(file=output, width=80, force_terminal=False)
    display.print(
        render_top(
            observed_snapshot,
            ProcessQuery(sort=ProcessSort.MEMORY, limit=2),
            height=30,
        )
    )
    rendered = output.getvalue()
    assert rendered.index("Heavy") < rendered.index("Fast")
    assert "37.5%" in rendered
    assert "50.0%" in rendered
    assert "q / Ctrl+C to quit" in rendered

    output = StringIO()
    display = Console(file=output, width=80, force_terminal=False)
    display.print(
        render_top(replace(observed_snapshot, processes=None), ProcessQuery(), 30)
    )
    assert "Process metrics unavailable" in output.getvalue()


def test_top_requires_interactive_terminal() -> None:
    result = CliRunner().invoke(app, ["top"])
    assert result.exit_code == 1
    assert "needs an interactive terminal" in result.output
