"""SQLite history with bounded raw samples and progressively coarser buckets."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock

from sqlalchemy import (
    DateTime,
    Float,
    Integer,
    String,
    create_engine,
    delete,
    event,
    select,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from systempulse.domain.snapshots import SystemSnapshot


class Base(DeclarativeBase):
    pass


class MetricRow(Base):
    """One raw observation or an average of an explicitly named time bucket."""

    __tablename__ = "metric_history"

    tier: Mapped[str] = mapped_column(String(16), primary_key=True)
    bucket_epoch: Mapped[int] = mapped_column(Integer, primary_key=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    cpu_percent: Mapped[float | None] = mapped_column(Float())
    memory_percent: Mapped[float | None] = mapped_column(Float())
    disk_percent: Mapped[float | None] = mapped_column(Float())
    download_bytes_per_second: Mapped[float | None] = mapped_column(Float())
    upload_bytes_per_second: Mapped[float | None] = mapped_column(Float())


@dataclass(frozen=True, slots=True)
class HistoryPoint:
    """A stored observation or mean of available observations in a time bucket."""

    observed_at: datetime
    cpu_percent: float | None
    memory_percent: float | None
    disk_percent: float | None
    download_bytes_per_second: float | None
    upload_bytes_per_second: float | None


_RAW = "raw"
_MINUTE = "minute"
_QUARTER_HOUR = "quarter_hour"


class HistoryStore:
    """Persist summary metrics without retaining process names or command lines."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._engine: Engine | None = None
        self._lock = Lock()
        self._last_compaction: datetime | None = None

    def _database(self) -> Engine:
        if self._engine is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            engine = create_engine(f"sqlite:///{self.path.as_posix()}")

            @event.listens_for(engine, "connect")
            def configure_sqlite(connection: object, _record: object) -> None:
                cursor = connection.cursor()  # type: ignore[attr-defined]
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA busy_timeout=3000")
                cursor.close()

            Base.metadata.create_all(engine)
            self._engine = engine
        return self._engine

    def close(self) -> None:
        """Release SQLite handles after the monitoring session exits."""
        with self._lock:
            if self._engine is not None:
                self._engine.dispose()
                self._engine = None

    def record(self, snapshot: SystemSnapshot) -> None:
        """Write one small summary and periodically compact older data."""
        with self._lock, Session(self._database()) as session:
            at = snapshot.created_at
            epoch = int(at.timestamp() * 1000)
            cpu = snapshot.metrics.cpu
            memory = snapshot.metrics.memory
            disk = snapshot.metrics.disk
            network = snapshot.metrics.network
            row = MetricRow(
                tier=_RAW,
                bucket_epoch=epoch,
                observed_at=at.replace(tzinfo=None),
                cpu_percent=cpu.total_percent if cpu else None,
                memory_percent=memory.percent if memory else None,
                disk_percent=disk.percent if disk else None,
                download_bytes_per_second=(
                    network.download_bytes_per_second if network else None
                ),
                upload_bytes_per_second=(
                    network.upload_bytes_per_second if network else None
                ),
            )
            session.merge(row)
            if self._last_compaction is None or at - self._last_compaction >= timedelta(
                minutes=1
            ):
                self._compact(session, at)
                self._last_compaction = at
            session.commit()

    def query(
        self, duration: timedelta, *, now: datetime | None = None
    ) -> tuple[HistoryPoint, ...]:
        """Return raw and rollup points in chronological order without duplicates."""
        if duration <= timedelta(0):
            raise ValueError("duration must be positive")
        end = now or datetime.now(UTC)
        cutoff = int((end - duration).timestamp() * 1000)
        with self._lock, Session(self._database()) as session:
            rows = session.scalars(
                select(MetricRow)
                .where(MetricRow.bucket_epoch >= cutoff)
                .order_by(MetricRow.bucket_epoch)
            ).all()
        return tuple(
            HistoryPoint(
                row.observed_at.replace(tzinfo=UTC),
                row.cpu_percent,
                row.memory_percent,
                row.disk_percent,
                row.download_bytes_per_second,
                row.upload_bytes_per_second,
            )
            for row in rows
        )

    def compact(self, *, now: datetime | None = None) -> None:
        """Apply retention immediately, useful for maintenance and tests."""
        at = now or datetime.now(UTC)
        with self._lock:
            with Session(self._database()) as session:
                self._compact(session, at)
                session.commit()
            self._last_compaction = at

    @classmethod
    def _compact(cls, session: Session, now: datetime) -> None:
        cls._rollup(
            session,
            _RAW,
            _MINUTE,
            60_000,
            int((now - timedelta(minutes=10)).timestamp() * 1000),
        )
        cls._rollup(
            session,
            _MINUTE,
            _QUARTER_HOUR,
            900_000,
            int((now - timedelta(hours=24)).timestamp() * 1000),
        )
        session.execute(
            delete(MetricRow).where(
                MetricRow.tier == _QUARTER_HOUR,
                MetricRow.bucket_epoch
                < int((now - timedelta(days=30)).timestamp() * 1000),
            )
        )

    @staticmethod
    def _rollup(
        session: Session, source: str, target: str, width: int, cutoff: int
    ) -> None:
        cutoff = cutoff // width * width
        rows = session.scalars(
            select(MetricRow)
            .where(MetricRow.tier == source, MetricRow.bucket_epoch < cutoff)
            .order_by(MetricRow.bucket_epoch)
        ).all()
        groups: dict[int, list[MetricRow]] = {}
        for row in rows:
            groups.setdefault(row.bucket_epoch // width * width, []).append(row)
        for epoch, members in groups.items():
            session.merge(
                MetricRow(
                    tier=target,
                    bucket_epoch=epoch,
                    observed_at=datetime.fromtimestamp(epoch / 1000, UTC).replace(
                        tzinfo=None
                    ),
                    cpu_percent=_mean(members, "cpu_percent"),
                    memory_percent=_mean(members, "memory_percent"),
                    disk_percent=_mean(members, "disk_percent"),
                    download_bytes_per_second=_mean(
                        members, "download_bytes_per_second"
                    ),
                    upload_bytes_per_second=_mean(members, "upload_bytes_per_second"),
                )
            )
        if rows:
            session.execute(
                delete(MetricRow).where(
                    MetricRow.tier == source, MetricRow.bucket_epoch < cutoff
                )
            )


def _mean(rows: list[MetricRow], field: str) -> float | None:
    values = [value for row in rows if (value := getattr(row, field)) is not None]
    return sum(values) / len(values) if values else None
