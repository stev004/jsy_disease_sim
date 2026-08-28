"""Reconstructible Parquet artifacts for Milestone 8 travel runs."""

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
from .travel import TravelRunResult
from .travel_schemas import TravelConfig

M8_ARTIFACT_SCHEMA_VERSION = "2.0"


class TravelArtifactManifest(StrictModel):
    """Parent-linked manifest for one completed M8 experiment."""

    manifest_schema_version: str = M8_ARTIFACT_SCHEMA_VERSION
    artifact_id: str
    framework_version: str
    module: str = "explicit_travel_visitor_layer"
    mode: str
    seed: int
    start_date: str
    duration_days: int
    starsim_version: str = "3.5.2"
    m2_artifact_id: str
    m2_logical_content_hash: str
    m3_artifact_id: str
    m3_logical_content_hash: str
    m4_logical_content_hash: str
    m5_run_config_hash: str
    m5_disease_config_hash: str
    observation_config_hash: str | None = None
    m7_scenario_hash: str | None = None
    travel_config_hash: str
    visitor_episode_hash: str
    visitor_population_hash: str
    temporary_network_hash: str
    seasonality_hash: str
    latent_outcome_hash: str
    artifact_bundle_hash: str
    scenario_hash: str
    counts: dict[str, int]
    diagnostics_status: str
    created_at: str
    git_commit: str | None = None
    dirty_worktree_flag: bool
    runtime_seconds: float
    peak_memory_bytes: int | None = None
    output_artifacts: list[ArtifactRecord]


@dataclass(frozen=True)
class TravelArtifact:
    """Written M8 artifact directory and validated manifest."""

    artifact_directory: Path
    manifest: TravelArtifactManifest


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


def _write_rows(path: Path, rows: list[dict[str, Any]], schema: pa.Schema | None = None) -> None:
    if rows:
        # Arrow infers a struct from the first row and otherwise drops keys
        # introduced only by later heterogeneous events. Normalize the union
        # explicitly so infector/candidate/episode identity is never lost.
        columns = sorted({key for row in rows for key in row})
        normalized = [{key: row.get(key) for key in columns} for row in rows]
        table = pa.Table.from_pylist(normalized, schema=schema)
    elif schema is not None:
        table = pa.Table.from_arrays(
            [pa.array([], type=field.type) for field in schema], schema=schema
        )
    else:
        table = pa.Table.from_pylist([{}]).slice(0, 0)
    pq.write_table(table, path, compression="zstd", use_dictionary=True, write_statistics=True)


TRAVEL_INTERVENTION_EVENT_SCHEMA = pa.schema(
    [
        ("date", pa.string()),
        ("time_index", pa.int64()),
        ("action", pa.string()),
        ("trip_id", pa.string()),
        ("person_id", pa.string()),
        ("visitor_uid", pa.string()),
        ("resident_agent_id", pa.string()),
        ("traveller_type", pa.string()),
        ("travel_party_id", pa.string()),
        ("runtime_slot_uid", pa.int64()),
        ("arrival_date", pa.string()),
        ("arrival_time_index", pa.int64()),
        ("departure_date", pa.string()),
        ("departure_time_index", pa.int64()),
        ("resident_or_visitor_status", pa.string()),
        ("episode_identity_hash", pa.string()),
        ("tested", pa.bool_()),
        ("sensitivity", pa.float64()),
        ("specificity", pa.float64()),
        ("administration_time_index", pa.int64()),
        ("result_time_index", pa.int64()),
        ("result_runtime_slot_uid", pa.int64()),
        ("result_episode_identity_hash", pa.string()),
        ("episode_active", pa.bool_()),
        ("actionable", pa.bool_()),
        ("detected", pa.bool_()),
        ("cause", pa.string()),
        ("activation_time_index", pa.int64()),
        ("release_time_index", pa.int64()),
        ("effective_time_index", pa.int64()),
        ("slot_uid", pa.int64()),
        ("active_age", pa.float64()),
        ("active_sex", pa.string()),
        ("arrival_disease_state", pa.string()),
        ("alive", pa.bool_()),
        ("susceptible", pa.bool_()),
        ("exposed", pa.bool_()),
        ("infectious", pa.bool_()),
        ("recovered", pa.bool_()),
        ("age", pa.float64()),
        ("rel_sus", pa.float64()),
        ("rel_trans", pa.float64()),
        ("route_id", pa.string()),
        ("intervention_id", pa.string()),
        ("intervention_type", pa.string()),
        ("detection_event_reference", pa.string()),
        ("agent_uid", pa.int64()),
        ("agent_id", pa.string()),
        ("household_id", pa.string()),
        ("setting_id", pa.string()),
        ("previous_state_json", pa.string()),
        ("new_state_json", pa.string()),
        ("config_hash", pa.string()),
        ("provenance_hash", pa.string()),
    ]
)


