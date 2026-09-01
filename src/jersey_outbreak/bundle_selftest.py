"""Relocation self-tests for release evidence scientific artifacts."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from . import __version__
from .contracts import NonEmptyString, StrictModel
from .hashing import canonical_json_bytes, sha256_bytes
from .scientific_verification import VerifiedScientificArtifact, verify_scientific_artifact


def _is_hex_hash(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


class VerificationStep(StrictModel):
    """One ordered operation in a bundle self-test."""

    step: NonEmptyString
    status: Literal["passed", "failed"]
    detail: NonEmptyString


class IdentityRecord(StrictModel):
    """One verifier result and all hashes exposed by its manifest."""

    artifact_type: NonEmptyString
    artifact_id: NonEmptyString
    hashes: dict[NonEmptyString, NonEmptyString]
    wall_time_seconds: float = Field(ge=0)

    @field_validator("hashes")
    @classmethod
    def validate_hashes(cls, value: dict[str, str]) -> dict[str, str]:
        for name, digest in value.items():
            if not _is_hex_hash(digest):
                raise ValueError(f"identity hash for {name} must be a 64-character hex digest")
        return value


class BundleIdentities(StrictModel):
    """Source/copy identities and the explicit agreement result."""

    model_config = ConfigDict(serialize_by_alias=True)
    artifact_type: str | None = None
    artifact_id: str | None = None
    source: IdentityRecord | None = None
    copy_identity: IdentityRecord | None = Field(default=None, alias="copy")
    agreement: dict[str, bool] = Field(default_factory=dict)


class BundleSelftestTranscript(StrictModel):
    """Machine-readable proof that an artifact survived relocation."""

    schema_version: Literal["1.0"] = "1.0"
    created_at: NonEmptyString
    git_commit: str | None = None
    dirty_worktree_flag: bool
    jos_version: NonEmptyString
    source_artifact: NonEmptyString
    copied_to: NonEmptyString
    steps: list[VerificationStep]
    identities: BundleIdentities
    status: Literal["passed", "failed"]
    logical_content_hash: NonEmptyString

    @field_validator("logical_content_hash")
    @classmethod
    def validate_logical_hash(cls, value: str) -> str:
        if not _is_hex_hash(value):
            raise ValueError("logical_content_hash must be a 64-character hex digest")
        return value

    @model_validator(mode="after")
    def derive_status(self) -> BundleSelftestTranscript:
        expected = "passed" if all(step.status == "passed" for step in self.steps) else "failed"
        if self.status != expected:
            raise ValueError("transcript status must be derived from the step statuses")
        return self


@dataclass(frozen=True)
class BundleSelftestResult:
    """Written transcript path and derived command status."""

    transcript_path: Path
    status: Literal["passed", "failed"]


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


def _code_root() -> Path:
    module_path = Path(__file__).resolve()
    for candidate in (module_path.parent, *module_path.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return module_path.parents[2]


def _transcript_path(source: Path, transcript_dir: Path | None) -> Path:
    if transcript_dir is None:
        if source.parent.name != "artifacts":
            raise ValueError(
                "artifact is not in a <bundle>/artifacts/ layout; provide --transcript-dir"
            )
        destination = source.parent.parent / "verification"
    else:
        destination = transcript_dir.expanduser().resolve()

    try:
        destination.relative_to(source)
    except ValueError:
        pass
    else:
        raise ValueError("transcript directory may not be inside the artifact directory")

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return destination / f"relocation-selftest-{stamp}.json"


def _manifest_hashes(
    verified: VerifiedScientificArtifact, artifact_directory: Path
) -> dict[str, str]:
    hashes: dict[str, str] = {}

    def add_payload(payload: dict[str, Any], prefix: str = "") -> None:
        for name, value in payload.items():
            if "hash" in name.lower() and isinstance(value, str) and _is_hex_hash(value):
                hashes[f"{prefix}{name}"] = value

    add_payload(verified.manifest_payload)
    for name, value in (
        ("scenario_hash", verified.scenario_hash),
        ("latent_outcome_hash", verified.latent_hash),
        ("artifact_bundle_hash", verified.bundle_hash),
        ("logical_content_hash", verified.logical_content_hash),
    ):
        if value is not None and _is_hex_hash(value):
            hashes[name] = value

    root_manifest = artifact_directory / "manifest.json"
    for nested_manifest in sorted(artifact_directory.rglob("manifest.json")):
        if nested_manifest == root_manifest:
            continue
        payload = json.loads(nested_manifest.read_text(encoding="utf-8"))
        relative_parent = nested_manifest.parent.relative_to(artifact_directory)
        prefix = f"embedded.{str(relative_parent).replace('/', '.')}."
        add_payload(payload, prefix)
    return hashes


def _identity(
    verified: VerifiedScientificArtifact, artifact_directory: Path, elapsed: float
) -> IdentityRecord:
    return IdentityRecord(
        artifact_type=verified.artifact_type,
        artifact_id=verified.artifact_id,
        hashes=_manifest_hashes(verified, artifact_directory),
        wall_time_seconds=elapsed,
    )


def _detail(error: BaseException) -> str:
    return f"{type(error).__name__}: {error}"


def _make_transcript(
    *,
    created_at: str,
    git_commit: str | None,
    dirty_worktree_flag: bool,
    source_artifact: Path,
    copied_to: Path,
    steps: list[VerificationStep],
    identities: BundleIdentities,
) -> BundleSelftestTranscript:
    status: Literal["passed", "failed"] = (
        "passed" if all(step.status == "passed" for step in steps) else "failed"
    )
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "git_commit": git_commit,
        "dirty_worktree_flag": dirty_worktree_flag,
        "jos_version": __version__,
        "source_artifact": str(source_artifact),
        "copied_to": str(copied_to),
        "steps": [step.model_dump(mode="json") for step in steps],
        "identities": identities.model_dump(mode="json", by_alias=True),
        "status": status,
    }
    logical_content_hash = sha256_bytes(canonical_json_bytes(payload))
    return BundleSelftestTranscript(
        created_at=created_at,
        git_commit=git_commit,
        dirty_worktree_flag=dirty_worktree_flag,
        jos_version=__version__,
        source_artifact=str(source_artifact),
        copied_to=str(copied_to),
        steps=steps,
        identities=identities,
        status=status,
        logical_content_hash=logical_content_hash,
    )


def _write_transcript(path: Path, transcript: BundleSelftestTranscript) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(transcript.model_dump(mode="json", by_alias=True), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def run_bundle_selftest(
    artifact_directory: Path,
    *,
    transcript_dir: Path | None = None,
    keep_copy: bool = False,
) -> BundleSelftestResult:
    """Verify an artifact in a temporary relocation and retain its transcript."""

    source = artifact_directory.expanduser().resolve()
    manifest_path = source / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("artifact directory must contain manifest.json")
    transcript_path = _transcript_path(source, transcript_dir)
    git_commit, dirty_worktree = _git_metadata(_code_root())
    created_at = datetime.now(UTC).isoformat()
    copy_root = Path(tempfile.mkdtemp(prefix="jos-bundle-selftest-"))
    copied_to = copy_root / source.name
    steps: list[VerificationStep] = []
    source_identity: IdentityRecord | None = None
    copy_identity: IdentityRecord | None = None

    try:
        try:
            shutil.copytree(source, copied_to)
            steps.append(
                VerificationStep(
                    step="copy_artifact",
                    status="passed",
                    detail=f"Copied artifact to {copied_to}",
                )
            )
        except Exception as exc:
            steps.append(
                VerificationStep(step="copy_artifact", status="failed", detail=_detail(exc))
            )

        if copied_to.is_dir():
            started = perf_counter()
            try:
                verified_copy = verify_scientific_artifact(copied_to)
                elapsed = perf_counter() - started
                copy_identity = _identity(verified_copy, copied_to, elapsed)
                steps.append(
                    VerificationStep(
                        step="verify_copy",
                        status="passed",
                        detail=(
                            f"{verified_copy.artifact_type} {verified_copy.artifact_id} "
                            f"verified in {elapsed:.6f}s at {copied_to}"
                        ),
                    )
                )
            except Exception as exc:
                steps.append(
                    VerificationStep(step="verify_copy", status="failed", detail=_detail(exc))
                )
        else:
            steps.append(
                VerificationStep(
                    step="verify_copy",
                    status="failed",
                    detail="copy was not created",
                )
            )

        started = perf_counter()
        try:
            verified_source = verify_scientific_artifact(source)
            elapsed = perf_counter() - started
            source_identity = _identity(verified_source, source, elapsed)
            steps.append(
                VerificationStep(
                    step="verify_original",
                    status="passed",
                    detail=(
                        f"{verified_source.artifact_type} {verified_source.artifact_id} "
                        f"verified in {elapsed:.6f}s at {source}"
                    ),
                )
            )
        except Exception as exc:
            steps.append(
                VerificationStep(step="verify_original", status="failed", detail=_detail(exc))
            )

        if source_identity is not None and copy_identity is not None:
            artifact_id_agrees = source_identity.artifact_id == copy_identity.artifact_id
            bundle_hash_agrees = (
                source_identity.hashes.get("artifact_bundle_hash")
                == copy_identity.hashes.get("artifact_bundle_hash")
                and source_identity.hashes.get("artifact_bundle_hash") is not None
            )
            agreement = {
                "artifact_id": artifact_id_agrees,
                "artifact_bundle_hash": bundle_hash_agrees,
            }
            identities = BundleIdentities(
                artifact_type=source_identity.artifact_type,
                artifact_id=source_identity.artifact_id,
                source=source_identity,
                copy=copy_identity,
                agreement=agreement,
            )
            compare_status: Literal["passed", "failed"] = (
                "passed" if all(agreement.values()) else "failed"
            )
            compare_detail = (
                f"artifact_id_agrees={artifact_id_agrees}; "
                f"artifact_bundle_hash_agrees={bundle_hash_agrees}"
            )
        else:
            available_identity = source_identity or copy_identity
            identities = BundleIdentities(
                artifact_type=available_identity.artifact_type if available_identity else None,
                artifact_id=available_identity.artifact_id if available_identity else None,
                source=source_identity,
                copy=copy_identity,
            )
            compare_status = "failed"
            compare_detail = "identity comparison unavailable because a verification failed"
        steps.append(
            VerificationStep(
                step="compare_identities",
                status=compare_status,
                detail=compare_detail,
            )
        )

        try:
            if keep_copy:
                cleanup_detail = f"Temporary copy retained at {copy_root}"
            else:
                shutil.rmtree(copy_root)
                cleanup_detail = "Temporary copy removed"
            steps.append(
                VerificationStep(
                    step="cleanup_copy",
                    status="passed",
                    detail=cleanup_detail,
                )
            )
        except Exception as exc:
            steps.append(
                VerificationStep(step="cleanup_copy", status="failed", detail=_detail(exc))
            )

        transcript = _make_transcript(
            created_at=created_at,
            git_commit=git_commit,
            dirty_worktree_flag=dirty_worktree,
            source_artifact=source,
            copied_to=copied_to,
            steps=steps,
            identities=identities,
        )
        _write_transcript(transcript_path, transcript)
        return BundleSelftestResult(transcript_path, transcript.status)
    finally:
        if not keep_copy and copy_root.exists():
            shutil.rmtree(copy_root, ignore_errors=True)
