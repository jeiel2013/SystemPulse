"""Export one observed snapshot without a server or network connection."""

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from html import escape
from io import StringIO
from pathlib import Path

from systempulse.domain.snapshots import SystemSnapshot
from systempulse.platform.paths import reports_directory
from systempulse.services.process_query import (
    ProcessQuery,
    ProcessSort,
    query_processes,
)


class ReportFormat(StrEnum):
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    MARKDOWN = "markdown"

    @property
    def extension(self) -> str:
        return "md" if self == self.MARKDOWN else self.value


@dataclass(frozen=True, slots=True)
class ReportRow:
    name: str
    value: str
    unit: str


@dataclass(frozen=True, slots=True)
class ReportProcess:
    pid: int
    name: str
    cpu_percent: float | None
    memory_bytes: int | None


@dataclass(frozen=True, slots=True)
class SystemReport:
    observed_at: datetime
    rows: tuple[ReportRow, ...]
    top_processes: tuple[ReportProcess, ...]


def build_report(snapshot: SystemSnapshot) -> SystemReport:
    """Include only measurements actually present in the current snapshot."""
    rows: list[ReportRow] = []

    def add(name: str, value: int | float | None, unit: str) -> None:
        if value is not None:
            rows.append(ReportRow(name, str(value), unit))

    cpu = snapshot.metrics.cpu
    memory = snapshot.metrics.memory
    disk = snapshot.metrics.disk
    network = snapshot.metrics.network
    add("CPU usage", cpu.total_percent if cpu else None, "percent")
    add("Memory usage", memory.percent if memory else None, "percent")
    add("Memory available", memory.available_bytes if memory else None, "bytes")
    add("Home disk usage", disk.percent if disk else None, "percent")
    add("Home disk free", disk.free_bytes if disk else None, "bytes")
    add(
        "Network download",
        network.download_bytes_per_second if network else None,
        "bytes/second",
    )
    add(
        "Network upload",
        network.upload_bytes_per_second if network else None,
        "bytes/second",
    )
    add(
        "Battery charge",
        snapshot.battery.percent if snapshot.battery else None,
        "percent",
    )
    if snapshot.gpu is not None:
        for gpu in snapshot.gpu.devices:
            prefix = f"GPU {gpu.index} ({gpu.name})"
            add(f"{prefix} load", gpu.utilization_percent, "percent")
            add(f"{prefix} VRAM used", gpu.vram_used_bytes, "bytes")
            add(f"{prefix} VRAM total", gpu.vram_total_bytes, "bytes")
            add(f"{prefix} temperature", gpu.temperature_celsius, "C")
    processes = snapshot.processes.processes if snapshot.processes else ()
    top = tuple(
        ReportProcess(
            row.pid, row.name or "Unknown", row.cpu_percent, row.memory_rss_bytes
        )
        for row in query_processes(
            processes, ProcessQuery(sort=ProcessSort.CPU, limit=10)
        )
    )
    return SystemReport(snapshot.created_at, tuple(rows), top)


def render_report(report: SystemReport, format: ReportFormat) -> str:
    """Produce a self-contained static report with escaped untrusted names."""
    timestamp = report.observed_at.isoformat()
    if format == ReportFormat.JSON:
        return (
            json.dumps(
                {
                    "observed_at": timestamp,
                    "metrics": [asdict(row) for row in report.rows],
                    "top_processes": [
                        asdict(process) for process in report.top_processes
                    ],
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )
    if format == ReportFormat.CSV:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(("kind", "name", "value", "unit"))
        for row in report.rows:
            writer.writerow(
                ("metric", _safe_csv(row.name), _safe_csv(row.value), row.unit)
            )
        for process in report.top_processes:
            writer.writerow(("process", _safe_csv(process.name), process.pid, "pid"))
        return output.getvalue()
    if format == ReportFormat.MARKDOWN:
        lines = [
            "# SystemPulse report",
            "",
            f"Observed: {timestamp}",
            "",
            "| Metric | Value | Unit |",
            "| --- | ---: | --- |",
        ]
        lines.extend(
            f"| {_safe_markdown(row.name)} | {_safe_markdown(row.value)} | {row.unit} |"
            for row in report.rows
        )
        lines.extend(
            (
                "",
                "## Top CPU processes",
                "",
                "| PID | Name | CPU % | Memory bytes |",
                "| ---: | --- | ---: | ---: |",
            )
        )
        lines.extend(
            f"| {process.pid} | {_safe_markdown(process.name)} | "
            f"{_display_number(process.cpu_percent)} | "
            f"{_display_number(process.memory_bytes)} |"
            for process in report.top_processes
        )
        return "\n".join(lines) + "\n"
    rows = "".join(
        f"<tr><td>{escape(row.name)}</td><td>{escape(row.value)}</td><td>{escape(row.unit)}</td></tr>"
        for row in report.rows
    )
    processes = "".join(
        f"<tr><td>{process.pid}</td><td>{escape(process.name)}</td>"
        f"<td>{_display_number(process.cpu_percent)}</td>"
        f"<td>{_display_number(process.memory_bytes)}</td></tr>"
        for process in report.top_processes
    )
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        "<title>SystemPulse report</title><style>"
        "body{font:16px system-ui;max-width:60rem;margin:2rem auto;"
        "padding:0 1rem;background:#101820;color:#edf2f7}"
        "table{border-collapse:collapse;width:100%;margin:1rem 0}"
        "td,th{padding:.5rem;border-bottom:1px solid #425466;"
        "text-align:left}</style>"
        f"<h1>SystemPulse report</h1><p>Observed: {escape(timestamp)}</p>"
        "<h2>Metrics</h2><table><tr><th>Metric</th><th>Value</th>"
        f"<th>Unit</th></tr>{rows}</table>"
        "<h2>Top CPU processes</h2><table><tr><th>PID</th><th>Name</th>"
        f"<th>CPU %</th><th>Memory bytes</th></tr>{processes}</table></html>"
    )


def write_report(
    report: SystemReport, format: ReportFormat, output: Path | None = None
) -> Path:
    """Create a report file without overwriting an existing file."""
    destination = output or (
        reports_directory()
        / f"report-{report.observed_at.strftime('%Y%m%d-%H%M%S-%f')}.{format.extension}"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8", newline="") as stream:
        stream.write(render_report(report, format))
    return destination


def _safe_csv(value: str) -> str:
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


def _safe_markdown(value: str) -> str:
    return escape(value).replace("|", "\\|").replace("\n", " ")


def _display_number(value: int | float | None) -> str:
    return str(value) if value is not None else "Unavailable"
