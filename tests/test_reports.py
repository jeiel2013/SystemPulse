"""Static exports preserve observed values and escape process names."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from systempulse.cli import app
from systempulse.domain.metrics import CpuMetrics
from systempulse.domain.processes import ProcessMetrics, ProcessSnapshot
from systempulse.domain.snapshots import MetricSnapshot, SystemSnapshot
from systempulse.reports.export import (
    ReportFormat,
    build_report,
    render_report,
    write_report,
)


def sample() -> SystemSnapshot:
    at = datetime.now(UTC)
    cpu = CpuMetrics(at, 25.0, (25.0,), 1, 1, None, None)
    process = ProcessMetrics(
        at, 42, None, "<script>|=bad", 10.0, 1024, None, None, None, None
    )
    formula = ProcessMetrics(at, 43, None, "=bad", 5.0, 512, None, None, None, None)
    return SystemSnapshot(
        at,
        MetricSnapshot(at, cpu, None),
        ProcessSnapshot(at, (process, formula)),
        None,
        (),
    )


def test_all_report_formats_escape_names_and_keep_real_metrics(tmp_path: Path) -> None:
    report = build_report(sample())
    assert any(row.name == "CPU usage" and row.value == "25.0" for row in report.rows)
    json_text = render_report(report, ReportFormat.JSON)
    csv_text = render_report(report, ReportFormat.CSV)
    markdown = render_report(report, ReportFormat.MARKDOWN)
    html = render_report(report, ReportFormat.HTML)
    assert '"cpu_percent": 10.0' in json_text
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;script&gt;" in markdown
    assert "\\|" in markdown
    assert "<script>|=bad" in csv_text
    assert "'=bad" in csv_text
    path = write_report(report, ReportFormat.JSON, tmp_path / "report.json")
    assert path.read_text(encoding="utf-8") == json_text
    with pytest.raises(FileExistsError):
        write_report(report, ReportFormat.JSON, path)


def test_report_cli_writes_requested_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("systempulse.cli._sample", sample)
    destination = tmp_path / "report.md"
    result = CliRunner().invoke(
        app, ["report", "--format", "markdown", "--output", str(destination)]
    )
    assert result.exit_code == 0
    assert destination.exists()
    assert "Export completed" in result.stdout
