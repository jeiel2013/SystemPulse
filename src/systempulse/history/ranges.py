"""Shared terminal history ranges."""

from datetime import timedelta
from enum import StrEnum


class HistoryRange(StrEnum):
    TEN_MINUTES = "10m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    SIX_HOURS = "6h"
    ONE_DAY = "24h"
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"

    @property
    def duration(self) -> timedelta:
        return {
            self.TEN_MINUTES: timedelta(minutes=10),
            self.THIRTY_MINUTES: timedelta(minutes=30),
            self.ONE_HOUR: timedelta(hours=1),
            self.SIX_HOURS: timedelta(hours=6),
            self.ONE_DAY: timedelta(days=1),
            self.SEVEN_DAYS: timedelta(days=7),
            self.THIRTY_DAYS: timedelta(days=30),
        }[self]
