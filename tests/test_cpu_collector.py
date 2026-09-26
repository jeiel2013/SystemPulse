"""Deterministic CPU collection tests."""

from collections import namedtuple
from types import SimpleNamespace
from typing import Any

import psutil
import pytest

from systempulse.collectors.cpu import CpuCollector
from systempulse.domain.availability import Availability

Times = namedtuple("Times", "user system idle")


def install_times(
    monkeypatch: pytest.MonkeyPatch,
    totals: list[Times],
    cores: list[list[Times]],
) -> None:
    total_reads = iter(totals)
    core_reads = iter(cores)

    def cpu_times(*, percpu: bool = False) -> Any:
        return next(core_reads) if percpu else next(total_reads)

    monkeypatch.setattr(psutil, "cpu_times", cpu_times)
    monkeypatch.setattr(
        psutil, "cpu_count", lambda *, logical=True: 2 if logical else 1
    )
    monkeypatch.setattr(
        psutil, "cpu_freq", lambda: SimpleNamespace(current=3200.0), raising=False
    )
    monkeypatch.setattr("systempulse.collectors.cpu.get_load_average", lambda: None)


def test_cpu_warms_up_then_reports_measured_delta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_times(
        monkeypatch,
        totals=[Times(10, 10, 80), Times(20, 20, 160)],
        cores=[
            [Times(5, 5, 40), Times(5, 5, 40)],
            [Times(15, 10, 75), Times(5, 5, 90)],
        ],
    )
    collector = CpuCollector()

    first = collector.collect()
    second = collector.collect()

    assert first.status.availability == Availability.WARMING_UP
    assert first.metric is None
    assert second.status.availability == Availability.AVAILABLE
    assert second.metric is not None
    assert second.metric.total_percent == 20.0
    assert second.metric.per_core_percent == (30.0, 0.0)
    assert second.metric.frequency_mhz == 3200.0


def test_cpu_does_not_report_zero_when_counters_have_not_advanced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_times(
        monkeypatch,
        totals=[Times(10, 10, 80), Times(10, 10, 80)],
        cores=[[Times(5, 5, 40)], [Times(5, 5, 40)]],
    )
    collector = CpuCollector()

    collector.collect()
    result = collector.collect()

    assert result.status.availability == Availability.WARMING_UP
    assert result.metric is None


def test_cpu_resets_baseline_when_core_count_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_times(
        monkeypatch,
        totals=[Times(10, 10, 80), Times(20, 20, 160)],
        cores=[
            [Times(5, 5, 40)],
            [Times(15, 10, 75), Times(5, 5, 90)],
        ],
    )
    collector = CpuCollector()

    collector.collect()
    result = collector.collect()

    assert result.status.availability == Availability.WARMING_UP


def test_cpu_remains_available_without_frequency_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_times(
        monkeypatch,
        totals=[Times(10, 10, 80), Times(20, 20, 160)],
        cores=[[Times(5, 5, 40)], [Times(15, 10, 75)]],
    )
    monkeypatch.delattr(psutil, "cpu_freq", raising=False)
    collector = CpuCollector()

    collector.collect()
    result = collector.collect()

    assert result.status.availability == Availability.AVAILABLE
    assert result.metric is not None
    assert result.metric.frequency_mhz is None
    assert result.metric.total_percent == 20.0
