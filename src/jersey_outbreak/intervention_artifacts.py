"""Visualization-ready M7 intervention artifacts and provenance manifests."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from .contracts import ArtifactRecord, StrictModel
from .hashing import canonical_json_bytes, sha256_bytes, sha256_file
from .intervention_analysis import InterventionComparison
from .outbreak_artifacts import write_outbreak_artifact
from .outbreak_runner import OutbreakRunResult, network_artifact_id
from .population_artifacts import portable_artifact_path, resolve_portable_artifact_path


class InterventionArtifactManifest(StrictModel):
    """Parent-linked manifest for one M7 scenario run."""

    manifest_schema_version: str = "2.1"
    artifact_id: str
    framework_version: str
    scenario_id: str
    scenario_hash: str
    scenario_config_hash: str
    run_config_hash: str
    latent_outcome_hash: str
    latent_logical_content_hash: str
    artifact_bundle_hash: str
    mode: str
    seed: int
    start_date: str
    duration_days: int
    starsim_version: str = "3.5.2"
    m2_logical_content_hash: str
    m2_artifact_id: str
    m3_logical_content_hash: str
    m3_artifact_id: str
    m4_logical_content_hash: str
    m4_artifact_id: str
    m5_disease_config_hash: str
    c4_observation_scheduler_version: str | None
    c4_observation_config_hash: str | None
    intervention_framework_version: str
    intervention_config_hashes: dict[str, str]
    sensitivity_config_ids: tuple[str, ...]
    route_weight_semantics: str
    matched_seed_coupling_diagnostics: dict[str, Any]
    logical_content_hash: str
    latent_bundle_artifact_id: str
    latent_bundle_manifest_sha256: str
    diagnostics_status: str
    created_at: str
    git_commit: str | None
    dirty_worktree_flag: bool
    runtime_seconds: float
    peak_memory_bytes: int | None
    output_artifacts: list[ArtifactRecord]


@dataclass(frozen=True)
class InterventionArtifact:
    """Written M7 artifact directory and validated manifest."""

    artifact_directory: Path
    manifest: InterventionArtifactManifest


def _git_metadata(root: Path) -> tuple[str | None, bool]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=False, capture_output=True, text=True
        )
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=root, check=False, capture_output=True, text=True
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


def _event_rows(result: OutbreakRunResult) -> list[dict[str, Any]]:
    rows = []
    for event in result.intervention_events:
        rows.append(
            {
                **event,
                "previous_state": json.dumps(event.get("previous_state"), sort_keys=True),
                "new_state": json.dumps(event.get("new_state"), sort_keys=True),
            }
        )
    return rows


def write_intervention_artifact(
    result: OutbreakRunResult, root: Path, output_dir: Path
) -> InterventionArtifact:
    """Write M7 state/events/effective-route tables without touching M5 artifacts."""

    if result.scenario_config is None or not result.scenario_hash:
        raise ValueError("an intervention artifact requires a scenario-backed run")
    root = root.resolve()
    output_dir = output_dir.resolve()
    scenario = result.scenario_config
    artifact_id = (
        f"jos-intervention-m7-{result.config.mode}-seed-{result.config.seed}-"
        f"{result.artifact_bundle_hash[:12]}"
    )
    artifact_directory = output_dir / artifact_id
    artifact_directory.mkdir(parents=True, exist_ok=True)
    manifest_path = artifact_directory / "manifest.json"
    if manifest_path.exists():
        manifest = InterventionArtifactManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        if manifest.artifact_bundle_hash != result.artifact_bundle_hash:
            raise ValueError("immutable M7 artifact ID already exists with different content")
        return InterventionArtifact(artifact_directory, manifest)

    state_path = artifact_directory / "daily_intervention_state.parquet"
    events_path = artifact_directory / "intervention_events.parquet"
    route_path = artifact_directory / "route_effects.parquet"
    scenario_path = artifact_directory / "scenario_config.json"
    diagnostics_path = artifact_directory / "diagnostics.json"
    _write_table(
        state_path,
        result.intervention_state,
        pa.schema(
            [
                ("date", pa.string()),
                ("time_index", pa.int64()),
                ("intervention_id", pa.string()),
                ("intervention_type", pa.string()),
                ("active_agents", pa.int64()),
                ("active_households", pa.int64()),
                ("active_settings", pa.int64()),
                ("route_intervention_active", pa.bool_()),
                ("affected_routes", pa.int64()),
                ("affected_residents", pa.int64()),
                ("affected_staff", pa.int64()),
                ("new_activations", pa.int64()),
                ("new_releases", pa.int64()),
                ("new_wfh_entries", pa.int64()),
                ("wfh_exits", pa.int64()),
                ("doses_administered", pa.int64()),
                ("newly_vaccinated", pa.int64()),
                ("protection_became_effective", pa.int64()),
                ("currently_protected", pa.int64()),
                ("protection_waned", pa.int64()),
                ("config_hash", pa.string()),
            ]
        ),
    )
    _write_table(
        events_path,
        _event_rows(result),
        pa.schema(
            [
                ("date", pa.string()),
                ("time_index", pa.int64()),
                ("intervention_id", pa.string()),
                ("intervention_type", pa.string()),
                ("action", pa.string()),
                ("cause", pa.string()),
                ("detection_event_reference", pa.string()),
                ("agent_uid", pa.int64()),
                ("agent_id", pa.string()),
                ("household_id", pa.string()),
                ("setting_id", pa.string()),
                ("previous_state", pa.string()),
                ("new_state", pa.string()),
                ("config_hash", pa.string()),
                ("provenance_hash", pa.string()),
            ]
        ),
    )
    _write_table(
        route_path,
        result.intervention_route_effects,
        pa.schema(
            [
                ("date", pa.string()),
                ("time_index", pa.int64()),
                ("route_id", pa.string()),
                ("base_edge_count", pa.int64()),
                ("effective_edge_count", pa.int64()),
                ("suppressed_edge_count", pa.int64()),
                ("mean_multiplier", pa.float64()),
                ("minimum_multiplier", pa.float64()),
                ("maximum_multiplier", pa.float64()),
                ("representation", pa.string()),
            ]
        ),
    )
    scenario_path.write_text(
        json.dumps(scenario.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    diagnostics_path.write_text(
        json.dumps(result.intervention_diagnostics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    # The complete M5 latent bundle is persisted inside the M7 directory.  It
    # is not an optional external pointer: removing or changing any latent
    # table makes M7 verification fail.
    latent_artifact = write_outbreak_artifact(result, root, artifact_directory / "latent_outputs")
    latent_manifest_path = latent_artifact.artifact_directory / "manifest.json"
    output_paths = (
        state_path,
        events_path,
        route_path,
        scenario_path,
        diagnostics_path,
        *sorted(path for path in latent_artifact.artifact_directory.iterdir() if path.is_file()),
    )
    git_commit, dirty = _git_metadata(root)
    parameter_hash = sha256_bytes(canonical_json_bytes(result.parameters.model_dump(mode="json")))
    observation_hash = (
        sha256_bytes(canonical_json_bytes(result.observation_config.model_dump(mode="json")))
        if result.observation_config is not None
        else None
    )
    config_hashes = result.intervention_diagnostics.get("intervention_config_hashes", {})
    manifest = InterventionArtifactManifest(
        artifact_id=artifact_id,
        framework_version=result.intervention_diagnostics.get("framework_version", "7.1.0"),
        scenario_id=scenario.scenario_id,
        scenario_hash=result.scenario_hash,
        scenario_config_hash=scenario.config_hash,
        run_config_hash=result.run_config_hash,
        latent_outcome_hash=result.latent_outcome_hash,
        latent_logical_content_hash=result.logical_content_hash,
        artifact_bundle_hash=result.artifact_bundle_hash,
        mode=result.config.mode,
        seed=result.config.seed,
        start_date=result.config.start_date.isoformat(),
        duration_days=result.config.duration_days,
        m2_logical_content_hash=result.generated.m2_input.manifest.logical_content_hash,
        m2_artifact_id=result.generated.m2_input.manifest.artifact_id,
        m3_logical_content_hash=result.generated.m3_input.manifest.logical_content_hash,
        m3_artifact_id=result.generated.m3_input.manifest.artifact_id,
        m4_logical_content_hash=result.generated.logical_content_hash,
        m4_artifact_id=network_artifact_id(result.generated),
        m5_disease_config_hash=parameter_hash,
        c4_observation_scheduler_version=("6.0.0" if result.observation_schedule else None),
        c4_observation_config_hash=observation_hash,
        intervention_framework_version=result.intervention_diagnostics.get(
            "framework_version", "7.1.0"
        ),
        intervention_config_hashes=config_hashes,
        sensitivity_config_ids=scenario.sensitivity_config_ids,
        route_weight_semantics=(
            "M4 edge weight is relative daily exposure opportunity; intervention multipliers "
            "are scenario assumptions and are composed multiplicatively."
        ),
        matched_seed_coupling_diagnostics={
            "matched_seed": "same declared seed gives matched starts",
            "true_common_random_numbers": "not guaranteed after event-path divergence",
        },
        logical_content_hash=result.artifact_bundle_hash,
        latent_bundle_artifact_id=latent_artifact.manifest.artifact_id,
        latent_bundle_manifest_sha256=sha256_file(latent_manifest_path),
        diagnostics_status="passed",
        created_at=datetime.now(UTC).isoformat(),
        git_commit=git_commit,
        dirty_worktree_flag=dirty,
        runtime_seconds=result.runtime_seconds,
        peak_memory_bytes=result.peak_memory_bytes,
        output_artifacts=[
            ArtifactRecord(
                path=portable_artifact_path(path, artifact_directory),
                sha256=sha256_file(path),
                size_bytes=path.stat().st_size,
            )
            for path in output_paths
        ],
    )
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return InterventionArtifact(artifact_directory, manifest)


def verify_intervention_artifact(artifact_directory: Path) -> InterventionArtifactManifest:
    """Verify that an M7 artifact and its directly included latent bundle resolve."""

    artifact_directory = artifact_directory.resolve()
    manifest_path = artifact_directory / "manifest.json"
    manifest = InterventionArtifactManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )
    required_latent = {
        "daily_epidemic.parquet",
        "daily_parish.parquet",
        "daily_route.parquet",
        "daily_age.parquet",
        "transmission_events.parquet",
        "manifest.json",
    }
    latent_candidates = list((artifact_directory / "latent_outputs").glob("jos-outbreak-m5-*"))
    if len(latent_candidates) != 1:
        raise ValueError("M7 artifact must contain exactly one resolvable latent bundle")
    latent_directory = latent_candidates[0]
    missing = sorted(name for name in required_latent if not (latent_directory / name).is_file())
    if missing:
        raise ValueError(f"M7 latent bundle is incomplete: {missing}")
    latent_manifest = latent_directory / "manifest.json"
    if sha256_file(latent_manifest) != manifest.latent_bundle_manifest_sha256:
        raise ValueError("M7 latent bundle manifest hash mismatch")
    seen: set[Path] = set()
    for record in manifest.output_artifacts:
        try:
            path = resolve_portable_artifact_path(record.path, artifact_directory)
        except ValueError as exc:
            raise ValueError(f"invalid M7 output path {record.path}: {exc}") from exc
        if path in seen:
            raise ValueError(f"M7 manifest contains duplicate output: {record.path}")
        seen.add(path)
        if not path.is_file():
            raise ValueError(f"M7 output is missing: {record.path}")
        if path.stat().st_size != record.size_bytes or sha256_file(path) != record.sha256:
            raise ValueError(f"M7 output hash mismatch or missing file: {record.path}")
    return manifest


def write_intervention_comparison_artifact(
    comparison: InterventionComparison, root: Path, output_dir: Path
) -> Path:
    """Write explicit health, paired-timeline and route-share comparison tables."""

    root = root.resolve()
    output_dir = output_dir.resolve()
    payload = {
        "comparison_id": comparison.comparison_id,
        "scenario_comparison": comparison.scenario_comparison,
        "route_shift": comparison.route_shift,
        "paired_seed_comparison": comparison.paired_seed_comparison,
    }
    logical_hash = sha256_bytes(canonical_json_bytes(payload))
    artifact_directory = output_dir / f"jos-intervention-comparison-m7-{logical_hash[:12]}"
    artifact_directory.mkdir(parents=True, exist_ok=True)
    manifest_path = artifact_directory / "manifest.json"
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing.get("logical_content_hash") != logical_hash:
            raise ValueError("immutable M7 comparison ID already exists with different content")
        return artifact_directory
    _write_table(
        artifact_directory / "scenario_comparison.parquet",
        list(comparison.scenario_comparison),
        pa.schema(
            [
                ("comparison_id", pa.string()),
                ("seed", pa.int64()),
                ("metric", pa.string()),
                ("baseline_value", pa.float64()),
                ("intervention_value", pa.float64()),
                ("absolute_difference", pa.float64()),
                ("relative_difference", pa.float64()),
            ]
        ),
    )
    _write_table(
        artifact_directory / "paired_seed_comparison.parquet",
        list(comparison.paired_seed_comparison),
        pa.schema(
            [
                ("comparison_id", pa.string()),
                ("seed", pa.int64()),
                ("scope", pa.string()),
                ("key", pa.string()),
                ("metric", pa.string()),
                ("date", pa.string()),
                ("baseline_value", pa.float64()),
                ("intervention_value", pa.float64()),
                ("difference", pa.float64()),
            ]
        ),
    )
    _write_table(
        artifact_directory / "route_effects.parquet",
        list(comparison.route_shift),
        pa.schema(
            [
                ("route_id", pa.string()),
                ("baseline_absolute_infections", pa.int64()),
                ("intervention_absolute_infections", pa.int64()),
                ("absolute_difference", pa.int64()),
                ("baseline_share", pa.float64()),
                ("intervention_share", pa.float64()),
                ("share_difference", pa.float64()),
                ("interpretation", pa.string()),
            ]
        ),
    )
    manifest = {
        "artifact_id": artifact_directory.name,
        "framework_version": "7.1.0",
        "comparison_id": comparison.comparison_id,
        "logical_content_hash": logical_hash,
        "created_at": datetime.now(UTC).isoformat(),
        "files": {
            name: {
                "sha256": sha256_file(artifact_directory / name),
                "size_bytes": (artifact_directory / name).stat().st_size,
            }
            for name in (
                "scenario_comparison.parquet",
                "paired_seed_comparison.parquet",
                "route_effects.parquet",
            )
        },
        "claim_boundary": "synthetic scenario comparison under declared model assumptions",
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return artifact_directory
