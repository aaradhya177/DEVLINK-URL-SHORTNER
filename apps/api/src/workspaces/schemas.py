import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.workspaces.permissions import validate_role


class WorkspaceCreate(BaseModel):
    """Request body for creating a workspace."""

    name: str = Field(min_length=1, max_length=120)
    model_config = ConfigDict(extra="forbid")


class WorkspaceUpdate(BaseModel):
    """Request body for updating workspace metadata."""

    name: str = Field(min_length=1, max_length=120)
    model_config = ConfigDict(extra="forbid")


class WorkspaceResponse(BaseModel):
    """Workspace response payload."""

    id: uuid.UUID
    name: str
    owner_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkspaceMemberCreate(BaseModel):
    """Request body for adding a workspace member."""

    user_id: uuid.UUID
    role: str = Field(default="viewer")
    model_config = ConfigDict(extra="forbid")

    @field_validator("role")
    @classmethod
    def validate_member_role(cls, value: str) -> str:
        """Validate a workspace member role."""
        return validate_role(value)


class WorkspaceMemberUpdate(BaseModel):
    """Request body for updating a workspace member role."""

    role: str
    model_config = ConfigDict(extra="forbid")

    @field_validator("role")
    @classmethod
    def validate_member_role(cls, value: str) -> str:
        """Validate a workspace member role."""
        return validate_role(value)


class WorkspaceMemberResponse(BaseModel):
    """Workspace member response payload."""

    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
