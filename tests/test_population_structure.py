import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from jersey_outbreak.cli import app
from jersey_outbreak.data_pipeline import DataBuildError
from jersey_outbreak.population_artifacts import write_population_artifact
from jersey_outbreak.population_generator import generate_population
from jersey_outbreak.population_schemas import PopulationGenerationConfig
from jersey_outbreak.population_structure_artifacts import (
    load_m2_population_artifact,
    write_structure_artifact,
)
from jersey_outbreak.population_structure_generator import generate_structure
from jersey_outbreak.population_structure_schemas import (
    ResidentStructureRecord,
    StructureGenerationConfig,
)

ROOT = Path(__file__).resolve().parents[1]


def _ci_population_artifact(tmp_path: Path):
    generated = generate_population(ROOT, PopulationGenerationConfig(mode="ci", seed=123))
    return write_population_artifact(generated, ROOT, tmp_path / "populations")


def test_structure_config_enforces_milestone_3_scale_boundaries() -> None:
    assert StructureGenerationConfig(mode="ci", seed=123).resolved_target_population == 3_000
    assert StructureGenerationConfig(mode="scaled", seed=123).resolved_target_population == 15_000
    assert StructureGenerationConfig(mode="full", seed=123).resolved_target_population == 104_540

    with pytest.raises(ValidationError):
        StructureGenerationConfig(mode="ci", seed=123, target_population=1_999)
    with pytest.raises(ValidationError):
        StructureGenerationConfig(mode="scaled", seed=123, target_population=25_001)
    with pytest.raises(ValidationError):
        StructureGenerationConfig(mode="full", seed=123, target_population=15_000)


def test_nullable_structure_fields_do_not_create_false_duplicate_workplaces() -> None:
    base = {
        "agent_id": "agent-1",
        "age": 40,
        "sex": "female",
        "home_parish": "St Helier",
        "economic_status": "unemployed",
        "work_from_home_days_per_week": 0,
        "primary_work_days_per_week": 0,
    }
    assert ResidentStructureRecord.model_validate(base).economic_status == "unemployed"

    with pytest.raises(ValidationError, match="secondary workplace"):
        ResidentStructureRecord.model_validate(
            {
                **base,
                "economic_status": "employed",
                "employment_sector": "Construction and quarrying",
                "primary_workplace_id": "workplace-1",
                "secondary_workplace_id": "workplace-1",
                "work_parish": "St Helier",
                "commute_mode": "walk",
                "primary_work_days_per_week": 4,
            }
        )


def test_ci_structure_is_deterministic_and_preserves_references(tmp_path: Path) -> None:
    population_artifact = _ci_population_artifact(tmp_path)
    m2_input = load_m2_population_artifact(ROOT, population_artifact.artifact_directory)
    config = StructureGenerationConfig(mode="ci", seed=123)
    first = generate_structure(ROOT, config, m2_input)
    second = generate_structure(ROOT, config, m2_input)

    assert first.logical_content_hash == second.logical_content_hash
    assert first.diagnostics["status"] == "passed"
    assert len(first.resident_structure) == 3_000
    assert first.diagnostics["employment"]["unique_workers"] == 1_666
    assert first.diagnostics["employment"]["additional_jobs"] == 117
    assert all(
        row["secondary_workplace_id"] is None
        or row["secondary_workplace_id"] != row["primary_workplace_id"]
        for row in first.resident_structure
    )
    assert all(row["age"] >= 4 for row in first.school_assignments)


def test_structure_artifact_writes_manifest_tables_and_provenance(tmp_path: Path) -> None:
    population_artifact = _ci_population_artifact(tmp_path)
    m2_input = load_m2_population_artifact(ROOT, population_artifact.artifact_directory)
    generated = generate_structure(ROOT, StructureGenerationConfig(mode="ci", seed=123), m2_input)
    artifact = write_structure_artifact(generated, ROOT, tmp_path / "structures", m2_input)

    manifest = json.loads((artifact.artifact_directory / "manifest.json").read_text())
    assert manifest["diagnostics_status"] == "passed"
    assert manifest["m2_artifact_id"] == population_artifact.manifest.artifact_id
    assert manifest["logical_content_hash"] == generated.logical_content_hash
    for filename in (
        "resident_structure.parquet",
        "schools.parquet",
        "classes.parquet",
        "school_assignments.parquet",
        "workplaces.parquet",
        "workplace_teams.parquet",
        "job_assignments.parquet",
        "diagnostics.json",
        "diagnostics.md",
        "benchmark.json",
    ):
        assert (artifact.artifact_directory / filename).exists()


def test_structure_cli_emits_machine_readable_summary(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "structure",
            "generate",
            "--mode",
            "ci",
            "--seed",
            "123",
            "--output-dir",
            str(tmp_path / "structures"),
        ],
    )
    assert result.exit_code == 0, result.stdout
    summary = json.loads(result.stdout)
    assert summary["diagnostics_status"] == "passed"
    manifest = json.loads((Path(summary["artifact_directory"]) / "manifest.json").read_text())
    assert summary["logical_content_hash"] == manifest["logical_content_hash"]
    assert summary["target_population"] == 3_000


def test_structure_rejects_mismatched_population_mode(tmp_path: Path) -> None:
    population_artifact = _ci_population_artifact(tmp_path)
    m2_input = load_m2_population_artifact(ROOT, population_artifact.artifact_directory)
    with pytest.raises(DataBuildError, match="mode"):
        generate_structure(ROOT, StructureGenerationConfig(mode="scaled", seed=123), m2_input)
