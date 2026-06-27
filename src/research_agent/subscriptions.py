"""Topic subscription management."""

from __future__ import annotations

from pathlib import Path

from research_agent.config import load_predefined_topics
from research_agent.models import TopicSubscription
from research_agent.storage import Database


class SubscriptionService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_custom(
        self,
        name: str,
        description: str = "",
        search_queries: list[str] | None = None,
        user_id: int | None = None,
    ) -> TopicSubscription:
        subscription = TopicSubscription(
            user_id=user_id,
            name=name,
            description=description,
            search_queries=search_queries or [name],
            active=True,
        )
        return self.db.create_subscription(subscription)

    def subscribe_predefined(
        self,
        predefined_id: str,
        topics_path: Path | None = None,
        user_id: int | None = None,
    ) -> TopicSubscription:
        existing = self.db.get_subscription_by_predefined(predefined_id, user_id=user_id)
        if existing:
            if not existing.active:
                return self.db.set_subscription_active(existing.id, True, user_id=user_id)  # type: ignore[arg-type]
            return existing

        topics = {topic["id"]: topic for topic in load_predefined_topics(topics_path)}
        if predefined_id not in topics:
            raise ValueError(f"Unknown predefined topic: {predefined_id}")

        topic = topics[predefined_id]
        subscription = TopicSubscription(
            user_id=user_id,
            name=topic["name"],
            description=topic.get("description", ""),
            predefined_id=predefined_id,
            search_queries=topic.get("search_queries", [topic["name"]]),
            active=True,
        )
        return self.db.create_subscription(subscription)

    def list_predefined(self, topics_path: Path | None = None) -> list[dict]:
        return load_predefined_topics(topics_path)

    def get(self, subscription_id: int, user_id: int | None = None) -> TopicSubscription | None:
        return self.db.get_subscription(subscription_id, user_id=user_id)

    def list(self, active_only: bool = False, user_id: int | None = None) -> list[TopicSubscription]:
        return self.db.list_subscriptions(active_only=active_only, user_id=user_id)

    def update(
        self,
        subscription_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        search_queries: list[str] | None = None,
        user_id: int | None = None,
    ) -> TopicSubscription | None:
        subscription = self.db.get_subscription(subscription_id, user_id=user_id)
        if subscription is None:
            return None

        if name is not None:
            subscription.name = name
        if description is not None:
            subscription.description = description
        if search_queries is not None:
            subscription.search_queries = search_queries

        return self.db.update_subscription(subscription)

    def pause(self, subscription_id: int, user_id: int | None = None) -> TopicSubscription | None:
        return self.db.set_subscription_active(subscription_id, False, user_id=user_id)

    def resume(self, subscription_id: int, user_id: int | None = None) -> TopicSubscription | None:
        return self.db.set_subscription_active(subscription_id, True, user_id=user_id)

    def delete(self, subscription_id: int, user_id: int | None = None) -> bool:
        return self.db.delete_subscription(subscription_id, user_id=user_id)
