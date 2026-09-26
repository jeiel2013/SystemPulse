"""Measure live collection and headless TUI cost on the current host."""

import argparse
import asyncio
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from statistics import median
from time import perf_counter

import psutil

from systempulse.services.monitor import create_default_session
from systempulse.tui.app import PulseApp


async def measure_collectors(seconds: float) -> list[float]:
    """Run the normal due-collector cadence without a terminal interface."""
    session = create_default_session()
    durations: list[float] = []
    try:
        deadline = perf_counter() + seconds
        while perf_counter() < deadline:
            started = perf_counter()
            await session.sample_due()
            durations.append(perf_counter() - started)
            await asyncio.sleep(max(0.0, 1.0 - (perf_counter() - started)))
    finally:
        await session.close()
    return durations


async def measure_tui(seconds: float) -> None:
    """Run the real Textual application with its collector loop headlessly."""
    session = create_default_session()
    app = PulseApp(session=session)
    try:
        async with app.run_test(size=(100, 30)):
            await asyncio.sleep(seconds)
    finally:
        await session.close()


async def run_phase(label: str, seconds: float, data_dir: Path) -> None:
    os.environ["SYSTEMPULSE_DATA_DIR"] = str(data_dir)
    process = psutil.Process()
    before = process.cpu_times()
    started = perf_counter()
    durations = await measure_collectors(seconds) if label == "collectors" else None
    if label == "tui":
        await measure_tui(seconds)
    elapsed = perf_counter() - started
    after = process.cpu_times()
    cpu_seconds = (after.user + after.system) - (before.user + before.system)
    rss_mib = process.memory_info().rss / 1024**2
    database = data_dir / "history.sqlite3"
    rows = 0
    if database.is_file():
        with closing(sqlite3.connect(database)) as connection:
            rows = connection.execute("SELECT count(*) FROM metric_history").fetchone()[
                0
            ]
    db_kib = (
        sum(path.stat().st_size for path in data_dir.glob("history.sqlite3*")) / 1024
    )
    print(
        f"{label}: {elapsed:.1f}s wall, {cpu_seconds:.2f}s CPU "
        f"({cpu_seconds / elapsed * 100:.1f}% of one core), "
        f"{rss_mib:.1f} MiB RSS, {rows} history rows, {db_kib:.1f} KiB SQLite"
    )
    if durations:
        print(
            f"  cycles: {len(durations)}, median {median(durations):.3f}s, "
            f"max {max(durations):.3f}s"
        )


async def main(seconds: float) -> None:
    """Measure both modes using disposable history directories."""
    with tempfile.TemporaryDirectory(prefix="systempulse-benchmark-") as directory:
        base = Path(directory)
        await run_phase("collectors", seconds, base / "collectors")
        await run_phase("tui", seconds, base / "tui")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=10.0)
    arguments = parser.parse_args()
    if arguments.seconds < 2:
        parser.error("--seconds must be at least 2")
    asyncio.run(main(arguments.seconds))
