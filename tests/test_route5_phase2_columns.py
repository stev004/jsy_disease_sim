"""ROUTE-5 phase-2 columnar dynamic-builder equivalence contracts."""

from __future__ import annotations

import importlib.util
import sys
import types
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from jersey_outbreak.network_generator import (
    EdgeColumns,
    RouteSnapshot,
    _complete_group,
    _complete_group_columns,
    _grouped_ring_edges,
    _grouped_ring_edges_columns,
    _ring_edges,
    _ring_edges_columns,
    _school_staff_cross_edges,
    _school_staff_cross_edges_columns,
    generate_networks,
)
from jersey_outbreak.network_schemas import NetworkGenerationConfig
from jersey_outbreak.starsim_adapter import _edge_arrays

ROOT = Path(__file__).resolve().parents[1]
BASE_ROOT = Path("/tmp/jos-r5b-base")
CONVERTED_ROUTES = ("workplace_transient", "school_cross_class", "bus")


class _FakeStarsim:
    @staticmethod
    def uids(values: np.ndarray) -> np.ndarray:
        return values


def _load_base_network_generator() -> types.ModuleType:
    package_name = "_jos_r5b_base"
    package_path = BASE_ROOT / "src" / "jersey_outbreak"
    package = types.ModuleType(package_name)
    package.__path__ = [str(package_path)]
    sys.modules[package_name] = package
    module_name = f"{package_name}.network_generator"
    spec = importlib.util.spec_from_file_location(
        module_name, package_path / "network_generator.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _column_edges(columns: EdgeColumns) -> tuple[dict[str, object], ...]:
    return RouteSnapshot.from_edge_columns("fixture", date(2025, 1, 6), columns).edges


def _assert_route_equal(
    actual, expected, route_id: str, when: date, uid_by_agent_id: dict[str, int]
) -> None:
    actual_edges = actual.route_snapshot(route_id, when).edges
    expected_edges = expected.route_snapshot(route_id, when).edges
    if actual_edges != expected_edges:
        for row, (actual_edge, expected_edge) in enumerate(
            zip(actual_edges, expected_edges, strict=False)
        ):
            if actual_edge != expected_edge:
                raise AssertionError(
                    f"{route_id} first differing row on {when}: {row}; "
                    f"actual={actual_edge!r}, expected={expected_edge!r}"
                )
        raise AssertionError(
            f"{route_id} edge row count differs on {when}: "
            f"actual={len(actual_edges)}, expected={len(expected_edges)}"
        )
    for actual_edge, expected_edge in zip(actual_edges, expected_edges, strict=True):
        assert type(actual_edge) is type(expected_edge)
        assert list(actual_edge) == list(expected_edge)

    actual_arrays = _edge_arrays(
        _FakeStarsim(), actual.route_snapshot(route_id, when), uid_by_agent_id
    )
    expected_arrays = _edge_arrays(
        _FakeStarsim(), expected.route_snapshot(route_id, when).edges, uid_by_agent_id
    )
    for name in ("p1", "p2", "beta"):
        assert actual_arrays[name].dtype == expected_arrays[name].dtype
        assert actual_arrays[name].shape == expected_arrays[name].shape
        assert actual_arrays[name].tobytes() == expected_arrays[name].tobytes(), (
            route_id,
            when,
            name,
        )


@pytest.mark.skipif(not BASE_ROOT.exists(), reason="phase-2 base comparison tree is not present")
@pytest.mark.parametrize("seed", (123, 124))
def test_three_phase2_builders_match_base_on_snapshot_and_fourteen_day_windows(
    m6_network, seed: int
) -> None:
    config = NetworkGenerationConfig(mode="ci", seed=seed)
    actual = generate_networks(config, m6_network.m2_input, m6_network.m3_input, ROOT)
    base_generator = _load_base_network_generator()
    expected = base_generator.generate_networks(
        config, m6_network.m2_input, m6_network.m3_input, ROOT
    )
    dates = [
        *config.snapshot_dates,
        *[config.start_date + timedelta(days=offset) for offset in range(14)],
    ]
    uid_by_agent_id = {agent_id: index for index, agent_id in enumerate(actual.agent_ids)}
    for route_id in CONVERTED_ROUTES:
        builder = actual._dynamic_builders[route_id]
        for when in dates:
            assert isinstance(builder(when), EdgeColumns), (route_id, when)
            _assert_route_equal(actual, expected, route_id, when, uid_by_agent_id)


def test_columnar_group_and_ring_twins_match_dict_references() -> None:
    # Storage order deliberately differs from canonical string order.
    agent_ids = ["agent-z", "agent-a", "agent-m", "agent-x"]
    index_by_agent_id = {agent_id: index for index, agent_id in enumerate(agent_ids)}

    expected_complete = _complete_group(["agent-m", "agent-z", "agent-a", "agent-a"], 0.45, 7)
    actual_complete = _complete_group_columns(
        ["agent-m", "agent-z", "agent-a", "agent-a"],
        0.45,
        7,
        agent_ids=agent_ids,
        index_by_agent_id=index_by_agent_id,
    )
    assert _column_edges(actual_complete) == tuple(expected_complete)

    excluded_pairs = {("agent-a", "agent-m")}
    expected_ring = _ring_edges(
        ["agent-z", "agent-a", "agent-m", "agent-x"],
        2,
        0.3,
        7,
        excluded_pairs,
    )
    actual_ring = _ring_edges_columns(
        ["agent-z", "agent-a", "agent-m", "agent-x"],
        2,
        0.3,
        7,
        excluded_pairs,
        agent_ids=agent_ids,
        index_by_agent_id=index_by_agent_id,
    )
    assert _column_edges(actual_ring) == tuple(expected_ring)

    groups = [["agent-z"], [], ["agent-x", "agent-a", "agent-m"], ["agent-m", "agent-a"]]
    expected_grouped = _grouped_ring_edges(
        groups,
        123,
        "fixture-route",
        date(2025, 1, 8),
        2,
        0.3,
        7,
        excluded_pairs,
    )
    actual_grouped = _grouped_ring_edges_columns(
        groups,
        123,
        "fixture-route",
        date(2025, 1, 8),
        2,
        0.3,
        7,
        excluded_pairs,
        agent_ids=agent_ids,
        index_by_agent_id=index_by_agent_id,
    )
    assert _column_edges(actual_grouped) == tuple(expected_grouped)

    assert (
        len(
            _complete_group_columns(
                ["agent-z"], 0.45, agent_ids=agent_ids, index_by_agent_id=index_by_agent_id
            )
        )
        == 0
    )
    assert (
        len(
            _ring_edges_columns(
                ["agent-z"],
                2,
                0.3,
                7,
                agent_ids=agent_ids,
                index_by_agent_id=index_by_agent_id,
            )
        )
        == 0
    )


def test_columnar_school_staff_twin_matches_dict_reference() -> None:
    agent_ids = ["staff-z", "pupil-a", "pupil-m", "staff-a"]
    index_by_agent_id = {agent_id: index for index, agent_id in enumerate(agent_ids)}
    school_year_groups = {
        ("school-1", "year-1"): ["pupil-m", "pupil-a"],
        ("school-1", "year-2"): [],
    }
    staff_by_school_year = {
        ("school-1", "year-1"): ["staff-z", "staff-a", "pupil-a"],
        ("school-1", "year-2"): ["staff-z"],
    }
    excluded_pairs = {("pupil-a", "staff-a")}
    expected = _school_staff_cross_edges(
        school_year_groups,
        staff_by_school_year,
        123,
        date(2025, 1, 8),
        2,
        0.5,
        14,
        excluded_pairs,
    )
    actual = _school_staff_cross_edges_columns(
        school_year_groups,
        staff_by_school_year,
        123,
        date(2025, 1, 8),
        2,
        0.5,
        14,
        excluded_pairs,
        agent_ids=agent_ids,
        index_by_agent_id=index_by_agent_id,
    )
    assert _column_edges(actual) == tuple(expected)
