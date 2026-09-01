"""Command-line interface for the bounded Milestone 0–6 workflows."""

from __future__ import annotations

import ipaddress
import json
from datetime import date
from pathlib import Path
from typing import Annotated

import typer

from .bundle_selftest import run_bundle_selftest
from .calibration import run_synthetic_recovery
from .calibration_artifacts import write_calibration_artifact
from .calibration_schemas import CalibrationConfig
from .data_pipeline import build_canonical
from .demo import run_demo
from .ensemble import run_ensemble
from .ensemble_artifacts import write_ensemble_artifact
from .intervention_analysis import compare_intervention_runs
from .intervention_artifacts import (
    write_intervention_artifact,
    write_intervention_comparison_artifact,
)
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
from .scenario import load_scenario_config
from .travel import (
    compare_travel_runs,
    load_travel_config,
    run_travel_ensemble,
    run_travel_outbreak,
)
from .travel_artifacts import write_travel_artifact
from .verification_archive import verify_verification_archive

app = typer.Typer(add_completion=False, no_args_is_help=True)
data_app = typer.Typer(add_completion=False, no_args_is_help=True)
population_app = typer.Typer(add_completion=False, no_args_is_help=True)
structure_app = typer.Typer(add_completion=False, no_args_is_help=True)
network_app = typer.Typer(add_completion=False, no_args_is_help=True)
outbreak_app = typer.Typer(add_completion=False, no_args_is_help=True)
observe_app = typer.Typer(add_completion=False, no_args_is_help=True)
ensemble_app = typer.Typer(add_completion=False, no_args_is_help=True)
scenario_app = typer.Typer(add_completion=False, no_args_is_help=True)
travel_app = typer.Typer(add_completion=False, no_args_is_help=True)
intervention_app = typer.Typer(add_completion=False, no_args_is_help=True)
calibration_app = typer.Typer(add_completion=False, no_args_is_help=True)
verification_app = typer.Typer(add_completion=False, no_args_is_help=True)
api_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(data_app, name="data")
app.add_typer(population_app, name="population")
app.add_typer(structure_app, name="structure")
app.add_typer(network_app, name="network")
app.add_typer(outbreak_app, name="outbreak")
app.add_typer(observe_app, name="observe")
app.add_typer(ensemble_app, name="ensemble")
app.add_typer(scenario_app, name="scenario")
app.add_typer(travel_app, name="travel")
app.add_typer(intervention_app, name="intervention")
app.add_typer(calibration_app, name="calibrate")
app.add_typer(verification_app, name="verify")
app.add_typer(api_app, name="api")


@app.callback()
def main() -> None:
    """Jersey Outbreak Simulator command-line tools."""


@api_app.command("serve")
def api_serve(
    port: Annotated[int, typer.Option(help="Loopback TCP port.")] = 8000,
    host: Annotated[
        str, typer.Option(help="Loopback host only; LAN binding is refused.")
    ] = "127.0.0.1",
    state_dir: Annotated[
        Path | None, typer.Option(help="Persistent application state directory (or JOS_STATE_DIR).")
    ] = None,
    max_concurrent_jobs: Annotated[
        int, typer.Option(help="Maximum concurrent API scientific jobs; default is one.")
    ] = 1,
) -> None:
    """Serve the local, versioned M9 API on a loopback interface."""

    try:
        is_loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        is_loopback = host.lower() == "localhost"
    if not is_loopback:
        raise typer.BadParameter("M9 API binding must be loopback (127.0.0.1, ::1, or localhost)")
    if not 1 <= port <= 65535:
        raise typer.BadParameter("port must be between 1 and 65535")
    if max_concurrent_jobs < 1:
        raise typer.BadParameter("max-concurrent-jobs must be at least one")
    import uvicorn

    from .api import create_app

    uvicorn.run(
        create_app(
            state_dir=state_dir,
            project_root=_repo_root(),
            max_concurrent_jobs=max_concurrent_jobs,
        ),
        host=host,
        port=port,
    )


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


