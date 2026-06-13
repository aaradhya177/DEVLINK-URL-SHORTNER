from pydantic import BaseModel, Field


class PasswordVerifyRequest(BaseModel):
    """Request body for password-protected redirect verification."""

    password: str = Field(min_length=1, max_length=128)


class PasswordVerifyResponse(BaseModel):
    """Response payload for successful redirect password verification."""

    redirect_token: str
    token_type: str = "bearer"
    expires_in: int
