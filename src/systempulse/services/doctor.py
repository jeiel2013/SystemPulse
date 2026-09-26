"""Evidence-based checks for the functionality currently shipped."""

import asyncio
import sys
from dataclasses import dataclass
from enum import StrEnum

from systempulse.domain.availability import Availability
from systempulse.domain.snapshots import SystemSnapshot
from systempulse.platform.paths import configuration_path, history_database_path
from systempulse.services.monitor import create_default_session
from systempulse.version import get_version

_SUPPORTED_PLATFORMS = frozenset({"win32", "linux", "darwin"})
_CORE_COLLECTORS = ("cpu", "memory", "processes", "system")


class CheckState(StrEnum):
    """Severity of a self-check result."""

    PASS = "ok"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    """One visible check with a concise explanation."""

    name: str
    state: CheckState
    detail: str


@dataclass(frozen=True, slots=True)
class DoctorReport:
    """A self-check report for the installed program and current machine."""

    version: str
    checks: tuple[DoctorCheck, ...]

    @property
    def exit_code(self) -> int:
        """Fail only when a required capability is broken."""
        return int(any(check.state == CheckState.FAIL for check in self.checks))


def assess_environment(
    snapshot: SystemSnapshot,
    *,
    python_version: tuple[int, int, int],
    platform_tag: str,
    interactive_terminal: bool,
    color_system: str | None,
    version: str,
) -> DoctorReport:
    """Turn observed collector results and runtime facts into checks."""
    python_label = ".".join(str(part) for part in python_version)
    checks = [
        DoctorCheck(
            "Python",
            CheckState.PASS if python_version >= (3, 12, 0) else CheckState.FAIL,
            python_label,
        ),
        DoctorCheck(
            "Platform",
            CheckState.PASS
            if platform_tag in _SUPPORTED_PLATFORMS
            else CheckState.WARN,
            snapshot.system.platform_name
            if snapshot.system is not None
            else platform_tag,
        ),
    ]
    statuses = {status.name: status for status in snapshot.collector_statuses}
    for name in _CORE_COLLECTORS:
        status = statuses.get(name)
        if status is None:
            checks.append(
                DoctorCheck(f"{name} collector", CheckState.FAIL, "Not registered")
            )
            continue
        if status.availability == Availability.AVAILABLE:
            state = CheckState.PASS
        elif status.availability in {Availability.WARMING_UP, Availability.DISABLED}:
            state = CheckState.WARN
        else:
            state = CheckState.FAIL
        detail = status.availability.value.replace("_", " ")
        if status.reason:
            detail += f" ({status.reason})"
        checks.append(DoctorCheck(f"{name} collector", state, detail))

    gpu_status = statuses.get("gpu")
    if gpu_status is not None:
        detail = gpu_status.availability.value.replace("_", " ")
        if snapshot.gpu is not None:
            detail += f" ({snapshot.gpu.devices[0].source})"
        elif gpu_status.reason:
            detail += f" ({gpu_status.reason})"
        checks.append(
            DoctorCheck(
                "GPU provider",
                CheckState.PASS
                if gpu_status.availability == Availability.AVAILABLE
                else CheckState.WARN,
                detail,
            )
        )

    checks.append(
        DoctorCheck(
            "Interactive terminal",
            CheckState.PASS if interactive_terminal else CheckState.WARN,
            "available"
            if interactive_terminal
            else "TUI requires an interactive terminal",
        )
    )
    if interactive_terminal:
        checks.append(
            DoctorCheck(
                "Terminal colors",
                CheckState.PASS if color_system is not None else CheckState.WARN,
                color_system or "No color capability detected",
            )
        )
    return DoctorReport(version=version, checks=tuple(checks))


def run_doctor(*, interactive_terminal: bool, color_system: str | None) -> DoctorReport:
    """Check actual collectors after CPU rates have had time to initialize."""
    session = create_default_session()

    async def sample_and_close() -> SystemSnapshot:
        try:
            return await session.sample_after_warmup()
        finally:
            await session.close()

    snapshot = asyncio.run(sample_and_close())
    report = assess_environment(
        snapshot,
        python_version=(
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro,
        ),
        platform_tag=sys.platform,
        interactive_terminal=interactive_terminal,
        color_system=color_system,
        version=get_version(),
    )
    return DoctorReport(
        report.version,
        (
            *report.checks,
            DoctorCheck(
                "Configuration",
                CheckState.WARN if session.config_error else CheckState.PASS,
                f"{configuration_path()} "
                f"({session.config_error or 'defaults or valid local TOML'})",
            ),
            DoctorCheck(
                "History database",
                CheckState.WARN if session.history_error else CheckState.PASS,
                f"{history_database_path()} ({session.history_error or 'accessible'})",
            ),
        ),
    )
