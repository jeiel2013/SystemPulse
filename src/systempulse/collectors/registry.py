"""Registration and enablement of local metric collectors."""

from dataclasses import dataclass

from systempulse.collectors.base import Collector


@dataclass(frozen=True, slots=True)
class RegisteredCollector:
    """One collector and its current enablement setting."""

    collector: Collector[object]
    enabled: bool


class CollectorRegistry:
    """Keep collectors discoverable without tying them to the UI."""

    def __init__(self) -> None:
        self._collectors: dict[str, RegisteredCollector] = {}

    def register(self, collector: Collector[object], *, enabled: bool = True) -> None:
        """Register a uniquely named collector."""
        name = collector.metadata.name
        if name in self._collectors:
            raise ValueError(f"collector {name!r} is already registered")
        self._collectors[name] = RegisteredCollector(collector, enabled)

    def set_enabled(self, name: str, enabled: bool) -> None:
        """Enable or disable a registered collector."""
        registered = self._collectors[name]
        self._collectors[name] = RegisteredCollector(registered.collector, enabled)

    def entries(self) -> tuple[RegisteredCollector, ...]:
        """Return an immutable view for one collection cycle."""
        return tuple(self._collectors.values())
