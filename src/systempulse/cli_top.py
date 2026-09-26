"""A compact continuous process monitor rendered with Rich."""

import asyncio
from time import monotonic

from rich import box
from rich.console import Console, Group, RenderableType
from rich.live import Live
from rich.table import Table
from rich.text import Text

from systempulse.domain.snapshots import SystemSnapshot
from systempulse.platform.keyboard import quit_key_reader
from systempulse.presentation import format_bytes, format_percent
from systempulse.services.monitor import MonitorSession
from systempulse.services.process_query import ProcessQuery, query_processes


def render_top(
    snapshot: SystemSnapshot, query: ProcessQuery, height: int
) -> RenderableType:
    """Show only observed values and fit rows to the current terminal height."""
    cpu = snapshot.metrics.cpu
    memory = snapshot.metrics.memory
    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="bold")
    summary.add_column()
    summary.add_row("CPU", format_percent(cpu.total_percent if cpu else None))
    summary.add_row("Memory", format_percent(memory.percent if memory else None))
    summary.add_row(
        "Available", format_bytes(memory.available_bytes if memory else None)
    )

    process_snapshot = snapshot.processes
    table = Table(box=box.SIMPLE, expand=True)
    table.add_column("PID", justify="right", no_wrap=True)
    table.add_column("Process", overflow="ellipsis", ratio=1)
    table.add_column("CPU", justify="right", no_wrap=True)
    table.add_column("Memory", justify="right", no_wrap=True)
    if process_snapshot is None:
        message = "Process metrics unavailable. Other collectors continue running."
    else:
        limit = min(query.limit or 20, max(1, height - 10))
        rows = query_processes(
            process_snapshot.processes,
            ProcessQuery(sort=query.sort, search=query.search, limit=limit),
        )
        for process in rows:
            table.add_row(
                str(process.pid),
                Text(process.name or "Unknown"),
                format_percent(process.cpu_percent),
                format_bytes(process.memory_rss_bytes),
            )
        message = (
            f"{len(rows)} shown · Process sample "
            f"{process_snapshot.sampled_at.astimezone():%H:%M:%S}"
        )
        if not rows:
            message = "No matching processes."
        if process_snapshot.skipped_count:
            message += f" · {process_snapshot.skipped_count} unreadable"
    return Group(
        Text("SystemPulse top", style="bold cyan"),
        summary,
        table,
        Text(f"{message} · q / Ctrl+C to quit", style="dim"),
    )


async def run_top(
    session: MonitorSession,
    console: Console,
    query: ProcessQuery,
    refresh_interval: float = 1.0,
) -> None:
    """Refresh each second, retaining collector baselines between scans."""
    if refresh_interval <= 0:
        raise ValueError("refresh_interval must be positive")
    with (
        quit_key_reader() as quit_requested,
        Live(
            Text("SystemPulse top · Warming up process rates…"),
            console=console,
            auto_refresh=False,
            transient=True,
        ) as live,
    ):
        await session.sample()
        next_sample = monotonic() + refresh_interval
        while True:
            if quit_requested():
                return
            remaining = next_sample - monotonic()
            if remaining > 0:
                await asyncio.sleep(min(0.1, remaining))
                continue
            snapshot = await session.sample_due()
            live.update(render_top(snapshot, query, console.height), refresh=True)
            next_sample = monotonic() + refresh_interval
