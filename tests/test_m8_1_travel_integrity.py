from __future__ import annotations

import json
from calendar import monthrange
from collections import defaultdict
from datetime import date

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from jersey_outbreak.hashing import sha256_file
from jersey_outbreak.travel import (
    TravelManager,
    benchmark_travel_generation,
    generate_travel_episodes,
    run_travel_outbreak,
)
from jersey_outbreak.travel_artifacts import verify_travel_artifact, write_travel_artifact
from jersey_outbreak.travel_schemas import (
    SeasonalityProfile,
    TravelConfig,
    TravelInterventionConfig,
)


def _travel(**updates: object) -> TravelConfig:
    payload: dict[str, object] = {
        "mode": "explicit_travel",
        "daily_arrivals": {"2025-01-06:AIRPORT": 3, "2025-01-08:AIRPORT": 2},
        "visitor_fraction": 1.0,
        "returning_resident_fraction": 0.0,
        "day_visitor_fraction": 0.0,
        "staying_with_resident_fraction": 0.0,
        "stay_duration_days": 1,
        "stay_duration_jitter_days": 0,
        "party_sizes": [1],
        "party_probabilities": [1.0],
    }
    payload.update(updates)
    return TravelConfig.model_validate(payload)


@pytest.fixture(scope="module")
def reuse_result(m6_network, m6_base_config, m6_parameters):
    return run_travel_outbreak(
        m6_network,
        m6_base_config.model_copy(update={"duration_days": 4}),
        m6_parameters,
        _travel(
            local_transport_probabilities={
                "BUS": 0.0,
                "PRIVATE_RENTAL_CAR": 0.0,
                "TAXI_RIDE": 1.0,
                "HOST_PICKUP": 0.0,
                "WALKING_OTHER": 0.0,
            }
        ),
    )


def test_source_scale_reconciliation_and_day_weighted_seasonality() -> None:
    neutral = TravelConfig(mode="explicit_travel", stream_scale=1.0)
    shaped = neutral.model_copy(
        update={
            "visitor_seasonality": SeasonalityProfile(
                profile_id="synthetic-shaped",
                monthly_multipliers=(0.5, 0.5, 0.7, 0.8, 1.0, 1.3, 1.7, 1.7, 1.3, 1.0, 0.7, 0.5),
            )
        }
    )
    neutral_result = benchmark_travel_generation(neutral)
    shaped_result = benchmark_travel_generation(shaped)
    expected = {"AIRPORT": 720_842, "FERRY": 196_623, "TOTAL": 917_465}
    assert neutral_result["simulated_movements"] == expected
    assert shaped_result["simulated_movements"] == expected
    assert neutral_result["reconciliation_error"] == 0
    weighted = sum(
        shaped.visitor_seasonality.multiplier(date(2025, month, day))
        for month in range(1, 13)
        for day in range(1, monthrange(2025, month)[1] + 1)
    )
    assert weighted == pytest.approx(365.0)


def test_person_level_split_is_not_changed_by_party_grouping(m6_network) -> None:
    config = _travel(
        daily_arrivals={"2025-01-06:AIRPORT": 1000},
        visitor_fraction=0.9,
        returning_resident_fraction=0.1,
        party_sizes=(1, 2, 4, 6),
        party_probabilities=(0.1, 0.2, 0.4, 0.3),
        stay_duration_days=2,
    )
    plan = generate_travel_episodes(
        config,
        seed=123,
        start_date=date(2025, 1, 6),
        duration_days=1,
        residents=m6_network.m2_input.residents,
        households=m6_network.m2_input.households,
    )
    assert len(plan.episodes) == 1000
    assert len(plan.returning_resident_episodes) == 100
    assert plan.reconciliation["returning_resident_person_fraction"] == pytest.approx(0.1)
    types_by_party: dict[str, set[str]] = defaultdict(set)
    for episode in plan.episodes:
        types_by_party[episode.travel_party_id].add(
            "resident" if episode.resident_agent_id is not None else "visitor"
        )
    assert all(len(types) == 1 for types in types_by_party.values())


