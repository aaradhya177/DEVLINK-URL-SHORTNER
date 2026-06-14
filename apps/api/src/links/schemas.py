import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.shared.url_utils import validate_safe_redirect_url


class LinkCreate(BaseModel):
    """Request body for creating a short link."""

    destination_url: str = Field(min_length=1, max_length=4096)
    workspace_id: uuid.UUID | None = None
    title: str | None = Field(default=None, max_length=255)
    custom_alias: str | None = Field(default=None, min_length=3, max_length=32)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    expires_at: datetime | None = None
    strip_tracking_params: bool = True
    model_config = ConfigDict(extra="forbid")

    @field_validator("destination_url")
    @classmethod
    def validate_destination_url(cls, value: str) -> str:
        """Require an absolute HTTP(S) destination URL."""
        return validate_safe_redirect_url(value)


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
    model_config = ConfigDict(extra="forbid")

    @field_validator("destination_url")
    @classmethod
    def validate_destination_url(cls, value: str | None) -> str | None:
        """Require an absolute HTTP(S) destination URL when one is supplied."""
        return validate_safe_redirect_url(value) if value is not None else None


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
    flagged_reason: str | None
    checked_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BulkLinkCreateRequest(BaseModel):
    """Bulk URL shortening request."""

    urls: list[str] = Field(min_length=1, max_length=50)
    workspace_id: uuid.UUID | None = None
    strip_tracking_params: bool = True
    model_config = ConfigDict(extra="forbid")

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, value: list[str]) -> list[str]:
        """Validate every bulk redirect URL before service processing."""
        for url in value:
            if len(url) > 4096:
                raise ValueError("URLs must be 4096 characters or fewer.")
            validate_safe_redirect_url(url)
        return value


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
