"""Contract tests for the Milestone 7 intervention framework."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from jersey_outbreak.intervention_artifacts import write_intervention_artifact
from jersey_outbreak.intervention_schemas import (
    InterventionConfig,
    ScenarioConfig,
    TargetPopulation,
)
from jersey_outbreak.outbreak_runner import run_outbreak


def _calendar_intervention(intervention_id: str, intervention_type: str, **kwargs):
    return InterventionConfig(
        intervention_id=intervention_id,
        type=intervention_type,
        start_date=date(2025, 1, 13),
        **kwargs,
    )


def _all_detected_observation(base):
    parameters = {
        key: parameter.model_copy(
            update={
                "value": 1.0
                if key
                in {
                    "symptomatic_probability",
                    "symptomatic_detection_probability",
                    "asymptomatic_detection_probability",
                }
                else parameter.value
            }
        )
        for key, parameter in base.parameters.items()
    }
    fixed_delay = base.reporting_delay.model_copy(update={"kind": "fixed", "days": (0,)})
    return base.model_copy(
        update={
            "observation_config_id": "m7-causal-test",
            "parameters": parameters,
            "symptom_onset_delay": fixed_delay,
            "detection_delay": fixed_delay,
            "reporting_delay": fixed_delay,
            "day_of_week_effect": (1.0,) * 7,
            "analysis_horizon_tail_days": None,
        }
    )


def test_intervention_schema_enforces_lifecycle_and_hashes() -> None:
    detection = InterventionConfig(
        intervention_id="isolation",
        type="case_isolation",
        duration_days=5,
    )
    assert detection.activation_rule == "detection_triggered"
    assert len(detection.config_hash) == 64
    scenario = ScenarioConfig(scenario_id="schema-test", interventions=(detection,))
    assert (
        scenario.config_hash
        == ScenarioConfig(scenario_id="schema-test", interventions=(detection,)).config_hash
    )

    with pytest.raises(ValueError, match="requires duration_days"):
        InterventionConfig(intervention_id="invalid", type="household_quarantine")
    with pytest.raises(ValueError, match="requires start_date"):
        InterventionConfig(intervention_id="invalid", type="school_closure")
    with pytest.raises(ValueError, match="unknown M4 routes"):
        _calendar_intervention("invalid", "masking", route_effects={"airport": 0.0})


def test_neutral_intervention_preserves_m5_outputs(
    m6_network, m6_parameters, m6_base_config
) -> None:
    config = m6_base_config.model_copy(
        update={"beta": 0.35, "duration_days": 4, "initial_seed_count": 8}
    )
    baseline = run_outbreak(m6_network, config, m6_parameters)
    neutral = run_outbreak(
        m6_network,
        config,
        m6_parameters,
        scenario=ScenarioConfig(
            scenario_id="neutral-school",
            start_date=config.start_date,
            duration_days=config.duration_days,
            interventions=(
                InterventionConfig(
                    intervention_id="neutral-school-closure",
                    type="school_closure",
                    start_date=config.start_date,
                    class_multiplier=1.0,
                    cross_class_multiplier=1.0,
                ),
            ),
        ),
    )
    assert neutral.generated.logical_content_hash == baseline.generated.logical_content_hash
    assert neutral.daily_epidemic == baseline.daily_epidemic
    assert neutral.daily_route == baseline.daily_route
    assert neutral.transmission_events == baseline.transmission_events
    assert neutral.daily_parish == baseline.daily_parish
    assert neutral.daily_age == baseline.daily_age
    assert neutral.latent_outcome_hash == baseline.latent_outcome_hash
    assert neutral.logical_content_hash == baseline.logical_content_hash
    assert all(
        row["representation"] == "canonical_reused" for row in neutral.intervention_route_effects
    )
    assert neutral.intervention_diagnostics["composition"]["canonical_network_mutated"] is False


def test_detection_effect_starts_after_detection_timestep(
    m6_network, m6_parameters, m6_base_config, m6_observation_config
) -> None:
    config = m6_base_config.model_copy(
        update={"beta": 0.0, "duration_days": 4, "initial_seed_count": 2}
    )
    scenario = ScenarioConfig(
        scenario_id="causal-isolation",
        start_date=config.start_date,
        duration_days=config.duration_days,
        interventions=(
            InterventionConfig(
                intervention_id="isolation",
                type="case_isolation",
                duration_days=2,
            ),
        ),
    )
    result = run_outbreak(
        m6_network,
        config,
        m6_parameters,
        observation_config=_all_detected_observation(m6_observation_config),
        scenario=scenario,
    )
    assert result.observation_schedule is not None
    detection_times = {
        (
            f"detection:{event.agent_id}:{event.detection_date}:{event.detection_reason}"
        ): event.detection_time_index
        for event in result.observation_schedule.delivered_detection_events
    }
    entered = [
        event
        for event in result.intervention_events
        if event["action"] == "agent_entered_isolation"
    ]
    assert entered
    assert all(
        event["time_index"] == detection_times[event["detection_event_reference"]] + 1
        for event in entered
    )
    assert all(
        event["time_index"] > detection_times[event["detection_event_reference"]]
        for event in entered
    )


@pytest.fixture(scope="module")
def m7_calendar_run(m6_network, m6_parameters, m6_base_config):
    config = m6_base_config.model_copy(
        update={
            "start_date": date(2025, 1, 13),
            "duration_days": 3,
            "beta": 0.0,
            "initial_seed_count": 0,
        }
    )
    scenario = ScenarioConfig(
        scenario_id="calendar-families",
        start_date=config.start_date,
        duration_days=config.duration_days,
        interventions=(
            _calendar_intervention(
                "school-close",
                "school_closure",
                class_multiplier=0.0,
                cross_class_multiplier=0.0,
            ),
            _calendar_intervention(
                "wfh",
                "workplace_reduction",
                target=TargetPopulation(age_bands=("18-64",), worker_only=True),
                additional_wfh_fraction=1.0,
            ),
            _calendar_intervention(
                "indoor-reduction",
                "community_reduction",
                indoor_multiplier=0.0,
                outdoor_multiplier=1.0,
            ),
            _calendar_intervention(
                "care-protection",
                "care_home_protection",
                care_contact_multiplier=0.0,
                care_external_resident_multiplier=0.0,
                care_external_staff_multiplier=0.0,
            ),
            _calendar_intervention(
                "vaccination",
                "vaccination",
                target=TargetPopulation(age_bands=("65+",)),
                coverage_target=1.0,
                rollout_rate=1.0,
                protection_delay_days=1,
                efficacy_susceptibility=1.0,
                efficacy_infectiousness=1.0,
            ),
        ),
    )
    return run_outbreak(m6_network, config, m6_parameters, scenario=scenario)


def test_calendar_families_apply_route_effects_without_mutating_m4(m7_calendar_run) -> None:
    result = m7_calendar_run
    assert (
        result.generated.logical_content_hash
        == result.diagnostics["network_immutability"]["before_logical_content_hash"]
    )
    by_date_route = {
        (row["date"], row["route_id"]): row for row in result.intervention_route_effects
    }
    indoor = by_date_route[("2025-01-13", "community_indoor")]
    assert indoor["effective_edge_count"] < indoor["base_edge_count"]
    workplace = by_date_route[("2025-01-13", "workplace_team")]
    assert workplace["suppressed_edge_count"] > 0
    care = by_date_route[("2025-01-13", "care_resident")]
    assert care["effective_edge_count"] == care["base_edge_count"]
    assert care["mean_multiplier"] == 0.0
    school = by_date_route[("2025-01-13", "school_class")]
    assert school["effective_edge_count"] <= school["base_edge_count"]


def test_vaccination_delay_and_artifact_contract(m7_calendar_run, tmp_path: Path) -> None:
    result = m7_calendar_run
    administered = [
        event for event in result.intervention_events if event["action"] == "vaccine_administered"
    ]
    effective = [
        event
        for event in result.intervention_events
        if event["action"] == "protection_became_effective"
    ]
    assert administered
    assert effective
    assert min(event["time_index"] for event in effective) >= 1
    artifact = write_intervention_artifact(result, Path.cwd(), tmp_path)
    assert artifact.manifest.scenario_hash == result.scenario_hash
    for filename in (
        "daily_intervention_state.parquet",
        "intervention_events.parquet",
        "route_effects.parquet",
        "scenario_config.json",
        "diagnostics.json",
        "manifest.json",
    ):
        assert (artifact.artifact_directory / filename).exists()
    manifest = json.loads((artifact.artifact_directory / "manifest.json").read_text())
    assert manifest["intervention_framework_version"] == "7.0.0"
    assert manifest["m4_logical_content_hash"] == result.generated.logical_content_hash
