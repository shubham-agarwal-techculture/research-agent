"""Domain models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TopicSubscription(BaseModel):
    id: int | None = None
    user_id: int | None = None
    name: str
    description: str = ""
    predefined_id: str | None = None
    search_queries: list[str] = Field(default_factory=list)
    active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SourceDocument(BaseModel):
    title: str
    url: str
    source_type: str
    origin: str
    published_at: datetime | None = None
    content_snippet: str = ""
    content_hash: str = ""


class ResearchRun(BaseModel):
    id: int | None = None
    subscription_id: int
    status: RunStatus = RunStatus.PENDING
    attempt: int = 1
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    output_path: str | None = None
    documents_found: int = 0


class RunOutput(BaseModel):
    subscription: TopicSubscription
    run: ResearchRun
    documents: list[SourceDocument]
    summary: str = ""


class User(BaseModel):
    id: int | None = None
    email: str
    display_name: str = ""
    created_at: datetime | None = None