def _build_m4_for_m6(
    root: Path,
    mode: PopulationMode,
    seed: int,
    destination: Path,
    *,
    isolate_parents: bool = False,
):
    """Build the existing M2/M3/M4.1 stack for an M6 command."""

    parent_output = destination / "parents" if isolate_parents else destination.parent
    m2_output = parent_output / "populations"
    m3_output = parent_output / "structures"
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
    duration_days: Annotated[int, typer.Option(help="Number of dated output points.")] = 30,
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
    duration_days: Annotated[int, typer.Option(help="Number of dated output points.")] = 30,
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
    duration_days: Annotated[int, typer.Option(help="Number of dated output points.")] = 30,
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


def _run_m7_scenario(
    *,
    mode: PopulationMode,
    seed: int,
    duration_days: int,
    scenario_path: Path | None,
    parameter_path: Path | None,
    observation_path: Path | None,
    output_dir: Path,
) -> dict[str, object]:
    root = _repo_root()
    destination = output_dir if output_dir.is_absolute() else root / output_dir
    parameter_path = (
        parameter_path
        if parameter_path is None or parameter_path.is_absolute()
        else root / parameter_path
    )
    observation_path = (
        observation_path
        if observation_path is None or observation_path.is_absolute()
        else root / observation_path
    )
    scenario_path = (
        scenario_path
        if scenario_path is None or scenario_path.is_absolute()
        else root / scenario_path
    )
    parameters = load_parameter_set(root, parameter_path)
    observation = load_observation_config(root, observation_path)
    scenario = load_scenario_config(root, scenario_path)
    if scenario.seed is not None and scenario.seed != seed:
        raise typer.BadParameter("scenario seed must match --seed")
    if scenario.start_date is not None and scenario.start_date != date(2025, 1, 6):
        # The current M4 demo build has one explicit reference start date;
        # run-level date overrides remain a library contract for later work.
        raise typer.BadParameter("M7 CLI currently requires scenario start_date 2025-01-06")
    run_config = default_run_config(mode, seed, parameters, duration_days=duration_days)
    generated = _build_m4_for_m6(root, mode, seed, destination)
    result = run_outbreak(
        generated,
        run_config,
        parameters,
        observation_config=observation,
        scenario=scenario.model_copy(
            update={
                "seed": seed,
                "start_date": run_config.start_date,
                "duration_days": duration_days,
                "disease_config_id": parameters.parameter_set_id,
                "observation_config_id": observation.observation_config_id,
            }
        ),
    )
    if hasattr(result, "travel_config"):
        travel_artifact = write_travel_artifact(result, root, destination)  # type: ignore[arg-type]
        return {
            "artifact_id": travel_artifact.manifest.artifact_id,
            "artifact_directory": str(travel_artifact.artifact_directory),
            "diagnostics_status": travel_artifact.manifest.diagnostics_status,
            "scenario_id": scenario.scenario_id,
            "scenario_hash": result.scenario_hash,
            "logical_content_hash": result.latent_outcome_hash,
            "runtime_seconds": result.runtime_seconds,
            "travel_controls": "M8",
        }
    m7_artifact = write_intervention_artifact(result, root, destination)
    return {
        "artifact_id": m7_artifact.manifest.artifact_id,
        "artifact_directory": str(m7_artifact.artifact_directory),
        "diagnostics_status": m7_artifact.manifest.diagnostics_status,
        "scenario_id": scenario.scenario_id,
        "scenario_hash": result.scenario_hash,
        "logical_content_hash": result.logical_content_hash,
        "runtime_seconds": result.runtime_seconds,
        "travel_controls": "DEFERRED TO M8",
    }


