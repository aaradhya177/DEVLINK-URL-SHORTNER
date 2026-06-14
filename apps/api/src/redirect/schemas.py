from pydantic import BaseModel, ConfigDict, Field


class PasswordVerifyRequest(BaseModel):
    """Request body for password-protected redirect verification."""

    password: str = Field(min_length=1, max_length=128)
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"password": "optional-secret"}},
    )


class PasswordVerifyResponse(BaseModel):
    """Response payload for successful redirect password verification."""

    redirect_token: str
    token_type: str = "bearer"
    expires_in: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "redirect_token": "eyJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 600,
            }
        }
    )
