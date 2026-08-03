from __future__ import annotations

import pytest

from app.shared.errors import TooManyRequestsError
from app.shared.rate_limit import SlidingWindowRateLimiter


def test_sliding_window_releases_expired_attempts() -> None:
    now = [100.0]
    limiter = SlidingWindowRateLimiter(
        limit=2,
        window_seconds=10,
        now=lambda: now[0],
    )

    limiter.check("client")
    limiter.check("client")
    with pytest.raises(TooManyRequestsError):
        limiter.check("client")

    now[0] = 111.0
    limiter.check("client")
