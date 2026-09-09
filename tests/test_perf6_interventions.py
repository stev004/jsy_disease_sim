"""PERF-6 route-effect vector/scalar parity contracts."""

from __future__ import annotations

import math
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from jersey_outbreak.intervention_schemas import (
    InterventionConfig,
    ScenarioConfig,
    TargetPopulation,
)
from jersey_outbreak.interventions import CARE_ROUTES, InterventionManager
from jersey_outbreak.outbreak_schemas import ROUTE_IDS
from jersey_outbreak.scenario import load_scenario_config
from jersey_outbreak.starsim_adapter import _edge_arrays, _load_starsim

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_PATHS = tuple(sorted((ROOT / "configs" / "scenarios").glob("*.yaml")))


def _scalar_composed_factors(manager, configs, route_id, snapshot, when, ti):
    return np.asarray(
        [
            max(
                0.0,
                min(
                    1.0,
                    math.prod(
                        manager._edge_multiplier(
                            config, route_id, str(edge["p1"]), str(edge["p2"]), when, ti
                        )
                        for config in configs
                    ),
                ),
            )
            for edge in snapshot.edges
        ],
        dtype=np.float64,
    )


def _assert_array_bytes(left: np.ndarray, right: np.ndarray, label: str) -> None:
    assert left.dtype == right.dtype, label
    assert left.shape == right.shape, label
    assert left.tobytes() == right.tobytes(), label


@pytest.mark.parametrize(
    ("label", "configs"),
    (
        (
            "age-targeted-residents-only",
            (
                InterventionConfig(
                    intervention_id="targeted-residents",
                    type="community_reduction",
                    start_date=date(2025, 1, 6),
                    target=TargetPopulation(age_bands=("18-64",)),
                    community_scope="residents_only",
                    indoor_multiplier=0.5,
                ),
            ),
        ),
        (
            "targeted-only",
            (
                InterventionConfig(
                    intervention_id="targeted-only",
                    type="community_reduction",
                    start_date=date(2025, 1, 6),
                    target=TargetPopulation(age_bands=("18-64",)),
                    indoor_multiplier=0.5,
                ),
            ),
        ),
        (
            "residents-only-only",
            (
                InterventionConfig(
                    intervention_id="residents-only",
                    type="community_reduction",
                    start_date=date(2025, 1, 6),
                    community_scope="residents_only",
                    indoor_multiplier=0.5,
                ),
            ),
        ),
        (
            "a-targeted-z-general",
            (
                InterventionConfig(
                    intervention_id="a-targeted",
                    type="community_reduction",
                    start_date=date(2025, 1, 6),
                    target=TargetPopulation(age_bands=("18-64",)),
                    indoor_multiplier=0.8,
                ),
                InterventionConfig(
                    intervention_id="z-general",
                    type="community_reduction",
                    start_date=date(2025, 1, 6),
                    indoor_multiplier=0.5,
                ),
            ),
        ),
    ),
)
def test_vector_community_route_effects_cover_target_and_scope_predicates(
    m6_network, label, configs
) -> None:
    manager = InterventionManager(
        m6_network,
        configs,
        run_seed=123,
        start_date=date(2025, 1, 6),
        duration_days=1,
        scenario=ScenarioConfig(scenario_id=f"perf6-{label}", interventions=configs),
    )
    snapshot = m6_network.route_snapshot("community_indoor", date(2025, 1, 6))
    p1_uids, p2_uids = manager._snapshot_uid_endpoints(snapshot)
    vector = manager._compose_edge_multipliers(
        [
            manager._edge_multiplier_array(
                config,
                "community_indoor",
                snapshot,
                p1_uids,
                p2_uids,
                date(2025, 1, 6),
                0,
            )
            for config in configs
        ]
    )
    scalar = _scalar_composed_factors(
        manager, configs, "community_indoor", snapshot, date(2025, 1, 6), 0
    )
    _assert_array_bytes(vector, scalar, f"community predicate coverage: {label}")

    # CI M4 contains resident endpoints only.  Temporarily treating one
    # endpoint as a travel-layer visitor exercises the scalar visitor branch
    # without changing the generated artifact or the route parity assertion.
    visitor_id = m6_network.agent_ids[0]
    visitor_row = manager._m2_by_agent.pop(visitor_id)
    try:
        manager._adherence_cache.clear()
        manager._vector_target_adheres_cache.clear()
        manager._vector_community_adheres_cache.clear()
        visitor_uid = manager._uid_by_agent_id[visitor_id]
        for config in configs:
            assert manager._vector_community_adheres(config)[visitor_uid] == (
                manager._community_endpoint_adheres(config, visitor_id)
            )
    finally:
        manager._m2_by_agent[visitor_id] = visitor_row