OBSERVATION_EVENT_SCHEMA = pa.schema(
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
        ("symptom_onset_date", pa.string()),
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
)


DETECTION_EVENT_SCHEMA = pa.schema(
    [
        ("agent_uid", pa.int64()),
        ("agent_id", pa.string()),
        ("detection_date", pa.string()),
        ("detection_time_index", pa.int64()),
        ("detection_reason", pa.string()),
        ("symptomatic", pa.bool_()),
        ("observation_config_id", pa.string()),
        ("provenance_json", pa.string()),
        ("delivered", pa.bool_()),
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
)


def _canonical_json_text(value: Any) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def _serialize_intervention_event_rows(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Serialize heterogeneous M7 state values without Arrow inference."""

    allowed = set(TRAVEL_INTERVENTION_EVENT_SCHEMA.names) | {"previous_state", "new_state"}
    unknown = sorted({key for row in rows for key in row} - allowed)
    if unknown:
        raise ValueError(f"travel intervention event schema is missing fields: {unknown}")
    serialized: list[dict[str, Any]] = []
    for event in rows:
        row = {
            key: value for key, value in event.items() if key not in {"previous_state", "new_state"}
        }
        row["previous_state_json"] = (
            _canonical_json_text(event["previous_state"]) if "previous_state" in event else None
        )
        row["new_state_json"] = (
            _canonical_json_text(event["new_state"]) if "new_state" in event else None
        )
        serialized.append(row)
    return serialized


def _deserialize_intervention_event_rows(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Reconstruct exact Python JSON types from the typed event table."""

    reconstructed: list[dict[str, Any]] = []
    for event in rows:
        row = dict(event)
        previous_json = row.pop("previous_state_json", None)
        new_json = row.pop("new_state_json", None)
        if previous_json is not None:
            row["previous_state"] = json.loads(previous_json)
        if new_json is not None:
            row["new_state"] = json.loads(new_json)
        reconstructed.append(row)
    return reconstructed


def _detection_rows(result: TravelRunResult) -> list[dict[str, Any]]:
    delivered = {id(event) for event in result.delivered_detection_events}
    return [
        {
            **{key: value for key, value in event.__dict__.items() if key != "provenance"},
            "provenance_json": _canonical_json_text(dict(event.provenance)),
            "delivered": id(event) in delivered,
        }
        for event in result.detection_events
    ]


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _without_null_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _without_null_fields(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [_without_null_fields(item) for item in value]
    return value


def _canonical_c5_events(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Undo Arrow union-schema null padding while retaining C5 nullable fields."""

    base_fields = {
        "time_index",
        "date",
        "infected_uid",
        "infector_uid",
        "route_id",
        "source_kind",
        "imported",
        "seeded",
        "state",
        "infected_agent_id",
        "infector_agent_id",
    }
    return [
        {key: value for key, value in row.items() if key in base_fields or value is not None}
        for row in rows
    ]


def _rows_for_result(result: TravelRunResult) -> dict[str, list[dict[str, Any]]]:
    return {
        "daily_travel_population.parquet": result.daily_travel_population,
        "travel_episodes.parquet": result.travel_episodes,
        "visitor_population.parquet": list(result.travel_plan.visitor_records),
        "visitor_events.parquet": result.visitor_events,
        "daily_travel_route.parquet": result.daily_travel_route,
        "temporary_edges.parquet": result.temporary_edges,
        "travel_transmission_events.parquet": result.travel_transmission_events,
        "travel_intervention_events.parquet": result.travel_intervention_events,
        "daily_travel_intervention_state.parquet": result.daily_travel_intervention_state,
        "seasonality_schedule.parquet": result.seasonality_schedule,
        "high_risk_strata.parquet": result.high_risk_strata,
        "daily_high_risk.parquet": result.high_risk_epidemic,
        "daily_epidemic.parquet": result.daily_epidemic,
        "daily_parish.parquet": result.daily_parish,
        "daily_route.parquet": result.daily_route,
        "daily_age.parquet": result.daily_age,
        "transmission_events.parquet": result.transmission_events,
        "observation_events.parquet": result.observation_events,
        "detection_events.parquet": _detection_rows(result),
    }


def write_travel_artifact(
    result: TravelRunResult,
    root: Path,
    output_dir: Path,
) -> TravelArtifact:
    """Write all M8 tables plus parent/config/hash metadata."""

    root = root.resolve()
    output_dir = output_dir.resolve()
    artifact_id = (
        f"jos-travel-m8-{result.config.mode}-seed-{result.config.seed}-"
        f"{result.artifact_bundle_hash[:12]}"
    )
    artifact_directory = output_dir / artifact_id
    artifact_directory.mkdir(parents=True, exist_ok=True)
    manifest_path = artifact_directory / "manifest.json"
    if manifest_path.exists():
        manifest = verify_travel_artifact(artifact_directory)
        if manifest.artifact_bundle_hash != result.artifact_bundle_hash:
            raise ValueError("immutable M8 artifact ID already exists with different content")
        return TravelArtifact(artifact_directory, manifest)

    for filename, rows in _rows_for_result(result).items():
        schema = None
        if filename == "travel_intervention_events.parquet":
            rows = _serialize_intervention_event_rows(rows)
            schema = TRAVEL_INTERVENTION_EVENT_SCHEMA
        elif filename == "observation_events.parquet":
            schema = OBSERVATION_EVENT_SCHEMA
        elif filename == "detection_events.parquet":
            schema = DETECTION_EVENT_SCHEMA
        _write_rows(artifact_directory / filename, rows, schema=schema)
    _write_json(
        artifact_directory / "travel_config.json",
        result.travel_config.model_dump(mode="json"),
    )
    _write_json(artifact_directory / "parameters.json", result.parameters.model_dump(mode="json"))
    _write_json(artifact_directory / "run_config.json", result.config.model_dump(mode="json"))
    _write_json(
        artifact_directory / "observation_config.json",
        result.observation_config.model_dump(mode="json")
        if result.observation_config is not None
        else None,
    )
    _write_json(
        artifact_directory / "scenario_config.json",
        result.scenario_config.model_dump(mode="json")
        if result.scenario_config is not None
        else None,
    )
    _write_json(artifact_directory / "diagnostics.json", result.diagnostics)
    _write_json(
        artifact_directory / "parent_reference.json",
        {
            "m2_artifact_id": result.base_generated.m2_input.manifest.artifact_id,
            "m2_logical_content_hash": result.base_generated.m2_input.manifest.logical_content_hash,
            "m3_artifact_id": result.base_generated.m3_input.manifest.artifact_id,
            "m3_logical_content_hash": result.base_generated.m3_input.manifest.logical_content_hash,
            "m4_logical_content_hash": result.base_generated.logical_content_hash,
            "m5_run_config_hash": sha256_bytes(
                canonical_json_bytes(result.config.model_dump(mode="json"))
            ),
            "m5_disease_config_hash": sha256_bytes(
                canonical_json_bytes(result.parameters.model_dump(mode="json"))
            ),
        },
    )

    git_commit, dirty_worktree = _git_metadata(root)
    output_paths = sorted(
        path for path in artifact_directory.iterdir() if path.name != "manifest.json"
    )
    output_artifacts = [
        ArtifactRecord(
            path=path.name,
            sha256=sha256_file(path),
            size_bytes=path.stat().st_size,
        )
        for path in output_paths
    ]
    manifest = TravelArtifactManifest(
        artifact_id=artifact_id,
        framework_version=result.diagnostics["framework_version"],
        mode=result.travel_config.mode,
        seed=result.config.seed,
        start_date=result.config.start_date.isoformat(),
        duration_days=result.config.duration_days,
        m2_artifact_id=result.base_generated.m2_input.manifest.artifact_id,
        m2_logical_content_hash=result.base_generated.m2_input.manifest.logical_content_hash,
        m3_artifact_id=result.base_generated.m3_input.manifest.artifact_id,
        m3_logical_content_hash=result.base_generated.m3_input.manifest.logical_content_hash,
        m4_logical_content_hash=result.base_generated.logical_content_hash,
        m5_run_config_hash=sha256_bytes(
            canonical_json_bytes(result.config.model_dump(mode="json"))
        ),
        m5_disease_config_hash=sha256_bytes(
            canonical_json_bytes(result.parameters.model_dump(mode="json"))
        ),
        observation_config_hash=result.diagnostics.get("observation_config_hash"),
        m7_scenario_hash=result.diagnostics.get("m7_scenario_hash"),
        travel_config_hash=result.travel_config_hash,
        visitor_episode_hash=result.visitor_episode_hash,
        visitor_population_hash=result.travel_plan.visitor_hash,
        temporary_network_hash=result.temporary_network_hash,
        seasonality_hash=result.seasonality_hash,
        latent_outcome_hash=result.latent_outcome_hash,
        artifact_bundle_hash=result.artifact_bundle_hash,
        scenario_hash=result.scenario_hash,
        counts={
            "resident_count": len(result.base_generated.agent_ids),
            "visitor_count": len(result.travel_plan.visitor_records),
            "visitor_capacity": result.travel_plan.visitor_capacity,
            "episode_count": len(result.travel_plan.episodes),
        },
        diagnostics_status=result.diagnostics["status"],
        created_at=datetime.now(UTC).isoformat(),
        git_commit=git_commit,
        dirty_worktree_flag=dirty_worktree,
        runtime_seconds=result.runtime_seconds,
        peak_memory_bytes=result.peak_memory_bytes,
        output_artifacts=output_artifacts,
    )
    _write_json(manifest_path, manifest.model_dump(mode="json"))
    return TravelArtifact(artifact_directory, manifest)


def verify_travel_artifact(artifact_directory: Path) -> TravelArtifactManifest:
    """Verify manifest schema, required tables, hashes and parent references."""

    artifact_directory = artifact_directory.resolve()
    manifest_path = artifact_directory / "manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"M8 artifact is missing {manifest_path.name}")
    manifest = TravelArtifactManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    required = {
        "travel_episodes.parquet",
        "visitor_population.parquet",
        "daily_travel_route.parquet",
        "temporary_edges.parquet",
        "seasonality_schedule.parquet",
        "daily_epidemic.parquet",
        "transmission_events.parquet",
        "observation_events.parquet",
        "detection_events.parquet",
    }
    recorded = {record.path for record in manifest.output_artifacts}
    missing = sorted(required - recorded)
    if missing:
        raise ValueError(f"M8 artifact manifest is missing required outputs: {missing}")
    for record in manifest.output_artifacts:
        path = artifact_directory / record.path
        if not path.exists():
            raise ValueError(f"M8 artifact output is missing: {record.path}")
        if path.stat().st_size != record.size_bytes or sha256_file(path) != record.sha256:
            raise ValueError(f"M8 artifact output hash mismatch: {record.path}")

    for filename in (
        "travel_config.json",
        "parent_reference.json",
        "diagnostics.json",
        "observation_config.json",
        "scenario_config.json",
    ):
        if not (artifact_directory / filename).exists():
            raise ValueError(f"M8 artifact is missing {filename}")
    travel_config_path = artifact_directory / "travel_config.json"
    travel_payload = json.loads(travel_config_path.read_text(encoding="utf-8"))
    if sha256_bytes(canonical_json_bytes(travel_payload)) != manifest.travel_config_hash:
        raise ValueError("M8 travel config hash does not match the manifest")
    travel_config = TravelConfig.model_validate(travel_payload)
    if travel_config.seasonality_hash != manifest.seasonality_hash:
        raise ValueError("M8 seasonality identity does not match the persisted travel config")

    def rows(filename: str) -> list[dict[str, Any]]:
        values = pq.read_table(artifact_directory / filename).to_pylist()
        if filename == "travel_intervention_events.parquet":
            return _deserialize_intervention_event_rows(values)
        return values

    episode_rows = rows("travel_episodes.parquet")
    episode_rows.sort(key=lambda row: (row["arrival_date"], row["person_id"]))
    if sha256_bytes(canonical_json_bytes(episode_rows)) != manifest.visitor_episode_hash:
        raise ValueError("M8 visitor episode logical hash mismatch")
    visitor_rows = rows("visitor_population.parquet")
    visitor_rows.sort(key=lambda row: row["visitor_uid"])
    if sha256_bytes(canonical_json_bytes(visitor_rows)) != manifest.visitor_population_hash:
        raise ValueError("M8 visitor population logical hash mismatch")
    temporary_rows = rows("temporary_edges.parquet")
    temporary_rows.sort(
        key=lambda row: (
            row["time_index"],
            row["route_id"],
            row["p1_runtime_slot_uid"],
            row["p2_runtime_slot_uid"],
        )
    )
    if sha256_bytes(canonical_json_bytes(temporary_rows)) != manifest.temporary_network_hash:
        raise ValueError("M8 temporary network logical hash mismatch")

    if not episode_rows:
        latent_payload = {
            "daily_epidemic": rows("daily_epidemic.parquet"),
            "daily_parish": rows("daily_parish.parquet"),
            "daily_route": rows("daily_route.parquet"),
            "daily_age": rows("daily_age.parquet"),
            "transmission_events": _canonical_c5_events(rows("transmission_events.parquet")),
        }
    else:
        latent_payload = {
            "daily_epidemic": rows("daily_epidemic.parquet"),
            "transmission_events": rows("transmission_events.parquet"),
            "daily_travel_population": rows("daily_travel_population.parquet"),
            "daily_travel_route": rows("daily_travel_route.parquet"),
            "travel_intervention_events": rows("travel_intervention_events.parquet"),
            "seasonality_schedule": rows("seasonality_schedule.parquet"),
        }
    resolved_latent_payload = (
        latent_payload if not episode_rows else _without_null_fields(latent_payload)
    )
    if sha256_bytes(canonical_json_bytes(resolved_latent_payload)) != manifest.latent_outcome_hash:
        raise ValueError("M8 latent outcome logical hash mismatch")

    scenario_config = json.loads(
        (artifact_directory / "scenario_config.json").read_text(encoding="utf-8")
    )
    observation_config = json.loads(
        (artifact_directory / "observation_config.json").read_text(encoding="utf-8")
    )
    if (
        sha256_bytes(canonical_json_bytes(observation_config))
        if observation_config is not None
        else None
    ) != manifest.observation_config_hash:
        raise ValueError("M8 observation config logical hash mismatch")
    run_payload = json.loads((artifact_directory / "run_config.json").read_text(encoding="utf-8"))
    scenario_payload = {
        "scenario": scenario_config,
        "m4_parent_hash": manifest.m4_logical_content_hash,
        "m2_hash": manifest.m2_logical_content_hash,
        "m3_hash": manifest.m3_logical_content_hash,
        "run_config": run_payload,
        "travel_config_hash": manifest.travel_config_hash,
        "visitor_episode_hash": manifest.visitor_episode_hash,
        "temporary_network_hash": manifest.temporary_network_hash,
        "seasonality_hash": manifest.seasonality_hash,
        "starsim_version": manifest.starsim_version,
        "scenario_config": scenario_config,
        "m7_scenario_hash": manifest.m7_scenario_hash,
        "observation_config_hash": manifest.observation_config_hash,
    }
    if sha256_bytes(canonical_json_bytes(scenario_payload)) != manifest.scenario_hash:
        raise ValueError("M8 scenario logical hash mismatch")
    artifact_payload = {
        "scenario_hash": manifest.scenario_hash,
        "latent_hash": manifest.latent_outcome_hash,
        "episode_hash": manifest.visitor_episode_hash,
    }
    if sha256_bytes(canonical_json_bytes(artifact_payload)) != manifest.artifact_bundle_hash:
        raise ValueError("M8 artifact bundle logical hash mismatch")
    diagnostics = json.loads((artifact_directory / "diagnostics.json").read_text(encoding="utf-8"))
    diagnostic_hashes = diagnostics.get("hashes", {})
    for manifest_name, diagnostic_name in (
        ("scenario_hash", "scenario"),
        ("travel_config_hash", "travel_config"),
        ("visitor_episode_hash", "visitor_episode"),
        ("visitor_population_hash", "visitor_population"),
        ("temporary_network_hash", "temporary_network"),
        ("seasonality_hash", "seasonality"),
        ("latent_outcome_hash", "latent_outcome"),
        ("artifact_bundle_hash", "artifact_bundle"),
    ):
        if diagnostic_hashes.get(diagnostic_name) != getattr(manifest, manifest_name):
            raise ValueError(f"M8 manifest hash mismatch for {manifest_name}")
    parent = json.loads((artifact_directory / "parent_reference.json").read_text(encoding="utf-8"))
    for key in (
        "m2_artifact_id",
        "m2_logical_content_hash",
        "m3_artifact_id",
        "m3_logical_content_hash",
        "m4_logical_content_hash",
        "m5_run_config_hash",
        "m5_disease_config_hash",
    ):
        if parent.get(key) != getattr(manifest, key):
            raise ValueError(f"M8 parent reference mismatch for {key}")
    return manifest
