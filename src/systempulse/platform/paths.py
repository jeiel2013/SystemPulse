"""Per-user application paths selected by the host platform."""

from pathlib import Path

from platformdirs import user_config_path, user_data_path


def history_database_path() -> Path:
    """Store private monitoring history outside the current working directory."""
    return (
        user_data_path("SystemPulse", appauthor=False, ensure_exists=False)
        / "history.sqlite3"
    )


def configuration_path() -> Path:
    """Find the optional per-user TOML settings file."""
    return (
        user_config_path("SystemPulse", appauthor=False, ensure_exists=False)
        / "config.toml"
    )


def reports_directory() -> Path:
    """Keep generated reports in the user's application data directory."""
    return (
        user_data_path("SystemPulse", appauthor=False, ensure_exists=False) / "reports"
    )
