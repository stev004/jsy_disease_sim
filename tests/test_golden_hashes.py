"""Committed logical-hash contracts for the M2/M3/M4/M8 generators."""

from __future__ import annotations

import importlib.metadata
import json
import os
import subprocess
import sys
import warnings
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pytest

from jersey_outbreak.hashing import canonical_json_bytes, sha256_bytes
from jersey_outbreak.network_generator import generate_networks
from jersey_outbreak.network_schemas import NetworkGenerationConfig
from jersey_outbreak.outbreak_runner import default_run_config, load_parameter_set
from jersey_outbreak.population_artifacts import write_population_artifact
from jersey_outbreak.population_generator import GeneratedPopulation, generate_population
from jersey_outbreak.population_schemas import PopulationGenerationConfig
from jersey_outbreak.population_structure_artifacts import (
    M2PopulationInput,
    M3StructureInput,
    load_m2_population_artifact,
    load_m3_structure_artifact,
    write_structure_artifact,
)
from jersey_outbreak.population_structure_generator import GeneratedStructure, generate_structure
from jersey_outbreak.population_structure_schemas import StructureGenerationConfig
from jersey_outbreak.travel import load_travel_config, run_travel_outbreak

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "golden_logical_hashes.json"


def _load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _table_hash(rows: list[dict[str, Any]], key: str) -> str:
    return sha256_bytes(canonical_json_bytes(sorted(rows, key=lambda row: row[key])))


def _build_m2_m3(
    mode: str, seed: int, output: Path
) -> tuple[GeneratedPopulation, M2PopulationInput, GeneratedStructure, M3StructureInput]:
    population = generate_population(ROOT, PopulationGenerationConfig(mode=mode, seed=seed))
    population_artifact = write_population_artifact(population, ROOT, output / "m2")
    m2_input = load_m2_population_artifact(ROOT, population_artifact.artifact_directory)
    structure = generate_structure(ROOT, StructureGenerationConfig(mode=mode, seed=seed), m2_input)
    structure_artifact = write_structure_artifact(structure, ROOT, output / "m3", m2_input)
    m3_input = load_m3_structure_artifact(ROOT, structure_artifact.artifact_directory)
    return population, m2_input, structure, m3_input


