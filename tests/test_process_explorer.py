"""Process table keyboard interactions and selection stability."""

from datetime import UTC, datetime

import pytest
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Input

from systempulse.domain.processes import (
    ProcessIdentity,
    ProcessMetrics,
    ProcessSnapshot,
)
from systempulse.tui.process_explorer import ProcessExplorer


def _process(pid: int, name: str, cpu: float, memory: int) -> ProcessMetrics:
    at = datetime.now(UTC)
    return ProcessMetrics(
        sampled_at=at,
        pid=pid,
        identity=ProcessIdentity(pid, at),
        name=name,
        cpu_percent=cpu,
        memory_rss_bytes=memory,
        status=None,
        user="operator",
        threads=2,
        parent_pid=None,
    )


class ExplorerApp(App[None]):
    def __init__(self) -> None:
        super().__init__()
        self.selected: ProcessMetrics | None = None

    def compose(self) -> ComposeResult:
        yield ProcessExplorer()

    def on_process_explorer_selected(self, event: ProcessExplorer.Selected) -> None:
        self.selected = event.process


@pytest.mark.asyncio
async def test_search_sort_and_selection_with_keyboard() -> None:
    app = ExplorerApp()
    fast = _process(10, "fast", 50.0, 100)
    heavy = _process(20, "Heavy", 5.0, 500)

    async with app.run_test(size=(90, 24)) as pilot:
        explorer = app.query_one(ProcessExplorer)
        table = app.query_one(DataTable)
        explorer.update_snapshot(ProcessSnapshot(datetime.now(UTC), (fast, heavy)))
        explorer.focus_table()
        await pilot.press("m")
        assert explorer.sort.value == "memory"
        assert str(table.get_row_at(0)[1]) == "Heavy"

        await pilot.press("/")
        assert isinstance(app.focused, Input)
        await pilot.press("f", "a", "s", "t")
        assert table.row_count == 1
        assert str(table.get_row_at(0)[1]) == "fast"
        await pilot.press("enter")
        assert app.focused is table
        await pilot.press("enter")
        assert app.selected == fast


@pytest.mark.asyncio
async def test_refresh_keeps_selected_instance_when_order_changes() -> None:
    app = ExplorerApp()
    first = _process(10, "first", 50.0, 100)
    second = _process(20, "second", 5.0, 200)

    async with app.run_test(size=(90, 24)) as pilot:
        explorer = app.query_one(ProcessExplorer)
        table = app.query_one(DataTable)
        explorer.update_snapshot(ProcessSnapshot(datetime.now(UTC), (first, second)))
        explorer.focus_table()
        table.move_cursor(row=1)
        await pilot.pause()

        changed = ProcessMetrics(
            sampled_at=datetime.now(UTC),
            pid=second.pid,
            identity=second.identity,
            name=second.name,
            cpu_percent=80.0,
            memory_rss_bytes=second.memory_rss_bytes,
            status=None,
            user=second.user,
            threads=second.threads,
            parent_pid=None,
        )
        explorer.update_snapshot(ProcessSnapshot(datetime.now(UTC), (first, changed)))

        assert table.cursor_row == 0
        assert str(table.get_row_at(0)[1]) == "second"
