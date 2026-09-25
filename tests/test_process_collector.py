"""Process scan behavior under access restrictions and PID reuse."""

from collections.abc import Iterator
from types import SimpleNamespace

import psutil
import pytest

from systempulse.collectors.processes import ProcessCollector
from systempulse.domain.availability import Availability


class FakeProcess:
    def __init__(
        self,
        pid: int,
        info: dict[str, object] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.pid = pid
        self._info = info or {}
        self._error = error

    @property
    def info(self) -> dict[str, object]:
        if self._error is not None:
            raise self._error
        return self._info


class FakeProcessIter:
    def __init__(self, scans: list[list[FakeProcess]]) -> None:
        self._scans = iter(scans)
        self.clears = 0
        self.attributes: tuple[str, ...] | None = None

    def __call__(
        self, *, attrs: tuple[str, ...], ad_value: object
    ) -> Iterator[FakeProcess]:
        self.attributes = attrs
        assert ad_value is None
        return iter(next(self._scans))

    def cache_clear(self) -> None:
        self.clears += 1


def process(pid: int, created: float, cpu: float) -> FakeProcess:
    return FakeProcess(
        pid,
        {
            "name": "worker",
            "create_time": created,
            "cpu_times": SimpleNamespace(user=cpu, system=0.0),
            "memory_info": SimpleNamespace(rss=2048),
            "username": "operator",
            "num_threads": 2,
        },
    )


def install_scan(
    monkeypatch: pytest.MonkeyPatch, scans: list[list[FakeProcess]]
) -> FakeProcessIter:
    fake = FakeProcessIter(scans)
    monkeypatch.setattr(psutil, "process_iter", fake)
    times = iter([100.0, 102.0])
    monkeypatch.setattr(
        "systempulse.collectors.processes.monotonic", lambda: next(times)
    )
    return fake


def test_process_scan_computes_cpu_from_matching_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = install_scan(
        monkeypatch,
        [[process(42, 1_000.0, 1.0)], [process(42, 1_000.0, 3.0)]],
    )
    collector = ProcessCollector()

    first = collector.collect()
    second = collector.collect()

    assert first.status.availability == Availability.AVAILABLE
    assert first.metric is not None
    assert first.metric.processes[0].cpu_percent is None
    assert second.metric is not None
    assert second.metric.processes[0].cpu_percent == 100.0
    assert second.metric.processes[0].memory_rss_bytes == 2048
    assert fake.clears == 2
    assert fake.attributes is not None
    assert "status" not in fake.attributes
    assert "ppid" not in fake.attributes


def test_pid_reuse_does_not_inherit_previous_cpu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_scan(
        monkeypatch,
        [[process(42, 1_000.0, 1.0)], [process(42, 2_000.0, 3.0)]],
    )
    collector = ProcessCollector()

    first = collector.collect()
    second = collector.collect()

    assert first.metric is not None and second.metric is not None
    assert first.metric.processes[0].identity != second.metric.processes[0].identity
    assert second.metric.processes[0].cpu_percent is None


def test_protected_process_is_retained_and_disappeared_process_is_skipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_scan(
        monkeypatch,
        [
            [
                FakeProcess(10, error=psutil.AccessDenied(10)),
                FakeProcess(11, error=psutil.NoSuchProcess(11)),
            ]
        ],
    )
    collector = ProcessCollector()

    result = collector.collect()

    assert result.metric is not None
    assert len(result.metric.processes) == 1
    protected = result.metric.processes[0]
    assert protected.pid == 10
    assert protected.name is None
    assert protected.identity is None
    assert result.metric.skipped_count == 1