def test_slot_reuse_keeps_event_time_identity_and_resets_state(reuse_result) -> None:
    arrivals = [
        event for event in reuse_result.visitor_events if event["action"] == "visitor_arrived"
    ]
    by_slot: dict[int, list[dict[str, object]]] = defaultdict(list)
    for event in arrivals:
        by_slot[int(event["runtime_slot_uid"])].append(event)
    reused = next(events for events in by_slot.values() if len(events) > 1)
    assert len({event["visitor_uid"] for event in reused}) == len(reused)
    assert len({event["trip_id"] for event in reused}) == len(reused)
    assert len({event["travel_party_id"] for event in reused}) == len(reused)
    assert len({event["episode_identity_hash"] for event in reused}) == len(reused)
    assert all(event["active_age"] > 0 for event in arrivals)
    resets = [
        event for event in reuse_result.visitor_events if event["action"] == "visitor_slot_reset"
    ]
    assert resets
    assert all(
        not event["alive"]
        and not event["susceptible"]
        and not event["exposed"]
        and not event["infectious"]
        and not event["recovered"]
        and event["age"] == 0
        and event["rel_sus"] == 1
        and event["rel_trans"] == 1
        for event in resets
    )
    audit = reuse_result.diagnostics["identity"]["inactive_slot_audit"]
    assert all(
        audit[key]
        for key in (
            "alive_false",
            "disease_states_false",
            "timers_nan",
            "modifiers_neutral",
            "excluded_from_auids",
        )
    )


def test_taxi_units_are_bounded_and_exact_edges_reconstruct(reuse_result) -> None:
    taxi_edges = [
        row
        for row in reuse_result.temporary_edges
        if row["route_id"] == "visitor_transit" and row["transport_type"] == "TAXI_RIDE"
    ]
    assert taxi_edges
    endpoints_by_unit: dict[str, set[int]] = defaultdict(set)
    for edge in taxi_edges:
        unit = str(edge["transport_unit_id"])
        endpoints_by_unit[unit].update(
            (int(edge["p1_runtime_slot_uid"]), int(edge["p2_runtime_slot_uid"]))
        )
    assert max(map(len, endpoints_by_unit.values())) <= reuse_result.travel_config.taxi_capacity
    assert reuse_result.temporary_network_hash
    assert all(row["episode_identity_hash"] for row in reuse_result.travel_episodes)


def test_host_household_route_never_duplicates_resident_household_edges(m6_network) -> None:
    config = _travel(
        daily_arrivals={"2025-01-06:AIRPORT": 4},
        staying_with_resident_fraction=1.0,
    )
    plan = generate_travel_episodes(
        config,
        seed=123,
        start_date=date(2025, 1, 6),
        duration_days=1,
        residents=m6_network.m2_input.residents,
        households=m6_network.m2_input.households,
    )
    manager = TravelManager(
        m6_network, plan, config, seed=123, start_date=date(2025, 1, 6), duration_days=1
    )
    edges = manager.route_edges("visitor_host_household", date(2025, 1, 6))
    assert edges
    assert all(
        str(edge["p1"]).startswith("visitor-slot-") or str(edge["p2"]).startswith("visitor-slot-")
        for edge in edges
    )


def test_all_optional_contact_zero_boundaries_are_exact(m6_network) -> None:
    config = _travel(
        terminal_mixing_contacts=0,
        visitor_transit_contacts=0,
        visitor_community_contacts=0,
        visitor_accommodation_contacts=0,
        visitor_party_contacts=0,
    )
    plan = generate_travel_episodes(
        config,
        seed=123,
        start_date=date(2025, 1, 6),
        duration_days=1,
        residents=m6_network.m2_input.residents,
        households=m6_network.m2_input.households,
    )
    manager = TravelManager(
        m6_network, plan, config, seed=123, start_date=date(2025, 1, 6), duration_days=1
    )
    for route in (
        "arrival_terminal",
        "visitor_party",
        "visitor_accommodation",
        "visitor_transit",
        "visitor_community_indoor",
        "visitor_community_outdoor",
    ):
        assert manager.route_edges(route, date(2025, 1, 6)) == []


