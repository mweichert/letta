# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Letta (formerly MemGPT) is an open-source platform for building stateful AI agents with advanced memory capabilities. It's a Python-based REST/WebSocket API server with pluggable LLM provider adapters (OpenAI, Anthropic, Google Gemini, Ollama, vLLM, etc.).

## Development Commands

### Setup
```bash
eval $(uv env activate)
uv sync --all-extras
```

### Running the Server
```bash
uv run letta server                    # Default REST API server
uv run letta server --debug --reload   # Development mode with hot-reload
uv run letta server --type websocket   # WebSocket API
```

### Testing
```bash
uv run pytest -s tests                                    # All tests
uv run pytest -s tests/integration_test_example.py       # Single file
uv run pytest -s tests/integration_test_example.py::test_name  # Single test
```

### Formatting & Linting
```bash
uv run black . -l 140                  # Format code (required before PRs)
uv run ruff check --fix .              # Lint and auto-fix
uv run pre-commit run --all-files      # Run all pre-commit checks
```

### Database Migrations (Alembic)
```bash
uv run alembic upgrade head                              # Run pending migrations
uv run alembic revision --autogenerate -m "message"      # Create new migration
```

### Docker Development
```bash
docker compose -f compose.yaml -f development.compose.yml up  # Dev with hot-reload
```

## Architecture

### Core Components (`letta/`)

- **`agent.py`** - Core agent implementation with memory management and tool execution
- **`server/server.py`** - Main FastAPI application, request handling, and agent orchestration
- **`server/rest_api/`** - REST endpoint definitions (routers)
- **`server/ws_api/`** - WebSocket endpoint definitions
- **`functions/`** - Built-in tool implementations (web_search, run_code, etc.)
- **`adapters/`** - LLM provider adapters for different backends
- **`orm/`** - SQLAlchemy ORM models
- **`schemas/`** - Pydantic models for API request/response validation

### Data Flow

1. Client requests hit FastAPI endpoints in `server/rest_api/` or `server/ws_api/`
2. Server orchestrates agent operations via `server/server.py`
3. Agent (`agent.py`) manages memory blocks, context, and tool execution
4. LLM calls go through adapters in `adapters/` to various providers
5. State persists to PostgreSQL (with pgvector for embeddings) via SQLAlchemy ORM

### Database

- Uses SQLAlchemy with async support
- PostgreSQL with pgvector extension for production (SQLite for local dev)
- Migrations managed via Alembic in `alembic/`

## Code Style

- Line length: 140 characters
- Python target: 3.12
- Formatter: Black
- Linter: Ruff
- Async: pytest-asyncio in auto mode

## Key Environment Variables

```bash
LETTA_PG_URI="postgresql://letta:letta@localhost:5432/letta"  # PostgreSQL connection
```

## Adding Dependencies

```bash
uv add package_name              # Standard dependency
uv add --dev package_name        # Dev-only dependency
uv add --optional group package  # Optional group (postgres, redis, dev, etc.)
```

## Fork Management

This is a fork of `letta-ai/letta` with a declarative branch composition system.

### Branch Structure

| Branch | Purpose |
|--------|---------|
| `main` | Mirror of upstream `letta-ai/letta:main` |
| `fork` | Composed working branch (auto-built from feature branches) |
| `feature/*` | Fork-only feature branches |
| `bugfix/*` | Fork-only bugfix branches |
| `fork-infra/*` | Fork infrastructure (CI/CD, etc.) |
| `pr/*` | Branches for upstream PR contributions |

### Remotes

- `origin` - mweichert/letta (this fork)
- `upstream` - letta-ai/letta (upstream repo)

### Configuration

The fork composition is defined in `fork.yaml`:

```yaml
upstream:
  remote: upstream
  branch: main

base: main

branches:
  - name: feature/better-proxy-support
    base: main
    description: Remove hardcoded openai-proxy naming for custom base URLs
```

### Rebuilding the Fork

To sync with upstream, rebase all branches, and rebuild fork:

```bash
uv run scripts/build-fork.py           # Full rebuild
uv run scripts/build-fork.py --dry-run # Preview changes
```

This script:
1. Fetches upstream and resets `main`
2. Rebases each branch onto its base (topologically sorted)
3. Merges all branches into `fork`
4. Pushes everything to origin

### Adding a New Branch

1. Create from main: `git checkout -b feature/my-feature main`
2. Make changes, commit, push
3. Add entry to `fork.yaml`
4. Run `uv run scripts/build-fork.py`

### Removing a Branch

1. Remove entry from `fork.yaml`
2. Run `uv run scripts/build-fork.py`
3. Optionally delete the branch: `git branch -d feature/old && git push origin --delete feature/old`

### Contributing Upstream

For changes intended for upstream:
1. Create a `pr/*` branch from `main`
2. Make changes and push
3. Create PR via `gh pr create`
4. Do NOT add to `fork.yaml` (these should go upstream, not stay in fork)

## GHCR Workflow

Docker images are built and pushed to `ghcr.io/mweichert/letta` via GitHub Actions.

### Triggers

- Push to `fork` branch → builds with `latest`, version, and SHA tags
- Push any git tag → builds with the tag name and SHA
- Manual `workflow_dispatch`

### Tagging convention

```bash
# Create a fork release tag
git checkout fork
git tag 0.16.1-fork.1
git push origin 0.16.1-fork.1
```

This creates: `ghcr.io/mweichert/letta:0.16.1-fork.1`

### Workflow file

Located at `.github/workflows/build-ghcr.yml` (only on `fork` branch)
