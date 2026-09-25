"""Keyboard-driven process search and sorting over typed snapshots."""

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DataTable, Input, Static

from systempulse.domain.processes import ProcessMetrics, ProcessSnapshot
from systempulse.presentation import format_bytes, format_percent
from systempulse.services.process_query import (
    ProcessQuery,
    ProcessSort,
    query_processes,
)


class ProcessExplorer(Widget):
    """An interactive table that receives process snapshots from the app."""

    class Selected(Message):
        """A process row was opened by keyboard or mouse."""

        def __init__(self, process: ProcessMetrics) -> None:
            super().__init__()
            self.process = process

    def __init__(self, *, id: str | None = None) -> None:
        super().__init__(id=id)
        self.sort = ProcessSort.CPU
        self._snapshot: ProcessSnapshot | None = None
        self._visible: tuple[ProcessMetrics, ...] = ()
        self._keys: tuple[str, ...] = ()

    def compose(self) -> ComposeResult:
        yield Static("PROCESSES  ·  SORT CPU", id="process-explorer-heading")
        yield Input(placeholder="Search process name", id="process-search")
        yield DataTable(id="process-table", cursor_type="row", zebra_stripes=True)
        yield Static(
            "/ Search  ·  c CPU  ·  m Memory  ·  p PID  ·  Enter Details",
            id="process-explorer-hint",
        )

    def on_mount(self) -> None:
        self.query_one("#process-table", DataTable).add_columns(
            "PID", "PROCESS", "CPU", "MEMORY", "USER", "THREADS"
        )

    def update_snapshot(self, snapshot: ProcessSnapshot | None) -> None:
        """Refresh rows only when the process collector produced a new scan."""
        if snapshot is self._snapshot:
            return
        self._snapshot = snapshot
        self._update_rows()

    def set_sort(self, sort: ProcessSort) -> None:
        self.sort = sort
        self.query_one("#process-explorer-heading", Static).update(
            f"PROCESSES  ·  SORT {sort.value.upper()}"
        )
        self._update_rows()

    def focus_search(self) -> None:
        self.query_one("#process-search", Input).focus()

    def focus_table(self) -> None:
        self.query_one("#process-table", DataTable).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "process-search":
            self._update_rows()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "process-search":
            self.focus_table()

    def on_key(self, event: events.Key) -> None:
        """Handle table shortcuts while leaving text entry to the Input widget."""
        if isinstance(self.app.focused, Input):
            if event.key == "escape":
                self.focus_table()
                event.stop()
            return
        sort_keys = {
            "c": ProcessSort.CPU,
            "m": ProcessSort.MEMORY,
            "p": ProcessSort.PID,
        }
        if event.key in sort_keys:
            self.set_sort(sort_keys[event.key])
            event.stop()
        elif event.key in ("/", "slash"):
            self.focus_search()
            event.stop()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id != "process-table":
            return
        if 0 <= event.cursor_row < len(self._visible):
            self.post_message(self.Selected(self._visible[event.cursor_row]))

    def _update_rows(self) -> None:
        table = self.query_one("#process-table", DataTable)
        old_row = table.cursor_row
        old_key = self._keys[old_row] if 0 <= old_row < len(self._keys) else None
        search = self.query_one("#process-search", Input).value
        self._visible = (
            query_processes(
                self._snapshot.processes, ProcessQuery(sort=self.sort, search=search)
            )
            if self._snapshot is not None
            else ()
        )
        table.clear()
        keys: list[str] = []
        for process in self._visible:
            key = (
                f"{process.pid}:{process.identity.created_at.isoformat()}"
                if process.identity is not None
                else f"{process.pid}:unknown"
            )
            keys.append(key)
            table.add_row(
                str(process.pid),
                Text(process.name or "Unknown"),
                format_percent(process.cpu_percent),
                format_bytes(process.memory_rss_bytes),
                Text(process.user or "Unavailable"),
                str(process.threads) if process.threads is not None else "Unavailable",
                key=key,
            )
        self._keys = tuple(keys)
        if keys:
            row = (
                keys.index(old_key) if old_key in keys else min(old_row, len(keys) - 1)
            )
            table.move_cursor(row=row, scroll=False)
        count = len(self._visible)
        text = (
            f"{count} matching processes"
            if self._snapshot is not None
            else "Process metrics unavailable"
        )
        self.query_one("#process-explorer-hint", Static).update(
            f"{text}  ·  / Search  ·  c CPU  ·  m Memory  ·  p PID  ·  Enter Details"
        )
