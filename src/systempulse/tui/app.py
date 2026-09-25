"""A live terminal overview driven only by application snapshots."""

import asyncio
from contextlib import suppress
from time import monotonic
from typing import ClassVar

from rich.table import Table
from rich.text import Text
from textual import events, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.widgets import DataTable, Footer, Header, Static

from systempulse.domain.availability import Availability
from systempulse.domain.snapshots import SystemSnapshot
from systempulse.presentation import format_bytes, format_percent, format_uptime
from systempulse.services.monitor import MonitorSession, create_default_session
from systempulse.services.process_details import ProcessDetailsService
from systempulse.tui.process_details import ProcessDetailsScreen
from systempulse.tui.process_explorer import ProcessExplorer

_SPARK = "▁▂▃▄▅▆▇█"


def cpu_sparkline(values: tuple[float | None, ...]) -> str:
    """Render observed CPU percentages without filling in unavailable samples."""
    return "".join(
        "·" if value is None else _SPARK[min(7, max(0, int(value * 8 / 100)))]
        for value in values
    )


class PulseApp(App[None]):
    """Show current health, recent CPU activity, and leading processes."""

    CSS_PATH = "styles.tcss"
    TITLE = "SystemPulse"
    SUB_TITLE = "Measure · Understand · Inform"
    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("1", "overview", "Overview"),
        ("2", "processes", "Processes"),
        ("3", "system", "System"),
    ]

    def __init__(
        self,
        session: MonitorSession | None = None,
        details_service: ProcessDetailsService | None = None,
    ) -> None:
        super().__init__()
        self.session = session or create_default_session()
        self.details_service = details_service or ProcessDetailsService()
        self._refresh_requested = asyncio.Event()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll(id="body"):
            yield Static(
                "LOCAL MONITORING  ·  Waiting for first sample", id="status-line"
            )
            with Container(id="summary"):
                yield Static(
                    "CPU\nWaiting for sample", id="cpu-card", classes="metric-card"
                )
                yield Static(
                    "MEMORY\nWaiting for sample",
                    id="memory-card",
                    classes="metric-card",
                )
            yield Static("CPU ACTIVITY\nWaiting for samples", id="cpu-history")
            yield Static("TOP CPU PROCESSES", id="process-heading")
            yield DataTable(id="top-processes", cursor_type="none", zebra_stripes=True)
            yield Static("Checking collectors…", id="collector-line")
        yield ProcessExplorer(id="process-explorer")
        with VerticalScroll(id="system-view"):
            yield Static("SYSTEM  ·  LOCAL HOST", id="system-heading")
            yield Static("Waiting for system facts", id="host-facts")
            yield Static("Waiting for hardware metrics", id="hardware-facts")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#top-processes", DataTable)
        table.add_columns("PID", "PROCESS", "CPU", "MEMORY")
        self._collect_loop()

    def on_resize(self, event: events.Resize) -> None:
        self.set_class(event.size.width < 70, "compact")
        self.set_class(event.size.height < 30, "short")

    def action_refresh(self) -> None:
        """Request an immediate full collection cycle."""
        self._refresh_requested.set()
        self.query_one("#status-line", Static).update("LOCAL MONITORING  ·  Refreshing")

    def action_overview(self) -> None:
        """Return to the live system summary."""
        self.remove_class("show-processes")
        self.remove_class("show-system")

    def action_processes(self) -> None:
        """Open the keyboard-driven process explorer."""
        self.add_class("show-processes")
        self.remove_class("show-system")
        self.query_one(ProcessExplorer).focus_table()

    def action_system(self) -> None:
        """Open observed host and hardware information."""
        self.remove_class("show-processes")
        self.add_class("show-system")

    def on_process_explorer_selected(self, event: ProcessExplorer.Selected) -> None:
        self.session.state.selected_process = event.process.identity
        self.push_screen(ProcessDetailsScreen(event.process, self.details_service))

    @work
    async def _collect_loop(self) -> None:
        """Keep psutil work off the UI loop and avoid overlapping scans."""
        while True:
            started_at = monotonic()
            if self._refresh_requested.is_set():
                self._refresh_requested.clear()
                snapshot = await self.session.sample()
            else:
                snapshot = await self.session.sample_due()
            self._render_snapshot(snapshot)
            remaining = max(0.0, 1.0 - (monotonic() - started_at))
            with suppress(TimeoutError):
                await asyncio.wait_for(
                    self._refresh_requested.wait(), timeout=remaining
                )

    def _render_snapshot(self, snapshot: SystemSnapshot) -> None:
        cpu = snapshot.metrics.cpu
        memory = snapshot.metrics.memory
        self.query_one("#cpu-card", Static).update(
            f"CPU\n{format_percent(cpu.total_percent if cpu else None)}"
            + (
                f"\n{cpu.logical_cores} logical cores"
                if cpu and cpu.logical_cores
                else ""
            )
        )
        self.query_one("#memory-card", Static).update(
            f"MEMORY\n{format_percent(memory.percent if memory else None)}"
            + (f"\n{format_bytes(memory.available_bytes)} available" if memory else "")
        )
        history = tuple(
            sample.metrics.cpu.total_percent if sample.metrics.cpu else None
            for sample in self.session.state.recent_snapshots
        )
        history_text = cpu_sparkline(history) if history else "Waiting for samples"
        self.query_one("#cpu-history", Static).update(f"CPU ACTIVITY\n{history_text}")

        table = self.query_one("#top-processes", DataTable)
        table.clear()
        process_snapshot = snapshot.processes
        self.query_one(ProcessExplorer).update_snapshot(process_snapshot)
        if process_snapshot is not None:
            leaders = sorted(
                (process for process in process_snapshot.processes if process.pid != 0),
                key=lambda process: (
                    process.cpu_percent is None,
                    -(process.cpu_percent or 0),
                    process.pid,
                ),
            )[:10]
            for process in leaders:
                table.add_row(
                    str(process.pid),
                    Text(process.name or "Unknown"),
                    format_percent(process.cpu_percent),
                    format_bytes(process.memory_rss_bytes),
                )
        observed_at = snapshot.created_at.astimezone().strftime("%H:%M:%S")
        count = len(process_snapshot.processes) if process_snapshot else 0
        self.query_one("#status-line", Static).update(
            f"LOCAL MONITORING  ·  {count} processes  ·  Snapshot {observed_at}"
        )
        waiting_or_unavailable = tuple(
            status
            for status in snapshot.collector_statuses
            if status.availability != Availability.AVAILABLE
        )
        status_text = (
            "All collectors available"
            if not waiting_or_unavailable
            else "Collectors: "
            + ", ".join(
                f"{status.name} {status.availability.value}"
                for status in waiting_or_unavailable
            )
        )
        self.query_one("#collector-line", Static).update(status_text)
        self._render_system(snapshot)

    def _render_system(self, snapshot: SystemSnapshot) -> None:
        """Present stable host facts separately from faster changing metrics."""
        system = snapshot.system
        if system is None:
            self.query_one("#host-facts", Static).update(
                "System information unavailable. Check collector status on Overview."
            )
        else:
            host = Table.grid(padding=(0, 2))
            host.add_column(style="bold")
            host.add_column(overflow="fold")
            host.add_row("Operating system", system.platform_name)
            host.add_row("Release", system.platform_release or "Unavailable")
            host.add_row("Architecture", system.architecture or "Unavailable")
            host.add_row("Hostname", system.hostname or "Unavailable")
            started = (
                system.boot_time.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
                if system.boot_time is not None
                else "Unavailable"
            )
            host.add_row("Started", started)
            host.add_row("Uptime", format_uptime(system.boot_time, snapshot.created_at))
            self.query_one("#host-facts", Static).update(host)

        hardware = Table.grid(padding=(0, 2))
        hardware.add_column(style="bold")
        hardware.add_column()
        cpu = snapshot.metrics.cpu
        memory = snapshot.metrics.memory
        hardware.add_row(
            "Physical cores",
            str(cpu.physical_cores) if cpu and cpu.physical_cores else "Unavailable",
        )
        hardware.add_row(
            "Logical cores",
            str(cpu.logical_cores) if cpu and cpu.logical_cores else "Unavailable",
        )
        hardware.add_row(
            "CPU frequency",
            f"{cpu.frequency_mhz / 1000:.2f} GHz"
            if cpu and cpu.frequency_mhz is not None
            else "Unavailable",
        )
        hardware.add_row(
            "Total memory", format_bytes(memory.total_bytes if memory else None)
        )
        hardware.add_row(
            "Swap / pagefile",
            format_bytes(memory.swap_total_bytes if memory else None),
        )
        self.query_one("#hardware-facts", Static).update(hardware)
