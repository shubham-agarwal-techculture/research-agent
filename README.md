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

## Quick start

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

## Project layout

```
src/research_agent/
  cli.py           # CLI commands
  config.py        # YAML + env configuration
  subscriptions.py # Subscription CRUD
  sources.py       # arXiv + RSS connectors
  pipeline.py      # Run orchestration + retries
  scheduler.py     # APScheduler integration
  output.py        # Markdown delivery
  storage.py       # SQLite persistence
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
