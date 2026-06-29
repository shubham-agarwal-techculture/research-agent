"""Tests for source connectors."""

from research_agent.models import SourceDocument, TopicSubscription
from research_agent.sources import (
    ArxivConnector,
    RssConnector,
    content_hash,
    dedupe_documents,
    format_arxiv_search_query,
    matches_search_query,
)


ARXIV_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Sample Paper</title>
    <summary>Sample abstract about agentic AI.</summary>
    <id>http://arxiv.org/abs/1234.5678</id>
    <published>2026-06-01T00:00:00Z</published>
    <link rel="alternate" href="http://arxiv.org/abs/1234.5678"/>
  </entry>
</feed>
"""


def test_dedupe_documents():
    doc_a = SourceDocument(
        title="Same",
        url="https://example.com/a",
        source_type="paper",
        origin="arxiv",
        content_hash=content_hash("Same", "https://example.com/a"),
    )
    doc_b = SourceDocument(
        title="Same",
        url="https://example.com/a",
        source_type="paper",
        origin="arxiv",
        content_hash=content_hash("Same", "https://example.com/a"),
    )
    unique = dedupe_documents([doc_a, doc_b])
    assert len(unique) == 1


def test_arxiv_connector_parses_atom():
    captured_params: list[dict] = []

    class FakeResponse:
        text = ARXIV_ATOM

        def raise_for_status(self):
            return None

    class FakeClient:
        def get(self, url, params=None):
            captured_params.append(params or {})
            return FakeResponse()

    connector = ArxivConnector(client=FakeClient())
    subscription = TopicSubscription(name="AI", search_queries=["agentic AI"])
    docs = connector.fetch(subscription, max_results=5)
    assert len(docs) == 1
    assert docs[0].origin == "arxiv"
    assert "agentic" in docs[0].content_snippet.lower() or docs[0].title == "Sample Paper"
    assert captured_params[0]["search_query"] == 'all:"agentic AI"'
    assert captured_params[0]["sortBy"] == "relevance"


def test_format_arxiv_search_query():
    assert format_arxiv_search_query("semiconductor") == "all:semiconductor"
    assert format_arxiv_search_query("search algorithms") == 'all:"search algorithms"'


def test_matches_search_query_uses_word_boundaries():
    assert matches_search_query("agentic", "Progress in agentic AI systems")
    assert not matches_search_query("agentic", "nodes of a network are agents")
    assert matches_search_query("quantum", "Quantum error correction breakthrough")
    assert not matches_search_query("quantum", "ambiguous headline")


def test_rss_connector_filters_by_keyword():
    rss_payload = """
    <rss version="2.0">
      <channel>
        <title>Feed</title>
        <item>
          <title>Quantum error correction breakthrough</title>
          <link>https://example.com/qec</link>
          <description>Progress in quantum computing.</description>
          <pubDate>Mon, 01 Jun 2026 12:00:00 GMT</pubDate>
        </item>
        <item>
          <title>Unrelated sports news</title>
          <link>https://example.com/sports</link>
          <description>Nothing relevant here.</description>
        </item>
      </channel>
    </rss>
    """

    class FakeResponse:
        text = rss_payload

        def raise_for_status(self):
            return None

    class FakeClient:
        def get(self, url):
            return FakeResponse()

    from research_agent.config import RssFeedConfig

    connector = RssConnector(
        feeds=[RssFeedConfig(name="Test Feed", url="https://example.com/feed")],
        client=FakeClient(),
    )
    subscription = TopicSubscription(name="Quantum", search_queries=["quantum"])
    docs = connector.fetch(subscription, max_results=5)
    assert len(docs) == 1
    assert docs[0].url == "https://example.com/qec"


def test_rss_connector_rejects_substring_false_positive():
    rss_payload = """
    <rss version="2.0">
      <channel>
        <title>Feed</title>
        <item>
          <title>Agents in sports leagues</title>
          <link>https://example.com/agents</link>
          <description>Player agents negotiate contracts.</description>
        </item>
      </channel>
    </rss>
    """

    class FakeResponse:
        text = rss_payload

        def raise_for_status(self):
            return None

    class FakeClient:
        def get(self, url):
            return FakeResponse()

    from research_agent.config import RssFeedConfig

    connector = RssConnector(
        feeds=[RssFeedConfig(name="Test Feed", url="https://example.com/feed")],
        client=FakeClient(),
    )
    subscription = TopicSubscription(name="AI", search_queries=["agentic AI"])
    docs = connector.fetch(subscription, max_results=5)
    assert docs == []
