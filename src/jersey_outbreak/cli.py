"""Command-line interface for the bounded Milestone 0–3 workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from .data_pipeline import build_canonical
from .demo import run_demo
from .population_artifacts import write_population_artifact
from .population_generator import generate_population
from .population_schemas import PopulationGenerationConfig, PopulationMode
from .population_structure_artifacts import load_m2_population_artifact, write_structure_artifact
from .population_structure_generator import generate_structure
from .population_structure_schemas import StructureGenerationConfig

app = typer.Typer(add_completion=False, no_args_is_help=True)
data_app = typer.Typer(add_completion=False, no_args_is_help=True)
population_app = typer.Typer(add_completion=False, no_args_is_help=True)
structure_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(data_app, name="data")
app.add_typer(population_app, name="population")
app.add_typer(structure_app, name="structure")


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
