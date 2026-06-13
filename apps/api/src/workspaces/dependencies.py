import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.security import get_current_user
from src.db.session import get_session
from src.models.user import User
from src.workspaces.permissions import user_has_workspace_role


def require_workspace_role(min_role: str) -> Callable[..., object]:
    """Build a FastAPI dependency requiring at least min_role for workspace_id."""

    async def dependency(
        workspace_id: uuid.UUID,
        current_user: Annotated[User, Depends(get_current_user)],
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> User:
        """Return the current user when they have the required workspace role."""
        allowed = await user_has_workspace_role(
            session,
            workspace_id,
            current_user.id,
            min_role,
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient workspace permissions.",
            )
        return current_user

    return dependency
