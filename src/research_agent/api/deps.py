"""FastAPI dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from research_agent.api.auth import decode_access_token
from research_agent.config import AppConfig
from research_agent.models import User
from research_agent.pipeline import ResearchPipeline
from research_agent.storage import Database
from research_agent.subscriptions import SubscriptionService

security = HTTPBearer(auto_error=False)


@dataclass
class AppServices:
    config: AppConfig
    pipeline: ResearchPipeline
    subscriptions: SubscriptionService

    @property
    def db(self) -> Database:
        return self.pipeline.db


def get_app_services(request: Request) -> AppServices:
    return request.app.state.services


def get_current_user(
    services: Annotated[AppServices, Depends(get_app_services)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user_id = decode_access_token(credentials.credentials, services.config.api)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = services.db.get_user(int(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
