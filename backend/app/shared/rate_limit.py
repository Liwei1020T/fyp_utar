from __future__ import annotations

from collections import defaultdict
from collections import deque
from collections.abc import Callable
from threading import Lock
from time import monotonic

from app.shared.errors import TooManyRequestsError


class SlidingWindowRateLimiter:
    def __init__(
        self,
        *,
        limit: int,
        window_seconds: int,
        now: Callable[[], float] = monotonic,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._now = now
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        # ponytail: process-local keys persist; use a shared gateway limiter for
        # multi-worker or long-lived production deployments.
        self._lock = Lock()

    def check(self, key: str) -> None:
        now = self._now()
        cutoff = now - self.window_seconds
        with self._lock:
            attempts = self._attempts[key]
            while attempts and attempts[0] <= cutoff:
                attempts.popleft()
            if len(attempts) >= self.limit:
                raise TooManyRequestsError()
            attempts.append(now)

    def clear(self, key: str | None = None) -> None:
        with self._lock:
            if key is None:
                self._attempts.clear()
            else:
                self._attempts.pop(key, None)
