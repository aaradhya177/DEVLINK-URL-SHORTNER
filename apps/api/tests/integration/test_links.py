from datetime import UTC, datetime, timedelta

import pytest

from src.links import service
from src.links.schemas import LinkCreate, LinkUpdate
from src.models.user import User


pytestmark = pytest.mark.integration


async def _user(session, email: str = "owner@example.com") -> User:
    user = User(email=email, password_hash="hash")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def test_link_create_and_dedup(db_session) -> None:
    """Posting the same normalized URL should return the existing active link."""
    user = await _user(db_session)
    payload = LinkCreate(destination_url="https://Example.com?a=1&utm_source=x")

    first = await service.create_link(db_session, payload, current_user=user)
    second = await service.create_link(db_session, payload, current_user=user)

    assert second.id == first.id
    assert second.destination_url == "https://example.com/?a=1"


async def test_custom_alias_collision(db_session) -> None:
    """Custom aliases should remain globally unique."""
    user = await _user(db_session)
    payload = LinkCreate(
        destination_url="https://example.com/a",
        custom_alias="docs-1",
    )
    await service.create_link(db_session, payload, current_user=user)

    with pytest.raises(service.AliasConflictError):
        await service.create_link(
            db_session,
            LinkCreate(
                destination_url="https://example.com/b",
                custom_alias="docs-1",
            ),
            current_user=user,
        )


async def test_expiration_validation_and_soft_delete(db_session) -> None:
    """Expired payloads are rejected and soft-delete deactivates the link."""
    user = await _user(db_session)

    with pytest.raises(service.InvalidExpirationError):
        await service.create_link(
            db_session,
            LinkCreate(
                destination_url="https://example.com",
                expires_at=datetime.now(UTC) - timedelta(minutes=1),
            ),
            current_user=user,
        )

    link = await service.create_link(
        db_session,
        LinkCreate(
            destination_url="https://example.com",
            expires_at=datetime.now(UTC) + timedelta(days=1),
        ),
        current_user=user,
    )
    deleted = await service.soft_delete_link(db_session, link.id, current_user=user)

    assert deleted.is_active is False


async def test_destination_update_resets_safety_metadata(db_session) -> None:
    """A changed destination should clear stale safety state."""
    user = await _user(db_session)
    link = await service.create_link(
        db_session,
        LinkCreate(destination_url="https://example.com/a"),
        current_user=user,
    )
    link.flagged_reason = "old_flag"
    link.checked_at = datetime.now(UTC)
    await db_session.commit()

    updated = await service.update_link(
        db_session,
        link.id,
        LinkUpdate(destination_url="https://example.com/b"),
        current_user=user,
    )

    assert updated.flagged_reason is None
    assert updated.checked_at is None
