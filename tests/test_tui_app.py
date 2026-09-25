"""The Textual overview renders snapshots and responds to terminal controls."""

from dataclasses import replace
from datetime import UTC, datetime
from io import StringIO

import pytest
from rich.console import Console
from textual.widgets import DataTable, Input, Static

from systempulse.domain.availability import Availability, CollectorStatus
from systempulse.domain.metrics import CpuMetrics, MemoryMetrics
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
    return SystemSnapshot(
        at, MetricSnapshot(at, cpu, memory), processes, None, statuses
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

        await pilot.press("r")
        await pilot.pause()
        assert session.full_calls >= 1

        await pilot.resize_terminal(80, 25)
        assert app.has_class("short")
        assert app.query_one("#top-processes", DataTable).region.y < 18

        await pilot.resize_terminal(50, 20)
        assert app.has_class("compact")
        cpu_card = app.query_one("#cpu-card", Static)
        memory_card = app.query_one("#memory-card", Static)
        assert memory_card.region.y > cpu_card.region.y
        assert cpu_card.region.width >= 40
        await pilot.press("q")


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
        await pilot.press("q", "2", "r", "m")
        assert app.query_one("#process-search", Input).value == "q2rm"
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
