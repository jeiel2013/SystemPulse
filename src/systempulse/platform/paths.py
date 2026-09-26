"""Per-user application paths selected by the host platform."""

import os
from pathlib import Path

from platformdirs import user_config_path, user_data_path


def _data_directory() -> Path:
    override = os.environ.get("SYSTEMPULSE_DATA_DIR")
    return (
        Path(override).expanduser()
        if override
        else user_data_path("SystemPulse", appauthor=False, ensure_exists=False)
    )


def _config_directory() -> Path:
    override = os.environ.get("SYSTEMPULSE_CONFIG_DIR")
    return (
        Path(override).expanduser()
        if override
        else user_config_path("SystemPulse", appauthor=False, ensure_exists=False)
    )


def history_database_path() -> Path:
    """Store private monitoring history outside the current working directory."""
    return _data_directory() / "history.sqlite3"


def configuration_path() -> Path:
    """Find the optional per-user TOML settings file."""
    return _config_directory() / "config.toml"


def reports_directory() -> Path:
    """Keep generated reports in the user's application data directory."""
    return _data_directory() / "reports"