def _build_cross_process_hashes() -> dict[str, str]:
    child = """
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from jersey_outbreak.population_artifacts import write_population_artifact
from jersey_outbreak.population_generator import generate_population
from jersey_outbreak.population_schemas import PopulationGenerationConfig
from jersey_outbreak.population_structure_artifacts import load_m2_population_artifact
from jersey_outbreak.population_structure_generator import generate_structure
from jersey_outbreak.population_structure_schemas import StructureGenerationConfig

root = Path.cwd()
with TemporaryDirectory() as directory:
    population = generate_population(root, PopulationGenerationConfig(mode="ci", seed=123))
    artifact = write_population_artifact(population, root, Path(directory) / "m2")
    m2 = load_m2_population_artifact(root, artifact.artifact_directory)
    structure = generate_structure(root, StructureGenerationConfig(mode="ci", seed=123), m2)
    print(json.dumps({"m2": population.logical_content_hash, "m3": structure.logical_content_hash}))
"""
    environment = os.environ.copy()
    source_path = str(ROOT / "src")
    environment["PYTHONPATH"] = os.pathsep.join(
        item for item in (source_path, environment.get("PYTHONPATH")) if item
    )
    completed = subprocess.run(
        [sys.executable, "-c", child],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    return json.loads(completed.stdout)


def test_cross_process_ci_baseline_matches() -> None:
    first = _build_cross_process_hashes()
    second = _build_cross_process_hashes()
    assert first == second
    expected = _load_fixture()["cross_process_baseline"]
    assert first == {
        "m2": expected["m2_logical_content_hash"],
        "m3": expected["m3_logical_content_hash"],
    }


@pytest.fixture(scope="module")
def generated_hash_inputs() -> dict[str, dict[str, Any]]:
    generated: dict[str, dict[str, Any]] = {}
    with TemporaryDirectory() as directory:
        output = Path(directory)
        for mode, seed in (("ci", 123), ("ci", 124), ("scaled", 123), ("scaled", 124)):
            population, m2, structure, m3 = _build_m2_m3(mode, seed, output / f"{mode}-{seed}")
            generated[f"{mode}-seed-{seed}"] = {
                "population": population,
                "m2": m2,
                "structure": structure,
                "m3": m3,
            }
    return generated


@pytest.mark.parametrize(
    "key",
    ("ci-seed-123", "ci-seed-124", "scaled-seed-123", "scaled-seed-124"),
)
def test_m2_m3_golden_hashes(key: str, generated_hash_inputs: dict[str, dict[str, Any]]) -> None:
    expected = _load_fixture()["generations"][key]
    generated = generated_hash_inputs[key]
    population = generated["population"]
    structure = generated["structure"]
    assert population.logical_content_hash == expected["m2_logical_content_hash"]
    assert structure.logical_content_hash == expected["m3_logical_content_hash"]

    m2_keys = {
        "residents": "agent_id",
        "households": "household_id",
        "communal_settings": "setting_id",
    }
    for table_name, checksum in expected.get("m2_table_sha256", {}).items():
        assert _table_hash(getattr(population, table_name), m2_keys[table_name]) == checksum

    m3_keys = {
        "resident_structure": "agent_id",
        "schools": "school_id",
        "classes": "class_id",
        "school_assignments": "agent_id",
        "workplaces": "workplace_id",
        "workplace_teams": "team_id",
        "job_assignments": "job_id",
    }
    for table_name, checksum in expected.get("m3_table_sha256", {}).items():
        assert _table_hash(getattr(structure, table_name), m3_keys[table_name]) == checksum


@pytest.mark.parametrize("key", ("ci-seed-123", "scaled-seed-123"))
def test_m4_golden_hash(key: str, generated_hash_inputs: dict[str, dict[str, Any]]) -> None:
    expected = _load_fixture()["generations"][key]
    generated = generated_hash_inputs[key]
    networks = generate_networks(
        NetworkGenerationConfig(
            mode=generated["m2"].manifest.mode,
            seed=generated["m2"].manifest.seed,
        ),
        generated["m2"],
        generated["m3"],
        ROOT,
    )
    assert networks.logical_content_hash == expected["m4_logical_content_hash"]


def test_m8_shipped_config_golden_hashes() -> None:
    expected = _load_fixture()["m8"]
    with TemporaryDirectory() as directory:
        _population, m2, _structure, m3 = _build_m2_m3("ci", 123, Path(directory))
        networks = generate_networks(NetworkGenerationConfig(mode="ci", seed=123), m2, m3, ROOT)
    parameters = load_parameter_set(ROOT)
    run_config = default_run_config(
        "ci",
        123,
        parameters,
        start_date=date.fromisoformat(expected["start_date"]),
        duration_days=expected["duration_days"],
    )
    for config_name, hashes in expected["configs"].items():
        result = run_travel_outbreak(
            networks,
            run_config,
            parameters,
            load_travel_config(ROOT, ROOT / "configs" / "travel" / config_name),
        )
        assert result.visitor_episode_hash == hashes["episode_hash"], config_name
        assert result.travel_plan.visitor_hash == hashes["visitor_hash"], config_name
        assert result.temporary_network_hash == hashes["temporary_network_hash"], config_name


def test_fixture_records_locked_environment_and_warns_on_numpy_drift() -> None:
    fixture = _load_fixture()
    environment = fixture["environment"]
    assert environment["python"]
    assert environment["git_commit"]
    assert fixture["generated_under"] == "uv.lock"
    ambient_numpy = importlib.metadata.version("numpy")
    if ambient_numpy != environment["numpy"]:
        warnings.warn(
            f"golden hashes were generated with numpy {environment['numpy']}; "
            f"ambient numpy is {ambient_numpy}",
            RuntimeWarning,
            stacklevel=2,
        )
