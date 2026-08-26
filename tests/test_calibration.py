import json
from pathlib import Path

from jersey_outbreak.calibration import run_synthetic_recovery
from jersey_outbreak.calibration_artifacts import write_calibration_artifact
from jersey_outbreak.calibration_schemas import CalibrationConfig

ROOT = Path(__file__).resolve().parents[1]


def test_synthetic_recovery_is_optuna_driven_and_does_not_use_real_data(
    m6_network, m6_parameters, m6_base_config, m6_observation_config
) -> None:
    config = CalibrationConfig(
        study_id="m6-test-recovery",
        candidate_min_days=0,
        candidate_max_days=2,
        trial_count=3,
        synthetic_truth_delay_days=1,
        heldout_seed=125,
    )
    result = run_synthetic_recovery(
        ROOT,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        calibration_config=config,
    )
    assert result.diagnostics["status"] == "passed"
    assert result.diagnostics["real_jersey_data_used"] is False
    assert len(result.trial_rows) == 3
    assert result.best_parameters == {"reporting_delay_days": 1}
    assert result.diagnostics["heldout"]["passed"] is True


def test_calibration_artifact_retains_trials_and_manifest(
    m6_network, m6_parameters, m6_base_config, m6_observation_config, tmp_path
) -> None:
    config = CalibrationConfig(
        study_id="m6-test-artifact",
        candidate_min_days=0,
        candidate_max_days=2,
        trial_count=3,
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
    artifact = write_calibration_artifact(result, ROOT, tmp_path)
    manifest = json.loads((artifact.artifact_directory / "manifest.json").read_text())
    assert manifest["status"] == "passed"
    assert manifest["trial_count"] == 3
    assert (artifact.artifact_directory / "calibration_trials.parquet").exists()
    assert (artifact.artifact_directory / "calibration_results.json").exists()
