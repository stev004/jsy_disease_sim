import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from jersey_outbreak.cli import app
from jersey_outbreak.data_pipeline import DataBuildError
from jersey_outbreak.hashing import sha256_file
from jersey_outbreak.population_artifacts import write_population_artifact
from jersey_outbreak.population_controls import _validate_canonical_inputs
from jersey_outbreak.population_generator import generate_population
from jersey_outbreak.population_schemas import PopulationGenerationConfig

ROOT = Path(__file__).resolve().parents[1]


def test_population_config_enforces_milestone_2_scale_boundaries() -> None:
    assert PopulationGenerationConfig(mode="ci", seed=123).resolved_target_population == 3_000
    assert PopulationGenerationConfig(mode="scaled", seed=123).resolved_target_population == 15_000
    assert PopulationGenerationConfig(mode="full", seed=123).resolved_target_population == 104_540

    with pytest.raises(ValidationError):
        PopulationGenerationConfig(mode="ci", seed=123, target_population=1_999)
    with pytest.raises(ValidationError):
        PopulationGenerationConfig(mode="scaled", seed=123, target_population=25_001)
    with pytest.raises(ValidationError):
        PopulationGenerationConfig(mode="full", seed=123, target_population=15_000)


def test_canonical_input_hashes_fail_closed_on_tampering(tmp_path: Path) -> None:
    processed = tmp_path / "data" / "processed"
    processed.mkdir(parents=True)
    table = processed / "control.csv"
    table.write_text("value\n1\n", encoding="utf-8")
    (processed / "table_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "tables": [{"path": "data/processed/control.csv", "sha256": sha256_file(table)}],
            }
        ),
        encoding="utf-8",
    )
    (processed / "quality_report.json").write_text(
        json.dumps({"build_status": "passed"}), encoding="utf-8"
    )

    assert _validate_canonical_inputs(tmp_path)["data/processed/control.csv"] == sha256_file(table)
    table.write_text("value\n2\n", encoding="utf-8")
    with pytest.raises(DataBuildError, match="hash mismatch"):
        _validate_canonical_inputs(tmp_path)


def test_ci_population_is_deterministic_and_preserves_membership_invariants() -> None:
    config = PopulationGenerationConfig(mode="ci", seed=123)
    first = generate_population(ROOT, config)
    second = generate_population(ROOT, config)
    changed_seed = generate_population(ROOT, PopulationGenerationConfig(mode="ci", seed=124))

    assert first.logical_content_hash == second.logical_content_hash
    assert first.logical_content_hash != changed_seed.logical_content_hash
    assert first.diagnostics["status"] == "passed"
    assert len(first.residents) == 3_000
    assert sum(row["resident_count"] for row in first.communal_settings) == 60
    assert all(
        (row["household_id"] is None) != (row["care_setting_id"] is None) for row in first.residents
    )
    assert all(
        row["member_count"]
        == sum(resident["household_id"] == row["household_id"] for resident in first.residents)
        for row in first.households
    )


def test_scaled_population_reaches_target_and_writes_parquet_artifacts(tmp_path: Path) -> None:
    generated = generate_population(ROOT, PopulationGenerationConfig(mode="scaled", seed=123))
    artifact = write_population_artifact(generated, ROOT, tmp_path)

    assert artifact.manifest.diagnostics_status == "passed"
    assert artifact.manifest.actual_population == 15_000
    assert artifact.manifest.logical_content_hash == generated.logical_content_hash
    assert (artifact.artifact_directory / "residents.parquet").exists()
    assert (artifact.artifact_directory / "households.parquet").exists()
    assert (artifact.artifact_directory / "communal_settings.parquet").exists()
    assert (artifact.artifact_directory / "diagnostics.json").exists()
    assert (artifact.artifact_directory / "benchmark.json").exists()


def test_population_cli_emits_machine_readable_artifact_summary(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        ["population", "generate", "--mode", "ci", "--seed", "123", "--output-dir", str(tmp_path)],
    )
    assert result.exit_code == 0, result.stdout
    summary = json.loads(result.stdout)
    manifest = json.loads((Path(summary["artifact_directory"]) / "manifest.json").read_text())
    assert summary["diagnostics_status"] == "passed"
    assert summary["logical_content_hash"] == manifest["logical_content_hash"]
    assert manifest["target_population"] == 3_000
