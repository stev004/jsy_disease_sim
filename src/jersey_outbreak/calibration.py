"""Small Optuna synthetic-recovery harness for Milestone 6."""

from __future__ import annotations

import platform
import resource
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .calibration_schemas import CalibrationConfig
from .hashing import canonical_json_bytes, sha256_bytes
from .network_generator import GeneratedNetworks, generate_networks
from .observation import ObservationRunResult, observe_latent_run
from .observation_schemas import ObservationConfig, ReportingDelayDistribution
from .outbreak_runner import OutbreakRunResult, run_outbreak
from .outbreak_schemas import OutbreakRunConfig, RespiratoryParameterSet


@dataclass(frozen=True)
class CalibrationResult:
    """Complete synthetic recovery experiment including all Optuna trials."""

    config: CalibrationConfig
    target_latent: OutbreakRunResult
    heldout_latent: OutbreakRunResult
    target_observation: ObservationRunResult
    heldout_observation: ObservationRunResult
    trial_rows: tuple[dict[str, Any], ...]
    best_parameters: dict[str, Any]
    diagnostics: dict[str, Any]
    logical_content_hash: str
    runtime_seconds: float
    peak_memory_bytes: int | None


def _delay_config(config: ObservationConfig, days: int) -> ObservationConfig:
    return config.model_copy(
        update={
            "reporting_delay": ReportingDelayDistribution(
                kind="fixed",
                days=(days,),
                status="scenario_assumption",
                source_ids=[],
                notes="Synthetic fixed delay candidate in the M6 recovery experiment.",
            )
        }
    )


def _reported_case_counts(observation: ObservationRunResult) -> dict[str, int]:
    return {row["date"]: int(row["reported_cases"]) for row in observation.daily_observed_cases}


def _objective_components(
    candidate: ObservationRunResult, target: ObservationRunResult
) -> dict[str, float]:
    candidate_counts = _reported_case_counts(candidate)
    target_counts = _reported_case_counts(target)
    dates = sorted(set(candidate_counts) | set(target_counts))
    differences = [candidate_counts.get(when, 0) - target_counts.get(when, 0) for when in dates]
    return {
        "reported_case_squared_error": float(sum(difference**2 for difference in differences)),
        "reported_case_absolute_error": float(sum(abs(difference) for difference in differences)),
        "reported_case_observations": float(sum(target_counts.values())),
    }


def _fully_detecting_observation(base: ObservationConfig) -> ObservationConfig:
    parameters = {
        key: parameter.model_copy(update={"value": 1.0})
        for key, parameter in base.parameters.items()
    }
    return base.model_copy(
        update={
            "observation_config_id": "m6-calibration-target-observation",
            "parameters": parameters,
            "day_of_week_effect": (1.0,) * 7,
        }
    )