def test_delayed_testing_and_all_arrival_quarantine_cover_resident_and_visitor(
    m6_network, m6_base_config, m6_parameters
) -> None:
    controls = TravelInterventionConfig(
        testing_probability=1.0,
        test_sensitivity=1.0,
        test_specificity=1.0,
        test_result_delay_days=1,
        quarantine_positive_only=False,
        quarantine_all_arrivals=True,
        quarantine_duration_days=2,
        quarantine_adherence=1.0,
    )
    config = _travel(
        daily_arrivals={"2025-01-07:AIRPORT": 2},
        visitor_fraction=0.5,
        returning_resident_fraction=0.5,
        stay_duration_days=2,
        arrival_infectious_fraction=1.0,
        returning_resident_external_acquisition_probability=1.0,
        interventions=controls,
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
    quarantined = [
        event for event in result.visitor_events if event["action"] == "quarantine_activated"
    ]
    released = [
        event for event in result.visitor_events if event["action"] == "quarantine_released"
    ]
    assert {event["resident_or_visitor_status"] for event in administered} == {
        "resident",
        "visitor",
    }
    assert all("detected" not in event for event in scheduled)
    assert all(event["time_index"] == 2 and event["detected"] for event in results)
    assert len(quarantined) == 2
    assert all(event["time_index"] == 1 for event in quarantined)
    assert len(released) == 2
    assert all(event["time_index"] == 3 for event in released)


def test_explicit_departure_mismatch_is_never_silent(m6_network) -> None:
    config = _travel(
        daily_arrivals={"2025-01-06:AIRPORT": 1},
        daily_departures={"2025-01-07:AIRPORT": 2},
        stay_duration_days=4,
    )
    with pytest.raises(ValueError, match="departure schedule reconciliation failed"):
        generate_travel_episodes(
            config,
            seed=123,
            start_date=date(2025, 1, 6),
            duration_days=3,
            residents=m6_network.m2_input.residents,
            households=m6_network.m2_input.households,
        )


def test_logical_tamper_fails_even_if_raw_checksum_is_updated(tmp_path, reuse_result) -> None:
    artifact = write_travel_artifact(reuse_result, tmp_path, tmp_path / "artifacts")
    path = artifact.artifact_directory / "travel_episodes.parquet"
    rows = pq.read_table(path).to_pylist()
    rows[0]["trip_id"] = "tampered-trip"
    pq.write_table(pa.Table.from_pylist(rows), path)
    manifest_path = artifact.artifact_directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    record = next(item for item in manifest["output_artifacts"] if item["path"] == path.name)
    record["sha256"] = sha256_file(path)
    record["size_bytes"] = path.stat().st_size
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match="episode logical hash mismatch"):
        verify_travel_artifact(artifact.artifact_directory)


def test_actual_transmissions_retain_all_four_event_time_directions(
    m6_network, m6_base_config, m6_parameters
) -> None:
    config = _travel(
        daily_arrivals={"2025-01-06:AIRPORT": 120, "2025-01-08:AIRPORT": 120},
        arrival_infectious_fraction=0.5,
        stay_duration_days=1,
        party_sizes=(10,),
        party_probabilities=(1.0,),
        terminal_mixing_contacts=20,
        visitor_party_contacts=9,
        visitor_community_contacts=20,
        visitor_community_indoor_probability=1.0,
        visitor_community_outdoor_probability=1.0,
    )
    run_config = m6_base_config.model_copy(
        update={
            "duration_days": 4,
            "beta": 1.0,
            "initial_seed_count": 800,
            "import_schedule": {},
            "import_rate_per_day": 0.0,
        }
    )
    result = run_travel_outbreak(m6_network, run_config, m6_parameters, config)
    susceptible_result = run_travel_outbreak(
        m6_network,
        run_config,
        m6_parameters,
        config.model_copy(update={"arrival_infectious_fraction": 0.0}),
    )
    events = [
        event
        for run in (result, susceptible_result)
        for event in run.transmission_events
        if event["source_kind"] == "local"
    ]
    directions = {event["transmission_direction"] for event in events}
    assert {
        "resident_to_resident",
        "resident_to_visitor",
        "visitor_to_resident",
        "visitor_to_visitor",
    } <= directions
    for event in events:
        assert event["infected_runtime_slot_uid"] == event["infected_uid"]
        assert "successful_candidate_hazards" in event
        if event["infected_population"] == "visitor":
            assert event["infected_trip_id"]
            assert event["infected_travel_party_id"]
            assert event["infected_episode_identity_hash"]
        if event["infector_population"] == "visitor":
            assert event["infector_trip_id"]
            assert event["infector_travel_party_id"]
            assert event["infector_episode_identity_hash"]
    visitor_actors_by_slot_ti: dict[int, dict[int, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    for event in result.transmission_events:
        for prefix in ("infected", "infector"):
            if event.get(f"{prefix}_population") != "visitor":
                continue
            visitor_actors_by_slot_ti[int(event[f"{prefix}_runtime_slot_uid"])][
                int(event["time_index"])
            ].add(str(event[f"{prefix}_resident_or_visitor_id"]))
    reused_event_slots = [
        by_ti for by_ti in visitor_actors_by_slot_ti.values() if 0 in by_ti and 2 in by_ti
    ]
    assert reused_event_slots
    assert all(by_ti[0].isdisjoint(by_ti[2]) for by_ti in reused_event_slots)
