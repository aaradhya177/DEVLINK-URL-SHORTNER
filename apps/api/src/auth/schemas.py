from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterRequest(BaseModel):
    """Request body for creating a password-backed user account."""

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "email": "ada@example.com",
                "password": "correct-horse-battery",
            }
        },
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Normalize and lightly validate an email address."""
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@"):
            raise ValueError("A valid email address is required.")
        return normalized


class LoginRequest(BaseModel):
    """Request body for password login."""

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "email": "ada@example.com",
                "password": "correct-horse-battery",
            }
        },
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Normalize an email address before credential lookup."""
        return value.strip().lower()


class RefreshRequest(BaseModel):
    """Request body for refresh-token rotation or logout."""

    refresh_token: str = Field(min_length=1)
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"refresh_token": "eyJhbGciOiJIUzI1NiJ9..."}},
    )


class TokenResponse(BaseModel):
    """Access and refresh JWT response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 900,
            }
        }
    )
