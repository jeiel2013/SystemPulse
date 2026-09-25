"""Non-interactive local monitoring commands."""

import asyncio
import sys
from enum import StrEnum
from typing import Annotated

import typer
from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from systempulse.domain.availability import Availability
from systempulse.domain.processes import ProcessMetrics
from systempulse.domain.snapshots import SystemSnapshot
from systempulse.presentation import format_bytes, format_percent
from systempulse.services.monitor import create_default_session
from systempulse.version import get_version

app = typer.Typer(
    add_completion=False,
    help="Local system monitoring and diagnostics for your terminal.",
)
console = Console()


class ProcessSort(StrEnum):
    """Supported sort keys for the one-shot process listing."""

    CPU = "cpu"
    MEMORY = "memory"
    PID = "pid"


def _sample() -> SystemSnapshot:
    """Observe two cycles to calculate nonblocking CPU rates."""
    return asyncio.run(create_default_session().sample_after_warmup())


def _sorted_processes(
    processes: tuple[ProcessMetrics, ...], sort: ProcessSort
) -> list[ProcessMetrics]:
    if sort == ProcessSort.PID:
        return sorted(processes, key=lambda process: process.pid)
    if sort == ProcessSort.MEMORY:
        return sorted(
            processes,
            key=lambda process: (
                process.memory_rss_bytes is None,
                -(process.memory_rss_bytes or 0),
                process.pid,
            ),
        )
    return sorted(
        processes,
        key=lambda process: (
            process.cpu_percent is None,
            -(process.cpu_percent or 0),
            process.pid,
        ),
    )


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
    """Show a current CPU, memory, and process summary."""
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
    process_snapshot = snapshot.processes
    if process_snapshot and process_snapshot.processes:
        top_cpu = next(
            (
                process
                for process in _sorted_processes(
                    process_snapshot.processes, ProcessSort.CPU
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
                for process in _sorted_processes(
                    process_snapshot.processes, ProcessSort.MEMORY
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

    rows = process_snapshot.processes
    if search:
        needle = search.casefold()
        rows = tuple(row for row in rows if needle in (row.name or "").casefold())
    sorted_rows = _sorted_processes(rows, sort)[:limit]
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


def main() -> None:
    """Run the SystemPulse command-line application."""
    app()
