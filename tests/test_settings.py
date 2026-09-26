"""Optional TOML settings validate rules and preserve safe defaults."""

from pathlib import Path

from systempulse.config.settings import load_settings
from systempulse.domain.analysis import MetricKey


def test_missing_settings_use_default_rules(tmp_path: Path) -> None:
    loaded = load_settings(tmp_path / "missing.toml")
    assert loaded.error is None
    assert len(loaded.settings.enabled_rules()) == 3


def test_custom_rule_and_invalid_config(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text(
        '[[rules]]\nid = "ram"\nmetric = "memory.percent"\n'
        "threshold_percent = 80\nfor_seconds = 30\n",
        encoding="utf-8",
    )
    loaded = load_settings(path)
    assert loaded.error is None
    assert loaded.settings.enabled_rules()[0].metric == MetricKey.MEMORY_PERCENT

    path.write_text('[[rules]]\nid = "bad"\nmetric = "unknown"\n', encoding="utf-8")
    invalid = load_settings(path)
    assert invalid.error is not None
    assert len(invalid.settings.enabled_rules()) == 3
