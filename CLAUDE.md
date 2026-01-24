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

## Important: Check Current Branch

At the start of each conversation, note the current branch from the git status context.

### Creating New Feature/Bugfix Branches

When asked to create a new `feature/*` or `bugfix/*` branch, **always use AskUserQuestion** to confirm which branch to base it on:

1. **Default option**: `main` (Recommended) - most changes should branch from here
2. **Additional options**: List any existing `feature/*` and `bugfix/*` branches from `fork.yaml` (in parent directory)

**If the user selects `main`**: First sync with upstream before creating the branch:
```bash
git fetch upstream && git checkout main && git reset --hard upstream/main
```

Then create and checkout the new branch from `main`.

**If the user selects another branch**: Simply create the new branch from that branch (it will be rebased during fork builds).

The `fork` branch is the composed working branch - never branch from it directly.

## Fork Management

This is a fork of `letta-ai/letta` with a declarative branch composition system.

**Fork management infrastructure is in the parent directory:** `~/Projects/forks/letta/`

See `~/Projects/forks/letta/CLAUDE.md` for:
- Fork composition configuration (`fork.yaml`)
- Build script (`scripts/build-fork.py`)
- Branch documentation (`branches/`)
- Detailed fork management instructions

### Quick Reference

```bash
cd ~/Projects/forks/letta
uv run scripts/build-fork.py           # Full rebuild
uv run scripts/build-fork.py --dry-run # Preview changes
```

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
