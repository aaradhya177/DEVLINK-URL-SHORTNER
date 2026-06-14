import re
import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.security import hash_password
from src.links import repository
from src.links.schemas import (
    BulkLinkCreateRequest,
    BulkLinkResult,
    LinkCreate,
    LinkResponse,
    LinkUpdate,
)
from src.models.link import Link
from src.models.user import User
from src.shared.cache import cached_link_from_model, invalidate_link_cache, set_link_cache
from src.shared.id_generator import SnowflakeGenerator, default_generator, encode_base62
from src.shared.url_utils import hash_long_url, normalize_url
from src.workspaces.permissions import user_has_workspace_role


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


class LinkPermissionError(LinkServiceError):
    """Raised when a user cannot access or modify a link."""


async def create_link(
    session: AsyncSession,
    payload: LinkCreate,
    current_user: User,
    generator: SnowflakeGenerator = default_generator,
) -> Link:
    """Create or deduplicate a short link."""
    if payload.workspace_id is not None:
        allowed = await user_has_workspace_role(
            session,
            payload.workspace_id,
            current_user.id,
            "editor",
        )
        if not allowed:
            raise LinkPermissionError("Insufficient workspace permissions.")

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
            owner_id=current_user.id,
            workspace_id=payload.workspace_id,
            now=datetime.now(UTC),
        )
        if existing_link is not None:
            await set_link_cache(
                existing_link.short_code,
                cached_link_from_model(existing_link),
            )
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
        workspace_id=payload.workspace_id,
        owner_id=current_user.id,
        short_code=short_code,
        destination_url=normalized_url,
        long_url_hash=long_url_hash,
        title=payload.title,
        password_hash=hash_password(payload.password) if payload.password else None,
        expires_at=expires_at,
        is_active=True,
    )

    try:
        created_link = await repository.create_link(session, link)
        await session.commit()
        await set_link_cache(
            created_link.short_code,
            cached_link_from_model(created_link),
        )
    except IntegrityError as exc:
        await session.rollback()
        raise AliasConflictError("Short code is already in use.") from exc

    return created_link


async def bulk_create_links(
    session: AsyncSession,
    payload: BulkLinkCreateRequest,
    current_user: User,
    generator: SnowflakeGenerator = default_generator,
) -> list[BulkLinkResult]:
    """Create many links with batched dedup lookup and per-item results."""
    if payload.workspace_id is not None:
        allowed = await user_has_workspace_role(
            session,
            payload.workspace_id,
            current_user.id,
            "editor",
        )
        if not allowed:
            raise LinkPermissionError("Insufficient workspace permissions.")

    now = datetime.now(UTC)
    prepared: list[tuple[int, str, str, str]] = []
    results: dict[int, BulkLinkResult] = {}
    for index, raw_url in enumerate(payload.urls):
        try:
            if not raw_url.startswith(("http://", "https://")):
                raise ValueError("URL must start with http:// or https://.")
            normalized_url = normalize_url(
                raw_url,
                strip_tracking_params=payload.strip_tracking_params,
            )
            long_url_hash = hash_long_url(normalized_url)
            prepared.append((index, raw_url, normalized_url, long_url_hash))
        except ValueError as exc:
            results[index] = BulkLinkResult(
                index=index,
                status="error",
                url=raw_url,
                error=str(exc),
            )

    existing_by_hash: dict[str, Link] = {}
    hashes = {item[3] for item in prepared}
    existing_links = await repository.get_links_by_long_url_hashes(
        session,
        hashes,
        owner_id=current_user.id,
        workspace_id=payload.workspace_id,
        now=now,
    )
    for existing_link in existing_links:
        existing_by_hash.setdefault(existing_link.long_url_hash, existing_link)

    new_links: list[tuple[int, str, Link]] = []
    seen_hashes: dict[str, Link] = {}
    for index, raw_url, normalized_url, long_url_hash in prepared:
        existing_link = existing_by_hash.get(long_url_hash) or seen_hashes.get(
            long_url_hash
        )
        if existing_link is not None:
            results[index] = BulkLinkResult(
                index=index,
                status="deduped",
                url=raw_url,
                link=LinkResponse.model_validate(existing_link),
            )
            continue

        link_id = generator.generate()
        link = Link(
            id=link_id,
            workspace_id=payload.workspace_id,
            owner_id=current_user.id,
            short_code=encode_base62(link_id),
            destination_url=normalized_url,
            long_url_hash=long_url_hash,
            is_active=True,
            click_count=0,
            created_at=now,
            updated_at=now,
        )
        session.add(link)
        new_links.append((index, raw_url, link))
        seen_hashes[long_url_hash] = link

    if new_links:
        await session.commit()
        for index, raw_url, link in new_links:
            await set_link_cache(link.short_code, cached_link_from_model(link))
            results[index] = BulkLinkResult(
                index=index,
                status="created",
                url=raw_url,
                link=LinkResponse.model_validate(link),
            )

    return [results[index] for index in range(len(payload.urls))]


