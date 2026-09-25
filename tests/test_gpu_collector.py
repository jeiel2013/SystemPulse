"""NVIDIA CSV collection is bounded, typed, and optional."""

import asyncio
import subprocess
from datetime import UTC, datetime, timedelta

import pytest

from systempulse.collectors.gpu.collector import GpuCollector
from systempulse.collectors.gpu.providers import (
    NvidiaSmiProvider,
    UnavailableProvider,
    parse_nvidia_csv,
    select_gpu_provider,
)
from systempulse.collectors.registry import CollectorRegistry
from systempulse.domain.availability import Availability
from systempulse.domain.gpu import GpuSnapshot
from systempulse.services.metrics import MetricService


def test_nvidia_csv_parses_multiple_devices_and_missing_fields() -> None:
    at = datetime(2026, 9, 25, tzinfo=UTC)
    snapshot = parse_nvidia_csv(
        '0,"GeForce, Test",42,6144,1024,55\n1,Other,N/A,8192,256,N/A\n', at
    )

    assert len(snapshot.devices) == 2
    assert snapshot.devices[0].name == "GeForce, Test"
    assert snapshot.devices[0].vram_total_bytes == 6144 * 1024**2
    assert snapshot.devices[0].vram_used_bytes == 1024 * 1024**2
    assert snapshot.devices[0].temperature_celsius == 55
    assert snapshot.devices[1].utilization_percent is None
    assert snapshot.devices[1].temperature_celsius is None


def test_nvidia_csv_rejects_malformed_or_impossible_values() -> None:
    at = datetime(2026, 9, 25, tzinfo=UTC)

    with pytest.raises(ValueError, match="column count"):
        parse_nvidia_csv("0,GPU,42", at)
    with pytest.raises(ValueError, match="exceed"):
        parse_nvidia_csv("0,GPU,42,1024,2048,55", at)
    with pytest.raises(ValueError, match="finite"):
        parse_nvidia_csv("0,GPU,nan,1024,256,55", at)


def test_nvidia_provider_runs_only_fixed_read_only_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[object, object]] = []

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, "0,Test GPU,20,6144,100,50\n")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = NvidiaSmiProvider("C:/Program Files/NVIDIA/nvidia-smi.exe").collect()

    assert result.devices[0].source == "nvidia-smi"
    args, options = calls[0]
    assert isinstance(args, list)
    assert args[0] == "C:/Program Files/NVIDIA/nvidia-smi.exe"
    assert args[1].startswith("--query-gpu=")
    assert options == {
        "capture_output": True,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "check": True,
        "timeout": 2.0,
    }


def test_gpu_collector_handles_no_devices_without_metric(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def no_devices(
        args: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 0, "")

    monkeypatch.setattr(subprocess, "run", no_devices)
    collector = GpuCollector(NvidiaSmiProvider("nvidia-smi"))

    assert collector.metadata.sampling_interval == timedelta(seconds=2)
    result = collector.collect()
    assert result.status.availability == Availability.UNAVAILABLE
    assert result.metric is None
    assert result.status.reason == "No NVIDIA GPU data was returned"


def test_missing_provider_does_not_break_metric_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("shutil.which", lambda _name: None)
    assert isinstance(select_gpu_provider(), UnavailableProvider)

    registry = CollectorRegistry()
    registry.register(GpuCollector(UnavailableProvider()))
    result = asyncio.run(MetricService(registry).collect_all())[0]

    assert result.status.availability == Availability.UNAVAILABLE
    assert result.metric is None


def test_provider_error_is_isolated_by_metric_service() -> None:
    class FailingProvider:
        name = "broken"

        def is_available(self) -> bool:
            return True

        def collect(self) -> GpuSnapshot:
            raise subprocess.TimeoutExpired("nvidia-smi", 2)

    registry = CollectorRegistry()
    registry.register(GpuCollector(FailingProvider()))
    result = asyncio.run(MetricService(registry).collect_all())[0]

    assert result.status.availability == Availability.ERROR
    assert result.status.reason == "TimeoutExpired"