def _run_m8_scenario(
    *,
    mode: PopulationMode,
    seed: int,
    duration_days: int,
    travel_path: Path | None,
    scenario_path: Path | None,
    parameter_path: Path | None,
    observation_path: Path | None,
    output_dir: Path,
) -> dict[str, object]:
    """Build the canonical resident parent and execute one M8 run."""

    root = _repo_root()
    destination = output_dir if output_dir.is_absolute() else root / output_dir
    parameter_path = (
        parameter_path
        if parameter_path is None or parameter_path.is_absolute()
        else root / parameter_path
    )
    observation_path = (
        observation_path
        if observation_path is None or observation_path.is_absolute()
        else root / observation_path
    )
    scenario_path = (
        scenario_path
        if scenario_path is None or scenario_path.is_absolute()
        else root / scenario_path
    )
    travel_path = (
        travel_path if travel_path is None or travel_path.is_absolute() else root / travel_path
    )
    parameters = load_parameter_set(root, parameter_path)
    observation = load_observation_config(root, observation_path)
    scenario = load_scenario_config(root, scenario_path) if scenario_path is not None else None
    travel_config = (
        scenario.travel
        if scenario is not None and scenario.travel is not None
        else load_travel_config(root, travel_path)
    )
    run_config = default_run_config(mode, seed, parameters, duration_days=duration_days)
    generated = _build_m4_for_m6(root, mode, seed, destination, isolate_parents=True)
    result = run_travel_outbreak(
        generated,
        run_config,
        parameters,
        travel_config,
        observation_config=observation,
        scenario=scenario,
    )
    artifact = write_travel_artifact(result, root, destination)
    return {
        "artifact_id": artifact.manifest.artifact_id,
        "artifact_directory": str(artifact.artifact_directory),
        "diagnostics_status": artifact.manifest.diagnostics_status,
        "scenario_hash": result.scenario_hash,
        "travel_config_hash": result.travel_config_hash,
        "visitor_episode_hash": result.visitor_episode_hash,
        "temporary_network_hash": result.temporary_network_hash,
        "seasonality_hash": result.seasonality_hash,
        "latent_outcome_hash": result.latent_outcome_hash,
        "visitor_count": len(result.travel_plan.visitor_records),
        "visitor_capacity": result.travel_plan.visitor_capacity,
        "runtime_seconds": result.runtime_seconds,
    }


@travel_app.command("run")
def travel_run(
    mode: Annotated[
        PopulationMode, typer.Option(help="Travel run scale: ci, scaled or full.")
    ] = "ci",
    seed: Annotated[int, typer.Option(help="Non-negative travel seed.")] = 123,
    duration_days: Annotated[int, typer.Option(help="Number of dated output points.")] = 30,
    travel_config: Annotated[Path | None, typer.Option(help="Versioned M8 travel YAML.")] = None,
    scenario_config: Annotated[
        Path | None, typer.Option(help="Optional M7+M8 scenario YAML.")
    ] = None,
    parameter_set: Annotated[
        Path | None, typer.Option(help="Versioned respiratory parameter YAML.")
    ] = None,
    observation_config: Annotated[
        Path | None, typer.Option(help="Versioned observation-model YAML.")
    ] = None,
    output_dir: Annotated[
        Path, typer.Option(help="Directory for versioned M8 travel artifacts.")
    ] = Path("outputs/travel"),
) -> None:
    """Run an explicit synthetic travel/visitor experiment."""

    typer.echo(
        json.dumps(
            _run_m8_scenario(
                mode=mode,
                seed=seed,
                duration_days=duration_days,
                travel_path=travel_config,
                scenario_path=scenario_config,
                parameter_path=parameter_set,
                observation_path=observation_config,
                output_dir=output_dir,
            ),
            ensure_ascii=False,
            sort_keys=True,
        )
    )


