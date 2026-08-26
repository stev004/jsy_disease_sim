import json
from pathlib import Path

import pytest

from jersey_outbreak.network_artifacts import write_network_artifact
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
from jersey_outbreak.staffing_evidence import care_minimums, nursing_nurse_minimum

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def staffing_inputs(tmp_path_factory: pytest.TempPathFactory):
    output = tmp_path_factory.mktemp("m4-1-inputs")
    population = generate_population(ROOT, PopulationGenerationConfig(mode="ci", seed=123))
    population_artifact = write_population_artifact(population, ROOT, output / "populations")
    m2_input = load_m2_population_artifact(ROOT, population_artifact.artifact_directory)
    structure = generate_structure(ROOT, StructureGenerationConfig(mode="ci", seed=123), m2_input)
    structure_artifact = write_structure_artifact(structure, ROOT, output / "structures", m2_input)
    return m2_input, load_m3_structure_artifact(ROOT, structure_artifact.artifact_directory)


@pytest.fixture(scope="module")
def staffing_network(staffing_inputs):
    m2_input, m3_input = staffing_inputs
    return generate_networks(NetworkGenerationConfig(mode="ci", seed=123), m2_input, m3_input)


def test_staff_reuses_existing_adult_workers_without_student_or_resident_overlap(
    staffing_network,
) -> None:
    generated = staffing_network
    m2_by_agent = {row["agent_id"]: row for row in generated.m2_input.residents}
    m3_by_agent = {row["agent_id"]: row for row in generated.m3_input.resident_structure}
    pupil_ids = {row["agent_id"] for row in generated.m3_input.school_assignments}
    care_resident_ids = {
        row["agent_id"]
        for row in generated.m2_input.residents
        if row.get("care_setting_id")
        in generated.staffing_diagnostics["care"]["regulatory_minimum_by_setting"]
    }
    school_staff = generated.school_staff_assignments
    care_staff = generated.care_staff_assignments
    all_staff_ids = [row["agent_id"] for row in school_staff + care_staff]
    assert len(all_staff_ids) == len(set(all_staff_ids))
    assert set(all_staff_ids) <= set(m2_by_agent)
    assert not set(all_staff_ids) & pupil_ids
    assert not set(all_staff_ids) & care_resident_ids
    assert all(
        m3_by_agent[row["agent_id"]]["economic_status"] == "employed"
        for row in school_staff + care_staff
    )
    assert all(m3_by_agent[row["agent_id"]]["age"] >= 18 for row in school_staff + care_staff)
    assert all(
        m2_by_agent[row["agent_id"]].get("household_id") is not None
        for row in school_staff + care_staff
    )


def test_school_staff_assignments_resolve_and_have_required_role_breakdown(
    staffing_network,
) -> None:
    generated = staffing_network
    schools = {row["school_id"]: row for row in generated.m3_input.schools}
    classes = {row["class_id"]: row for row in generated.m3_input.classes}
    roles = {row["role"] for row in generated.school_staff_assignments}
    assert roles == {"teacher", "teaching_assistant", "head_deputy"}
    assert generated.staffing_diagnostics["school"]["staff_assigned_to_zero_schools"] == 0
    assert generated.staffing_diagnostics["school"]["duplicate_staff_assignments"] == 0
    for row in generated.school_staff_assignments:
        assert row["school_id"] in schools
        if row["class_id"] is not None:
            assert row["class_id"] in classes
            assert classes[row["class_id"]]["school_id"] == row["school_id"]
            assert classes[row["class_id"]]["school_year"] == row["school_year"]
        else:
            assert row["role"] == "head_deputy"

    breakdown = generated.staffing_diagnostics["school"]["route_edge_breakdown"]
    assert breakdown["school_class"]["pupil_staff"] > 0
    assert breakdown["school_class"]["pupil_pupil"] > 0
    assert breakdown["school_cross_class"]["pupil_staff"] > 0


def test_school_calendar_suppresses_staff_contacts(staffing_network) -> None:
    generated = staffing_network
    monday = generated.route_snapshot("school_class", generated.config.snapshot_dates[0]).edges
    august = generated.route_snapshot("school_class", generated.config.snapshot_dates[-1]).edges
    assert monday
    assert any(
        endpoint in {row["agent_id"] for row in generated.school_staff_assignments}
        for edge in monday
        for endpoint in (edge["p1"], edge["p2"])
    )
    assert not august
    assert (
        generated.route_snapshot("school_cross_class", generated.config.snapshot_dates[-1]).edges
        == ()
    )


def test_care_regulatory_boundary_rules_and_staffed_settings(staffing_network) -> None:
    assert nursing_nurse_minimum(1) == (1, 1)
    assert nursing_nurse_minimum(10) == (1, 1)
    assert nursing_nurse_minimum(11) == (1, 0)
    assert nursing_nurse_minimum(20) == (1, 0)
    assert nursing_nurse_minimum(21) == (2, 1)
    assert nursing_nurse_minimum(40) == (2, 1)
    assert nursing_nurse_minimum(41) == (3, 2)
    assert care_minimums("Care home (without nursing)", 16)["support_day_required"] == 2
    assert care_minimums("Care home (with nursing)", 41)["support_day_required"] == 9

    diagnostics = staffing_network.staffing_diagnostics["care"]
    assert diagnostics["settings_failing_minimum"] == []
    assert diagnostics["cross_facility_staff"] == 0
    assert diagnostics["synthetic_care_support_workers"] > 0
    assert diagnostics["regulatory_status"] == "regulatory_minimum"
    assert diagnostics["actual_staff_roster_status"] == "unknown"
    assert staffing_network.route_snapshot(
        "care_staff", staffing_network.config.snapshot_dates[0]
    ).edges


