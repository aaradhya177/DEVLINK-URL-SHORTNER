import logging
import time
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from redis.exceptions import RedisError

from app.core.config import settings
from src.auth.security import get_current_user
from src.models.user import User
from src.shared.cache import redis_client


logger = logging.getLogger(__name__)


RATE_LIMITS = {
    "read": lambda: settings.rate_limit_read_requests,
    "write": lambda: settings.rate_limit_write_requests,
    "bulk": lambda: settings.rate_limit_bulk_requests,
}


def rate_limit(category: str) -> Callable[..., object]:
    """Build a FastAPI dependency enforcing per-user sliding-window limits."""

    async def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        """Return the current user when they are within the configured limit."""
        limit = RATE_LIMITS[category]()
        window_seconds = settings.rate_limit_window_seconds
        retry_after = await _check_sliding_window(
            user_id=str(current_user.id),
            category=category,
            limit=limit,
            window_seconds=window_seconds,
        )
        if retry_after is not None:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded.",
                headers={"Retry-After": str(retry_after)},
            )
        return current_user

    return dependency


async def _check_sliding_window(
    user_id: str,
    category: str,
    limit: int,
    window_seconds: int,
) -> int | None:
    """Return retry-after seconds when over limit, otherwise None."""
    now_ms = int(time.time() * 1000)
    window_ms = window_seconds * 1000
    key = f"rl:app:{category}:{user_id}"
    member = f"{now_ms}:{time.perf_counter_ns()}"

    try:
        result = await redis_client.eval(
            """
            redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, ARGV[1] - ARGV[2])
            redis.call('ZADD', KEYS[1], ARGV[1], ARGV[3])
            local count = redis.call('ZCARD', KEYS[1])
            redis.call('EXPIRE', KEYS[1], ARGV[4])
            local oldest = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
            return {count, oldest[2] or ARGV[1]}
            """,
            1,
            key,
            now_ms,
            window_ms,
            member,
            window_seconds,
        )
        count = int(result[0])
        if count <= limit:
            return None

        oldest_score = int(result[1])
        retry_after_ms = max(0, (oldest_score + window_ms) - now_ms)
        return max(1, int(retry_after_ms / 1000))
    except RedisError as exc:
        logger.warning("app_rate_limit_failed_open", extra={"error": str(exc)})
        return None
