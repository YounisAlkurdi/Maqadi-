"""System clock implementation."""

from datetime import UTC, datetime


class SystemClock:
    """UTC wall-clock implementation of the Clock port."""

    def now(self) -> datetime:
        return datetime.now(UTC)
