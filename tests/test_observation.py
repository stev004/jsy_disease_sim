import json
from datetime import date
from pathlib import Path

import pytest

from jersey_outbreak.hashing import canonical_json_bytes, sha256_bytes
from jersey_outbreak.observation import observe_latent_run
from jersey_outbreak.observation_artifacts import write_observation_artifact
from jersey_outbreak.observation_schemas import (
    ObservationConfig,
    ReportingDelayDistribution,
)

ROOT = Path(__file__).resolve().parents[1]


def _config_with(
    base: ObservationConfig,
    *,
    observation_config_id: str | None = None,
    reporting_delay: ReportingDelayDistribution | None = None,
    parameter_values: dict[str, float] | None = None,
) -> ObservationConfig:
    parameters = dict(base.parameters)
    for key, value in (parameter_values or {}).items():
        parameters[key] = parameters[key].model_copy(update={"value": value})
    return base.model_copy(
        update={
            "observation_config_id": observation_config_id or base.observation_config_id,
            "parameters": parameters,
            "reporting_delay": reporting_delay or base.reporting_delay,
        }
    )


def _event_hash(result) -> str:
    return sha256_bytes(canonical_json_bytes(result.latent_run.transmission_events))


def test_invalid_observation_probability_is_rejected(m6_observation_config) -> None:
    payload = m6_observation_config.model_dump(mode="json")
    payload["parameters"]["symptomatic_detection_probability"]["value"] = 1.2
    with pytest.raises(ValueError, match="outside valid_range"):
        ObservationConfig.model_validate(payload)


def test_invalid_reporting_delay_distribution_is_rejected() -> None:
    with pytest.raises(ValueError, match="exactly one day"):
        ReportingDelayDistribution(kind="fixed", days=(1, 2))
    with pytest.raises(ValueError, match="sum to one"):
        ReportingDelayDistribution(kind="discrete", days=(0, 2), probabilities=(0.2, 0.2))


def test_explicit_horizon_tail_cannot_truncate_realized_natural_history(
    m6_latent_run, m6_observation_config
) -> None:
    too_short = m6_observation_config.model_copy(update={"analysis_horizon_tail_days": 2})
    with pytest.raises(ValueError, match="tail must cover realized natural-history"):
        observe_latent_run(m6_latent_run, too_short)


def test_same_latent_run_and_observation_config_reproduce(
    m6_latent_run, m6_observation_config
) -> None:
    first = observe_latent_run(m6_latent_run, m6_observation_config)
    second = observe_latent_run(m6_latent_run, m6_observation_config)
    assert first.logical_content_hash == second.logical_content_hash
    assert first.observation_events == second.observation_events
    assert first.latent_run.logical_content_hash == m6_latent_run.logical_content_hash


def test_ascertainment_changes_observation_not_latent_run(
    m6_latent_run, m6_observation_config
) -> None:
    baseline = observe_latent_run(m6_latent_run, m6_observation_config)
    lower_detection = observe_latent_run(
        m6_latent_run,
        _config_with(
            m6_observation_config,
            parameter_values={
                "symptomatic_detection_probability": 0.05,
                "asymptomatic_detection_probability": 0.0,
            },
        ),
    )
    assert (
        baseline.latent_run.logical_content_hash == lower_detection.latent_run.logical_content_hash
    )
    assert _event_hash(baseline) == _event_hash(lower_detection)
    assert baseline.logical_content_hash != lower_detection.logical_content_hash
    assert (
        baseline.diagnostics["reported_case_count"]
        > lower_detection.diagnostics["reported_case_count"]
    )


def test_reporting_delay_shifts_reports_without_shifting_infections(
    m6_latent_run, m6_observation_config
) -> None:
    fully_detected = _config_with(
        m6_observation_config,
        parameter_values={
            "symptomatic_detection_probability": 1.0,
            "asymptomatic_detection_probability": 1.0,
        },
    )
    no_delay = observe_latent_run(
        m6_latent_run,
        _config_with(
            fully_detected,
            reporting_delay=ReportingDelayDistribution(kind="fixed", days=(0,)),
        ),
    )
    delayed = observe_latent_run(
        m6_latent_run,
        _config_with(
            fully_detected,
            reporting_delay=ReportingDelayDistribution(kind="fixed", days=(3,)),
        ),
    )
    assert [event["infection_date"] for event in no_delay.observation_events] == [
        event["infection_date"] for event in delayed.observation_events
    ]
    assert all(
        date.fromisoformat(event["report_date"]) >= date.fromisoformat(event["infection_date"])
        for event in delayed.observation_events
    )
    assert all(
        (
            date.fromisoformat(delayed_event["report_date"])
            - date.fromisoformat(base_event["report_date"])
        ).days
        == 3
        for base_event, delayed_event in zip(
            no_delay.observation_events, delayed.observation_events, strict=True
        )
    )


def test_observation_parish_and_age_aggregates_reconcile(
    m6_latent_run, m6_observation_config
) -> None:
    result = observe_latent_run(m6_latent_run, m6_observation_config)
    assert sum(row["latent_infections"] for row in result.daily_observed_cases) == len(
        result.observation_events
    )
    assert (
        sum(row["detected_infections"] for row in result.daily_observed_cases)
        == result.diagnostics["detected_event_count"]
    )
    assert (
        sum(row["reported_cases"] for row in result.daily_observed_cases)
        == result.diagnostics["reported_case_count"]
    )
    assert sum(row["new_latent_infections"] for row in result.daily_observed_parish) == len(
        result.observation_events
    )
    assert (
        sum(row["new_reported_cases"] for row in result.daily_observed_age)
        == result.diagnostics["reported_case_count"]
    )


def test_observation_artifact_contains_provenance_and_tidy_tables(
    m6_latent_run, m6_observation_config, tmp_path: Path
) -> None:
    result = observe_latent_run(m6_latent_run, m6_observation_config)
    artifact = write_observation_artifact(result, ROOT, tmp_path)
    manifest = json.loads((artifact.artifact_directory / "manifest.json").read_text())
    assert manifest["status"] == "passed"
    assert manifest["latent_run_logical_content_hash"] == m6_latent_run.logical_content_hash
    assert manifest["observation_config_id"] == m6_observation_config.observation_config_id
    for filename in (
        "daily_observed_cases.parquet",
        "daily_observed_parish.parquet",
        "daily_observed_age.parquet",
        "observation_events.parquet",
        "observation_config.json",
        "diagnostics.json",
    ):
        assert (artifact.artifact_directory / filename).exists()
