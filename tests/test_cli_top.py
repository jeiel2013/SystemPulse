"""Continuous top refreshes observed snapshots and stops on the quit key."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from io import StringIO

import pytest
from rich.console import Console

from systempulse.cli_top import run_top
from systempulse.services.process_query import ProcessQuery


@pytest.mark.asyncio
async def test_top_refreshes_and_quits_on_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Session:
        samples = 0
        due_samples = 0

        async def sample(self) -> None:
            self.samples += 1

        async def sample_due(self) -> None:
            self.due_samples += 1

    session = Session()

    @contextmanager
    def reader() -> Iterator[Callable[[], bool]]:
        yield lambda: session.due_samples > 0

    monkeypatch.setattr("systempulse.cli_top.quit_key_reader", reader)
    monkeypatch.setattr(
        "systempulse.cli_top.render_top", lambda *_args: "Observed process table"
    )
    output = StringIO()
    display = Console(file=output, width=80, force_terminal=False)

    await run_top(session, display, ProcessQuery(), refresh_interval=0.01)

    assert session.samples == 1
    assert session.due_samples == 1
