from pathlib import Path

from jersey_outbreak.population_generator import generate_population
from jersey_outbreak.population_schemas import PopulationGenerationConfig

ROOT = Path(__file__).resolve().parents[1]


def test_residual_fallback_builds_frozen_failures_and_is_absent_otherwise() -> None:
    for seed, expected_parish in ((62001, "Trinity"), (62002, "St Peter")):
        generated = generate_population(ROOT, PopulationGenerationConfig(mode="ci", seed=seed))

        assert generated.diagnostics["status"] == "passed"
        disclosure = generated.diagnostics["private_assignment_residual_fallback"]
        parish_rows = {row["parish"]: row for row in disclosure["parishes"]}
        assert expected_parish in parish_rows
        assert parish_rows[expected_parish]["deferred_other_roles"] > 0

    current_seed = generate_population(ROOT, PopulationGenerationConfig(mode="ci", seed=123))
    assert current_seed.diagnostics["status"] == "passed"
    assert "private_assignment_residual_fallback" not in current_seed.diagnostics
