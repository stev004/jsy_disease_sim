"""Equivalence tests for the columnar route-snapshot core."""

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
    _canonical_edge,
    _deduplicate_edge_columns,
    _deduplicate_edges,
    _merge_sorted_edge_columns,
    _merge_sorted_edges,
    generate_networks,
)
from jersey_outbreak.network_schemas import NetworkGenerationConfig
from jersey_outbreak.starsim_adapter import _edge_arrays, agent_uid_mapping

ROOT = Path(__file__).resolve().parents[1]
BASE_ROOT = Path("/tmp/jos-r5a-base")


class _FakeStarsim:
    @staticmethod
    def uids(values: np.ndarray) -> np.ndarray:
        return values


def _columns_for_edges(edges: list[dict[str, object]], agent_ids: list[str]) -> EdgeColumns:
    snapshot = RouteSnapshot.from_edge_dicts(
        "fixture",
        date(2025, 1, 6),
        edges,
        {agent_id: i for i, agent_id in enumerate(agent_ids)},
        agent_ids,
    )
    return EdgeColumns(
        snapshot.p1_index,
        snapshot.p2_index,
        snapshot.weight,
        snapshot.persistence_days,
        agent_ids,
    )


def _load_base_network_generator() -> types.ModuleType:
    package_name = "_jos_r5a_base"
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


def test_columnar_dedup_and_merge_match_dict_reference() -> None:
    agent_ids = ["agent-9", "agent-10", "agent-a", "agent-z"]
    emitted = [
        _canonical_edge("agent-9", "agent-10", 0.2, 1),
        _canonical_edge("agent-10", "agent-9", 0.7, 7),
        _canonical_edge("agent-9", "agent-10", 0.7, 30),
        _canonical_edge("agent-a", "agent-z", 0.1, 1),
        _canonical_edge("agent-z", "agent-a", 0.1, 7),
    ]
    dict_emitted = [edge for edge in emitted if edge is not None]
    columns = _columns_for_edges(dict_emitted, agent_ids)
    actual = _deduplicate_edge_columns(columns)
    expected = _deduplicate_edges(dict_emitted)
    assert RouteSnapshot.from_edge_columns("fixture", date(2025, 1, 6), actual).edges == tuple(
        expected
    )

    first = [
        {"p1": "agent-10", "p2": "agent-9", "weight": 0.4, "persistence_days": 7},
        {"p1": "agent-9", "p2": "agent-z", "weight": 0.9, "persistence_days": 7},
        {"p1": "agent-a", "p2": "agent-z", "weight": 0.8, "persistence_days": 30},
    ]
    second = [
        {"p1": "agent-10", "p2": "agent-9", "weight": 0.4, "persistence_days": 1},
        {"p1": "agent-9", "p2": "agent-z", "weight": 0.3, "persistence_days": 1},
        {"p1": "agent-a", "p2": "agent-z", "weight": 0.9, "persistence_days": 1},
    ]
    # The dict reference assumes canonical input, as do the column helpers.
    first = [
        _canonical_edge(edge["p1"], edge["p2"], edge["weight"], edge["persistence_days"])
        for edge in first
    ]  # type: ignore[arg-type]
    second = [
        _canonical_edge(edge["p1"], edge["p2"], edge["weight"], edge["persistence_days"])
        for edge in second
    ]  # type: ignore[arg-type]
    first_dict = [edge for edge in first if edge is not None]
    second_dict = [edge for edge in second if edge is not None]
    actual_merge = _merge_sorted_edge_columns(
        _deduplicate_edge_columns(_columns_for_edges(first_dict, agent_ids)),
        _deduplicate_edge_columns(_columns_for_edges(second_dict, agent_ids)),
    )
    expected_merge = _merge_sorted_edges(first_dict, second_dict)
    assert RouteSnapshot.from_edge_columns(
        "fixture", date(2025, 1, 6), actual_merge
    ).edges == tuple(expected_merge)


