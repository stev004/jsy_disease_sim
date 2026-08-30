import json
import statistics
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from jersey_outbreak.network_artifacts import write_network_artifact
from jersey_outbreak.network_generator import (
    CONTACT_ACTIVITY_ROUTES,
    _activity_participation_probabilities,
    _persistent_contact_activity,
    generate_networks,
)
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
    build_starsim_sim,
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


def test_zero_activity_cv_is_exact_m11b_projection(network_inputs) -> None:
    m2_input, m3_input = network_inputs
    implicit = generate_networks(NetworkGenerationConfig(mode="ci", seed=123), m2_input, m3_input)
    explicit = generate_networks(
        NetworkGenerationConfig(mode="ci", seed=123, activity_cv=0.0),
        m2_input,
        m3_input,
    )
    assert implicit.logical_content_hash == explicit.logical_content_hash
    assert implicit.route_specs == explicit.route_specs
    for when in implicit.config.snapshot_dates:
        assert implicit.snapshot(when) == explicit.snapshot(when)
    diagnostic = explicit.diagnostics["contact_activity"]
    assert diagnostic["zero_cv_exact_bypass"] is True
    assert diagnostic["approved_routes"] == list(CONTACT_ACTIVITY_ROUTES)
    assert diagnostic["realised_mean"] == 1.0
    assert diagnostic["realised_cv"] == 0.0


def test_synthetic_contact_activity_moments_and_route_scope(network_inputs, generated) -> None:
    values = [
        _persistent_contact_activity(20260830, f"fixture-{index}", 0.5, "1.0")
        for index in range(10_000)
    ]
    mean = statistics.fmean(values)
    cv = statistics.pstdev(values) / mean
    assert mean == pytest.approx(1.0, rel=0.02)
    assert cv == pytest.approx(0.5, rel=0.03)
    assert _persistent_contact_activity(123, "person-1", 0.5, "1.0") == (
        _persistent_contact_activity(123, "person-1", 0.5, "1.0")
    )
    fixture_config = NetworkGenerationConfig(mode="ci", seed=20260830, activity_cv=0.5)
    probabilities = _activity_participation_probabilities(
        (f"fixture-{index}" for index in range(100)),
        41.25,
        config=fixture_config,
    )
    assert sum(probabilities.values()) == pytest.approx(41.25, abs=1e-10)
    assert all(0.0 <= probability <= 1.0 for probability in probabilities.values())

    m2_input, m3_input = network_inputs
    sensitivity = generate_networks(
        NetworkGenerationConfig(mode="ci", seed=123, activity_cv=0.5),
        m2_input,
        m3_input,
    )
    assert sensitivity.config.community_age_mixing == generated.config.community_age_mixing
    assert sensitivity.config.activity_cv == 0.5
    assert NetworkGenerationConfig(mode="ci", seed=123).activity_cv == 0.0
    school_staff = {row["agent_id"] for row in generated.school_staff_assignments}
    for when in generated.config.snapshot_dates:
        assert sensitivity.route_snapshot("bus", when) == generated.route_snapshot("bus", when)
        baseline_staff_edges = {
            (edge["p1"], edge["p2"])
            for edge in generated.route_snapshot("school_cross_class", when).edges
            if {edge["p1"], edge["p2"]} & school_staff
        }
        sensitivity_staff_edges = {
            (edge["p1"], edge["p2"])
            for edge in sensitivity.route_snapshot("school_cross_class", when).edges
            if {edge["p1"], edge["p2"]} & school_staff
        }
        assert sensitivity_staff_edges == baseline_staff_edges
    assert sensitivity.route_snapshot(
        "community_indoor", sensitivity.config.snapshot_dates[0]
    ) != generated.route_snapshot("community_indoor", generated.config.snapshot_dates[0])
    diagnostic = sensitivity.diagnostics["contact_activity"]
    assert diagnostic["application"] == "participation_once"
    activity_provenance = diagnostic["provenance"]["activity_cv"]
    assert activity_provenance["value"] == 0.5
    assert activity_provenance["status"] == "scenario_assumption"
    assert activity_provenance["role"] == "structural_assumption"
    assert activity_provenance["sensitivity_required"] is True


