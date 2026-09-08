"""Measure the PERF-6 scalar route loop against the vectorized implementation."""

from __future__ import annotations

import argparse
import math
import time
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import numpy as np

from jersey_outbreak.cli import _build_m4_for_m6
from jersey_outbreak.interventions import CARE_ROUTES, InterventionManager
from jersey_outbreak.scenario import load_scenario_config
from jersey_outbreak.starsim_adapter import _edge_arrays, _load_starsim, build_starsim_networks


def _scalar_apply(manager: InterventionManager, when: date, ti: int) -> None:
    """Run the pre-PERF-6 per-edge application loop as the benchmark baseline."""

    ss_module = _load_starsim()
    route_map = {str(key): route for key, route in manager.sim.networks.items()}
    for route_id in sorted(manager.generated.route_specs):
        route = route_map.get(route_id)
        if route is None:
            continue
        relevant_configs = [
            config
            for config in manager.intervention_configs
            if manager._config_can_touch_route(config, route_id, when, ti)
        ]
        if not relevant_configs:
            continue
        base_edges = list(manager.generated.route_snapshot(route_id, when).edges)
        effective_edges = []
        multipliers = []
        for edge in base_edges:
            factors = [
                manager._edge_multiplier(
                    config, route_id, str(edge["p1"]), str(edge["p2"]), when, ti
                )
                for config in relevant_configs
            ]
            factor = max(0.0, min(1.0, math.prod(factors)))
            multipliers.append(factor)
            if factor > 0 or route_id in CARE_ROUTES:
                if factor == 1.0:
                    effective_edges.append(edge)
                else:
                    effective_edges.append({**edge, "weight": float(edge["weight"]) * factor})
        if any(factor != 1.0 for factor in multipliers):
            arrays = _edge_arrays(ss_module, effective_edges, manager._uid_by_agent_id)
            route.edges.p1 = arrays["p1"]
            route.edges.p2 = arrays["p2"]
            route.edges.beta = arrays["beta"]
            route.edges.dur = np.ones(len(effective_edges), dtype=float)


def _manager(generated, scenario, seed: int, days: int) -> InterventionManager:
    manager = InterventionManager(
        generated,
        scenario.interventions,
        run_seed=seed,
        start_date=date(2025, 1, 6),
        duration_days=days,
        scenario=scenario,
    )
    for config in scenario.interventions:
        if config.type == "case_isolation":
            manager._isolation_until[config.intervention_id] = np.full(
                len(generated.agent_ids), -1, dtype=np.int64
            )
        elif config.type == "household_quarantine":
            manager._quarantine_until[config.intervention_id] = {}
    return manager


def _measure(manager: InterventionManager, days: int, *, vector: bool) -> float:
    elapsed = 0.0
    for ti in range(days):
        when = date(2025, 1, 6) + timedelta(days=ti)
        manager._refresh_wfh(when, ti)
        route_map = dict(
            zip(
                sorted(manager.generated.route_specs),
                build_starsim_networks(manager.generated),
                strict=True,
            )
        )
        manager.setattribute("sim", SimpleNamespace(networks=route_map))
        started = time.perf_counter()
        if vector:
            manager._apply_effective_routes(when, ti)
        else:
            _scalar_apply(manager, when, ti)
        elapsed += time.perf_counter() - started
    return elapsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("ci", "scaled", "full"), default="full")
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--scenario", default="m7_combined")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    scenario_path = Path(args.scenario)
    if not scenario_path.exists():
        scenario_path = root / "configs" / "scenarios" / f"{args.scenario}.yaml"
    scenario = load_scenario_config(root, scenario_path).model_copy(
        update={"seed": args.seed, "duration_days": args.days}
    )
    with TemporaryDirectory(prefix="jos-perf6-bench-") as directory:
        generated = _build_m4_for_m6(root, args.mode, args.seed, Path(directory))
        base_seconds = _measure(
            _manager(generated, scenario, args.seed, args.days), args.days, vector=False
        )
        branch_seconds = _measure(
            _manager(generated, scenario, args.seed, args.days), args.days, vector=True
        )
    print(f"mode={args.mode} seed={args.seed} days={args.days} scenario={scenario.scenario_id}")
    print(f"base_scalar_route_effect_seconds={base_seconds:.6f}")
    print(f"branch_vector_route_effect_seconds={branch_seconds:.6f}")
    print(f"speedup={base_seconds / branch_seconds:.2f}x")


if __name__ == "__main__":
    main()
