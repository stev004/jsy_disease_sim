from __future__ import annotations

import json
from dataclasses import replace
from datetime import date

import pytest

import jersey_outbreak.travel as travel_module
from jersey_outbreak.intervention_schemas import InterventionConfig, ScenarioConfig
from jersey_outbreak.travel import (
    TravelManager,
    generate_travel_episodes,
    provenance_table,
    run_travel_outbreak,
)
from jersey_outbreak.travel_artifacts import verify_travel_artifact, write_travel_artifact
from jersey_outbreak.travel_schemas import TravelConfig, TravelInterventionConfig


def _small_travel_config(**updates: object) -> TravelConfig:
    payload: dict[str, object] = {
        "mode": "explicit_travel",
        "daily_arrivals": {"2025-01-06:AIRPORT": 2},
        "visitor_fraction": 1.0,
        "returning_resident_fraction": 0.0,
        "day_visitor_fraction": 0.0,
        "staying_with_resident_fraction": 0.5,
        "party_sizes": [1],
        "party_probabilities": [1.0],
        "stay_duration_days": 1,
        "stay_duration_jitter_days": 0,
    }
    payload.update(updates)
    return TravelConfig.model_validate(payload)


def test_travel_episode_identity_and_air_ferry_separation() -> None:
    config = _small_travel_config(daily_arrivals={"2025-01-06:AIRPORT": 2, "2025-01-06:FERRY": 1})
    residents = [
        {
            "agent_id": f"resident-{index}",
            "age": 40,
            "sex": "female",
            "home_parish": "St Helier",
            "household_id": "household-1",
        }
        for index in range(5)
    ]
    households = [{"household_id": "household-1", "home_parish": "St Helier"}]
    left = generate_travel_episodes(
        config,
        seed=123,
        start_date=date(2025, 1, 6),
        duration_days=3,
        residents=residents,
        households=households,
    )
    right = generate_travel_episodes(
        config,
        seed=123,
        start_date=date(2025, 1, 6),
        duration_days=3,
        residents=residents,
        households=households,
    )
    assert left.episode_hash == right.episode_hash
    assert len(left.visitor_records) == 3
    assert {episode.entry_mode for episode in left.visitor_episodes} == {"AIRPORT", "FERRY"}
    assert not {episode.visitor_uid for episode in left.visitor_episodes} & {
        row["agent_id"] for row in residents
    }
    assert left.visitor_capacity >= 3


def test_zero_arrivals_are_a_real_noop_for_resident_outputs(
    tmp_path, m6_network, m6_base_config, m6_parameters, m6_latent_run
) -> None:
    config = _small_travel_config(mode="both", daily_arrivals={"2025-01-06:AIRPORT": 0})
    result = run_travel_outbreak(m6_network, m6_base_config, m6_parameters, config)
    assert result.travel_plan.visitor_records == ()
    assert all(row["active_visitors"] == 0 for row in result.daily_travel_population)
    assert result.daily_epidemic == m6_latent_run.daily_epidemic
    assert result.daily_route == m6_latent_run.daily_route
    assert result.daily_age == m6_latent_run.daily_age
    assert result.daily_parish == m6_latent_run.daily_parish
    assert result.transmission_events == m6_latent_run.transmission_events
    assert result.latent_outcome_hash == m6_latent_run.latent_outcome_hash
    assert not any(row["active_edges"] for row in result.daily_travel_route)
    artifact = write_travel_artifact(result, tmp_path, tmp_path / "zero-artifact")
    assert verify_travel_artifact(artifact.artifact_directory).latent_outcome_hash == (
        m6_latent_run.latent_outcome_hash
    )


def test_departure_stops_active_visitor_routes(m6_network, m6_base_config, m6_parameters) -> None:
    result = run_travel_outbreak(
        m6_network,
        m6_base_config.model_copy(update={"duration_days": 4}),
        m6_parameters,
        _small_travel_config(),
    )
    populations = {row["date"]: row for row in result.daily_travel_population}
    assert populations["2025-01-06"]["active_visitors"] == 2
    assert populations["2025-01-07"]["active_visitors"] == 0
    assert any(event["action"] == "visitor_departed" for event in result.visitor_events)
    jan7 = [row for row in result.daily_travel_route if row["date"] == "2025-01-07"]
    assert all(row["active_edges"] == 0 for row in jan7)


