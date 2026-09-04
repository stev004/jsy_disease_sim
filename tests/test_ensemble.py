import json
from dataclasses import replace
from pathlib import Path

import pytest

from jersey_outbreak.ensemble import _summary_rows, compare_ensembles, run_ensemble
from jersey_outbreak.ensemble_artifacts import (
    write_comparison_artifact,
    write_ensemble_artifact,
)
from jersey_outbreak.ensemble_schemas import EnsembleConfig
from jersey_outbreak.scientific_hashes import (
    m6_ensemble_config_hash,
    m6_ensemble_logical_hash,
)
from jersey_outbreak.scientific_verification import verify_m6_ensemble_artifact


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


def test_m6_identity_excludes_execution_resources_but_retains_science(
    m6_base_config, m6_observation_config
) -> None:
    config = EnsembleConfig(
        ensemble_id="m6-identity",
        base_run_config=m6_base_config,
        observation_config=m6_observation_config,
        replicate_seeds=(123,),
    )
    execution_variant = config.model_copy(
        update={
            "workers": 2,
            "estimated_worker_memory_bytes": 1_000_000_000,
            "memory_safety_fraction": 0.8,
            "allow_unsafe_workers": True,
        }
    )

    def logical_hash(candidate: EnsembleConfig) -> str:
        return m6_ensemble_logical_hash(
            config=candidate.model_dump(mode="json"),
            replicate_records=[],
            summary=[],
            trajectories={},
            replicate_grid=[],
        )

    base_config_hash = m6_ensemble_config_hash(config.model_dump(mode="json"))
    execution_base_config_hash = m6_ensemble_config_hash(execution_variant.model_dump(mode="json"))
    logical = logical_hash(config)
    execution_logical = logical_hash(execution_variant)
    artifact_id = f"jos-ensemble-m6-{config.ensemble_id}-{logical[:12]}"
    execution_artifact_id = (
        f"jos-ensemble-m6-{execution_variant.ensemble_id}-{execution_logical[:12]}"
    )

    assert logical == execution_logical
    assert base_config_hash == execution_base_config_hash
    assert artifact_id.rsplit("-", 1)[-1] == execution_artifact_id.rsplit("-", 1)[-1]

    scientific_variant = config.model_copy(update={"replicate_seeds": (124,)})
    assert logical_hash(scientific_variant) != logical