def test_staffing_is_seed_reproducible_and_seed_sensitive(staffing_inputs) -> None:
    m2_input, m3_input = staffing_inputs
    first = generate_networks(NetworkGenerationConfig(mode="ci", seed=123), m2_input, m3_input)
    second = generate_networks(NetworkGenerationConfig(mode="ci", seed=123), m2_input, m3_input)
    changed = generate_networks(NetworkGenerationConfig(mode="ci", seed=999), m2_input, m3_input)
    first_school = [
        (row["agent_id"], row["school_id"], row["class_id"])
        for row in first.school_staff_assignments
    ]
    second_school = [
        (row["agent_id"], row["school_id"], row["class_id"])
        for row in second.school_staff_assignments
    ]
    changed_school = [
        (row["agent_id"], row["school_id"], row["class_id"])
        for row in changed.school_staff_assignments
    ]
    assert first.logical_content_hash == second.logical_content_hash
    assert first_school == second_school
    assert first.logical_content_hash != changed.logical_content_hash
    assert first_school != changed_school


def test_staff_routes_are_independent_and_care_contacts_are_bounded(staffing_inputs) -> None:
    m2_input, m3_input = staffing_inputs
    baseline = generate_networks(NetworkGenerationConfig(mode="ci", seed=123), m2_input, m3_input)
    no_school = generate_networks(
        NetworkGenerationConfig(
            mode="ci",
            seed=123,
            enabled_route_families=(
                "household",
                "work",
                "care",
                "transport",
                "indoor_community",
                "outdoor_community",
            ),
        ),
        m2_input,
        m3_input,
    )
    no_care = generate_networks(
        NetworkGenerationConfig(
            mode="ci",
            seed=123,
            enabled_route_families=(
                "household",
                "school",
                "work",
                "transport",
                "indoor_community",
                "outdoor_community",
            ),
        ),
        m2_input,
        m3_input,
    )
    assert "school_class" not in no_school.route_specs
    assert "care_staff" not in no_care.route_specs
    assert (
        no_school.route_snapshot("care_staff", baseline.config.snapshot_dates[0]).edges
        == baseline.route_snapshot("care_staff", baseline.config.snapshot_dates[0]).edges
    )
    assert (
        no_care.route_snapshot("school_class", baseline.config.snapshot_dates[0]).edges
        == baseline.route_snapshot("school_class", baseline.config.snapshot_dates[0]).edges
    )
    care_edges = baseline.route_snapshot("care_staff", baseline.config.snapshot_dates[0]).edges
    care_staff = baseline.care_staff_assignments
    care_residents = {
        row["agent_id"]
        for row in baseline.m2_input.residents
        if row.get("care_setting_id") is not None
    }
    theoretical_all_pairs = len(care_staff) * len(care_residents)
    assert len(care_edges) < theoretical_all_pairs


def test_institutional_staff_primary_workplaces_are_reinterpreted(
    staffing_network,
) -> None:
    generated = staffing_network
    audit = generated.diagnostics["staffing"]["occupational_staff_mapping"]
    jobs_by_agent: dict[str, list[dict[str, object]]] = {}
    for row in generated.m3_input.job_assignments:
        jobs_by_agent.setdefault(row["agent_id"], []).append(row)
    for kind, assignment_rows in (
        ("school", generated.school_staff_assignments),
        ("care", generated.care_staff_assignments),
    ):
        staff_ids = {row["agent_id"] for row in assignment_rows}
        secondary_ids = {
            agent_id
            for agent_id in staff_ids
            if any(row["job_role"] == "secondary" for row in jobs_by_agent[agent_id])
        }
        result = audit[kind]
        assert result["endpoints"] == len(staff_ids)
        assert result["m3_primary_job_membership"] == len(staff_ids)
        assert result["primary_job_reinterpreted_to_institution"] == len(staff_ids)
        assert result["m3_secondary_job_workers"] == len(secondary_ids)
        assert result["effective_ordinary_workplace_job_membership"] == len(secondary_ids)
        assert result["unintended_occupational_double_counting"] == 0
        assert result["ordinary_workplace_route_participants_any_snapshot"] <= len(secondary_ids)
    assert audit["household_community_transport_preserved"] is True
    assert audit["unintended_occupational_double_counting"] == 0


def test_staffing_artifacts_persist_assignments_and_statuses(
    staffing_network, tmp_path: Path
) -> None:
    artifact = write_network_artifact(staffing_network, ROOT, tmp_path / "networks")
    manifest = json.loads((artifact.artifact_directory / "manifest.json").read_text())
    assert (artifact.artifact_directory / "school_staff_assignments.parquet").exists()
    assert (artifact.artifact_directory / "care_staff_assignments.parquet").exists()
    assert (artifact.artifact_directory / "staffing_provenance.json").exists()
    assert any(
        record["path"].endswith("staffing_provenance.json")
        for record in manifest["output_artifacts"]
    )
    provenance = json.loads((artifact.artifact_directory / "staffing_provenance.json").read_text())
    assert provenance["school"]["statuses"]["official_fte"] == "observed"
    assert provenance["care"]["statuses"]["regulatory_ratio"] == "regulatory_minimum"
