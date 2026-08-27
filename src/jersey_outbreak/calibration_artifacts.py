"""Versioned artifacts for C3 synthetic calibration experiments."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

from .calibration import CalibrationResult
from .calibration_schemas import CalibrationArtifactManifest
from .contracts import ArtifactRecord
from .hashing import canonical_json_bytes, sha256_bytes, sha256_file


@dataclass(frozen=True)
class CalibrationArtifact:
    """Written calibration artifact directory and validated manifest."""

    artifact_directory: Path
    manifest: CalibrationArtifactManifest


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


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def write_calibration_artifact(
    result: CalibrationResult, root: Path, output_dir: Path
) -> CalibrationArtifact:
    """Write every trial, recovery result and provenance reference."""

    root = root.resolve()
    output_dir = output_dir.resolve()
    config_hash = sha256_bytes(canonical_json_bytes(result.config.model_dump(mode="json")))
    parameter_hash = sha256_bytes(
        canonical_json_bytes(result.target_latent.parameters.model_dump(mode="json"))
    )
    observation_hash = sha256_bytes(
        canonical_json_bytes(result.target_observation.config.model_dump(mode="json"))
    )
    artifact_id = f"jos-calibration-m6-{result.config.study_id}-{result.logical_content_hash[:12]}"
    artifact_directory = output_dir / artifact_id
    artifact_directory.mkdir(parents=True, exist_ok=True)
    manifest_path = artifact_directory / "manifest.json"
    if manifest_path.exists():
        existing = CalibrationArtifactManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        if existing.logical_content_hash != result.logical_content_hash:
            raise ValueError(
                "immutable calibration artifact ID already exists with different content"
            )
        return CalibrationArtifact(artifact_directory, existing)

    trials_path = artifact_directory / "calibration_trials.parquet"
    results_path = artifact_directory / "calibration_results.json"
    diagnostics_path = artifact_directory / "diagnostics.json"
    config_path = artifact_directory / "calibration_config.json"
    trial_rows = [
        {
            "trial_number": row["trial_number"],
            "state": row["state"],
            "value": row["value"],
            "parameter_name": row.get("parameter_name", "reporting_delay_days"),
            "parameter_value": row.get("parameter_value", row.get("reporting_delay_days")),
            "reporting_delay_days": row.get("reporting_delay_days"),
            "transmission_beta": row.get("transmission_beta"),
            "training_replicates": row.get("training_replicates", 1),
            "objective_components": json.dumps(
                row["objective_components"], sort_keys=True, separators=(",", ":")
            ),
        }
        for row in result.trial_rows
    ]
    pq.write_table(
        pa.Table.from_pylist(
            trial_rows,
            schema=pa.schema(
                [
                    ("trial_number", pa.int64()),
                    ("state", pa.string()),
                    ("value", pa.float64()),
                    ("parameter_name", pa.string()),
                    ("parameter_value", pa.float64()),
                    ("reporting_delay_days", pa.int64()),
                    ("transmission_beta", pa.float64()),
                    ("training_replicates", pa.int64()),
                    ("objective_components", pa.string()),
                ]
            ),
        ),
        trials_path,
        compression="zstd",
        use_dictionary=True,
        write_statistics=True,
    )
    results_path.write_text(
        json.dumps(
            {
                "synthetic_truth": result.diagnostics["synthetic_truth"],
                "best_candidate": result.best_parameters,
                "recovery_error": (
                    result.diagnostics["recovery_error"]
                    if "recovery_error" in result.diagnostics
                    else result.diagnostics["recovery_error_days"]
                ),
                "heldout": result.diagnostics["heldout"],
                "target_latent_run_logical_content_hash": result.target_latent.logical_content_hash,
                "heldout_latent_run_logical_content_hash": (
                    result.heldout_latent.logical_content_hash
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    diagnostics_path.write_text(
        json.dumps(result.diagnostics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    config_path.write_text(
        json.dumps(result.config.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    output_paths = (trials_path, results_path, diagnostics_path, config_path)
    git_commit, dirty_worktree = _git_metadata(root)
    output_artifacts = [
        ArtifactRecord(
            path=_relative_path(path, root),
            sha256=sha256_file(path),
            size_bytes=path.stat().st_size,
        )
        for path in output_paths
    ]
    is_delay = result.config.hidden_parameter == "reporting_delay_days"
    recovery_error = float(
        result.diagnostics["recovery_error"]
        if "recovery_error" in result.diagnostics
        else result.diagnostics["recovery_error_days"]
    )
    recovery_tolerance = float(
        result.diagnostics["recovery_tolerance"]
        if "recovery_tolerance" in result.diagnostics
        else result.config.recovery_tolerance_days
    )
    heldout_recovery_error = float(
        result.diagnostics["heldout"].get("recovery_error")
        if "recovery_error" in result.diagnostics["heldout"]
        else result.diagnostics["heldout"]["recovery_error_days"]
    )
    manifest = CalibrationArtifactManifest(
        artifact_id=artifact_id,
        study_id=result.config.study_id,
        status=result.diagnostics["status"],
        target_latent_run_logical_content_hash=result.target_latent.logical_content_hash,
        heldout_latent_run_logical_content_hash=result.heldout_latent.logical_content_hash,
        calibration_config_hash=config_hash,
        disease_parameter_hash=parameter_hash,
        observation_parameter_hash=observation_hash,
        logical_content_hash=result.logical_content_hash,
        trial_count=result.config.trial_count,
        parameter_name=result.config.hidden_parameter,
        recovered_parameter_value=float(next(iter(result.best_parameters.values()))),
        synthetic_truth_value=float(
            result.config.synthetic_truth_beta
            if result.config.hidden_parameter == "transmission_beta"
            else result.config.synthetic_truth_delay_days
        ),
        recovery_error=recovery_error,
        recovery_tolerance=recovery_tolerance,
        recovery_error_days=(result.diagnostics["recovery_error_days"] if is_delay else None),
        recovery_tolerance_days=(result.config.recovery_tolerance_days if is_delay else None),
        heldout_objective=result.diagnostics["heldout"]["objective_components"][
            "reported_case_squared_error"
        ]
        if is_delay
        else result.diagnostics["heldout"]["objective_components"]["objective"],
        heldout_recovery_error=heldout_recovery_error,
        heldout_recovery_error_days=(
            result.diagnostics["heldout"]["recovery_error_days"] if is_delay else None
        ),
        heldout_passed=result.diagnostics["heldout"]["passed"],
        created_at=datetime.now(UTC).isoformat(),
        git_commit=git_commit,
        dirty_worktree_flag=dirty_worktree,
        runtime_seconds=result.runtime_seconds,
        output_artifacts=output_artifacts,
    )
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return CalibrationArtifact(artifact_directory, manifest)