@pytest.mark.parametrize("scenario_path", SCENARIO_PATHS, ids=lambda path: path.stem)
def test_vector_route_effects_match_scalar_oracle_for_30_days(m6_network, scenario_path) -> None:
    scenario = load_scenario_config(ROOT, scenario_path)
    configs = tuple(config for config in scenario.interventions if config.type != "vaccination")
    manager = InterventionManager(
        m6_network,
        configs,
        run_seed=123,
        start_date=date(2025, 1, 6),
        duration_days=30,
        scenario=ScenarioConfig(scenario_id="perf6-test", interventions=configs),
    )
    for config in configs:
        if config.type == "case_isolation":
            manager._isolation_until[config.intervention_id] = np.full(
                len(m6_network.agent_ids), -1, dtype=np.int64
            )
        elif config.type == "household_quarantine":
            manager._quarantine_until[config.intervention_id] = {}

    ss_module = _load_starsim()
    for ti in range(30):
        when = date(2025, 1, 6) + timedelta(days=ti)
        for config in configs:
            if config.type == "case_isolation":
                states = manager._isolation_until[config.intervention_id]
                states.fill(-1)
                states[0] = ti + 2
            elif config.type == "household_quarantine":
                states = manager._quarantine_until[config.intervention_id]
                states.clear()
                household_id = m6_network.m2_input.residents[0].get("household_id")
                if household_id is not None:
                    states[str(household_id)] = ti + 2

        for route_id in sorted(m6_network.route_specs):
            relevant = tuple(
                config
                for config in configs
                if manager._config_can_touch_route(config, route_id, when, ti)
            )
            if not relevant:
                continue
            snapshot = m6_network.route_snapshot(route_id, when)
            p1_uids, p2_uids = manager._snapshot_uid_endpoints(snapshot)
            vector = manager._compose_edge_multipliers(
                [
                    manager._edge_multiplier_array(
                        config, route_id, snapshot, p1_uids, p2_uids, when, ti
                    )
                    for config in relevant
                ]
            )
            scalar = _scalar_composed_factors(manager, relevant, route_id, snapshot, when, ti)
            _assert_array_bytes(
                vector,
                scalar,
                f"factor {scenario_path.name} day={ti} route={route_id}",
            )

            retained = (vector > 0) | (route_id in CARE_ROUTES)
            retained_indices = np.flatnonzero(retained)
            scalar_edges = [
                edge if factor == 1.0 else {**edge, "weight": float(edge["weight"]) * factor}
                for edge, factor in zip(snapshot.edges, scalar, strict=True)
                if factor > 0 or route_id in CARE_ROUTES
            ]
            scalar_arrays = _edge_arrays(ss_module, scalar_edges, manager._uid_by_agent_id)
            vector_arrays = _edge_arrays(
                ss_module, snapshot, manager._uid_by_agent_id, manager._uid_of_index
            )
            _assert_array_bytes(
                vector_arrays["p1"][retained_indices],
                scalar_arrays["p1"],
                f"p1 {scenario_path.name} day={ti} route={route_id}",
            )
            _assert_array_bytes(
                vector_arrays["p2"][retained_indices],
                scalar_arrays["p2"],
                f"p2 {scenario_path.name} day={ti} route={route_id}",
            )
            scalar_beta = np.asarray([edge["weight"] for edge in scalar_edges], dtype=float)
            vector_beta = snapshot.weight[retained_indices].copy()
            changed = vector[retained_indices] != 1.0
            vector_beta[changed] = (
                snapshot.weight[retained_indices][changed] * vector[retained_indices][changed]
            )
            _assert_array_bytes(
                vector_beta,
                scalar_beta,
                f"beta {scenario_path.name} day={ti} route={route_id}",
            )
            _assert_array_bytes(
                np.ones(len(retained_indices), dtype=float),
                np.ones(len(scalar_edges), dtype=float),
                f"dur {scenario_path.name} day={ti} route={route_id}",
            )


