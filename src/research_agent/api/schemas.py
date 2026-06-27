"""API request and response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(default="", max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    created_at: datetime | None = None


class SubscriptionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    search_queries: list[str] = Field(default_factory=list)


class SubscriptionUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    search_queries: list[str] | None = None


class SubscriptionResponse(BaseModel):
    id: int
    name: str
    description: str
    predefined_id: str | None = None
    search_queries: list[str]
    active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PredefinedTopicResponse(BaseModel):
    id: str
    name: str
    description: str
    search_queries: list[str]


class RunResponse(BaseModel):
    id: int
    subscription_id: int
    status: str
    attempt: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    output_path: str | None = None
    documents_found: int = 0


class SourceDocumentResponse(BaseModel):
    title: str
    url: str
    source_type: str
    origin: str
    published_at: datetime | None = None
    content_snippet: str = ""


class RunOutputResponse(BaseModel):
    run: RunResponse
    markdown: str
