"""A live terminal overview driven only by application snapshots."""

import asyncio
from contextlib import suppress
from datetime import UTC, datetime
from time import monotonic
from typing import ClassVar

import psutil
from rich.table import Table
from rich.text import Text
from sqlalchemy.exc import SQLAlchemyError
from textual import events, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.widgets import DataTable, Footer, Header, Static

from systempulse.domain.analysis import Alert, AlertState
from systempulse.domain.availability import Availability
from systempulse.domain.processes import ProcessMetrics
from systempulse.domain.snapshots import SystemSnapshot
from systempulse.history.ranges import HistoryRange
from systempulse.history.store import HistoryPoint
from systempulse.presentation import (
    format_bytes,
    format_percent,
    format_rate,
    format_remaining_time,
    format_temperature,
    format_uptime,
)
from systempulse.reports.export import ReportFormat, build_report, write_report
from systempulse.services.monitor import MonitorSession, create_default_session
from systempulse.services.process_details import ProcessDetailsService
from systempulse.services.process_query import (
    ProcessQuery,
    ProcessSort,
    query_processes,
)
from systempulse.services.process_tree import ProcessTreeRow, ProcessTreeService
from systempulse.tui.process_details import ProcessDetailsScreen
from systempulse.tui.process_explorer import ProcessExplorer
from systempulse.tui.themes import PULSE_DARK, PULSE_LIGHT, themes_for_color_system

_SPARK = "▁▂▃▄▅▆▇█"


def cpu_sparkline(values: tuple[float | None, ...]) -> str:
    """Render observed CPU percentages without filling in unavailable samples."""
    return "".join(
        "·" if value is None else _SPARK[min(7, max(0, int(value * 8 / 100)))]
        for value in values
    )


