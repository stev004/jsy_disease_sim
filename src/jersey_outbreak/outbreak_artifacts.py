"""Parquet outputs and provenance manifest for Milestone 5 runs."""

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
from .hashing import canonical_json_bytes, sha256_bytes, sha256_file
from .outbreak_runner import OutbreakRunResult, network_artifact_id
from .outbreak_schemas import OutbreakArtifactManifest


@dataclass(frozen=True)
class OutbreakArtifact:
    """Written M5 artifact directory and validated manifest."""

    artifact_directory: Path
    manifest: OutbreakArtifactManifest


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


def _write_table(path: Path, rows: list[dict[str, Any]], schema: pa.Schema) -> None:
    if rows:
        table = pa.Table.from_pylist(rows, schema=schema)
    else:
        table = pa.Table.from_arrays(
            [pa.array([], type=field.type) for field in schema], schema=schema
        )
    pq.write_table(table, path, compression="zstd", use_dictionary=True, write_statistics=True)


def write_outbreak_artifact(
    result: OutbreakRunResult, root: Path, output_dir: Path
) -> OutbreakArtifact:
    """Write stable tidy tables, event attribution and a versioned run manifest."""

    root = root.resolve()
    output_dir = output_dir.resolve()
    config_hash = sha256_bytes(canonical_json_bytes(result.config.model_dump(mode="json")))
    artifact_id = (
        f"jos-outbreak-m5-{result.config.mode}-seed-{result.config.seed}-"
        f"{result.logical_content_hash[:12]}"
    )
    artifact_directory = output_dir / artifact_id
    artifact_directory.mkdir(parents=True, exist_ok=True)
    manifest_path = artifact_directory / "manifest.json"
    if manifest_path.exists():
        existing = OutbreakArtifactManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        if existing.logical_content_hash != result.logical_content_hash:
            raise ValueError("immutable M5 artifact ID already exists with different content")
        return OutbreakArtifact(artifact_directory, existing)

    epidemic_path = artifact_directory / "daily_epidemic.parquet"
    parish_path = artifact_directory / "daily_parish.parquet"
    route_path = artifact_directory / "daily_route.parquet"
    age_path = artifact_directory / "daily_age.parquet"
    events_path = artifact_directory / "transmission_events.parquet"
    parameters_path = artifact_directory / "parameters.json"
    diagnostics_path = artifact_directory / "diagnostics.json"
    network_reference_path = artifact_directory / "network_reference.json"

    _write_table(
        epidemic_path,
        result.daily_epidemic,
        pa.schema(
            [
                ("date", pa.string()),
                ("time_index", pa.int64()),
                ("susceptible", pa.int64()),
                ("exposed", pa.int64()),
                ("infectious", pa.int64()),
                ("recovered", pa.int64()),
                ("severe", pa.int64()),
                ("dead", pa.int64()),
                ("new_infections", pa.int64()),
                ("new_local_infections", pa.int64()),
                ("new_imported_infections", pa.int64()),
                ("new_seeded_infections", pa.int64()),
                ("cumulative_infections", pa.int64()),
                ("cumulative_total_infections", pa.int64()),
                ("prevalence", pa.float64()),
                ("attack_rate", pa.float64()),
            ]
        ),
    )
    _write_table(
        parish_path,
        result.daily_parish,
        pa.schema(
            [
                ("date", pa.string()),
                ("time_index", pa.int64()),
                ("parish", pa.string()),
                ("new_seeded_infections", pa.int64()),
                ("new_imported_infections", pa.int64()),
                ("new_local_infections", pa.int64()),
                ("new_infections", pa.int64()),
            ]
        ),
    )
    _write_table(
        route_path,
        result.daily_route,
        pa.schema(
            [
                ("date", pa.string()),
                ("time_index", pa.int64()),
                ("route_id", pa.string()),
                ("new_events", pa.int64()),
                ("new_local_infections", pa.int64()),
                ("new_imported_infections", pa.int64()),
                ("new_seeded_infections", pa.int64()),
                ("cumulative_infections", pa.int64()),
            ]
        ),
    )
    _write_table(
        age_path,
        result.daily_age,
        pa.schema(
            [
                ("date", pa.string()),
                ("time_index", pa.int64()),
                ("age_band", pa.string()),
                ("new_seeded_infections", pa.int64()),
                ("new_imported_infections", pa.int64()),
                ("new_local_infections", pa.int64()),
                ("new_infections", pa.int64()),
            ]
        ),
    )
    _write_table(
        events_path,
        result.transmission_events,
        pa.schema(
            [
                ("time_index", pa.int64()),
                ("date", pa.string()),
                ("infected_uid", pa.int64()),
                ("infected_agent_id", pa.string()),
                ("infector_uid", pa.int64()),
                ("infector_agent_id", pa.string()),
                ("route_id", pa.string()),
                ("source_kind", pa.string()),
                ("imported", pa.bool_()),
                ("seeded", pa.bool_()),
                ("state", pa.string()),
            ]
        ),
    )
    parameters_path.write_text(
        json.dumps(result.parameters.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    diagnostics_path.write_text(
        json.dumps(result.diagnostics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    network_reference_path.write_text(
        json.dumps(
            {
                "m4_artifact_id": network_artifact_id(result.generated),
                "m4_logical_content_hash": result.generated.logical_content_hash,
                "route_ids": sorted(result.generated.route_specs),
                "network_is_immutable_input": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    output_paths = (
        epidemic_path,
        parish_path,
        route_path,
        age_path,
        events_path,
        parameters_path,
        diagnostics_path,
        network_reference_path,
    )
    git_commit, dirty_worktree = _git_metadata(root)
    output_artifacts = [
        ArtifactRecord(
            path=_relative_path(path, root),
            sha256=sha256_file(path),
            size_bytes=path.stat().st_size,
        )
        for path in output_paths
    ]
    parameter_set_hash = sha256_bytes(
        canonical_json_bytes(result.parameters.model_dump(mode="json"))
    )
    manifest = OutbreakArtifactManifest(
        artifact_id=artifact_id,
        generator_version=result.config.generator_version,
        mode=result.config.mode,
        seed=result.config.seed,
        start_date=result.config.start_date,
        duration_days=result.config.duration_days,
        dt_days=result.config.dt_days,
        m2_artifact_id=result.generated.m2_input.manifest.artifact_id,
        m2_logical_content_hash=result.generated.m2_input.manifest.logical_content_hash,
        m3_artifact_id=result.generated.m3_input.manifest.artifact_id,
        m3_logical_content_hash=result.generated.m3_input.manifest.logical_content_hash,
        m4_artifact_id=network_artifact_id(result.generated),
        m4_logical_content_hash=result.generated.logical_content_hash,
        parameter_set_id=result.parameters.parameter_set_id,
        parameter_set_hash=parameter_set_hash,
        config_hash=config_hash,
        logical_content_hash=result.logical_content_hash,
        diagnostics_status=result.diagnostics["status"],
        seed_specification=result.diagnostics["seeding"],
        import_specification=result.diagnostics["imports"],
        attribution_totals=result.diagnostics["attribution"]["totals"],
        created_at=datetime.now(UTC).isoformat(),
        git_commit=git_commit,
        dirty_worktree_flag=dirty_worktree,
        runtime_seconds=result.runtime_seconds,
        peak_memory_bytes=result.peak_memory_bytes,
        output_artifacts=output_artifacts,
    )
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return OutbreakArtifact(artifact_directory, manifest)