def test_infectious_arrival_testing_and_quarantine_are_prospective(
    m6_network, m6_base_config, m6_parameters
) -> None:
    config = _small_travel_config(
        arrival_infectious_fraction=1.0,
        interventions=TravelInterventionConfig(
            testing_probability=1.0,
            test_sensitivity=1.0,
            test_specificity=1.0,
            quarantine_positive_only=True,
            quarantine_duration_days=2,
            quarantine_adherence=1.0,
            quarantine_external_route_multiplier=0.0,
        ),
    )
    result = run_travel_outbreak(
        m6_network,
        m6_base_config.model_copy(update={"duration_days": 4}),
        m6_parameters,
        config,
    )
    administered = [
        event for event in result.visitor_events if event["action"] == "arrival_test_administered"
    ]
    scheduled = [
        event
        for event in result.visitor_events
        if event["action"] == "arrival_test_result_scheduled"
    ]
    results = [event for event in result.visitor_events if event["action"] == "arrival_test_result"]
    started = [
        event for event in result.visitor_events if event["action"] == "quarantine_activated"
    ]
    assert len(administered) == len(scheduled) == len(results) == 2
    assert all("detected" not in event for event in scheduled)
    assert all(event["detected"] for event in results)
    assert len(started) == 2
    assert all(event["time_index"] == 0 for event in started)
    assert result.diagnostics["interventions"]["prospective"] is True


def test_hashes_include_material_travel_controls() -> None:
    baseline = TravelConfig(mode="explicit_travel")
    assert baseline.config_hash != baseline.model_copy(update={"stay_duration_days": 7}).config_hash
    assert (
        baseline.config_hash != baseline.model_copy(update={"annual_air_arrivals": 1}).config_hash
    )
    assert (
        baseline.seasonality_hash
        != baseline.model_copy(
            update={
                "visitor_seasonality": baseline.visitor_seasonality.model_copy(
                    update={
                        "monthly_multipliers": (
                            0.5,
                            0.5,
                            0.5,
                            0.5,
                            0.5,
                            0.5,
                            1.5,
                            1.5,
                            1.5,
                            1.5,
                            1.5,
                            1.5,
                        )
                    }
                )
            }
        ).seasonality_hash
    )
    assert (
        baseline.intervention_hash
        != baseline.model_copy(
            update={"interventions": TravelInterventionConfig(arrival_volume_multiplier=0.5)}
        ).intervention_hash
    )


def test_travel_edge_weights_are_configurable_and_provenanced(m6_network) -> None:
    config = _small_travel_config(arrival_terminal_edge_weight=0.12)
    plan = generate_travel_episodes(
        config,
        seed=123,
        start_date=date(2025, 1, 6),
        duration_days=3,
        residents=m6_network.m2_input.residents,
        households=m6_network.m2_input.households,
    )
    manager = TravelManager(
        m6_network,
        plan,
        config,
        seed=123,
        start_date=date(2025, 1, 6),
        duration_days=3,
    )
    terminal_edges = manager.route_edges("arrival_terminal", date(2025, 1, 6))
    assert terminal_edges
    assert all(edge["weight"] == pytest.approx(0.12) for edge in terminal_edges)

    expected = {
        "arrival_terminal_edge_weight": 0.12,
        "visitor_party_edge_weight": 0.60,
        "visitor_accommodation_edge_weight": 0.55,
        "visitor_host_household_edge_weight": 0.80,
        "visitor_transit_bus_edge_weight": 0.35,
        "visitor_transit_vehicle_edge_weight": 0.25,
        "visitor_community_indoor_edge_weight": 0.35,
        "visitor_community_outdoor_edge_weight": 0.18,
    }
    resolved = config.resolved_parameter_provenance()
    compact = {row["parameter"]: row for row in provenance_table(config)}
    for name, value in expected.items():
        assert resolved[name]["value"] == value
        assert resolved[name]["status"] == "scenario_assumption"
        assert resolved[name]["sensitivity_required"] is True
        assert compact[name]["value_or_distribution"] == value
        assert compact[name]["provenance_status"] == "scenario_assumption"
        assert compact[name]["sensitivity_required"] is True

    route_specs = manager.route_view().route_specs
    assert route_specs["arrival_terminal"]["relative_weight"] == 0.12
    assert route_specs["visitor_party"]["relative_weight"] == 0.60
    assert route_specs["visitor_transit"]["relative_weight_components"] == {
        "bus": 0.35,
        "vehicle": 0.25,
    }


