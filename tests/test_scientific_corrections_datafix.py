"""Regression tests for the DATA-7, DATA-10 and DISEASE-10 corrections."""

from __future__ import annotations

import csv
from dataclasses import replace
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from jersey_outbreak.observation import observe_latent_run
from jersey_outbreak.observation_scheduler import ObservationScheduleSnapshot
from jersey_outbreak.travel import _high_risk_epidemic_rows, load_travel_config
from jersey_outbreak.travel_schemas import TravelConfig

ROOT = Path(__file__).resolve().parents[1]


def test_data7_defaults_are_loaded_from_the_hash_validated_m1_table() -> None:
    with (ROOT / "data/processed/passenger_arrivals.csv").open(newline="") as handle:
        canonical = {
            row["mode"]: int(row["passengers"])
            for row in csv.DictReader(handle)
            if row["year"] == "2025"
        }
    config = TravelConfig(mode="explicit_travel")

    assert config.annual_air_arrivals == canonical["air"]
    assert config.annual_ferry_arrivals == canonical["sea"]
    resolved = config.resolved_parameter_provenance()
    assert resolved["annual_air_arrivals"]["status"] == "observed"
    assert resolved["annual_ferry_arrivals"]["status"] == "observed"
    assert "rounded to the nearest thousand" in resolved["annual_air_arrivals"]["derivation"]


def test_data7_override_is_not_stamped_observed() -> None:
    config = TravelConfig(mode="explicit_travel", annual_air_arrivals=2_000_000)

    resolved = config.resolved_parameter_provenance()

    assert resolved["annual_air_arrivals"]["status"] == "scenario_assumption"
    assert "2000000" in resolved["annual_air_arrivals"]["derivation"]
    assert "720842" in resolved["annual_air_arrivals"]["derivation"]


def test_data7_missing_canonical_table_fails_closed(tmp_path: Path) -> None:
    config_path = tmp_path / "travel.yaml"
    config_path.write_text("mode: explicit_travel\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Milestone 1 canonical manifests"):
        load_travel_config(tmp_path, config_path)


def test_data10_resident_arrival_detection_is_assigned_to_resident_stratum() -> None:
    resident_event = {
        "date": "2025-01-06",
        "action": "arrival_test_result",
        "detected": True,
        "visitor_uid": None,
        "resident_agent_id": "resident-1",
    }
    manager = SimpleNamespace(event_log=[resident_event])
    strata = [
        {"agent_id": "resident-1", "risk_stratum": "older_resident"},
        {"agent_id": "visitor-1", "risk_stratum": "visitor_travel_exposure"},
    ]

    rows = _high_risk_epidemic_rows(
        manager,
        strata,
        [],
        date(2025, 1, 6),
        1,
    )

    detections = {row["risk_stratum"]: row["detections"] for row in rows}
    assert detections == {
        "older_resident": 1,
        "visitor_travel_exposure": 0,
    }
    assert sum(detections.values()) == 1


def test_data10_unknown_detection_subject_fails_instead_of_disappearing() -> None:
    manager = SimpleNamespace(
        event_log=[
            {
                "date": "2025-01-06",
                "action": "arrival_test_result",
                "detected": True,
                "visitor_uid": None,
                "resident_agent_id": "not-a-stratum",
            }
        ]
    )

    with pytest.raises(AssertionError, match="not in high-risk strata"):
        _high_risk_epidemic_rows(
            manager,
            [{"agent_id": "resident-1", "risk_stratum": "general_resident"}],
            [],
            date(2025, 1, 6),
            1,
        )


def test_disease10_no_online_schedule_is_explicitly_not_compared(
    m6_latent_run, m6_observation_config
) -> None:
    result = observe_latent_run(m6_latent_run, m6_observation_config)

    interface = result.diagnostics["detection_event_interface"]
    assert interface["offline_online_comparison"] == "not_compared"
    assert interface["offline_rebuild_executed"] is True


def test_disease10_disagreement_records_tri_state_before_raising(
    m6_latent_run, m6_observation_config
) -> None:
    parameters = {
        key: value.model_copy(
            update={"value": 1.0 if key.endswith("detection_probability") else value.value}
        )
        for key, value in m6_observation_config.parameters.items()
    }
    config = m6_observation_config.model_copy(update={"parameters": parameters})
    baseline = observe_latent_run(m6_latent_run, config)
    assert baseline.detection_events
    tampered = replace(baseline.detection_events[0], detection_date="2099-01-01")
    schedule = ObservationScheduleSnapshot(
        observation_events=tuple(baseline.observation_events),
        detection_events=(tampered, *baseline.detection_events[1:]),
        delivered_detection_events=baseline.detection_events,
        pending_detection_count=0,
        stream_fingerprint=baseline.diagnostics["detection_event_interface"].get(
            "stream_fingerprint", ""
        ),
    )
    # The stream fingerprint is recorded in the observation_rng block, not the
    # interface block; keep the fixture's online schedule otherwise identical.
    schedule = replace(
        schedule,
        stream_fingerprint=baseline.diagnostics["observation_rng"]["stream_fingerprint"],
    )
    online_latent = replace(m6_latent_run, observation_schedule=schedule)

    with pytest.raises(RuntimeError) as caught:
        observe_latent_run(online_latent, config)

    diagnostics = getattr(caught.value, "diagnostics", {})
    assert diagnostics["detection_event_interface"]["offline_online_comparison"] == (
        "compared_and_unequal"
    )
    assert diagnostics["detection_event_interface"]["offline_rebuild_executed"] is True


def test_disease10_event_key_declaration_is_the_scheduler_key_contract(
    m6_latent_run, m6_observation_config
) -> None:
    result = observe_latent_run(m6_latent_run, m6_observation_config)

    assert result.diagnostics["observation_rng"]["event_key_inputs"] == [
        "infection-event",
        "infected_uid",
        "infected_agent_id",
        "date",
        "source_kind",
        "route_id",
        "infector_uid",
        "infected_episode_identity_hash",
        "infector_episode_identity_hash",
    ]
