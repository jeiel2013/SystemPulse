"""The Textual overview renders snapshots and responds to terminal controls."""

from dataclasses import replace
from datetime import UTC, datetime
from io import StringIO

import pytest
from rich.color import Color, ColorSystem
from rich.console import Console
from textual import constants
from textual.containers import VerticalScroll
from textual.widgets import DataTable, Input, Static

from systempulse.domain.availability import Availability, CollectorStatus
from systempulse.domain.gpu import GpuMetrics, GpuSnapshot
from systempulse.domain.io import DiskMetrics, NetworkMetrics
from systempulse.domain.metrics import CpuMetrics, MemoryMetrics, SystemMetrics
from systempulse.domain.processes import (
    ProcessDetails,
    ProcessIdentity,
    ProcessMetrics,
    ProcessSnapshot,
)
from systempulse.domain.snapshots import MetricSnapshot, SystemSnapshot
from systempulse.services.state import ApplicationState
from systempulse.tui.app import PulseApp, cpu_sparkline
from systempulse.tui.process_details import ProcessDetailsScreen
from systempulse.tui.process_explorer import ProcessExplorer


def _snapshot(*, available: bool = True) -> SystemSnapshot:
    at = datetime.now(UTC)
    cpu = CpuMetrics(at, 42.0, (42.0,), 1, 1, None, None) if available else None
    memory = (
        MemoryMetrics(at, 1024, 512, 512, 50.0, None, None, None) if available else None
    )
    processes = (
        ProcessSnapshot(
            at,
            (
                ProcessMetrics(
                    at,
                    42,
                    ProcessIdentity(42, at),
                    "worker",
                    12.0,
                    1024,
                    None,
                    None,
                    None,
                    None,
                ),
            ),
        )
        if available
        else None
    )
    statuses = (
        CollectorStatus(
            "cpu", Availability.AVAILABLE if available else Availability.ERROR, at
        ),
    )
    system = (
        SystemMetrics(at, "Test OS", "1.0", "test64", "test-host", at)
        if available
        else None
    )
    return SystemSnapshot(
        at,
        MetricSnapshot(
            at,
            cpu,
            memory,
            DiskMetrics(at, "/", 1000, 400, 600, 40.0, 100, 200, 50.0, 20.0),
            NetworkMetrics(at, 1000, 2000, 100.0, 25.0, ()),
        ),
        processes,
        system,
        statuses,
    )


class FakeSession:
    def __init__(self, snapshot: SystemSnapshot) -> None:
        self.state = ApplicationState()
        self.snapshot = snapshot
        self.full_calls = 0

    async def sample_due(self) -> SystemSnapshot:
        self.state.update(self.snapshot)
        return self.snapshot

    async def sample(self) -> SystemSnapshot:
        self.full_calls += 1
        return await self.sample_due()


class FakeDetailsService:
    def __init__(self) -> None:
        self.calls = 0

    async def read(self, identity: ProcessIdentity) -> ProcessDetails:
        self.calls += 1
        return ProcessDetails(
            sampled_at=datetime.now(UTC),
            identity=identity,
            name="worker",
            status="running",
            user="operator",
            threads=2,
            parent_pid=1,
            executable="/usr/bin/worker",
            command_line=("worker", "--run"),
        )


class MissingDetailsService:
    async def read(self, identity: ProcessIdentity) -> None:
        return None


@pytest.mark.asyncio
async def test_overview_renders_and_handles_refresh_resize_and_quit() -> None:
    session = FakeSession(_snapshot())
    app = PulseApp(session=session)

    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.pause()
        assert app.query_one("#top-processes", DataTable).row_count == 1
        assert "42.0%" in str(app.query_one("#cpu-card", Static).render())
        assert "40.0%" in str(app.query_one("#disk-card", Static).render())
        assert "100 B/s" in str(app.query_one("#network-card", Static).render())

        await pilot.press("r")
        await pilot.pause()
        assert session.full_calls >= 1

        await pilot.resize_terminal(80, 25)
        assert app.has_class("short")
        assert app.query_one("#top-processes", DataTable).region.y < 25

        await pilot.resize_terminal(50, 20)
        assert app.has_class("compact")
        cpu_card = app.query_one("#cpu-card", Static)
        memory_card = app.query_one("#memory-card", Static)
        assert memory_card.region.y > cpu_card.region.y
        assert cpu_card.region.width >= 40
        await pilot.press("q")


