"""I/O rates are measured from counter deltas and survive missing sources."""

from types import SimpleNamespace

import pytest

from systempulse.collectors.disk import DiskCollector
from systempulse.collectors.network import NetworkCollector
from systempulse.domain.availability import Availability


def test_disk_rate_needs_two_samples_and_recovers_after_reset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "systempulse.collectors.disk.psutil.disk_usage",
        lambda _path: SimpleNamespace(total=1000, used=400, free=600, percent=40.0),
    )
    counters = iter(((100, 200), (150, 260), (10, 20)))

    def read_disk_counters() -> SimpleNamespace:
        read, write = next(counters)
        return SimpleNamespace(read_bytes=read, write_bytes=write)

    monkeypatch.setattr(
        "systempulse.collectors.disk.psutil.disk_io_counters", read_disk_counters
    )
    times = iter((10.0, 12.0, 14.0))
    monkeypatch.setattr("systempulse.collectors.disk.monotonic", lambda: next(times))

    collector = DiskCollector()
    first = collector.collect().metric
    second = collector.collect().metric
    reset = collector.collect().metric

    assert first is not None and first.read_bytes_per_second is None
    assert second is not None and second.read_bytes_per_second == 25.0
    assert second.write_bytes_per_second == 30.0
    assert reset is not None and reset.read_bytes_per_second is None


def test_network_rates_and_unavailable_counter(monkeypatch: pytest.MonkeyPatch) -> None:
    readings = iter(((100, 200), (160, 220)))

    def read_counters(*, pernic: bool = False, nowrap: bool = True) -> object:
        assert nowrap
        if pernic:
            return {"eth0": SimpleNamespace(bytes_recv=100, bytes_sent=200)}
        received, sent = next(readings)
        return SimpleNamespace(bytes_recv=received, bytes_sent=sent)

    monkeypatch.setattr(
        "systempulse.collectors.network.psutil.net_io_counters", read_counters
    )
    times = iter((10.0, 12.0))
    monkeypatch.setattr("systempulse.collectors.network.monotonic", lambda: next(times))
    collector = NetworkCollector()
    first = collector.collect().metric
    second = collector.collect().metric

    assert first is not None and first.download_bytes_per_second is None
    assert second is not None and second.download_bytes_per_second == 30.0
    assert second.upload_bytes_per_second == 10.0
    assert second.interfaces[0].name == "eth0"

    monkeypatch.setattr(
        "systempulse.collectors.network.psutil.net_io_counters", lambda **_kwargs: None
    )
    assert collector.collect().status.availability == Availability.UNAVAILABLE
