"""Portable GPU provider contract and an NVIDIA CLI implementation."""

import csv
import shutil
import subprocess
from datetime import UTC, datetime
from io import StringIO
from math import isfinite
from typing import Protocol

from systempulse.domain.gpu import GpuMetrics, GpuSnapshot

_QUERY = (
    "--query-gpu=index,name,utilization.gpu,memory.total,memory.used,temperature.gpu"
)
_FORMAT = "--format=csv,noheader,nounits"
_MISSING = frozenset({"", "n/a", "not supported", "[not supported]"})


class GpuUnavailableError(Exception):
    """A supported provider found no GPU devices to report."""


class GpuProvider(Protocol):
    """Return measured devices without exposing vendor logic to the core."""

    @property
    def name(self) -> str: ...

    def is_available(self) -> bool: ...

    def collect(self) -> GpuSnapshot: ...


class UnavailableProvider:
    """Explicit fallback when no supported local GPU source exists."""

    name = "unavailable"

    def is_available(self) -> bool:
        return False

    def collect(self) -> GpuSnapshot:
        raise RuntimeError("No supported GPU provider is available")


def _optional_number(raw: str) -> float | None:
    value = raw.strip()
    if value.casefold() in _MISSING:
        return None
    number = float(value)
    if not isfinite(number):
        raise ValueError("GPU measurement must be finite")
    return number


def _mib_to_bytes(raw: str) -> int | None:
    number = _optional_number(raw)
    return None if number is None else int(number * 1024**2)


def parse_nvidia_csv(output: str, sampled_at: datetime) -> GpuSnapshot:
    """Parse all devices while preserving unsupported fields as unavailable."""
    devices: list[GpuMetrics] = []
    for row in csv.reader(StringIO(output)):
        if not row:
            continue
        if len(row) != 6:
            raise ValueError("Unexpected nvidia-smi CSV column count")
        index, name, utilization, total, used, temperature = row
        devices.append(
            GpuMetrics(
                sampled_at=sampled_at,
                index=int(index.strip()),
                name=name.strip(),
                utilization_percent=_optional_number(utilization),
                vram_total_bytes=_mib_to_bytes(total),
                vram_used_bytes=_mib_to_bytes(used),
                temperature_celsius=_optional_number(temperature),
                source="nvidia-smi",
            )
        )
    return GpuSnapshot(sampled_at, tuple(devices))


class NvidiaSmiProvider:
    """Use NVIDIA's fixed, read-only CSV query with a short timeout."""

    name = "nvidia-smi"

    def __init__(self, executable: str | None = None) -> None:
        self._executable = executable or shutil.which("nvidia-smi")

    def is_available(self) -> bool:
        return self._executable is not None

    def collect(self) -> GpuSnapshot:
        if self._executable is None:
            raise RuntimeError("nvidia-smi is not installed")
        result = subprocess.run(
            [self._executable, _QUERY, _FORMAT],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            timeout=2.0,
        )
        if not result.stdout.strip():
            raise GpuUnavailableError("No NVIDIA GPU data was returned")
        return parse_nvidia_csv(result.stdout, datetime.now(UTC))


def select_gpu_provider() -> GpuProvider:
    """Select a supported local source without probing unavailable vendors."""
    executable = shutil.which("nvidia-smi")
    return NvidiaSmiProvider(executable) if executable else UnavailableProvider()
