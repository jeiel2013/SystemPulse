"""Process details are verified by instance and degrade on protected fields."""

import os
from contextlib import nullcontext
from datetime import UTC, datetime
from threading import get_ident

import psutil
import pytest

from systempulse.domain.processes import ProcessIdentity
from systempulse.services.process_details import ProcessDetailsService


class FakeProcess:
    def __init__(
        self,
        pid: int,
        created: float,
        *,
        protected: bool = False,
    ) -> None:
        self.pid = pid
        self.created = created
        self.protected = protected
        self.thread_id: int | None = None

    def create_time(self) -> float:
        self.thread_id = get_ident()
        return self.created

    def oneshot(self) -> nullcontext[None]:
        return nullcontext()

    def name(self) -> str:
        return "worker"

    def status(self) -> str:
        return "running"

    def username(self) -> str:
        if self.protected:
            raise psutil.AccessDenied(self.pid)
        return "operator"

    def num_threads(self) -> int:
        return 2

    def ppid(self) -> int:
        return 1

    def exe(self) -> str:
        if self.protected:
            raise psutil.AccessDenied(self.pid)
        return "/opt/worker"

    def cmdline(self) -> list[str]:
        return ["worker", "--serve"]


@pytest.mark.asyncio
async def test_details_are_collected_off_event_loop_and_preserve_missing_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created = 1_000.0
    fake = FakeProcess(42, created, protected=True)
    monkeypatch.setattr(psutil, "Process", lambda pid: fake)
    identity = ProcessIdentity(42, datetime.fromtimestamp(created, UTC))
    event_loop_thread = get_ident()

    details = await ProcessDetailsService().read(identity)

    assert details is not None
    assert details.identity == identity
    assert details.user is None
    assert details.executable is None
    assert details.command_line == ("worker", "--serve")
    assert fake.thread_id != event_loop_thread


@pytest.mark.asyncio
async def test_pid_reuse_during_read_discards_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instances = iter((FakeProcess(42, 1_000.0), FakeProcess(42, 2_000.0)))
    monkeypatch.setattr(psutil, "Process", lambda pid: next(instances))
    identity = ProcessIdentity(42, datetime.fromtimestamp(1_000.0, UTC))

    assert await ProcessDetailsService().read(identity) is None


@pytest.mark.asyncio
async def test_missing_process_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(pid: int) -> FakeProcess:
        raise psutil.NoSuchProcess(pid)

    monkeypatch.setattr(psutil, "Process", missing)
    identity = ProcessIdentity(42, datetime.fromtimestamp(1_000.0, UTC))

    assert await ProcessDetailsService().read(identity) is None


@pytest.mark.asyncio
async def test_real_process_details_can_be_read() -> None:
    process = psutil.Process(os.getpid())
    identity = ProcessIdentity(
        process.pid, datetime.fromtimestamp(process.create_time(), UTC)
    )

    details = await ProcessDetailsService().read(identity)

    assert details is not None
    assert details.identity == identity
    assert details.name is not None
