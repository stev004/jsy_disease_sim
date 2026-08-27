"""Small synthetic-recovery harness for the bounded C3 calibration experiments."""

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


def _beta_objective_components(
    candidate: ObservationRunResult, target: ObservationRunResult
) -> dict[str, float]:
    """Score beta candidates against synthetic truth on the complete date grid."""

    candidate_counts = _reported_case_counts(candidate)
    target_counts = _reported_case_counts(target)
    dates = sorted(set(candidate_counts) | set(target_counts))
    differences = [candidate_counts.get(when, 0) - target_counts.get(when, 0) for when in dates]
    candidate_cumulative = 0
    target_cumulative = 0
    cumulative_error = 0.0
    for when in dates:
        candidate_cumulative += candidate_counts.get(when, 0)
        target_cumulative += target_counts.get(when, 0)
        cumulative_error += float((candidate_cumulative - target_cumulative) ** 2)
    daily_squared = float(sum(difference**2 for difference in differences))
    return {
        "daily_shape_squared_error": daily_squared,
        "daily_shape_absolute_error": float(sum(abs(difference) for difference in differences)),
        "cumulative_size_squared_error": cumulative_error,
        "reported_case_observations": float(sum(target_counts.values())),
        "objective": daily_squared + cumulative_error,
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

    if (
        calibration_config is not None
        and calibration_config.hidden_parameter == "transmission_beta"
    ):
        return run_beta_recovery(
            root,
            generated,
            parameters,
            base_run_config,
            observation_config,
            calibration_config=calibration_config,
        )

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


def _network_for_seed(root: Path, generated: GeneratedNetworks, seed: int) -> GeneratedNetworks:
    if generated.config.seed == seed:
        return generated
    return generate_networks(
        generated.config.model_copy(update={"seed": seed}),
        generated.m2_input,
        generated.m3_input,
        root,
    )


def _beta_observation_config(base: ObservationConfig) -> ObservationConfig:
    """Use an explicit fully observed synthetic target for beta recovery."""

    return _fully_detecting_observation(base).model_copy(
        update={"observation_config_id": "c3-beta-calibration-observation"}
    )


def _scale_detection_probability(config: ObservationConfig, factor: float) -> ObservationConfig:
    parameters = {
        key: parameter.model_copy(
            update={"value": min(1.0, float(parameter.value or 0.0) * factor)}
        )
        if key in {"symptomatic_detection_probability", "asymptomatic_detection_probability"}
        else parameter
        for key, parameter in config.parameters.items()
    }
    return config.model_copy(
        update={
            "observation_config_id": f"{config.observation_config_id}-ascertainment-sensitivity",
            "parameters": parameters,
        }
    )


def _scale_route_multipliers(config: OutbreakRunConfig, factor: float) -> dict[str, float]:
    return {route_id: float(value) * factor for route_id, value in config.route_multipliers.items()}


def run_beta_recovery(
    root: Path,
    generated: GeneratedNetworks,
    parameters: RespiratoryParameterSet,
    base_run_config: OutbreakRunConfig,
    observation_config: ObservationConfig,
    *,
    calibration_config: CalibrationConfig,
) -> CalibrationResult:
    """Recover beta on synthetic truth with train/held-out and confounding profiles.

    The experiment is deliberately a profile over the declared beta grid. It is
    not calibration to Jersey surveillance data: truth is generated by this
    same generic disease module, observed under an explicit fully-observed
    synthetic ascertainment configuration, and scored on complete date grids.
    """

    if calibration_config.hidden_parameter != "transmission_beta":
        raise ValueError("run_beta_recovery requires hidden_parameter='transmission_beta'")
    started = time.perf_counter()
    before_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    config = calibration_config
    truth_beta = float(config.synthetic_truth_beta)
    target_observation_config = _beta_observation_config(observation_config)
    trial_components: dict[float, list[dict[str, float]]] = {
        float(beta): [] for beta in config.candidate_beta_values
    }
    target_latent: OutbreakRunResult | None = None
    target_observation: ObservationRunResult | None = None
    for seed in config.training_replicate_seeds:
        network = _network_for_seed(root, generated, int(seed))
        run_controls = base_run_config.model_copy(
            update={
                "seed": int(seed),
                "beta": truth_beta,
                "initial_seed_count": max(10, base_run_config.initial_seed_count),
            }
        )
        truth_latent = run_outbreak(network, run_controls, parameters)
        truth_observation = observe_latent_run(truth_latent, target_observation_config)
        if target_latent is None:
            target_latent = truth_latent
            target_observation = truth_observation
        for beta in config.candidate_beta_values:
            candidate_controls = run_controls.model_copy(update={"beta": float(beta)})
            candidate_latent = run_outbreak(network, candidate_controls, parameters)
            candidate_observation = observe_latent_run(candidate_latent, target_observation_config)
            trial_components[float(beta)].append(
                _beta_objective_components(candidate_observation, truth_observation)
            )

    profile_rows: list[dict[str, Any]] = []
    for trial_number, beta in enumerate(config.candidate_beta_values):
        components = trial_components[float(beta)]
        aggregate = {key: float(sum(row[key] for row in components)) for key in components[0]}
        profile_rows.append(
            {
                "trial_number": trial_number,
                "state": "COMPLETE",
                "value": aggregate["objective"],
                "parameter_name": "transmission_beta",
                "parameter_value": float(beta),
                "reporting_delay_days": None,
                "transmission_beta": float(beta),
                "objective_components": aggregate,
                "training_replicates": len(components),
            }
        )
    best = min(profile_rows, key=lambda row: (row["value"], row["parameter_value"]))
    recovered = float(best["parameter_value"])

    heldout_latent: OutbreakRunResult | None = None
    heldout_truth: ObservationRunResult | None = None
    heldout_candidate: ObservationRunResult | None = None
    heldout_components: list[dict[str, float]] = []
    ascertainment_components: list[dict[str, float]] = []
    route_components: list[dict[str, float]] = []
    altered_observation_config = _scale_detection_probability(target_observation_config, 0.5)
    for seed in config.heldout_replicate_seeds:
        network = _network_for_seed(root, generated, int(seed))
        truth_controls = base_run_config.model_copy(
            update={
                "seed": int(seed),
                "beta": truth_beta,
                "initial_seed_count": max(10, base_run_config.initial_seed_count),
            }
        )
        truth_latent = run_outbreak(network, truth_controls, parameters)
        candidate_latent = run_outbreak(
            network, truth_controls.model_copy(update={"beta": recovered}), parameters
        )
        truth_observation = observe_latent_run(truth_latent, target_observation_config)
        candidate_observation = observe_latent_run(candidate_latent, target_observation_config)
        heldout_components.append(
            _beta_objective_components(candidate_observation, truth_observation)
        )
        ascertainment_components.append(
            _beta_objective_components(
                observe_latent_run(candidate_latent, altered_observation_config), truth_observation
            )
        )
        scaled_controls = truth_controls.model_copy(
            update={
                "beta": recovered,
                "route_multipliers": _scale_route_multipliers(truth_controls, 0.5),
            }
        )
        scaled_latent = run_outbreak(network, scaled_controls, parameters)
        route_components.append(
            _beta_objective_components(
                observe_latent_run(scaled_latent, target_observation_config), truth_observation
            )
        )
        if heldout_latent is None:
            heldout_latent = candidate_latent
            heldout_truth = truth_observation
            heldout_candidate = candidate_observation

    if target_latent is None or target_observation is None:
        raise RuntimeError("beta calibration produced no training replicates")
    if heldout_latent is None or heldout_truth is None or heldout_candidate is None:
        raise RuntimeError("beta calibration produced no held-out replicates")
    aggregate_heldout = {
        key: float(sum(row[key] for row in heldout_components)) for key in heldout_components[0]
    }
    recovery_error = abs(recovered - truth_beta)
    status = (
        "passed"
        if recovery_error <= float(config.recovery_tolerance_beta)
        and aggregate_heldout["objective"] == 0
        else "failed"
    )
    diagnostics: dict[str, Any] = {
        "status": status,
        "study_id": config.study_id,
        "calibration_parameter": "transmission_beta",
        "objective_components": list(heldout_components[0]),
        "objective_units": "synthetic daily reported-case shape plus cumulative-size squared error",
        "synthetic_truth": {
            "parameter": "transmission_beta",
            "value": truth_beta,
            "training_replicate_seeds": list(config.training_replicate_seeds),
            "observation_config_id": target_observation_config.observation_config_id,
            "real_jersey_data_used": False,
        },
        "best_candidate": {"transmission_beta": recovered},
        "recovery_error": recovery_error,
        "recovery_tolerance": float(config.recovery_tolerance_beta),
        "heldout": {
            "seeds": list(config.heldout_replicate_seeds),
            "objective_components": aggregate_heldout,
            "recovery_error": recovery_error,
            "passed": aggregate_heldout["objective"] == 0,
        },
        "identifiability_profile": {
            "ascertainment_factor": 0.5,
            "altered_ascertainment_objective": float(
                sum(row["objective"] for row in ascertainment_components)
            ),
            "route_multiplier_factor": 0.5,
            "altered_route_weight_objective": float(
                sum(row["objective"] for row in route_components)
            ),
            "interpretation": (
                "Sensitivity profiles expose confounding between beta, ascertainment "
                "and route weights; "
                "they are not additional Jersey evidence or a claim of separate identification."
            ),
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
                "trial_rows": profile_rows,
                "best_parameters": {"transmission_beta": recovered},
                "heldout_components": aggregate_heldout,
                "identifiability_profile": diagnostics["identifiability_profile"],
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
        trial_rows=tuple(profile_rows),
        best_parameters={"transmission_beta": recovered},
        diagnostics=diagnostics,
        logical_content_hash=logical_content_hash,
        runtime_seconds=runtime_seconds,
        peak_memory_bytes=peak_memory_bytes,
    )
