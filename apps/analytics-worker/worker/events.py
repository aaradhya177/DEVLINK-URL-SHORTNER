from datetime import datetime
import uuid

from pydantic import BaseModel, Field, field_validator


class ClickEventMessage(BaseModel):
    """Kafka click-event message schema."""

    event_id: uuid.UUID
    link_id: int
    timestamp: datetime
    ip: str = Field(min_length=1)
    user_agent: str | None = None
    referrer: str | None = None

    @field_validator("link_id")
    @classmethod
    def validate_link_id(cls, value: int) -> int:
        """Require a positive link ID."""
        if value <= 0:
            raise ValueError("link_id must be positive.")
        return value
