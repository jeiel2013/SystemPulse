"""Build an on-demand process tree without slowing periodic scans."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime

import psutil

from systempulse.domain.processes import ProcessIdentity


@dataclass(frozen=True, slots=True)
class ProcessTreeEntry:
    pid: int
    name: str
    parent_pid: int | None
    create_time: datetime | None

    @property
    def identity(self) -> ProcessIdentity | None:
        return ProcessIdentity(self.pid, self.create_time) if self.create_time else None


@dataclass(frozen=True, slots=True)
class ProcessTreeRow:
    entry: ProcessTreeEntry
    depth: int


def build_tree(entries: tuple[ProcessTreeEntry, ...]) -> tuple[ProcessTreeRow, ...]:
    """Order a single scan by parent, guarding cycles and PID reuse."""
    by_pid = {entry.pid: entry for entry in entries}
    children: dict[int, list[ProcessTreeEntry]] = {}
    roots: list[ProcessTreeEntry] = []
    for entry in entries:
        parent = by_pid.get(entry.parent_pid) if entry.parent_pid is not None else None
        valid_parent = (
            parent is not None
            and parent.pid != entry.pid
            and (
                parent.create_time is None
                or entry.create_time is None
                or parent.create_time <= entry.create_time
            )
        )
        if valid_parent and parent is not None:
            children.setdefault(parent.pid, []).append(entry)
        else:
            roots.append(entry)
    rows: list[ProcessTreeRow] = []
    visited: set[int] = set()

    def visit(entry: ProcessTreeEntry, depth: int) -> None:
        if entry.pid in visited:
            return
        visited.add(entry.pid)
        rows.append(ProcessTreeRow(entry, depth))
        for child in sorted(
            children.get(entry.pid, ()),
            key=lambda item: (item.name.casefold(), item.pid),
        ):
            visit(child, depth + 1)

    for root in sorted(roots, key=lambda item: (item.name.casefold(), item.pid)):
        visit(root, 0)
    for entry in entries:
        visit(entry, 0)
    return tuple(rows)


def _scan_tree() -> tuple[ProcessTreeEntry, ...]:
    entries: list[ProcessTreeEntry] = []
    for process in psutil.process_iter(
        attrs=["pid", "name", "ppid", "create_time"], ad_value=None
    ):
        try:
            info = process.info
            created = info.get("create_time")
            entries.append(
                ProcessTreeEntry(
                    pid=int(info["pid"]),
                    name=str(info.get("name") or "Unknown"),
                    parent_pid=int(info["ppid"])
                    if info.get("ppid") is not None
                    else None,
                    create_time=datetime.fromtimestamp(created, UTC)
                    if created is not None
                    else None,
                )
            )
        except (
            psutil.AccessDenied,
            psutil.NoSuchProcess,
            psutil.ZombieProcess,
            OSError,
            TypeError,
            ValueError,
        ):
            continue
    return tuple(entries)


class ProcessTreeService:
    """Scan parent relationships only when the user requests the tree."""

    async def read(self) -> tuple[ProcessTreeRow, ...]:
        return await asyncio.to_thread(lambda: build_tree(_scan_tree()))