def test_m6_schema_1_4_verifies_with_legacy_config_payload(
    m6_network, m6_parameters, m6_base_config, m6_observation_config, tmp_path
) -> None:
    result = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        (123,),
        ensemble_id="m6-legacy-1-4",
    )
    artifact = write_ensemble_artifact(result, Path(__file__).resolve().parents[1], tmp_path)
    manifest_path = artifact.artifact_directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    legacy_hash = m6_ensemble_logical_hash(
        config=result.config.model_dump(mode="json"),
        replicate_records=[record.model_dump(mode="json") for record in result.replicate_records],
        summary=list(result.summary),
        trajectories=result.replicate_trajectories,
        replicate_grid=list(result.replicate_grid),
        schema_version="1.4",
    )
    manifest["manifest_schema_version"] = "1.4"
    manifest["logical_content_hash"] = legacy_hash
    manifest["artifact_id"] = f"jos-ensemble-m6-{result.config.ensemble_id}-{legacy_hash[:12]}"
    manifest["base_config_hash"] = m6_ensemble_config_hash(
        result.config.model_dump(mode="json"), schema_version="1.4"
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    assert verify_m6_ensemble_artifact(artifact.artifact_directory).logical_content_hash == (
        legacy_hash
    )


def test_ensemble_summary_quantiles_use_declared_linear_definition() -> None:
    trajectories = {
        seed: (
            {
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_new_infections",
                "date": "2025-01-01",
                "value": value,
            },
        )
        for seed, value in enumerate((1, 2, 3, 4), start=1)
    }
    rows = _summary_rows(trajectories, 0.25, 0.75)
    assert rows[0]["lower_value"] == 1.75
    assert rows[0]["median"] == 2.5
    assert rows[0]["upper_value"] == 3.25
    assert rows[0]["replicate_count"] == 4
    assert rows[0]["interval_class"] == "stochastic_replicate_quantile"


def test_ensemble_summary_requires_resolvable_empirical_tails() -> None:
    def trajectories(count: int) -> dict[int, tuple[dict[str, object], ...]]:
        return {
            seed: (
                {
                    "scope": "epidemic",
                    "key": "all",
                    "metric": "latent_new_infections",
                    "date": "2025-01-01",
                    "value": seed,
                },
            )
            for seed in range(count)
        }

    insufficient = _summary_rows(trajectories(39), 0.025, 0.975)[0]
    sufficient = _summary_rows(trajectories(40), 0.025, 0.975)[0]
    assert insufficient["interval_class"] == "insufficient_tail"
    assert insufficient["lower_value"] is None
    assert insufficient["upper_value"] is None
    assert insufficient["median"] is not None
    assert sufficient["interval_class"] == "stochastic_replicate_quantile"
    assert sufficient["lower_value"] is not None
    assert sufficient["upper_value"] is not None


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
    checkpoint_directory = tmp_path / "outputs" / ".replicates-in-progress" / "m6-sequential"
    assert {path.name for path in checkpoint_directory.glob("seed-*.json")} == {
        "seed-123.json",
        "seed-124.json",
    }


def test_process_parallelism_preserves_declared_outputs(
    m6_network, m6_parameters, m6_base_config, m6_observation_config, tmp_path
) -> None:
    seeds = (123, 124)
    sequential = run_ensemble(
        tmp_path / "sequential",
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        seeds,
        ensemble_id="m6-workers",
        workers=1,
    )
    parallel = run_ensemble(
        tmp_path / "parallel",
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        seeds,
        ensemble_id="m6-workers",
        workers=2,
    )
    assert sequential.logical_content_hash == parallel.logical_content_hash
    assert sequential.summary == parallel.summary
    assert sequential.replicate_trajectories == parallel.replicate_trajectories
    assert sequential.replicate_grid == parallel.replicate_grid
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
    assert comparison.paired_summary
    assert all(row["paired_count"] == 2 for row in comparison.paired_summary)
    assert all(row["requested_pair_count"] == 2 for row in comparison.paired_summary)
    assert all(row["missing_or_failed_pair_count"] == 0 for row in comparison.paired_summary)
    assert all(
        row["quantile_method"] == "numpy.quantile(method='linear')"
        for row in comparison.paired_summary
    )
    target_summary = next(
        row
        for row in comparison.paired_summary
        if row["metric"] == "observed_reported_cases"
        and any(
            candidate["metric"] == row["metric"]
            and candidate["scope"] == row["scope"]
            and candidate["key"] == row["key"]
            and candidate["date"] == row["date"]
            and candidate["difference"] != 0
            for candidate in observed_differences
        )
    )
    target_differences = [
        float(row["difference"])
        for row in observed_differences
        if row["scope"] == target_summary["scope"]
        and row["key"] == target_summary["key"]
        and row["date"] == target_summary["date"]
    ]
    assert target_summary["median_difference"] == pytest.approx(
        sum(target_differences) / len(target_differences)
    )
    assert target_summary["mean_difference"] == pytest.approx(
        sum(target_differences) / len(target_differences)
    )
    assert all(
        row["fraction_negative"] + row["fraction_zero"] + row["fraction_positive"]
        == pytest.approx(1.0)
        for row in comparison.paired_summary
    )

    failed_record = comparison_ensemble.replicate_records[1].model_copy(
        update={
            "status": "failed",
            "latent_run_logical_content_hash": None,
            "observation_logical_content_hash": None,
            "m4_logical_content_hash": None,
            "error": "controlled failure",
        }
    )
    partial_ensemble = replace(
        comparison_ensemble,
        replicate_records=(comparison_ensemble.replicate_records[0], failed_record),
        replicate_trajectories={
            123: comparison_ensemble.replicate_trajectories[123],
        },
    )
    partial = compare_ensembles(baseline, partial_ensemble, comparison_id="m6-partial")
    assert partial.diagnostics["missing_or_failed_pair_count"] == 1
    assert all(row["paired_count"] == 1 for row in partial.paired_summary)
    assert all(row["missing_or_failed_pair_count"] == 1 for row in partial.paired_summary)
    assert all(row["median_difference"] is None for row in partial.paired_summary)


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
    assert comparison.paired_summary
    assert all(row["median_difference"] is None for row in comparison.paired_summary)
    assert all(row["mean_difference"] == 0 for row in comparison.paired_summary)
    assert all(row["fraction_zero"] == 1 for row in comparison.paired_summary)
    assert all(row["interval_class"] == "insufficient_tail" for row in comparison.paired_summary)
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
    assert all(
        ".replicates-in-progress" not in record["path"]
        for record in ensemble_manifest["output_artifacts"]
    )
    assert comparison_manifest["paired_count"] == 1
    assert (ensemble_artifact.artifact_directory / "ensemble_summary.parquet").exists()
    assert (comparison_artifact.artifact_directory / "matched_seed_comparison.parquet").exists()
    assert (comparison_artifact.artifact_directory / "paired_difference_summary.parquet").exists()