def history_sparkline(points: tuple[HistoryPoint, ...]) -> str:
    """Fit observed CPU history into a terminal-width sparkline."""
    if len(points) > 60:
        indexes = (round(index * (len(points) - 1) / 59) for index in range(60))
        values = tuple(points[index].cpu_percent for index in indexes)
    else:
        values = tuple(point.cpu_percent for point in points)
    return cpu_sparkline(values)


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
        ("4", "history", "History"),
        ("5", "alerts", "Alerts"),
        ("6", "tree", "Tree"),
        ("h", "history_range", "Range"),
        ("d", "dismiss_alert", "Dismiss"),
        ("e", "export_report", "Export"),
        ("t", "toggle_theme", "Theme"),
    ]

    def __init__(
        self,
        session: MonitorSession | None = None,
        details_service: ProcessDetailsService | None = None,
        tree_service: ProcessTreeService | None = None,
    ) -> None:
        super().__init__()
        self.session = session or create_default_session()
        self.details_service = details_service or ProcessDetailsService()
        self.tree_service = tree_service or ProcessTreeService()
        self._refresh_requested = asyncio.Event()
        self._history_range = HistoryRange.TEN_MINUTES
        self._history_last = 0.0
        self._visible_alerts: tuple[Alert, ...] = ()
        self._tree_rows: tuple[ProcessTreeRow, ...] = ()

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
                yield Static(
                    "GPU\nChecking provider", id="gpu-card", classes="metric-card"
                )
            with Container(id="io-summary"):
                yield Static(
                    "HOME DISK\nWaiting for sample",
                    id="disk-card",
                    classes="metric-card",
                )
                yield Static(
                    "NETWORK\nWaiting for sample",
                    id="network-card",
                    classes="metric-card",
                )
            yield Static("CPU ACTIVITY\nWaiting for samples", id="cpu-history")
            yield Static("TOP CPU PROCESSES", id="process-heading")
            yield DataTable(id="top-processes", cursor_type="none", zebra_stripes=True)
            yield Static("TOP MEMORY PROCESSES", id="memory-process-heading")
            yield DataTable(
                id="top-memory-processes", cursor_type="none", zebra_stripes=True
            )
            yield Static("SYSTEM ANALYSIS\nWaiting for samples", id="analysis-panel")
            yield Static("Checking collectors…", id="collector-line")
        yield ProcessExplorer(id="process-explorer")
        with VerticalScroll(id="system-view"):
            yield Static("SYSTEM  ·  LOCAL HOST", id="system-heading")
            yield Static("Waiting for system facts", id="host-facts")
            yield Static("Waiting for hardware metrics", id="hardware-facts")
            yield Static("Checking GPU provider", id="gpu-facts")
            yield Static("Checking battery", id="battery-facts")
            yield Static("Checking sensors", id="sensor-facts")
        with VerticalScroll(id="history-view"):
            yield Static("HISTORY · LOCAL METRICS", id="history-heading")
            yield Static("Loading local history", id="history-chart")
            yield Static("Press h to change range", id="history-hint")
        with VerticalScroll(id="alerts-view"):
            yield Static("ALERTS · OBSERVED THRESHOLDS", id="alerts-heading")
            yield DataTable(id="alert-table", cursor_type="row", zebra_stripes=True)
            yield Static(
                "No alerts recorded. Press d to dismiss a selected active alert.",
                id="alerts-hint",
            )
        with VerticalScroll(id="tree-view"):
            yield Static("PROCESS TREE · ON-DEMAND SCAN", id="tree-heading")
            yield DataTable(id="tree-table", cursor_type="row", zebra_stripes=True)
            yield Static("Enter opens details · r rescans", id="tree-hint")
        yield Footer()

    def on_mount(self) -> None:
        for theme in themes_for_color_system(self.console.color_system):
            self.register_theme(theme)
        self.theme = PULSE_DARK.name
        table = self.query_one("#top-processes", DataTable)
        table.add_columns("PID", "PROCESS", "CPU", "MEMORY")
        self.query_one("#top-memory-processes", DataTable).add_columns(
            "PID", "PROCESS", "MEMORY", "CPU"
        )
        self.query_one("#alert-table", DataTable).add_columns(
            "WHEN", "STATE", "SEVERITY", "OBSERVATION"
        )
        self.query_one("#tree-table", DataTable).add_columns("PID", "PROCESS")
        self.query_one("#body", VerticalScroll).focus()
        self._collect_loop()

    async def on_unmount(self) -> None:
        if isinstance(self.session, MonitorSession):
            await self.session.close()

    def on_resize(self, event: events.Resize) -> None:
        self.set_class(event.size.width < 70, "compact")
        self.set_class(event.size.height < 30, "short")

    def action_refresh(self) -> None:
        """Request an immediate full collection cycle."""
        self._refresh_requested.set()
        self.query_one("#status-line", Static).update("LOCAL MONITORING  ·  Refreshing")
        if self.has_class("show-tree"):
            self._load_tree()

    def action_overview(self) -> None:
        """Return to the live system summary."""
        self.remove_class("show-processes")
        self.remove_class("show-system")
        self.remove_class("show-history")
        self.remove_class("show-alerts")
        self.remove_class("show-tree")
        self.query_one("#body", VerticalScroll).focus()

    def action_processes(self) -> None:
        """Open the keyboard-driven process explorer."""
        self.add_class("show-processes")
        self.remove_class("show-system")
        self.remove_class("show-history")
        self.remove_class("show-alerts")
        self.remove_class("show-tree")
        self.query_one(ProcessExplorer).focus_table()

    def action_system(self) -> None:
        """Open observed host and hardware information."""
        self.remove_class("show-processes")
        self.add_class("show-system")
        self.remove_class("show-history")
        self.remove_class("show-alerts")
        self.remove_class("show-tree")

    def action_history(self) -> None:
        """Open the local metric timeline."""
        self.remove_class("show-processes")
        self.remove_class("show-system")
        self.add_class("show-history")
        self.remove_class("show-alerts")
        self.remove_class("show-tree")
        self.query_one("#history-view", VerticalScroll).focus()
        self._load_history()

    def action_alerts(self) -> None:
        """Open the locally observed alert lifecycle."""
        self.remove_class("show-processes")
        self.remove_class("show-system")
        self.remove_class("show-history")
        self.add_class("show-alerts")
        self.remove_class("show-tree")
        self.query_one("#alert-table", DataTable).focus()

    def action_tree(self) -> None:
        """Scan parent relationships only when this view is opened."""
        self.remove_class("show-processes")
        self.remove_class("show-system")
        self.remove_class("show-history")
        self.remove_class("show-alerts")
        self.add_class("show-tree")
        self.query_one("#tree-table", DataTable).focus()
        self._load_tree()

    @work(exclusive=True, group="process-tree")
    async def _load_tree(self) -> None:
        try:
            rows = await self.tree_service.read()
        except (OSError, psutil.Error) as error:
            self.query_one("#tree-hint", Static).update(
                f"Process tree unavailable ({type(error).__name__})."
            )
            return
        if not self.has_class("show-tree"):
            return
        self._tree_rows = rows
        table = self.query_one("#tree-table", DataTable)
        table.clear()
        for row in rows:
            table.add_row(
                str(row.entry.pid),
                "  " * min(row.depth, 20) + row.entry.name,
            )
        self.query_one("#tree-hint", Static).update(
            f"{len(rows)} processes · Enter details · r rescan"
        )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id != "tree-table":
            return
        if not 0 <= event.cursor_row < len(self._tree_rows):
            return
        entry = self._tree_rows[event.cursor_row].entry
        process = ProcessMetrics(
            sampled_at=datetime.now(UTC),
            pid=entry.pid,
            identity=entry.identity,
            name=entry.name,
            cpu_percent=None,
            memory_rss_bytes=None,
            status=None,
            user=None,
            threads=None,
            parent_pid=entry.parent_pid,
        )
        self.push_screen(ProcessDetailsScreen(process, self.details_service))

    async def action_dismiss_alert(self) -> None:
        """Dismiss only a selected active alert, leaving its rule in place."""
        if not self.has_class("show-alerts") or not isinstance(
            self.session, MonitorSession
        ):
            return
        table = self.query_one("#alert-table", DataTable)
        index = table.cursor_row
        if 0 <= index < len(self._visible_alerts):
            alert = self._visible_alerts[index]
            if alert.state == AlertState.ACTIVE:
                await self.session.dismiss_alert(alert.rule_id)
                self._render_alerts()
                self.notify("Alert dismissed", timeout=2)

    async def action_export_report(self) -> None:
        """Write a local Markdown report of the latest observed snapshot."""
        snapshot = self.session.state.current_snapshot
        if snapshot is None:
            self.notify("Waiting for the first sample", timeout=3)
            return
        try:
            destination = await asyncio.to_thread(
                write_report, build_report(snapshot), ReportFormat.MARKDOWN
            )
        except (OSError, ValueError) as error:
            self.notify(f"Report failed: {type(error).__name__}", severity="error")
            return
        self.notify(f"Export completed: {destination}", timeout=5)

    def action_history_range(self) -> None:
        """Cycle through supported history windows in the history view."""
        if not self.has_class("show-history"):
            return
        ranges = tuple(HistoryRange)
        index = ranges.index(self._history_range)
        self._history_range = ranges[(index + 1) % len(ranges)]
        self._load_history()

    def action_toggle_theme(self) -> None:
        """Switch the active Textual palette and all theme-backed panel colors."""
        self.theme = (
            PULSE_LIGHT.name if self.theme == PULSE_DARK.name else PULSE_DARK.name
        )
        label = "Light" if self.theme == PULSE_LIGHT.name else "Dark"
        self.notify(f"{label} theme active", timeout=2)

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
            if not isinstance(self.screen, ProcessDetailsScreen):
                self._render_snapshot(snapshot)
            if self.has_class("show-history") and monotonic() - self._history_last >= 5:
                self._load_history()
            remaining = max(0.0, 1.0 - (monotonic() - started_at))
            with suppress(TimeoutError):
                await asyncio.wait_for(
                    self._refresh_requested.wait(), timeout=remaining
                )

    @work(exclusive=True, group="history")
    async def _load_history(self) -> None:
        """Read SQLite outside the UI loop and render only the active history view."""
        self._history_last = monotonic()
        store = (
            self.session.history_store
            if isinstance(self.session, MonitorSession)
            else None
        )
        if store is None:
            self.query_one("#history-chart", Static).update("No historical data yet.")
            return
        try:
            points = await asyncio.to_thread(store.query, self._history_range.duration)
        except (OSError, SQLAlchemyError) as error:
            self.query_one("#history-chart", Static).update(
                f"History unavailable ({type(error).__name__})."
            )
            return
        if not self.has_class("show-history"):
            return
        if not points:
            content = (
                "No historical data yet. Keep SystemPulse running to collect samples."
            )
        else:
            latest = points[-1]
            content = (
                f"CPU · {history_sparkline(points)}\n"
                f"Latest CPU {format_percent(latest.cpu_percent)} · "
                f"RAM {format_percent(latest.memory_percent)} · "
                f"Disk {format_percent(latest.disk_percent)}\n"
                f"Network ↓ {format_rate(latest.download_bytes_per_second)} · "
                f"↑ {format_rate(latest.upload_bytes_per_second)}\n"
                f"{len(points)} observed points"
            )
        self.query_one("#history-chart", Static).update(content)
        self.query_one("#history-hint", Static).update(
            f"Range {self._history_range.value} · Press h for next range"
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
        disk = snapshot.metrics.disk
        network = snapshot.metrics.network
        self.query_one("#disk-card", Static).update(
            "HOME DISK\n"
            + (
                f"{format_percent(disk.percent)} used · "
                f"{format_bytes(disk.free_bytes)} free"
                if disk
                else "Unavailable"
            )
            + (
                f"\nRead {format_rate(disk.read_bytes_per_second)} · "
                f"Write {format_rate(disk.write_bytes_per_second)}"
                if disk
                else ""
            )
        )
        self.query_one("#network-card", Static).update(
            "NETWORK\n"
            + (
                f"↓ {format_rate(network.download_bytes_per_second)} · "
                f"↑ {format_rate(network.upload_bytes_per_second)}"
                if network
                else "Unavailable"
            )
            + (f"\n{len(network.interfaces)} interfaces" if network else "")
        )
        gpu = snapshot.gpu.devices[0] if snapshot.gpu is not None else None
        if gpu is None:
            status = next(
                (item for item in snapshot.collector_statuses if item.name == "gpu"),
                None,
            )
            label = (
                status.availability.value.replace("_", " ").title()
                if status is not None
                else "Checking provider"
            )
            self.query_one("#gpu-card", Static).update(f"GPU\n{label}")
        else:
            self.query_one("#gpu-card", Static).update(
                f"GPU {gpu.index}\n"
                f"{format_percent(gpu.utilization_percent)} load\n"
                f"VRAM {format_bytes(gpu.vram_used_bytes)} used\n"
                f"Temp {format_temperature(gpu.temperature_celsius)}"
            )
        history = tuple(
            sample.cpu_percent for sample in self.session.state.recent_samples
        )
        history_text = cpu_sparkline(history) if history else "Waiting for samples"
        self.query_one("#cpu-history", Static).update(f"CPU ACTIVITY\n{history_text}")

        table = self.query_one("#top-processes", DataTable)
        table.clear()
        memory_table = self.query_one("#top-memory-processes", DataTable)
        memory_table.clear()
        process_snapshot = snapshot.processes
        self.query_one(ProcessExplorer).update_snapshot(process_snapshot)
        if process_snapshot is not None:
            visible = tuple(
                process for process in process_snapshot.processes if process.pid != 0
            )
            for process in query_processes(
                visible, ProcessQuery(sort=ProcessSort.CPU, limit=10)
            ):
                table.add_row(
                    str(process.pid),
                    Text(process.name or "Unknown"),
                    format_percent(process.cpu_percent),
                    format_bytes(process.memory_rss_bytes),
                )
            for process in query_processes(
                visible, ProcessQuery(sort=ProcessSort.MEMORY, limit=10)
            ):
                memory_table.add_row(
                    str(process.pid),
                    Text(process.name or "Unknown"),
                    format_bytes(process.memory_rss_bytes),
                    format_percent(process.cpu_percent),
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
        if isinstance(self.session, MonitorSession):
            failures = tuple(
                result.name
                for result in self.session.plugin_results
                if not result.loaded
            )
            if failures:
                status_text += " · Plugins unavailable: " + ", ".join(failures)
            if self.session.history_error:
                status_text += f" · History {self.session.history_error}"
        self.query_one("#collector-line", Static).update(status_text)
        self._render_system(snapshot)
        self._render_analysis(snapshot)
        self._render_alerts()

    def _render_analysis(self, snapshot: SystemSnapshot) -> None:
        """Present measurements and rule-backed observations without causes."""
        cpu = snapshot.metrics.cpu
        memory = snapshot.metrics.memory
        disk = snapshot.metrics.disk
        active = self.session.state.active_alerts
        lines = [
            "SYSTEM ANALYSIS",
            f"CPU {format_percent(cpu.total_percent if cpu else None)} · "
            f"RAM {format_percent(memory.percent if memory else None)} · "
            f"Disk {format_percent(disk.percent if disk else None)}",
            f"{len(active)} active alerts",
        ]
        lines.extend(item.message for item in self.session.state.observations[-3:])
        self.query_one("#analysis-panel", Static).update("\n".join(lines))

    def _render_alerts(self) -> None:
        entries = tuple(reversed(self.session.state.alerts))
        if entries == self._visible_alerts:
            return
        self._visible_alerts = entries
        table = self.query_one("#alert-table", DataTable)
        table.clear()
        for alert in entries:
            table.add_row(
                alert.triggered_at.astimezone().strftime("%H:%M:%S"),
                alert.state.value,
                alert.severity.value,
                alert.message,
            )
        self.query_one("#alerts-hint", Static).update(
            f"{len(entries)} recorded alerts · d dismisses the selected active alert"
            if entries
            else "No alerts recorded."
        )

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
        self._render_gpu(snapshot)
        battery = snapshot.battery
        if battery is None:
            self.query_one("#battery-facts", Static).update("Battery unavailable.")
        else:
            power = "Plugged in" if battery.power_plugged else "On battery"
            self.query_one("#battery-facts", Static).update(
                f"BATTERY\n{format_percent(battery.percent)} · {power}\n"
                f"Remaining {format_remaining_time(battery.seconds_left)}"
            )
        sensors = snapshot.sensors
        if sensors is None:
            self.query_one("#sensor-facts", Static).update(
                "Sensor readings unavailable."
            )
        else:
            readings = ["SENSORS"]
            readings.extend(
                f"{item.group} · {item.label}: {item.value:.0f} {item.unit}"
                for item in sensors.readings[:20]
            )
            self.query_one("#sensor-facts", Static).update("\n".join(readings))

    def _render_gpu(self, snapshot: SystemSnapshot) -> None:
        """Show each measured GPU or the actual provider state."""
        if snapshot.gpu is None:
            status = next(
                (item for item in snapshot.collector_statuses if item.name == "gpu"),
                None,
            )
            if status is None:
                message = "Waiting for GPU provider"
            elif status.availability == Availability.UNAVAILABLE:
                message = (
                    "GPU metrics unavailable. Supported: nvidia-smi, rocm-smi, xpu-smi."
                )
            else:
                message = f"GPU metrics {status.availability.value}"
                if status.reason:
                    message += f" ({status.reason})"
            self.query_one("#gpu-facts", Static).update(message)
            return

        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold")
        table.add_column(overflow="fold")
        for gpu in snapshot.gpu.devices:
            table.add_row(f"GPU {gpu.index}", gpu.name)
            table.add_row("Load", format_percent(gpu.utilization_percent))
            table.add_row(
                "VRAM",
                f"{format_bytes(gpu.vram_used_bytes)} / "
                f"{format_bytes(gpu.vram_total_bytes)}",
            )
            table.add_row("Temperature", format_temperature(gpu.temperature_celsius))
            table.add_row("Source", gpu.source)
        self.query_one("#gpu-facts", Static).update(table)
