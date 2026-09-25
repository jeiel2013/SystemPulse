"""Validation for measurements at collector boundaries."""

from datetime import datetime, timedelta
from math import isfinite


def require_utc(value: datetime, name: str = "sampled_at") -> None:
    """Reject timestamps that cannot be safely stored as UTC instants."""
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{name} must be timezone-aware UTC")


def require_percent(value: float, name: str) -> None:
    """Validate a bounded system percentage."""
    if not isfinite(value) or not 0 <= value <= 100:
        raise ValueError(f"{name} must be a finite percentage from 0 to 100")


def require_nonnegative(value: int | float, name: str) -> None:
    """Validate a count or measurement that cannot be negative."""
    if not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
