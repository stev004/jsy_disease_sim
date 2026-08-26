import json
from pathlib import Path

import pytest

from jersey_outbreak.ensemble import _summary_rows, compare_ensembles, run_ensemble
from jersey_outbreak.ensemble_artifacts import (
    write_comparison_artifact,
    write_ensemble_artifact,
)
from jersey_outbreak.ensemble_schemas import EnsembleConfig


def test_ensemble_config_requires_explicit_unique_seeds(
    m6_base_config, m6_observation_config
) -> None:
    with pytest.raises(ValueError, match="unique"):
        EnsembleConfig(
            ensemble_id="duplicate-seeds",
            base_run_config=m6_base_config,
            observation_config=m6_observation_config,
            replicate_seeds=(123, 123),
        )


def test_ensemble_summary_quantiles_use_declared_linear_definition() -> None:
    trajectories = {
        1: ({"scope": "epidemic", "key": "all", "metric": "x", "date": "2025-01-01", "value": 1},),
        2: ({"scope": "epidemic", "key": "all", "metric": "x", "date": "2025-01-01", "value": 3},),
    }
    rows = _summary_rows(trajectories, 0.25, 0.75)
    assert rows[0]["lower_value"] == 1.5
    assert rows[0]["median"] == 2.0
    assert rows[0]["upper_value"] == 2.5
    assert rows[0]["replicate_count"] == 2


def test_sequential_ensemble_persists_seed_results_and_is_reproducible(
    m6_network, m6_parameters, m6_base_config, m6_observation_config, tmp_path
) -> None:
    seeds = (123, 124)
    first = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        seeds,
        ensemble_id="m6-sequential",
    )
    second = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        seeds,
        ensemble_id="m6-sequential",
    )
    assert first.diagnostics["status"] == "passed"
    assert [record.seed for record in first.replicate_records] == [123, 124]
    assert first.logical_content_hash == second.logical_content_hash
    assert first.summary == second.summary


def test_process_parallelism_preserves_declared_outputs(
    m6_network, m6_parameters, m6_base_config, m6_observation_config, tmp_path
) -> None:
    seeds = (123, 124)
    sequential = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        seeds,
        ensemble_id="m6-workers",
        workers=1,
    )
    parallel = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        seeds,
        ensemble_id="m6-workers",
        workers=2,
    )
    assert sequential.summary == parallel.summary
    assert sequential.replicate_trajectories == parallel.replicate_trajectories
    assert [record.latent_run_logical_content_hash for record in sequential.replicate_records] == [
        record.latent_run_logical_content_hash for record in parallel.replicate_records
    ]


def test_changing_replicate_seed_changes_synthetic_membership_but_not_controls(
    m6_network, m6_parameters, m6_base_config, m6_observation_config, tmp_path
) -> None:
    baseline = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        (123,),
        ensemble_id="m6-seed-123",
    )
    changed = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        (999,),
        ensemble_id="m6-seed-999",
    )
    assert baseline.diagnostics["status"] == "passed"
    assert changed.diagnostics["status"] == "passed"
    assert baseline.m2_logical_content_hash == changed.m2_logical_content_hash
    assert baseline.m3_logical_content_hash == changed.m3_logical_content_hash
    assert baseline.replicate_records[0].m4_logical_content_hash != (
        changed.replicate_records[0].m4_logical_content_hash
    )


def test_failed_replicate_is_not_reported_as_complete(
    m6_network, m6_parameters, m6_base_config, m6_observation_config, tmp_path
) -> None:
    failed_config = m6_base_config.model_copy(update={"initial_seed_count": 4000})
    result = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        failed_config,
        m6_observation_config,
        (123,),
        ensemble_id="m6-failure",
    )
    assert result.diagnostics["status"] == "failed"
    assert result.diagnostics["failed_replicates"] == 1
    assert result.replicate_records[0].status == "failed"


def test_matched_comparison_preserves_seed_pairing(
    m6_network, m6_parameters, m6_base_config, m6_observation_config, tmp_path
) -> None:
    baseline = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        (123, 124),
        ensemble_id="m6-compare-a",
    )
    altered_parameters = {
        key: parameter.model_copy(update={"value": 0.0})
        if key.endswith("detection_probability")
        else parameter
        for key, parameter in m6_observation_config.parameters.items()
    }
    altered = m6_observation_config.model_copy(update={"parameters": altered_parameters})
    comparison_ensemble = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        altered,
        (123, 124),
        ensemble_id="m6-compare-b",
    )
    comparison = compare_ensembles(baseline, comparison_ensemble, comparison_id="m6-ab")
    assert comparison.diagnostics["status"] == "passed"
    assert comparison.diagnostics["paired_seed_count"] == 2
    assert comparison.diagnostics["missing_or_failed_pair_count"] == 0
    assert all(row["seed"] in {123, 124} for row in comparison.paired_rows)
    observed_differences = [
        row for row in comparison.paired_rows if row["metric"] == "observed_reported_cases"
    ]
    assert any(row["difference"] != 0 for row in observed_differences)


def test_ensemble_and_comparison_artifacts_preserve_provenance(
    m6_network, m6_parameters, m6_base_config, m6_observation_config, tmp_path: Path
) -> None:
    first = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        (123,),
        ensemble_id="m6-artifact-a",
    )
    second = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        (123,),
        ensemble_id="m6-artifact-b",
    )
    ensemble_artifact = write_ensemble_artifact(
        first, Path(__file__).resolve().parents[1], tmp_path
    )
    comparison = compare_ensembles(first, second, comparison_id="m6-artifact-comparison")
    comparison_artifact = write_comparison_artifact(
        comparison, Path(__file__).resolve().parents[1], tmp_path
    )
    ensemble_manifest = json.loads(
        (ensemble_artifact.artifact_directory / "manifest.json").read_text()
    )
    comparison_manifest = json.loads(
        (comparison_artifact.artifact_directory / "manifest.json").read_text()
    )
    assert (
        ensemble_manifest["m2_logical_content_hash"]
        == m6_network.m2_input.manifest.logical_content_hash
    )
    assert ensemble_manifest["successful_replicates"] == 1
    assert comparison_manifest["paired_count"] == 1
    assert (ensemble_artifact.artifact_directory / "ensemble_summary.parquet").exists()
    assert (comparison_artifact.artifact_directory / "matched_seed_comparison.parquet").exists()