def run_synthetic_recovery(
    root: Path,
    generated: GeneratedNetworks,
    parameters: RespiratoryParameterSet,
    base_run_config: OutbreakRunConfig,
    observation_config: ObservationConfig,
    *,
    calibration_config: CalibrationConfig | None = None,
) -> CalibrationResult:
    """Recover one fixed reporting-delay parameter on synthetic data only."""

    started = time.perf_counter()
    before_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    config = calibration_config or CalibrationConfig(study_id="m6-reporting-delay-recovery")
    target_observation_config = _fully_detecting_observation(
        _delay_config(observation_config, config.synthetic_truth_delay_days)
    )
    target_run_config = base_run_config.model_copy(
        update={"seed": generated.config.seed, "beta": 0.0, "initial_seed_count": 10}
    )
    target_latent = run_outbreak(generated, target_run_config, parameters)
    target_observation = observe_latent_run(target_latent, target_observation_config)

    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    search_space = {
        "reporting_delay_days": list(
            range(config.candidate_min_days, config.candidate_max_days + 1)
        )
    }
    sampler = optuna.samplers.GridSampler(search_space, seed=config.study_seed)
    study = optuna.create_study(
        study_name=config.study_id,
        direction="minimize",
        sampler=sampler,
    )

    def objective(trial: Any) -> float:
        candidate_days = int(
            trial.suggest_int(
                "reporting_delay_days",
                config.candidate_min_days,
                config.candidate_max_days,
            )
        )
        candidate = observe_latent_run(
            target_latent,
            _delay_config(target_observation_config, candidate_days),
        )
        components = _objective_components(candidate, target_observation)
        for key, value in components.items():
            trial.set_user_attr(key, value)
        return components["reported_case_squared_error"]

    study.optimize(objective, n_trials=config.trial_count, show_progress_bar=False)
    trial_rows = tuple(
        {
            "trial_number": trial.number,
            "state": trial.state.name,
            "value": float(trial.value) if trial.value is not None else None,
            "reporting_delay_days": trial.params.get("reporting_delay_days"),
            "objective_components": dict(trial.user_attrs),
        }
        for trial in sorted(study.trials, key=lambda item: item.number)
    )
    recovered = int(study.best_trial.params["reporting_delay_days"])

    heldout_network_config = generated.config.model_copy(update={"seed": config.heldout_seed})
    heldout_generated = generate_networks(
        heldout_network_config,
        generated.m2_input,
        generated.m3_input,
        root,
    )
    heldout_run_config = base_run_config.model_copy(
        update={"seed": config.heldout_seed, "beta": 0.0, "initial_seed_count": 10}
    )
    heldout_latent = run_outbreak(heldout_generated, heldout_run_config, parameters)
    heldout_truth = observe_latent_run(
        heldout_latent,
        _delay_config(target_observation_config, config.synthetic_truth_delay_days),
    )
    heldout_candidate = observe_latent_run(
        heldout_latent,
        _delay_config(target_observation_config, recovered),
    )
    heldout_components = _objective_components(heldout_candidate, heldout_truth)
    recovery_error = abs(recovered - config.synthetic_truth_delay_days)
    status = (
        "passed"
        if recovery_error <= config.recovery_tolerance_days
        and heldout_components["reported_case_squared_error"] == 0
        else "failed"
    )
    diagnostics: dict[str, Any] = {
        "status": status,
        "study_id": config.study_id,
        "sampler": "GridSampler",
        "sampler_seed": config.study_seed,
        "objective_components": [
            "reported_case_squared_error",
            "reported_case_absolute_error",
            "reported_case_observations",
        ],
        "objective_units": "daily reported-case count squared for the optimized component",
        "synthetic_truth": {
            "parameter": config.hidden_parameter,
            "value": config.synthetic_truth_delay_days,
            "observation_seed": target_observation_config.observation_seed,
            "latent_seed": target_run_config.seed,
        },
        "best_candidate": {"reporting_delay_days": recovered},
        "recovery_error_days": recovery_error,
        "recovery_tolerance_days": config.recovery_tolerance_days,
        "heldout": {
            "seed": config.heldout_seed,
            "objective_components": heldout_components,
            "recovery_error_days": recovery_error,
            "passed": heldout_components["reported_case_squared_error"] == 0,
        },
        "all_trials_retained": True,
        "real_jersey_data_used": False,
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
                "config": config.model_dump(mode="json"),
                "target_latent_hash": target_latent.logical_content_hash,
                "heldout_latent_hash": heldout_latent.logical_content_hash,
                "trial_rows": trial_rows,
                "best_parameters": {"reporting_delay_days": recovered},
                "heldout_components": heldout_components,
            }
        )
    )
    runtime_seconds = time.perf_counter() - started
    peak_memory_bytes = max(before_memory, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    diagnostics["benchmark"]["runtime_seconds"] = runtime_seconds
    diagnostics["benchmark"]["peak_memory_bytes"] = peak_memory_bytes
    return CalibrationResult(
        config=config,
        target_latent=target_latent,
        heldout_latent=heldout_latent,
        target_observation=target_observation,
        heldout_observation=heldout_candidate,
        trial_rows=trial_rows,
        best_parameters={"reporting_delay_days": recovered},
        diagnostics=diagnostics,
        logical_content_hash=logical_content_hash,
        runtime_seconds=runtime_seconds,
        peak_memory_bytes=peak_memory_bytes,
    )