def test_returning_resident_absence_is_separate_from_visitor_presence(m6_network) -> None:
    config = TravelConfig(
        mode="explicit_travel",
        daily_arrivals={"2025-01-08:AIRPORT": 1},
        visitor_fraction=0.0,
        returning_resident_fraction=1.0,
        party_sizes=(1,),
        party_probabilities=(1.0,),
        stay_duration_days=3,
    )
    plan = generate_travel_episodes(
        config,
        seed=123,
        start_date=date(2025, 1, 6),
        duration_days=4,
        residents=m6_network.m2_input.residents,
        households=m6_network.m2_input.households,
    )
    assert len(plan.visitor_records) == 0
    assert plan.returning_resident_episodes[0].absence_start_date == date(2025, 1, 5)
    assert [row["resident_away"] for row in plan.daily_stream] == [1, 1, 0, 0]
    assert plan.returning_resident_episodes[0].home_household_id is not None


def test_returning_resident_is_absent_from_routes_until_return(
    m6_network, m6_base_config, m6_parameters
) -> None:
    config = TravelConfig(
        mode="explicit_travel",
        daily_arrivals={"2025-01-08:AIRPORT": 1},
        visitor_fraction=0.0,
        returning_resident_fraction=1.0,
        party_sizes=(1,),
        party_probabilities=(1.0,),
        stay_duration_days=3,
    )
    result = run_travel_outbreak(
        m6_network,
        m6_base_config.model_copy(update={"duration_days": 4}),
        m6_parameters,
        config,
    )
    assert [row["resident_away"] for row in result.daily_travel_population] == [1, 1, 0, 0]
    returned = [event for event in result.visitor_events if event["action"] == "resident_returned"]
    assert len(returned) == 1
    assert returned[0]["time_index"] == 2
    assert result.diagnostics["denominators"]["resident_attack_rate_denominator"] == 3000
    assert result.diagnostics["travel_scaling_context"]["movements_per_resident_year"] > 0
    assert all(
        (
            row["visitor_to_resident_endpoint_ratio"]
            == row["visitor_opportunity_endpoints"] / row["resident_opportunity_endpoints"]
            if row["resident_opportunity_endpoints"]
            else row["visitor_to_resident_endpoint_ratio"] is None
        )
        for row in result.daily_travel_route
    )
    assert all(row["present_infectious"] == row["infectious"] for row in result.daily_epidemic)
    assert all(
        row["resident_attack_rate"] == row["resident_cumulative_incidence_per_capita"]
        and row["visitor_attack_rate"] == row["visitor_cumulative_incidence_per_arrived"]
        for row in result.daily_epidemic
    )

    plan = generate_travel_episodes(
        config,
        seed=123,
        start_date=date(2025, 1, 6),
        duration_days=4,
        residents=m6_network.m2_input.residents,
        households=m6_network.m2_input.households,
    )
    manager = TravelManager(
        m6_network,
        plan,
        config,
        seed=123,
        start_date=date(2025, 1, 6),
        duration_days=4,
    )
    view = manager.route_view()
    away_id = str(plan.returning_resident_episodes[0].resident_agent_id)
    for when in (date(2025, 1, 6), date(2025, 1, 7)):
        for route_id in m6_network.route_specs:
            assert all(
                away_id not in {edge["p1"], edge["p2"]}
                for edge in view.route_snapshot(route_id, when).edges
            )
    manager.present_resident_ids.add(away_id)
    manager.away_resident_ids.discard(away_id)
    view._snapshot_cache.clear()
    assert any(
        away_id in {edge["p1"], edge["p2"]}
        for edge in view.route_snapshot("household", date(2025, 1, 8)).edges
    )


def test_visitor_attack_rate_denominator_matches_arrived_alias_semantics(
    m6_network, m6_base_config, m6_parameters
) -> None:
    config = _small_travel_config(daily_arrivals={"2025-01-06:AIRPORT": 1, "2025-01-08:AIRPORT": 1})
    result = run_travel_outbreak(
        m6_network,
        m6_base_config.model_copy(update={"duration_days": 4}),
        m6_parameters,
        config,
    )

    jan6 = next(row for row in result.daily_epidemic if row["date"] == "2025-01-06")
    assert len(result.travel_plan.visitor_records) == 2
    assert jan6["visitor_arrived_denominator"] == 1
    assert jan6["visitor_attack_rate"] == jan6["visitor_cumulative_incidence_per_arrived"]
    assert (
        result.diagnostics["denominators"]["visitor_attack_rate_denominator"]
        == "arrived visitor identities by date"
    )


