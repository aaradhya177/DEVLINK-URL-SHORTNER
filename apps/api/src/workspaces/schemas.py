import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.workspaces.permissions import validate_role


class WorkspaceCreate(BaseModel):
    """Request body for creating a workspace."""

    name: str = Field(min_length=1, max_length=120)
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"name": "Engineering"}},
    )


class WorkspaceUpdate(BaseModel):
    """Request body for updating workspace metadata."""

    name: str = Field(min_length=1, max_length=120)
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"name": "Platform Engineering"}},
    )


class WorkspaceResponse(BaseModel):
    """Workspace response payload."""

    id: uuid.UUID
    name: str
    owner_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "b9300502-d860-4d26-ad73-4f88724f9fb0",
                "name": "Engineering",
                "owner_id": "d7b5f7a2-8a6c-4a46-9443-6480a4f7aa1e",
                "created_at": "2026-06-15T12:00:00Z",
                "updated_at": "2026-06-15T12:00:00Z",
            }
        },
    )


class WorkspaceMemberCreate(BaseModel):
    """Request body for adding a workspace member."""

    user_id: uuid.UUID
    role: str = Field(default="viewer")
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "29e61574-f3ae-4f08-8ba4-c770659d0d6e",
                "role": "editor",
            }
        },
    )

    @field_validator("role")
    @classmethod
    def validate_member_role(cls, value: str) -> str:
        """Validate a workspace member role."""
        return validate_role(value)


class WorkspaceMemberUpdate(BaseModel):
    """Request body for updating a workspace member role."""

    role: str
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"role": "viewer"}},
    )

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

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "f88a2925-71e2-4144-9450-44af3a7d12ab",
                "workspace_id": "b9300502-d860-4d26-ad73-4f88724f9fb0",
                "user_id": "29e61574-f3ae-4f08-8ba4-c770659d0d6e",
                "role": "editor",
                "created_at": "2026-06-15T12:00:00Z",
            }
        },
    )