def test_full_mode_contract_excludes_only_care_and_medical_from_community(
    network_inputs,
) -> None:
    m2_input, m3_input = network_inputs
    full_m2 = replace(
        m2_input,
        manifest=m2_input.manifest.model_copy(update={"mode": "full"}),
    )
    full_m3 = replace(
        m3_input,
        manifest=m3_input.manifest.model_copy(update={"mode": "full"}),
    )
    bounded_full = generate_networks(
        NetworkGenerationConfig(mode="full", seed=123), full_m2, full_m3
    )
    setting_type_by_id = {
        row["setting_id"]: row["setting_type"] for row in full_m2.communal_settings
    }
    care_or_medical = {
        row["agent_id"]
        for row in full_m2.residents
        if isinstance(row.get("care_setting_id"), str)
        and any(
            token in setting_type_by_id[row["care_setting_id"]].lower()
            for token in ("care", "medical")
        )
    }
    other_communal = {
        row["agent_id"]
        for row in full_m2.residents
        if isinstance(row.get("care_setting_id"), str) and row["agent_id"] not in care_or_medical
    }
    memberships = {
        row["agent_id"]
        for route_id in ("community_indoor", "community_outdoor")
        for row in bounded_full.route_memberships[route_id]
    }
    endpoints = {
        endpoint
        for when in bounded_full.config.snapshot_dates
        for route_id in ("community_indoor", "community_outdoor")
        for edge in bounded_full.route_snapshot(route_id, when).edges
        for endpoint in (edge["p1"], edge["p2"])
    }
    care_staff = {row["agent_id"] for row in bounded_full.care_staff_assignments}
    assert care_or_medical
    assert other_communal
    assert not care_or_medical & memberships
    assert not care_or_medical & endpoints
    assert other_communal <= memberships
    assert care_staff <= memberships
    assert care_staff & endpoints
    residence_diagnostics = bounded_full.diagnostics["cross_route"][
        "community_participation_by_residence_type"
    ]
    for setting_type, row in residence_diagnostics.items():
        if "care" in setting_type.lower() or "medical" in setting_type.lower():
            assert row["eligible_pool_count"] == 0
            assert not any(row["baseline_endpoint_count_by_route"].values())


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


def test_fixed_route_persistence_is_measured_from_realised_snapshots(generated) -> None:
    route_id = "workplace_team"
    edge_sets = [
        {(edge["p1"], edge["p2"]) for edge in generated.route_snapshot(route_id, when).edges}
        for when in generated.config.snapshot_dates
    ]
    realised = [
        len(previous & current) / max(1, len(previous | current))
        for previous, current in zip(edge_sets, edge_sets[1:], strict=False)
    ]
    diagnostic = generated.diagnostics["routes"][route_id]
    assert diagnostic["persistence_diagnostic_kind"] == "measurement"
    assert diagnostic["cross_day_jaccard"] == pytest.approx(realised)
    assert diagnostic["repeated_edge_rate"] == pytest.approx(sum(realised) / len(realised))


def test_running_sim_calendar_edges_align_across_weekend_and_term_boundary(generated) -> None:
    start = date(2025, 2, 15)
    duration_days = 10
    sim = build_starsim_sim(generated, start_date=start, duration_days=duration_days)
    mapping = agent_uid_mapping(generated)
    dynamic_routes = {
        route_id
        for route_id, spec in generated.route_specs.items()
        if route_id in generated._dynamic_builders or spec["active_calendar"] != "always"
    }
    observed_dates: list[date] = []

    def assert_live_edges(_sim) -> None:
        raw_date = str(sim.t.now("str"))[:10].replace(".", "-")
        when = date.fromisoformat(raw_date)
        observed_dates.append(when)
        for route_id in dynamic_routes:
            network = sim.networks[route_id]
            actual = {
                (int(left), int(right))
                for left, right in zip(network.edges.p1, network.edges.p2, strict=True)
            }
            expected = {
                (mapping[edge["p1"]], mapping[edge["p2"]])
                for edge in generated.route_snapshot(route_id, when).edges
            }
            assert actual == expected, (route_id, when)

    final_network = sorted(generated.route_specs)[-1]
    sim.loop.insert(assert_live_edges, label=f"{final_network}.step")
    sim.run(verbose=0)
    assert observed_dates == [start + i * (date.resolution) for i in range(duration_days)]


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
