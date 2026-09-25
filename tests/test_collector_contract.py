"""Tests for collector result and metadata invariants."""

from datetime import UTC, datetime, timedelta

import pytest

from systempulse.collectors.base import CollectionResult, CollectorMetadata
from systempulse.domain.availability import Availability, CollectorStatus


def test_metadata_rejects_nonpositive_sampling_interval() -> None:
    with pytest.raises(ValueError, match="sampling_interval"):
        CollectorMetadata(name="cpu", sampling_interval=timedelta(0))


def test_result_rejects_metric_with_unavailable_status() -> None:
    status = CollectorStatus(
        name="cpu",
        availability=Availability.UNAVAILABLE,
        checked_at=datetime.now(UTC),
    )

    with pytest.raises(ValueError, match="available status"):
        CollectionResult(status=status, metric=42.0)


def test_result_rejects_available_status_without_metric() -> None:
    status = CollectorStatus(
        name="cpu",
        availability=Availability.AVAILABLE,
        checked_at=datetime.now(UTC),
    )

    with pytest.raises(ValueError, match="available status"):
        CollectionResult[float](status=status)
