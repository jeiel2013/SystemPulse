"""Validate optional TOML settings before constructing local rules."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from systempulse.domain.analysis import MetricKey, Rule, Severity
from systempulse.platform.paths import configuration_path


class RuleSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    metric: MetricKey
    threshold_percent: float = Field(ge=0, le=100)
    for_seconds: float = Field(ge=0)
    severity: Severity = Severity.WARNING
    enabled: bool = True

    def to_rule(self) -> Rule:
        return Rule(
            self.id,
            self.metric,
            self.threshold_percent,
            self.for_seconds,
            self.severity,
        )


def _default_rules() -> tuple[RuleSettings, ...]:
    return (
        RuleSettings(
            id="high-cpu",
            metric=MetricKey.CPU_PERCENT,
            threshold_percent=90,
            for_seconds=120,
        ),
        RuleSettings(
            id="high-memory",
            metric=MetricKey.MEMORY_PERCENT,
            threshold_percent=90,
            for_seconds=120,
        ),
        RuleSettings(
            id="high-disk",
            metric=MetricKey.DISK_PERCENT,
            threshold_percent=95,
            for_seconds=120,
        ),
    )


class AppSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rules: tuple[RuleSettings, ...] = Field(default_factory=_default_rules)

    @model_validator(mode="after")
    def unique_rule_ids(self) -> "AppSettings":
        ids = [rule.id for rule in self.rules]
        if len(ids) != len(set(ids)):
            raise ValueError("rule ids must be unique")
        return self

    def enabled_rules(self) -> tuple[Rule, ...]:
        return tuple(rule.to_rule() for rule in self.rules if rule.enabled)


@dataclass(frozen=True, slots=True)
class LoadedSettings:
    settings: AppSettings
    error: str | None = None


def load_settings(path: Path | None = None) -> LoadedSettings:
    """Return defaults if the optional config is missing or invalid."""
    chosen = path or configuration_path()
    try:
        if not chosen.exists():
            return LoadedSettings(AppSettings())
        with chosen.open("rb") as stream:
            raw = tomllib.load(stream)
        return LoadedSettings(AppSettings.model_validate(raw))
    except (OSError, tomllib.TOMLDecodeError, ValidationError) as error:
        return LoadedSettings(AppSettings(), f"{type(error).__name__}: {error}")
