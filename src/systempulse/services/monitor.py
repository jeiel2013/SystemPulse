"""Wire local collectors to the application's typed state."""

import asyncio

from sqlalchemy.exc import SQLAlchemyError

from systempulse.collectors.base import CollectionResult
from systempulse.collectors.battery import BatteryCollector
from systempulse.collectors.cpu import CpuCollector
from systempulse.collectors.disk import DiskCollector
from systempulse.collectors.gpu.collector import GpuCollector
from systempulse.collectors.memory import MemoryCollector
from systempulse.collectors.network import NetworkCollector
from systempulse.collectors.processes import ProcessCollector
from systempulse.collectors.registry import CollectorRegistry
from systempulse.collectors.sensors import SensorCollector
from systempulse.collectors.system import SystemCollector
from systempulse.config.settings import load_settings
from systempulse.domain.analysis import Alert
from systempulse.domain.snapshots import SystemSnapshot
from systempulse.history.store import HistoryStore
from systempulse.platform.paths import history_database_path
from systempulse.plugins.loader import PluginResult, register_plugins
from systempulse.rules.engine import RuleEngine
from systempulse.services.aggregator import MetricAggregator
from systempulse.services.metrics import MetricService
from systempulse.services.state import ApplicationState


class MonitorSession:
    """Own collection baselines and snapshots for one running monitor."""

    def __init__(
        self,
        registry: CollectorRegistry,
        history_store: HistoryStore | None = None,
        rule_engine: RuleEngine | None = None,
        config_error: str | None = None,
        plugin_results: tuple[PluginResult, ...] = (),
    ) -> None:
        self.registry = registry
        self.state = ApplicationState()
        self._metrics = MetricService(registry)
        self._aggregator = MetricAggregator()
        self.history_store = history_store
        self.history_error: str | None = None
        self.rule_engine = rule_engine
        self.config_error = config_error
        self.plugin_results = plugin_results

    async def _publish(
        self, results: tuple[CollectionResult[object], ...]
    ) -> SystemSnapshot:
        snapshot = self._aggregator.aggregate(results)
        self.state.update(snapshot)
        changed_alerts: tuple[Alert, ...] = ()
        if self.rule_engine is not None:
            analysis = self.rule_engine.evaluate(snapshot)
            self.state.add_analysis(
                analysis.observations, analysis.new_alerts, analysis.ended_alerts
            )
            changed_alerts = (*analysis.new_alerts, *analysis.ended_alerts)
        if self.history_store is not None:
            try:
                await asyncio.to_thread(
                    self.history_store.record, snapshot, changed_alerts
                )
                self.history_error = None
            except (OSError, SQLAlchemyError) as error:
                self.history_error = type(error).__name__
        return snapshot

    async def dismiss_alert(self, rule_id: str) -> bool:
        """Dismiss an active alert without altering the underlying rule."""
        if self.rule_engine is None:
            return False
        alert = self.rule_engine.dismiss(rule_id)
        if alert is None:
            return False
        self.state.update_alert(alert)
        if self.history_store is not None:
            try:
                await asyncio.to_thread(self.history_store.save_alert, alert)
            except (OSError, SQLAlchemyError) as error:
                self.history_error = type(error).__name__
        return True

    async def sample(self) -> SystemSnapshot:
        """Collect a cycle and publish its snapshot to application state."""
        results = await self._metrics.collect_all()
        return await self._publish(results)

    async def sample_due(self) -> SystemSnapshot:
        """Publish a cycle while respecting each collector's interval."""
        results = await self._metrics.collect_due()
        return await self._publish(results)

    async def close(self) -> None:
        """Release any open history database connection on exit."""
        if self.history_store is not None:
            await asyncio.to_thread(self.history_store.close)

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
    registry.register(DiskCollector())
    registry.register(NetworkCollector())
    registry.register(ProcessCollector())
    registry.register(SystemCollector())
    registry.register(GpuCollector())
    registry.register(BatteryCollector())
    registry.register(SensorCollector())
    loaded = load_settings()
    plugin_results = register_plugins(registry, loaded.settings.enabled_plugins)
    return MonitorSession(
        registry,
        HistoryStore(history_database_path()),
        RuleEngine(loaded.settings.enabled_rules()),
        loaded.error,
        plugin_results,
    )
