"""SQLite persistence layer."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from research_agent.models import ResearchRun, RunStatus, SourceDocument, TopicSubscription

SCHEMA = """
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    predefined_id TEXT,
    search_queries TEXT NOT NULL DEFAULT '[]',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS research_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    attempt INTEGER NOT NULL DEFAULT 1,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT,
    output_path TEXT,
    documents_found INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
);

CREATE TABLE IF NOT EXISTS source_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    source_type TEXT NOT NULL,
    origin TEXT NOT NULL,
    published_at TEXT,
    content_snippet TEXT NOT NULL DEFAULT '',
    content_hash TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES research_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_runs_subscription ON research_runs(subscription_id);
CREATE INDEX IF NOT EXISTS idx_documents_run ON source_documents(run_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_subscriptions_predefined
    ON subscriptions(predefined_id) WHERE predefined_id IS NOT NULL;
"""


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat()


def _from_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def initialize(self) -> None:
        with self.connection() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _row_to_subscription(self, row: sqlite3.Row) -> TopicSubscription:
        return TopicSubscription(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            predefined_id=row["predefined_id"],
            search_queries=json.loads(row["search_queries"]),
            active=bool(row["active"]),
            created_at=_from_iso(row["created_at"]),
            updated_at=_from_iso(row["updated_at"]),
        )

    def create_subscription(self, subscription: TopicSubscription) -> TopicSubscription:
        now = _utc_now()
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO subscriptions
                    (name, description, predefined_id, search_queries, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    subscription.name,
                    subscription.description,
                    subscription.predefined_id,
                    json.dumps(subscription.search_queries),
                    int(subscription.active),
                    _to_iso(now),
                    _to_iso(now),
                ),
            )
            subscription.id = cursor.lastrowid
            subscription.created_at = now
            subscription.updated_at = now
        return subscription

    def get_subscription(self, subscription_id: int) -> TopicSubscription | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM subscriptions WHERE id = ?",
                (subscription_id,),
            ).fetchone()
        return self._row_to_subscription(row) if row else None

    def get_subscription_by_predefined(self, predefined_id: str) -> TopicSubscription | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM subscriptions WHERE predefined_id = ?",
                (predefined_id,),
            ).fetchone()
        return self._row_to_subscription(row) if row else None

    def list_subscriptions(self, active_only: bool = False) -> list[TopicSubscription]:
        query = "SELECT * FROM subscriptions"
        params: tuple = ()
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY created_at ASC"

        with self.connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_subscription(row) for row in rows]

    def update_subscription(self, subscription: TopicSubscription) -> TopicSubscription:
        if subscription.id is None:
            raise ValueError("Subscription id is required for update")

        now = _utc_now()
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE subscriptions
                SET name = ?, description = ?, search_queries = ?, active = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    subscription.name,
                    subscription.description,
                    json.dumps(subscription.search_queries),
                    int(subscription.active),
                    _to_iso(now),
                    subscription.id,
                ),
            )
        subscription.updated_at = now
        return subscription

    def delete_subscription(self, subscription_id: int) -> bool:
        with self.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM subscriptions WHERE id = ?",
                (subscription_id,),
            )
        return cursor.rowcount > 0

    def set_subscription_active(self, subscription_id: int, active: bool) -> TopicSubscription | None:
        subscription = self.get_subscription(subscription_id)
        if subscription is None:
            return None
        subscription.active = active
        return self.update_subscription(subscription)

    def create_run(self, subscription_id: int, attempt: int = 1) -> ResearchRun:
        now = _utc_now()
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO research_runs
                    (subscription_id, status, attempt, started_at, documents_found)
                VALUES (?, ?, ?, ?, 0)
                """,
                (subscription_id, RunStatus.RUNNING.value, attempt, _to_iso(now)),
            )
        return ResearchRun(
            id=cursor.lastrowid,
            subscription_id=subscription_id,
            status=RunStatus.RUNNING,
            attempt=attempt,
            started_at=now,
        )

    def complete_run(
        self,
        run_id: int,
        *,
        status: RunStatus,
        output_path: str | None = None,
        documents_found: int = 0,
        error_message: str | None = None,
    ) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE research_runs
                SET status = ?, completed_at = ?, output_path = ?, documents_found = ?, error_message = ?
                WHERE id = ?
                """,
                (
                    status.value,
                    _to_iso(_utc_now()),
                    output_path,
                    documents_found,
                    error_message,
                    run_id,
                ),
            )

    def save_documents(self, run_id: int, documents: list[SourceDocument]) -> None:
        with self.connection() as conn:
            conn.executemany(
                """
                INSERT INTO source_documents
                    (run_id, title, url, source_type, origin, published_at, content_snippet, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        run_id,
                        doc.title,
                        doc.url,
                        doc.source_type,
                        doc.origin,
                        _to_iso(doc.published_at),
                        doc.content_snippet,
                        doc.content_hash,
                    )
                    for doc in documents
                ],
            )

    def get_run(self, run_id: int) -> ResearchRun | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM research_runs WHERE id = ?",
                (run_id,),
            ).fetchone()
        if not row:
            return None
        return ResearchRun(
            id=row["id"],
            subscription_id=row["subscription_id"],
            status=RunStatus(row["status"]),
            attempt=row["attempt"],
            started_at=_from_iso(row["started_at"]),
            completed_at=_from_iso(row["completed_at"]),
            error_message=row["error_message"],
            output_path=row["output_path"],
            documents_found=row["documents_found"],
        )

    def list_runs(self, subscription_id: int | None = None, limit: int = 20) -> list[ResearchRun]:
        query = "SELECT * FROM research_runs"
        params: list = []
        if subscription_id is not None:
            query += " WHERE subscription_id = ?"
            params.append(subscription_id)
        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)

        with self.connection() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            ResearchRun(
                id=row["id"],
                subscription_id=row["subscription_id"],
                status=RunStatus(row["status"]),
                attempt=row["attempt"],
                started_at=_from_iso(row["started_at"]),
                completed_at=_from_iso(row["completed_at"]),
                error_message=row["error_message"],
                output_path=row["output_path"],
                documents_found=row["documents_found"],
            )
            for row in rows
        ]

    def get_documents_for_run(self, run_id: int) -> list[SourceDocument]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM source_documents WHERE run_id = ? ORDER BY id ASC",
                (run_id,),
            ).fetchall()

        return [
            SourceDocument(
                title=row["title"],
                url=row["url"],
                source_type=row["source_type"],
                origin=row["origin"],
                published_at=_from_iso(row["published_at"]),
                content_snippet=row["content_snippet"],
                content_hash=row["content_hash"],
            )
            for row in rows
        ]
