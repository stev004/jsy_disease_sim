"""Application-to-engine adapter used by the M9 worker only.

FastAPI routes and the persistent scheduler never call scientific modules
directly.  This module is the single translation boundary from a validated
M9 request to the already verified M5–M8 orchestration and artifact writers.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from .api_schemas import API_SCHEMA_VERSION, JobRequest
from .ensemble import compare_ensembles, run_ensemble
from .ensemble_artifacts import write_comparison_artifact, write_ensemble_artifact
from .hashing import sha256_file
from .intervention_artifacts import write_intervention_artifact
from .intervention_schemas import ScenarioConfig
from .network_artifacts import write_network_artifact
from .network_generator import generate_networks
from .network_schemas import NetworkGenerationConfig
from .observation import load_observation_config
from .observation_schemas import ObservationConfig
from .outbreak_artifacts import write_outbreak_artifact
from .outbreak_runner import default_run_config, load_parameter_set, run_outbreak
from .outbreak_schemas import OutbreakRunConfig, RespiratoryParameterSet
from .population_artifacts import write_population_artifact
from .population_generator import generate_population
from .population_schemas import PopulationGenerationConfig, PopulationMode
from .population_structure_artifacts import (
    load_m2_population_artifact,
    load_m3_structure_artifact,
    write_structure_artifact,
)
from .population_structure_generator import generate_structure
from .population_structure_schemas import StructureGenerationConfig
from .scientific_verification import verify_scientific_artifact
from .travel import TravelRunResult
from .travel_artifacts import write_travel_artifact

ProgressCallback = Callable[[str, str], None]


@dataclass(frozen=True)
class AdapterResult:
    """Untrusted worker locators consumed by the application finalizer."""

    artifacts: tuple[dict[str, Any], ...]


def _git_identity(root: Path) -> tuple[str | None, bool]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=False, capture_output=True, text=True
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


def observed_engine_identity(root: Path) -> dict[str, Any]:
    """Return provenance captured by the worker, rather than copied from HTTP."""

    commit, dirty = _git_identity(root)
    return {
        "engine_git_commit": commit,
        "dirty_worktree_flag": dirty,
        "python_version": platform.python_version(),
        "starsim_version": "3.5.2",
    }


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _build_parent(root: Path, mode: PopulationMode, seed: int, destination: Path):
    """Build the existing M2/M3/M4 parent inside the job-owned directory."""

    parent_output = destination / "parents"
    m2_generated = generate_population(root, PopulationGenerationConfig(mode=mode, seed=seed))
    m2_artifact = write_population_artifact(m2_generated, root, parent_output / "populations")
    m2_input = load_m2_population_artifact(root, m2_artifact.artifact_directory)
    m3_generated = generate_structure(
        root, StructureGenerationConfig(mode=mode, seed=seed), m2_input
    )
    m3_artifact = write_structure_artifact(
        m3_generated, root, parent_output / "structures", m2_input
    )
    m3_input = load_m3_structure_artifact(root, m3_artifact.artifact_directory)
    generated = generate_networks(
        NetworkGenerationConfig(mode=mode, seed=seed), m2_input, m3_input, root
    )
    # The M4 artifact is a useful reconstructibility parent.  It is not
    # returned as a user result artifact, but it remains within the job root.
    write_network_artifact(generated, root, parent_output / "networks")
    return generated


def _parameters(root: Path, supplied: RespiratoryParameterSet | None) -> RespiratoryParameterSet:
    return supplied or load_parameter_set(root)


def _observation(root: Path, supplied: ObservationConfig | None) -> ObservationConfig:
    return supplied or load_observation_config(root)


def _run_config(request: Any, parameters: RespiratoryParameterSet) -> OutbreakRunConfig:
    supplied = getattr(request, "run_config", None)
    if supplied is None:
        return default_run_config(
            request.mode,
            request.seed if hasattr(request, "seed") else request.replicate_seeds[0],
            parameters,
            start_date=request.start_date,
            duration_days=request.duration_days,
        )
    config = OutbreakRunConfig.model_validate(supplied)
    expected_seed = request.seed if hasattr(request, "seed") else request.replicate_seeds[0]
    if (config.mode, config.seed, config.start_date, config.duration_days) != (
        request.mode,
        expected_seed,
        request.start_date,
        request.duration_days,
    ):
        raise ValueError("run_config mode, seed, date and duration must match the API request")
    if config.parameter_set_id != parameters.parameter_set_id:
        raise ValueError("run_config parameter_set_id must match the supplied parameter set")
    return config


def _normalize_scenario(
    scenario: ScenarioConfig | None,
    *,
    seed: int,
    run_config: OutbreakRunConfig,
    parameters: RespiratoryParameterSet,
    observation: ObservationConfig | None,
) -> ScenarioConfig | None:
    if scenario is None:
        return None
    if scenario.seed is not None and scenario.seed != seed:
        raise ValueError("scenario seed must match the run seed")
    if scenario.start_date is not None and scenario.start_date != run_config.start_date:
        raise ValueError("scenario start_date must match the run start_date")
    if scenario.duration_days is not None and scenario.duration_days != run_config.duration_days:
        raise ValueError("scenario duration_days must match the run duration_days")
    return scenario.model_copy(
        update={
            "seed": seed,
            "start_date": run_config.start_date,
            "duration_days": run_config.duration_days,
            "disease_config_id": parameters.parameter_set_id,
            "observation_config_id": observation.observation_config_id if observation else None,
        }
    )


def _path_inside(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("scientific artifact escaped its job output directory") from exc
    return resolved


def _dataset_names(artifact_directory: Path, payload: dict[str, Any]) -> list[str]:
    names: set[str] = set()
    for record in payload.get("output_artifacts", []):
        candidate = Path(str(record["path"]))
        if not candidate.is_absolute():
            candidate = artifact_directory / candidate
        try:
            candidate = _path_inside(candidate, artifact_directory)
        except ValueError:
            continue
        if candidate.suffix == ".parquet" and candidate.is_file():
            names.add(candidate.stem)
    return sorted(names)


def artifact_reference(
    artifact_directory: Path,
    job_directory: Path,
    *,
    role: str,
    artifact_type: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    artifact_directory = _path_inside(artifact_directory, job_directory)
    manifest_path = artifact_directory / "manifest.json"
    hashes = {
        "scenario_hash": payload.get("scenario_hash"),
        "latent_hash": payload.get("latent_outcome_hash")
        or payload.get("latent_logical_content_hash"),
        "bundle_hash": payload.get("artifact_bundle_hash"),
        "logical_content_hash": payload.get("logical_content_hash"),
    }
    size_bytes = sum(
        path.stat().st_size for path in artifact_directory.rglob("*") if path.is_file()
    )
    return {
        "role": role,
        "artifact_type": artifact_type,
        "artifact_id": str(payload["artifact_id"]),
        "manifest_path": str(manifest_path.relative_to(job_directory)),
        **hashes,
        "verification_status": "passed",
        "size_bytes": size_bytes,
        "datasets": _dataset_names(artifact_directory, payload),
    }


def _finish_artifact(
    artifact_directory: Path,
    job_directory: Path,
    *,
    role: str,
    hash_overrides: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    verified = verify_scientific_artifact(artifact_directory)
    reference = artifact_reference(
        artifact_directory,
        job_directory,
        role=role,
        artifact_type=verified.artifact_type,
        payload=verified.manifest_payload,
    )
    for name in ("scenario_hash", "latent_hash", "bundle_hash"):
        if reference[name] is None and hash_overrides and hash_overrides.get(name) is not None:
            reference[name] = hash_overrides[name]
    return reference


def execute_job(
    request_payload: dict[str, Any],
    *,
    root: Path,
    job_directory: Path,
    progress: ProgressCallback | None = None,
) -> AdapterResult:
    """Execute one validated request and return verified artifact references."""

    request = parse_request(request_payload)
    root = root.resolve()
    job_directory = job_directory.resolve()
    output_root = job_directory / "artifacts"
    output_root.mkdir(parents=True, exist_ok=True)

    def phase(name: str, message: str) -> None:
        if progress is not None:
            progress(name, message)

    phase("validating", "Reloaded and validated the persisted canonical request")
    parameters = _parameters(root, getattr(request, "parameters", None))
    if request.kind == "scenario_run":
        run_config = _run_config(request, parameters)
        observation = (
            _observation(root, request.observation_config)
            if request.scenario is not None or request.observation_config is not None
            else None
        )
        scenario = _normalize_scenario(
            request.scenario,
            seed=request.seed,
            run_config=run_config,
            parameters=parameters,
            observation=observation,
        )
        phase("preparing", "Building the immutable M2/M3/M4 scientific parent")
        generated = _build_parent(root, request.mode, request.seed, job_directory)
        phase("running", "Executing the existing JOS scientific runner")
        result = run_outbreak(
            generated,
            run_config,
            parameters,
            observation_config=observation,
            scenario=scenario,
        )
        phase("writing_artifacts", "Writing the versioned scientific artifact")
        if isinstance(result, TravelRunResult):
            artifact_dir = write_travel_artifact(result, root, output_root).artifact_directory
        elif scenario is not None:
            artifact_dir = write_intervention_artifact(  # type: ignore[arg-type]
                result, root, output_root
            ).artifact_directory
        else:
            artifact_dir = write_outbreak_artifact(result, root, output_root).artifact_directory
        phase("verifying", "Verifying scientific manifest and output hashes")
        scientific_hashes = {
            "scenario_hash": getattr(result, "scenario_hash", None),
            "latent_hash": getattr(result, "latent_outcome_hash", None)
            or getattr(result, "logical_content_hash", None),
            "bundle_hash": getattr(result, "artifact_bundle_hash", None),
        }
        reference = _finish_artifact(
            artifact_dir,
            job_directory,
            role="scientific_result",
            hash_overrides=scientific_hashes,
        )
        phase("finalizing", "Scientific artifact is ready for application finalization")
        return AdapterResult((reference,))

    if request.kind == "ensemble":
        first_seed = request.replicate_seeds[0]
        run_config = _run_config(request, parameters)
        observation = _observation(root, request.observation_config)
        scenario = _normalize_scenario(
            request.scenario,
            seed=first_seed,
            run_config=run_config,
            parameters=parameters,
            observation=observation,
        )
        phase("preparing", "Building the immutable M2/M3/M4 scientific parent")
        generated = _build_parent(root, request.mode, first_seed, job_directory)
        phase("running", "Executing the existing bounded ensemble runner")
        ensemble_result = run_ensemble(
            root,
            generated,
            parameters,
            run_config,
            observation,
            request.replicate_seeds,
            ensemble_id=request.ensemble_id,
            workers=request.workers,
            allow_unsafe_workers=request.allow_unsafe_workers,
            scenario=scenario,
        )
        phase("writing_artifacts", "Writing the ensemble scientific artifact")
        ensemble_artifact = write_ensemble_artifact(ensemble_result, root, output_root)
        phase("verifying", "Verifying ensemble manifest and output hashes")
        reference = _finish_artifact(
            ensemble_artifact.artifact_directory,
            job_directory,
            role="ensemble",
            hash_overrides={"scenario_hash": ensemble_result.scenario_hash},
        )
        phase("finalizing", "Ensemble artifact is ready for application finalization")
        return AdapterResult((reference,))

    # The comparison path executes two existing ensembles and then the
    # existing matched-seed comparison.  The API scheduler counts this whole
    # operation as one job, preserving the default one-job safety boundary.
    first_seed = request.replicate_seeds[0]
    observation = _observation(root, request.observation_config)
    base_config = default_run_config(
        request.mode,
        first_seed,
        parameters,
        start_date=request.start_date,
        duration_days=request.duration_days,
    )
    baseline = _normalize_scenario(
        request.baseline,
        seed=first_seed,
        run_config=base_config,
        parameters=parameters,
        observation=observation,
    )
    treated = _normalize_scenario(
        request.treated,
        seed=first_seed,
        run_config=base_config,
        parameters=parameters,
        observation=observation,
    )
    phase("preparing", "Building the shared immutable M2/M3/M4 comparison parent")
    generated = _build_parent(root, request.mode, first_seed, job_directory)
    phase("running", "Executing matched baseline and treated ensembles")
    ensemble_a = run_ensemble(
        root,
        generated,
        parameters,
        base_config,
        observation,
        request.replicate_seeds,
        ensemble_id=f"{request.comparison_id}-baseline",
        workers=request.workers,
        allow_unsafe_workers=request.allow_unsafe_workers,
        scenario=baseline,
    )
    ensemble_b = run_ensemble(
        root,
        generated,
        parameters,
        base_config,
        observation,
        request.replicate_seeds,
        ensemble_id=f"{request.comparison_id}-treated",
        workers=request.workers,
        allow_unsafe_workers=request.allow_unsafe_workers,
        scenario=treated,
    )
    phase("writing_artifacts", "Writing both ensemble artifacts and paired results")
    artifact_a = write_ensemble_artifact(ensemble_a, root, output_root / "baseline")
    artifact_b = write_ensemble_artifact(ensemble_b, root, output_root / "treated")
    comparison = compare_ensembles(ensemble_a, ensemble_b, comparison_id=request.comparison_id)
    artifact_comparison = write_comparison_artifact(comparison, root, output_root / "comparison")
    phase("verifying", "Verifying comparison and both scientific ensemble manifests")
    references = (
        _finish_artifact(
            artifact_a.artifact_directory,
            job_directory,
            role="baseline",
            hash_overrides={"scenario_hash": ensemble_a.scenario_hash},
        ),
        _finish_artifact(
            artifact_b.artifact_directory,
            job_directory,
            role="treated",
            hash_overrides={"scenario_hash": ensemble_b.scenario_hash},
        ),
        _finish_artifact(
            artifact_comparison.artifact_directory,
            job_directory,
            role="comparison",
            hash_overrides={"bundle_hash": comparison.logical_content_hash},
        ),
    )
    phase("finalizing", "Comparison artifacts are ready for application finalization")
    return AdapterResult(references)


def validate_job_request(request: Any, root: Path) -> Any:
    """Run inexpensive scientific-contract validation before queue insertion."""

    validated = parse_request(
        request.model_dump(mode="json") if hasattr(request, "model_dump") else request
    )
    parameters = _parameters(root, getattr(validated, "parameters", None))
    if validated.kind == "scenario_run":
        config = _run_config(validated, parameters)
        observation = (
            _observation(root, validated.observation_config)
            if validated.scenario is not None or validated.observation_config is not None
            else None
        )
        _normalize_scenario(
            validated.scenario,
            seed=validated.seed,
            run_config=config,
            parameters=parameters,
            observation=observation,
        )
    elif validated.kind == "ensemble":
        config = _run_config(validated, parameters)
        observation = _observation(root, validated.observation_config)
        _normalize_scenario(
            validated.scenario,
            seed=validated.replicate_seeds[0],
            run_config=config,
            parameters=parameters,
            observation=observation,
        )
    else:
        observation = _observation(root, validated.observation_config)
        config = default_run_config(
            validated.mode,
            validated.replicate_seeds[0],
            parameters,
            start_date=validated.start_date,
            duration_days=validated.duration_days,
        )
        _normalize_scenario(
            validated.baseline,
            seed=validated.replicate_seeds[0],
            run_config=config,
            parameters=parameters,
            observation=observation,
        )
        _normalize_scenario(
            validated.treated,
            seed=validated.replicate_seeds[0],
            run_config=config,
            parameters=parameters,
            observation=observation,
        )
    return validated


def parse_request(payload: dict[str, Any]) -> Any:
    """Validate a persisted request with the same discriminated schema as HTTP."""

    return TypeAdapter(JobRequest).validate_json(
        json.dumps(payload, ensure_ascii=False, default=str)
    )


def canonical_request_envelope(
    request: Any, submitted_engine_identity: dict[str, Any]
) -> dict[str, Any]:
    """Bind the canonical application request to its submission-time engine identity."""

    return {
        "schema_version": API_SCHEMA_VERSION,
        "request": request.model_dump(mode="json"),
        "submitted_engine_identity": submitted_engine_identity,
    }


def result_manifest_hash(path: Path) -> str:
    return sha256_file(path)
