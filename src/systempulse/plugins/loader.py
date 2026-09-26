"""Load explicitly enabled collector entry points in isolation."""

from dataclasses import dataclass
from importlib.metadata import EntryPoint, entry_points
from typing import cast

from systempulse.collectors.base import Collector, CollectorMetadata
from systempulse.collectors.registry import CollectorRegistry

ENTRY_POINT_GROUP = "systempulse.collectors"


@dataclass(frozen=True, slots=True)
class PluginResult:
    name: str
    loaded: bool
    detail: str


def discover_plugins() -> tuple[EntryPoint, ...]:
    """List installed collector factories without executing their code."""
    return tuple(entry_points(group=ENTRY_POINT_GROUP))


def register_plugins(
    registry: CollectorRegistry, enabled: tuple[str, ...]
) -> tuple[PluginResult, ...]:
    """Execute only named opt-in plugins; contain import and factory failures."""
    available = {entry.name: entry for entry in discover_plugins()}
    results: list[PluginResult] = []
    for name in enabled:
        entry = available.get(name)
        if entry is None:
            results.append(PluginResult(name, False, "Not installed"))
            continue
        try:
            factory = entry.load()
            collector = factory()
            metadata = collector.metadata
            if (
                not isinstance(metadata, CollectorMetadata)
                or not callable(collector.is_available)
                or not callable(collector.collect)
            ):
                raise TypeError("Invalid collector contract")
            registry.register(cast("Collector[object]", collector))
        except Exception as error:
            results.append(PluginResult(name, False, type(error).__name__))
        else:
            results.append(PluginResult(name, True, metadata.name))
    return tuple(results)
