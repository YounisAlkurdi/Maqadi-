"""In-memory rate limiter for invite-code join throttling."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain.errors import RateLimitedError
from app.domain.ports import Clock


@dataclass
class _AttemptState:
    failures: int = 0
    locked_until: datetime | None = None


class InMemoryRateLimiter:
    """Tracks failed attempts per key and locks for lock_seconds after max_failures."""

    def __init__(
        self,
        clock: Clock,
        *,
        max_failures: int = 5,
        lock_seconds: int = 900,
    ) -> None:
        self._clock = clock
        self._max_failures = max_failures
        self._lock_duration = timedelta(seconds=lock_seconds)
        self._states: dict[str, _AttemptState] = {}

    async def check(self, key: str) -> None:
        state = self._states.get(key)
        if state is None:
            return
        now = self._clock.now()
        if state.locked_until is not None:
            if now < state.locked_until:
                raise RateLimitedError("Too many failed join attempts. Try again later.")
            self._states.pop(key, None)

    async def record_failure(self, key: str) -> None:
        now = self._clock.now()
        state = self._states.get(key)
        if state is None:
            state = _AttemptState()
            self._states[key] = state
        elif state.locked_until is not None and now >= state.locked_until:
            state = _AttemptState()
            self._states[key] = state

        state.failures += 1
        if state.failures >= self._max_failures:
            state.locked_until = now + self._lock_duration

    async def reset(self, key: str) -> None:
        self._states.pop(key, None)
