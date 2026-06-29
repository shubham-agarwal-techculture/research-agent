"""Pluggable research source connectors."""

from __future__ import annotations

import hashlib
import logging
import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Iterable

import feedparser
import httpx

from research_agent.config import AppConfig, RssFeedConfig
from research_agent.models import SourceDocument, TopicSubscription

logger = logging.getLogger(__name__)

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def content_hash(title: str, url: str) -> str:
    payload = f"{title.strip().lower()}|{url.strip().lower()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def format_arxiv_search_query(query: str) -> str:
    """Build an arXiv API search_query value for a subscription keyword."""
    query = query.strip()
    if not query:
        return "all:*"
    if " " in query:
        return f'all:"{query}"'
    return f"all:{query}"


def matches_search_query(query: str, text: str) -> bool:
    """Match a query against text using word boundaries (avoids substring false positives)."""
    query = query.strip().lower()
    if not query:
        return False
    pattern = r"(?<!\w)" + re.escape(query).replace(r"\ ", r"\s+") + r"(?!\w)"
    return re.search(pattern, text.lower()) is not None


def dedupe_documents(documents: Iterable[SourceDocument]) -> list[SourceDocument]:
    seen: set[str] = set()
    unique: list[SourceDocument] = []
    for doc in documents:
        key = doc.content_hash or content_hash(doc.title, doc.url)
        if key in seen:
            continue
        seen.add(key)
        doc.content_hash = key
        unique.append(doc)
    return unique


class SourceConnector(ABC):
    name: str

    @abstractmethod
    def fetch(self, subscription: TopicSubscription, max_results: int) -> list[SourceDocument]:
        raise NotImplementedError


class ArxivConnector(SourceConnector):
    name = "arxiv"
    API_URL = "https://export.arxiv.org/api/query"

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=30.0)

    def fetch(self, subscription: TopicSubscription, max_results: int) -> list[SourceDocument]:
        documents: list[SourceDocument] = []
        per_query = max(1, max_results // max(len(subscription.search_queries), 1))

        for query in subscription.search_queries:
            params = {
                "search_query": format_arxiv_search_query(query),
                "start": 0,
                "max_results": per_query,
                "sortBy": "relevance",
                "sortOrder": "descending",
            }
            try:
                response = self.client.get(self.API_URL, params=params)
                response.raise_for_status()
                documents.extend(self._parse_atom(response.text))
            except httpx.HTTPError as exc:
                logger.warning("arXiv fetch failed for query %r: %s", query, exc)

        return dedupe_documents(documents)[:max_results]

    def _parse_atom(self, payload: str) -> list[SourceDocument]:
        root = ET.fromstring(payload)
        documents: list[SourceDocument] = []

        for entry in root.findall("atom:entry", ATOM_NS):
            title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
            summary = (entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").strip()
            link = ""
            for link_el in entry.findall("atom:link", ATOM_NS):
                if link_el.attrib.get("rel") == "alternate":
                    link = link_el.attrib.get("href", "")
                    break
            if not link:
                link = entry.findtext("atom:id", default="", namespaces=ATOM_NS) or ""

            published_raw = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
            published_at = None
            if published_raw:
                published_at = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))

            documents.append(
                SourceDocument(
                    title=re.sub(r"\s+", " ", title),
                    url=link,
                    source_type="paper",
                    origin="arxiv",
                    published_at=published_at,
                    content_snippet=re.sub(r"\s+", " ", summary)[:1200],
                    content_hash=content_hash(title, link),
                )
            )

        return documents


class RssConnector(SourceConnector):
    name = "rss"

    def __init__(self, feeds: list[RssFeedConfig], client: httpx.Client | None = None) -> None:
        self.feeds = feeds
        self.client = client or httpx.Client(timeout=30.0, follow_redirects=True)

    def fetch(self, subscription: TopicSubscription, max_results: int) -> list[SourceDocument]:
        documents: list[SourceDocument] = []
        queries = [query for query in subscription.search_queries if query.strip()]

        for feed in self.feeds:
            try:
                response = self.client.get(feed.url)
                response.raise_for_status()
                parsed = feedparser.parse(response.text)
            except httpx.HTTPError as exc:
                logger.warning("RSS fetch failed for %s: %s", feed.name, exc)
                continue

            for entry in parsed.entries:
                title = getattr(entry, "title", "") or ""
                summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
                link = getattr(entry, "link", "") or ""
                haystack = f"{title} {summary}"
                if queries and not any(matches_search_query(query, haystack) for query in queries):
                    continue

                published_at = None
                if getattr(entry, "published", None):
                    try:
                        published_at = parsedate_to_datetime(entry.published).astimezone(UTC)
                    except (TypeError, ValueError):
                        published_at = None

                documents.append(
                    SourceDocument(
                        title=re.sub(r"\s+", " ", title.strip()),
                        url=link,
                        source_type="article",
                        origin=feed.name,
                        published_at=published_at,
                        content_snippet=re.sub(r"<[^>]+>", "", summary)[:1200],
                        content_hash=content_hash(title, link),
                    )
                )

        return dedupe_documents(documents)[:max_results]


def build_connectors(config: AppConfig, client: httpx.Client | None = None) -> list[SourceConnector]:
    enabled = set(config.ingestion.enabled_sources)
    connectors: list[SourceConnector] = []

    if "arxiv" in enabled:
        connectors.append(ArxivConnector(client=client))
    if "rss" in enabled:
        connectors.append(RssConnector(feeds=config.rss_feeds, client=client))

    return connectors
