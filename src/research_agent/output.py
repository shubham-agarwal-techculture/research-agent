"""Markdown output delivery."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from research_agent.models import RunOutput, SourceDocument


def _format_timestamp(value: datetime | None) -> str:
    if value is None:
        return "Unknown"
    return value.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")


def _render_document(doc: SourceDocument) -> str:
    lines = [
        f"### {doc.title}",
        "",
        f"- **Source:** {doc.origin} ({doc.source_type})",
        f"- **URL:** {doc.url}",
        f"- **Published:** {_format_timestamp(doc.published_at)}",
    ]
    if doc.content_snippet:
        lines.extend(["", doc.content_snippet])
    lines.append("")
    return "\n".join(lines)


def build_markdown(output: RunOutput) -> str:
    subscription = output.subscription
    run = output.run
    documents = output.documents

    lines = [
        f"# Research Digest: {subscription.name}",
        "",
        f"- **Run ID:** {run.id}",
        f"- **Started:** {_format_timestamp(run.started_at)}",
        f"- **Status:** {run.status.value}",
        f"- **Documents found:** {len(documents)}",
        "",
        "## Topic",
        "",
        subscription.description or "_No description provided._",
        "",
        "## Summary",
        "",
        output.summary,
        "",
        "## Sources Consulted",
        "",
    ]

    if not documents:
        lines.append("_No new documents matched this run._")
    else:
        for doc in documents:
            lines.append(_render_document(doc))

    lines.extend(
        [
            "",
            "---",
            "",
            "_Phase 0 output: raw research digest. Agentic synthesis arrives in Phase 1._",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown_output(output: RunOutput, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = (output.run.started_at or datetime.now(UTC)).strftime("%Y%m%d_%H%M%S")
    slug = output.subscription.name.lower().replace(" ", "-")
    filename = f"{timestamp}_{slug}_run-{output.run.id}.md"
    path = output_dir / filename
    path.write_text(build_markdown(output), encoding="utf-8")
    return path
