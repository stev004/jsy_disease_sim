"""ROUTE-4 weekday memo equivalence and bounded-storage contracts."""

from __future__ import annotations

import importlib.util
import sys
import types
from datetime import date, timedelta
from pathlib import Path

import pytest

from jersey_outbreak.network_generator import EdgeColumns, GeneratedNetworks, generate_networks
from jersey_outbreak.network_schemas import NetworkGenerationConfig
from jersey_outbreak.starsim_adapter import _edge_arrays

ROOT = Path(__file__).resolve().parents[1]
BASE_ROOT = Path("/tmp/jos-r4-base")


class _FakeStarsim:
    @staticmethod
    def uids(values):
        return values


def _load_base_network_generator() -> types.ModuleType:
    package_name = "_jos_r4_base"
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


def _freevars(function):
    return dict(
        zip(
            function.__code__.co_freevars,
            (cell.cell_contents for cell in function.__closure__ or ()),
            strict=True,
        )
    )


def _assert_route_equal(
    actual: GeneratedNetworks, expected: GeneratedNetworks, route_id: str, when: date
) -> None:
    actual_edges = actual.route_snapshot(route_id, when).edges
    expected_edges = expected.route_snapshot(route_id, when).edges
    if actual_edges != expected_edges:
        for row, (actual_edge, expected_edge) in enumerate(
            zip(actual_edges, expected_edges, strict=True)
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


@pytest.mark.skipif(not BASE_ROOT.exists(), reason="ROUTE-4 parent comparison tree is not present")
def test_workplace_weekday_memos_match_parent_for_180_dates(m6_network) -> None:
    config = NetworkGenerationConfig(mode="ci", seed=123)
    branch = generate_networks(config, m6_network.m2_input, m6_network.m3_input, ROOT)
    base_generator = _load_base_network_generator()
    base = base_generator.generate_networks(config, m6_network.m2_input, m6_network.m3_input, ROOT)

    branch._snapshot_cache.clear()
    base._snapshot_cache.clear()
    uid_by_agent_id = {agent_id: index for index, agent_id in enumerate(branch.agent_ids)}
    for day_offset in range(180):
        when = config.start_date + timedelta(days=day_offset)
        for route_id in ("workplace_team", "workplace_transient"):
            _assert_route_equal(branch, base, route_id, when)
        actual_arrays = _edge_arrays(
            _FakeStarsim(), branch.route_snapshot("workplace_team", when), uid_by_agent_id
        )
        expected_snapshot = base.route_snapshot("workplace_team", when)
        expected_arrays = _edge_arrays(_FakeStarsim(), expected_snapshot.edges, uid_by_agent_id)
        for name in ("p1", "p2", "beta"):
            assert actual_arrays[name].dtype == expected_arrays[name].dtype
            assert actual_arrays[name].shape == expected_arrays[name].shape
            assert actual_arrays[name].tobytes() == expected_arrays[name].tobytes(), (
                "workplace_team array bytes differ",
                when,
                name,
            )

    team_builder = branch._dynamic_builders["workplace_team"]
    transient_builder = branch._dynamic_builders["workplace_transient"]
    team_memo = _freevars(team_builder)["workplace_team_columns_by_weekday"]
    transient_memo = _freevars(transient_builder)["workplace_transient_groups_by_weekday"]
    assert len(team_memo) <= 5
    assert set(team_memo) <= set(range(5))
    assert all(isinstance(columns, EdgeColumns) for columns in team_memo.values())
    assert len(transient_memo) <= 5
    assert set(transient_memo) <= set(range(5))
    assert all(isinstance(groups, list) for groups in transient_memo.values())
