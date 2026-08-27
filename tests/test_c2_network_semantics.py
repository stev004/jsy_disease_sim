from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
import pytest

from jersey_outbreak.network_generator import generate_networks
from jersey_outbreak.network_schemas import NetworkGenerationConfig
from jersey_outbreak.population_artifacts import write_population_artifact
from jersey_outbreak.population_generator import generate_population
from jersey_outbreak.population_schemas import PopulationGenerationConfig
from jersey_outbreak.population_structure_artifacts import (
    load_m2_population_artifact,
    load_m3_structure_artifact,
    write_structure_artifact,
)
from jersey_outbreak.population_structure_generator import generate_structure
from jersey_outbreak.population_structure_schemas import StructureGenerationConfig
from jersey_outbreak.respiratory import RespiratorySEIRS

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def c2_inputs(tmp_path_factory: pytest.TempPathFactory):
    output = tmp_path_factory.mktemp("c2-inputs")
    population = generate_population(ROOT, PopulationGenerationConfig(mode="ci", seed=123))
    population_artifact = write_population_artifact(population, ROOT, output / "populations")
    m2_input = load_m2_population_artifact(ROOT, population_artifact.artifact_directory)
    structure = generate_structure(ROOT, StructureGenerationConfig(mode="ci", seed=123), m2_input)
    structure_artifact = write_structure_artifact(structure, ROOT, output / "structures", m2_input)
    return m2_input, load_m3_structure_artifact(ROOT, structure_artifact.artifact_directory)


@pytest.fixture(scope="module")
def c2_network(c2_inputs):
    m2_input, m3_input = c2_inputs
    return generate_networks(NetworkGenerationConfig(mode="ci", seed=123), m2_input, m3_input)


def _pairs(network, route_id: str, when: date) -> set[tuple[str, str]]:
    return {(edge["p1"], edge["p2"]) for edge in network.route_snapshot(route_id, when).edges}


def test_nested_school_and_workplace_routes_are_exclusive(c2_network) -> None:
    when = date(2025, 1, 6)
    assert not _pairs(c2_network, "school_class", when) & _pairs(
        c2_network, "school_cross_class", when
    )
    assert not _pairs(c2_network, "workplace_team", when) & _pairs(
        c2_network, "workplace_transient", when
    )
    forbidden = [
        row
        for row in c2_network.diagnostics["cross_route"]["route_overlap_matrix"]
        if row["policy"] == "FORBIDDEN"
    ]
    assert forbidden
    assert all(
        row["overlapping_agent_pairs"] == 0 and row["status"] == "passed" for row in forbidden
    )


def test_school_calendar_uses_term_and_holiday_boundaries(c2_network) -> None:
    assert c2_network.route_snapshot("school_class", date(2025, 2, 17)).edges == ()
    assert c2_network.route_snapshot("school_cross_class", date(2025, 2, 21)).edges == ()
    assert c2_network.route_snapshot("school_class", date(2025, 2, 24)).edges
    assert c2_network.route_snapshot("school_class", date(2025, 8, 11)).edges == ()
    provenance = c2_network.diagnostics["calendars"]["school_calendar_provenance"]
    assert provenance["source_id"] == "states_assembly_r119_2024_school_terms"
    assert len(provenance["source_sha256"]) == 64


def test_shared_vehicle_is_bounded_and_excludes_unsupported_car_commuters(c2_network) -> None:
    memberships: dict[str, set[str]] = defaultdict(set)
    for row in c2_network.route_memberships["shared_vehicle"]:
        memberships[row["group_id"]].add(row["agent_id"])
    assert memberships
    assert all(
        2 <= len(group) <= c2_network.config.shared_vehicle_capacity
        for group in memberships.values()
    )
    participants = set().union(*memberships.values())
    m3_by_agent = {row["agent_id"]: row for row in c2_network.m3_input.resident_structure}
    assert all(m3_by_agent[agent_id]["commute_mode"] == "car" for agent_id in participants)
    car_commuters = {
        agent_id for agent_id, row in m3_by_agent.items() if row["commute_mode"] == "car"
    }
    diagnostics = c2_network.diagnostics["cross_route"]["shared_vehicle"]
    assert diagnostics["shared_vehicle_participants"] == len(participants)
    assert diagnostics["unmatched_car_commuters"] == len(car_commuters - participants)
    assert diagnostics["car_alone_commuters"] == diagnostics["unmatched_car_commuters"]
    assert diagnostics["non_household_shared_rides"] == 0


