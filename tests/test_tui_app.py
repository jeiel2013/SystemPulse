"""The Textual overview renders snapshots and responds to terminal controls."""

from datetime import UTC, datetime

import pytest
from textual.widgets import DataTable, Static

from systempulse.domain.availability import Availability, CollectorStatus
from systempulse.domain.metrics import CpuMetrics, MemoryMetrics
from systempulse.domain.processes import ProcessMetrics, ProcessSnapshot
from systempulse.domain.snapshots import MetricSnapshot, SystemSnapshot
from systempulse.services.state import ApplicationState
from systempulse.tui.app import PulseApp, cpu_sparkline


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
                    at, 42, None, "worker", 12.0, 1024, None, None, None, None
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
async def test_unavailable_metrics_have_an_explicit_empty_state() -> None:
    app = PulseApp(session=FakeSession(_snapshot(available=False)))

    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        assert "Unavailable" in str(app.query_one("#cpu-card", Static).render())
        assert app.query_one("#top-processes", DataTable).row_count == 0
        assert "error" in str(app.query_one("#collector-line", Static).render())


def test_sparkline_preserves_missing_observations() -> None:
    assert cpu_sparkline((None, 0.0, 50.0, 100.0)) == "·▁▅█"