def test_ordered_clamp_and_care_zero_beta_retention() -> None:
    ordered = [np.asarray([0.1]), np.asarray([0.7]), np.asarray([3.0])]
    expected = np.asarray([max(0.0, min(1.0, math.prod(vector[0] for vector in ordered)))])
    actual = InterventionManager._compose_edge_multipliers(ordered)
    _assert_array_bytes(actual, expected, "ordered product")
    assert actual[0] == math.prod((0.1, 0.7, 3.0))
    assert actual[0] != math.prod((3.0, 0.1, 0.7))

    assert (
        InterventionManager._compose_edge_multipliers([np.asarray([0.5]), np.asarray([0.0])])[0]
        == 0.0
    )
    assert (
        InterventionManager._compose_edge_multipliers([np.asarray([0.5]), np.asarray([3.0])])[0]
        == 1.0
    )
    assert np.array_equal(
        (np.asarray([0.0, 0.5]) > 0) | ("care_resident" in CARE_ROUTES),
        np.asarray([True, True]),
    )
    assert np.array_equal(
        (np.asarray([0.0, 0.5]) > 0) | ("community_indoor" in CARE_ROUTES),
        np.asarray([False, True]),
    )


def test_scalar_helper_remains_the_oracle(m6_network) -> None:
    manager = InterventionManager(
        m6_network, (), run_seed=123, start_date=date(2025, 1, 6), duration_days=1
    )
    assert callable(manager._edge_multiplier)


def _schema_target_variants(m6_network):
    resident = m6_network.m2_input.residents[0]
    school = m6_network.m3_input.school_assignments[0]
    job = m6_network.m3_input.job_assignments[0]
    setting = m6_network.m2_input.communal_settings[0]
    age = int(resident["age"])
    age_band = "0-4" if age <= 4 else "5-17" if age <= 17 else "18-64" if age <= 64 else "65+"
    return (
        ("untargeted", TargetPopulation()),
        ("agent_ids", TargetPopulation(agent_ids=(str(resident["agent_id"]),))),
        ("age_min", TargetPopulation(age_min=age)),
        ("age_max", TargetPopulation(age_max=age)),
        ("age_bands", TargetPopulation(age_bands=(age_band,))),
        ("home_parishes", TargetPopulation(home_parishes=(str(resident["home_parish"]),))),
        (
            "employment_sectors",
            TargetPopulation(employment_sectors=(str(job["sector"]),)),
        ),
        ("school_types", TargetPopulation(school_types=(str(school["school_type"]),))),
        ("school_ids", TargetPopulation(school_ids=(str(school["school_id"]),))),
        (
            "workplace_ids",
            TargetPopulation(workplace_ids=(str(job["workplace_id"]),)),
        ),
        (
            "care_setting_types",
            TargetPopulation(care_setting_types=(str(setting["setting_type"]),)),
        ),
        ("care_role_resident", TargetPopulation(care_role="care_resident")),
        ("care_role_staff", TargetPopulation(care_role="care_staff")),
        ("worker_only", TargetPopulation(worker_only=True)),
        (
            "include_institutional_staff",
            TargetPopulation(include_institutional_staff=True),
        ),
    )


def _schema_grid_config(
    intervention_id: str,
    intervention_type: str,
    community_scope: str,
    target: TargetPopulation,
    adherence: float,
    *,
    care_target: str = "both",
):
    common = {
        "intervention_id": intervention_id,
        "type": intervention_type,
        "target": target,
        "adherence": adherence,
        "community_scope": community_scope,
        "start_date": date(2025, 1, 6),
    }
    if intervention_type in {"case_isolation", "household_quarantine"}:
        common.pop("start_date")
        common.update(
            duration_days=2,
            route_effects={route_id: 0.5 for route_id in ROUTE_IDS},
        )
    elif intervention_type == "school_closure":
        common.update(class_multiplier=0.5, cross_class_multiplier=0.5)
    elif intervention_type == "workplace_reduction":
        common.update(workplace_multiplier=0.5, commute_multiplier=0.5, additional_wfh_fraction=1.0)
    elif intervention_type == "community_reduction":
        common.update(indoor_multiplier=0.5, outdoor_multiplier=0.5)
    elif intervention_type == "care_home_protection":
        common.update(
            care_target=care_target,
            care_contact_multiplier=0.5,
            care_external_resident_multiplier=0.5,
            care_external_staff_multiplier=0.5,
        )
    elif intervention_type in {"masking", "gathering_reduction"}:
        common.update(route_effects={route_id: 0.5 for route_id in ROUTE_IDS})
    elif intervention_type == "vaccination":
        common.update(
            coverage_target=1.0,
            rollout_rate=1.0,
            efficacy_susceptibility=0.5,
            efficacy_infectiousness=0.5,
        )
    return InterventionConfig(**common)


