"""Terminal-friendly formatting for measurements stored in base units."""


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
