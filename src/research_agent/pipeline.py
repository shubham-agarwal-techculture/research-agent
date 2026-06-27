"""Research run orchestration."""

from __future__ import annotations

import logging
import time
from pathlib import Path

import httpx

from research_agent.config import AppConfig
from research_agent.models import ResearchRun, RunOutput, RunStatus, SourceDocument, TopicSubscription
from research_agent.output import write_markdown_output
from research_agent.sources import SourceConnector, build_connectors, dedupe_documents
from research_agent.storage import Database
from research_agent.subscriptions import SubscriptionService

logger = logging.getLogger(__name__)


def build_simple_summary(subscription: TopicSubscription, documents: list[SourceDocument]) -> str:
    if not documents:
        return (
            f"No matching research items were found for **{subscription.name}** in this run. "
            "Try broadening search queries or adding RSS feeds in config."
        )

    origins = sorted({doc.origin for doc in documents})
    types = sorted({doc.source_type for doc in documents})
    return (
        f"Collected **{len(documents)}** items for **{subscription.name}** from "
        f"{', '.join(origins)} ({', '.join(types)}). "
        "Review the sources below; Phase 1 will add multi-step agentic analysis and idea synthesis."
    )


class ResearchPipeline:
    def __init__(
        self,
        config: AppConfig,
        db: Database,
        connectors: list[SourceConnector] | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.config = config
        self.db = db
        self.client = client or httpx.Client(timeout=30.0)
        self.connectors = connectors or build_connectors(config, client=self.client)
        self.output_dir = config.data_dir / config.output.directory

    def run_for_subscription(self, subscription: TopicSubscription, attempt: int = 1) -> ResearchRun:
        if subscription.id is None:
            raise ValueError("Subscription must be persisted before running")

        run = self.db.create_run(subscription.id, attempt=attempt)
        logger.info(
            "Starting run %s for subscription %s (%s), attempt %s",
            run.id,
            subscription.id,
            subscription.name,
            attempt,
        )

        try:
            documents = self._gather(subscription)
            summary = build_simple_summary(subscription, documents)
            run.documents_found = len(documents)
            run.status = RunStatus.COMPLETED
            run_output = RunOutput(
                subscription=subscription,
                run=run,
                documents=documents,
                summary=summary,
            )
            output_path = write_markdown_output(run_output, self.output_dir)
            self.db.save_documents(run.id, documents)
            self.db.complete_run(
                run.id,
                status=RunStatus.COMPLETED,
                output_path=str(output_path),
                documents_found=len(documents),
            )
            run.status = RunStatus.COMPLETED
            run.output_path = str(output_path)
            run.documents_found = len(documents)
            logger.info("Completed run %s -> %s", run.id, output_path)
            return run
        except Exception as exc:
            logger.exception("Run %s failed", run.id)
            self.db.complete_run(
                run.id,
                status=RunStatus.FAILED,
                error_message=str(exc),
            )
            run.status = RunStatus.FAILED
            run.error_message = str(exc)
            raise

    def run_with_retry(self, subscription: TopicSubscription) -> ResearchRun:
        retry = self.config.scheduler.retry
        last_error: Exception | None = None

        for attempt in range(1, retry.max_attempts + 1):
            try:
                return self.run_for_subscription(subscription, attempt=attempt)
            except Exception as exc:
                last_error = exc
                if attempt >= retry.max_attempts:
                    break
                logger.warning(
                    "Run failed for subscription %s (attempt %s/%s). Retrying in %ss.",
                    subscription.id,
                    attempt,
                    retry.max_attempts,
                    retry.delay_seconds,
                )
                time.sleep(retry.delay_seconds)

        assert last_error is not None
        raise last_error

    def run_all_active(self) -> list[ResearchRun]:
        subscriptions = self.db.list_subscriptions(active_only=True)
        results: list[ResearchRun] = []

        for subscription in subscriptions:
            try:
                results.append(self.run_with_retry(subscription))
            except Exception:
                failed = self.db.list_runs(subscription_id=subscription.id, limit=1)[0]
                results.append(failed)

        return results

    def _gather(self, subscription: TopicSubscription) -> list[SourceDocument]:
        max_results = self.config.ingestion.max_results_per_source
        collected: list[SourceDocument] = []

        for connector in self.connectors:
            try:
                collected.extend(connector.fetch(subscription, max_results=max_results))
            except Exception as exc:
                logger.warning("Connector %s failed: %s", connector.name, exc)

        return dedupe_documents(collected)


def create_pipeline(config: AppConfig) -> tuple[ResearchPipeline, SubscriptionService]:
    db_path = config.data_dir / "research_agent.db"
    db = Database(db_path)
    pipeline = ResearchPipeline(config, db)
    subscriptions = SubscriptionService(db)
    return pipeline, subscriptions