@pytest.mark.parametrize("testing_enabled", [False, True])
def test_repeat_returning_resident_trips_reconcile_without_person_key_collision(
    monkeypatch, m6_network, m6_base_config, m6_parameters, testing_enabled
) -> None:
    config = TravelConfig(
        mode="explicit_travel",
        daily_arrivals={"2025-01-06:AIRPORT": 1, "2025-01-10:AIRPORT": 1},
        visitor_fraction=0.0,
        returning_resident_fraction=1.0,
        party_sizes=(1,),
        party_probabilities=(1.0,),
        stay_duration_days=2,
        interventions=TravelInterventionConfig(
            testing_probability=1.0 if testing_enabled else 0.0,
            test_sensitivity=1.0,
            test_specificity=1.0,
        ),
    )
    resident = next(row for row in m6_network.m2_input.residents if row["household_id"] is not None)
    household = next(
        row
        for row in m6_network.m2_input.households
        if row["household_id"] == resident["household_id"]
    )
    plan = generate_travel_episodes(
        config,
        seed=123,
        start_date=date(2025, 1, 6),
        duration_days=7,
        residents=[resident],
        households=[household],
    )
    assert len(plan.returning_resident_episodes) == 2
    assert len({row.resident_agent_id for row in plan.returning_resident_episodes}) == 1
    assert len({row.trip_id for row in plan.returning_resident_episodes}) == 2
    resident_count = len(m6_network.agent_ids)
    adjusted_stream = tuple(
        {
            **row,
            "resident_present": resident_count - row["resident_away"],
            "present_population": resident_count - row["resident_away"],
        }
        for row in plan.daily_stream
    )
    plan = replace(plan, daily_stream=adjusted_stream)
    monkeypatch.setattr(travel_module, "generate_travel_episodes", lambda *args, **kwargs: plan)

    result = run_travel_outbreak(
        m6_network,
        m6_base_config.model_copy(update={"duration_days": 7}),
        m6_parameters,
        config,
    )
    planned = [row["resident_away"] for row in result.daily_travel_population]
    realised = [row["resident_away"] for row in result.daily_travel_intervention_state]
    assert planned == realised
    returned = [row for row in result.visitor_events if row["action"] == "resident_returned"]
    assert len(returned) == 2
    assert len({row["trip_id"] for row in returned}) == 2
    administered = [
        row for row in result.visitor_events if row["action"] == "arrival_test_administered"
    ]
    assert len(administered) == (2 if testing_enabled else 0)


def test_m8_artifact_verification_detects_tampering(
    tmp_path, m6_network, m6_base_config, m6_parameters
) -> None:
    result = run_travel_outbreak(
        m6_network,
        m6_base_config.model_copy(update={"duration_days": 3}),
        m6_parameters,
        _small_travel_config(),
    )
    artifact = write_travel_artifact(result, tmp_path, tmp_path / "artifacts")
    assert (
        verify_travel_artifact(artifact.artifact_directory).artifact_id
        == artifact.manifest.artifact_id
    )
    manifest = json.loads((artifact.artifact_directory / "manifest.json").read_text())
    assert {item["path"] for item in manifest["output_artifacts"]} >= {
        "travel_episodes.parquet",
        "daily_travel_route.parquet",
        "seasonality_schedule.parquet",
    }
    path = artifact.artifact_directory / "seasonality_schedule.parquet"
    path.write_bytes(path.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_travel_artifact(artifact.artifact_directory)


def test_m7_intervention_composes_with_travel_layer(
    m6_network, m6_base_config, m6_parameters
) -> None:
    travel = _small_travel_config()
    scenario = ScenarioConfig(
        schema_version="8.0",
        scenario_id="m8-test-composed",
        scenario_version="8.0.0",
        travel=travel,
        interventions=(
            InterventionConfig(
                intervention_id="m8-community-reduction",
                type="community_reduction",
                start_date=date(2025, 1, 6),
                indoor_multiplier=0.5,
                outdoor_multiplier=0.75,
            ),
        ),
    )
    result = run_travel_outbreak(
        m6_network,
        m6_base_config.model_copy(update={"duration_days": 3}),
        m6_parameters,
        travel,
        scenario=scenario,
    )
    assert result.m7_intervention_diagnostics["intervention_ids"] == ["m8-community-reduction"]
    assert result.diagnostics["interventions"]["m7_composed"] is True
    assert result.base_generated.logical_content_hash == m6_network.logical_content_hash
    visitor_effects = [
        row
        for row in result.m7_intervention_route_effects
        if row["route_id"] in {"visitor_community_indoor", "visitor_community_outdoor"}
        and row["base_edge_count"] > 0
    ]
    assert visitor_effects
    assert all(row["mean_multiplier"] < 1.0 for row in visitor_effects)
