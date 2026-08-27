"""Immutable, hash-checked verification manifests for milestone handoffs."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import field_validator

from .contracts import ArtifactRecord, NonEmptyString, StrictModel
from .hashing import canonical_json_bytes, sha256_bytes, sha256_file


class VerificationManifest(StrictModel):
    """A small archive index tying results to code and parent logical hashes."""

    schema_version: NonEmptyString = "1.0"
    verification_id: NonEmptyString
    milestone: NonEmptyString = "C3"
    status: Literal["passed", "failed"]
    git_commit: str | None = None
    dirty_worktree_flag: bool
    parent_hashes: dict[str, NonEmptyString]
    layer_hashes: dict[str, NonEmptyString]
    source_manifest_hashes: dict[str, NonEmptyString]
    command_results: dict[str, Any]
    benchmarks: dict[str, Any]
    retention_policy: dict[str, Any]
    logical_content_hash: NonEmptyString
    created_at: NonEmptyString
    output_artifacts: list[ArtifactRecord]

    @field_validator("layer_hashes", "source_manifest_hashes")
    @classmethod
    def validate_artifact_hashes(cls, value: dict[str, str]) -> dict[str, str]:
        for name, digest in value.items():
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError(f"verification hash for {name} must be a 64-character hex digest")
        return value

    @field_validator("logical_content_hash")
    @classmethod
    def validate_logical_hash(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("verification logical_content_hash must be a 64-character hex digest")
        return value


@dataclass(frozen=True)
class VerificationArchive:
    """Location and validated manifest for one immutable verification archive."""

    archive_directory: Path
    manifest: VerificationManifest


def _git_metadata(root: Path) -> tuple[str | None, bool]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        return commit.stdout.strip() or None, bool(status.stdout.strip())
    except OSError:
        return None, True


def _artifact_records(directory: Path, paths: tuple[Path, ...]) -> list[ArtifactRecord]:
    return [
        ArtifactRecord(
            path=str(path.relative_to(directory)),
            sha256=sha256_file(path),
            size_bytes=path.stat().st_size,
        )
        for path in paths
    ]


def _validate_expected_hashes(actual: dict[str, str], expected: dict[str, str] | None) -> None:
    if expected is None:
        return
    for name, value in expected.items():
        if actual.get(name) != value:
            raise ValueError(f"verification parent hash mismatch for {name}")


def write_verification_archive(
    root: Path,
    output_dir: Path,
    *,
    verification_id: str,
    milestone: str = "C3",
    parent_hashes: dict[str, str],
    layer_hashes: dict[str, str],
    source_manifest_hashes: dict[str, str] | None = None,
    command_results: dict[str, Any] | None = None,
    benchmarks: dict[str, Any] | None = None,
    retention_policy: dict[str, Any] | None = None,
    require_clean: bool = True,
) -> VerificationArchive:
    """Write a content-addressed verification index and retained summaries.

    Generated simulation directories can remain outside Git, but their exact
    paths and hashes must be retained in a separately backed-up archive. A
    clean Git tree is required by default so a manifest cannot masquerade as a
    verified release while local code is modified.
    """

    root = root.resolve()
    archive_directory = output_dir.resolve() / verification_id
    archive_directory.mkdir(parents=True, exist_ok=True)
    git_commit, dirty_worktree = _git_metadata(root)
    if require_clean and dirty_worktree:
        raise RuntimeError("verification archive requires a clean Git worktree")
    source_manifest_hashes = source_manifest_hashes or {}
    command_results = command_results or {}
    benchmarks = benchmarks or {}
    retention_policy = retention_policy or {
        "git_tracked_code": "required",
        "generated_outputs": "external-retention-required",
        "manifest": "retain-with-generated-output-bundle",
    }
    payload = {
        "verification_id": verification_id,
        "milestone": milestone,
        "git_commit": git_commit,
        "dirty_worktree_flag": dirty_worktree,
        "parent_hashes": parent_hashes,
        "layer_hashes": layer_hashes,
        "source_manifest_hashes": source_manifest_hashes,
        "command_results": command_results,
        "benchmarks": benchmarks,
        "retention_policy": retention_policy,
    }
    logical_content_hash = sha256_bytes(canonical_json_bytes(payload))
    manifest_path = archive_directory / "manifest.json"
    if manifest_path.exists():
        existing = VerificationManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        if existing.logical_content_hash != logical_content_hash:
            raise ValueError("verification archive ID already exists with different content")
        return VerificationArchive(archive_directory, existing)

    summary_path = archive_directory / "verification_summary.json"
    summary_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifacts = _artifact_records(archive_directory, (summary_path,))
    manifest = VerificationManifest(
        verification_id=verification_id,
        milestone=milestone,
        status="passed",
        git_commit=git_commit,
        dirty_worktree_flag=dirty_worktree,
        parent_hashes=parent_hashes,
        layer_hashes=layer_hashes,
        source_manifest_hashes=source_manifest_hashes,
        command_results=command_results,
        benchmarks=benchmarks,
        retention_policy=retention_policy,
        logical_content_hash=logical_content_hash,
        created_at=datetime.now(UTC).isoformat(),
        output_artifacts=artifacts,
    )
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return VerificationArchive(archive_directory, manifest)


def verify_verification_archive(
    manifest_path: Path,
    *,
    expected_parent_hashes: dict[str, str] | None = None,
    expected_git_commit: str | None = None,
) -> dict[str, Any]:
    """Verify retained files and optionally enforce current parent identity."""

    manifest_path = manifest_path.resolve()
    manifest = VerificationManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    payload = {
        "verification_id": manifest.verification_id,
        "milestone": manifest.milestone,
        "git_commit": manifest.git_commit,
        "dirty_worktree_flag": manifest.dirty_worktree_flag,
        "parent_hashes": manifest.parent_hashes,
        "layer_hashes": manifest.layer_hashes,
        "source_manifest_hashes": manifest.source_manifest_hashes,
        "command_results": manifest.command_results,
        "benchmarks": manifest.benchmarks,
        "retention_policy": manifest.retention_policy,
    }
    if sha256_bytes(canonical_json_bytes(payload)) != manifest.logical_content_hash:
        raise ValueError("verification manifest logical content hash mismatch")
    _validate_expected_hashes(manifest.parent_hashes, expected_parent_hashes)
    if expected_git_commit is not None and manifest.git_commit != expected_git_commit:
        raise ValueError("verification archive Git commit does not match expected commit")
    checked = []
    for artifact in manifest.output_artifacts:
        artifact_path = manifest_path.parent / artifact.path
        if not artifact_path.exists():
            raise FileNotFoundError(f"retained verification artifact is missing: {artifact.path}")
        observed_hash = sha256_file(artifact_path)
        if observed_hash != artifact.sha256 or artifact_path.stat().st_size != artifact.size_bytes:
            raise ValueError(f"retained verification artifact hash mismatch: {artifact.path}")
        checked.append(artifact.path)
    return {
        "status": "passed",
        "verification_id": manifest.verification_id,
        "git_commit": manifest.git_commit,
        "dirty_worktree_flag": manifest.dirty_worktree_flag,
        "checked_artifacts": checked,
        "parent_hashes": manifest.parent_hashes,
    }
