from __future__ import annotations

import json
from datetime import date

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from jersey_outbreak.hashing import canonical_json_bytes, sha256_bytes, sha256_file
from jersey_outbreak.intervention_schemas import (
    InterventionConfig,
    ScenarioConfig,
    TargetPopulation,
)
from jersey_outbreak.observation_scheduler import ObservationScheduler
from jersey_outbreak.travel import run_travel_outbreak
from jersey_outbreak.travel_artifacts import (
    _deserialize_intervention_event_rows,
    verify_travel_artifact,
    write_travel_artifact,
)
from jersey_outbreak.travel_schemas import TravelConfig, TravelInterventionConfig


def _all_detected(base, *, delay_days: int = 0):
    parameters = {
        key: parameter.model_copy(update={"value": 1.0})
        for key, parameter in base.parameters.items()
    }
    fixed = base.reporting_delay.model_copy(
        update={"kind": "fixed", "days": (delay_days,), "probabilities": None}
    )
    zero = fixed.model_copy(update={"days": (0,)})
    return base.model_copy(
        update={
            "observation_config_id": "m8.2-episode-identity",
            "parameters": parameters,
            "symptom_onset_delay": zero,
            "detection_delay": fixed,
            "reporting_delay": zero,
            "day_of_week_effect": (1.0,) * 7,
            "analysis_horizon_tail_days": None,
        }
    )


def _travel(*, arrivals: dict[str, int], stay_days: int, delay_days: int) -> TravelConfig:
    return TravelConfig(
        mode="explicit_travel",
        daily_arrivals=arrivals,
        visitor_fraction=1.0,
        returning_resident_fraction=0.0,
        day_visitor_fraction=0.0,
        staying_with_resident_fraction=0.0,
        stay_duration_days=stay_days,
        stay_duration_jitter_days=0,
        party_sizes=(1,),
        party_probabilities=(1.0,),
        arrival_infectious_fraction=1.0,
        interventions=TravelInterventionConfig(
            testing_probability=1.0,
            test_sensitivity=1.0,
            test_specificity=1.0,
            test_result_delay_days=delay_days,
            quarantine_positive_only=True,
            quarantine_duration_days=3,
            quarantine_adherence=1.0,
            quarantine_external_route_multiplier=0.0,
        ),
    )


def test_observation_and_detection_keep_episode_identity_across_slot_reuse(
    m6_observation_config,
) -> None:
    config = _all_detected(m6_observation_config, delay_days=2)
    scheduler = ObservationScheduler(
        latent_seed=123,
        start_date=date(2025, 1, 6),
        config=config,
        agent_id_by_uid={3000: "visitor-slot-000000", 0: "resident-0"},
        resident_by_agent_id={
            "visitor-A": {"age": 35, "home_parish": "St Helier", "population_kind": "visitor"},
            "resident-0": {"age": 65, "home_parish": "St Saviour"},
        },
    )
    latent = {
        "infected_uid": 3000,
        "infected_agent_id": "visitor-A",
        "infected_actor_type": "visitor",
        "infected_runtime_slot_uid": 3000,
        "infected_trip_id": "trip-A",
        "infected_travel_party_id": "party-A",
        "infected_episode_identity_hash": "hash-A",
        "date": "2025-01-06",
        "source_kind": "local",
        "route_id": "visitor_party",
    }
    observation = scheduler.schedule_infection(latent)
    scheduler.agent_id_by_uid[3000] = "visitor-B"
    assert scheduler.deliver_due(1) == ()
    detection = scheduler.deliver_due(2)[0]
    expected = {
        "infected_agent_id": "visitor-A",
        "infected_trip_id": "trip-A",
        "infected_travel_party_id": "party-A",
        "infected_episode_identity_hash": "hash-A",
    }
    assert {key: observation[key] for key in expected} == expected
    assert {key: getattr(detection, key) for key in expected} == expected
    assert detection.infected_actor_type == "visitor"
    assert detection.infected_runtime_uid == 3000

    resident = scheduler.schedule_infection(
        {
            "infected_uid": 0,
            "infected_agent_id": "resident-0",
            "date": "2025-01-06",
            "source_kind": "seeded",
            "route_id": "seeded",
        }
    )
    assert resident["infected_agent_id"] == "resident-0"
    assert resident["infected_actor_type"] == "resident"
    assert resident["infected_trip_id"] is None


def test_departed_test_result_is_historical_and_cannot_touch_reused_slot(
    m6_network, m6_base_config, m6_parameters
) -> None:
    result = run_travel_outbreak(
        m6_network,
        m6_base_config.model_copy(update={"duration_days": 4}),
        m6_parameters,
        _travel(
            arrivals={"2025-01-06:AIRPORT": 1, "2025-01-07:AIRPORT": 1},
            stay_days=1,
            delay_days=2,
        ),
    )
    arrivals = [row for row in result.visitor_events if row["action"] == "visitor_arrived"]
    assert len(arrivals) == 2
    assert arrivals[0]["runtime_slot_uid"] == arrivals[1]["runtime_slot_uid"]
    historical = [
        row
        for row in result.visitor_events
        if row["action"] == "test_result_available_after_departure"
    ]
    assert len(historical) == 2
    assert {row["visitor_uid"] for row in historical} == {row["visitor_uid"] for row in arrivals}
    assert all(row["detected"] and not row["actionable"] for row in historical)
    assert all(not row["episode_active"] for row in historical)
    assert not any(
        row["action"] in {"arrival_test_result", "quarantine_activated"}
        for row in result.visitor_events
    )
    assert all(row["episode_identity_hash"] for row in historical)


