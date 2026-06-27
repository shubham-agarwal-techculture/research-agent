"""CLI entry point."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Annotated, Optional

import typer

from research_agent.config import load_config
from research_agent.pipeline import create_pipeline
from research_agent.scheduler import SchedulerService

app = typer.Typer(
    name="research-agent",
    help="Personal Research Agent — Phase 0 foundation CLI",
    no_args_is_help=True,
)

subscribe_app = typer.Typer(help="Manage topic subscriptions")
app.add_typer(subscribe_app, name="subscribe")


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def _resolve_config(config: Path | None) -> tuple:
    cfg = load_config(config)
    pipeline, subscriptions = create_pipeline(cfg)
    return cfg, pipeline, subscriptions


@subscribe_app.command("add")
def subscribe_add(
    name: Annotated[str, typer.Argument(help="Custom topic name")],
    description: Annotated[str, typer.Option("--description", "-d", help="Topic description")] = "",
    query: Annotated[
        Optional[list[str]],
        typer.Option("--query", "-q", help="Search query (repeatable)"),
    ] = None,
    config: Annotated[Path | None, typer.Option("--config", help="Path to config.yaml")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Create a custom topic subscription."""
    _setup_logging(verbose)
    _, _, subscriptions = _resolve_config(config)
    created = subscriptions.create_custom(name=name, description=description, search_queries=query)
    typer.echo(f"Created subscription #{created.id}: {created.name}")


@subscribe_app.command("predefined")
def subscribe_predefined(
    topic_id: Annotated[str, typer.Argument(help="Predefined topic id")],
    config: Annotated[Path | None, typer.Option("--config")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Subscribe to a predefined topic."""
    _setup_logging(verbose)
    _, _, subscriptions = _resolve_config(config)
    created = subscriptions.subscribe_predefined(topic_id)
    typer.echo(f"Subscribed to predefined topic #{created.id}: {created.name}")


@subscribe_app.command("list")
def subscribe_list(
    active_only: Annotated[bool, typer.Option("--active-only", help="Show only active subscriptions")] = False,
    config: Annotated[Path | None, typer.Option("--config")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """List topic subscriptions."""
    _setup_logging(verbose)
    _, _, subscriptions = _resolve_config(config)
    items = subscriptions.list(active_only=active_only)
    if not items:
        typer.echo("No subscriptions found.")
        raise typer.Exit(0)

    for item in items:
        status = "active" if item.active else "paused"
        typer.echo(f"[{item.id}] {item.name} ({status})")
        if item.description:
            typer.echo(f"  {item.description}")
        if item.search_queries:
            typer.echo(f"  queries: {', '.join(item.search_queries)}")


@subscribe_app.command("pause")
def subscribe_pause(
    subscription_id: Annotated[int, typer.Argument()],
    config: Annotated[Path | None, typer.Option("--config")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Pause a subscription."""
    _setup_logging(verbose)
    _, _, subscriptions = _resolve_config(config)
    updated = subscriptions.pause(subscription_id)
    if updated is None:
        typer.echo(f"Subscription #{subscription_id} not found.", err=True)
        raise typer.Exit(1)
    typer.echo(f"Paused subscription #{updated.id}: {updated.name}")


@subscribe_app.command("resume")
def subscribe_resume(
    subscription_id: Annotated[int, typer.Argument()],
    config: Annotated[Path | None, typer.Option("--config")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Resume a paused subscription."""
    _setup_logging(verbose)
    _, _, subscriptions = _resolve_config(config)
    updated = subscriptions.resume(subscription_id)
    if updated is None:
        typer.echo(f"Subscription #{subscription_id} not found.", err=True)
        raise typer.Exit(1)
    typer.echo(f"Resumed subscription #{updated.id}: {updated.name}")


@subscribe_app.command("remove")
def subscribe_remove(
    subscription_id: Annotated[int, typer.Argument()],
    config: Annotated[Path | None, typer.Option("--config")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Delete a subscription."""
    _setup_logging(verbose)
    _, _, subscriptions = _resolve_config(config)
    if not subscriptions.delete(subscription_id):
        typer.echo(f"Subscription #{subscription_id} not found.", err=True)
        raise typer.Exit(1)
    typer.echo(f"Deleted subscription #{subscription_id}")


@app.command("topics")
def list_topics(
    config: Annotated[Path | None, typer.Option("--config")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """List predefined topics available for subscription."""
    _setup_logging(verbose)
    _, _, subscriptions = _resolve_config(config)
    topics = subscriptions.list_predefined()
    for topic in topics:
        typer.echo(f"{topic['id']}: {topic['name']}")
        typer.echo(f"  {topic.get('description', '')}")


@app.command("run")
def run_once(
    subscription_id: Annotated[
        Optional[int],
        typer.Option("--subscription-id", "-s", help="Run a single subscription"),
    ] = None,
    config: Annotated[Path | None, typer.Option("--config")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Run research ingestion now (all active subscriptions by default)."""
    _setup_logging(verbose)
    _, pipeline, subscriptions = _resolve_config(config)

    if subscription_id is not None:
        subscription = subscriptions.get(subscription_id)
        if subscription is None:
            typer.echo(f"Subscription #{subscription_id} not found.", err=True)
            raise typer.Exit(1)
        run = pipeline.run_with_retry(subscription)
        typer.echo(json.dumps({"run_id": run.id, "status": run.status.value, "output": run.output_path}, indent=2))
        return

    runs = pipeline.run_all_active()
    payload = [
        {"run_id": run.id, "subscription_id": run.subscription_id, "status": run.status.value, "output": run.output_path}
        for run in runs
    ]
    typer.echo(json.dumps(payload, indent=2))


@app.command("runs")
def list_runs(
    subscription_id: Annotated[Optional[int], typer.Option("--subscription-id", "-s")] = None,
    limit: Annotated[int, typer.Option("--limit", "-n")] = 10,
    config: Annotated[Path | None, typer.Option("--config")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """List recent research runs."""
    _setup_logging(verbose)
    cfg, pipeline, _ = _resolve_config(config)
    runs = pipeline.db.list_runs(subscription_id=subscription_id, limit=limit)
    if not runs:
        typer.echo("No runs found.")
        raise typer.Exit(0)

    for run in runs:
        typer.echo(
            f"run #{run.id} | subscription #{run.subscription_id} | "
            f"{run.status.value} | docs={run.documents_found} | output={run.output_path or '-'}"
        )


@app.command("serve")
def serve_scheduler(
    config: Annotated[Path | None, typer.Option("--config")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Start the twice-daily scheduler daemon."""
    _setup_logging(verbose)
    cfg, pipeline, _ = _resolve_config(config)
    service = SchedulerService(cfg, pipeline)
    service.start()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
