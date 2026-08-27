"""Command-line interface for the bounded Milestone 0–6 workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from .calibration import run_synthetic_recovery
from .calibration_artifacts import write_calibration_artifact
from .calibration_schemas import CalibrationConfig
from .data_pipeline import build_canonical
from .demo import run_demo
from .ensemble import run_ensemble
from .ensemble_artifacts import write_ensemble_artifact
from .network_artifacts import write_network_artifact
from .network_generator import generate_networks
from .network_schemas import NetworkGenerationConfig
from .observation import load_observation_config, observe_latent_run
from .observation_artifacts import write_observation_artifact
from .outbreak_artifacts import write_outbreak_artifact
from .outbreak_runner import default_run_config, load_parameter_set, run_outbreak
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
from .verification_archive import verify_verification_archive

app = typer.Typer(add_completion=False, no_args_is_help=True)
data_app = typer.Typer(add_completion=False, no_args_is_help=True)
population_app = typer.Typer(add_completion=False, no_args_is_help=True)
structure_app = typer.Typer(add_completion=False, no_args_is_help=True)
network_app = typer.Typer(add_completion=False, no_args_is_help=True)
outbreak_app = typer.Typer(add_completion=False, no_args_is_help=True)
observe_app = typer.Typer(add_completion=False, no_args_is_help=True)
ensemble_app = typer.Typer(add_completion=False, no_args_is_help=True)
calibration_app = typer.Typer(add_completion=False, no_args_is_help=True)
verification_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(data_app, name="data")
app.add_typer(population_app, name="population")
app.add_typer(structure_app, name="structure")
app.add_typer(network_app, name="network")
app.add_typer(outbreak_app, name="outbreak")
app.add_typer(observe_app, name="observe")
app.add_typer(ensemble_app, name="ensemble")
app.add_typer(calibration_app, name="calibrate")
app.add_typer(verification_app, name="verify")


@app.callback()
def main() -> None:
    """Jersey Outbreak Simulator command-line tools."""


@app.command()
def demo(
    seed: Annotated[int, typer.Option(help="Non-negative Starsim random seed.")] = 123,
    output_dir: Annotated[Path, typer.Option(help="Directory for run artifacts.")] = Path(
        "outputs"
    ),
) -> None:
    """Run the official Starsim SIR compatibility/reproducibility spike."""

    run = run_demo(seed=seed, output_dir=output_dir)
    typer.echo(json.dumps(run.summary, ensure_ascii=False, sort_keys=True))


def _repo_root() -> Path:
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate
    return current


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _build_m4_for_m6(root: Path, mode: PopulationMode, seed: int, destination: Path):
    """Build the existing M2/M3/M4.1 stack for an M6 command."""

    m2_output = destination.parent / "populations"
    m3_output = destination.parent / "structures"
    m2_generated = generate_population(root, PopulationGenerationConfig(mode=mode, seed=seed))
    m2_artifact = write_population_artifact(m2_generated, root, m2_output)
    m2_input = load_m2_population_artifact(root, m2_artifact.artifact_directory)
    m3_generated = generate_structure(
        root, StructureGenerationConfig(mode=mode, seed=seed), m2_input
    )
    m3_artifact = write_structure_artifact(m3_generated, root, m3_output, m2_input)
    m3_input = load_m3_structure_artifact(root, m3_artifact.artifact_directory)
    return generate_networks(
        NetworkGenerationConfig(mode=mode, seed=seed), m2_input, m3_input, root
    )


@data_app.command("build")
def data_build(
    output_dir: Annotated[
        Path, typer.Option(help="Directory for deterministic canonical tables and quality reports.")
    ] = Path("data/processed"),
) -> None:
    """Validate the source registry and rebuild Milestone 1 aggregate controls."""

    root = _repo_root()
    destination = output_dir if output_dir.is_absolute() else root / output_dir
    report = build_canonical(root, destination)
    typer.echo(
        json.dumps(
            {
                "build_status": report["build_status"],
                "table_count": len(report["tables"]),
                "warning_count": len(report["warnings"]),
                "quality_report": _display_path(destination / "quality_report.json", root),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


@population_app.command("generate")
def population_generate(
    mode: Annotated[
        PopulationMode, typer.Option(help="Population scale: ci, scaled or full.")
    ] = "ci",
    seed: Annotated[int, typer.Option(help="Non-negative generator seed.")] = 123,
    output_dir: Annotated[
        Path, typer.Option(help="Directory for versioned population artifacts.")
    ] = Path("outputs/populations"),
) -> None:
    """Generate and validate a disease-agnostic synthetic population."""

    root = _repo_root()
    destination = output_dir if output_dir.is_absolute() else root / output_dir
    config = PopulationGenerationConfig(mode=mode, seed=seed)
    generated = generate_population(root, config)
    artifact = write_population_artifact(generated, root, destination)
    typer.echo(
        json.dumps(
            {
                "artifact_id": artifact.manifest.artifact_id,
                "artifact_directory": str(artifact.artifact_directory),
                "diagnostics_status": artifact.manifest.diagnostics_status,
                "logical_content_hash": artifact.manifest.logical_content_hash,
                "mode": artifact.manifest.mode,
                "target_population": artifact.manifest.target_population,
                "households": artifact.manifest.household_count,
                "communal_residents": artifact.manifest.communal_resident_count,
                "runtime_seconds": artifact.manifest.runtime_seconds,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


@structure_app.command("generate")
def structure_generate(
    mode: Annotated[
        PopulationMode, typer.Option(help="Structure scale: ci, scaled or full.")
    ] = "ci",
    seed: Annotated[int, typer.Option(help="Non-negative structure seed.")] = 123,
    population_artifact: Annotated[
        Path | None,
        typer.Option(help="Existing validated Milestone 2 artifact directory."),
    ] = None,
    output_dir: Annotated[
        Path, typer.Option(help="Directory for versioned Milestone 3 artifacts.")
    ] = Path("outputs/structures"),
) -> None:
    """Generate disease-agnostic schools, workplaces and movement structure."""

    root = _repo_root()
    destination = output_dir if output_dir.is_absolute() else root / output_dir
    config = StructureGenerationConfig(mode=mode, seed=seed)
    if population_artifact is None:
        m2_output = destination.parent / "populations"
        m2_config = PopulationGenerationConfig(mode=mode, seed=seed)
        m2_generated = generate_population(root, m2_config)
        m2_artifact = write_population_artifact(m2_generated, root, m2_output)
        m2_path = m2_artifact.artifact_directory
    else:
        m2_path = population_artifact
        if not m2_path.is_absolute():
            m2_path = root / m2_path
    m2_input = load_m2_population_artifact(root, m2_path)
    generated = generate_structure(root, config, m2_input)
    artifact = write_structure_artifact(generated, root, destination, m2_input)
    typer.echo(
        json.dumps(
            {
                "artifact_id": artifact.manifest.artifact_id,
                "artifact_directory": str(artifact.artifact_directory),
                "diagnostics_status": artifact.manifest.diagnostics_status,
                "logical_content_hash": artifact.manifest.logical_content_hash,
                "mode": artifact.manifest.mode,
                "target_population": artifact.manifest.target_population,
                "m2_artifact_id": artifact.manifest.m2_artifact_id,
                "schools": generated.diagnostics["schools"]["school_count"],
                "workplaces": generated.diagnostics["workplaces"]["total"],
                "primary_jobs": generated.diagnostics["employment"]["primary_jobs"],
                "secondary_jobs": generated.diagnostics["employment"]["additional_jobs"],
                "runtime_seconds": artifact.manifest.runtime_seconds,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


@network_app.command("generate")
def network_generate(
    mode: Annotated[PopulationMode, typer.Option(help="Network scale: ci, scaled or full.")] = "ci",
    seed: Annotated[int, typer.Option(help="Non-negative network seed.")] = 123,
    population_artifact: Annotated[
        Path | None,
        typer.Option(help="Existing validated Milestone 2 artifact directory."),
    ] = None,
    structure_artifact: Annotated[
        Path | None,
        typer.Option(help="Existing validated Milestone 3 artifact directory."),
    ] = None,
    output_dir: Annotated[
        Path, typer.Option(help="Directory for versioned Milestone 4 route artifacts.")
    ] = Path("outputs/networks"),
) -> None:
    """Generate disease-agnostic Jersey routes and selected dynamic snapshots."""

    root = _repo_root()
    destination = output_dir if output_dir.is_absolute() else root / output_dir
    config = NetworkGenerationConfig(mode=mode, seed=seed)
    if population_artifact is None and structure_artifact is not None:
        raise typer.BadParameter(
            "--structure-artifact requires --population-artifact so the "
            "M2 hash boundary is explicit"
        )
    if population_artifact is None:
        m2_output = destination.parent / "populations"
        m3_output = destination.parent / "structures"
        m2_generated = generate_population(root, PopulationGenerationConfig(mode=mode, seed=seed))
        m2_artifact = write_population_artifact(m2_generated, root, m2_output)
        m2_path = m2_artifact.artifact_directory
        m2_input = load_m2_population_artifact(root, m2_path)
        m3_generated = generate_structure(
            root,
            StructureGenerationConfig(mode=mode, seed=seed),
            m2_input,
        )
        m3_artifact = write_structure_artifact(m3_generated, root, m3_output, m2_input)
        m3_path = m3_artifact.artifact_directory
    else:
        m2_path = population_artifact
        if not m2_path.is_absolute():
            m2_path = root / m2_path
        m2_input = load_m2_population_artifact(root, m2_path)
        if structure_artifact is None:
            m3_output = destination.parent / "structures"
            m3_generated = generate_structure(
                root,
                StructureGenerationConfig(mode=mode, seed=seed),
                m2_input,
            )
            m3_artifact = write_structure_artifact(m3_generated, root, m3_output, m2_input)
            m3_path = m3_artifact.artifact_directory
        else:
            m3_path = structure_artifact
            if not m3_path.is_absolute():
                m3_path = root / m3_path
    m3_input = load_m3_structure_artifact(root, m3_path)
    generated = generate_networks(config, m2_input, m3_input, root)
    artifact = write_network_artifact(generated, root, destination)
    typer.echo(
        json.dumps(
            {
                "artifact_id": artifact.manifest.artifact_id,
                "artifact_directory": str(artifact.artifact_directory),
                "diagnostics_status": artifact.manifest.diagnostics_status,
                "logical_content_hash": artifact.manifest.logical_content_hash,
                "mode": artifact.manifest.mode,
                "target_population": artifact.manifest.target_population,
                "routes": len(generated.route_specs),
                "baseline_edges": generated.diagnostics["benchmark"]["total_baseline_edges"],
                "runtime_seconds": generated.runtime_seconds,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


@outbreak_app.command("run")
def outbreak_run(
    mode: Annotated[
        PopulationMode, typer.Option(help="Outbreak scale: ci, scaled or full.")
    ] = "ci",
    seed: Annotated[int, typer.Option(help="Non-negative outbreak seed.")] = 123,
    duration_days: Annotated[int, typer.Option(help="Number of daily disease timesteps.")] = 30,
    parameter_set: Annotated[
        Path | None, typer.Option(help="Versioned respiratory parameter YAML.")
    ] = None,
    output_dir: Annotated[
        Path, typer.Option(help="Directory for versioned M5 outbreak artifacts.")
    ] = Path("outputs/outbreaks"),
) -> None:
    """Run the latent generic respiratory SEIRS demonstration."""

    root = _repo_root()
    destination = output_dir if output_dir.is_absolute() else root / output_dir
    parameter_path = parameter_set
    if parameter_path is not None and not parameter_path.is_absolute():
        parameter_path = root / parameter_path
    parameters = load_parameter_set(root, parameter_path)
    config = default_run_config(
        mode,
        seed,
        parameters,
        duration_days=duration_days,
    )
    m2_output = destination.parent / "populations"
    m3_output = destination.parent / "structures"
    m4_output = destination.parent / "networks"
    m2_generated = generate_population(root, PopulationGenerationConfig(mode=mode, seed=seed))
    m2_artifact = write_population_artifact(m2_generated, root, m2_output)
    m2_input = load_m2_population_artifact(root, m2_artifact.artifact_directory)
    m3_generated = generate_structure(
        root, StructureGenerationConfig(mode=mode, seed=seed), m2_input
    )
    m3_artifact = write_structure_artifact(m3_generated, root, m3_output, m2_input)
    m3_input = load_m3_structure_artifact(root, m3_artifact.artifact_directory)
    generated = generate_networks(
        NetworkGenerationConfig(mode=mode, seed=seed), m2_input, m3_input, root
    )
    m4_artifact = write_network_artifact(generated, root, m4_output)
    result = run_outbreak(generated, config, parameters)
    artifact = write_outbreak_artifact(result, root, destination)
    typer.echo(
        json.dumps(
            {
                "artifact_id": artifact.manifest.artifact_id,
                "artifact_directory": str(artifact.artifact_directory),
                "diagnostics_status": artifact.manifest.diagnostics_status,
                "logical_content_hash": artifact.manifest.logical_content_hash,
                "mode": artifact.manifest.mode,
                "target_population": len(generated.agent_ids),
                "m4_artifact_id": m4_artifact.manifest.artifact_id,
                "starsim_version": artifact.manifest.starsim_version,
                "attribution_totals": artifact.manifest.attribution_totals,
                "runtime_seconds": result.runtime_seconds,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


@observe_app.command("run")
def observe_run(
    mode: Annotated[
        PopulationMode, typer.Option(help="Observation scale: ci, scaled or full.")
    ] = "ci",
    seed: Annotated[int, typer.Option(help="Non-negative latent-run seed.")] = 123,
    duration_days: Annotated[int, typer.Option(help="Number of daily disease timesteps.")] = 30,
    parameter_set: Annotated[
        Path | None, typer.Option(help="Versioned respiratory parameter YAML.")
    ] = None,
    observation_config: Annotated[
        Path | None, typer.Option(help="Versioned observation-model YAML.")
    ] = None,
    output_dir: Annotated[
        Path, typer.Option(help="Directory for versioned M6 observation artifacts.")
    ] = Path("outputs/observations"),
) -> None:
    """Run M5 once and apply the standalone M6 observation transformation."""

    root = _repo_root()
    destination = output_dir if output_dir.is_absolute() else root / output_dir
    parameter_path = (
        parameter_set
        if parameter_set is None or parameter_set.is_absolute()
        else root / parameter_set
    )
    observation_path = (
        observation_config
        if observation_config is None or observation_config.is_absolute()
        else root / observation_config
    )
    parameters = load_parameter_set(root, parameter_path)
    observation = load_observation_config(root, observation_path)
    run_config = default_run_config(mode, seed, parameters, duration_days=duration_days)
    generated = _build_m4_for_m6(root, mode, seed, destination)
    latent = run_outbreak(
        generated,
        run_config,
        parameters,
        observation_config=observation,
    )
    observed = observe_latent_run(latent, observation)
    artifact = write_observation_artifact(observed, root, destination)
    typer.echo(
        json.dumps(
            {
                "artifact_id": artifact.manifest.artifact_id,
                "artifact_directory": str(artifact.artifact_directory),
                "diagnostics_status": artifact.manifest.diagnostics_status,
                "latent_run_logical_content_hash": (
                    artifact.manifest.latent_run_logical_content_hash
                ),
                "observation_config_id": artifact.manifest.observation_config_id,
                "runtime_seconds": observed.runtime_seconds,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def _parse_seeds(value: str) -> tuple[int, ...]:
    try:
        seeds = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    except ValueError as exc:
        raise typer.BadParameter("--seeds must be a comma-separated list of integers") from exc
    if not seeds:
        raise typer.BadParameter("--seeds must contain at least one integer")
    return seeds


@ensemble_app.command("run")
def ensemble_run(
    mode: Annotated[
        PopulationMode, typer.Option(help="Ensemble scale: ci, scaled or full.")
    ] = "ci",
    seeds: Annotated[
        str, typer.Option(help="Explicit comma-separated unique replicate seeds.")
    ] = "101,102,103",
    duration_days: Annotated[int, typer.Option(help="Number of daily disease timesteps.")] = 30,
    workers: Annotated[int, typer.Option(help="Bounded process workers; 1 is sequential.")] = 1,
    parameter_set: Annotated[
        Path | None, typer.Option(help="Versioned respiratory parameter YAML.")
    ] = None,
    observation_config: Annotated[
        Path | None, typer.Option(help="Versioned observation-model YAML.")
    ] = None,
    ensemble_id: Annotated[
        str, typer.Option(help="Stable identifier for this ensemble.")
    ] = "m6-demo",
    output_dir: Annotated[
        Path, typer.Option(help="Directory for versioned M6 ensemble artifacts.")
    ] = Path("outputs/ensembles"),
) -> None:
    """Run explicit M5 seeds and summarize latent and observed trajectories."""

    root = _repo_root()
    destination = output_dir if output_dir.is_absolute() else root / output_dir
    parameter_path = (
        parameter_set
        if parameter_set is None or parameter_set.is_absolute()
        else root / parameter_set
    )
    observation_path = (
        observation_config
        if observation_config is None or observation_config.is_absolute()
        else root / observation_config
    )
    parameters = load_parameter_set(root, parameter_path)
    replicate_seeds = _parse_seeds(seeds)
    base_config = default_run_config(
        mode, replicate_seeds[0], parameters, duration_days=duration_days
    )
    generated = _build_m4_for_m6(root, mode, replicate_seeds[0], destination)
    result = run_ensemble(
        root,
        generated,
        parameters,
        base_config,
        load_observation_config(root, observation_path),
        replicate_seeds,
        ensemble_id=ensemble_id,
        workers=workers,
    )
    artifact = write_ensemble_artifact(result, root, destination)
    typer.echo(
        json.dumps(
            {
                "artifact_id": artifact.manifest.artifact_id,
                "artifact_directory": str(artifact.artifact_directory),
                "diagnostics_status": artifact.manifest.diagnostics_status,
                "status": result.diagnostics["status"],
                "replicate_count": len(result.replicate_records),
                "successful_replicates": result.diagnostics["successful_replicates"],
                "logical_content_hash": result.logical_content_hash,
                "runtime_seconds": result.runtime_seconds,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


@calibration_app.command("synthetic")
def calibration_synthetic(
    mode: Annotated[
        PopulationMode, typer.Option(help="Calibration harness scale: ci, scaled or full.")
    ] = "ci",
    seed: Annotated[int, typer.Option(help="Seed for the target synthetic latent run.")] = 123,
    duration_days: Annotated[int, typer.Option(help="Number of daily disease timesteps.")] = 30,
    parameter_set: Annotated[
        Path | None, typer.Option(help="Versioned respiratory parameter YAML.")
    ] = None,
    observation_config: Annotated[
        Path | None, typer.Option(help="Versioned observation-model YAML.")
    ] = None,
    output_dir: Annotated[
        Path, typer.Option(help="Directory for versioned M6 calibration artifacts.")
    ] = Path("outputs/calibration"),
) -> None:
    """Recover a hidden observation parameter from synthetic data only."""

    root = _repo_root()
    destination = output_dir if output_dir.is_absolute() else root / output_dir
    parameter_path = (
        parameter_set
        if parameter_set is None or parameter_set.is_absolute()
        else root / parameter_set
    )
    observation_path = (
        observation_config
        if observation_config is None or observation_config.is_absolute()
        else root / observation_config
    )
    parameters = load_parameter_set(root, parameter_path)
    base_config = default_run_config(mode, seed, parameters, duration_days=duration_days)
    generated = _build_m4_for_m6(root, mode, seed, destination)
    result = run_synthetic_recovery(
        root,
        generated,
        parameters,
        base_config,
        load_observation_config(root, observation_path),
    )
    artifact = write_calibration_artifact(result, root, destination)
    typer.echo(
        json.dumps(
            {
                "artifact_id": artifact.manifest.artifact_id,
                "artifact_directory": str(artifact.artifact_directory),
                "status": result.diagnostics["status"],
                "recovered_parameter": result.best_parameters,
                "synthetic_truth": result.diagnostics["synthetic_truth"],
                "heldout": result.diagnostics["heldout"],
                "logical_content_hash": result.logical_content_hash,
                "runtime_seconds": result.runtime_seconds,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


@calibration_app.command("beta")
def calibration_beta(
    mode: Annotated[
        PopulationMode, typer.Option(help="Calibration harness scale: ci, scaled or full.")
    ] = "ci",
    seed: Annotated[int, typer.Option(help="Seed for the base synthetic network.")] = 123,
    duration_days: Annotated[int, typer.Option(help="Number of daily disease timesteps.")] = 8,
    parameter_set: Annotated[
        Path | None, typer.Option(help="Versioned respiratory parameter YAML.")
    ] = None,
    observation_config: Annotated[
        Path | None, typer.Option(help="Versioned observation-model YAML.")
    ] = None,
    output_dir: Annotated[
        Path, typer.Option(help="Directory for versioned C3 calibration artifacts.")
    ] = Path("outputs/calibration"),
) -> None:
    """Recover generic transmission beta on synthetic train and held-out runs."""

    root = _repo_root()
    destination = output_dir if output_dir.is_absolute() else root / output_dir
    parameter_path = (
        parameter_set
        if parameter_set is None or parameter_set.is_absolute()
        else root / parameter_set
    )
    observation_path = (
        observation_config
        if observation_config is None or observation_config.is_absolute()
        else root / observation_config
    )
    parameters = load_parameter_set(root, parameter_path)
    base_config = default_run_config(mode, seed, parameters, duration_days=duration_days)
    generated = _build_m4_for_m6(root, mode, seed, destination)
    config = CalibrationConfig(
        study_id="c3-beta-recovery",
        hidden_parameter="transmission_beta",
        trial_count=5,
        synthetic_truth_beta=base_config.beta,
    )
    result = run_synthetic_recovery(
        root,
        generated,
        parameters,
        base_config,
        load_observation_config(root, observation_path),
        calibration_config=config,
    )
    artifact = write_calibration_artifact(result, root, destination)
    typer.echo(
        json.dumps(
            {
                "artifact_id": artifact.manifest.artifact_id,
                "status": result.diagnostics["status"],
                "recovered_parameter": result.best_parameters,
                "synthetic_truth": result.diagnostics["synthetic_truth"],
                "heldout": result.diagnostics["heldout"],
                "logical_content_hash": result.logical_content_hash,
                "runtime_seconds": result.runtime_seconds,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


@verification_app.command("archive-check")
def verification_archive_check(
    manifest: Annotated[Path, typer.Argument(help="Verification manifest JSON path.")],
) -> None:
    """Verify an immutable verification archive's retained files."""

    result = verify_verification_archive(manifest)
    typer.echo(json.dumps(result, ensure_ascii=False, sort_keys=True))
