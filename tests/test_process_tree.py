"""Process ancestry is ordered on demand and rejects reused parent PIDs."""

from datetime import UTC, datetime, timedelta

from systempulse.services.process_tree import ProcessTreeEntry, build_tree


def test_tree_orders_parent_before_child_and_rejects_newer_parent() -> None:
    at = datetime(2026, 1, 1, tzinfo=UTC)
    parent = ProcessTreeEntry(10, "parent", None, at)
    child = ProcessTreeEntry(11, "child", 10, at + timedelta(seconds=1))
    reused_parent = ProcessTreeEntry(12, "new parent", None, at + timedelta(hours=1))
    older_child = ProcessTreeEntry(13, "older child", 12, at)

    rows = build_tree((child, older_child, parent, reused_parent))
    positions = {row.entry.pid: row for row in rows}

    assert positions[10].depth == 0
    assert positions[11].depth == 1
    assert positions[13].depth == 0
    assert len(rows) == 4
