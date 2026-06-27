"""API integration tests."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from research_agent.api.app import create_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"""
data_dir: {tmp_path / "data"}
api:
  jwt_secret: test-secret-key
  cors_origins:
    - http://localhost:5173
scheduler:
  retry:
    max_attempts: 1
    delay_seconds: 0
""".strip(),
        encoding="utf-8",
    )

    topics_path = tmp_path / "predefined_topics.yaml"
    topics_path.write_text(
        """
topics:
  - id: ai-agents
    name: AI Agents
    description: Agentic workflows
    search_queries:
      - agentic AI
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    (tmp_path / "predefined_topics.yaml").write_text(topics_path.read_text(encoding="utf-8"), encoding="utf-8")

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def auth_header(client: TestClient, email: str = "user@example.com", password: str = "password123") -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "display_name": "Test User"},
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_login_and_me(client: TestClient):
    headers = auth_header(client)
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "user@example.com"
    assert payload["display_name"] == "Test User"


def test_subscription_and_predefined_flow(client: TestClient):
    headers = auth_header(client, email="researcher@example.com")

    topics = client.get("/api/topics/predefined", headers=headers)
    assert topics.status_code == 200
    assert topics.json()[0]["id"] == "ai-agents"

    created = client.post("/api/subscriptions", headers=headers, json={
        "name": "Custom Topic",
        "description": "My interests",
        "search_queries": ["quantum"],
    })
    assert created.status_code == 201
    sub_id = created.json()["id"]

    predefined = client.post("/api/subscriptions/predefined/ai-agents", headers=headers)
    assert predefined.status_code == 200

    listed = client.get("/api/subscriptions", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 2

    paused = client.post(f"/api/subscriptions/{sub_id}/pause", headers=headers)
    assert paused.status_code == 200
    assert paused.json()["active"] is False

    deleted = client.delete(f"/api/subscriptions/{sub_id}", headers=headers)
    assert deleted.status_code == 204


def test_runs_require_auth(client: TestClient):
    response = client.get("/api/runs")
    assert response.status_code == 401
