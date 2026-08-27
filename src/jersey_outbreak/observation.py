"""Standalone latent-to-observed transformation for Milestone 6."""

from __future__ import annotations

import platform
import resource
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from .hashing import canonical_json_bytes, sha256_bytes
from .observation_scheduler import DetectionEvent, build_offline_schedule
from .observation_schemas import ObservationConfig
from .outbreak_runner import OutbreakRunResult


def load_observation_config(root: Path, path: Path | None = None) -> ObservationConfig:
    """Load and strictly validate an observation YAML configuration."""

    config_path = path or root / "configs" / "observation" / "observation_demo.yaml"
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            for entry in payload.get("parameters", {}).values():
                if isinstance(entry, dict) and isinstance(entry.get("valid_range"), list):
                    entry["valid_range"] = tuple(entry["valid_range"])
            delay = payload.get("reporting_delay")
            if isinstance(delay, dict):
                if isinstance(delay.get("days"), list):
                    delay["days"] = tuple(delay["days"])
                if isinstance(delay.get("probabilities"), list):
                    delay["probabilities"] = tuple(delay["probabilities"])
            if isinstance(payload.get("day_of_week_effect"), list):
                payload["day_of_week_effect"] = tuple(payload["day_of_week_effect"])
        return ObservationConfig.model_validate(payload)
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        raise ValueError(f"invalid observation configuration {config_path}: {exc}") from exc


@dataclass(frozen=True)
class ObservationRunResult:
    """Plain-Python observation tables derived from one immutable M5 run."""

    latent_run: OutbreakRunResult
    config: ObservationConfig
    daily_observed_cases: list[dict[str, Any]]
    daily_observed_parish: list[dict[str, Any]]
    daily_observed_age: list[dict[str, Any]]
    observation_events: list[dict[str, Any]]
    detection_events: tuple[DetectionEvent, ...]
    diagnostics: dict[str, Any]
    logical_content_hash: str
    runtime_seconds: float
    peak_memory_bytes: int | None

    def iter_detection_events(self):
        """Expose detection notifications without exposing a route mutator."""

        return iter(self.detection_events)


def _date_range(start: date, end: date) -> list[date]:
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def _maximum_delay(distribution: Any) -> int:
    return max(int(day) for day in distribution.days)


