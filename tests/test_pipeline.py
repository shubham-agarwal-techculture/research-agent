"""Tests for research pipeline and output."""

from pathlib import Path

import pytest

from research_agent.config import load_config
from research_agent.models import RunOutput, SourceDocument, TopicSubscription
from research_agent.output import build_markdown, write_markdown_output
from research_agent.pipeline import ResearchPipeline, build_simple_summary, create_pipeline
from research_agent.sources import SourceConnector


class StubConnector(SourceConnector):
    name = "stub"

    def fetch(self, subscription: TopicSubscription, max_results: int) -> list[SourceDocument]:
        return [
            SourceDocument(
                title=f"Doc for {subscription.name}",
                url="https://example.com/doc",
                source_type="article",
                origin="stub",
                content_snippet="Stub content",
                content_hash="abc123",
            )
        ]


@pytest.fixture
def pipeline(tmp_path: Path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"""
data_dir: {tmp_path / "data"}
scheduler:
  retry:
    max_attempts: 1
    delay_seconds: 0
""".strip(),
        encoding="utf-8",
    )
    config = load_config(config_path)
    pipeline, subscriptions = create_pipeline(config)
    pipeline.connectors = [StubConnector()]
    return pipeline, subscriptions


def test_build_simple_summary():
    subscription = TopicSubscription(name="AI Agents")
    docs = [
        SourceDocument(
            title="One",
            url="https://example.com/1",
            source_type="paper",
            origin="arxiv",
        )
    ]
    summary = build_simple_summary(subscription, docs)
    assert "1" in summary
    assert "AI Agents" in summary


def test_pipeline_run_writes_output(pipeline):
    runner, subscriptions = pipeline
    created = subscriptions.create_custom("Pipeline Topic", search_queries=["test"])
    run = runner.run_for_subscription(created)
    assert run.status.value == "completed"
    assert run.output_path is not None
    assert Path(run.output_path).exists()


def test_markdown_output_contains_sources(pipeline):
    runner, subscriptions = pipeline
    created = subscriptions.create_custom("Markdown Topic")
    run = runner.run_for_subscription(created)
    docs = runner.db.get_documents_for_run(run.id)
    run_output = RunOutput(
        subscription=created,
        run=run,
        documents=docs,
        summary=build_simple_summary(created, docs),
    )
    output = write_markdown_output(run_output, runner.output_dir)
    content = output.read_text(encoding="utf-8")
    assert "Markdown Topic" in content
    assert "Sources Consulted" in content
