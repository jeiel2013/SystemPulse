"""Aggregation retains observed values and unavailable states."""

from datetime import UTC, datetime

import pytest

from systempulse.collectors.base import CollectionResult
from systempulse.domain.availability import Availability, CollectorStatus
from systempulse.domain.metrics import CpuMetrics
from systempulse.domain.processes import ProcessSnapshot
from systempulse.services.aggregator import MetricAggregator


def result(name: str, metric: object | None) -> CollectionResult[object]:
    return CollectionResult(
        status=CollectorStatus(
            name=name,
            availability=(
                Availability.AVAILABLE
                if metric is not None
                else Availability.UNAVAILABLE
            ),
            checked_at=datetime.now(UTC),
        ),
        metric=metric,
    )


def test_aggregator_keeps_sample_timestamp_and_unavailable_status() -> None:
    sampled_at = datetime(2026, 1, 1, tzinfo=UTC)
    cpu = CpuMetrics(
        sampled_at=sampled_at,
        total_percent=25.0,
        per_core_percent=(25.0,),
        physical_cores=1,
        logical_cores=1,
        frequency_mhz=None,
        load_average=None,
    )

    snapshot = MetricAggregator().aggregate(
        (result("cpu", cpu), result("memory", None))
    )

    assert snapshot.metrics.cpu is cpu
    assert snapshot.metrics.cpu.sampled_at == sampled_at
    assert snapshot.metrics.memory is None
    assert snapshot.collector_statuses[1].availability == Availability.UNAVAILABLE


def test_aggregator_rejects_wrong_metric_type() -> None:
    with pytest.raises(TypeError, match="cpu collector"):
        MetricAggregator().aggregate((result("cpu", "not CPU metrics"),))


def test_aggregator_keeps_process_scan_timestamp() -> None:
    scanned_at = datetime(2026, 1, 1, tzinfo=UTC)
    processes = ProcessSnapshot(sampled_at=scanned_at, processes=())

    snapshot = MetricAggregator().aggregate((result("processes", processes),))

    assert snapshot.processes is processes
    assert snapshot.processes.sampled_at == scanned_at


def test_aggregator_rejects_duplicate_collector_results() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        MetricAggregator().aggregate((result("memory", None), result("memory", None)))
