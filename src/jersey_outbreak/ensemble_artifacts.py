"""Persisted tables and provenance manifests for C3 ensembles."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from .contracts import ArtifactRecord
from .ensemble import ComparisonResult, EnsembleResult
from .ensemble_schemas import ComparisonArtifactManifest, EnsembleArtifactManifest
from .hashing import canonical_json_bytes, sha256_bytes, sha256_file


@dataclass(frozen=True)
class EnsembleArtifact:
    """Written ensemble artifact directory and validated manifest."""

    artifact_directory: Path
    manifest: EnsembleArtifactManifest


@dataclass(frozen=True)
class ComparisonArtifact:
    """Written matched-seed comparison artifact directory and manifest."""

    artifact_directory: Path
    manifest: ComparisonArtifactManifest


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


def _write_table(
    path: Path, rows: list[dict[str, Any]] | tuple[dict[str, Any], ...], schema: pa.Schema
) -> None:
    if rows:
        table = pa.Table.from_pylist(list(rows), schema=schema)
    else:
        table = pa.Table.from_arrays(
            [pa.array([], type=field.type) for field in schema], schema=schema
        )
    pq.write_table(table, path, compression="zstd", use_dictionary=True, write_statistics=True)


def _records(root: Path, paths: tuple[Path, ...]) -> list[ArtifactRecord]:
    return [
        ArtifactRecord(
            path=_relative_path(path, root),
            sha256=sha256_file(path),
            size_bytes=path.stat().st_size,
        )
        for path in paths
    ]


def _config_hash(result: EnsembleResult) -> str:
    return sha256_bytes(canonical_json_bytes(result.config.model_dump(mode="json")))


def write_ensemble_artifact(
    result: EnsembleResult, root: Path, output_dir: Path
) -> EnsembleArtifact:
    """Write replicate trajectories, quantile summaries and provenance."""

    root = root.resolve()
    output_dir = output_dir.resolve()
    artifact_id = f"jos-ensemble-m6-{result.config.ensemble_id}-{result.logical_content_hash[:12]}"
    artifact_directory = output_dir / artifact_id
    artifact_directory.mkdir(parents=True, exist_ok=True)
    manifest_path = artifact_directory / "manifest.json"
    if manifest_path.exists():
        existing = EnsembleArtifactManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        if existing.logical_content_hash != result.logical_content_hash:
            raise ValueError(
                "immutable M6 ensemble artifact ID already exists with different content"
            )
        return EnsembleArtifact(artifact_directory, existing)

    summary_path = artifact_directory / "ensemble_summary.parquet"
    trajectories_path = artifact_directory / "replicate_trajectories.parquet"
    grid_path = artifact_directory / "replicate_grid.parquet"
    records_path = artifact_directory / "replicate_records.json"
    config_path = artifact_directory / "ensemble_config.json"
    diagnostics_path = artifact_directory / "diagnostics.json"
    _write_table(
        summary_path,
        result.summary,
        pa.schema(
            [
                ("scope", pa.string()),
                ("key", pa.string()),
                ("metric", pa.string()),
                ("metric_semantic", pa.string()),
                ("date", pa.string()),
                ("cell_semantic", pa.string()),
                ("lower_quantile", pa.float64()),
                ("median", pa.float64()),
                ("upper_quantile", pa.float64()),
                ("lower_value", pa.float64()),
                ("upper_value", pa.float64()),
                ("replicate_count", pa.int64()),
                ("requested_replicates", pa.int64()),
                ("successful_replicates", pa.int64()),
                ("failed_replicates", pa.int64()),
                ("contributing_replicates", pa.int64()),
                ("observed_replicates", pa.int64()),
                ("structural_zero_replicates", pa.int64()),
                ("carried_forward_replicates", pa.int64()),
                ("outside_metric_horizon_replicates", pa.int64()),
                ("non_contributing_replicates", pa.int64()),
            ]
        ),
    )
    trajectory_rows = tuple(
        row
        for seed in sorted(result.replicate_trajectories)
        for row in result.replicate_trajectories[seed]
    )
    _write_table(
        trajectories_path,
        trajectory_rows,
        pa.schema(
            [
                ("seed", pa.int64()),
                ("scope", pa.string()),
                ("key", pa.string()),
                ("metric", pa.string()),
                ("date", pa.string()),
                ("value", pa.float64()),
            ]
        ),
    )
    _write_table(
        grid_path,
        result.replicate_grid,
        pa.schema(
            [
                ("seed", pa.int64()),
                ("scope", pa.string()),
                ("key", pa.string()),
                ("metric", pa.string()),
                ("metric_semantic", pa.string()),
                ("date", pa.string()),
                ("value", pa.float64()),
                ("cell_semantic", pa.string()),
                ("contributes", pa.bool_()),
            ]
        ),
    )
    records_path.write_text(
        json.dumps(
            [record.model_dump(mode="json") for record in result.replicate_records],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    config_path.write_text(
        json.dumps(result.config.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    diagnostics_path.write_text(
        json.dumps(result.diagnostics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    output_paths = (
        summary_path,
        trajectories_path,
        grid_path,
        records_path,
        config_path,
        diagnostics_path,
    )
    git_commit, dirty_worktree = _git_metadata(root)
    successful = [record for record in result.replicate_records if record.status == "passed"]
    m4_hashes = {
        str(record.seed): record.m4_logical_content_hash
        for record in successful
        if record.m4_logical_content_hash is not None
    }
    m5_hashes = {
        str(record.seed): record.latent_run_logical_content_hash
        for record in successful
        if record.latent_run_logical_content_hash is not None
    }
    intervention_hashes = {
        intervention_id: intervention_hash
        for record in successful
        for intervention_id, intervention_hash in record.intervention_config_hashes.items()
    }
    observation_hash = sha256_bytes(
        canonical_json_bytes(result.config.observation_config.model_dump(mode="json"))
    )
    manifest = EnsembleArtifactManifest(
        artifact_id=artifact_id,
        logical_content_hash=result.logical_content_hash,
        ensemble_id=result.config.ensemble_id,
        status=result.diagnostics["status"],
        diagnostics_status=("passed" if result.diagnostics["status"] == "passed" else "failed"),
        replicate_seeds=result.config.replicate_seeds,
        replicate_count=len(result.replicate_records),
        successful_replicates=len(successful),
        failed_replicates=len(result.replicate_records) - len(successful),
        requested_workers=result.diagnostics["requested_workers"],
        planned_workers=result.diagnostics["planned_workers"],
        actual_workers=result.diagnostics["actual_workers"],
        execution_mode=result.diagnostics["execution_mode"],
        fallback_reason=result.diagnostics["fallback_reason"],
        m2_logical_content_hash=result.m2_logical_content_hash,
        m3_logical_content_hash=result.m3_logical_content_hash,
        m4_logical_content_hashes=m4_hashes,
        m5_logical_content_hashes=m5_hashes,
        disease_parameter_hash=result.disease_parameter_hash,
        observation_parameter_hash=observation_hash,
        base_config_hash=_config_hash(result),
        scenario_hash=(result.scenario_hash if result.config.scenario is not None else None),
        intervention_config_hashes=intervention_hashes,
        quantile_configuration={
            "lower": result.config.lower_quantile,
            "median": 0.5,
            "upper": result.config.upper_quantile,
        },
        replicate_records=list(result.replicate_records),
        created_at=datetime.now(UTC).isoformat(),
        git_commit=git_commit,
        dirty_worktree_flag=dirty_worktree,
        runtime_seconds=result.runtime_seconds,
        peak_memory_bytes=result.peak_memory_bytes,
        output_artifacts=_records(root, output_paths),
    )
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return EnsembleArtifact(artifact_directory, manifest)


def write_comparison_artifact(
    result: ComparisonResult, root: Path, output_dir: Path
) -> ComparisonArtifact:
    """Write paired rows and configuration references for an A/B comparison."""

    root = root.resolve()
    output_dir = output_dir.resolve()
    artifact_id = f"jos-comparison-m6-{result.comparison_id}-{result.logical_content_hash[:12]}"
    artifact_directory = output_dir / artifact_id
    artifact_directory.mkdir(parents=True, exist_ok=True)
    manifest_path = artifact_directory / "manifest.json"
    if manifest_path.exists():
        existing = ComparisonArtifactManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        if existing.logical_content_hash != result.logical_content_hash:
            raise ValueError(
                "immutable M6 comparison artifact ID already exists with different content"
            )
        return ComparisonArtifact(artifact_directory, existing)

    paired_path = artifact_directory / "matched_seed_comparison.parquet"
    config_path = artifact_directory / "comparison_config.json"
    diagnostics_path = artifact_directory / "diagnostics.json"
    _write_table(
        paired_path,
        result.paired_rows,
        pa.schema(
            [
                ("seed", pa.int64()),
                ("scope", pa.string()),
                ("key", pa.string()),
                ("metric", pa.string()),
                ("date", pa.string()),
                ("status", pa.string()),
                ("value_a", pa.float64()),
                ("value_b", pa.float64()),
                ("difference", pa.float64()),
            ]
        ),
    )
    config_path.write_text(
        json.dumps(
            {
                "comparison_id": result.comparison_id,
                "ensemble_a_id": result.ensemble_a.config.ensemble_id,
                "ensemble_b_id": result.ensemble_b.config.ensemble_id,
                "config_a_hash": _config_hash(result.ensemble_a),
                "config_b_hash": _config_hash(result.ensemble_b),
                "matched_seed_list": sorted(
                    set(result.ensemble_a.config.replicate_seeds)
                    & set(result.ensemble_b.config.replicate_seeds)
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
    output_paths = (paired_path, config_path, diagnostics_path)
    git_commit, dirty_worktree = _git_metadata(root)
    manifest = ComparisonArtifactManifest(
        artifact_id=artifact_id,
        logical_content_hash=result.logical_content_hash,
        comparison_id=result.comparison_id,
        status=result.diagnostics["status"],
        config_a_hash=_config_hash(result.ensemble_a),
        config_b_hash=_config_hash(result.ensemble_b),
        matched_seed_list=tuple(
            sorted(
                set(result.ensemble_a.config.replicate_seeds)
                & set(result.ensemble_b.config.replicate_seeds)
            )
        ),
        paired_count=result.diagnostics["paired_seed_count"],
        missing_or_failed_pairs=result.diagnostics["missing_or_failed_pair_count"],
        created_at=datetime.now(UTC).isoformat(),
        git_commit=git_commit,
        dirty_worktree_flag=dirty_worktree,
        runtime_seconds=result.runtime_seconds,
        output_artifacts=_records(root, output_paths),
    )
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return ComparisonArtifact(artifact_directory, manifest)
