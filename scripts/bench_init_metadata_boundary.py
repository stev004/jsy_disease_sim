"""Cross-tree PERF-1 proof and initialization benchmark."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import statistics
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import sciris as sc
import starsim as ss

from jersey_outbreak.network_generator import GeneratedNetworks, generate_networks
from jersey_outbreak.network_schemas import NetworkGenerationConfig
from jersey_outbreak.observation import load_observation_config, observe_latent_run
from jersey_outbreak.observation_scheduler import ObservationScheduler
from jersey_outbreak.outbreak_runner import default_run_config, load_parameter_set, run_outbreak
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
from jersey_outbreak.respiratory import RespiratorySEIRS
from jersey_outbreak.starsim_adapter import build_starsim_disease_sim

ROOT = Path(__file__).resolve().parents[1]
PARENT_PATHS = Path("/home/steven/jos-astra-perf-evidence-20260905/full-parent-paths.json")


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def _array_fingerprint(value: Any) -> str:
    array = np.asarray(value)
    digest = hashlib.sha256()
    digest.update(array.dtype.str.encode())
    digest.update(json.dumps(array.shape).encode())
    digest.update(np.ascontiguousarray(array).tobytes())
    return digest.hexdigest()


def _build_generated(root: Path, mode: str, seed: int, output: Path) -> GeneratedNetworks:
    m2_path: Path | None = None
    m3_path: Path | None = None
    if mode == "full" and seed == 101 and PARENT_PATHS.exists():
        parents = json.loads(PARENT_PATHS.read_text(encoding="utf-8"))
        m2_path = Path(parents["m2"])
        m3_path = Path(parents["m3"])

    if m2_path is None or m3_path is None:
        population = generate_population(root, PopulationGenerationConfig(mode=mode, seed=seed))
        population_artifact = write_population_artifact(population, root, output / "m2")
        m2_path = population_artifact.artifact_directory
        m2_input = load_m2_population_artifact(root, m2_path)
        structure = generate_structure(
            root, StructureGenerationConfig(mode=mode, seed=seed), m2_input
        )
        structure_artifact = write_structure_artifact(structure, root, output / "m3", m2_input)
        m3_path = structure_artifact.artifact_directory
    m2_input = load_m2_population_artifact(root, m2_path)
    m3_input = load_m3_structure_artifact(root, m3_path)
    return generate_networks(NetworkGenerationConfig(mode=mode, seed=seed), m2_input, m3_input)


def _build_initialized_sim(
    generated: GeneratedNetworks, config: Any, parameters: Any, observation_config: Any
) -> Any:
    route_betas = {
        route_id: config.beta * float(config.route_multipliers[route_id])
        for route_id in generated.route_specs
    }
    agent_id_by_uid = {uid: agent_id for uid, agent_id in enumerate(generated.agent_ids)}
    resident_by_agent_id = {row["agent_id"]: row for row in generated.m3_input.resident_structure}
    scheduler = ObservationScheduler(
        latent_seed=config.seed,
        start_date=config.start_date,
        config=observation_config,
        agent_id_by_uid=agent_id_by_uid,
        resident_by_agent_id=resident_by_agent_id,
    )
    disease = RespiratorySEIRS(
        route_betas=route_betas,
        initial_seed_count=config.initial_seed_count,
        initial_prevalence=config.initial_prevalence,
        import_schedule=config.import_schedule,
        import_rate_per_day=config.import_rate_per_day,
        latent_duration=config.latent_duration,
        infectious_duration=config.infectious_duration,
        immunity_duration=config.immunity_duration,
        symptomatic_probability=config.symptomatic_probability,
        waning_enabled=config.waning_enabled,
        observation_scheduler=scheduler,
    )
    return build_starsim_disease_sim(
        generated,
        disease,
        start_date=config.start_date,
        duration_days=config.duration_days,
        seed=config.seed,
    )


def _init_snapshot(sim: Any) -> dict[str, Any]:
    distributions = [
        {
            "path": str(path),
            "seed": int(dist.seed),
            "trace": str(dist.trace),
        }
        for path, dist in sim.dists.dists.items()
    ]
    rng_states: dict[str, Any] = {}
    for path, dist in sim.dists.dists.items():
        for attribute in ("rng", "_rng", "random_state"):
            candidate = getattr(dist, attribute, None)
            bit_generator = getattr(candidate, "bit_generator", None)
            if bit_generator is not None:
                rng_states[str(path)] = _jsonable(bit_generator.state)
                break

    rate_paths: dict[str, list[str]] = {}
    for name, module in [*sim.networks.items(), *sim.diseases.items()]:
        found = sc.search(module, type=ss.Rate, skip=dict(keys=["sim", "module"]))
        rate_paths[str(name)] = [str(path) for path in found]

    network_arrays: dict[str, dict[str, str]] = {}
    for name, network in sim.networks.items():
        network_arrays[str(name)] = {
            field: _array_fingerprint(getattr(network.edges, field))
            for field in ("p1", "p2", "beta")
        }

    disease = next(iter(sim.diseases.values()))
    disease_arrays = {
        field: _array_fingerprint(getattr(disease, field).values)
        for field in (
            "susceptible",
            "exposed",
            "infected",
            "recovered",
            "rel_sus",
            "rel_trans",
            "ti_exposed",
            "ti_infected",
            "ti_recovered",
            "ti_susceptible",
        )
    }
    return {
        "distributions": distributions,
        "distribution_rng_states": rng_states,
        "rate_paths": rate_paths,
        "rand_seed": int(sim.pars.rand_seed),
        "network_arrays": network_arrays,
        "disease_arrays": disease_arrays,
    }


def _run_root(
    root: Path,
    modes: list[str],
    seeds: list[int],
    days: list[int],
    *,
    run_repeats: int,
) -> dict[str, Any]:
    observation_config = load_observation_config(root)
    parameters = load_parameter_set(root)
    results: dict[str, Any] = {}
    init_timings: list[float] = []
    full_init_timings: list[float] = []
    online_timings: dict[str, list[float]] = {f"{mode}:{day}": [] for mode in modes for day in days}

    with tempfile.TemporaryDirectory(prefix="jos-perf1-bench-") as temporary:
        cache: dict[tuple[str, int], GeneratedNetworks] = {}
        for mode in modes:
            for seed in seeds:
                generated = cache.setdefault(
                    (mode, seed),
                    _build_generated(root, mode, seed, Path(temporary) / f"{mode}-{seed}"),
                )
                for repetition in range(2 if mode == "full" else 1):
                    config = default_run_config(mode, seed, parameters, duration_days=max(days))
                    started = time.perf_counter()
                    sim = _build_initialized_sim(generated, config, parameters, observation_config)
                    init_elapsed = time.perf_counter() - started
                    init_timings.append(init_elapsed)
                    if mode == "full":
                        full_init_timings.append(init_elapsed)
                    if repetition == 0:
                        init_snapshot = _init_snapshot(sim)

                for day in days:
                    config = default_run_config(mode, seed, parameters, duration_days=day)
                    run_key = f"{mode}:{seed}:{day}"
                    runs: list[dict[str, Any]] = []
                    for _ in range(run_repeats):
                        started = time.perf_counter()
                        latent = run_outbreak(
                            generated,
                            config,
                            parameters,
                            observation_config=observation_config,
                        )
                        observed = observe_latent_run(latent, observation_config)
                        elapsed = time.perf_counter() - started
                        online_timings[f"{mode}:{day}"].append(elapsed)
                        event_bytes = json.dumps(
                            latent.transmission_events,
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode()
                        runs.append(
                            {
                                "latent_hash": latent.logical_content_hash,
                                "latent_outcome_hash": latent.latent_outcome_hash,
                                "observed_hash": observed.logical_content_hash,
                                "transmission_events": latent.transmission_events,
                                "event_sha256": hashlib.sha256(event_bytes).hexdigest(),
                                "event_count": len(latent.transmission_events),
                                "elapsed_s": elapsed,
                            }
                        )
                    results[run_key] = {
                        "init": init_snapshot,
                        "network_hash": generated.logical_content_hash,
                        "runs": runs,
                    }
    return {
        "results": results,
        "init_timings_s": init_timings,
        "full_init_timings_s": full_init_timings,
        "online_timings_s": online_timings,
    }


def _ensure_base_tree(base_sha: str, root: Path) -> Path:
    base_root = Path("/tmp/jos-perf1-base")
    if not (base_root / "pyproject.toml").exists():
        base_root.mkdir(parents=True, exist_ok=True)
        archive = subprocess.run(
            ["git", "archive", base_sha], cwd=root, check=True, capture_output=True
        ).stdout
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
            tar.extractall(base_root)
        subprocess.run(["uv", "sync", "--frozen"], cwd=base_root, check=True)
    return base_root


def _run_base_subprocess(
    script: Path, base_root: Path, modes: list[str], seeds: list[int], days: list[int]
) -> dict[str, Any]:
    child_args = [
        str(script),
        "--child",
        "--root",
        str(base_root),
        "--modes",
        *modes,
        "--seeds",
        *(str(seed) for seed in seeds),
        "--days",
        *(str(day) for day in days),
    ]
    child_code = (
        f"import runpy,sys; sys.argv={child_args!r}; "
        f"runpy.run_path({str(script)!r}, run_name='__main__')"
    )
    environment = os.environ.copy()
    environment.setdefault("MPLCONFIGDIR", "/tmp/mpl-jos-perf1")
    completed = subprocess.run(
        ["uv", "run", "python", "-c", child_code],
        cwd=base_root,
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    return json.loads(completed.stdout.strip().splitlines()[-1])


def _compare(base: dict[str, Any], branch: dict[str, Any]) -> dict[str, Any]:
    base_results = base["results"]
    branch_results = branch["results"]
    keys_equal = sorted(base_results) == sorted(branch_results)
    common = sorted(set(base_results) & set(branch_results))
    distribution_equal = keys_equal and all(
        base_results[key]["init"]["distributions"] == branch_results[key]["init"]["distributions"]
        and base_results[key]["init"]["rate_paths"] == branch_results[key]["init"]["rate_paths"]
        for key in common
    )
    seed_equal = keys_equal and all(
        base_results[key]["init"]["rand_seed"] == branch_results[key]["init"]["rand_seed"]
        and base_results[key]["init"]["distributions"]
        == branch_results[key]["init"]["distributions"]
        and base_results[key]["init"]["distribution_rng_states"]
        == branch_results[key]["init"]["distribution_rng_states"]
        for key in common
    )
    arrays_equal = keys_equal and all(
        base_results[key]["init"]["network_arrays"] == branch_results[key]["init"]["network_arrays"]
        and base_results[key]["init"]["disease_arrays"]
        == branch_results[key]["init"]["disease_arrays"]
        for key in common
    )
    hashes_equal = keys_equal and all(
        [
            (base_results[key]["runs"][0][field] == branch_results[key]["runs"][0][field])
            for key in common
            for field in ("latent_hash", "latent_outcome_hash", "observed_hash")
        ]
    )
    lifecycle_equal = keys_equal and all(
        base_results[key]["runs"][0]["transmission_events"]
        == branch_results[key]["runs"][0]["transmission_events"]
        for key in common
    )
    route_equal = keys_equal and all(
        base_results[key]["network_hash"] == branch_results[key]["network_hash"] for key in common
    )
    return {
        "ordered_distribution_and_rate_paths_equal": distribution_equal,
        "distribution_seeds_and_rng_states_equal": seed_equal,
        "initialized_arrays_bit_equal": arrays_equal,
        "all_scientific_hashes_equal": hashes_equal,
        "all_route_and_array_fingerprints_equal": route_equal,
        "lifecycle_and_consumer_order_equal": lifecycle_equal,
    }


def _median_or_none(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base")
    parser.add_argument("--modes", nargs="+", choices=("ci", "full"), required=True)
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--days", nargs="+", type=int, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.child:
        payload = _run_root(args.root, args.modes, args.seeds, args.days, run_repeats=1)
        print(json.dumps(payload, separators=(",", ":")))
        return 0
    if args.base is None or args.out is None:
        raise SystemExit("--base and --out are required")

    branch = _run_root(args.root, args.modes, args.seeds, args.days, run_repeats=2)
    base_root = _ensure_base_tree(args.base, args.root)
    base = _run_base_subprocess(
        Path(__file__).resolve(), base_root, args.modes, args.seeds, args.days
    )
    comparisons = _compare(base, branch)

    route_test = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/test_bench_dynamic_routes.py"],
        cwd=args.root,
        capture_output=True,
        text=True,
    )
    comparisons["all_route_and_array_fingerprints_equal"] = (
        comparisons["all_route_and_array_fingerprints_equal"] and route_test.returncode == 0
    )
    proof = {
        **comparisons,
        "route_test_exit_code": route_test.returncode,
        "base_sha": args.base,
        "full_online_init_median_s": _median_or_none(branch["full_init_timings_s"]),
        "full_online_7d_median_s": _median_or_none(branch["online_timings_s"].get("full:7", [])),
        "full_online_30d_median_s": _median_or_none(branch["online_timings_s"].get("full:30", [])),
        "cases": {
            key: {
                "network_hash": value["network_hash"],
                "latent_hash": value["runs"][0]["latent_hash"],
                "latent_outcome_hash": value["runs"][0]["latent_outcome_hash"],
                "observed_hash": value["runs"][0]["observed_hash"],
                "event_count": value["runs"][0]["event_count"],
                "event_sha256": value["runs"][0]["event_sha256"],
            }
            for key, value in branch["results"].items()
        },
    }
    args.out.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(proof, indent=2, sort_keys=True))
    return 0 if all(value is True for value in comparisons.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
