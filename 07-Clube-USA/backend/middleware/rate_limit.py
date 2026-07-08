import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException


class SlidingWindowLimiter:
    """In-memory sliding window rate limiter keyed by IP.

    NOTE: Works for a single process only. Before scaling past one process
    instance, migrate to a Redis-backed solution (e.g. redis-py + Lua script).
    """

    def __init__(self, max_calls: int, period_seconds: int) -> None:
        self._max = max_calls
        self._period = period_seconds
        self._log: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            window_start = now - self._period
            calls = [t for t in self._log[key] if t > window_start]
            if len(calls) >= self._max:
                raise HTTPException(
                    status_code=429,
                    detail="Muitas tentativas. Aguarde alguns minutos e tente novamente.",
                    headers={"Retry-After": str(self._period)},
                )
            calls.append(now)
            self._log[key] = calls


login_limiter = SlidingWindowLimiter(max_calls=5, period_seconds=300)
register_limiter = SlidingWindowLimiter(max_calls=3, period_seconds=3600)
