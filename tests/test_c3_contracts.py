"""Adversarial C3 tests for observation, ensembles, calibration and archives."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from jersey_outbreak.calibration import run_synthetic_recovery
from jersey_outbreak.calibration_schemas import CalibrationConfig
from jersey_outbreak.ensemble import _summary_rows, safe_worker_bound
from jersey_outbreak.hashing import canonical_json_bytes, sha256_bytes
from jersey_outbreak.observation import observe_latent_run
from jersey_outbreak.observation_schemas import ReportingDelayDistribution
from jersey_outbreak.verification_archive import (
    verify_verification_archive,
    write_verification_archive,
)

ROOT = Path(__file__).resolve().parents[1]


def _controlled_latent(latent, *, event_count: int = 2, seed: int | None = None):
    start = "2025-01-06"
    events = []
    for index, agent_id in enumerate(latent.generated.agent_ids[:event_count]):
        events.append(
            {
                "infected_agent_id": agent_id,
                "infected_uid": index,
                "date": "2025-01-06" if index == 0 else "2025-01-07",
                "source_kind": "seeded" if index == 0 else "local",
                "route_id": "household",
            }
        )
    daily = [
        {
            "date": start,
            "new_local_infections": 0,
            "new_imported_infections": 0,
            "new_seeded_infections": event_count,
        },
        {
            "date": "2025-01-07",
            "new_local_infections": 0,
            "new_imported_infections": 0,
            "new_seeded_infections": 0,
        },
    ]
    config = latent.config
    if seed is not None:
        config = config.model_copy(update={"seed": seed})
    return replace(
        latent,
        config=config,
        daily_epidemic=daily,
        transmission_events=events,
        logical_content_hash=sha256_bytes(canonical_json_bytes({"events": events, "seed": seed})),
    )


def _delay(days: int) -> ReportingDelayDistribution:
    return ReportingDelayDistribution(
        kind="fixed",
        days=(days,),
        status="scenario_assumption",
        notes="C3 controlled test delay.",
    )


def test_observation_horizon_conserves_latent_events_and_exposes_causal_timeline(
    m6_latent_run, m6_observation_config
) -> None:
    latent = _controlled_latent(m6_latent_run)
    parameters = {
        key: parameter.model_copy(
            update={
                "value": (
                    1.0
                    if key in {"symptomatic_probability", "symptomatic_detection_probability"}
                    else 0.0
                )
            }
        )
        for key, parameter in m6_observation_config.parameters.items()
    }
    config = m6_observation_config.model_copy(
        update={
            "parameters": parameters,
            "symptom_onset_delay": _delay(0),
            "detection_delay": _delay(1),
            "reporting_delay": _delay(2),
            "day_of_week_effect": (1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0),
        }
    )
    result = observe_latent_run(latent, config)
    assert result.diagnostics["latent_incidence_conservation"] is True
    assert result.diagnostics["chronology_violations"] == 0
    assert len(result.detection_events) == 1
    assert result.detection_events[0].detection_date == "2025-01-07"
    assert result.daily_observed_cases[-1]["date"] == "2025-01-10"
    assert result.diagnostics["detection_event_interface"]["mutates_latent_or_routes"] is False


def test_observation_stream_is_replicate_specific(m6_latent_run, m6_observation_config) -> None:
    first = observe_latent_run(
        _controlled_latent(m6_latent_run, event_count=20, seed=123), m6_observation_config
    )
    same = observe_latent_run(
        _controlled_latent(m6_latent_run, event_count=20, seed=123), m6_observation_config
    )
    changed = observe_latent_run(
        _controlled_latent(m6_latent_run, event_count=20, seed=999), m6_observation_config
    )
    assert first.logical_content_hash == same.logical_content_hash
    assert (
        first.diagnostics["observation_rng"]["stream_fingerprint"]
        == same.diagnostics["observation_rng"]["stream_fingerprint"]
    )
    assert first.logical_content_hash != changed.logical_content_hash
    assert (
        first.diagnostics["observation_rng"]["stream_fingerprint"]
        != changed.diagnostics["observation_rng"]["stream_fingerprint"]
    )


def test_ensemble_summary_structurally_fills_incidence_and_reports_contributors() -> None:
    trajectories = {
        1: (
            {
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_new_infections",
                "date": "2025-01-01",
                "value": 1,
            },
        ),
        2: (
            {
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_new_infections",
                "date": "2025-01-02",
                "value": 3,
            },
        ),
    }
    rows = _summary_rows(
        trajectories,
        0.25,
        0.75,
        requested_replicates=3,
        horizon=("2025-01-01", "2025-01-02", "2025-01-03"),
    )
    assert len(rows) == 3
    assert [row["median"] for row in rows] == [0.5, 1.5, 0.0]
    assert all(row["requested_replicates"] == 3 for row in rows)
    assert all(row["successful_replicates"] == 2 for row in rows)
    assert all(row["contributing_replicates"] == 2 for row in rows)
    assert all(row["failed_replicates"] == 1 for row in rows)


def test_worker_bound_is_memory_safe_and_deterministic() -> None:
    assert safe_worker_bound(32, available_memory_bytes=1_000_000_000, cpu_count=32) == 1
    assert safe_worker_bound(32, available_memory_bytes=32_000_000_000, cpu_count=4) == 4
    with pytest.raises(ValueError):
        safe_worker_bound(0)


def test_beta_recovery_has_train_heldout_and_confounding_profile(
    m6_network, m6_parameters, m6_base_config, m6_observation_config
) -> None:
    config = CalibrationConfig(
        study_id="c3-test-beta",
        hidden_parameter="transmission_beta",
        candidate_beta_values=(0.04, 0.08, 0.12),
        trial_count=3,
        synthetic_truth_beta=0.08,
        training_replicate_seeds=(123,),
        heldout_replicate_seeds=(125,),
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
    assert result.best_parameters == {"transmission_beta": 0.08}
    assert result.diagnostics["heldout"]["passed"] is True
    assert result.diagnostics["identifiability_profile"]["altered_ascertainment_objective"] >= 0
    assert result.diagnostics["identifiability_profile"]["altered_route_weight_objective"] >= 0


def test_verification_archive_rejects_stale_parent_hashes(tmp_path: Path) -> None:
    archive = write_verification_archive(
        ROOT,
        tmp_path,
        verification_id="c3-test-archive",
        parent_hashes={"m4": "a" * 64},
        layer_hashes={"m2": "b" * 64, "m3": "c" * 64},
        command_results={"pytest": "passed"},
        require_clean=False,
    )
    assert (
        verify_verification_archive(archive.archive_directory / "manifest.json")["status"]
        == "passed"
    )
    with pytest.raises(ValueError, match="parent hash mismatch"):
        verify_verification_archive(
            archive.archive_directory / "manifest.json",
            expected_parent_hashes={"m4": "d" * 64},
        )
