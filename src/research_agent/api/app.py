"""FastAPI application."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from research_agent.api.auth import create_access_token, hash_password, verify_password
from research_agent.api.deps import AppServices, get_app_services, get_current_user
from research_agent.api.schemas import (
    LoginRequest,
    PredefinedTopicResponse,
    RegisterRequest,
    RunOutputResponse,
    RunResponse,
    SourceDocumentResponse,
    SubscriptionCreateRequest,
    SubscriptionResponse,
    SubscriptionUpdateRequest,
    TokenResponse,
    UserResponse,
)
from research_agent.config import load_config
from research_agent.models import ResearchRun, TopicSubscription, User
from research_agent.pipeline import create_pipeline

logger = logging.getLogger(__name__)


def _subscription_response(subscription: TopicSubscription) -> SubscriptionResponse:
    return SubscriptionResponse(
        id=subscription.id,  # type: ignore[arg-type]
        name=subscription.name,
        description=subscription.description,
        predefined_id=subscription.predefined_id,
        search_queries=subscription.search_queries,
        active=subscription.active,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at,
    )


def _run_response(run: ResearchRun) -> RunResponse:
    return RunResponse(
        id=run.id,  # type: ignore[arg-type]
        subscription_id=run.subscription_id,
        status=run.status.value,
        attempt=run.attempt,
        started_at=run.started_at,
        completed_at=run.completed_at,
        error_message=run.error_message,
        output_path=run.output_path,
        documents_found=run.documents_found,
    )


def create_app() -> FastAPI:
    config = load_config()
    pipeline, subscriptions = create_pipeline(config)
    services = AppServices(config=config, pipeline=pipeline, subscriptions=subscriptions)

    app = FastAPI(
        title="Research Agent API",
        description="REST API for the Personal Research Agent",
        version="0.2.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.services = services

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
    def register(payload: RegisterRequest, svc: AppServices = Depends(get_app_services)) -> TokenResponse:
        if svc.db.get_user_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        user = svc.db.create_user(
            email=payload.email,
            password_hash=hash_password(payload.password),
            display_name=payload.display_name or payload.email.split("@")[0],
        )
        token = create_access_token(str(user.id), svc.config.api)
        return TokenResponse(access_token=token)

    @app.post("/api/auth/login", response_model=TokenResponse)
    def login(payload: LoginRequest, svc: AppServices = Depends(get_app_services)) -> TokenResponse:
        record = svc.db.get_user_by_email(payload.email)
        if record is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        user, password_hash = record
        if not verify_password(payload.password, password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token = create_access_token(str(user.id), svc.config.api)
        return TokenResponse(access_token=token)

    @app.get("/api/auth/me", response_model=UserResponse)
    def me(current_user: User = Depends(get_current_user)) -> UserResponse:
        return UserResponse(
            id=current_user.id,  # type: ignore[arg-type]
            email=current_user.email,
            display_name=current_user.display_name,
            created_at=current_user.created_at,
        )

    @app.get("/api/topics/predefined", response_model=list[PredefinedTopicResponse])
    def list_predefined_topics(
        svc: AppServices = Depends(get_app_services),
        _: User = Depends(get_current_user),
    ) -> list[PredefinedTopicResponse]:
        topics = svc.subscriptions.list_predefined()
        return [
            PredefinedTopicResponse(
                id=topic["id"],
                name=topic["name"],
                description=topic.get("description", ""),
                search_queries=topic.get("search_queries", []),
            )
            for topic in topics
        ]

    @app.get("/api/subscriptions", response_model=list[SubscriptionResponse])
    def list_subscriptions(
        active_only: bool = False,
        svc: AppServices = Depends(get_app_services),
        current_user: User = Depends(get_current_user),
    ) -> list[SubscriptionResponse]:
        items = svc.subscriptions.list(active_only=active_only, user_id=current_user.id)
        return [_subscription_response(item) for item in items]

    @app.post("/api/subscriptions", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
    def create_subscription(
        payload: SubscriptionCreateRequest,
        svc: AppServices = Depends(get_app_services),
        current_user: User = Depends(get_current_user),
    ) -> SubscriptionResponse:
        created = svc.subscriptions.create_custom(
            name=payload.name,
            description=payload.description,
            search_queries=payload.search_queries or [payload.name],
            user_id=current_user.id,
        )
        return _subscription_response(created)

    @app.post("/api/subscriptions/predefined/{topic_id}", response_model=SubscriptionResponse)
    def subscribe_predefined(
        topic_id: str,
        svc: AppServices = Depends(get_app_services),
        current_user: User = Depends(get_current_user),
    ) -> SubscriptionResponse:
        try:
            created = svc.subscriptions.subscribe_predefined(topic_id, user_id=current_user.id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        return _subscription_response(created)

    @app.patch("/api/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
    def update_subscription(
        subscription_id: int,
        payload: SubscriptionUpdateRequest,
        svc: AppServices = Depends(get_app_services),
        current_user: User = Depends(get_current_user),
    ) -> SubscriptionResponse:
        updated = svc.subscriptions.update(
            subscription_id,
            name=payload.name,
            description=payload.description,
            search_queries=payload.search_queries,
            user_id=current_user.id,
        )
        if updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
        return _subscription_response(updated)

    @app.post("/api/subscriptions/{subscription_id}/pause", response_model=SubscriptionResponse)
    def pause_subscription(
        subscription_id: int,
        svc: AppServices = Depends(get_app_services),
        current_user: User = Depends(get_current_user),
    ) -> SubscriptionResponse:
        updated = svc.subscriptions.pause(subscription_id, user_id=current_user.id)
        if updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
        return _subscription_response(updated)

    @app.post("/api/subscriptions/{subscription_id}/resume", response_model=SubscriptionResponse)
    def resume_subscription(
        subscription_id: int,
        svc: AppServices = Depends(get_app_services),
        current_user: User = Depends(get_current_user),
    ) -> SubscriptionResponse:
        updated = svc.subscriptions.resume(subscription_id, user_id=current_user.id)
        if updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
        return _subscription_response(updated)

    @app.delete("/api/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_subscription(
        subscription_id: int,
        svc: AppServices = Depends(get_app_services),
        current_user: User = Depends(get_current_user),
    ) -> None:
        if not svc.subscriptions.delete(subscription_id, user_id=current_user.id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    @app.get("/api/runs", response_model=list[RunResponse])
    def list_runs(
        subscription_id: int | None = None,
        limit: int = 20,
        svc: AppServices = Depends(get_app_services),
        current_user: User = Depends(get_current_user),
    ) -> list[RunResponse]:
        runs = svc.db.list_runs(
            subscription_id=subscription_id,
            user_id=current_user.id,
            limit=limit,
        )
        return [_run_response(run) for run in runs]

    @app.get("/api/runs/{run_id}", response_model=RunResponse)
    def get_run(
        run_id: int,
        svc: AppServices = Depends(get_app_services),
        current_user: User = Depends(get_current_user),
    ) -> RunResponse:
        run = svc.db.get_run(run_id, user_id=current_user.id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
        return _run_response(run)

    @app.get("/api/runs/{run_id}/documents", response_model=list[SourceDocumentResponse])
    def get_run_documents(
        run_id: int,
        svc: AppServices = Depends(get_app_services),
        current_user: User = Depends(get_current_user),
    ) -> list[SourceDocumentResponse]:
        if svc.db.get_run(run_id, user_id=current_user.id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

        documents = svc.db.get_documents_for_run(run_id, user_id=current_user.id)
        return [
            SourceDocumentResponse(
                title=doc.title,
                url=doc.url,
                source_type=doc.source_type,
                origin=doc.origin,
                published_at=doc.published_at,
                content_snippet=doc.content_snippet,
            )
            for doc in documents
        ]

    @app.get("/api/runs/{run_id}/output", response_model=RunOutputResponse)
    def get_run_output(
        run_id: int,
        svc: AppServices = Depends(get_app_services),
        current_user: User = Depends(get_current_user),
    ) -> RunOutputResponse:
        run = svc.db.get_run(run_id, user_id=current_user.id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
        if not run.output_path:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output not available")

        path = Path(run.output_path)
        if not path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output file missing")

        return RunOutputResponse(run=_run_response(run), markdown=path.read_text(encoding="utf-8"))

    @app.post("/api/runs", status_code=status.HTTP_202_ACCEPTED)
    def trigger_all_runs(
        background_tasks: BackgroundTasks,
        svc: AppServices = Depends(get_app_services),
        current_user: User = Depends(get_current_user),
    ) -> dict[str, int]:
        subscriptions = svc.subscriptions.list(active_only=True, user_id=current_user.id)
        for subscription in subscriptions:
            background_tasks.add_task(
                _run_pipeline_for_subscription,
                svc,
                subscription.id,
                current_user.id,
            )
        return {"started": len(subscriptions)}

    @app.post(
        "/api/runs/subscription/{subscription_id}",
        response_model=RunResponse,
    )
    def trigger_subscription_run(
        subscription_id: int,
        svc: AppServices = Depends(get_app_services),
        current_user: User = Depends(get_current_user),
    ) -> RunResponse:
        subscription = svc.subscriptions.get(subscription_id, user_id=current_user.id)
        if subscription is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

        run = svc.pipeline.run_with_retry(subscription)
        return _run_response(run)

    return app


def _run_pipeline_for_subscription(services: AppServices, subscription_id: int, user_id: int) -> None:
    subscription = services.subscriptions.get(subscription_id, user_id=user_id)
    if subscription is None:
        return
    try:
        services.pipeline.run_with_retry(subscription)
    except Exception:
        logger.exception("Background run failed for subscription %s", subscription_id)


app = create_app()
