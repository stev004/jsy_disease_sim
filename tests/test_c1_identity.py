from __future__ import annotations

from datetime import date

import numpy as np

from jersey_outbreak.network_generator import generate_networks
from jersey_outbreak.network_schemas import NetworkGenerationConfig
from jersey_outbreak.population_structure_generator import (
    SEMI_URBAN_PARISHES,
    _destination_category,
)
from jersey_outbreak.starsim_adapter import build_starsim_sim


def test_c1_population_relational_and_communal_age_structure(m6_network) -> None:
    residents = m6_network.m2_input.residents
    by_household: dict[str, list[dict]] = {}
    for row in residents:
        if row["household_id"] is not None:
            by_household.setdefault(row["household_id"], []).append(row)

    for members in by_household.values():
        parents = [
            row["age"] for row in members if row["household_role"] in {"parent", "adult", "partner"}
        ]
        children = [
            row["age"]
            for row in members
            if row["household_role"] in {"dependent_child", "adult_child"}
        ]
        assert not any(parent <= child for parent in parents for child in children)
        if parents and children:
            assert min(parents) - max(children) >= 15
        adult_pair = [
            row["age"] for row in members if row["household_role"] in {"adult", "partner"}
        ]
        if len(adult_pair) == 2:
            assert abs(adult_pair[0] - adult_pair[1]) <= 25

    setting_by_id = {row["setting_id"]: row for row in m6_network.m2_input.communal_settings}
    for row in residents:
        setting = setting_by_id.get(row["care_setting_id"])
        if setting is None:
            continue
        lowered = setting["setting_type"].lower()
        if "care home" in lowered:
            assert row["age"] >= 50
        if "children's home" in lowered:
            assert row["age"] <= 17
        if "detention" in lowered:
            assert 18 <= row["age"] <= 64


def test_c1_m3_identity_controls_and_geography(m6_network) -> None:
    m3 = m6_network.m3_input
    resident_ids = {row["agent_id"] for row in m6_network.m2_input.residents}
    staff_ids = {
        row["agent_id"]
        for row in m6_network.school_staff_assignments + m6_network.care_staff_assignments
    }
    assert staff_ids <= resident_ids
    assert all(
        18 <= next(row["age"] for row in m3.resident_structure if row["agent_id"] == agent_id) <= 95
        for agent_id in staff_ids
    )
    assert len(staff_ids) == len(
        m6_network.school_staff_assignments + m6_network.care_staff_assignments
    )

    employment = m3
    for row in employment.resident_structure:
        if row["economic_status"] == "employed":
            assert 18 <= row["age"] <= 74
    assert SEMI_URBAN_PARISHES == {"St Clement", "St Saviour"}
    assert "St Brelade" not in SEMI_URBAN_PARISHES
    assert _destination_category("St Brelade") == "Rural parishes"

    for workplace in m3.workplaces:
        assert workplace["public_private"] == "unknown"
        if workplace["size_band"] == "50+":
            assert 50 <= workplace["employee_count"] <= 500
    private_workplaces = sum(
        workplace["workplace_universe"] == "private_undertaking_control"
        for workplace in m3.workplaces
    )
    nonprivate_workplaces = sum(
        workplace["workplace_universe"] == "synthetic_nonprivate" for workplace in m3.workplaces
    )
    assert private_workplaces > 0
    assert nonprivate_workplaces > 0
    assert {workplace["workplace_universe"] for workplace in m3.workplaces} == {
        "private_undertaking_control",
        "synthetic_nonprivate",
    }
    assert all(
        job["job_universe"] in {"resident_worker_primary", "synthetic_secondary"}
        for job in m3.job_assignments
    )
    assert all(
        job["employment_universe"] in {"private_undertaking_control", "synthetic_nonprivate"}
        for job in m3.job_assignments
    )


def test_c1_starsim_identity_is_exact(m6_network) -> None:
    sim = build_starsim_sim(m6_network, duration_days=1)
    m2_by_agent = {row["agent_id"]: row for row in m6_network.m2_input.residents}
    expected_ids = m6_network.agent_ids
    expected_ages = np.asarray(
        [m2_by_agent[agent_id]["age"] for agent_id in expected_ids], dtype=float
    )
    expected_female = np.asarray(
        [m2_by_agent[agent_id]["sex"] == "female" for agent_id in expected_ids], dtype=bool
    )
    assert np.array_equal(np.asarray(sim.people.age), expected_ages)
    assert np.array_equal(np.asarray(sim.people.female), expected_female)


def test_c1_school_calendar_suppresses_staff_school_edges(m6_network) -> None:
    school_staff = {row["agent_id"] for row in m6_network.school_staff_assignments}
    monday_endpoints = {
        endpoint
        for edge in m6_network.route_snapshot("school_class", date(2025, 1, 6)).edges
        for endpoint in (edge["p1"], edge["p2"])
    }
    august_endpoints = {
        endpoint
        for edge in m6_network.route_snapshot("school_class", date(2025, 8, 11)).edges
        for endpoint in (edge["p1"], edge["p2"])
    }
    assert monday_endpoints & school_staff
    assert not august_endpoints & school_staff


def test_c1_care_staff_route_is_bounded_and_separable(m6_network) -> None:
    care_edges = m6_network.route_snapshot("care_staff", date(2025, 1, 6)).edges
    resident_edges = m6_network.route_snapshot("care_resident", date(2025, 1, 6)).edges
    assert care_edges
    assert resident_edges
    assert len(care_edges) < len(m6_network.m2_input.residents) * len(
        m6_network.care_staff_assignments
    )
    assert all(edge not in resident_edges for edge in care_edges)
    assert m6_network.diagnostics["staffing"]["care"]["settings_failing_minimum"] == []

    staff_disabled = generate_networks(
        NetworkGenerationConfig(
            mode=m6_network.config.mode,
            seed=m6_network.config.seed,
            disabled_route_ids=("care_staff",),
        ),
        m6_network.m2_input,
        m6_network.m3_input,
    )
    assert "care_staff" not in staff_disabled.route_specs
    assert "care_resident" in staff_disabled.route_specs
    assert staff_disabled.route_snapshot("care_resident", date(2025, 1, 6)).edges == resident_edges
