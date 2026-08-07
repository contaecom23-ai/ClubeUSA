from collections import defaultdict
from datetime import datetime, timedelta
from threading import Lock


class InMemoryRateLimiter:
    """
    Thread-safe sliding-window rate limiter.
    Good for a single process (1k users). For multi-worker deployments, swap
    this for a Redis-backed implementation — see DECISOES.md.
    """

    def __init__(self) -> None:
        self._windows: dict[str, list[datetime]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str, max_calls: int, period_seconds: int) -> bool:
        now = datetime.now()
        cutoff = now - timedelta(seconds=period_seconds)
        with self._lock:
            calls = [t for t in self._windows[key] if t > cutoff]
            if len(calls) >= max_calls:
                return False
            calls.append(now)
            self._windows[key] = calls
            return True

    def reset(self, key: str) -> None:
        with self._lock:
            self._windows.pop(key, None)


rate_limiter = InMemoryRateLimiter()
