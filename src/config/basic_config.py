from functools import lru_cache

from pydantic import BaseModel, Field, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class AWSConfig(BaseModel):
    """Configuration for AWS."""

    access_key_id: str | None = Field(default=None, description="AWS access key ID")
    secret_access_key: str | None = Field(default=None, description="AWS secret access key")
    region: str | None = Field(default=None, description="AWS region")


class CeleryConfig(BaseModel):
    """Configuration for Celery."""

    app_name: str = Field(default="debugmate-worker", description="Name of the Celery application")
    task_name: str = Field(default="process_events", description="Name of the Celery task to process events")
    broker_url: str | None = Field(default=None, description="URL of the Celery broker (used only for local environment)")
    endpoint_url: str | None = Field(default=None, description="Custom endpoint URL for the broker")
    is_secure: bool | None = Field(default=None, description="Use SSL when connecting to the broker")
    visibility_timeout: PositiveInt = Field(default=3600, description="Visibility timeout for tasks in seconds")
    polling_interval: PositiveInt = Field(default=5, description="Polling interval for the broker in seconds")
    queue_name: str = Field(default="debugmate-queue", description="Name of the Celery task queue")
    queue_url: str | None = Field(default=None, description="URL of the Celery task queue")


class BasicConfig(BaseSettings):
    """Basic configuration for the application."""

    debug: bool = Field(default=False, description="Enable debug mode")
    environment: str = Field(default="production", description="Application environment (e.g., local, staging, production)")
    log_level: str = Field(default="INFO", description="Logging level for the application")
    celery: CeleryConfig = Field(default_factory=CeleryConfig, description="Celery configuration")
    aws: AWSConfig = Field(default_factory=AWSConfig, description="AWS configuration")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )


@lru_cache()
def get_config() -> BasicConfig:
    """Returns the basic configuration for the application."""
    return BasicConfig()
