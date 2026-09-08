"""Benchmark full versus internal M4 diagnostics construction."""

from __future__ import annotations

import argparse
import json
import statistics
import tempfile
import time
from pathlib import Path

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

ROOT = Path(__file__).resolve().parents[1]
PARENT_PATHS = Path("/home/steven/jos-astra-perf-evidence-20260905/full-parent-paths.json")


def _positive_repeats(value: str) -> int:
    repeats = int(value)
    if repeats < 1:
        raise argparse.ArgumentTypeError("repeats must be at least 1")
    return repeats


def _load_parents(mode: str, seed: int, scratch: Path):
    if mode == "full" and seed == 101 and PARENT_PATHS.exists():
        parents = json.loads(PARENT_PATHS.read_text(encoding="utf-8"))
        m2_path = Path(parents["m2"])
        m3_path = Path(parents["m3"])
    else:
        population = generate_population(ROOT, PopulationGenerationConfig(mode=mode, seed=seed))
        population_artifact = write_population_artifact(population, ROOT, scratch / "m2")
        m2_path = population_artifact.artifact_directory
        m2_input = load_m2_population_artifact(ROOT, m2_path)
        structure = generate_structure(
            ROOT, StructureGenerationConfig(mode=mode, seed=seed), m2_input
        )
        structure_artifact = write_structure_artifact(structure, ROOT, scratch / "m3", m2_input)
        m3_path = structure_artifact.artifact_directory
    return (
        load_m2_population_artifact(ROOT, m2_path),
        load_m3_structure_artifact(ROOT, m3_path),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("ci", "full"), default="full")
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--repeats", type=_positive_repeats, default=5)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="jos-perf4-diagnostics-") as directory:
        m2_input, m3_input = _load_parents(args.mode, args.seed, Path(directory))
        config = NetworkGenerationConfig(mode=args.mode, seed=args.seed)
        timings: dict[str, list[float]] = {"full": [], "internal": []}
        for repeat in range(1, args.repeats + 1):
            for diagnostics in ("full", "internal"):
                started = time.perf_counter()
                generated = generate_networks(
                    config,
                    m2_input,
                    m3_input,
                    ROOT,
                    diagnostics=diagnostics,
                )
                elapsed = time.perf_counter() - started
                timings[diagnostics].append(elapsed)
                print(f"repeat {repeat}: {diagnostics}={elapsed:.3f} s")
                if generated.logical_content_hash == "":
                    raise AssertionError("M4 generation returned an empty logical hash")

    full_median = statistics.median(timings["full"])
    internal_median = statistics.median(timings["internal"])
    saving = full_median - internal_median
    print(f"median(full): {full_median:.3f} s")
    print(f"median(internal): {internal_median:.3f} s")
    print(f"median saving: {saving:.3f} s")
    decision = "SHIP" if saving >= 5.0 else "NO-GO"
    print(f"ship decision: {decision} (requirement: >= 5.0 s)")
    return 0 if decision == "SHIP" else 2


if __name__ == "__main__":
    raise SystemExit(main())
