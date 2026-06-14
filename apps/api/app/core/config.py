from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    kafka_brokers: str
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    devlink_worker_id: int = 1
    rate_limit_read_requests: int = 300
    rate_limit_write_requests: int = 60
    rate_limit_bulk_requests: int = 10
    rate_limit_window_seconds: int = 60
    google_safe_browsing_api_key: str | None = None
    url_safety_timeout_seconds: float = 0.4
    app_env: str = "local"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("jwt_algorithm")
    @classmethod
    def validate_jwt_algorithm(cls, value: str) -> str:
        """Allow only strong symmetric JWT signing algorithms."""
        if value not in {"HS256", "HS384", "HS512"}:
            raise ValueError("JWT_ALGORITHM must be HS256, HS384, or HS512.")
        return value

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        """Reject placeholder or weak JWT secrets."""
        placeholders = {"change-me", "change-me-in-local-env"}
        if value in placeholders:
            raise ValueError("JWT_SECRET must be replaced with a strong secret.")
        return value


settings = Settings()
