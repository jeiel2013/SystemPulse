"""GPU measurements preserve optional fields and reject impossible values."""

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from systempulse.domain.gpu import GpuMetrics, GpuSnapshot


def _gpu() -> GpuMetrics:
    return GpuMetrics(
        datetime(2026, 9, 25, tzinfo=UTC),
        0,
        "Test GPU",
        42.0,
        8 * 1024**3,
        2 * 1024**3,
        54.0,
        "test",
    )


def test_gpu_snapshot_retains_observed_optional_fields() -> None:
    gpu = replace(_gpu(), temperature_celsius=None)
    snapshot = GpuSnapshot(gpu.sampled_at, (gpu,))

    assert snapshot.devices[0].temperature_celsius is None
    assert snapshot.devices[0].vram_used_bytes == 2 * 1024**3


def test_gpu_rejects_impossible_vram_and_duplicate_indexes() -> None:
    with pytest.raises(ValueError, match="exceed"):
        replace(_gpu(), vram_used_bytes=9 * 1024**3)
    gpu = _gpu()
    with pytest.raises(ValueError, match="unique"):
        GpuSnapshot(gpu.sampled_at, (gpu, gpu))
