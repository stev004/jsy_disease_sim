"""Regression coverage for persisted M7 calendar scenario verification."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from jersey_outbreak.intervention_artifacts import write_intervention_artifact
from jersey_outbreak.intervention_schemas import InterventionConfig, ScenarioConfig
from jersey_outbreak.outbreak_runner import default_run_config, run_outbreak
from jersey_outbreak.scientific_verification import verify_scientific_artifact


def _persisted_round_trip(scenario: ScenarioConfig) -> ScenarioConfig:
    persisted = json.dumps(scenario.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    return ScenarioConfig.model_validate_json(persisted)


def test_calendar_interventions_round_trip_with_exact_semantics() -> None:
    scenario = ScenarioConfig(
        scenario_id="m9-4-calendar-round-trip",
        start_date=date(2025, 1, 6),
        duration_days=4,
        interventions=(
            InterventionConfig(
                intervention_id="school-full-closure",
                type="school_closure",
                start_date=date(2025, 1, 6),
                end_date=date(2025, 1, 7),
                class_multiplier=0.0,
                cross_class_multiplier=0.0,
            ),
            InterventionConfig(
                intervention_id="workplace-duration",
                type="workplace_reduction",
                start_date=date(2025, 1, 7),
                duration_days=2,
                release_rule="duration",
                workplace_multiplier=0.5,
            ),
        ),
    )

    reloaded = _persisted_round_trip(scenario)
    school, workplace = reloaded.interventions

    assert reloaded == scenario
    assert school.class_multiplier == 0.0
    assert school.cross_class_multiplier == 0.0
    assert [
        school.active_date_window(date(2025, 1, day), date(2025, 1, 9)) for day in (5, 6, 7, 8)
    ] == [False, True, True, False]
    assert [
        workplace.active_date_window(date(2025, 1, day), date(2025, 1, 9)) for day in (6, 7, 8, 9)
    ] == [False, True, True, False]


def test_calendar_round_trip_rejects_malformed_and_python_string_dates() -> None:
    scenario = ScenarioConfig(
        scenario_id="m9-4-malformed-date",
        interventions=(
            InterventionConfig(
                intervention_id="community-calendar",
                type="community_reduction",
                start_date=date(2025, 1, 6),
            ),
        ),
    )
    payload = scenario.model_dump(mode="json")
    payload["interventions"][0]["start_date"] = "2025-02-30"

    with pytest.raises(ValidationError, match="start_date"):
        ScenarioConfig.model_validate_json(json.dumps(payload))
    with pytest.raises(ValidationError, match="start_date"):
        InterventionConfig(
            intervention_id="python-string-date",
            type="community_reduction",
            start_date="2025-01-06",  # type: ignore[arg-type]
        )


def test_school_calendar_artifact_reloads_through_scientific_verifier(
    tmp_path: Path, m6_network, m6_parameters
) -> None:
    config = default_run_config(
        "ci", 123, m6_parameters, start_date=date(2025, 1, 6), duration_days=2
    )
    scenario = ScenarioConfig(
        scenario_id="m9-4-school-artifact",
        start_date=config.start_date,
        duration_days=config.duration_days,
        interventions=(
            InterventionConfig(
                intervention_id="school-full-closure",
                type="school_closure",
                start_date=date(2025, 1, 6),
                end_date=date(2025, 1, 6),
                class_multiplier=0.0,
                cross_class_multiplier=0.0,
            ),
        ),
    )
    result = run_outbreak(m6_network, config, m6_parameters, scenario=scenario)
    artifact = write_intervention_artifact(result, Path.cwd(), tmp_path)

    verified = verify_scientific_artifact(artifact.artifact_directory)
    persisted = verified.extra["scenario_config"]

    assert verified.artifact_type == "m7_intervention"
    assert persisted["interventions"][0]["start_date"] == "2025-01-06"
    assert persisted["interventions"][0]["end_date"] == "2025-01-06"
    assert persisted["interventions"][0]["class_multiplier"] == 0.0
    assert persisted["interventions"][0]["cross_class_multiplier"] == 0.0


@pytest.mark.parametrize("detection_triggered", [False, True])
def test_baseline_and_detection_triggered_scenarios_still_verify(
    tmp_path: Path,
    m6_network,
    m6_parameters,
    m6_observation_config,
    detection_triggered: bool,
) -> None:
    config = default_run_config(
        "ci", 123, m6_parameters, start_date=date(2025, 1, 6), duration_days=2
    )
    interventions = (
        (
            InterventionConfig(
                intervention_id="case-isolation",
                type="case_isolation",
                duration_days=2,
            ),
        )
        if detection_triggered
        else ()
    )
    scenario = ScenarioConfig(
        scenario_id=("m9-4-detection" if detection_triggered else "m9-4-baseline"),
        start_date=config.start_date,
        duration_days=config.duration_days,
        interventions=interventions,
    )
    result = run_outbreak(
        m6_network,
        config,
        m6_parameters,
        observation_config=(m6_observation_config if detection_triggered else None),
        scenario=scenario,
    )
    artifact = write_intervention_artifact(result, Path.cwd(), tmp_path)

    verified = verify_scientific_artifact(artifact.artifact_directory)

    assert verified.artifact_type == "m7_intervention"
    assert verified.extra["scenario_config"]["scenario_id"] == scenario.scenario_id
