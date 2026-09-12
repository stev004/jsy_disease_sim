"""Shared fail-closed Git provenance lookup."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _git_metadata(root: Path) -> tuple[str | None, bool]:
    """Return ``(commit, dirty)`` or fail closed when Git provenance is unknown."""

    try:
        commit_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None, True

    if commit_result.returncode != 0 or status_result.returncode != 0:
        return None, True
    commit = commit_result.stdout.strip()
    if not commit:
        return None, True
    return commit, bool(status_result.stdout.strip())
