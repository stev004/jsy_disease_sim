"""Milestone 5 generic respiratory run orchestration and tidy summaries."""

from __future__ import annotations

import platform
import resource
import subprocess
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from .hashing import canonical_json_bytes, sha256_bytes
from .network_generator import GeneratedNetworks
from .observation_scheduler import (
    DetectionConsumer,
    ObservationScheduler,
    ObservationScheduleSnapshot,
)
from .observation_schemas import ObservationConfig
from .outbreak_schemas import ROUTE_IDS, OutbreakRunConfig, RespiratoryParameterSet
from .population_schemas import PopulationMode
from .respiratory import RespiratorySEIRS
from .starsim_adapter import build_starsim_disease_sim

AGE_BANDS: tuple[tuple[str, int, int | None], ...] = (
    ("0-4", 0, 4),
    ("5-17", 5, 17),
    ("18-64", 18, 64),
    ("65+", 65, None),
)


@dataclass(frozen=True)
class OutbreakRunResult:
    """Plain-Python M5 outputs extracted from Starsim."""

    config: OutbreakRunConfig
    parameters: RespiratoryParameterSet
    generated: GeneratedNetworks
    daily_epidemic: list[dict[str, Any]]
    daily_parish: list[dict[str, Any]]
    daily_route: list[dict[str, Any]]
    daily_age: list[dict[str, Any]]
    transmission_events: list[dict[str, Any]]
    diagnostics: dict[str, Any]
    logical_content_hash: str
    runtime_seconds: float
    peak_memory_bytes: int | None
    observation_schedule: ObservationScheduleSnapshot | None = None


def load_parameter_set(root: Path, path: Path | None = None) -> RespiratoryParameterSet:
    """Load and strictly validate the versioned demo parameter YAML."""

    parameter_path = path or root / "configs" / "diseases" / "respiratory_seirs_demo.yaml"
    try:
        payload = yaml.safe_load(parameter_path.read_text(encoding="utf-8"))
        for entry in payload.get("parameters", {}).values():
            if isinstance(entry.get("valid_range"), list):
                entry["valid_range"] = tuple(entry["valid_range"])
        parameters = RespiratoryParameterSet.model_validate(payload)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise ValueError(f"invalid respiratory parameter set {parameter_path}: {exc}") from exc
    return parameters


def default_run_config(
    mode: PopulationMode,
    seed: int,
    parameters: RespiratoryParameterSet,
    *,
    start_date: date = date(2025, 1, 6),
    duration_days: int = 30,
) -> OutbreakRunConfig:
    """Create runtime controls from the demo parameter set without hiding assumptions."""

    return OutbreakRunConfig(
        mode=mode,
        seed=seed,
        start_date=start_date,
        duration_days=duration_days,
        parameter_set_id=parameters.parameter_set_id,
        initial_seed_count=round(parameters.numeric("initial_seed_count")),
        import_rate_per_day=parameters.numeric("import_rate_per_day"),
        beta=parameters.numeric("transmission_beta"),
        latent_period_days=parameters.numeric("latent_period_days"),
        infectious_period_days=parameters.numeric("infectious_period_days"),
        immunity_duration_days=parameters.numeric("immunity_duration_days"),
        waning_enabled=bool(round(parameters.numeric("immunity_waning_enabled"))),
        route_multipliers=dict(parameters.route_multipliers),
    )


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


def network_artifact_id(generated: GeneratedNetworks) -> str:
    """Return the same deterministic M4 artifact ID used by its writer."""

    config_hash = sha256_bytes(canonical_json_bytes(generated.config.model_dump(mode="json")))
    return (
        f"jos-networks-m4-{generated.config.mode}-seed-{generated.config.seed}-{config_hash[:12]}"
    )


def _state_count(disease: Any, key: str, index: int) -> int:
    return int(round(float(disease.results[key][index])))


def _age_band(age: int) -> str:
    for label, low, high in AGE_BANDS:
        if age >= low and (high is None or age <= high):
            return label
    raise ValueError(f"age {age} is outside configured age bands")


def _date_range(start: date, n_points: int) -> list[date]:
    return [start + timedelta(days=index) for index in range(n_points)]


