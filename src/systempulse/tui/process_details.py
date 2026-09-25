"""Read-only process detail modal with verified, on-demand facts."""

from typing import ClassVar

from rich.console import Group
from rich.table import Table
from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static

from systempulse.domain.processes import ProcessDetails, ProcessMetrics
from systempulse.presentation import format_bytes, format_percent
from systempulse.services.process_details import ProcessDetailsService


class ProcessDetailsScreen(ModalScreen[None]):
    """Show last observed rates and freshly verified process facts."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Close"),
    ]

    def __init__(
        self, process: ProcessMetrics, details_service: ProcessDetailsService
    ) -> None:
        super().__init__()
        self.process = process
        self.details_service = details_service

    def compose(self) -> ComposeResult:
        with Vertical(id="detail-dialog"):
            yield Static("PROCESS DETAILS", id="detail-heading")
            with VerticalScroll(id="detail-scroll"):
                yield Static("Loading verified details…", id="detail-body")
            yield Static("Esc / q  Close", id="detail-hint")

    def on_mount(self) -> None:
        self._load_details()

    @work
    async def _load_details(self) -> None:
        identity = self.process.identity
        if identity is None:
            self.query_one("#detail-body", Static).update(
                self._last_observation_table(
                    self.process,
                    "Detailed data unavailable: process identity was not readable.",
                )
            )
            return
        try:
            details = await self.details_service.read(identity)
        except Exception as error:
            self.query_one("#detail-body", Static).update(
                f"Detailed data unavailable ({type(error).__name__})."
            )
            return
        if details is None:
            self.query_one("#detail-body", Static).update(
                self._last_observation_table(
                    self.process,
                    "This process ended or its PID was reused after the last scan.",
                )
            )
            return
        self.query_one("#detail-body", Static).update(
            self._details_table(self.process, details)
        )

    @staticmethod
    def _last_observation_table(process: ProcessMetrics, message: str) -> Group:
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold")
        table.add_column(overflow="fold")
        table.add_row("Name", Text(process.name or "Unavailable"))
        table.add_row("PID", str(process.pid))
        table.add_row("CPU (last scan)", format_percent(process.cpu_percent))
        table.add_row("Memory (last scan)", format_bytes(process.memory_rss_bytes))
        table.add_row("User (last scan)", Text(process.user or "Unavailable"))
        sampled_at = process.sampled_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        table.add_row("Last observed", sampled_at)
        return Group(Text(message, style="yellow"), table)

    @staticmethod
    def _details_table(process: ProcessMetrics, details: ProcessDetails) -> Table:
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold")
        table.add_column(overflow="fold")
        table.add_row("Name", Text(details.name or process.name or "Unavailable"))
        table.add_row("PID", str(process.pid))
        table.add_row("Status", Text(details.status or "Unavailable"))
        table.add_row("User", Text(details.user or "Unavailable"))
        table.add_row("CPU (last scan)", format_percent(process.cpu_percent))
        table.add_row("Memory (last scan)", format_bytes(process.memory_rss_bytes))
        threads = str(details.threads) if details.threads is not None else "Unavailable"
        table.add_row("Threads", threads)
        started = details.identity.created_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        table.add_row("Started", started)
        table.add_row("Executable", Text(details.executable or "Unavailable"))
        table.add_row(
            "Parent PID",
            str(details.parent_pid)
            if details.parent_pid is not None
            else "Unavailable",
        )
        command = (
            Text(" ".join(details.command_line))
            if details.command_line is not None
            else Text("Unavailable")
        )
        table.add_row("Command", command)
        observed_at = details.sampled_at.astimezone().strftime("%H:%M:%S")
        table.add_row("Details read", observed_at)
        return table
