"""Uptime formatting uses observed boot time and handles invalid deltas."""

from datetime import UTC, datetime, timedelta

from systempulse.presentation import format_temperature, format_uptime


def test_uptime_formats_days_and_hours() -> None:
    observed = datetime(2026, 9, 25, tzinfo=UTC)

    assert format_uptime(
        observed - timedelta(days=3, hours=14, minutes=5), observed
    ) == ("3d 14h 5m")
    assert format_uptime(observed - timedelta(hours=2, minutes=3), observed) == (
        "2h 3m"
    )


def test_uptime_does_not_guess_missing_or_future_boot_time() -> None:
    observed = datetime(2026, 9, 25, tzinfo=UTC)

    assert format_uptime(None, observed) == "Unavailable"
    assert format_uptime(observed + timedelta(seconds=1), observed) == "Unavailable"


def test_temperature_marks_missing_sensor() -> None:
    assert format_temperature(51.2) == "51 C"
    assert format_temperature(None) == "Unavailable"