def run_outbreak(
    generated: GeneratedNetworks,
    config: OutbreakRunConfig,
    parameters: RespiratoryParameterSet,
    *,
    observation_config: ObservationConfig | None = None,
    detection_consumer: DetectionConsumer | None = None,
) -> OutbreakRunResult:
    """Run the generic respiratory disease through the unchanged M4 route stack."""

    if generated.config.mode != config.mode or generated.config.seed != config.seed:
        raise ValueError("M5 run controls must match the M4 route artifact mode and seed")
    if config.parameter_set_id != parameters.parameter_set_id:
        raise ValueError("run parameter_set_id does not match the loaded parameter set")
    if config.dt_days != 1.0:
        raise ValueError("M5 currently supports only the verified daily Starsim timestep")
    route_betas = {
        route_id: config.beta * float(config.route_multipliers[route_id])
        for route_id in generated.route_specs
    }
    if any(beta > 1 for beta in route_betas.values()):
        raise ValueError("beta multiplied by a route multiplier must be at most 1")

    started = time.perf_counter()
    before_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    agent_ids = generated.agent_ids
    agent_id_by_uid = {uid: agent_id for uid, agent_id in enumerate(agent_ids)}
    m3_by_agent = {row["agent_id"]: row for row in generated.m3_input.resident_structure}
    scheduler = (
        ObservationScheduler(
            latent_seed=config.seed,
            start_date=config.start_date,
            config=observation_config,
            agent_id_by_uid=agent_id_by_uid,
            resident_by_agent_id=m3_by_agent,
            consumer=detection_consumer,
        )
        if observation_config is not None
        else None
    )
    disease = RespiratorySEIRS(
        route_betas=route_betas,
        initial_seed_count=config.initial_seed_count,
        initial_prevalence=config.initial_prevalence,
        import_schedule=config.import_schedule,
        import_rate_per_day=config.import_rate_per_day,
        latent_period_days=config.latent_period_days,
        infectious_period_days=config.infectious_period_days,
        immunity_duration_days=config.immunity_duration_days,
        waning_enabled=config.waning_enabled,
        observation_scheduler=scheduler,
    )
    network_hash_before = generated.logical_content_hash
    sim = build_starsim_disease_sim(
        generated,
        disease,
        start_date=config.start_date,
        duration_days=config.duration_days,
        seed=config.seed,
    )
    if scheduler is not None:

        def deliver_detection_notifications(_sim: Any) -> None:
            scheduler.deliver_due(int(disease.ti))

        sim.loop.insert(deliver_detection_notifications, label=f"{disease.name}.step")
    sim.run(verbose=0)
    if generated.logical_content_hash != network_hash_before:
        raise RuntimeError("M5 mutated the M4 route artifact")

    observation_schedule = scheduler.snapshot() if scheduler is not None else None
    events: list[dict[str, Any]] = []
    for event in disease._all_events:
        target_uid = int(event["infected_uid"])
        source_uid = event["infector_uid"]
        target_agent_id = agent_id_by_uid[target_uid]
        source_agent_id = None if source_uid is None else agent_id_by_uid[int(source_uid)]
        events.append(
            {
                **event,
                "infected_uid": target_uid,
                "infected_agent_id": target_agent_id,
                "infector_uid": None if source_uid is None else int(source_uid),
                "infector_agent_id": source_agent_id,
            }
        )

    n_points = len(disease.results.n_susceptible)
    dates = _date_range(config.start_date, n_points)
    daily_epidemic: list[dict[str, Any]] = []
    for index, when in enumerate(dates):
        daily_epidemic.append(
            {
                "date": when.isoformat(),
                "time_index": index,
                "susceptible": _state_count(disease, "n_susceptible", index),
                "exposed": _state_count(disease, "n_exposed", index),
                "infectious": _state_count(disease, "n_infected", index),
                "recovered": _state_count(disease, "n_recovered", index),
                "severe": 0,
                "dead": 0,
                "new_infections": _state_count(disease, "new_infections", index),
                "new_local_infections": _state_count(disease, "new_local", index),
                "new_imported_infections": _state_count(disease, "new_imported", index),
                "new_seeded_infections": _state_count(disease, "new_seeded", index),
                "cumulative_infections": _state_count(disease, "cum_infections", index),
                "cumulative_total_infections": _state_count(disease, "cum_total_infections", index),
                "prevalence": float(disease.results.prevalence[index]),
                "attack_rate": float(disease.results.attack_rate[index]),
            }
        )

    events_by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        events_by_date[event["date"]].append(event)
    parishes = sorted({row["home_parish"] for row in m3_by_agent.values()})
    daily_parish: list[dict[str, Any]] = []
    for when in dates:
        date_key = when.isoformat()
        for parish in parishes:
            parish_events = [
                event
                for event in events_by_date[date_key]
                if m3_by_agent[event["infected_agent_id"]]["home_parish"] == parish
            ]
            seeded = sum(event["seeded"] for event in parish_events)
            imported = sum(event["imported"] for event in parish_events)
            local = sum(event["source_kind"] == "local" for event in parish_events)
            daily_parish.append(
                {
                    "date": date_key,
                    "time_index": (when - config.start_date).days,
                    "parish": parish,
                    "new_seeded_infections": seeded,
                    "new_imported_infections": imported,
                    "new_local_infections": local,
                    "new_infections": seeded + imported + local,
                }
            )

    route_rows = [*ROUTE_IDS, "exogenous_import", "seeded"]
    daily_route: list[dict[str, Any]] = []
    cumulative_route_counts: Counter[str] = Counter()
    for when in dates:
        date_key = when.isoformat()
        day_events = events_by_date[date_key]
        for route_id in route_rows:
            route_events = [event for event in day_events if event["route_id"] == route_id]
            cumulative_route_counts[route_id] += len(route_events)
            daily_route.append(
                {
                    "date": date_key,
                    "time_index": (when - config.start_date).days,
                    "route_id": route_id,
                    "new_events": len(route_events),
                    "new_local_infections": sum(
                        event["source_kind"] == "local" for event in route_events
                    ),
                    "new_imported_infections": sum(
                        event["source_kind"] == "imported" for event in route_events
                    ),
                    "new_seeded_infections": sum(
                        event["source_kind"] == "seeded" for event in route_events
                    ),
                    "cumulative_infections": cumulative_route_counts[route_id],
                }
            )

    daily_age: list[dict[str, Any]] = []
    for when in dates:
        date_key = when.isoformat()
        day_events = events_by_date[date_key]
        for label, _, _ in AGE_BANDS:
            age_events = [
                event
                for event in day_events
                if _age_band(int(m3_by_agent[event["infected_agent_id"]]["age"])) == label
            ]
            seeded = sum(event["seeded"] for event in age_events)
            imported = sum(event["imported"] for event in age_events)
            local = sum(event["source_kind"] == "local" for event in age_events)
            daily_age.append(
                {
                    "date": date_key,
                    "time_index": (when - config.start_date).days,
                    "age_band": label,
                    "new_seeded_infections": seeded,
                    "new_imported_infections": imported,
                    "new_local_infections": local,
                    "new_infections": seeded + imported + local,
                }
            )

    state_residuals = [
        row["susceptible"] + row["exposed"] + row["infectious"] + row["recovered"] - len(agent_ids)
        for row in daily_epidemic
    ]
    route_counts = Counter(event["route_id"] for event in events if event["source_kind"] == "local")
    multi_route_events = [
        event
        for event in events
        if event["source_kind"] == "local"
        and int(event.get("successful_candidate_route_count", 1)) > 1
    ]
    attribution_totals = {
        "seeded": sum(event["seeded"] for event in events),
        "imported": sum(event["imported"] for event in events),
        "local": sum(event["source_kind"] == "local" for event in events),
        "total_events": len(events),
    }
    attribution_totals.update(
        {f"route:{route}": int(route_counts.get(route, 0)) for route in ROUTE_IDS}
    )
    diagnostics: dict[str, Any] = {
        "status": "passed",
        "module": "generic_respiratory_seirs",
        "module_version": RespiratorySEIRS.disease_module_version,
        "starsim_version": "3.5.2",
        "network_immutability": {
            "before_logical_content_hash": network_hash_before,
            "after_logical_content_hash": generated.logical_content_hash,
            "passed": generated.logical_content_hash == network_hash_before,
        },
        "states": {
            "state_names": ["susceptible", "exposed", "infected", "recovered"],
            "severity_implemented": False,
            "disease_deaths_implemented": False,
            "maximum_conservation_residual": max(abs(value) for value in state_residuals),
            "conserved": all(value == 0 for value in state_residuals),
        },
        "attribution": {
            "totals": attribution_totals,
            "seeded": attribution_totals["seeded"],
            "imported": attribution_totals["imported"],
            "local": attribution_totals["local"],
            "total_events": attribution_totals["total_events"],
            "all_local_events_have_route": all(
                event["route_id"] in ROUTE_IDS
                for event in events
                if event["source_kind"] == "local"
            ),
            "all_local_events_have_infector": all(
                event["infector_uid"] is not None
                for event in events
                if event["source_kind"] == "local"
            ),
            "conserved": (
                attribution_totals["total_events"]
                == attribution_totals["seeded"]
                + attribution_totals["imported"]
                + attribution_totals["local"]
            ),
            "multi_route_evidence": {
                "events_with_multiple_successful_routes": len(multi_route_events),
                "candidate_route_count_distribution": dict(
                    sorted(
                        Counter(
                            int(event["successful_candidate_route_count"])
                            for event in multi_route_events
                        ).items()
                    )
                ),
                "attribution_selection": (
                    "stable target/timestep draw proportional to successful edge hazard; "
                    "candidate occurrence is the unchanged union of Starsim edge successes"
                ),
            },
        },
        "seeding": {
            "requested_count": config.initial_seed_count,
            "initial_prevalence": config.initial_prevalence,
            "realized_seed_uids": list(disease._seed_uids),
        },
        "imports": {
            "schedule": dict(config.import_schedule),
            "rate_per_day": config.import_rate_per_day,
            "realized_imports": attribution_totals["imported"],
        },
        "parameter_provenance": parameters.model_dump(mode="json"),
        "online_observation_scheduler": (
            {
                "attached": True,
                "consumer_attached": detection_consumer is not None,
                "scheduled_detection_count": len(observation_schedule.detection_events),
                "delivered_detection_count": len(observation_schedule.delivered_detection_events),
                "pending_after_latent_horizon": observation_schedule.pending_detection_count,
                "lifecycle_order": [
                    "disease_state_progression",
                    "network_refresh",
                    "existing_intervention_step",
                    "disease_transmission_and_imports",
                    "detection_delivery",
                    "future_consumer_hook",
                ],
                "earliest_consumer_effect": "next_timestep",
                "no_retroactive_transmission_effect": True,
            }
            if observation_schedule is not None
            else {"attached": False}
        ),
        "benchmark": {
            "n_agents": len(agent_ids),
            "n_points": n_points,
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
                "config": config.model_dump(mode="json"),
                "parameters": parameters.model_dump(mode="json"),
                "daily_epidemic": daily_epidemic,
                "daily_parish": daily_parish,
                "daily_route": daily_route,
                "daily_age": daily_age,
                "transmission_events": events,
                "network_logical_content_hash": generated.logical_content_hash,
            }
        )
    )
    runtime_seconds = time.perf_counter() - started
    peak_memory_bytes = max(before_memory, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    diagnostics["benchmark"]["runtime_seconds"] = runtime_seconds
    diagnostics["benchmark"]["peak_memory_bytes"] = peak_memory_bytes
    return OutbreakRunResult(
        config=config,
        parameters=parameters,
        generated=generated,
        daily_epidemic=daily_epidemic,
        daily_parish=daily_parish,
        daily_route=daily_route,
        daily_age=daily_age,
        transmission_events=events,
        diagnostics=diagnostics,
        logical_content_hash=logical_content_hash,
        runtime_seconds=runtime_seconds,
        peak_memory_bytes=peak_memory_bytes,
        observation_schedule=observation_schedule,
    )