def test_shared_vehicle_switch_removes_only_that_route(c2_inputs, c2_network) -> None:
    m2_input, m3_input = c2_inputs
    disabled = generate_networks(
        NetworkGenerationConfig(mode="ci", seed=123, shared_vehicle_enabled=False),
        m2_input,
        m3_input,
    )
    assert "shared_vehicle" not in disabled.route_specs
    when = date(2025, 1, 6)
    for route_id in c2_network.route_specs:
        if route_id != "shared_vehicle":
            assert (
                c2_network.route_snapshot(route_id, when).edges
                == disabled.route_snapshot(route_id, when).edges
            )


def test_community_mixing_has_cross_age_edges_and_configured_persistence(c2_network) -> None:
    m2_by_agent = {row["agent_id"]: row for row in c2_network.m2_input.residents}
    edges = c2_network.route_snapshot("community_indoor", date(2025, 1, 6)).edges
    child_adult = sum(
        min(m2_by_agent[edge["p1"]]["age"], m2_by_agent[edge["p2"]]["age"]) < 18
        and max(m2_by_agent[edge["p1"]]["age"], m2_by_agent[edge["p2"]]["age"]) >= 18
        for edge in edges
    )
    adult_older = sum(
        18
        <= min(m2_by_agent[edge["p1"]]["age"], m2_by_agent[edge["p2"]]["age"])
        < 65
        <= max(m2_by_agent[edge["p1"]]["age"], m2_by_agent[edge["p2"]]["age"])
        and max(m2_by_agent[edge["p1"]]["age"], m2_by_agent[edge["p2"]]["age"]) >= 65
        for edge in edges
    )
    assert child_adult > 0
    assert adult_older > 0
    for route_id, minimum in (("community_indoor", 0.25), ("community_outdoor", 0.15)):
        diagnostic = c2_network.diagnostics["routes"][route_id]
        assert min(diagnostic["cross_day_jaccard"]) >= minimum
        assert max(diagnostic["new_edge_rate"]) < 1.0
        assert diagnostic["age_mixing_matrix"]["0-4"]["18-34"] > 0


def _permuted_attribution(
    order: tuple[str, str], route_betas: dict[str, float] | None = None
) -> tuple[tuple[int, ...], dict[int, dict]]:
    import starsim as ss

    class FixedNetwork(ss.Network):
        def step(self):
            return None

    networks = [
        FixedNetwork(
            name=route_id,
            p1=ss.uids(np.array([0], dtype=np.int64)),
            p2=ss.uids(np.array([1], dtype=np.int64)),
            beta=np.ones(1),
            label=route_id,
        )
        for route_id in order
    ]
    disease = RespiratorySEIRS(
        route_betas=route_betas or {"route_a": 0.8, "route_b": 0.4},
        initial_seed_count=0,
        waning_enabled=False,
    )
    sim = ss.Sim(
        n_agents=3,
        start="2025-01-06",
        stop="2025-01-08",
        dt=ss.days(1),
        rand_seed=123,
        networks=networks,
        diseases=disease,
        verbose=0,
        copy_inputs=False,
    )
    sim.init()
    disease.infected[0] = True
    disease.susceptible[1] = True
    disease.susceptible[2] = True
    cases, sources, _network_indices = disease._order_invariant_infect()
    assert np.array_equal(sources, np.array([0], dtype=np.int64))
    return tuple(int(case) for case in cases), disease._last_attribution_evidence.copy()


def test_route_order_permutation_preserves_infection_and_attribution() -> None:
    first_cases, first_evidence = _permuted_attribution(("route_a", "route_b"))
    second_cases, second_evidence = _permuted_attribution(("route_b", "route_a"))
    assert first_cases == second_cases == (1,)
    assert first_evidence[1] == second_evidence[1]
    assert first_evidence[1]["successful_candidate_routes"] == ["route_a", "route_b"]
    assert first_evidence[1]["successful_candidate_edge_count"] == 2
    assert first_evidence[1]["attributed_route_id"] == "route_a"
    assert first_evidence[1]["successful_candidate_route_count"] == 2

    reverse_first_cases, reverse_first_evidence = _permuted_attribution(
        ("route_a", "route_b"), {"route_a": 0.4, "route_b": 0.8}
    )
    reverse_second_cases, reverse_second_evidence = _permuted_attribution(
        ("route_b", "route_a"), {"route_a": 0.4, "route_b": 0.8}
    )
    assert reverse_first_cases == reverse_second_cases == (1,)
    assert reverse_first_evidence[1] == reverse_second_evidence[1]
    assert reverse_first_evidence[1]["attributed_route_id"] == "route_b"
