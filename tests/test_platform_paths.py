"""Per-user path selection and explicit test overrides."""

from pathlib import Path

from pytest import MonkeyPatch

from systempulse.platform.paths import (
    configuration_path,
    history_database_path,
    reports_directory,
)


def test_path_overrides_keep_data_and_config_separate(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("SYSTEMPULSE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("SYSTEMPULSE_CONFIG_DIR", str(tmp_path / "config"))

    assert history_database_path() == tmp_path / "data" / "history.sqlite3"
    assert reports_directory() == tmp_path / "data" / "reports"
    assert configuration_path() == tmp_path / "config" / "config.toml"
