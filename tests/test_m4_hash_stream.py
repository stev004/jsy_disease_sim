from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from jersey_outbreak.hashing import (
    canonical_json_bytes,
    iter_canonical_json_chunks,
    sha256_bytes,
)
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


def test_m4_stream_hash_matches_golden_and_eager_payload() -> None:
    with TemporaryDirectory() as directory:
        output = Path(directory)
        population = generate_population(ROOT, PopulationGenerationConfig(mode="ci", seed=123))
        population_artifact = write_population_artifact(population, ROOT, output / "m2")
        m2_input = load_m2_population_artifact(ROOT, population_artifact.artifact_directory)
        structure = generate_structure(
            ROOT, StructureGenerationConfig(mode="ci", seed=123), m2_input
        )
        structure_artifact = write_structure_artifact(structure, ROOT, output / "m3", m2_input)
        m3_input = load_m3_structure_artifact(ROOT, structure_artifact.artifact_directory)
        generated = generate_networks(
            NetworkGenerationConfig(mode="ci", seed=123), m2_input, m3_input, ROOT
        )

    payload: dict[str, Any] = {
        "agent_ids": generated.agent_ids,
        "route_specs": generated.route_specs,
        "structural_edges": generated.structural_edges,
        "memberships": generated.route_memberships,
        "school_staff_assignments": generated.school_staff_assignments,
        "care_staff_assignments": generated.care_staff_assignments,
        "staffing_provenance": generated.staffing_provenance,
        "snapshots": {
            route_id: [
                {
                    "date": when.isoformat(),
                    "edges": list(generated.route_snapshot(route_id, when).edges),
                }
                for when in generated.config.snapshot_dates
            ]
            for route_id in sorted(generated.route_specs)
        },
    }
    eager_bytes = canonical_json_bytes(payload)
    assert b"".join(iter_canonical_json_chunks(payload)) == eager_bytes
    assert generated.logical_content_hash == sha256_bytes(eager_bytes)

    fixture = json.loads(
        (ROOT / "tests" / "fixtures" / "golden_logical_hashes.json").read_text(encoding="utf-8")
    )
    assert (
        generated.logical_content_hash
        == fixture["generations"]["ci-seed-123"]["m4_logical_content_hash"]
    )
