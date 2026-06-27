"""Application configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RetryConfig(BaseModel):
    max_attempts: int = 3
    delay_seconds: int = 60


class SchedulerConfig(BaseModel):
    run_times: list[str] = Field(default_factory=lambda: ["09:00", "21:00"])
    retry: RetryConfig = Field(default_factory=RetryConfig)


class IngestionConfig(BaseModel):
    max_results_per_source: int = 5
    enabled_sources: list[str] = Field(default_factory=lambda: ["arxiv", "rss"])


class OutputConfig(BaseModel):
    format: str = "markdown"
    directory: str = "outputs"


class RssFeedConfig(BaseModel):
    name: str
    url: str


class AppConfig(BaseModel):
    data_dir: Path = Path("data")
    timezone: str = "UTC"
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    ingestion: IngestionConfig = Field(default_factory=IngestionConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    rss_feeds: list[RssFeedConfig] = Field(default_factory=list)
    api: "ApiConfig" = Field(default_factory=lambda: ApiConfig())


class ApiConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])
    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 60 * 24 * 7


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RESEARCH_AGENT_", env_file=".env")

    data_dir: Path | None = None
    timezone: str | None = None
    jwt_secret: str | None = None


def load_config(config_path: Path | None = None) -> AppConfig:
    path = config_path or Path("config.yaml")
    data: dict[str, Any] = {}

    if path.exists():
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}

    config = AppConfig.model_validate(data)
    settings = Settings()

    if settings.data_dir is not None:
        config.data_dir = settings.data_dir
    if settings.timezone is not None:
        config.timezone = settings.timezone
    if settings.jwt_secret is not None:
        config.api.jwt_secret = settings.jwt_secret

    config.data_dir.mkdir(parents=True, exist_ok=True)
    return config


def load_predefined_topics(path: Path | None = None) -> list[dict[str, Any]]:
    topic_path = path or Path("predefined_topics.yaml")
    if not topic_path.exists():
        return []

    with topic_path.open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    return list(payload.get("topics", []))
