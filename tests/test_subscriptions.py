"""Tests for subscription management."""

from pathlib import Path

import pytest

from research_agent.config import load_config
from research_agent.pipeline import create_pipeline
from research_agent.subscriptions import SubscriptionService


@pytest.fixture
def services(tmp_path: Path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(f"data_dir: {tmp_path / 'data'}\n", encoding="utf-8")

    topics_path = tmp_path / "predefined_topics.yaml"
    topics_path.write_text(
        """
topics:
  - id: test-topic
    name: Test Topic
    description: A test predefined topic.
    search_queries:
      - testing
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)
    pipeline, _ = create_pipeline(config)
    service = SubscriptionService(pipeline.db)
    return service, topics_path


def test_create_custom_subscription(services):
    service, _ = services
    created = service.create_custom("My Topic", description="Custom desc", search_queries=["alpha"])
    assert created.id is not None
    assert created.name == "My Topic"
    assert created.search_queries == ["alpha"]


def test_subscribe_predefined(services):
    service, topics_path = services
    created = service.subscribe_predefined("test-topic", topics_path=topics_path)
    assert created.predefined_id == "test-topic"
    again = service.subscribe_predefined("test-topic", topics_path=topics_path)
    assert again.id == created.id


def test_pause_and_resume(services):
    service, _ = services
    created = service.create_custom("Pause Me")
    paused = service.pause(created.id)
    assert paused is not None
    assert paused.active is False
    resumed = service.resume(created.id)
    assert resumed is not None
    assert resumed.active is True


def test_delete_subscription(services):
    service, _ = services
    created = service.create_custom("Delete Me")
    assert service.delete(created.id) is True
    assert service.get(created.id) is None