async def get_link(
    session: AsyncSession,
    link_id: int,
    current_user: User,
) -> Link:
    """Return a link by ID when the current user can read it."""
    link = await repository.get_link_by_id(session, link_id)
    if link is None:
        raise LinkNotFoundError("Link not found.")
    if not await _can_read_link(session, link, current_user):
        raise LinkPermissionError("Insufficient link permissions.")
    return link


async def list_links(
    session: AsyncSession,
    current_user: User,
    limit: int = 50,
    offset: int = 0,
    include_inactive: bool = False,
) -> list[Link]:
    """Return paginated links visible to the current user."""
    links = await repository.list_links(
        session,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        include_inactive=include_inactive,
    )
    return list(links)


async def update_link(
    session: AsyncSession,
    link_id: int,
    payload: LinkUpdate,
    current_user: User,
) -> Link:
    """Update link metadata, destination, alias, activation, or expiration."""
    link = await get_link(session, link_id, current_user=current_user)
    if not await _can_write_link(session, link, current_user):
        raise LinkPermissionError("Insufficient link permissions.")
    update_data = payload.model_dump(exclude_unset=True)
    previous_short_code = link.short_code

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
    if payload.password is not None:
        link.password_hash = hash_password(payload.password)
    if payload.clear_password:
        link.password_hash = None
    if payload.is_active is not None:
        link.is_active = payload.is_active

    link.updated_at = datetime.now(UTC)

    try:
        updated_link = await repository.update_link(session, link)
        await session.commit()
        await invalidate_link_cache(previous_short_code)
        if previous_short_code != updated_link.short_code:
            await invalidate_link_cache(updated_link.short_code)
    except IntegrityError as exc:
        await session.rollback()
        raise AliasConflictError("Short code is already in use.") from exc

    return updated_link


async def soft_delete_link(
    session: AsyncSession,
    link_id: int,
    current_user: User,
) -> Link:
    """Deactivate a link instead of physically deleting it."""
    link = await get_link(session, link_id, current_user=current_user)
    if not await _can_write_link(session, link, current_user):
        raise LinkPermissionError("Insufficient link permissions.")
    short_code = link.short_code
    deleted_link = await repository.soft_delete_link(session, link, datetime.now(UTC))
    await session.commit()
    await invalidate_link_cache(short_code)
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


async def _can_read_link(
    session: AsyncSession,
    link: Link,
    current_user: User,
) -> bool:
    """Return whether a user can read a link."""
    if link.owner_id == current_user.id:
        return True
    if link.workspace_id is None:
        return False
    return await user_has_workspace_role(
        session,
        link.workspace_id,
        current_user.id,
        "viewer",
    )


async def _can_write_link(
    session: AsyncSession,
    link: Link,
    current_user: User,
) -> bool:
    """Return whether a user can mutate a link."""
    if link.owner_id == current_user.id:
        return True
    if link.workspace_id is None:
        return False
    return await user_has_workspace_role(
        session,
        link.workspace_id,
        current_user.id,
        "editor",
    )
