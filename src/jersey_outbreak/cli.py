"""Command-line interface for the bounded Milestone 0 and 1 workflows."""

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

app = typer.Typer(add_completion=False, no_args_is_help=True)
data_app = typer.Typer(add_completion=False, no_args_is_help=True)
population_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(data_app, name="data")
app.add_typer(population_app, name="population")


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
