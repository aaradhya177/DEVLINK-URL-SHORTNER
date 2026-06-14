import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LinkCreate(BaseModel):
    """Request body for creating a short link."""

    destination_url: str = Field(min_length=1, max_length=4096)
    workspace_id: uuid.UUID | None = None
    title: str | None = Field(default=None, max_length=255)
    custom_alias: str | None = Field(default=None, min_length=3, max_length=32)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    expires_at: datetime | None = None
    strip_tracking_params: bool = True

    @field_validator("destination_url")
    @classmethod
    def validate_destination_url(cls, value: str) -> str:
        """Require an absolute HTTP(S) destination URL."""
        if not value.startswith(("http://", "https://")):
            raise ValueError("destination_url must start with http:// or https://.")
        return value


class LinkUpdate(BaseModel):
    """Request body for updating link metadata or destination."""

    destination_url: str | None = Field(default=None, min_length=1, max_length=4096)
    title: str | None = Field(default=None, max_length=255)
    custom_alias: str | None = Field(default=None, min_length=3, max_length=32)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    clear_password: bool = False
    is_active: bool | None = None
    expires_at: datetime | None = None
    strip_tracking_params: bool = True

    @field_validator("destination_url")
    @classmethod
    def validate_destination_url(cls, value: str | None) -> str | None:
        """Require an absolute HTTP(S) destination URL when one is supplied."""
        if value is not None and not value.startswith(("http://", "https://")):
            raise ValueError("destination_url must start with http:// or https://.")
        return value


class LinkResponse(BaseModel):
    """Response payload for link CRUD endpoints."""

    id: int
    workspace_id: uuid.UUID | None
    owner_id: uuid.UUID | None
    short_code: str
    destination_url: str
    title: str | None
    is_password_protected: bool
    is_active: bool
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BulkLinkCreateRequest(BaseModel):
    """Bulk URL shortening request."""

    urls: list[str] = Field(min_length=1, max_length=50)
    workspace_id: uuid.UUID | None = None
    strip_tracking_params: bool = True


class BulkLinkResult(BaseModel):
    """Per-item bulk shortening result."""

    index: int
    status: str
    url: str
    link: LinkResponse | None = None
    error: str | None = None


class BulkLinkCreateResponse(BaseModel):
    """Bulk URL shortening response."""

    results: list[BulkLinkResult]
