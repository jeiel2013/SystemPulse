"""Terminal-friendly formatting for measurements stored in base units."""

from datetime import datetime


def format_bytes(value: int | None) -> str:
    """Format a byte count using IEC units without changing the stored value."""
    if value is None:
        return "Unavailable"
    amount = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if amount < 1024 or unit == "TiB":
            return f"{amount:.0f} {unit}" if unit == "B" else f"{amount:.1f} {unit}"
        amount /= 1024
    raise AssertionError("unreachable")


def format_percent(value: float | None) -> str:
    """Show unavailable measurements explicitly."""
    return "Unavailable" if value is None else f"{value:.1f}%"


def format_rate(value: float | None) -> str:
    """Format an observed byte-per-second rate without guessing a baseline."""
    return "Unavailable" if value is None else f"{format_bytes(round(value))}/s"


def format_temperature(value: float | None) -> str:
    """Show observed temperatures without manufacturing missing readings."""
    return "Unavailable" if value is None else f"{value:.0f} C"


def format_uptime(boot_time: datetime | None, observed_at: datetime) -> str:
    """Express elapsed host time without guessing when boot time is unavailable."""
    if boot_time is None:
        return "Unavailable"
    seconds = int((observed_at - boot_time).total_seconds())
    if seconds < 0:
        return "Unavailable"
    days, remainder = divmod(seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes = remainder // 60
    return f"{days}d {hours}h {minutes}m" if days else f"{hours}h {minutes}m"
