"""Wire local collectors to the application's typed state."""

import asyncio

from systempulse.collectors.cpu import CpuCollector
from systempulse.collectors.memory import MemoryCollector
from systempulse.collectors.processes import ProcessCollector
from systempulse.collectors.registry import CollectorRegistry
from systempulse.domain.snapshots import SystemSnapshot
from systempulse.services.aggregator import MetricAggregator
from systempulse.services.metrics import MetricService
from systempulse.services.state import ApplicationState


class MonitorSession:
    """Own collection baselines and snapshots for one running monitor."""

    def __init__(self, registry: CollectorRegistry) -> None:
        self.registry = registry
        self.state = ApplicationState()
        self._metrics = MetricService(registry)
        self._aggregator = MetricAggregator()

    async def sample(self) -> SystemSnapshot:
        """Collect a cycle and publish its snapshot to application state."""
        results = await self._metrics.collect_all()
        snapshot = self._aggregator.aggregate(results)
        self.state.update(snapshot)
        return snapshot

    async def sample_after_warmup(self, delay_seconds: float = 1.0) -> SystemSnapshot:
        """Take two samples so CPU rates have an observed time interval."""
        if delay_seconds <= 0:
            raise ValueError("delay_seconds must be positive")
        await self.sample()
        await asyncio.sleep(delay_seconds)
        return await self.sample()


def create_default_session() -> MonitorSession:
    """Register the collectors currently shipped with SystemPulse."""
    registry = CollectorRegistry()
    registry.register(CpuCollector())
    registry.register(MemoryCollector())
    registry.register(ProcessCollector())
    return MonitorSession(registry)
