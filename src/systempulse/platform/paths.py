"""Per-user application paths selected by the host platform."""

from pathlib import Path

from platformdirs import user_data_path


def history_database_path() -> Path:
    """Store private monitoring history outside the current working directory."""
    return (
        user_data_path("SystemPulse", appauthor=False, ensure_exists=False)
        / "history.sqlite3"
    )
