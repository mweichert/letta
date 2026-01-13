# Fork Management

## Purpose

Infrastructure for managing this fork of Letta, including:
- Declarative fork composition (`fork.yaml`)
- Build script to sync, rebase, and rebuild the fork branch
- GHCR workflow for Docker image builds
- Branch documentation

## Components

### Fork Composition System

The `fork` branch is built declaratively from `fork.yaml`:

```yaml
upstream:
  remote: upstream
  branch: main

base: main

branches:
  - name: feature/better-proxy-support
    base: main
    docs: branches/feature/better-proxy-support.md
```

**Rebuild the fork:**
```bash
uv run scripts/build-fork.py           # Full rebuild
uv run scripts/build-fork.py --dry-run # Preview
```

### GHCR Workflow

GitHub Actions workflow to build and push Docker images to `ghcr.io/mweichert/letta`.

**Triggers:**
- Push to `fork` branch → `latest`, version, SHA tags
- Push git tag → tag name, SHA

**Usage:**
```bash
git checkout fork
git tag 0.16.1-fork.1
git push origin 0.16.1-fork.1
# Creates: ghcr.io/mweichert/letta:0.16.1-fork.1
```

### Branch Documentation

Each branch has documentation in `branches/<type>/<name>.md` linked from `fork.yaml`.

## Files

- `fork.yaml` - Fork composition configuration
- `scripts/build-fork.py` - Build script
- `branches/` - Branch documentation
- `.github/workflows/build-ghcr.yml` - GHCR workflow
- `CLAUDE.md` - Development guidance (includes fork management docs)
