"""Non-interactive local monitoring commands."""

import asyncio
import sys
from contextlib import suppress
from pathlib import Path
from typing import Annotated

import typer
from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from systempulse.cli_top import run_top
from systempulse.config.settings import load_settings
from systempulse.domain.analysis import AlertState
from systempulse.domain.availability import Availability
from systempulse.domain.snapshots import SystemSnapshot
from systempulse.history.ranges import HistoryRange
from systempulse.history.store import HistoryStore
from systempulse.platform.paths import history_database_path
from systempulse.plugins.loader import discover_plugins
from systempulse.presentation import (
    format_bytes,
    format_percent,
    format_rate,
    format_remaining_time,
    format_temperature,
    format_uptime,
)
from systempulse.reports.export import ReportFormat, build_report, write_report
from systempulse.services.doctor import CheckState, run_doctor
from systempulse.services.monitor import create_default_session
from systempulse.services.process_query import (
    ProcessQuery,
    ProcessSort,
    query_processes,
)
from systempulse.services.process_tree import ProcessTreeService
from systempulse.version import get_version

app = typer.Typer(
    add_completion=False,
    help="Local system monitoring and diagnostics for your terminal.",
)
console = Console()


def _sample() -> SystemSnapshot:
    """Observe two cycles to calculate nonblocking CPU rates."""
    async def observe() -> SystemSnapshot:
        session = create_default_session()
        try:
            return await session.sample_after_warmup()
        finally:
            await session.close()

    return asyncio.run(observe())


@app.callback(invoke_without_command=True)
def root(context: typer.Context) -> None:
    """Open the live terminal interface when no command is selected."""
    if context.invoked_subcommand is None:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            typer.echo(
                "SystemPulse needs an interactive terminal. "
                "Use 'systempulse status' for one-shot output.",
                err=True,
            )
            raise typer.Exit(code=1)
        from systempulse.tui.app import PulseApp

        PulseApp().run()


@app.command()
def version() -> None:
    """Show the installed SystemPulse version."""
    typer.echo(f"SystemPulse {get_version()}")


@app.command()
def status() -> None:
    """Show a current CPU, memory, process, and host summary."""
    snapshot = _sample()
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()
    cpu = snapshot.metrics.cpu
    memory = snapshot.metrics.memory
    table.add_row("CPU", format_percent(cpu.total_percent if cpu else None))
    table.add_row("Memory", format_percent(memory.percent if memory else None))
    table.add_row(
        "Available memory", format_bytes(memory.available_bytes if memory else None)
    )
    disk = snapshot.metrics.disk
    network = snapshot.metrics.network
    table.add_row("Home disk", format_percent(disk.percent if disk else None))
    if disk is not None:
        table.add_row("Disk free", format_bytes(disk.free_bytes))
        table.add_row("Disk read", format_rate(disk.read_bytes_per_second))
        table.add_row("Disk write", format_rate(disk.write_bytes_per_second))
    table.add_row(
        "Network download",
        format_rate(network.download_bytes_per_second if network else None),
    )
    table.add_row(
        "Network upload",
        format_rate(network.upload_bytes_per_second if network else None),
    )
    battery = snapshot.battery
    if battery is not None:
        power = "Plugged in" if battery.power_plugged else "On battery"
        table.add_row(
            "Battery",
            f"{format_percent(battery.percent)} · {power} · "
            f"{format_remaining_time(battery.seconds_left)} remaining",
        )
    elif any(status.name == "battery" for status in snapshot.collector_statuses):
        table.add_row("Battery", "Unavailable")
    system = snapshot.system
    table.add_row(
        "System",
        f"{system.platform_name} {system.platform_release}".strip()
        if system is not None
        else "Unavailable",
    )
    table.add_row(
        "Uptime",
        format_uptime(system.boot_time if system else None, snapshot.created_at),
    )
    if snapshot.gpu is None:
        table.add_row("GPU", "Unavailable")
    else:
        gpu = snapshot.gpu.devices[0]
        extra = len(snapshot.gpu.devices) - 1
        label = f"{gpu.name} (+{extra} more)" if extra else gpu.name
        table.add_row("GPU", label)
        table.add_row("GPU load", format_percent(gpu.utilization_percent))
        table.add_row(
            "VRAM",
            f"{format_bytes(gpu.vram_used_bytes)} / "
            f"{format_bytes(gpu.vram_total_bytes)}",
        )
        table.add_row("GPU temperature", format_temperature(gpu.temperature_celsius))
    process_snapshot = snapshot.processes
    if process_snapshot and process_snapshot.processes:
        top_cpu = next(
            (
                process
                for process in query_processes(
                    process_snapshot.processes, ProcessQuery(sort=ProcessSort.CPU)
                )
                if process.cpu_percent is not None
            ),
            None,
        )
        if top_cpu is not None:
            table.add_row(
                "Top CPU process",
                Text.assemble(top_cpu.name or "Unknown", f" (PID {top_cpu.pid})"),
            )
            table.add_row("Process CPU", format_percent(top_cpu.cpu_percent))
        top_memory = next(
            (
                process
                for process in query_processes(
                    process_snapshot.processes, ProcessQuery(sort=ProcessSort.MEMORY)
                )
                if process.memory_rss_bytes is not None
            ),
            None,
        )
        if top_memory is not None:
            table.add_row(
                "Top memory process",
                Text.assemble(top_memory.name or "Unknown", f" (PID {top_memory.pid})"),
            )
            table.add_row("Process memory", format_bytes(top_memory.memory_rss_bytes))
    observed_at = snapshot.created_at.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    table.add_row("Observed", observed_at)
    console.print("[bold cyan]SystemPulse[/bold cyan]")
    console.print(table)
    unavailable = tuple(
        result
        for result in snapshot.collector_statuses
        if result.availability != Availability.AVAILABLE
    )
    if unavailable:
        console.print(
            "Collectors: "
            + ", ".join(
                f"{result.name} ({result.availability.value})" for result in unavailable
            )
        )


