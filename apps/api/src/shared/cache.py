import base64
import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings


logger = logging.getLogger(__name__)
LINK_CACHE_PREFIX = "link:"
DEFAULT_LINK_CACHE_TTL_SECONDS = 300
EXPIRATION_SKEW_SECONDS = 5
QR_CACHE_TTL_SECONDS = 3600


@dataclass(slots=True)
class CachedLink:
    """Serializable redirect metadata cached by short code."""

    link_id: int
    long_url: str
    expires_at: str | None
    is_active: bool
    is_password_protected: bool
    password_hash: str | None
    workspace_id: str | None
    flagged_reason: str | None


redis_client: Redis = Redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
    socket_connect_timeout=0.2,
    socket_timeout=0.2,
)


async def get_link_cache(short_code: str) -> CachedLink | None:
    """Return cached redirect metadata, or None on miss/Redis failure."""
    try:
        raw_value = await redis_client.get(_link_cache_key(short_code))
    except RedisError as exc:
        logger.warning("redis_link_cache_get_failed", extra={"error": str(exc)})
        return None

    if raw_value is None:
        return None

    try:
        payload = json.loads(raw_value)
        payload.setdefault("flagged_reason", None)
        return CachedLink(**payload)
    except (TypeError, ValueError) as exc:
        logger.warning(
            "redis_link_cache_decode_failed",
            extra={"short_code": short_code, "error": str(exc)},
        )
        await invalidate_link_cache(short_code)
        return None


async def set_link_cache(
    short_code: str,
    cached_link: CachedLink,
    ttl_seconds: int | None = None,
) -> None:
    """Cache redirect metadata for one short code."""
    ttl = ttl_seconds or _ttl_from_expires_at(cached_link.expires_at)
    if ttl <= 0:
        return

    try:
        await redis_client.setex(
            _link_cache_key(short_code),
            ttl,
            json.dumps(asdict(cached_link), separators=(",", ":")),
        )
    except RedisError as exc:
        logger.warning("redis_link_cache_set_failed", extra={"error": str(exc)})


async def invalidate_link_cache(short_code: str) -> None:
    """Remove one short-code cache entry, ignoring Redis outages."""
    try:
        await redis_client.delete(_link_cache_key(short_code))
    except RedisError as exc:
        logger.warning("redis_link_cache_delete_failed", extra={"error": str(exc)})


async def get_qr_cache(short_code: str, image_format: str) -> bytes | None:
    """Return cached QR image bytes, or None on miss/Redis failure."""
    try:
        raw_value = await redis_client.get(_qr_cache_key(short_code, image_format))
    except RedisError as exc:
        logger.warning("redis_qr_cache_get_failed", extra={"error": str(exc)})
        return None
    if raw_value is None:
        return None
    try:
        return base64.b64decode(raw_value.encode("ascii"))
    except ValueError as exc:
        logger.warning("redis_qr_cache_decode_failed", extra={"error": str(exc)})
        return None


async def set_qr_cache(
    short_code: str,
    image_format: str,
    image_bytes: bytes,
) -> None:
    """Cache QR image bytes as base64 text."""
    try:
        await redis_client.setex(
            _qr_cache_key(short_code, image_format),
            QR_CACHE_TTL_SECONDS,
            base64.b64encode(image_bytes).decode("ascii"),
        )
    except RedisError as exc:
        logger.warning("redis_qr_cache_set_failed", extra={"error": str(exc)})


def cached_link_from_model(link: object) -> CachedLink:
    """Build cached redirect metadata from a Link-like ORM object."""
    expires_at = getattr(link, "expires_at")
    workspace_id = getattr(link, "workspace_id")
    password_hash = getattr(link, "password_hash")
    return CachedLink(
        link_id=getattr(link, "id"),
        long_url=getattr(link, "destination_url"),
        expires_at=expires_at.isoformat() if expires_at is not None else None,
        is_active=getattr(link, "is_active"),
        is_password_protected=password_hash is not None,
        password_hash=password_hash,
        workspace_id=str(workspace_id) if workspace_id is not None else None,
        flagged_reason=getattr(link, "flagged_reason", None),
    )


async def increment_rate_limit(
    key: str,
    limit: int,
    window_seconds: int,
) -> tuple[bool, int]:
    """Increment a fixed-window counter and return whether it is allowed."""
    try:
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, window_seconds)
        return count <= limit, max(0, limit - count)
    except RedisError as exc:
        logger.warning("redis_rate_limit_failed", extra={"error": str(exc)})
        return True, limit


def _link_cache_key(short_code: str) -> str:
    """Return the Redis cache key for a short code."""
    return f"{LINK_CACHE_PREFIX}{short_code}"


def _qr_cache_key(short_code: str, image_format: str) -> str:
    """Return the Redis cache key for a QR image."""
    return f"qr:{image_format}:{short_code}"


def _ttl_from_expires_at(expires_at: str | None) -> int:
    """Return a TTL slightly shorter than link expiration."""
    if expires_at is None:
        return DEFAULT_LINK_CACHE_TTL_SECONDS

    expires_dt = datetime.fromisoformat(expires_at)
    if expires_dt.tzinfo is None:
        expires_dt = expires_dt.replace(tzinfo=UTC)
    seconds = int((expires_dt - datetime.now(UTC)).total_seconds())
    return max(0, seconds - EXPIRATION_SKEW_SECONDS)