def observe_latent_run(
    latent_run: OutbreakRunResult,
    config: ObservationConfig,
) -> ObservationRunResult:
    """Apply observation-only randomness without touching the M5 result.

    The output horizon is the complete latent horizon plus the configured or
    derived maximum observation-delay tail. All aggregation is built from
    pre-indexed event counters so zero-valued dates remain explicit.
    """

    started = time.perf_counter()
    before_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    m3_by_agent = {row["agent_id"]: row for row in latent_run.generated.m3_input.resident_structure}
    agent_id_by_uid = {uid: agent_id for uid, agent_id in enumerate(latent_run.generated.agent_ids)}
    offline_schedule = build_offline_schedule(
        latent_run.transmission_events,
        latent_seed=latent_run.config.seed,
        start_date=latent_run.config.start_date,
        config=config,
        agent_id_by_uid=agent_id_by_uid,
        resident_by_agent_id=m3_by_agent,
    )
    observation_events = list(offline_schedule.observation_events)
    detection_events = offline_schedule.detection_events
    detection_payloads = [
        {**event.__dict__, "provenance": dict(event.provenance)} for event in detection_events
    ]
    online_schedule = latent_run.observation_schedule
    online_agreement = None
    if online_schedule is not None:
        online_payloads = [
            {**event.__dict__, "provenance": dict(event.provenance)}
            for event in online_schedule.detection_events
        ]
        online_agreement = (
            online_schedule.observation_events == offline_schedule.observation_events
            and online_payloads == detection_payloads
            and online_schedule.stream_fingerprint == offline_schedule.stream_fingerprint
        )
        if not online_agreement:
            raise RuntimeError("offline observation schedule disagrees with runtime schedule")

    latent_start = date.fromisoformat(latent_run.daily_epidemic[0]["date"])
    latent_end = date.fromisoformat(latent_run.daily_epidemic[-1]["date"])
    derived_tail = sum(
        _maximum_delay(distribution)
        for distribution in (
            config.symptom_onset_delay,
            config.detection_delay,
            config.reporting_delay,
        )
    )
    horizon_tail = (
        config.analysis_horizon_tail_days
        if config.analysis_horizon_tail_days is not None
        else derived_tail
    )
    dates = _date_range(latent_start, latent_end + timedelta(days=horizon_tail))
    latent_by_date = Counter(event["infection_date"] for event in observation_events)
    detected_by_date = Counter(
        event["detection_date"] for event in observation_events if event["detection_date"]
    )
    reported_by_date = Counter(
        event["report_date"] for event in observation_events if event["report_date"] is not None
    )
    delays_by_report_date: dict[str, list[int]] = defaultdict(list)
    for event in observation_events:
        if event["report_date"] is not None:
            delays_by_report_date[event["report_date"]].append(event["reporting_delay_days"])
    parish_by_date: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    age_by_date: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for event in observation_events:
        parish = event["home_parish"]
        age_band = event["age_band"]
        parish_by_date[(event["infection_date"], parish)]["latent"] += 1
        age_by_date[(event["infection_date"], age_band)]["latent"] += 1
        if event["detection_date"] is not None:
            parish_by_date[(event["detection_date"], parish)]["detected"] += 1
            age_by_date[(event["detection_date"], age_band)]["detected"] += 1
        if event["report_date"] is not None:
            parish_by_date[(event["report_date"], parish)]["reported"] += 1
            age_by_date[(event["report_date"], age_band)]["reported"] += 1
    daily_observed_cases: list[dict[str, Any]] = []
    for when in dates:
        date_key = when.isoformat()
        latent = latent_by_date[date_key]
        delays = delays_by_report_date[date_key]
        daily_observed_cases.append(
            {
                "date": date_key,
                "latent_infections": latent,
                "detected_infections": detected_by_date[date_key],
                "reported_cases": reported_by_date[date_key],
                "ascertainment_fraction": detected_by_date[date_key] / latent if latent else None,
                "mean_reporting_delay_days": sum(delays) / len(delays) if delays else None,
            }
        )

    parishes = sorted(
        {row["home_parish"] for row in latent_run.generated.m3_input.resident_structure}
    )
    age_bands = ("0-4", "5-17", "18-64", "65+")
    daily_observed_parish: list[dict[str, Any]] = []
    daily_observed_age: list[dict[str, Any]] = []
    for when in dates:
        date_key = when.isoformat()
        for parish in parishes:
            counts = parish_by_date[(date_key, parish)]
            daily_observed_parish.append(
                {
                    "date": date_key,
                    "parish": parish,
                    "new_latent_infections": counts["latent"],
                    "new_detected_infections": counts["detected"],
                    "new_reported_cases": counts["reported"],
                }
            )
        for age_band in age_bands:
            counts = age_by_date[(date_key, age_band)]
            daily_observed_age.append(
                {
                    "date": date_key,
                    "age_band": age_band,
                    "new_latent_infections": counts["latent"],
                    "new_detected_infections": counts["detected"],
                    "new_reported_cases": counts["reported"],
                }
            )

    detected_count = sum(event["detected"] for event in observation_events)
    delays = [
        int(event["reporting_delay_days"])
        for event in observation_events
        if event["reporting_delay_days"] is not None
    ]
    chronology_violations = [
        event
        for event in observation_events
        if (
            event["symptom_onset_date"] is not None
            and event["symptom_onset_date"] < event["infection_date"]
        )
        or (
            event["detection_date"] is not None
            and (
                event["detection_date"] < event["infection_date"]
                or (
                    event["symptom_onset_date"] is not None
                    and event["detection_date"] < event["symptom_onset_date"]
                )
            )
        )
        or (
            event["report_date"] is not None
            and (event["detection_date"] is None or event["report_date"] < event["detection_date"])
        )
    ]
    latent_conservation_difference = sum(
        row["latent_infections"] for row in daily_observed_cases
    ) - len(observation_events)
    no_report_before_infection = not chronology_violations
    diagnostics: dict[str, Any] = {
        "status": "passed" if no_report_before_infection else "failed",
        "latent_run_logical_content_hash": latent_run.logical_content_hash,
        "latent_event_count": len(observation_events),
        "detected_event_count": detected_count,
        "reported_case_count": sum(
            event["report_date"] is not None for event in observation_events
        ),
        "ascertainment_fraction": detected_count / len(observation_events)
        if observation_events
        else 0.0,
        "reporting_delay_summary": {
            "min_days": min(delays) if delays else None,
            "max_days": max(delays) if delays else None,
            "mean_days": sum(delays) / len(delays) if delays else None,
        },
        "no_report_before_infection": no_report_before_infection,
        "chronology_violations": len(chronology_violations),
        "latent_incidence_conservation_difference": latent_conservation_difference,
        "latent_incidence_conservation": latent_conservation_difference == 0,
        "infection_date_semantics": "Copied from immutable M5 latent event date.",
        "symptom_onset_date_semantics": (
            "Optional infection date plus the configured generic symptom-onset delay; "
            "not a named-pathogen natural-history claim."
        ),
        "detection_date_semantics": (
            "Optional symptom onset (or infection for asymptomatic cases) plus the configured "
            "generic detection/testing delay."
        ),
        "report_date_semantics": "Detection date plus the configured non-negative reporting delay.",
        "analysis_horizon": {
            "latent_start": latent_start.isoformat(),
            "latent_end": latent_end.isoformat(),
            "observation_end": dates[-1].isoformat(),
            "tail_days": horizon_tail,
            "tail_source": (
                "explicit_configured_tail"
                if config.analysis_horizon_tail_days is not None
                else "maximum_configured_delay_sum"
            ),
        },
        "detection_event_interface": {
            "event_count": len(detection_events),
            "consumer": "runtime consumer hook; none attached for offline aggregation",
            "mutates_latent_or_routes": False,
            "runtime_delivery": online_schedule is not None,
            "offline_online_agreement": online_agreement,
            "fields": [
                "agent_uid",
                "detection_date",
                "detection_time_index",
                "detection_reason",
                "symptomatic",
                "observation_config_id",
                "provenance",
            ],
        },
        "observation_rng": {
            "stream_namespace": "observation",
            "stream_key_inputs": [
                "latent_replicate_seed",
                "observation_seed",
                "observation_config_id",
            ],
            "event_key_inputs": [
                "infected_uid",
                "infected_agent_id",
                "infection_date",
                "source_kind",
                "route_id",
                "infector_uid",
            ],
            "stream_fingerprint": offline_schedule.stream_fingerprint,
        },
        "parish_semantics": "Grouped by synthetic resident home parish, not infection location.",
        "latent_outputs_untouched": True,
        "parameter_provenance": config.model_dump(mode="json"),
        "benchmark": {
            "runtime_seconds": time.perf_counter() - started,
            "peak_memory_bytes": max(
                before_memory, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            ),
            "python_version": platform.python_version(),
        },
    }
    logical_content_hash = sha256_bytes(
        canonical_json_bytes(
            {
                "latent_run_logical_content_hash": latent_run.logical_content_hash,
                "config": config.model_dump(mode="json"),
                "daily_observed_cases": daily_observed_cases,
                "daily_observed_parish": daily_observed_parish,
                "daily_observed_age": daily_observed_age,
                "observation_events": observation_events,
                "detection_events": detection_payloads,
            }
        )
    )
    runtime_seconds = time.perf_counter() - started
    peak_memory_bytes = max(before_memory, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    diagnostics["benchmark"]["runtime_seconds"] = runtime_seconds
    diagnostics["benchmark"]["peak_memory_bytes"] = peak_memory_bytes
    return ObservationRunResult(
        latent_run=latent_run,
        config=config,
        daily_observed_cases=daily_observed_cases,
        daily_observed_parish=daily_observed_parish,
        daily_observed_age=daily_observed_age,
        observation_events=observation_events,
        detection_events=tuple(detection_events),
        diagnostics=diagnostics,
        logical_content_hash=logical_content_hash,
        runtime_seconds=runtime_seconds,
        peak_memory_bytes=peak_memory_bytes,
    )
