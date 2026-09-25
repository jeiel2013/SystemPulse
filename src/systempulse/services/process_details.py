"""Read expensive process facts only for a selected, verified process instance."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime

import psutil

from systempulse.domain.processes import ProcessDetails, ProcessIdentity


def _optional[T](call: Callable[[], T]) -> T | None:
    try:
        return call()
    except (psutil.AccessDenied, OSError, NotImplementedError):
        return None


def _created_at(process: psutil.Process) -> datetime:
    return datetime.fromtimestamp(process.create_time(), UTC)


class ProcessDetailsService:
    """Isolate detailed psutil calls from the UI event loop."""

    async def read(self, identity: ProcessIdentity) -> ProcessDetails | None:
        """Return details only if PID still refers to the selected instance."""
        return await asyncio.to_thread(self._read_sync, identity)

    @staticmethod
    def _read_sync(identity: ProcessIdentity) -> ProcessDetails | None:
        try:
            process = psutil.Process(identity.pid)
            if _created_at(process) != identity.created_at:
                return None
            with process.oneshot():
                name = _optional(process.name)
                status = _optional(process.status)
                user = _optional(process.username)
                threads = _optional(process.num_threads)
                parent_pid = _optional(process.ppid)
                executable = _optional(process.exe)
                command = _optional(process.cmdline)
            # psutil caches create_time on each Process object; instantiate again.
            if _created_at(psutil.Process(identity.pid)) != identity.created_at:
                return None
            return ProcessDetails(
                sampled_at=datetime.now(UTC),
                identity=identity,
                name=name or None,
                status=status or None,
                user=user or None,
                threads=threads,
                parent_pid=parent_pid,
                executable=executable or None,
                command_line=tuple(command) if command is not None else None,
            )
        except (
            psutil.NoSuchProcess,
            psutil.ZombieProcess,
            psutil.AccessDenied,
            OSError,
            OverflowError,
            ValueError,
        ):
            return None
