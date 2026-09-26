"""Portable GPU provider contract and an NVIDIA CLI implementation."""

import csv
import json
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import replace
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


def _field_number(fields: Mapping[str, object], field: str) -> float | None:
    value = fields.get(field)
    return _optional_number(str(value)) if value is not None else None


def parse_nvidia_csv(
    output: str, sampled_at: datetime, *, source: str = "nvidia-smi"
) -> GpuSnapshot:
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
                source=source,
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


class IntelXpuSmiProvider:
    """Read documented Intel XPU Manager fields in one bounded CSV query."""

    name = "xpu-smi"

    def __init__(self, executable: str | None = None) -> None:
        self._executable = executable or shutil.which("xpu-smi")

    def is_available(self) -> bool:
        return self._executable is not None

    def collect(self) -> GpuSnapshot:
        if self._executable is None:
            raise GpuUnavailableError("xpu-smi is not installed")
        result = subprocess.run(
            [
                self._executable,
                "--query-gpu=index,name,utilization.gpu,memory.total,memory.used,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            timeout=2.0,
        )
        if not result.stdout.strip():
            raise GpuUnavailableError("No Intel GPU data was returned")
        return parse_nvidia_csv(result.stdout, datetime.now(UTC), source="xpu-smi")


def parse_rocm_json(output: str, sampled_at: datetime) -> GpuSnapshot:
    """Parse only recognized ROCm SMI fields; missing fields stay unavailable."""
    raw = json.loads(output)
    if not isinstance(raw, dict):
        raise ValueError("Unexpected ROCm SMI JSON root")
    devices: list[GpuMetrics] = []
    for key, fields in raw.items():
        if (
            not key.startswith("card")
            or not key[4:].isdigit()
            or not isinstance(fields, dict)
        ):
            continue
        name = next(
            (
                str(fields[item]).strip()
                for item in ("Card Series", "Device Name", "Card Model")
                if fields.get(item) not in (None, "N/A", "")
            ),
            "AMD GPU",
        )

        total = _field_number(fields, "VRAM Total Memory (B)")
        used = _field_number(fields, "VRAM Total Used Memory (B)")
        temperature = _field_number(fields, "Temperature (Sensor edge) (C)")
        if temperature is None:
            temperature = _field_number(fields, "Temperature (Sensor junction) (C)")
        devices.append(
            GpuMetrics(
                sampled_at,
                int(key[4:]),
                name,
                _field_number(fields, "GPU use (%)"),
                int(total) if total is not None else None,
                int(used) if used is not None else None,
                temperature,
                "rocm-smi",
            )
        )
    if not devices:
        raise GpuUnavailableError("No AMD GPU data was returned")
    return GpuSnapshot(sampled_at, tuple(devices))


class RocmSmiProvider:
    """Read-only ROCm SMI JSON query for available AMD GPU data."""

    name = "rocm-smi"

    def __init__(self, executable: str | None = None) -> None:
        self._executable = executable or shutil.which("rocm-smi")

    def is_available(self) -> bool:
        return self._executable is not None

    def collect(self) -> GpuSnapshot:
        if self._executable is None:
            raise GpuUnavailableError("rocm-smi is not installed")
        result = subprocess.run(
            [
                self._executable,
                "--showproductname",
                "--showuse",
                "--showmeminfo",
                "vram",
                "--showtemp",
                "--json",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            timeout=2.0,
        )
        return parse_rocm_json(result.stdout, datetime.now(UTC))


class CombinedGpuProvider:
    """Collect vendors independently so one failed source cannot hide another."""

    name = "multiple providers"

    def __init__(self, providers: tuple[GpuProvider, ...]) -> None:
        self.providers = providers

    def is_available(self) -> bool:
        return any(provider.is_available() for provider in self.providers)

    def collect(self) -> GpuSnapshot:
        devices: list[GpuMetrics] = []
        sampled_at = datetime.now(UTC)
        for provider in self.providers:
            try:
                sample = provider.collect()
            except (
                GpuUnavailableError,
                OSError,
                subprocess.SubprocessError,
                ValueError,
            ):
                continue
            offset = len(devices)
            devices.extend(
                replace(device, sampled_at=sampled_at, index=offset + index)
                for index, device in enumerate(sample.devices)
            )
        if not devices:
            raise GpuUnavailableError("No supported GPU data was returned")
        return GpuSnapshot(sampled_at, tuple(devices))


def select_gpu_provider() -> GpuProvider:
    """Select a supported local source without probing unavailable vendors."""
    providers: tuple[GpuProvider, ...] = (
        NvidiaSmiProvider(),
        RocmSmiProvider(),
        IntelXpuSmiProvider(),
    )
    available = tuple(provider for provider in providers if provider.is_available())
    if not available:
        return UnavailableProvider()
    return available[0] if len(available) == 1 else CombinedGpuProvider(available)
