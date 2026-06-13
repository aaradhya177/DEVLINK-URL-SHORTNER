import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.workspace_member import WorkspaceMember


ROLE_RANKS = {
    "viewer": 1,
    "editor": 2,
    "admin": 3,
    "owner": 4,
}


def role_allows(actual_role: str, minimum_role: str) -> bool:
    """Return whether actual_role satisfies minimum_role."""
    return ROLE_RANKS.get(actual_role, 0) >= ROLE_RANKS[minimum_role]


async def get_workspace_role(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> str | None:
    """Return a user's role in a workspace, if they are a member."""
    stmt = select(WorkspaceMember.role).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id,
    )
    return await session.scalar(stmt)


async def user_has_workspace_role(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    minimum_role: str,
) -> bool:
    """Return whether a user has at least minimum_role in a workspace."""
    role = await get_workspace_role(session, workspace_id, user_id)
    return role is not None and role_allows(role, minimum_role)


def validate_role(role: str) -> str:
    """Return a valid role or raise ValueError."""
    normalized_role = role.strip().lower()
    if normalized_role not in ROLE_RANKS:
        raise ValueError("Role must be one of owner, admin, editor, or viewer.")
    return normalized_role
