"""Package version access."""

from importlib.metadata import version


def get_version() -> str:
    """Return the version from installed package metadata."""
    return version("systempulse-monitor")
