from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import jersey_outbreak.population_structure_generator as structure_generator
from jersey_outbreak.data_pipeline import DataBuildError
from jersey_outbreak.population_artifacts import write_population_artifact
from jersey_outbreak.population_generator import generate_population
from jersey_outbreak.population_schemas import PopulationGenerationConfig
from jersey_outbreak.population_structure_artifacts import load_m2_population_artifact
from jersey_outbreak.population_structure_schemas import StructureGenerationConfig

ROOT = Path(__file__).resolve().parents[1]


def _original_assign_secondary_jobs(
    jobs: list[dict[str, Any]],
    primary_workplace: dict[str, tuple[str, str | None]],
    slots_by_sector: dict[str, list[tuple[str, str | None]]],
    secondary_candidates_after_shuffle: list[str],
    secondary_count: int,
    rng: np.random.Generator,
    workplace_by_id: dict[str, dict[str, Any]],
) -> tuple[list[tuple[str, int, tuple[str, str | None]]], set[str]]:
    """Reference copy of the pre-PERF-2 secondary-job loop."""

    secondary_workers: set[str] = set()
    remaining_slots = [
        (sector, index, slot)
        for sector, slots in slots_by_sector.items()
        for index, slot in enumerate(slots)
    ]
    secondary_candidates = secondary_candidates_after_shuffle
    for _ in range(secondary_count):
        eligible = [
            agent_id
            for agent_id in secondary_candidates
            if agent_id not in secondary_workers
            and any(
                slot[0] != primary_workplace[agent_id][0]
                for _sector, _index, slot in remaining_slots
            )
        ]
        if not eligible:
            raise DataBuildError("secondary jobs cannot be assigned without workplace duplication")
        agent_id = str(rng.choice(eligible))
        primary_id = primary_workplace[agent_id][0]
        slot_index = next(
            index
            for index, (_sector, _local_index, slot) in enumerate(remaining_slots)
            if slot[0] != primary_id
        )
        sector, _local_index, (workplace_id, slot_team_id) = remaining_slots.pop(slot_index)
        slots_by_sector[sector].remove((workplace_id, slot_team_id))
        secondary_workers.add(agent_id)
        primary_jobs_for_agent = next(
            job for job in jobs if job["agent_id"] == agent_id and job["job_role"] == "primary"
        )
        primary_jobs_for_agent["days_per_week"] = 4
        workplace = workplace_by_id[workplace_id]
        jobs.append(
            {
                "job_id": f"job-m3-{len(jobs):07d}",
                "agent_id": agent_id,
                "workplace_id": workplace_id,
                "job_role": "secondary",
                "sector": workplace["sector"],
                "work_parish": workplace["work_parish"],
                "days_per_week": 1,
                "remote_days_per_week": 0,
                "team_id": slot_team_id,
                "job_universe": "synthetic_secondary",
                "employment_universe": workplace["workplace_universe"],
            }
        )
    return remaining_slots, secondary_workers


@pytest.mark.parametrize("seed", (123, 124))
def test_secondary_job_rewrite_matches_original_loop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, seed: int
) -> None:
    population = generate_population(ROOT, PopulationGenerationConfig(mode="ci", seed=seed))
    population_artifact = write_population_artifact(population, ROOT, tmp_path / "population")
    m2_input = load_m2_population_artifact(ROOT, population_artifact.artifact_directory)

    captured: dict[str, Any] = {}
    optimized = structure_generator._assign_secondary_jobs

    def capture_pre_loop_state(
        jobs: list[dict[str, Any]],
        primary_workplace: dict[str, tuple[str, str | None]],
        slots_by_sector: dict[str, list[tuple[str, str | None]]],
        secondary_candidates: list[str],
        secondary_count: int,
        rng: np.random.Generator,
        workplace_by_id: dict[str, dict[str, Any]],
    ) -> tuple[list[tuple[str, int, tuple[str, str | None]]], set[str]]:
        captured["pre"] = {
            "jobs": deepcopy(jobs),
            "primary_workplace": deepcopy(primary_workplace),
            "slots_by_sector": deepcopy(slots_by_sector),
            "secondary_candidates": list(secondary_candidates),
            "secondary_count": secondary_count,
            "rng_state": deepcopy(rng.bit_generator.state),
            "workplace_by_id": deepcopy(workplace_by_id),
        }
        optimized_jobs = deepcopy(jobs)
        optimized_primary_workplace = deepcopy(primary_workplace)
        optimized_slots_by_sector = deepcopy(slots_by_sector)
        optimized_candidates = list(secondary_candidates)
        optimized_rng = np.random.default_rng()
        optimized_rng.bit_generator.state = deepcopy(rng.bit_generator.state)
        optimized_workplace_by_id = deepcopy(workplace_by_id)
        result = optimized(
            optimized_jobs,
            optimized_primary_workplace,
            optimized_slots_by_sector,
            optimized_candidates,
            secondary_count,
            optimized_rng,
            optimized_workplace_by_id,
        )
        jobs[:] = optimized_jobs
        slots_by_sector.clear()
        slots_by_sector.update(optimized_slots_by_sector)
        rng.bit_generator.state = deepcopy(optimized_rng.bit_generator.state)
        captured["optimized_jobs"] = deepcopy(optimized_jobs)
        captured["optimized_slots_by_sector"] = deepcopy(optimized_slots_by_sector)
        captured["optimized_remaining_slots"] = deepcopy(result[0])
        captured["optimized_secondary_workers"] = deepcopy(result[1])
        captured["optimized_rng_state"] = deepcopy(rng.bit_generator.state)
        return result

    monkeypatch.setattr(structure_generator, "_assign_secondary_jobs", capture_pre_loop_state)
    generated = structure_generator.generate_structure(
        ROOT, StructureGenerationConfig(mode="ci", seed=seed), m2_input
    )

    pre = captured["pre"]
    reference_jobs = deepcopy(pre["jobs"])
    reference_slots_by_sector = deepcopy(pre["slots_by_sector"])
    reference_rng = np.random.default_rng()
    reference_rng.bit_generator.state = deepcopy(pre["rng_state"])
    reference_remaining_slots, reference_secondary_workers = _original_assign_secondary_jobs(
        reference_jobs,
        pre["primary_workplace"],
        reference_slots_by_sector,
        pre["secondary_candidates"],
        pre["secondary_count"],
        reference_rng,
        pre["workplace_by_id"],
    )

    assert reference_jobs == captured["optimized_jobs"] == generated.job_assignments
    assert reference_remaining_slots == captured["optimized_remaining_slots"]
    assert reference_slots_by_sector == captured["optimized_slots_by_sector"]
    assert reference_secondary_workers == captured["optimized_secondary_workers"]
    assert reference_rng.bit_generator.state == captured["optimized_rng_state"]


def test_generator_choice_and_integer_draws_are_identical() -> None:
    for seed in range(200):
        for length in (1, 2, 63, 64, 1000, 50000):
            candidates = [f"agent-{index}" for index in range(length)]
            choice_rng = np.random.default_rng(seed)
            integer_rng = np.random.default_rng(seed)

            choice = str(choice_rng.choice(candidates))
            indexed = candidates[int(integer_rng.integers(0, len(candidates)))]

            assert choice == indexed
            assert choice_rng.bit_generator.state == integer_rng.bit_generator.state
