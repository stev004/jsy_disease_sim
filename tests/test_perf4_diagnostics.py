from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import jersey_outbreak.ensemble as ensemble_module
import jersey_outbreak.network_artifacts as network_artifacts_module
from jersey_outbreak.ensemble import run_ensemble
from jersey_outbreak.network_artifacts import write_network_artifact
from jersey_outbreak.network_generator import GeneratedNetworks, generate_networks
from jersey_outbreak.observation import load_observation_config, observe_latent_run
from jersey_outbreak.outbreak_runner import default_run_config, load_parameter_set, run_outbreak

ROOT = Path(__file__).resolve().parents[1]


def _build_pair(m6_network: GeneratedNetworks) -> tuple[GeneratedNetworks, GeneratedNetworks]:
    full = generate_networks(
        m6_network.config,
        m6_network.m2_input,
        m6_network.m3_input,
        ROOT,
        diagnostics="full",
    )
    internal = generate_networks(
        m6_network.config,
        m6_network.m2_input,
        m6_network.m3_input,
        ROOT,
        diagnostics="internal",
    )
    return full, internal


def _normalised_artifact_file(path: Path) -> Any:
    if path.suffix != ".json":
        return path.read_bytes()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if path.name == "manifest.json":
        for key in ("created_at", "runtime_seconds", "peak_memory_bytes"):
            payload.pop(key, None)
        payload["output_artifacts"] = [
            {"path": record["path"]} for record in payload["output_artifacts"]
        ]
    elif path.name == "benchmark.json":
        for key in ("construction_runtime_seconds", "peak_memory_bytes"):
            payload.pop(key, None)
    elif path.name == "diagnostics.json":
        benchmark = payload.get("benchmark")
        if isinstance(benchmark, dict):
            for key in ("construction_runtime_seconds", "peak_memory_bytes"):
                benchmark.pop(key, None)
    return payload


def test_full_and_internal_modes_preserve_network_and_run_identity(m6_network) -> None:
    full, internal = _build_pair(m6_network)

    assert full.logical_content_hash == internal.logical_content_hash
    assert full.staffing_diagnostics == internal.staffing_diagnostics
    assert full.staffing_provenance == internal.staffing_provenance
    assert full.diagnostics["staffing"] == internal.diagnostics["staffing"]
    assert (
        full.diagnostics["provenance"]["staffing"] == internal.diagnostics["provenance"]["staffing"]
    )
    assert (
        full.diagnostics["cross_route"]["route_overlap_matrix"]
        == (internal.diagnostics["cross_route"]["route_overlap_matrix"])
    )
    for route_id in full.route_specs:
        for snapshot_date in full.config.snapshot_dates:
            assert (
                full.route_snapshot(route_id, snapshot_date).edges
                == internal.route_snapshot(route_id, snapshot_date).edges
            )

    assert internal.diagnostics["route_analysis"] == {
        "omitted": "internal_replicate_mode",
        "omitted_keys": [
            "routes",
            "cross_route.zero_non_household_contacts",
            "cross_route.agents_by_route_type_count",
            "cross_route.community_participation_by_residence_type",
            "cross_route.route_participation",
        ],
    }
    assert internal.diagnostics["routes"] == {"omitted": "internal_replicate_mode"}
    cross_route = internal.diagnostics["cross_route"]
    for key in (
        "zero_non_household_contacts",
        "agents_by_route_type_count",
        "community_participation_by_residence_type",
        "route_participation",
    ):
        assert cross_route[key] == {"omitted": "internal_replicate_mode"}

    parameters = load_parameter_set(ROOT)
    observation = load_observation_config(ROOT)
    run_config = default_run_config("ci", 123, parameters, duration_days=7)
    full_latent = run_outbreak(full, run_config, parameters, observation_config=observation)
    internal_latent = run_outbreak(internal, run_config, parameters, observation_config=observation)
    full_observed = observe_latent_run(full_latent, observation)
    internal_observed = observe_latent_run(internal_latent, observation)
    assert full_latent.logical_content_hash == internal_latent.logical_content_hash
    assert full_latent.latent_outcome_hash == internal_latent.latent_outcome_hash
    assert full_observed.logical_content_hash == internal_observed.logical_content_hash


