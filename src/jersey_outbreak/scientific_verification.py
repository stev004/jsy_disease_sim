"""Allow-listed, content-aware verification for M5--M8 scientific artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
from pydantic import TypeAdapter

from .artifact_catalog import SCIENTIFIC_DATASET_CATALOG
from .ensemble_schemas import (
    ComparisonArtifactManifest,
    EnsembleArtifactManifest,
    EnsembleConfig,
    EnsembleReplicateRecord,
)
from .hashing import canonical_json_bytes, sha256_bytes, sha256_file
from .intervention_artifacts import InterventionArtifactManifest, verify_intervention_artifact
from .intervention_schemas import ScenarioConfig
from .outbreak_schemas import OutbreakArtifactManifest, OutbreakRunConfig, RespiratoryParameterSet
from .population_artifacts import resolve_portable_artifact_path
from .respiratory import RespiratorySEIRS
from .scientific_hashes import (
    m5_artifact_bundle_hash,
    m5_latent_outcome_hash,
    m5_logical_content_hash,
    m6_comparison_logical_hash,
    m6_ensemble_logical_hash,
)
from .travel_artifacts import TravelArtifactManifest, verify_travel_artifact


@dataclass(frozen=True)
class VerifiedScientificArtifact:
    artifact_type: str
    artifact_id: str
    artifact_directory: Path
    manifest_payload: dict[str, Any]
    scenario_hash: str | None
    latent_hash: str | None
    bundle_hash: str | None
    logical_content_hash: str | None
    engine_git_commit: str | None
    dirty_worktree_flag: bool
    datasets: tuple[str, ...]
    size_bytes: int
    extra: dict[str, Any] = field(default_factory=dict)


def _legacy_artifact_path(path_value: str, artifact_directory: Path) -> Path:
    candidate = Path(path_value)
    if not candidate.is_absolute():
        candidate = artifact_directory / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(artifact_directory.resolve())
    except ValueError as exc:
        raise ValueError("scientific artifact output escaped its artifact directory") from exc
    return resolved


def _uses_legacy_paths(payload: dict[str, Any]) -> bool:
    version = payload.get("manifest_schema_version")
    if payload.get("module") == "generic_respiratory_seirs":
        return version in {"1.0", "1.1"}
    if "ensemble_id" in payload:
        return version in {"1.2", "1.3"}
    if "comparison_id" in payload:
        return version in {"1.0", "1.1"}
    return False


def _record_files(artifact_directory: Path, payload: dict[str, Any]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for record in payload.get("output_artifacts", []):
        try:
            candidate = (
                _legacy_artifact_path(str(record["path"]), artifact_directory)
                if _uses_legacy_paths(payload)
                else resolve_portable_artifact_path(str(record["path"]), artifact_directory)
            )
        except ValueError as exc:
            raise ValueError(
                f"invalid scientific artifact output path: {record['path']}: {exc}"
            ) from exc
        if candidate in seen:
            raise ValueError(
                f"scientific artifact manifest contains duplicate output: {record['path']}"
            )
        seen.add(candidate)
        if not candidate.is_file():
            raise ValueError(f"scientific artifact file is missing: {candidate.name}")
        if candidate.stat().st_size != int(record["size_bytes"]):
            raise ValueError(f"scientific artifact size mismatch: {candidate.name}")
        if sha256_file(candidate) != str(record["sha256"]):
            raise ValueError(f"scientific artifact hash mismatch: {candidate.name}")
        files.append(candidate)
    return files


def _required_files(files: list[Path], required: set[str]) -> None:
    names = {path.name for path in files}
    missing = sorted(required - names)
    if missing:
        raise ValueError(f"scientific artifact is incomplete: {missing}")


def _rows(directory: Path, name: str) -> list[dict[str, Any]]:
    return pq.read_table(directory / name).to_pylist()


def _verify_m5_tables(
    manifest: OutbreakArtifactManifest,
    daily_epidemic: list[dict[str, Any]],
    daily_parish: list[dict[str, Any]],
    daily_route: list[dict[str, Any]],
    daily_age: list[dict[str, Any]],
    events: list[dict[str, Any]],
    diagnostics: dict[str, Any],
) -> None:
    if len(daily_epidemic) != manifest.duration_days:
        raise ValueError("M5 daily epidemic horizon does not match the manifest")
    population_sizes: set[int] = set()
    cumulative_previous = 0
    for expected_index, row in enumerate(daily_epidemic):
        if int(row["time_index"]) != expected_index:
            raise ValueError("M5 daily epidemic time index is not canonical")
        state_values = [
            int(row[name]) for name in ("susceptible", "exposed", "infectious", "recovered", "dead")
        ]
        if any(value < 0 for value in state_values):
            raise ValueError("M5 epidemic compartment is negative")
        population_sizes.add(sum(state_values))
        if int(row["new_infections"]) != int(row["new_local_infections"]) + int(
            row["new_imported_infections"]
        ):
            raise ValueError("M5 daily infection flows do not reconcile")
        cumulative = int(row["cumulative_total_infections"])
        increment = (
            int(row["new_local_infections"])
            + int(row["new_imported_infections"])
            + int(row["new_seeded_infections"])
        )
        if cumulative != cumulative_previous + increment:
            raise ValueError("M5 cumulative infections do not reconcile")
        cumulative_previous = cumulative
    if len(population_sizes) != 1:
        raise ValueError("M5 population conservation failed")
    population_size = next(iter(population_sizes))
    benchmark = diagnostics.get("benchmark", {})
    if (
        diagnostics.get("status") != "passed"
        or benchmark.get("n_agents") != population_size
        or benchmark.get("n_points") != manifest.duration_days
    ):
        raise ValueError("M5 diagnostics do not match persisted daily content")

    epidemic_by_date = {str(row["date"]): row for row in daily_epidemic}
    for rows, value_name, label in (
        (daily_parish, "new_infections", "parish"),
        (daily_age, "new_infections", "age"),
        (daily_route, "new_local_infections", "route"),
    ):
        totals: dict[str, int] = {}
        for row in rows:
            date = str(row["date"])
            totals[date] = totals.get(date, 0) + int(row[value_name])

        if label == "route":
            expected_totals = {
                date: int(epidemic["new_local_infections"])
                for date, epidemic in epidemic_by_date.items()
            }
        else:
            expected_totals = {
                date: (
                    int(epidemic["new_local_infections"])
                    + int(epidemic["new_imported_infections"])
                    + int(epidemic["new_seeded_infections"])
                )
                for date, epidemic in epidemic_by_date.items()
            }
        if any(totals.get(date, 0) != value for date, value in expected_totals.items()):
            raise ValueError(f"M5 daily {label} totals do not reconcile")

    event_totals = {"local": 0, "imported": 0, "seeded": 0}
    events_by_date: dict[str, dict[str, int]] = {}
    for event in events:
        source = (
            "seeded" if event.get("seeded") else "imported" if event.get("imported") else "local"
        )
        event_totals[source] += 1
        per_date = events_by_date.setdefault(str(event["date"]), {key: 0 for key in event_totals})
        per_date[source] += 1
    for date, epidemic in epidemic_by_date.items():
        per_date = events_by_date.get(date, {key: 0 for key in event_totals})
        if (
            per_date["local"] != int(epidemic["new_local_infections"])
            or per_date["imported"] != int(epidemic["new_imported_infections"])
            or per_date["seeded"] != int(epidemic["new_seeded_infections"])
        ):
            raise ValueError("M5 transmission events do not reconcile with daily flows")
    attribution = diagnostics.get("attribution", {}).get("totals", {})
    if any(attribution.get(key) != value for key, value in event_totals.items()):
        raise ValueError("M5 attribution diagnostics do not match transmission events")
    if attribution.get("total_events") != len(events):
        raise ValueError("M5 total event diagnostics do not reconcile")


def _reconstruct_m5_config(
    manifest: OutbreakArtifactManifest, parameters: RespiratoryParameterSet
) -> OutbreakRunConfig:
    seed_spec = manifest.seed_specification
    import_spec = manifest.import_specification
    initial_prevalence = seed_spec.get("initial_prevalence")
    initial_seed_count = 0 if initial_prevalence is not None else int(seed_spec["requested_count"])
    return OutbreakRunConfig(
        generator_version=manifest.generator_version,
        mode=manifest.mode,
        seed=manifest.seed,
        start_date=manifest.start_date,
        duration_days=manifest.duration_days,
        dt_days=manifest.dt_days,
        parameter_set_id=manifest.parameter_set_id,
        initial_seed_count=initial_seed_count,
        initial_prevalence=initial_prevalence,
        import_schedule={
            str(key): int(value) for key, value in import_spec.get("schedule", {}).items()
        },
        import_rate_per_day=float(import_spec.get("rate_per_day", 0.0)),
        beta=parameters.numeric("transmission_beta"),
        latent_duration=parameters.durations["latent"],
        infectious_duration=parameters.durations["infectious"],
        immunity_duration=parameters.durations["immunity"],
        symptomatic_probability=parameters.numeric("symptom_probability"),
        waning_enabled=bool(round(parameters.numeric("immunity_waning_enabled"))),
        route_multipliers=dict(parameters.route_multipliers),
    )


def verify_m5_artifact(artifact_directory: Path) -> VerifiedScientificArtifact:
    artifact_directory = artifact_directory.resolve()
    manifest_path = artifact_directory / "manifest.json"
    manifest = OutbreakArtifactManifest.model_validate_json(manifest_path.read_bytes())
    payload = manifest.model_dump(mode="json")
    files = _record_files(artifact_directory, payload)
    _required_files(
        files,
        {
            "daily_epidemic.parquet",
            "daily_parish.parquet",
            "daily_route.parquet",
            "daily_age.parquet",
            "transmission_events.parquet",
            "parameters.json",
            "diagnostics.json",
            "network_reference.json",
        },
    )
    if manifest.diagnostics_status != "passed":
        raise ValueError("M5 artifact diagnostics did not pass")
    parameters_payload = json.loads((artifact_directory / "parameters.json").read_text())
    for parameter in parameters_payload.get("parameters", {}).values():
        valid_range = parameter.get("valid_range")
        if isinstance(valid_range, list):
            parameter["valid_range"] = tuple(valid_range)
    parameters = RespiratoryParameterSet.model_validate(parameters_payload)
    parameter_hash = sha256_bytes(canonical_json_bytes(parameters.model_dump(mode="json")))
    if parameter_hash != manifest.parameter_set_hash:
        raise ValueError("M5 disease parameter logical hash mismatch")
    config = _reconstruct_m5_config(manifest, parameters)
    config_payload = config.model_dump(mode="json")
    config_hash = sha256_bytes(canonical_json_bytes(config_payload))
    if config_hash != manifest.config_hash:
        raise ValueError("M5 run configuration logical hash mismatch")
    network = json.loads((artifact_directory / "network_reference.json").read_text())
    if (
        network.get("m4_artifact_id") != manifest.m4_artifact_id
        or network.get("m4_logical_content_hash") != manifest.m4_logical_content_hash
    ):
        raise ValueError("M5 network parent identity mismatch")
    daily_epidemic = _rows(artifact_directory, "daily_epidemic.parquet")
    daily_parish = _rows(artifact_directory, "daily_parish.parquet")
    daily_route = _rows(artifact_directory, "daily_route.parquet")
    daily_age = _rows(artifact_directory, "daily_age.parquet")
    transmission_events = _rows(artifact_directory, "transmission_events.parquet")
    diagnostics = json.loads((artifact_directory / "diagnostics.json").read_text())
    _verify_m5_tables(
        manifest,
        daily_epidemic,
        daily_parish,
        daily_route,
        daily_age,
        transmission_events,
        diagnostics,
    )
    latent_hash = m5_latent_outcome_hash(
        daily_epidemic=daily_epidemic,
        daily_parish=daily_parish,
        daily_route=daily_route,
        daily_age=daily_age,
        transmission_events=transmission_events,
    )
    logical_hash = m5_logical_content_hash(
        config=config_payload,
        parameters=parameters.model_dump(mode="json"),
        latent_hash=latent_hash,
        network_hash=manifest.m4_logical_content_hash,
    )
    if logical_hash != manifest.logical_content_hash:
        raise ValueError("M5 scientific logical content hash mismatch")
    if not manifest.artifact_id.endswith(logical_hash[:12]):
        raise ValueError("M5 artifact ID does not bind its logical content hash")
    bundle_hash = m5_artifact_bundle_hash(
        logical_hash=logical_hash,
        latent_hash=latent_hash,
        scenario_hash=None,
        daily_intervention_state=[],
        intervention_events=[],
        route_effects=[],
    )
    datasets = tuple(sorted(SCIENTIFIC_DATASET_CATALOG["m5_outbreak"]))
    return VerifiedScientificArtifact(
        "m5_outbreak",
        manifest.artifact_id,
        artifact_directory,
        payload,
        None,
        latent_hash,
        bundle_hash,
        logical_hash,
        manifest.git_commit,
        manifest.dirty_worktree_flag,
        datasets,
        sum(path.stat().st_size for path in artifact_directory.rglob("*") if path.is_file()),
        {
            "run_config": config_payload,
            "run_config_hash": config_hash,
            "parameter_hash": parameter_hash,
        },
    )


def verify_m6_ensemble_artifact(artifact_directory: Path) -> VerifiedScientificArtifact:
    artifact_directory = artifact_directory.resolve()
    manifest = EnsembleArtifactManifest.model_validate_json(
        (artifact_directory / "manifest.json").read_bytes()
    )
    payload = manifest.model_dump(mode="json")
    files = _record_files(artifact_directory, payload)
    _required_files(
        files,
        {
            "ensemble_summary.parquet",
            "replicate_trajectories.parquet",
            "replicate_grid.parquet",
            "replicate_records.json",
            "ensemble_config.json",
            "diagnostics.json",
        },
    )
    if manifest.diagnostics_status != "passed" or manifest.status != "passed":
        raise ValueError("M6 ensemble diagnostics did not pass")
    config = EnsembleConfig.model_validate_json(
        (artifact_directory / "ensemble_config.json").read_bytes()
    )
    records = TypeAdapter(list[EnsembleReplicateRecord]).validate_json(
        (artifact_directory / "replicate_records.json").read_bytes()
    )
    record_payloads = [record.model_dump(mode="json") for record in records]
    if record_payloads != [record.model_dump(mode="json") for record in manifest.replicate_records]:
        raise ValueError("M6 replicate records do not match the manifest")
    if (
        len(records) != manifest.replicate_count
        or tuple(record.seed for record in records) != manifest.replicate_seeds
        or tuple(config.replicate_seeds) != manifest.replicate_seeds
        or config.ensemble_id != manifest.ensemble_id
    ):
        raise ValueError("M6 replicate identity contract does not reconcile")
    successful = [record for record in records if record.status == "passed"]
    failed = [record for record in records if record.status == "failed"]
    if (
        len(successful) != manifest.successful_replicates
        or len(failed) != manifest.failed_replicates
        or config.workers != manifest.requested_workers
    ):
        raise ValueError("M6 replicate or worker counts do not reconcile")
    trajectory_rows = _rows(artifact_directory, "replicate_trajectories.parquet")
    trajectories: dict[int, list[dict[str, Any]]] = {}
    for row in trajectory_rows:
        trajectories.setdefault(int(row["seed"]), []).append(row)
    summary = _rows(artifact_directory, "ensemble_summary.parquet")
    grid = _rows(artifact_directory, "replicate_grid.parquet")
    successful_seeds = {record.seed for record in successful}
    if {int(row["seed"]) for row in trajectory_rows} != successful_seeds:
        raise ValueError("M6 trajectory seeds do not match successful replicate records")
    if grid and {int(row["seed"]) for row in grid} != set(manifest.replicate_seeds):
        raise ValueError("M6 completed grid seeds do not match requested replicates")
    for row in summary:
        if (
            int(row["requested_replicates"]) != manifest.replicate_count
            or int(row["successful_replicates"]) != manifest.successful_replicates
            or int(row["failed_replicates"]) != manifest.failed_replicates
        ):
            raise ValueError("M6 summary replicate counts do not reconcile")
    logical_hash = m6_ensemble_logical_hash(
        config=config.model_dump(mode="json"),
        replicate_records=record_payloads,
        summary=summary,
        trajectories=trajectories,
        replicate_grid=grid,
    )
    if logical_hash != manifest.logical_content_hash:
        raise ValueError("M6 ensemble scientific logical content hash mismatch")
    if not manifest.artifact_id.endswith(logical_hash[:12]):
        raise ValueError("M6 ensemble artifact ID does not bind its logical content hash")
    config_hash = sha256_bytes(canonical_json_bytes(config.model_dump(mode="json")))
    if config_hash != manifest.base_config_hash:
        raise ValueError("M6 ensemble configuration hash mismatch")
    observation_hash = sha256_bytes(
        canonical_json_bytes(config.observation_config.model_dump(mode="json"))
    )
    if observation_hash != manifest.observation_parameter_hash:
        raise ValueError("M6 observation configuration hash mismatch")
    expected_m4 = {
        str(record.seed): record.m4_logical_content_hash
        for record in successful
        if record.m4_logical_content_hash is not None
    }
    expected_m5 = {
        str(record.seed): record.latent_run_logical_content_hash
        for record in successful
        if record.latent_run_logical_content_hash is not None
    }
    if (
        expected_m4 != manifest.m4_logical_content_hashes
        or expected_m5 != manifest.m5_logical_content_hashes
    ):
        raise ValueError("M6 replicate parent identities do not match the manifest")
    expected_interventions = {
        intervention_id: intervention_hash
        for record in successful
        for intervention_id, intervention_hash in record.intervention_config_hashes.items()
    }
    if expected_interventions != manifest.intervention_config_hashes:
        raise ValueError("M6 intervention identities do not match replicate records")
    diagnostics = json.loads((artifact_directory / "diagnostics.json").read_text())
    if (
        diagnostics.get("status") != manifest.status
        or diagnostics.get("successful_replicates") != manifest.successful_replicates
        or diagnostics.get("failed_replicates") != manifest.failed_replicates
        or diagnostics.get("requested_workers") != manifest.requested_workers
        or diagnostics.get("planned_workers") != manifest.planned_workers
        or diagnostics.get("actual_workers") != manifest.actual_workers
    ):
        raise ValueError("M6 diagnostics do not match the artifact manifest")
    scenario_hash = (
        sha256_bytes(
            canonical_json_bytes(
                {
                    str(record.seed): record.scenario_hash
                    for record in records
                    if record.status == "passed" and record.scenario_hash is not None
                }
            )
        )
        if config.scenario is not None
        else None
    )
    if scenario_hash != manifest.scenario_hash:
        raise ValueError("M6 ensemble scenario hash mismatch")
    return VerifiedScientificArtifact(
        "m6_ensemble",
        manifest.artifact_id,
        artifact_directory,
        payload,
        scenario_hash,
        None,
        logical_hash,
        logical_hash,
        manifest.git_commit,
        manifest.dirty_worktree_flag,
        tuple(sorted(SCIENTIFIC_DATASET_CATALOG["m6_ensemble"])),
        sum(path.stat().st_size for path in artifact_directory.rglob("*") if path.is_file()),
        {"ensemble_config": config.model_dump(mode="json")},
    )


def verify_m6_comparison_artifact(artifact_directory: Path) -> VerifiedScientificArtifact:
    artifact_directory = artifact_directory.resolve()
    manifest = ComparisonArtifactManifest.model_validate_json(
        (artifact_directory / "manifest.json").read_bytes()
    )
    payload = manifest.model_dump(mode="json")
    files = _record_files(artifact_directory, payload)
    required_files = {
        "matched_seed_comparison.parquet",
        "comparison_config.json",
        "diagnostics.json",
    }
    if manifest.manifest_schema_version in {"1.1", "1.2"}:
        required_files.add("paired_difference_summary.parquet")
    _required_files(files, required_files)
    if manifest.status != "passed":
        raise ValueError("M6 comparison did not pass")
    config = json.loads((artifact_directory / "comparison_config.json").read_text())
    rows = _rows(artifact_directory, "matched_seed_comparison.parquet")
    summary = (
        _rows(artifact_directory, "paired_difference_summary.parquet")
        if manifest.manifest_schema_version in {"1.1", "1.2"}
        else None
    )
    for key in ("comparison_id", "config_a_hash", "config_b_hash"):
        if config.get(key) != getattr(manifest, key):
            raise ValueError(f"M6 comparison configuration mismatch for {key}")
    if tuple(config.get("matched_seed_list", [])) != manifest.matched_seed_list:
        raise ValueError("M6 comparison matched seed list mismatch")
    logical_hash = m6_comparison_logical_hash(
        comparison_id=manifest.comparison_id,
        config_a_hash=manifest.config_a_hash,
        config_b_hash=manifest.config_b_hash,
        rows=rows,
        summary=summary,
    )
    if logical_hash != manifest.logical_content_hash:
        raise ValueError("M6 comparison scientific logical content hash mismatch")
    if not manifest.artifact_id.endswith(logical_hash[:12]):
        raise ValueError("M6 comparison artifact ID does not bind its logical content hash")
    if manifest.paired_count + manifest.missing_or_failed_pairs != len(manifest.matched_seed_list):
        raise ValueError("M6 comparison paired and failed counts do not reconcile")
    paired_seeds = {
        int(row["seed"]) for row in rows if row["status"] in {"paired", "missing_metric"}
    }
    failed_seeds = {int(row["seed"]) for row in rows if row["status"] == "missing_or_failed"}
    if (
        len(paired_seeds) != manifest.paired_count
        or len(failed_seeds) != manifest.missing_or_failed_pairs
        or paired_seeds | failed_seeds != set(manifest.matched_seed_list)
    ):
        raise ValueError("M6 comparison rows do not match paired seed counts")
    diagnostics = json.loads((artifact_directory / "diagnostics.json").read_text())
    if (
        diagnostics.get("status") != manifest.status
        or diagnostics.get("paired_seed_count") != manifest.paired_count
        or diagnostics.get("missing_or_failed_pair_count") != manifest.missing_or_failed_pairs
    ):
        raise ValueError("M6 comparison diagnostics do not match the manifest")
    return VerifiedScientificArtifact(
        "m6_comparison",
        manifest.artifact_id,
        artifact_directory,
        payload,
        None,
        None,
        logical_hash,
        logical_hash,
        manifest.git_commit,
        manifest.dirty_worktree_flag,
        tuple(sorted(SCIENTIFIC_DATASET_CATALOG["m6_comparison"])),
        sum(path.stat().st_size for path in artifact_directory.rglob("*") if path.is_file()),
        {"comparison_config": config},
    )


def _decode_m7_events(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decoded: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        for key in ("previous_state", "new_state"):
            if isinstance(item.get(key), str):
                item[key] = json.loads(item[key])
        decoded.append(item)
    return decoded


def verify_m7_artifact(artifact_directory: Path) -> VerifiedScientificArtifact:
    artifact_directory = artifact_directory.resolve()
    manifest: InterventionArtifactManifest = verify_intervention_artifact(artifact_directory)
    payload = manifest.model_dump(mode="json")
    latent_dirs = list((artifact_directory / "latent_outputs").glob("jos-outbreak-m5-*"))
    if len(latent_dirs) != 1:
        raise ValueError("M7 artifact must contain exactly one M5 latent bundle")
    latent = verify_m5_artifact(latent_dirs[0])
    if latent.artifact_id != manifest.latent_bundle_artifact_id:
        raise ValueError("M7 latent artifact identity mismatch")
    if (
        latent.latent_hash != manifest.latent_outcome_hash
        or latent.logical_content_hash != manifest.latent_logical_content_hash
    ):
        raise ValueError("M7 latent scientific identity mismatch")
    if (
        latent.manifest_payload["m2_logical_content_hash"] != manifest.m2_logical_content_hash
        or latent.manifest_payload["m3_logical_content_hash"] != manifest.m3_logical_content_hash
        or latent.manifest_payload["m4_logical_content_hash"] != manifest.m4_logical_content_hash
    ):
        raise ValueError("M7/M5 parent identity mismatch")
    if (
        latent.engine_git_commit != manifest.git_commit
        or latent.dirty_worktree_flag != manifest.dirty_worktree_flag
    ):
        raise ValueError("M7/M5 engine provenance mismatch")
    scenario_path = artifact_directory / "scenario_config.json"
    scenario = ScenarioConfig.model_validate_json(scenario_path.read_bytes())
    if scenario.config_hash != manifest.scenario_config_hash:
        raise ValueError("M7 scenario configuration hash mismatch")
    model_versions = {
        "intervention_framework": "7.0.0",
        "outbreak_generator": latent.manifest_payload["generator_version"],
        "respiratory_module": RespiratorySEIRS.disease_module_version,
    }
    scenario_hash = scenario.run_hash(
        disease_config_hash=manifest.m5_disease_config_hash,
        network_hash=manifest.m4_logical_content_hash,
        observation_config_hash=manifest.c4_observation_config_hash,
        seed=manifest.seed,
        start_date=__import__("datetime").date.fromisoformat(manifest.start_date),
        duration_days=manifest.duration_days,
        run_config_hash=manifest.run_config_hash,
        m2_hash=manifest.m2_logical_content_hash,
        m3_hash=manifest.m3_logical_content_hash,
        starsim_version=manifest.starsim_version,
        jos_model_versions=model_versions,
    )
    if scenario_hash != manifest.scenario_hash:
        raise ValueError("M7 scenario logical hash mismatch")
    bundle_hash = m5_artifact_bundle_hash(
        logical_hash=manifest.latent_logical_content_hash,
        latent_hash=manifest.latent_outcome_hash,
        scenario_hash=scenario_hash,
        daily_intervention_state=_rows(artifact_directory, "daily_intervention_state.parquet"),
        intervention_events=_decode_m7_events(
            _rows(artifact_directory, "intervention_events.parquet")
        ),
        route_effects=_rows(artifact_directory, "route_effects.parquet"),
    )
    if bundle_hash != manifest.artifact_bundle_hash or bundle_hash != manifest.logical_content_hash:
        raise ValueError("M7 artifact bundle logical hash mismatch")
    if not manifest.artifact_id.endswith(bundle_hash[:12]):
        raise ValueError("M7 artifact ID does not bind its logical content hash")
    return VerifiedScientificArtifact(
        "m7_intervention",
        manifest.artifact_id,
        artifact_directory,
        payload,
        scenario_hash,
        manifest.latent_outcome_hash,
        bundle_hash,
        bundle_hash,
        manifest.git_commit,
        manifest.dirty_worktree_flag,
        tuple(sorted(SCIENTIFIC_DATASET_CATALOG["m7_intervention"])),
        sum(path.stat().st_size for path in artifact_directory.rglob("*") if path.is_file()),
        {
            "scenario_config": scenario.model_dump(mode="json"),
            "run_config": latent.extra["run_config"],
        },
    )


def verify_m8_artifact(artifact_directory: Path) -> VerifiedScientificArtifact:
    artifact_directory = artifact_directory.resolve()
    manifest: TravelArtifactManifest = verify_travel_artifact(artifact_directory)
    payload = manifest.model_dump(mode="json")
    return VerifiedScientificArtifact(
        "m8_travel",
        manifest.artifact_id,
        artifact_directory,
        payload,
        manifest.scenario_hash,
        manifest.latent_outcome_hash,
        manifest.artifact_bundle_hash,
        manifest.artifact_bundle_hash,
        manifest.git_commit,
        manifest.dirty_worktree_flag,
        tuple(sorted(SCIENTIFIC_DATASET_CATALOG["m8_travel"])),
        sum(path.stat().st_size for path in artifact_directory.rglob("*") if path.is_file()),
        {
            "scenario_config": json.loads(
                (artifact_directory / "scenario_config.json").read_text()
            ),
            "run_config": json.loads((artifact_directory / "run_config.json").read_text()),
        },
    )


def verify_scientific_artifact(artifact_directory: Path) -> VerifiedScientificArtifact:
    """Dispatch one manifest to a fixed verifier; artifact data cannot choose code."""

    artifact_directory = artifact_directory.resolve()
    payload = json.loads((artifact_directory / "manifest.json").read_text(encoding="utf-8"))
    if "travel_config_hash" in payload:
        return verify_m8_artifact(artifact_directory)
    if "latent_bundle_artifact_id" in payload:
        return verify_m7_artifact(artifact_directory)
    if "ensemble_id" in payload:
        return verify_m6_ensemble_artifact(artifact_directory)
    if "comparison_id" in payload:
        return verify_m6_comparison_artifact(artifact_directory)
    if payload.get("module") == "generic_respiratory_seirs":
        return verify_m5_artifact(artifact_directory)
    raise ValueError("unsupported scientific artifact manifest")