def test_converter_preserves_dict_view_and_unknown_agent_error() -> None:
    agent_ids = ["agent-9", "agent-10"]
    edges = [
        {"p1": "agent-10", "p2": "agent-9", "weight": 0.25, "persistence_days": 3},
    ]
    snapshot = RouteSnapshot.from_edge_dicts(
        "fixture",
        date(2025, 1, 6),
        edges,
        {agent_id: i for i, agent_id in enumerate(agent_ids)},
        agent_ids,
    )
    assert snapshot.edges == tuple(edges)
    assert snapshot.p1_index.dtype == np.dtype(np.int64)
    assert snapshot.p2_index.dtype == np.dtype(np.int64)
    assert snapshot.weight.dtype == np.dtype(np.float64)
    assert snapshot.persistence_days.dtype == np.dtype(np.int64)
    assert all(
        array.flags.c_contiguous
        for array in (
            snapshot.p1_index,
            snapshot.p2_index,
            snapshot.weight,
            snapshot.persistence_days,
        )
    )
    with pytest.raises(ValueError, match="route edge references unknown JOS agent: missing"):
        RouteSnapshot.from_edge_dicts(
            "fixture",
            date(2025, 1, 6),
            [{"p1": "missing", "p2": "agent-9", "weight": 0.1, "persistence_days": 1}],
            {"agent-9": 0},
            ["agent-9"],
        )


def test_columnar_and_dict_adapter_bytes_match(m6_network) -> None:
    m2_input, m3_input = m6_network.m2_input, m6_network.m3_input
    config = NetworkGenerationConfig(mode="ci", seed=123)
    generated = generate_networks(config, m2_input, m3_input)
    uid_by_agent_id = agent_uid_mapping(generated)
    starsim = _FakeStarsim()
    dates = [*config.snapshot_dates, *[config.start_date + timedelta(days=i) for i in range(10)]]
    for route_id in sorted(generated.route_specs):
        for snapshot_date in dates:
            snapshot = generated.route_snapshot(route_id, snapshot_date)
            columnar = _edge_arrays(starsim, snapshot, uid_by_agent_id)
            columnar_container = _edge_arrays(
                starsim,
                EdgeColumns(
                    snapshot.p1_index,
                    snapshot.p2_index,
                    snapshot.weight,
                    snapshot.persistence_days,
                    snapshot.agent_ids,
                ),
                uid_by_agent_id,
            )
            dict_view = _edge_arrays(starsim, snapshot.edges, uid_by_agent_id)
            for name in ("p1", "p2", "beta"):
                assert columnar[name].dtype == dict_view[name].dtype
                assert columnar[name].shape == dict_view[name].shape
                assert columnar[name].flags.c_contiguous
                assert dict_view[name].flags.c_contiguous
                assert columnar[name].tobytes() == dict_view[name].tobytes()
                assert columnar_container[name].tobytes() == dict_view[name].tobytes()


@pytest.mark.skipif(not BASE_ROOT.exists(), reason="base comparison tree is not present")
def test_all_ci_route_snapshots_match_base(m6_network) -> None:
    m2_input, m3_input = m6_network.m2_input, m6_network.m3_input
    config = NetworkGenerationConfig(mode="ci", seed=123)
    generated = generate_networks(config, m2_input, m3_input)
    base_generator = _load_base_network_generator()
    base_generated = base_generator.generate_networks(config, m2_input, m3_input, ROOT)
    dates = [*config.snapshot_dates, *[config.start_date + timedelta(days=i) for i in range(10)]]
    for route_id in sorted(
        config.route_specs if hasattr(config, "route_specs") else generated.route_specs
    ):
        for snapshot_date in dates:
            actual = generated.route_snapshot(route_id, snapshot_date).edges
            expected = base_generated.route_snapshot(route_id, snapshot_date).edges
            assert actual == expected, (route_id, snapshot_date)
