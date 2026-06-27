# Personal Research Agent

A personal idea machine that subscribes to research topics, runs twice-daily research pipelines, and delivers structured digests (Phase 0) on the path to full agentic idea synthesis.

## Documents

- [`description.md`](description.md) — Original product vision
- [`REQUIREMENTS.md`](REQUIREMENTS.md) — Requirements document (draft for review)

## Phase 0 (Current)

Phase 0 delivers the foundation described in `REQUIREMENTS.md`:

- **Subscriptions** — Custom and predefined topic CRUD (pause/resume/delete)
- **Scheduler** — Twice-daily configurable runs (timezone-aware)
- **Basic ingestion** — Pluggable connectors for arXiv and RSS
- **Simple output** — Markdown digests written to `data/outputs/`

Phase 1 will add the multi-step agentic analysis loop and idea synthesis.

## Web UI (decoupled frontend)

The project includes a **React SPA** (`frontend/`) and a **FastAPI REST API** that wraps the same core engine. Each user gets an isolated account with their own subscriptions and digests.

### Start the API

```powershell
research-agent api
# or: research-agent-api
```

API runs at `http://localhost:8001` by default. OpenAPI docs: `http://localhost:8001/docs`

> **Note:** Port 8000 is commonly used by other local apps. If registration returns "Not Found", another service may be bound to 8000 — start the API with `research-agent api` (port 8001) or set `api.port` in `config.yaml`.

### Start the frontend

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

UI runs at `http://localhost:5173` and talks to the API via `VITE_API_URL`.

### Web features

- User registration and login (JWT)
- Browse and subscribe to predefined topics
- Create custom subscriptions
- Trigger research runs and view markdown digests
- Per-user data isolation in SQLite

Set a strong `api.jwt_secret` in `config.yaml` (or `RESEARCH_AGENT_JWT_SECRET`) before deploying publicly.

## CLI quick start

### 1. Install

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 2. Configure

```powershell
Copy-Item config.example.yaml config.yaml
```

Edit `config.yaml` to set your timezone, run times, and RSS feeds.

### 3. Subscribe to topics

```powershell
# List predefined topics
research-agent topics

# Subscribe to a predefined topic
research-agent subscribe predefined ai-agents

# Or create a custom subscription
research-agent subscribe add "My Topic" -d "What I want to track" -q "topic keyword"
```

### 4. Run manually

```powershell
research-agent run
research-agent runs
```

Outputs are saved under `data/outputs/` as markdown files.

### 5. Start the scheduler

```powershell
research-agent serve
```

Runs all active subscriptions at the configured times (default: 09:00 and 21:00).

## CLI reference

| Command | Description |
|---------|-------------|
| `research-agent topics` | List predefined topics |
| `research-agent subscribe add` | Create custom subscription |
| `research-agent subscribe predefined <id>` | Subscribe to predefined topic |
| `research-agent subscribe list` | List subscriptions |
| `research-agent subscribe pause <id>` | Pause subscription |
| `research-agent subscribe resume <id>` | Resume subscription |
| `research-agent subscribe remove <id>` | Delete subscription |
| `research-agent run` | Run all active subscriptions now |
| `research-agent run -s <id>` | Run one subscription |
| `research-agent runs` | List recent runs |
| `research-agent serve` | Start twice-daily scheduler |
| `research-agent api` | Start REST API for web UI |

## Project layout

```
src/research_agent/
  api/             # FastAPI REST API
  cli.py           # CLI commands
  ...
frontend/          # React SPA (Vite + TypeScript)
predefined_topics.yaml
config.example.yaml
tests/
```

## Tests

```powershell
pytest
```

## Data

Local runtime data is stored under `data/` (gitignored):

- `data/research_agent.db` — subscriptions, runs, ingested documents
- `data/outputs/` — markdown digests