@pytest.mark.asyncio
async def test_overview_orders_cpu_and_memory_leaders_independently() -> None:
    snapshot = _snapshot()
    assert snapshot.processes is not None
    worker = snapshot.processes.processes[0]
    memory_hog = replace(
        worker,
        pid=43,
        identity=ProcessIdentity(43, worker.sampled_at),
        name="memory-hog",
        cpu_percent=1.0,
        memory_rss_bytes=4096,
    )
    snapshot = replace(
        snapshot,
        processes=ProcessSnapshot(worker.sampled_at, (worker, memory_hog)),
    )
    app = PulseApp(session=FakeSession(snapshot))

    async with app.run_test(size=(90, 28)) as pilot:
        await pilot.pause()
        cpu_table = app.query_one("#top-processes", DataTable)
        memory_table = app.query_one("#top-memory-processes", DataTable)
        assert str(cpu_table.get_row_at(0)[1]) == "worker"
        assert str(memory_table.get_row_at(0)[1]) == "memory-hog"
        assert memory_table.row_count == 2


@pytest.mark.asyncio
async def test_top_memory_remains_reachable_in_short_terminal() -> None:
    app = PulseApp(session=FakeSession(_snapshot()))

    async with app.run_test(size=(80, 20)) as pilot:
        await pilot.pause()
        body = app.query_one("#body", VerticalScroll)
        assert app.focused is body
        assert app.query_one("#top-memory-processes", DataTable).region.y >= 20
        for _ in range(10):
            if body.max_scroll_y > 0:
                break
            await pilot.pause(0.05)
        assert body.max_scroll_y > 0
        await pilot.press("pagedown")
        assert body.scroll_target_y > 0


@pytest.mark.asyncio
async def test_theme_shortcut_changes_screen_and_panel_colors() -> None:
    app = PulseApp(session=FakeSession(_snapshot()))

    async with app.run_test(size=(90, 28)) as pilot:
        await pilot.pause()
        assert app.theme == "pulse-dark"
        dark_screen = app.screen.styles.background
        dark_panel = app.query_one("#cpu-card", Static).styles.background

        await pilot.press("t")
        await pilot.pause()
        assert app.theme == "pulse-light"
        assert app.screen.styles.background != dark_screen
        assert app.query_one("#cpu-card", Static).styles.background != dark_panel

        await pilot.press("2")
        assert app.query_one("#process-table", DataTable).styles.background == (
            app.query_one("#cpu-card", Static).styles.background
        )
        await pilot.press("t")
        await pilot.pause()
        assert app.theme == "pulse-dark"
        assert app.screen.styles.background == dark_screen


@pytest.mark.asyncio
async def test_256_color_terminal_keeps_theme_surfaces_distinct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(constants, "COLOR_SYSTEM", "256")
    app = PulseApp(session=FakeSession(_snapshot()))

    async with app.run_test(size=(90, 28)) as pilot:
        await pilot.pause()
        assert app.console.color_system == "256"
        for expected_theme in ("pulse-dark", "pulse-light"):
            assert app.theme == expected_theme
            theme = app.current_theme
            surfaces = (theme.background, theme.surface, theme.panel)
            assert all(color is not None for color in surfaces)
            color_indexes = {
                Color.parse(color).downgrade(ColorSystem.EIGHT_BIT).number
                for color in surfaces
                if color is not None
            }
            assert len(color_indexes) == 3
            await pilot.press("t")
            await pilot.pause()


@pytest.mark.asyncio
async def test_process_navigation_opens_verified_details_and_returns() -> None:
    session = FakeSession(_snapshot())
    details_service = FakeDetailsService()
    app = PulseApp(session=session, details_service=details_service)

    async with app.run_test(size=(90, 26)) as pilot:
        await pilot.pause()
        await pilot.press("2")
        assert app.has_class("show-processes")
        assert app.query_one(ProcessExplorer).query_one(DataTable).row_count == 1

        await pilot.press("/")
        await pilot.press("q", "2", "r", "m", "t")
        assert app.query_one("#process-search", Input).value == "q2rmt"
        assert app.theme == "pulse-dark"
        await pilot.press("escape")
        assert app.focused is app.query_one("#process-table", DataTable)
        app.query_one("#process-search", Input).value = ""
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, ProcessDetailsScreen)
        assert details_service.calls == 1
        assert session.state.selected_process is not None
        content = app.screen.query_one("#detail-body", Static).content
        rendered = StringIO()
        Console(file=rendered, width=80, force_terminal=False).print(content)
        assert "worker --run" in rendered.getvalue()
        assert "CPU (last scan)" in rendered.getvalue()

        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, ProcessDetailsScreen)
        await pilot.press("1")
        assert not app.has_class("show-processes")


@pytest.mark.asyncio
async def test_system_view_shows_host_facts_and_survives_resize() -> None:
    app = PulseApp(session=FakeSession(_snapshot()))

    async with app.run_test(size=(90, 26)) as pilot:
        await pilot.pause()
        await pilot.press("3")
        assert app.has_class("show-system")
        assert not app.has_class("show-processes")
        host = app.query_one("#host-facts", Static)
        output = StringIO()
        Console(file=output, width=80, force_terminal=False).print(host.content)
        assert "Test OS" in output.getvalue()
        assert "test-host" in output.getvalue()

        await pilot.resize_terminal(50, 20)
        assert app.has_class("compact")
        assert app.query_one("#system-view").region.width >= 40
        await pilot.press("2")
        assert not app.has_class("show-system")
        assert app.has_class("show-processes")