def test_default_mode_matches_explicit_full_public_artifact_bytes(
    m6_network, tmp_path: Path
) -> None:
    default = generate_networks(m6_network.config, m6_network.m2_input, m6_network.m3_input, ROOT)
    explicit = generate_networks(
        m6_network.config,
        m6_network.m2_input,
        m6_network.m3_input,
        ROOT,
        diagnostics="full",
    )
    default_artifact = write_network_artifact(default, ROOT, tmp_path / "default")
    explicit_artifact = write_network_artifact(explicit, ROOT, tmp_path / "explicit")
    default_files = {path.name for path in default_artifact.artifact_directory.iterdir()}
    explicit_files = {path.name for path in explicit_artifact.artifact_directory.iterdir()}
    assert default_files == explicit_files
    for name in sorted(default_files):
        assert _normalised_artifact_file(default_artifact.artifact_directory / name) == (
            _normalised_artifact_file(explicit_artifact.artifact_directory / name)
        )


def test_replicate_worker_uses_internal_mode_and_does_not_write_m4_artifact(
    m6_network, m6_parameters, m6_observation_config, m6_base_config, monkeypatch
) -> None:
    seen: list[str | None] = []
    original = ensemble_module.generate_networks

    def wrapped(*args: Any, **kwargs: Any) -> GeneratedNetworks:
        seen.append(kwargs.get("diagnostics"))
        return original(*args, **kwargs)

    def fail_if_public_artifact_written(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("internal replicate mode must not write a public M4 artifact")

    monkeypatch.setattr(ensemble_module, "generate_networks", wrapped)
    monkeypatch.setattr(
        network_artifacts_module, "write_network_artifact", fail_if_public_artifact_written
    )
    job = {
        "seed": 123,
        "network_config": m6_network.config,
        "m2_input": m6_network.m2_input,
        "m3_input": m6_network.m3_input,
        "root": str(ROOT),
        "base_run_config": m6_base_config.model_copy(update={"duration_days": 7}),
        "parameters": m6_parameters,
        "observation_config": m6_observation_config,
        "scenario": None,
    }
    output = ensemble_module._run_replicate_job(job)
    assert output.status == "passed", output.error
    assert seen == ["internal"]


def test_two_seed_seven_day_ensemble_matches_full_mode_direct_runs(
    m6_network,
    m6_parameters,
    m6_observation_config,
    m6_base_config,
    tmp_path: Path,
) -> None:
    seeds = (123, 124)
    run_config = m6_base_config.model_copy(update={"duration_days": 7})
    ensemble = run_ensemble(
        tmp_path / "ensemble",
        m6_network,
        m6_parameters,
        run_config,
        m6_observation_config,
        seeds,
        ensemble_id="perf4-two-seed",
        checkpoint_root=tmp_path / "checkpoints",
        workers=2,
    )
    records = {record.seed: record for record in ensemble.replicate_records}
    for seed in seeds:
        full = generate_networks(
            m6_network.config.model_copy(update={"seed": seed}),
            m6_network.m2_input,
            m6_network.m3_input,
            ROOT,
            diagnostics="full",
        )
        latent = run_outbreak(full, run_config.model_copy(update={"seed": seed}), m6_parameters)
        observed = observe_latent_run(latent, m6_observation_config)
        record = records[seed]
        assert record.m4_logical_content_hash == full.logical_content_hash
        assert record.latent_run_logical_content_hash == latent.logical_content_hash
        assert record.observation_logical_content_hash == observed.logical_content_hash


@pytest.mark.parametrize("diagnostics", ["invalid", True, False])
def test_diagnostics_mode_is_explicit(diagnostics, m6_network) -> None:
    with pytest.raises(ValueError, match="diagnostics must be 'full' or 'internal'"):
        generate_networks(
            m6_network.config,
            m6_network.m2_input,
            m6_network.m3_input,
            ROOT,
            diagnostics=diagnostics,
        )  # type: ignore[arg-type]
