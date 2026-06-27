"""Uvicorn entry point for the REST API."""

from __future__ import annotations

import uvicorn

from research_agent.config import load_config


def main() -> None:
    config = load_config()
    uvicorn.run(
        "research_agent.api.app:app",
        host=config.api.host,
        port=config.api.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