@travel_app.command("compare")
def travel_compare(
    mode: Annotated[
        PopulationMode, typer.Option(help="Comparison scale: ci, scaled or full.")
    ] = "ci",
    seed: Annotated[int, typer.Option(help="Matched comparison seed.")] = 123,
    duration_days: Annotated[int, typer.Option(help="Number of dated output points.")] = 30,
    baseline_config: Annotated[Path, typer.Option(help="Baseline M8 travel YAML.")] = Path(
        "configs/travel/m8_explicit_travel.yaml"
    ),
    treated_config: Annotated[Path, typer.Option(help="Treated M8 travel YAML.")] = Path(
        "configs/travel/m8_reduced_arrivals.yaml"
    ),
    output_dir: Annotated[Path, typer.Option(help="Directory for comparison outputs.")] = Path(
        "outputs/travel_comparisons"
    ),
) -> None:
    """Run a matched-seed travel comparison and emit direction-aware deltas."""

    root = _repo_root()
    destination = output_dir if output_dir.is_absolute() else root / output_dir
    baseline_path = baseline_config if baseline_config.is_absolute() else root / baseline_config
    treated_path = treated_config if treated_config.is_absolute() else root / treated_config
    parameters = load_parameter_set(root)
    base_config = default_run_config(mode, seed, parameters, duration_days=duration_days)
    generated = _build_m4_for_m6(root, mode, seed, destination, isolate_parents=True)
    observation = load_observation_config(root)
    baseline = run_travel_outbreak(
        generated,
        base_config,
        parameters,
        load_travel_config(root, baseline_path),
        observation_config=observation,
    )
    treated = run_travel_outbreak(
        generated,
        base_config,
        parameters,
        load_travel_config(root, treated_path),
        observation_config=observation,
    )
    comparison = compare_travel_runs(baseline, treated, comparison_id="m8-cli-comparison")
    destination.mkdir(parents=True, exist_ok=True)
    comparison_path = destination / "m8-cli-comparison.json"
    comparison_path.write_text(
        json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    typer.echo(json.dumps(comparison, ensure_ascii=False, sort_keys=True))


@travel_app.command("ensemble")
def travel_ensemble(
    mode: Annotated[
        PopulationMode, typer.Option(help="Ensemble scale: ci, scaled or full.")
    ] = "ci",
    seeds: Annotated[str, typer.Option(help="Comma-separated replicate seeds.")] = "101,102,103",
    duration_days: Annotated[int, typer.Option(help="Number of dated output points.")] = 30,
    travel_config: Annotated[Path, typer.Option(help="Versioned M8 travel YAML.")] = Path(
        "configs/travel/m8_explicit_travel.yaml"
    ),
    output_dir: Annotated[Path, typer.Option(help="Directory for ensemble outputs.")] = Path(
        "outputs/travel_ensembles"
    ),
) -> None:
    """Run a small multi-seed M8 ensemble with state/event semantics retained."""

    root = _repo_root()
    destination = output_dir if output_dir.is_absolute() else root / output_dir
    replicate_seeds = _parse_seeds(seeds)
    parameters = load_parameter_set(root)
    base_config = default_run_config(
        mode, replicate_seeds[0], parameters, duration_days=duration_days
    )
    generated = _build_m4_for_m6(root, mode, replicate_seeds[0], destination, isolate_parents=True)
    result = run_travel_ensemble(
        generated,
        parameters,
        base_config,
        load_travel_config(
            root, travel_config if travel_config.is_absolute() else root / travel_config
        ),
        replicate_seeds,
    )
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "m8-ensemble.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    typer.echo(json.dumps(result, ensure_ascii=False, sort_keys=True))


@scenario_app.command("run")
def scenario_run(
    mode: Annotated[
        PopulationMode, typer.Option(help="Scenario scale: ci, scaled or full.")
    ] = "ci",
    seed: Annotated[int, typer.Option(help="Non-negative scenario seed.")] = 123,
    duration_days: Annotated[int, typer.Option(help="Number of dated output points.")] = 30,
    scenario_config: Annotated[
        Path | None, typer.Option(help="Versioned M7 scenario YAML.")
    ] = None,
    parameter_set: Annotated[
        Path | None, typer.Option(help="Versioned respiratory parameter YAML.")
    ] = None,
    observation_config: Annotated[
        Path | None, typer.Option(help="Versioned observation-model YAML.")
    ] = None,
    output_dir: Annotated[Path, typer.Option(help="Directory for versioned M7 artifacts.")] = Path(
        "outputs/interventions"
    ),
) -> None:
    """Run one synthetic intervention scenario through the prospective M7 layer."""

    typer.echo(
        json.dumps(
            _run_m7_scenario(
                mode=mode,
                seed=seed,
                duration_days=duration_days,
                scenario_path=scenario_config,
                parameter_path=parameter_set,
                observation_path=observation_config,
                output_dir=output_dir,
            ),
            ensure_ascii=False,
            sort_keys=True,
        )
    )


@intervention_app.command("run")
def intervention_run(
    mode: Annotated[
        PopulationMode, typer.Option(help="Intervention scale: ci, scaled or full.")
    ] = "ci",
    seed: Annotated[int, typer.Option(help="Non-negative scenario seed.")] = 123,
    duration_days: Annotated[int, typer.Option(help="Number of dated output points.")] = 30,
    scenario_config: Annotated[
        Path | None, typer.Option(help="Versioned M7 scenario YAML.")
    ] = None,
    parameter_set: Annotated[
        Path | None, typer.Option(help="Versioned respiratory parameter YAML.")
    ] = None,
    observation_config: Annotated[
        Path | None, typer.Option(help="Versioned observation-model YAML.")
    ] = None,
    output_dir: Annotated[Path, typer.Option(help="Directory for versioned M7 artifacts.")] = Path(
        "outputs/interventions"
    ),
) -> None:
    """Alias for the M7 scenario runner."""

    typer.echo(
        json.dumps(
            _run_m7_scenario(
                mode=mode,
                seed=seed,
                duration_days=duration_days,
                scenario_path=scenario_config,
                parameter_path=parameter_set,
                observation_path=observation_config,
                output_dir=output_dir,
            ),
            ensure_ascii=False,
            sort_keys=True,
        )
    )


@intervention_app.command("compare")
def intervention_compare(
    mode: Annotated[
        PopulationMode, typer.Option(help="Comparison scale: ci, scaled or full.")
    ] = "ci",
    seed: Annotated[int, typer.Option(help="Matched seed for baseline and scenario.")] = 123,
    duration_days: Annotated[int, typer.Option(help="Number of dated output points.")] = 30,
    scenario_config: Annotated[
        Path, typer.Option(help="M7 scenario YAML to compare with baseline.")
    ] = Path("configs/scenarios/m7_school_closure.yaml"),
    parameter_set: Annotated[
        Path | None, typer.Option(help="Versioned respiratory parameter YAML.")
    ] = None,
    observation_config: Annotated[
        Path | None, typer.Option(help="Versioned observation-model YAML.")
    ] = None,
    output_dir: Annotated[Path, typer.Option(help="Directory for comparison artifacts.")] = Path(
        "outputs/intervention_comparisons"
    ),
) -> None:
    """Run a matched-seed baseline/scenario comparison and route-shift analysis."""

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
    scenario_path = scenario_config if scenario_config.is_absolute() else root / scenario_config
    parameters = load_parameter_set(root, parameter_path)
    observation = load_observation_config(root, observation_path)
    scenario = load_scenario_config(root, scenario_path).model_copy(
        update={"seed": seed, "duration_days": duration_days}
    )
    run_config = default_run_config(mode, seed, parameters, duration_days=duration_days)
    generated = _build_m4_for_m6(root, mode, seed, destination)
    baseline = run_outbreak(generated, run_config, parameters, observation_config=observation)
    treated = run_outbreak(
        generated,
        run_config,
        parameters,
        observation_config=observation,
        scenario=scenario,
    )
    comparison = compare_intervention_runs(baseline, treated, comparison_id=scenario.scenario_id)
    artifact_directory = write_intervention_comparison_artifact(comparison, root, destination)
    typer.echo(
        json.dumps(
            {
                "artifact_directory": str(artifact_directory),
                "comparison_id": comparison.comparison_id,
                "scenario_hash": treated.scenario_hash,
                "paired_seed": seed,
                "cumulative_difference": comparison.scenario_comparison[0]["absolute_difference"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


@intervention_app.command("ensemble")
def intervention_ensemble(
    mode: Annotated[
        PopulationMode, typer.Option(help="Ensemble scale: ci, scaled or full.")
    ] = "ci",
    seeds: Annotated[
        str, typer.Option(help="Explicit comma-separated unique replicate seeds.")
    ] = "101,102,103",
    duration_days: Annotated[int, typer.Option(help="Number of dated output points.")] = 30,
    workers: Annotated[int, typer.Option(help="Bounded process workers; 1 is sequential.")] = 1,
    scenario_config: Annotated[Path, typer.Option(help="Versioned M7 scenario YAML.")] = Path(
        "configs/scenarios/m7_school_closure.yaml"
    ),
    ensemble_id: Annotated[str, typer.Option(help="Stable ensemble identifier.")] = "m7-demo",
    parameter_set: Annotated[
        Path | None, typer.Option(help="Versioned respiratory parameter YAML.")
    ] = None,
    observation_config: Annotated[
        Path | None, typer.Option(help="Versioned observation-model YAML.")
    ] = None,
    output_dir: Annotated[Path, typer.Option(help="Directory for ensemble artifacts.")] = Path(
        "outputs/ensembles"
    ),
) -> None:
    """Run a bounded matched-seed intervention ensemble."""

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
    scenario_path = scenario_config if scenario_config.is_absolute() else root / scenario_config
    parameters = load_parameter_set(root, parameter_path)
    observation = load_observation_config(root, observation_path)
    replicate_seeds = _parse_seeds(seeds)
    scenario = load_scenario_config(root, scenario_path)
    base_config = default_run_config(
        mode, replicate_seeds[0], parameters, duration_days=duration_days
    )
    generated = _build_m4_for_m6(root, mode, replicate_seeds[0], destination)
    result = run_ensemble(
        root,
        generated,
        parameters,
        base_config,
        observation,
        replicate_seeds,
        ensemble_id=ensemble_id,
        workers=workers,
        scenario=scenario,
    )
    artifact = write_ensemble_artifact(result, root, destination)
    typer.echo(
        json.dumps(
            {
                "artifact_id": artifact.manifest.artifact_id,
                "artifact_directory": str(artifact.artifact_directory),
                "status": result.diagnostics["status"],
                "scenario_hash": result.scenario_hash,
                "successful_replicates": result.diagnostics["successful_replicates"],
                "logical_content_hash": result.logical_content_hash,
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
    duration_days: Annotated[int, typer.Option(help="Number of dated output points.")] = 30,
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
    duration_days: Annotated[int, typer.Option(help="Number of dated output points.")] = 8,
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


@verification_app.command("bundle-selftest")
def verification_bundle_selftest(
    artifact_dir: Annotated[Path, typer.Argument(help="Scientific artifact directory.")],
    transcript_dir: Annotated[
        Path | None, typer.Option(help="Directory for the bundle-level transcript.")
    ] = None,
    keep_copy: Annotated[
        bool, typer.Option(help="Retain the temporary relocated copy for inspection.")
    ] = False,
) -> None:
    """Verify a copied scientific artifact and write its relocation transcript."""

    try:
        result = run_bundle_selftest(
            artifact_dir,
            transcript_dir=transcript_dir,
            keep_copy=keep_copy,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"BUNDLE_SELFTEST {result.status} {result.transcript_path}")
    if result.status != "passed":
        raise typer.Exit(code=1)