@pytest.mark.asyncio
async def test_overview_and_system_view_show_observed_gpu_values() -> None:
    snapshot = _snapshot()
    at = snapshot.created_at
    gpu = GpuMetrics(at, 0, "Test GPU", 38.0, 6 * 1024**3, 2 * 1024**3, 51.0, "test")
    snapshot = replace(snapshot, gpu=GpuSnapshot(at, (gpu,)))
    app = PulseApp(session=FakeSession(snapshot))

    async with app.run_test(size=(90, 28)) as pilot:
        await pilot.pause()
        card = str(app.query_one("#gpu-card", Static).render())
        assert "38.0%" in card
        assert "2.0 GiB" in card
        assert "51 C" in card

        await pilot.press("3")
        output = StringIO()
        Console(file=output, width=80, force_terminal=False).print(
            app.query_one("#gpu-facts", Static).content
        )
        assert "Test GPU" in output.getvalue()
        assert "2.0 GiB / 6.0 GiB" in output.getvalue()


@pytest.mark.asyncio
async def test_gpu_unavailable_is_explicit_in_both_views() -> None:
    snapshot = _snapshot()
    snapshot = replace(
        snapshot,
        collector_statuses=(
            *snapshot.collector_statuses,
            CollectorStatus("gpu", Availability.UNAVAILABLE, snapshot.created_at),
        ),
    )
    app = PulseApp(session=FakeSession(snapshot))

    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        assert "Unavailable" in str(app.query_one("#gpu-card", Static).render())
        await pilot.press("3")
        assert "nvidia-smi" in str(app.query_one("#gpu-facts", Static).render())


@pytest.mark.asyncio
async def test_system_view_marks_missing_collector_data() -> None:
    app = PulseApp(session=FakeSession(_snapshot(available=False)))

    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        await pilot.press("3")
        assert "unavailable" in str(app.query_one("#host-facts", Static).render())
        output = StringIO()
        Console(file=output, width=80, force_terminal=False).print(
            app.query_one("#hardware-facts", Static).content
        )
        assert "Unavailable" in output.getvalue()


@pytest.mark.asyncio
async def test_history_view_cycles_ranges_and_shows_empty_state() -> None:
    app = PulseApp(session=FakeSession(_snapshot()))
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        await pilot.press("4")
        await pilot.pause()
        assert app.has_class("show-history")
        assert "No historical data" in str(
            app.query_one("#history-chart", Static).render()
        )
        await pilot.press("h")
        await pilot.pause()
        assert app._history_range.value == "30m"
        await pilot.press("1")
        assert not app.has_class("show-history")


@pytest.mark.asyncio
async def test_disappeared_process_shows_last_observation_only() -> None:
    app = PulseApp(
        session=FakeSession(_snapshot()), details_service=MissingDetailsService()
    )

    async with app.run_test(size=(90, 26)) as pilot:
        await pilot.pause()
        await pilot.press("2", "enter")
        await pilot.pause()
        body = app.screen.query_one("#detail-body", Static).content
        output = StringIO()
        Console(file=output, width=80, force_terminal=False).print(body)

        assert "PID was reused" in output.getvalue()
        assert "CPU (last scan)" in output.getvalue()
        assert "12.0%" in output.getvalue()


@pytest.mark.asyncio
async def test_unverified_process_shows_last_scan_without_detail_read() -> None:
    snapshot = _snapshot()
    assert snapshot.processes is not None
    process = replace(snapshot.processes.processes[0], identity=None)
    snapshot = replace(
        snapshot,
        processes=ProcessSnapshot(snapshot.processes.sampled_at, (process,)),
    )
    details_service = FakeDetailsService()
    app = PulseApp(session=FakeSession(snapshot), details_service=details_service)

    async with app.run_test(size=(90, 26)) as pilot:
        await pilot.pause()
        await pilot.press("2", "enter")
        await pilot.pause()
        content = app.screen.query_one("#detail-body", Static).content
        output = StringIO()
        Console(file=output, width=80, force_terminal=False).print(content)

        assert details_service.calls == 0
        assert "identity was not readable" in output.getvalue()
        assert "Memory (last scan)" in output.getvalue()


@pytest.mark.asyncio
async def test_unavailable_metrics_have_an_explicit_empty_state() -> None:
    app = PulseApp(session=FakeSession(_snapshot(available=False)))

    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        assert "Unavailable" in str(app.query_one("#cpu-card", Static).render())
        assert app.query_one("#top-processes", DataTable).row_count == 0
        assert "error" in str(app.query_one("#collector-line", Static).render())
        await pilot.press("ctrl+c")


def test_sparkline_preserves_missing_observations() -> None:
    assert cpu_sparkline((None, 0.0, 50.0, 100.0)) == "·▁▅█"
