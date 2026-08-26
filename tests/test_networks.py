import json
from datetime import date
from pathlib import Path

import pytest

from jersey_outbreak.network_artifacts import write_network_artifact
from jersey_outbreak.network_generator import generate_networks
from jersey_outbreak.network_schemas import ROUTE_FAMILIES, NetworkGenerationConfig
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
from jersey_outbreak.starsim_adapter import (
    agent_uid_mapping,
    run_starsim_network_compatibility,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def network_inputs(tmp_path_factory: pytest.TempPathFactory):
    output = tmp_path_factory.mktemp("m4-inputs")
    population = generate_population(ROOT, PopulationGenerationConfig(mode="ci", seed=123))
    population_artifact = write_population_artifact(population, ROOT, output / "populations")
    m2_input = load_m2_population_artifact(ROOT, population_artifact.artifact_directory)
    structure = generate_structure(ROOT, StructureGenerationConfig(mode="ci", seed=123), m2_input)
    structure_artifact = write_structure_artifact(structure, ROOT, output / "structures", m2_input)
    return (
        m2_input,
        load_m3_structure_artifact(ROOT, structure_artifact.artifact_directory),
    )


@pytest.fixture(scope="module")
def generated(network_inputs):
    m2_input, m3_input = network_inputs
    return generate_networks(NetworkGenerationConfig(mode="ci", seed=123), m2_input, m3_input)


def test_network_is_deterministic_and_seed_sensitive(network_inputs) -> None:
    m2_input, m3_input = network_inputs
    config = NetworkGenerationConfig(mode="ci", seed=123)
    first = generate_networks(config, m2_input, m3_input)
    second = generate_networks(config, m2_input, m3_input)
    assert first.logical_content_hash == second.logical_content_hash
    for when in config.snapshot_dates:
        for route_id in first.route_specs:
            assert (
                first.route_snapshot(route_id, when).edges
                == second.route_snapshot(route_id, when).edges
            )

    changed = generate_networks(NetworkGenerationConfig(mode="ci", seed=999), m2_input, m3_input)
    assert changed.logical_content_hash != first.logical_content_hash
    assert changed.route_snapshot("community_indoor", config.snapshot_dates[0]).edges != (
        first.route_snapshot("community_indoor", config.snapshot_dates[0]).edges
    )


def test_edge_invariants_and_route_membership_boundaries(generated) -> None:
    valid_agents = set(generated.agent_ids)
    m2_by_agent = {row["agent_id"]: row for row in generated.m2_input.residents}
    m3_by_agent = {row["agent_id"]: row for row in generated.m3_input.resident_structure}
    class_by_agent = {row["agent_id"]: row for row in generated.m3_input.school_assignments}
    school_staff_by_agent = {row["agent_id"]: row for row in generated.school_staff_assignments}
    job_by_agent = {}
    for row in generated.m3_input.job_assignments:
        job_by_agent.setdefault(row["agent_id"], []).append(row)

    for route_id in generated.route_specs:
        for when in generated.config.snapshot_dates:
            edges = list(generated.route_snapshot(route_id, when).edges)
            pairs = [(edge["p1"], edge["p2"]) for edge in edges]
            assert all(left in valid_agents and right in valid_agents for left, right in pairs)
            assert all(left != right for left, right in pairs)
            assert len(pairs) == len(set(pairs))
            assert all(0 <= edge["weight"] <= 1 for edge in edges)

    for when in generated.config.snapshot_dates:
        for edge in generated.route_snapshot("household", when).edges:
            assert (
                m2_by_agent[edge["p1"]]["household_id"] == m2_by_agent[edge["p2"]]["household_id"]
            )
            assert m2_by_agent[edge["p1"]]["household_id"] is not None
        for edge in generated.route_snapshot("school_class", when).edges:
            if edge["p1"] in school_staff_by_agent and edge["p2"] in school_staff_by_agent:
                assert (
                    school_staff_by_agent[edge["p1"]]["class_id"]
                    == school_staff_by_agent[edge["p2"]]["class_id"]
                )
            elif edge["p1"] in school_staff_by_agent:
                assert (
                    school_staff_by_agent[edge["p1"]]["class_id"]
                    == class_by_agent[edge["p2"]]["class_id"]
                )
            elif edge["p2"] in school_staff_by_agent:
                assert (
                    school_staff_by_agent[edge["p2"]]["class_id"]
                    == class_by_agent[edge["p1"]]["class_id"]
                )
            else:
                assert (
                    class_by_agent[edge["p1"]]["class_id"] == class_by_agent[edge["p2"]]["class_id"]
                )
        for edge in generated.route_snapshot("school_cross_class", when).edges:
            left = school_staff_by_agent.get(edge["p1"], class_by_agent.get(edge["p1"]))
            right = school_staff_by_agent.get(edge["p2"], class_by_agent.get(edge["p2"]))
            assert left is not None and right is not None
            assert (left["school_id"], left["school_year"]) == (
                right["school_id"],
                right["school_year"],
            )
        for edge in generated.route_snapshot("workplace_team", when).edges:
            left_jobs = job_by_agent[edge["p1"]]
            right_jobs = job_by_agent[edge["p2"]]
            assert any(
                left_job.get("team_id") == right_job.get("team_id")
                and left_job.get("team_id") is not None
                for left_job in left_jobs
                for right_job in right_jobs
            )
        for edge in generated.route_snapshot("workplace_transient", when).edges:
            left_workplaces = {job["workplace_id"] for job in job_by_agent[edge["p1"]]}
            right_workplaces = {job["workplace_id"] for job in job_by_agent[edge["p2"]]}
            assert left_workplaces & right_workplaces
        for edge in generated.route_snapshot("care_resident", when).edges:
            assert (
                m2_by_agent[edge["p1"]]["care_setting_id"]
                == m2_by_agent[edge["p2"]]["care_setting_id"]
            )
            assert m2_by_agent[edge["p1"]]["household_id"] is None

    assert set(m3_by_agent) == valid_agents


def test_calendar_and_wfh_suppression(generated) -> None:
    monday = date(2025, 1, 6)
    saturday = date(2025, 1, 11)
    summer_monday = date(2025, 8, 11)
    assert generated.route_snapshot("school_class", monday).edges
    assert not generated.route_snapshot("school_class", summer_monday).edges
    assert generated.route_snapshot("workplace_team", monday).edges
    assert not generated.route_snapshot("workplace_team", saturday).edges
    assert not generated.route_snapshot("bus", saturday).edges

    wfh_agents = {
        row["agent_id"]
        for row in generated.m3_input.resident_structure
        if row["commute_mode"] == "work_from_home"
    }
    for route_id in ("workplace_team", "workplace_transient", "shared_vehicle", "bus"):
        endpoints = {
            endpoint
            for edge in generated.route_snapshot(route_id, monday).edges
            for endpoint in (edge["p1"], edge["p2"])
        }
        assert not endpoints & wfh_agents


def test_route_family_removal_is_independent(generated, network_inputs) -> None:
    m2_input, m3_input = network_inputs
    for disabled_family in ROUTE_FAMILIES:
        enabled = tuple(family for family in ROUTE_FAMILIES if family != disabled_family)
        reduced = generate_networks(
            NetworkGenerationConfig(
                mode="ci",
                seed=123,
                enabled_route_families=enabled,
            ),
            m2_input,
            m3_input,
        )
        assert all(spec["route_family"] != disabled_family for spec in reduced.route_specs.values())
        for route_id in reduced.route_specs:
            for when in reduced.config.snapshot_dates:
                assert (
                    reduced.route_snapshot(route_id, when).edges
                    == generated.route_snapshot(route_id, when).edges
                )


def test_starsim_mapping_and_network_only_execution(generated) -> None:
    mapping = agent_uid_mapping(generated)
    assert len(mapping) == 3000
    assert list(mapping.values()) == list(range(3000))
    compatibility = run_starsim_network_compatibility(generated, duration_days=2)
    assert compatibility["starsim_version"] == "3.5.2"
    assert compatibility["network_count"] == len(generated.route_specs)
    assert compatibility["executed_without_disease"] is True


def test_network_artifact_contains_provenance_and_selected_snapshots(
    generated, tmp_path: Path
) -> None:
    artifact = write_network_artifact(generated, ROOT, tmp_path / "networks")
    manifest = json.loads((artifact.artifact_directory / "manifest.json").read_text())
    assert manifest["diagnostics_status"] == "passed"
    assert manifest["m2_artifact_id"] == generated.m2_input.manifest.artifact_id
    assert manifest["m3_artifact_id"] == generated.m3_input.manifest.artifact_id
    assert manifest["starsim_version"] == "3.5.2"
    assert (artifact.artifact_directory / "snapshot_edges.parquet").exists()
    assert (artifact.artifact_directory / "diagnostics.md").exists()
