"""Parquet outputs and manifests for corrected C3 observation runs."""

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
from .observation import ObservationRunResult
from .observation_schemas import ObservationArtifactManifest
from .population_artifacts import portable_artifact_path, resolve_portable_artifact_path


@dataclass(frozen=True)
class ObservationArtifact:
    """Written observation artifact directory and validated manifest."""

    artifact_directory: Path
    manifest: ObservationArtifactManifest


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


def _write_table(path: Path, rows: list[dict[str, Any]], schema: pa.Schema) -> None:
    if rows:
        table = pa.Table.from_pylist(rows, schema=schema)
    else:
        table = pa.Table.from_arrays(
            [pa.array([], type=field.type) for field in schema], schema=schema
        )
    pq.write_table(table, path, compression="zstd", use_dictionary=True, write_statistics=True)


def _latent_artifact_id(result: ObservationRunResult) -> str:
    latent = result.latent_run
    return (
        f"jos-outbreak-m5-{latent.config.mode}-seed-{latent.config.seed}-"
        f"{latent.logical_content_hash[:12]}"
    )


def write_observation_artifact(
    result: ObservationRunResult, root: Path, output_dir: Path
) -> ObservationArtifact:
    """Write observation tables and a content-addressed provenance manifest."""

    root = root.resolve()
    output_dir = output_dir.resolve()
    config_hash = sha256_bytes(canonical_json_bytes(result.config.model_dump(mode="json")))
    artifact_id = (
        f"jos-observation-m6-{result.latent_run.config.mode}-seed-"
        f"{result.config.observation_seed}-{result.logical_content_hash[:12]}"
    )
    artifact_directory = output_dir / artifact_id
    artifact_directory.mkdir(parents=True, exist_ok=True)
    manifest_path = artifact_directory / "manifest.json"
    if manifest_path.exists():
        existing = ObservationArtifactManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        if existing.logical_content_hash != result.logical_content_hash:
            raise ValueError(
                "immutable M6 observation artifact ID already exists with different content"
            )
        return ObservationArtifact(artifact_directory, existing)

    cases_path = artifact_directory / "daily_observed_cases.parquet"
    parish_path = artifact_directory / "daily_observed_parish.parquet"
    age_path = artifact_directory / "daily_observed_age.parquet"
    events_path = artifact_directory / "observation_events.parquet"
    detections_path = artifact_directory / "detection_events.parquet"
    config_path = artifact_directory / "observation_config.json"
    diagnostics_path = artifact_directory / "diagnostics.json"

    _write_table(
        cases_path,
        result.daily_observed_cases,
        pa.schema(
            [
                ("date", pa.string()),
                ("latent_infections", pa.int64()),
                ("detected_infections", pa.int64()),
                ("reported_cases", pa.int64()),
                ("ascertainment_fraction", pa.float64()),
                ("mean_reporting_delay_days", pa.float64()),
            ]
        ),
    )
    _write_table(
        parish_path,
        result.daily_observed_parish,
        pa.schema(
            [
                ("date", pa.string()),
                ("parish", pa.string()),
                ("new_latent_infections", pa.int64()),
                ("new_detected_infections", pa.int64()),
                ("new_reported_cases", pa.int64()),
            ]
        ),
    )
    _write_table(
        age_path,
        result.daily_observed_age,
        pa.schema(
            [
                ("date", pa.string()),
                ("age_band", pa.string()),
                ("new_latent_infections", pa.int64()),
                ("new_detected_infections", pa.int64()),
                ("new_reported_cases", pa.int64()),
            ]
        ),
    )
    _write_table(
        events_path,
        result.observation_events,
        pa.schema(
            [
                ("infected_agent_id", pa.string()),
                ("infected_uid", pa.int64()),
                ("infected_actor_type", pa.string()),
                ("infected_runtime_uid", pa.int64()),
                ("infected_trip_id", pa.string()),
                ("infected_travel_party_id", pa.string()),
                ("infected_episode_identity_hash", pa.string()),
                ("infector_agent_id", pa.string()),
                ("infector_actor_type", pa.string()),
                ("infector_runtime_uid", pa.int64()),
                ("infector_trip_id", pa.string()),
                ("infector_travel_party_id", pa.string()),
                ("infector_episode_identity_hash", pa.string()),
                ("infection_date", pa.string()),
                ("infectious_start_date", pa.string()),
                ("symptom_onset_date", pa.string()),
                ("recovery_date", pa.string()),
                ("detection_date", pa.string()),
                ("report_date", pa.string()),
                ("symptom_onset_delay_days", pa.int64()),
                ("detection_delay_days", pa.int64()),
                ("reporting_delay_days", pa.int64()),
                ("symptomatic", pa.bool_()),
                ("tested", pa.bool_()),
                ("detected", pa.bool_()),
                ("detection_reason", pa.string()),
                ("source_kind", pa.string()),
                ("route_id", pa.string()),
                ("home_parish", pa.string()),
                ("age_band", pa.string()),
            ]
        ),
    )
    # Keep the event-interface provenance JSON-friendly in the persisted table.
    detection_table = pa.Table.from_pylist(
        [
            {**event.__dict__, "provenance": json.dumps(dict(event.provenance), sort_keys=True)}
            for event in result.detection_events
        ],
        schema=pa.schema(
            [
                ("agent_uid", pa.int64()),
                ("agent_id", pa.string()),
                ("detection_date", pa.string()),
                ("detection_time_index", pa.int64()),
                ("detection_reason", pa.string()),
                ("symptomatic", pa.bool_()),
                ("observation_config_id", pa.string()),
                ("provenance", pa.string()),
                ("infected_agent_id", pa.string()),
                ("infected_actor_type", pa.string()),
                ("infected_runtime_uid", pa.int64()),
                ("infected_trip_id", pa.string()),
                ("infected_travel_party_id", pa.string()),
                ("infected_episode_identity_hash", pa.string()),
                ("infector_agent_id", pa.string()),
                ("infector_actor_type", pa.string()),
                ("infector_runtime_uid", pa.int64()),
                ("infector_trip_id", pa.string()),
                ("infector_travel_party_id", pa.string()),
                ("infector_episode_identity_hash", pa.string()),
            ]
        ),
    )
    pq.write_table(
        detection_table,
        detections_path,
        compression="zstd",
        use_dictionary=True,
        write_statistics=True,
    )
    config_path.write_text(
        json.dumps(result.config.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    diagnostics_path.write_text(
        json.dumps(result.diagnostics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    output_paths = (
        cases_path,
        parish_path,
        age_path,
        events_path,
        detections_path,
        config_path,
        diagnostics_path,
    )
    git_commit, dirty_worktree = _git_metadata(root)
    output_artifacts = [
        ArtifactRecord(
            path=portable_artifact_path(path, artifact_directory),
            sha256=sha256_file(path),
            size_bytes=path.stat().st_size,
        )
        for path in output_paths
    ]
    manifest = ObservationArtifactManifest(
        artifact_id=artifact_id,
        latent_run_logical_content_hash=result.latent_run.logical_content_hash,
        latent_m5_artifact_id=_latent_artifact_id(result),
        observation_config_id=result.config.observation_config_id,
        observation_config_hash=config_hash,
        observation_seed=result.config.observation_seed,
        logical_content_hash=result.logical_content_hash,
        status=result.diagnostics["status"],
        diagnostics_status=result.diagnostics["status"],
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
    return ObservationArtifact(artifact_directory, manifest)


def verify_observation_artifact(artifact_directory: Path) -> ObservationArtifactManifest:
    """Verify the portable output records of one standalone M6 observation artifact."""

    artifact_directory = artifact_directory.resolve()
    manifest_path = artifact_directory / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("M6 observation artifact is missing manifest.json")
    manifest = ObservationArtifactManifest.model_validate_json(manifest_path.read_bytes())
    required = {
        "daily_observed_cases.parquet",
        "daily_observed_parish.parquet",
        "daily_observed_age.parquet",
        "observation_events.parquet",
        "detection_events.parquet",
        "observation_config.json",
        "diagnostics.json",
    }
    seen: set[Path] = set()
    files: set[str] = set()
    for record in manifest.output_artifacts:
        try:
            path = resolve_portable_artifact_path(record.path, artifact_directory)
        except ValueError as exc:
            raise ValueError(f"invalid M6 observation output path {record.path}: {exc}") from exc
        if path in seen:
            raise ValueError(f"M6 observation manifest contains duplicate output: {record.path}")
        seen.add(path)
        if not path.is_file():
            raise ValueError(f"M6 observation output is missing: {record.path}")
        if path.stat().st_size != record.size_bytes:
            raise ValueError(f"M6 observation output size mismatch: {record.path}")
        if sha256_file(path) != record.sha256:
            raise ValueError(f"M6 observation output hash mismatch: {record.path}")
        files.add(path.name)
    missing = sorted(required - files)
    if missing:
        raise ValueError(f"M6 observation artifact is incomplete: {missing}")
    return manifest