@app.command()
def processes(
    sort: Annotated[ProcessSort, typer.Option(help="Sort by CPU, memory, or PID.")] = (
        ProcessSort.CPU
    ),
    limit: Annotated[
        int, typer.Option(min=1, max=500, help="Maximum rows to show.")
    ] = 20,
    search: Annotated[
        str | None, typer.Option(help="Case-insensitive name filter.")
    ] = None,
) -> None:
    """List observed processes with one-second CPU rates."""
    snapshot = _sample()
    process_snapshot = snapshot.processes
    if process_snapshot is None:
        console.print("Process metrics are unavailable.")
        raise typer.Exit(code=1)

    sorted_rows = query_processes(
        process_snapshot.processes,
        ProcessQuery(sort=sort, search=search or "", limit=limit),
    )
    table = Table(title=f"Processes ({len(sorted_rows)} shown)", box=box.SIMPLE)
    table.add_column("PID", justify="right")
    table.add_column("Name", overflow="ellipsis")
    table.add_column("CPU", justify="right")
    table.add_column("Memory", justify="right")
    for row in sorted_rows:
        table.add_row(
            str(row.pid),
            Text(row.name or "Unknown"),
            format_percent(row.cpu_percent),
            format_bytes(row.memory_rss_bytes),
        )
    console.print(table)
    if not sorted_rows:
        console.print("No matching processes.")
    if process_snapshot.skipped_count:
        console.print(f"{process_snapshot.skipped_count} processes could not be read.")


@app.command()
def top(
    sort: Annotated[ProcessSort, typer.Option(help="Sort by CPU, memory, or PID.")] = (
        ProcessSort.CPU
    ),
    limit: Annotated[
        int, typer.Option(min=1, max=500, help="Maximum rows to show.")
    ] = 20,
    search: Annotated[
        str | None, typer.Option(help="Case-insensitive name filter.")
    ] = None,
) -> None:
    """Continuously show CPU, memory, and leading processes; press q to quit."""
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        typer.echo("SystemPulse top needs an interactive terminal.", err=True)
        raise typer.Exit(code=1)
    async def monitor() -> None:
        session = create_default_session()
        try:
            await run_top(
                session,
                console,
                ProcessQuery(sort=sort, search=search or "", limit=limit),
            )
        finally:
            await session.close()

    with suppress(KeyboardInterrupt):
        asyncio.run(monitor())


