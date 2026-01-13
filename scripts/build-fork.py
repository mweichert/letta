#!/usr/bin/env python3
"""
Build the fork branch from fork.yaml configuration.

Usage:
    uv run scripts/build-fork.py           # Full rebuild: sync + rebase + build + push
    uv run scripts/build-fork.py --dry-run # Preview what would happen (no changes)
"""

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class UpstreamConfig:
    remote: str
    branch: str


@dataclass
class BranchConfig:
    name: str
    base: str
    description: str


@dataclass
class ForkConfig:
    upstream: UpstreamConfig
    base: str
    branches: list[BranchConfig]


class ForkBuilder:
    def __init__(self, config: ForkConfig, dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run
        self.original_branch = self._get_current_branch()

    def _get_current_branch(self) -> str:
        """Get the current git branch name."""
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def git_run(self, *args: str, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
        """Execute a git command with consistent error handling."""
        cmd = ["git", *args]
        cmd_str = " ".join(cmd)

        if self.dry_run:
            print(f"  [dry-run] {cmd_str}")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        print(f"  $ {cmd_str}")
        return subprocess.run(
            cmd,
            check=check,
            capture_output=capture,
            text=True,
        )

    def sync_upstream(self) -> None:
        """Fetch upstream and reset base branch to match."""
        print(f"\n=== Syncing with upstream ({self.config.upstream.remote}/{self.config.upstream.branch}) ===")

        self.git_run("fetch", self.config.upstream.remote)
        self.git_run("checkout", self.config.base)
        self.git_run("reset", "--hard", f"{self.config.upstream.remote}/{self.config.upstream.branch}")
        self.git_run("push", "origin", self.config.base, "--force-with-lease")

    def _topological_sort(self) -> list[BranchConfig]:
        """Sort branches so dependencies are rebased before dependents."""
        # Build dependency graph
        branch_map = {b.name: b for b in self.config.branches}
        sorted_branches: list[BranchConfig] = []
        visited: set[str] = set()

        def visit(branch: BranchConfig) -> None:
            if branch.name in visited:
                return
            visited.add(branch.name)

            # If this branch depends on another branch (not base), visit that first
            if branch.base != self.config.base and branch.base in branch_map:
                visit(branch_map[branch.base])

            sorted_branches.append(branch)

        for branch in self.config.branches:
            visit(branch)

        return sorted_branches

    def rebase_branches(self) -> None:
        """Rebase all branches onto their base branches."""
        print("\n=== Rebasing branches ===")

        sorted_branches = self._topological_sort()

        for branch in sorted_branches:
            print(f"\nRebasing {branch.name} onto {branch.base}...")
            self.git_run("checkout", branch.name)
            self.git_run("rebase", branch.base)
            self.git_run("push", "origin", branch.name, "--force-with-lease")

    def build_fork(self) -> None:
        """Build the fork branch by merging all feature branches."""
        print("\n=== Building fork branch ===")

        # Start from base
        self.git_run("checkout", self.config.base)

        # Delete and recreate fork branch
        self.git_run("branch", "-D", "fork", check=False)
        self.git_run("checkout", "-b", "fork")

        # Merge each branch
        for branch in self.config.branches:
            print(f"\nMerging {branch.name}...")
            result = self.git_run("merge", "--no-edit", branch.name, check=False)
            if result.returncode != 0:
                print(f"\nError: Merge conflict while merging {branch.name}")
                print("Resolve conflicts, then run: git merge --continue")
                print(f"Or abort with: git merge --abort && git checkout {self.original_branch}")
                sys.exit(1)

        # Push fork branch
        self.git_run("push", "origin", "fork", "--force-with-lease")

    def run(self) -> None:
        """Run the full rebuild: sync + rebase + build."""
        if self.dry_run:
            print("=== DRY RUN MODE - No changes will be made ===")

        # Check for uncommitted changes
        result = subprocess.run(["git", "diff-index", "--quiet", "HEAD", "--"], capture_output=True)
        if result.returncode != 0:
            print("Error: You have uncommitted changes. Please commit or stash them first.")
            sys.exit(1)

        self.sync_upstream()
        self.rebase_branches()
        self.build_fork()

        print("\n=== Done! ===")
        print(f"\nCommits in fork ahead of {self.config.base}:")
        subprocess.run(["git", "log", "--oneline", f"{self.config.base}..fork"])


def load_config(config_path: Path) -> ForkConfig:
    """Load and parse the YAML configuration file."""
    with open(config_path) as f:
        data = yaml.safe_load(f)

    upstream = UpstreamConfig(
        remote=data["upstream"]["remote"],
        branch=data["upstream"]["branch"],
    )

    branches = [
        BranchConfig(
            name=b["name"],
            base=b["base"],
            description=b.get("description", ""),
        )
        for b in data["branches"]
    ]

    return ForkConfig(
        upstream=upstream,
        base=data["base"],
        branches=branches,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build fork branch from fork.yaml configuration",
        epilog="""
What this script does:
  1. Sync      Fetch upstream, reset 'main' to upstream/main, push main
  2. Rebase    Rebase each branch onto its base (topologically sorted)
  3. Build     Create 'fork' from main, merge all branches, push fork

All changes are pushed to origin automatically.

Configuration is read from fork.yaml in the repository root.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing (no git commands run)")
    args = parser.parse_args()

    # Find config file
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    config_path = repo_root / "fork.yaml"

    if not config_path.exists():
        print(f"Error: {config_path} not found")
        sys.exit(1)

    config = load_config(config_path)
    builder = ForkBuilder(config, dry_run=args.dry_run)
    builder.run()


if __name__ == "__main__":
    main()
