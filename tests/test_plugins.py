"""Third-party collector code runs only after explicit local enablement."""

from datetime import timedelta
from types import SimpleNamespace

import pytest

from systempulse.collectors.base import CollectionResult, CollectorMetadata
from systempulse.collectors.registry import CollectorRegistry
from systempulse.plugins.loader import register_plugins


def test_plugins_are_opt_in_and_failures_are_isolated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class PluginCollector:
        metadata = CollectorMetadata("plugin-test", timedelta(seconds=5))

        def is_available(self) -> bool:
            return True

        def collect(self) -> CollectionResult[object]:
            raise AssertionError("not sampled by registration")

    def load_factory() -> object:
        calls.append("load")
        return PluginCollector

    entry = SimpleNamespace(name="example", load=load_factory)
    monkeypatch.setattr("systempulse.plugins.loader.discover_plugins", lambda: (entry,))
    registry = CollectorRegistry()
    assert register_plugins(registry, ()) == ()
    assert calls == []

    results = register_plugins(registry, ("example", "missing"))
    assert results[0].loaded is True
    assert results[1].loaded is False
    assert registry.entries()[0].collector.metadata.name == "plugin-test"
