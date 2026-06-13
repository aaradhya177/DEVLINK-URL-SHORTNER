import re
import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.links import repository
from src.links.schemas import LinkCreate, LinkUpdate
from src.models.link import Link
from src.shared.id_generator import SnowflakeGenerator, default_generator, encode_base62
from src.shared.url_utils import hash_long_url, normalize_url


ALIAS_PATTERN = re.compile(r"^[A-Za-z0-9-]{3,32}$")
RESERVED_ALIASES = {
    "admin",
    "api",
    "app",
    "auth",
    "dashboard",
    "health",
    "login",
    "logout",
    "register",
    "settings",
}


class LinkServiceError(Exception):
    """Base class for link service errors."""


class LinkNotFoundError(LinkServiceError):
    """Raised when a requested link does not exist."""


class AliasConflictError(LinkServiceError):
    """Raised when a custom alias is already taken."""


class InvalidAliasError(LinkServiceError):
    """Raised when a custom alias has an invalid format or reserved value."""


class InvalidExpirationError(LinkServiceError):
    """Raised when an expiration timestamp is invalid."""


async def create_link(
    session: AsyncSession,
    payload: LinkCreate,
    owner_id: uuid.UUID | None = None,
    generator: SnowflakeGenerator = default_generator,
) -> Link:
    """Create or deduplicate a short link."""
    expires_at = _validate_expiration(payload.expires_at)
    normalized_url = normalize_url(
        payload.destination_url,
        strip_tracking_params=payload.strip_tracking_params,
    )
    long_url_hash = hash_long_url(normalized_url)

    if payload.custom_alias is None:
        existing_link = await repository.get_link_by_long_url_hash(
            session,
            long_url_hash=long_url_hash,
            owner_id=owner_id,
            now=datetime.now(UTC),
        )
        if existing_link is not None:
            return existing_link
        link_id = generator.generate()
        short_code = encode_base62(link_id)
    else:
        short_code = _validate_custom_alias(payload.custom_alias)
        existing_alias = await repository.get_link_by_short_code(session, short_code)
        if existing_alias is not None:
            raise AliasConflictError("Custom alias is already in use.")
        link_id = generator.generate()

    link = Link(
        id=link_id,
        owner_id=owner_id,
        short_code=short_code,
        destination_url=normalized_url,
        long_url_hash=long_url_hash,
        title=payload.title,
        expires_at=expires_at,
        is_active=True,
    )

    try:
        created_link = await repository.create_link(session, link)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise AliasConflictError("Short code is already in use.") from exc

    return created_link


async def get_link(
    session: AsyncSession,
    link_id: int,
    owner_id: uuid.UUID | None = None,
) -> Link:
    """Return a link by ID or raise when it cannot be found."""
    link = await repository.get_link_by_id(session, link_id, owner_id=owner_id)
    if link is None:
        raise LinkNotFoundError("Link not found.")
    return link


async def list_links(
    session: AsyncSession,
    owner_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
    include_inactive: bool = False,
) -> list[Link]:
    """Return paginated links for the current placeholder owner."""
    links = await repository.list_links(
        session,
        owner_id=owner_id,
        limit=limit,
        offset=offset,
        include_inactive=include_inactive,
    )
    return list(links)


async def update_link(
    session: AsyncSession,
    link_id: int,
    payload: LinkUpdate,
    owner_id: uuid.UUID | None = None,
) -> Link:
    """Update link metadata, destination, alias, activation, or expiration."""
    link = await get_link(session, link_id, owner_id=owner_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "expires_at" in update_data:
        link.expires_at = _validate_expiration(payload.expires_at)

    if payload.destination_url is not None:
        normalized_url = normalize_url(
            payload.destination_url,
            strip_tracking_params=payload.strip_tracking_params,
        )
        link.destination_url = normalized_url
        link.long_url_hash = hash_long_url(normalized_url)

    if payload.custom_alias is not None:
        next_short_code = _validate_custom_alias(payload.custom_alias)
        if next_short_code != link.short_code:
            existing_alias = await repository.get_link_by_short_code(
                session,
                next_short_code,
            )
            if existing_alias is not None:
                raise AliasConflictError("Custom alias is already in use.")
            link.short_code = next_short_code

    if "title" in update_data:
        link.title = payload.title
    if payload.is_active is not None:
        link.is_active = payload.is_active

    link.updated_at = datetime.now(UTC)

    try:
        updated_link = await repository.update_link(session, link)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise AliasConflictError("Short code is already in use.") from exc

    return updated_link


async def soft_delete_link(
    session: AsyncSession,
    link_id: int,
    owner_id: uuid.UUID | None = None,
) -> Link:
    """Deactivate a link instead of physically deleting it."""
    link = await get_link(session, link_id, owner_id=owner_id)
    deleted_link = await repository.soft_delete_link(session, link, datetime.now(UTC))
    await session.commit()
    return deleted_link


def _validate_custom_alias(alias: str) -> str:
    """Return a valid alias or raise a service error."""
    normalized_alias = alias.strip()
    if not ALIAS_PATTERN.fullmatch(normalized_alias):
        raise InvalidAliasError(
            "Custom alias must be 3-32 characters using letters, numbers, or hyphens."
        )
    if normalized_alias.lower() in RESERVED_ALIASES:
        raise InvalidAliasError("Custom alias is reserved.")
    return normalized_alias


def _validate_expiration(expires_at: datetime | None) -> datetime | None:
    """Return a future expiration timestamp or raise a service error."""
    if expires_at is None:
        return None

    now = datetime.now(UTC)
    comparable_expires_at = (
        expires_at.replace(tzinfo=UTC) if expires_at.tzinfo is None else expires_at
    )
    if comparable_expires_at <= now:
        raise InvalidExpirationError("expires_at must be in the future.")
    return comparable_expires_at