@pytest.mark.parametrize("delay_days", [0, 1])
def test_visitor_result_before_or_on_final_active_timestep_remains_actionable(
    delay_days, m6_network, m6_base_config, m6_parameters
) -> None:
    result = run_travel_outbreak(
        m6_network,
        m6_base_config.model_copy(update={"duration_days": 3}),
        m6_parameters,
        _travel(
            arrivals={"2025-01-06:AIRPORT": 1},
            stay_days=2,
            delay_days=delay_days,
        ),
    )
    due = [row for row in result.visitor_events if row["action"] == "arrival_test_result"]
    assert len(due) == 1
    assert due[0]["time_index"] == delay_days
    assert due[0]["episode_active"] and due[0]["actionable"]
    assert any(row["action"] == "quarantine_activated" for row in result.visitor_events)


def test_returning_resident_delayed_result_remains_actionable(
    m6_network, m6_base_config, m6_parameters
) -> None:
    travel = TravelConfig(
        mode="explicit_travel",
        daily_arrivals={"2025-01-06:AIRPORT": 1},
        visitor_fraction=0.0,
        returning_resident_fraction=1.0,
        party_sizes=(1,),
        party_probabilities=(1.0,),
        returning_resident_external_acquisition_probability=1.0,
        interventions=TravelInterventionConfig(
            testing_probability=1.0,
            test_sensitivity=1.0,
            test_specificity=1.0,
            test_result_delay_days=2,
            quarantine_positive_only=True,
            quarantine_duration_days=2,
            quarantine_adherence=1.0,
        ),
    )
    result = run_travel_outbreak(
        m6_network,
        m6_base_config.model_copy(update={"duration_days": 4}),
        m6_parameters,
        travel,
    )
    due = [row for row in result.visitor_events if row["action"] == "arrival_test_result"]
    assert len(due) == 1
    assert due[0]["resident_or_visitor_status"] == "resident"
    assert due[0]["time_index"] == 2
    assert due[0]["episode_active"] and due[0]["actionable"] and due[0]["detected"]


def test_combined_m7_m8_event_states_round_trip_and_logical_tamper_fails(
    tmp_path, m6_network, m6_base_config, m6_parameters, m6_observation_config
) -> None:
    travel = _travel(
        arrivals={"2025-01-06:AIRPORT": 2},
        stay_days=3,
        delay_days=0,
    ).model_copy(
        update={
            "interventions": TravelInterventionConfig(
                traveller_vaccination_coverage=1.0,
                traveller_vaccination_efficacy=0.25,
            )
        }
    )
    scenario = ScenarioConfig(
        schema_version="8.0",
        scenario_id="m8.2-combined-vaccination",
        scenario_version="8.2.0",
        start_date=date(2025, 1, 6),
        duration_days=3,
        travel=travel,
        interventions=(
            InterventionConfig(
                intervention_id="m7-resident-vaccination",
                type="vaccination",
                start_date=date(2025, 1, 6),
                target=TargetPopulation(age_bands=("65+",)),
                coverage_target=1.0,
                rollout_rate=1.0,
                protection_delay_days=1,
                efficacy_susceptibility=0.5,
            ),
        ),
    )
    observation = _all_detected(m6_observation_config)
    result = run_travel_outbreak(
        m6_network,
        m6_base_config.model_copy(update={"duration_days": 3}),
        m6_parameters,
        travel,
        observation_config=observation,
        scenario=scenario,
    )
    artifact = write_travel_artifact(result, tmp_path, tmp_path / "combined-artifacts")
    manifest = verify_travel_artifact(artifact.artifact_directory)
    assert json.loads(
        (artifact.artifact_directory / "scenario_config.json").read_text()
    ) == scenario.model_dump(mode="json")
    assert manifest.m7_scenario_hash == scenario.config_hash
    assert manifest.observation_config_hash == sha256_bytes(
        canonical_json_bytes(observation.model_dump(mode="json"))
    )
    table_path = artifact.artifact_directory / "travel_intervention_events.parquet"
    serialized = pq.read_table(table_path).to_pylist()
    state_values = [row["new_state_json"] for row in serialized if row["new_state_json"]]
    assert any(value.startswith("{") for value in state_values)
    assert "true" in state_values
    reconstructed = _deserialize_intervention_event_rows(serialized)
    reconstructed_states = [row["new_state"] for row in reconstructed if "new_state" in row]
    assert any(isinstance(value, dict) for value in reconstructed_states)
    assert any(isinstance(value, bool) for value in reconstructed_states)
    assert result.observation_events
    assert all(row["infected_agent_id"] for row in result.observation_events)

    table = pq.read_table(table_path)
    tampered = table.to_pylist()
    target = next(row for row in tampered if row["new_state_json"] == "true")
    target["new_state_json"] = "false"
    pq.write_table(pa.Table.from_pylist(tampered, schema=table.schema), table_path)
    manifest_path = artifact.artifact_directory / "manifest.json"
    payload = json.loads(manifest_path.read_text())
    record = next(row for row in payload["output_artifacts"] if row["path"] == table_path.name)
    record["sha256"] = sha256_file(table_path)
    record["size_bytes"] = table_path.stat().st_size
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match="latent outcome logical hash mismatch"):
        verify_travel_artifact(artifact.artifact_directory)
