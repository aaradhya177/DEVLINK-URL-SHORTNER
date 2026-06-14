from redis.exceptions import RedisError

from src.shared import rate_limiter


class FakeSlidingWindowRedis:
    """Small Redis eval fake for the sliding-window Lua script."""

    def __init__(self) -> None:
        self.scores: dict[str, list[int]] = {}

    async def eval(
        self,
        _: str,
        key_count: int,
        key: str,
        now_ms: int,
        window_ms: int,
        member: str,
        window_seconds: int,
    ) -> list[int]:
        """Mimic the count/oldest return shape used by the limiter."""
        assert key_count == 1
        assert member
        assert window_seconds > 0
        scores = [
            score for score in self.scores.setdefault(key, []) if score >= now_ms - window_ms
        ]
        scores.append(now_ms)
        self.scores[key] = sorted(scores)
        return [len(scores), self.scores[key][0]]


class BrokenRedis:
    """Redis fake that forces fail-open behavior."""

    async def eval(self, *_: object) -> object:
        """Raise like a Redis outage."""
        raise RedisError("redis down")


async def test_sliding_window_allows_until_limit(monkeypatch) -> None:
    """Requests inside the limit should not produce Retry-After."""
    monkeypatch.setattr(rate_limiter, "redis_client", FakeSlidingWindowRedis())
    monkeypatch.setattr(rate_limiter.time, "time", lambda: 1000.0)

    assert await rate_limiter._check_sliding_window("u1", "write", 2, 60) is None
    assert await rate_limiter._check_sliding_window("u1", "write", 2, 60) is None


async def test_sliding_window_returns_retry_after_when_limited(monkeypatch) -> None:
    """The first request over limit should return a retry delay."""
    monkeypatch.setattr(rate_limiter, "redis_client", FakeSlidingWindowRedis())
    monkeypatch.setattr(rate_limiter.time, "time", lambda: 1000.0)

    assert await rate_limiter._check_sliding_window("u1", "write", 1, 60) is None
    retry_after = await rate_limiter._check_sliding_window("u1", "write", 1, 60)

    assert retry_after == 60


async def test_sliding_window_fails_open_on_redis_error(monkeypatch) -> None:
    """Redis outages should not block application reads/writes."""
    monkeypatch.setattr(rate_limiter, "redis_client", BrokenRedis())

    assert await rate_limiter._check_sliding_window("u1", "write", 1, 60) is None