@app.command()
def doctor() -> None:
    """Check the runtime, shipped collectors, and terminal capabilities."""
    report = run_doctor(
        interactive_terminal=sys.stdin.isatty() and sys.stdout.isatty(),
        color_system=console.color_system,
    )
    table = Table(title=f"SystemPulse doctor ({report.version})", box=box.SIMPLE)
    table.add_column("Result")
    table.add_column("Check")
    table.add_column("Detail", overflow="fold")
    styles = {
        CheckState.PASS: "green",
        CheckState.WARN: "yellow",
        CheckState.FAIL: "red",
    }
    for check in report.checks:
        table.add_row(
            Text(check.state.value.upper(), style=styles[check.state]),
            check.name,
            check.detail,
        )
    console.print(table)
    if report.exit_code:
        raise typer.Exit(code=report.exit_code)


@app.command()
def history(
    range: Annotated[
        HistoryRange, typer.Option(help="History range from 10m to 30d.")
    ] = HistoryRange.TEN_MINUTES,
) -> None:
    """Show recent local metric history without opening the TUI."""
    store = HistoryStore(history_database_path())
    try:
        points = store.query(range.duration)
    finally:
        store.close()
    if not points:
        console.print("No historical data yet. Run systempulse to collect samples.")
        return
    table = Table(title=f"SystemPulse history · {range.value}", box=box.SIMPLE)
    table.add_column("Observed")
    table.add_column("CPU", justify="right")
    table.add_column("Memory", justify="right")
    table.add_column("Disk", justify="right")
    table.add_column("Download", justify="right")
    table.add_column("Upload", justify="right")
    for point in points[-20:]:
        table.add_row(
            point.observed_at.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
            format_percent(point.cpu_percent),
            format_percent(point.memory_percent),
            format_percent(point.disk_percent),
            format_rate(point.download_bytes_per_second),
            format_rate(point.upload_bytes_per_second),
        )
    console.print(table)
    console.print(f"{len(points)} points in range; showing the latest 20.")


@app.command()
def alerts(
    limit: Annotated[int, typer.Option(min=1, max=100)] = 20,
) -> None:
    """Show locally recorded threshold alerts and their current state."""
    store = HistoryStore(history_database_path())
    try:
        entries = store.query_alerts(limit)
    finally:
        store.close()
    if not entries:
        console.print("No alerts recorded.")
        return
    table = Table(title="SystemPulse alerts", box=box.SIMPLE)
    table.add_column("Triggered")
    table.add_column("State")
    table.add_column("Severity")
    table.add_column("Observation", overflow="fold")
    for alert in entries:
        state_style = "yellow" if alert.state == AlertState.ACTIVE else "dim"
        table.add_row(
            alert.triggered_at.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
            Text(alert.state.value, style=state_style),
            alert.severity.value,
            alert.message,
        )
    console.print(table)


@app.command("tree")
def process_tree(
    limit: Annotated[int, typer.Option(min=1, max=1000)] = 200,
) -> None:
    """Show an on-demand snapshot of process parent relationships."""
    rows = asyncio.run(ProcessTreeService().read())
    table = Table(title=f"Process tree ({min(len(rows), limit)} shown)", box=box.SIMPLE)
    table.add_column("PID", justify="right")
    table.add_column("Process", overflow="ellipsis")
    for row in rows[:limit]:
        table.add_row(str(row.entry.pid), "  " * min(row.depth, 20) + row.entry.name)
    console.print(table)


@app.command()
def report(
    format: Annotated[
        ReportFormat, typer.Option(help="Export format.")
    ] = ReportFormat.MARKDOWN,
    output: Annotated[
        Path | None,
        typer.Option(help="Destination file; defaults to user data reports directory."),
    ] = None,
) -> None:
    """Export one local observed snapshot as a static file."""
    snapshot = _sample()
    try:
        destination = write_report(build_report(snapshot), format, output)
    except (OSError, ValueError) as error:
        typer.echo(f"Report could not be written: {error}", err=True)
        raise typer.Exit(code=1) from error
    console.print(f"Export completed: {destination}")


@app.command()
def plugins() -> None:
    """List installed collector entry points without executing them."""
    installed = discover_plugins()
    enabled = set(load_settings().settings.enabled_plugins)
    if not installed:
        console.print("No collector plugins installed.")
        return
    table = Table(title="Collector plugins", box=box.SIMPLE)
    table.add_column("Name")
    table.add_column("State")
    table.add_column("Entry point")
    for entry in installed:
        table.add_row(
            entry.name,
            "enabled" if entry.name in enabled else "disabled",
            entry.value,
        )
    console.print(table)


def main() -> None:
    """Run the SystemPulse command-line application."""
    app()
