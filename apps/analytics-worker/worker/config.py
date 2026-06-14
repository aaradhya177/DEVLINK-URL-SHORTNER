from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven analytics worker settings."""

    database_url: str = "postgresql+asyncpg://devlink:devlink@localhost:5432/devlink"
    kafka_brokers: str = "localhost:9092"
    click_events_topic: str = "click-events"
    kafka_group_id: str = "devlink-analytics-worker"
    geoip_database_path: str | None = None
    ip_hash_secret: str = Field(default="local-dev-ip-hash-secret", min_length=16)
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
