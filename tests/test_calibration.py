import json
from pathlib import Path

from jersey_outbreak.calibration import _profile_beta_nuisance, run_synthetic_recovery
from jersey_outbreak.calibration_artifacts import write_calibration_artifact
from jersey_outbreak.calibration_schemas import CalibrationConfig

ROOT = Path(__file__).resolve().parents[1]


def test_beta_nuisance_profile_reminimizes_at_each_beta() -> None:
    profile = _profile_beta_nuisance(
        {
            0.04: {0.5: 4.0, 1.0: 1.0},
            0.08: {0.5: 0.0, 1.0: 2.0},
            0.12: {0.5: 3.0, 1.0: 3.0},
        }
    )

    rows = {row["transmission_beta"]: row for row in profile["rows"]}
    assert rows[0.04]["argmin_nuisance_factor"] == 1.0
    assert rows[0.08]["argmin_nuisance_factor"] == 0.5
    assert profile["argmin"] == {
        "transmission_beta": 0.08,
        "nuisance_factor": 0.5,
        "objective": 0.0,
    }


def test_beta_heldout_gate_rejects_non_identifiable_exact_reproduction(
    m6_network, m6_parameters, m6_base_config, m6_observation_config
) -> None:
    config = CalibrationConfig(
        study_id="c3-test-beta-degenerate-gate",
        hidden_parameter="transmission_beta",
        candidate_beta_values=(0.04, 0.06),
        trial_count=2,
        synthetic_truth_beta=0.06,
        recovery_tolerance_beta=0.021,
        training_replicate_seeds=(123,),
        heldout_replicate_seeds=(125,),
    )
    result = run_synthetic_recovery(
        ROOT,
        m6_network,
        m6_parameters,
        m6_base_config.model_copy(update={"duration_days": 1}),
        m6_observation_config,
        calibration_config=config,
    )

    assert result.best_parameters == {"transmission_beta": 0.04}
    assert result.diagnostics["recovery_error"] <= config.recovery_tolerance_beta
    assert result.diagnostics["heldout"]["objective_components"]["objective"] == 0
    assert result.diagnostics["status"] == "failed"
    assert result.diagnostics["heldout"]["passed"] is False
    assert result.diagnostics["heldout"]["tied_minimizers"] == [0.04, 0.06]


def test_delay_recovery_discloses_noiseless_beta_zero_operator_check(
    m6_network, m6_parameters, m6_base_config, m6_observation_config
) -> None:
    config = CalibrationConfig(
        study_id="c3-test-delay-disclosure",
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

    truth = result.diagnostics["synthetic_truth"]
    assert truth["experiment"] == "delay_operator_invertibility_check"
    assert truth["transmission_beta"] == 0.0
    assert truth["initial_seed_count"] == 10
    assert truth["secondary_transmission_event_count"] == 0
    assert truth["target_observation"]["fully_detecting"] is True
    assert truth["target_observation"]["detection_parameters"] == {
        "symptomatic_detection_probability": 1.0,
        "asymptomatic_detection_probability": 1.0,
    }
    assert all(
        event["source_kind"] == "seeded" for event in result.target_latent.transmission_events
    )
    assert len(result.target_latent.transmission_events) <= truth["initial_seed_count"]


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
    assert manifest["manifest_schema_version"] == "1.4"
    assert manifest["trial_count"] == 3
    assert (artifact.artifact_directory / "calibration_trials.parquet").exists()
    assert (artifact.artifact_directory / "calibration_results.json").exists()
