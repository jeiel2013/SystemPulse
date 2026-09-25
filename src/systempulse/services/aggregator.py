"""Convert typed collection results into one application snapshot."""

from datetime import UTC, datetime

from systempulse.collectors.base import CollectionResult
from systempulse.domain.gpu import GpuSnapshot
from systempulse.domain.metrics import CpuMetrics, MemoryMetrics, SystemMetrics
from systempulse.domain.processes import ProcessSnapshot
from systempulse.domain.snapshots import MetricSnapshot, SystemSnapshot


class MetricAggregator:
    """Build a snapshot without substituting values for missing collectors."""

    def aggregate(
        self, results: tuple[CollectionResult[object], ...]
    ) -> SystemSnapshot:
        """Preserve each sample time and include every collector status."""
        cpu: CpuMetrics | None = None
        memory: MemoryMetrics | None = None
        processes: ProcessSnapshot | None = None
        system: SystemMetrics | None = None
        gpu: GpuSnapshot | None = None
        seen: set[str] = set()
        statuses = tuple(result.status for result in results)

        for result in results:
            name = result.status.name
            if name in seen:
                raise ValueError(f"duplicate collection result for {name!r}")
            seen.add(name)
            metric = result.metric
            if name == "cpu":
                if metric is not None and not isinstance(metric, CpuMetrics):
                    raise TypeError("cpu collector returned an unexpected metric")
                cpu = metric
            elif name == "memory":
                if metric is not None and not isinstance(metric, MemoryMetrics):
                    raise TypeError("memory collector returned an unexpected metric")
                memory = metric
            elif name == "processes":
                if metric is not None and not isinstance(metric, ProcessSnapshot):
                    raise TypeError("process collector returned an unexpected metric")
                processes = metric
            elif name == "system":
                if metric is not None and not isinstance(metric, SystemMetrics):
                    raise TypeError("system collector returned an unexpected metric")
                system = metric
            elif name == "gpu":
                if metric is not None and not isinstance(metric, GpuSnapshot):
                    raise TypeError("gpu collector returned an unexpected metric")
                gpu = metric

        created_at = datetime.now(UTC)
        return SystemSnapshot(
            created_at=created_at,
            metrics=MetricSnapshot(created_at=created_at, cpu=cpu, memory=memory),
            processes=processes,
            system=system,
            collector_statuses=statuses,
            gpu=gpu,
        )
