"""PERF-6 route-effect vector/scalar parity contracts."""

from __future__ import annotations

import math
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from jersey_outbreak.intervention_schemas import ScenarioConfig
from jersey_outbreak.interventions import CARE_ROUTES, InterventionManager
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