def _schema_grid_configs(m6_network):
    intervention_types = (
        "case_isolation",
        "household_quarantine",
        "school_closure",
        "workplace_reduction",
        "community_reduction",
        "care_home_protection",
        "vaccination",
        "masking",
        "gathering_reduction",
    )
    scopes = ("everyone_present", "residents_only")
    adherence_values = (0.0, 0.5, 1.0)
    target_variants = _schema_target_variants(m6_network)
    configs = []
    for intervention_type in intervention_types:
        care_targets = (
            ("nursing", "non_nursing", "both")
            if intervention_type == "care_home_protection"
            else ("both",)
        )
        for care_target in care_targets:
            for scope in scopes:
                for target_name, target in target_variants:
                    for adherence in adherence_values:
                        configs.append(
                            _schema_grid_config(
                                f"grid-{intervention_type}-{care_target}-{scope}-{target_name}-{adherence}",
                                intervention_type,
                                scope,
                                target,
                                adherence,
                                care_target=care_target,
                            )
                        )
    return tuple(configs)


def _set_grid_state(manager, configs, ti: int, m6_network) -> None:
    for config in configs:
        if config.type == "case_isolation":
            states = manager._isolation_until[config.intervention_id]
            states.fill(-1)
            states[0] = ti + 2
        elif config.type == "household_quarantine":
            states = manager._quarantine_until[config.intervention_id]
            states.clear()
            household_id = m6_network.m2_input.residents[0].get("household_id")
            if household_id is not None:
                states[str(household_id)] = ti + 2


def _assert_generated_route_parity(m6_network, configs, days: int = 7) -> None:
    manager = InterventionManager(
        m6_network,
        configs,
        run_seed=123,
        start_date=date(2025, 1, 6),
        duration_days=days,
    )
    for config in configs:
        if config.type == "case_isolation":
            manager._isolation_until[config.intervention_id] = np.full(
                len(m6_network.agent_ids), -1, dtype=np.int64
            )
        elif config.type == "household_quarantine":
            manager._quarantine_until[config.intervention_id] = {}

    for ti in range(days):
        when = date(2025, 1, 6) + timedelta(days=ti)
        manager._refresh_wfh(when, ti)
        _set_grid_state(manager, configs, ti, m6_network)
        for route_id in sorted(m6_network.route_specs):
            snapshot = m6_network.route_snapshot(route_id, when)
            p1_uids, p2_uids = manager._snapshot_uid_endpoints(snapshot)
            for config in configs:
                vector = manager._edge_multiplier_array(
                    config, route_id, snapshot, p1_uids, p2_uids, when, ti
                )
                scalar = np.asarray(
                    [
                        manager._edge_multiplier(
                            config,
                            route_id,
                            str(edge["p1"]),
                            str(edge["p2"]),
                            when,
                            ti,
                        )
                        for edge in snapshot.edges
                    ],
                    dtype=np.float64,
                )
                _assert_array_bytes(
                    vector,
                    scalar,
                    f"schema grid config={config.intervention_id} day={ti} route={route_id}",
                )


def test_vector_route_effects_cover_generated_intervention_schema_grid(m6_network) -> None:
    configs = _schema_grid_configs(m6_network)
    assert len(configs) == 990
    _assert_generated_route_parity(m6_network, configs)

    targeted = InterventionConfig(
        intervention_id="a-targeted",
        type="community_reduction",
        start_date=date(2025, 1, 6),
        target=TargetPopulation(age_bands=("18-64",)),
        community_scope="residents_only",
        adherence=0.5,
        indoor_multiplier=0.8,
    )
    general = InterventionConfig(
        intervention_id="z-general",
        type="community_reduction",
        start_date=date(2025, 1, 6),
        adherence=0.5,
        indoor_multiplier=0.5,
    )
    _assert_generated_route_parity(m6_network, (targeted, general))
    _assert_generated_route_parity(m6_network, (general, targeted))
