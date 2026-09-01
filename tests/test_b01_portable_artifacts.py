from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from jersey_outbreak.calibration import run_synthetic_recovery
from jersey_outbreak.calibration_artifacts import (
    verify_calibration_artifact,
    write_calibration_artifact,
)
from jersey_outbreak.calibration_schemas import CalibrationConfig
from jersey_outbreak.cli import app
from jersey_outbreak.ensemble import run_ensemble
from jersey_outbreak.ensemble_artifacts import write_ensemble_artifact
from jersey_outbreak.intervention_artifacts import write_intervention_artifact
from jersey_outbreak.intervention_schemas import ScenarioConfig
from jersey_outbreak.observation import observe_latent_run
from jersey_outbreak.observation_artifacts import (
    verify_observation_artifact,
    write_observation_artifact,
)
from jersey_outbreak.outbreak_artifacts import write_outbreak_artifact
from jersey_outbreak.outbreak_runner import run_outbreak
from jersey_outbreak.scientific_verification import (
    verify_m5_artifact,
    verify_scientific_artifact,
)

ROOT = Path(__file__).resolve().parents[1]


def _assert_relative_records(artifact_directory: Path) -> None:
    manifest = json.loads((artifact_directory / "manifest.json").read_text(encoding="utf-8"))
    assert all(
        not Path(record["path"]).is_absolute() and ".." not in Path(record["path"]).parts
        for record in manifest["output_artifacts"]
    )


def test_default_in_repository_m5_cli_output_verifies(monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = CliRunner().invoke(app, ["outbreak", "run", "--mode", "ci", "--duration-days", "2"])
    assert result.exit_code == 0, result.stdout
    summary = json.loads(result.stdout)
    artifact_directory = Path(summary["artifact_directory"])
    _assert_relative_records(artifact_directory)
    assert verify_scientific_artifact(artifact_directory).artifact_type == "m5_outbreak"


def test_m5_outside_repository_and_relocated_copy_verify(m6_latent_run, tmp_path: Path) -> None:
    artifact = write_outbreak_artifact(m6_latent_run, ROOT, tmp_path / "outside")
    _assert_relative_records(artifact.artifact_directory)
    assert verify_m5_artifact(artifact.artifact_directory).artifact_id == (
        artifact.manifest.artifact_id
    )

    copied = tmp_path / "relocated-m5"
    shutil.copytree(artifact.artifact_directory, copied)
    shutil.rmtree(artifact.artifact_directory)
    assert verify_m5_artifact(copied).artifact_id == artifact.manifest.artifact_id


def test_relocated_m7_copy_recursively_verifies_embedded_m5(
    m6_network, m6_parameters, m6_base_config, tmp_path: Path
) -> None:
    config = m6_base_config.model_copy(update={"duration_days": 2})
    scenario = ScenarioConfig(
        scenario_id="b01-relocated-m7",
        start_date=config.start_date,
        duration_days=config.duration_days,
    )
    result = run_outbreak(m6_network, config, m6_parameters, scenario=scenario)
    artifact = write_intervention_artifact(result, ROOT, tmp_path / "m7")
    _assert_relative_records(artifact.artifact_directory)

    copied = tmp_path / "relocated-m7"
    shutil.copytree(artifact.artifact_directory, copied)
    shutil.rmtree(artifact.artifact_directory)
    assert verify_scientific_artifact(copied).artifact_type == "m7_intervention"


def test_relocated_m6_observation_and_ensemble_copies_verify(
    m6_network,
    m6_parameters,
    m6_base_config,
    m6_observation_config,
    m6_latent_run,
    tmp_path: Path,
) -> None:
    observed = observe_latent_run(m6_latent_run, m6_observation_config)
    observation_artifact = write_observation_artifact(observed, ROOT, tmp_path / "observation")
    _assert_relative_records(observation_artifact.artifact_directory)
    assert verify_observation_artifact(observation_artifact.artifact_directory).artifact_id == (
        observation_artifact.manifest.artifact_id
    )
    observation_copy = tmp_path / "relocated-observation"
    shutil.copytree(observation_artifact.artifact_directory, observation_copy)
    shutil.rmtree(observation_artifact.artifact_directory)
    assert verify_observation_artifact(observation_copy).artifact_id == (
        observation_artifact.manifest.artifact_id
    )

    ensemble = run_ensemble(
        tmp_path / "ensemble-runs",
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        (123,),
        ensemble_id="b01-relocated-ensemble",
    )
    ensemble_artifact = write_ensemble_artifact(ensemble, ROOT, tmp_path / "ensemble")
    _assert_relative_records(ensemble_artifact.artifact_directory)
    ensemble_copy = tmp_path / "relocated-ensemble"
    shutil.copytree(ensemble_artifact.artifact_directory, ensemble_copy)
    shutil.rmtree(ensemble_artifact.artifact_directory)
    assert verify_scientific_artifact(ensemble_copy).artifact_type == "m6_ensemble"


def test_relocated_calibration_copy_verifies(
    m6_network, m6_parameters, m6_base_config, m6_observation_config, tmp_path: Path
) -> None:
    config = CalibrationConfig(
        study_id="b01-relocated-calibration",
        candidate_min_days=0,
        candidate_max_days=1,
        trial_count=2,
        synthetic_truth_delay_days=1,
        heldout_seed=126,
    )
    result = run_synthetic_recovery(
        ROOT,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        calibration_config=config,
    )
    artifact = write_calibration_artifact(result, ROOT, tmp_path / "calibration")
    _assert_relative_records(artifact.artifact_directory)
    copied = tmp_path / "relocated-calibration"
    shutil.copytree(artifact.artifact_directory, copied)
    shutil.rmtree(artifact.artifact_directory)
    assert verify_calibration_artifact(copied).artifact_id == artifact.manifest.artifact_id


@pytest.mark.parametrize("bad_path", ["/absolute/file.parquet", "../outside/file.parquet"])
def test_m5_verifier_rejects_absolute_and_parent_paths(
    m6_latent_run, tmp_path: Path, bad_path: str
) -> None:
    artifact = write_outbreak_artifact(m6_latent_run, ROOT, tmp_path)
    manifest_path = artifact.artifact_directory / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["output_artifacts"][0]["path"] = bad_path
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(
        ValueError, match="portable artifact paths? (must be relative|must not contain)"
    ):
        verify_m5_artifact(artifact.artifact_directory)


@pytest.mark.parametrize("defect", ["hash", "size", "missing", "duplicate"])
def test_m5_manifest_integrity_failures_remain_detected(
    m6_latent_run, tmp_path: Path, defect: str
) -> None:
    artifact = write_outbreak_artifact(m6_latent_run, ROOT, tmp_path)
    manifest_path = artifact.artifact_directory / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    record = payload["output_artifacts"][0]
    if defect == "hash":
        record["sha256"] = "0" * 64
    elif defect == "size":
        record["size_bytes"] += 1
    elif defect == "missing":
        record["path"] = "missing.parquet"
    else:
        payload["output_artifacts"].append(dict(record))
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    expected = {
        "hash": "hash mismatch",
        "size": "size mismatch",
        "missing": "file is missing",
        "duplicate": "duplicate output",
    }[defect]
    with pytest.raises(ValueError, match=expected):
        verify_m5_artifact(artifact.artifact_directory)
