"""Optional hardware sources may be absent without failing the monitor."""

from types import SimpleNamespace

import pytest

from systempulse.collectors.battery import BatteryCollector
from systempulse.collectors.sensors import SensorCollector
from systempulse.domain.availability import Availability


def test_battery_absence_and_observed_charge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "systempulse.collectors.battery.psutil.sensors_battery",
        lambda: None,
        raising=False,
    )
    assert BatteryCollector().collect().status.availability == Availability.UNAVAILABLE
    monkeypatch.setattr(
        "systempulse.collectors.battery.psutil.sensors_battery",
        lambda: SimpleNamespace(percent=67.0, power_plugged=True, secsleft=-1),
        raising=False,
    )
    metric = BatteryCollector().collect().metric
    assert metric is not None
    assert metric.percent == 67.0
    assert metric.seconds_left is None


def test_sensor_fan_survives_temperature_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken_temperature() -> None:
        raise OSError("not exposed")

    monkeypatch.setattr(
        "systempulse.collectors.sensors.psutil.sensors_temperatures",
        broken_temperature,
        raising=False,
    )
    monkeypatch.setattr(
        "systempulse.collectors.sensors.psutil.sensors_fans",
        lambda: {"case": [SimpleNamespace(label="Front", current=1200)]},
        raising=False,
    )
    metric = SensorCollector().collect().metric
    assert metric is not None
    assert metric.readings[0].unit == "RPM"
    assert metric.readings[0].value == 1200
