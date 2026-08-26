"""Standalone latent-to-observed transformation for Milestone 6."""

from __future__ import annotations

import hashlib
import platform
import resource
import subprocess
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import yaml  # type: ignore[import-untyped]

from .hashing import canonical_json_bytes, sha256_bytes
from .observation_schemas import ObservationConfig
from .outbreak_runner import OutbreakRunResult


def _stable_seed(seed: int, *parts: object) -> int:
    digest = hashlib.sha256("|".join(str(part) for part in (seed, *parts)).encode()).digest()
    return int.from_bytes(digest[:8], byteorder="little", signed=False)


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
    diagnostics: dict[str, Any]
    logical_content_hash: str
    runtime_seconds: float
    peak_memory_bytes: int | None


def _age_band(age: int) -> str:
    if age <= 4:
        return "0-4"
    if age <= 17:
        return "5-17"
    if age <= 64:
        return "18-64"
    return "65+"


def _date_range(start: date, end: date) -> list[date]:
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def _probability(config: ObservationConfig, name: str) -> float:
    value = config.numeric(name)
    if not 0 <= value <= 1:
        raise ValueError(f"observation probability {name!r} must be in [0, 1]")
    return value


def _delay_sampler(config: ObservationConfig, rng: np.random.Generator) -> int:
    delay = config.reporting_delay
    if delay.kind == "fixed":
        return int(delay.days[0])
    probabilities = np.asarray(delay.probabilities, dtype=float)
    return int(rng.choice(np.asarray(delay.days, dtype=np.int64), p=probabilities))


def _git_metadata(root: Path) -> tuple[str | None, bool]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        return commit.stdout.strip() or None, bool(status.stdout.strip())
    except OSError:
        return None, True


def observe_latent_run(
    latent_run: OutbreakRunResult,
    config: ObservationConfig,
) -> ObservationRunResult:
    """Apply observation-only randomness without touching the M5 result."""

    started = time.perf_counter()
    before_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    symptomatic_probability = _probability(config, "symptomatic_probability")
    symptomatic_detection_probability = _probability(config, "symptomatic_detection_probability")
    asymptomatic_detection_probability = _probability(config, "asymptomatic_detection_probability")
    rng = np.random.default_rng(_stable_seed(config.observation_seed, config.observation_config_id))
    m3_by_agent = {row["agent_id"]: row for row in latent_run.generated.m3_input.resident_structure}
    ordered_events = sorted(
        latent_run.transmission_events,
        key=lambda event: (event["date"], event["infected_agent_id"]),
    )
    observation_events: list[dict[str, Any]] = []
    for event in ordered_events:
        agent_id = event["infected_agent_id"]
        resident = m3_by_agent[agent_id]
        infection_date = date.fromisoformat(event["date"])
        delay = _delay_sampler(config, rng)
        report_date = infection_date + timedelta(days=delay)
        symptomatic = bool(rng.random() < symptomatic_probability)
        day_effect = config.day_of_week_effect[report_date.weekday()]
        detection_probability = (
            symptomatic_detection_probability if symptomatic else asymptomatic_detection_probability
        ) * day_effect
        tested = bool(rng.random() < detection_probability)
        observation_events.append(
            {
                "infected_agent_id": agent_id,
                "infection_date": infection_date.isoformat(),
                "detection_date": infection_date.isoformat() if tested else None,
                "report_date": report_date.isoformat() if tested else None,
                "reporting_delay_days": delay if tested else None,
                "symptomatic": symptomatic,
                "tested": tested,
                "detected": tested,
                "source_kind": event["source_kind"],
                "route_id": event["route_id"],
                "home_parish": resident["home_parish"],
                "age_band": _age_band(int(resident["age"])),
            }
        )

    latent_start = date.fromisoformat(latent_run.daily_epidemic[0]["date"])
    latest_report = max(
        [
            date.fromisoformat(event["report_date"])
            for event in observation_events
            if event["report_date"] is not None
        ]
        or [date.fromisoformat(latent_run.daily_epidemic[-1]["date"])],
    )
    dates = _date_range(latent_start, latest_report)
    latent_by_date = Counter(event["infection_date"] for event in observation_events)
    detected_by_infection_date = Counter(
        event["infection_date"] for event in observation_events if event["detected"]
    )
    reported_by_date = Counter(
        event["report_date"] for event in observation_events if event["report_date"] is not None
    )
    delays_by_report_date: dict[str, list[int]] = defaultdict(list)
    for event in observation_events:
        if event["report_date"] is not None:
            delays_by_report_date[event["report_date"]].append(event["reporting_delay_days"])
    daily_observed_cases: list[dict[str, Any]] = []
    for when in dates:
        date_key = when.isoformat()
        latent = latent_by_date[date_key]
        detected = detected_by_infection_date[date_key]
        delays = delays_by_report_date[date_key]
        daily_observed_cases.append(
            {
                "date": date_key,
                "latent_infections": latent,
                "detected_infections": detected,
                "reported_cases": reported_by_date[date_key],
                "ascertainment_fraction": detected / latent if latent else None,
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
            relevant = [event for event in observation_events if event["home_parish"] == parish]
            daily_observed_parish.append(
                {
                    "date": date_key,
                    "parish": parish,
                    "new_latent_infections": sum(
                        event["infection_date"] == date_key for event in relevant
                    ),
                    "new_detected_infections": sum(
                        event["infection_date"] == date_key and event["detected"]
                        for event in relevant
                    ),
                    "new_reported_cases": sum(
                        event["report_date"] == date_key for event in relevant
                    ),
                }
            )
        for age_band in age_bands:
            relevant = [event for event in observation_events if event["age_band"] == age_band]
            daily_observed_age.append(
                {
                    "date": date_key,
                    "age_band": age_band,
                    "new_latent_infections": sum(
                        event["infection_date"] == date_key for event in relevant
                    ),
                    "new_detected_infections": sum(
                        event["infection_date"] == date_key and event["detected"]
                        for event in relevant
                    ),
                    "new_reported_cases": sum(
                        event["report_date"] == date_key for event in relevant
                    ),
                }
            )

    detected_count = sum(event["detected"] for event in observation_events)
    delays = [
        int(event["reporting_delay_days"])
        for event in observation_events
        if event["reporting_delay_days"] is not None
    ]
    no_report_before_infection = all(
        event["report_date"] is None or event["report_date"] >= event["infection_date"]
        for event in observation_events
    )
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
        "infection_date_semantics": "Copied from immutable M5 latent event date.",
        "detection_date_semantics": (
            "For this bounded model, a detected infection is tested on its infection date; "
            "the configured delay is from that anchor to report date."
        ),
        "report_date_semantics": "Infection/detection date plus the non-negative reporting delay.",
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
        diagnostics=diagnostics,
        logical_content_hash=logical_content_hash,
        runtime_seconds=runtime_seconds,
        peak_memory_bytes=peak_memory_bytes,
    )
