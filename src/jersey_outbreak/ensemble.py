"""Deterministic Milestone 6 ensemble and matched-seed comparison runners."""

from __future__ import annotations

import multiprocessing as mp
import os
import platform
import resource
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np

from .ensemble_schemas import EnsembleConfig, EnsembleReplicateRecord
from .hashing import canonical_json_bytes, sha256_bytes
from .network_generator import GeneratedNetworks, generate_networks
from .observation import ObservationRunResult, observe_latent_run
from .observation_schemas import ObservationConfig
from .outbreak_runner import OutbreakRunResult, run_outbreak
from .outbreak_schemas import RespiratoryParameterSet


@dataclass(frozen=True)
class ReplicateOutput:
    """Small serializable output returned by one independent replicate."""

    seed: int
    status: Literal["passed", "failed"]
    latent_logical_content_hash: str | None
    observation_logical_content_hash: str | None
    m4_logical_content_hash: str | None
    runtime_seconds: float
    trajectories: tuple[dict[str, Any], ...]
    error: str | None


@dataclass(frozen=True)
class EnsembleResult:
    """An ensemble with explicit replicate records and tidy summaries."""

    config: EnsembleConfig
    replicate_records: tuple[EnsembleReplicateRecord, ...]
    replicate_trajectories: dict[int, tuple[dict[str, Any], ...]]
    summary: tuple[dict[str, Any], ...]
    diagnostics: dict[str, Any]
    logical_content_hash: str
    runtime_seconds: float
    peak_memory_bytes: int | None
    m2_logical_content_hash: str
    m3_logical_content_hash: str
    disease_parameter_hash: str


@dataclass(frozen=True)
class ComparisonResult:
    """Paired output for two ensembles evaluated on their seed identities."""

    comparison_id: str
    ensemble_a: EnsembleResult
    ensemble_b: EnsembleResult
    paired_rows: tuple[dict[str, Any], ...]
    diagnostics: dict[str, Any]
    logical_content_hash: str
    runtime_seconds: float


def _trajectory_rows(
    latent: OutbreakRunResult, observed: ObservationRunResult, seed: int
) -> tuple[dict[str, Any], ...]:
    """Convert one latent/observed pair into a UI-ready long trajectory table."""

    rows: list[dict[str, Any]] = []
    for row in latent.daily_epidemic:
        latent_total = (
            row["new_local_infections"]
            + row["new_imported_infections"]
            + row["new_seeded_infections"]
        )
        rows.extend(
            [
                {
                    "seed": seed,
                    "scope": "epidemic",
                    "key": "all",
                    "metric": "latent_new_infections",
                    "date": row["date"],
                    "value": latent_total,
                },
                {
                    "seed": seed,
                    "scope": "epidemic",
                    "key": "all",
                    "metric": "latent_prevalence",
                    "date": row["date"],
                    "value": row["prevalence"],
                },
                {
                    "seed": seed,
                    "scope": "epidemic",
                    "key": "all",
                    "metric": "latent_cumulative_infections",
                    "date": row["date"],
                    "value": row["cumulative_total_infections"],
                },
                {
                    "seed": seed,
                    "scope": "epidemic",
                    "key": "all",
                    "metric": "latent_attack_rate",
                    "date": row["date"],
                    "value": row["attack_rate"],
                },
            ]
        )
    for row in latent.daily_route:
        rows.append(
            {
                "seed": seed,
                "scope": "route",
                "key": row["route_id"],
                "metric": "latent_local_infections",
                "date": row["date"],
                "value": row["new_local_infections"],
            }
        )
    for row in latent.daily_parish:
        rows.append(
            {
                "seed": seed,
                "scope": "parish",
                "key": row["parish"],
                "metric": "latent_new_infections",
                "date": row["date"],
                "value": row["new_infections"],
            }
        )
    for row in latent.daily_age:
        rows.append(
            {
                "seed": seed,
                "scope": "age",
                "key": row["age_band"],
                "metric": "latent_new_infections",
                "date": row["date"],
                "value": row["new_infections"],
            }
        )
    for row in observed.daily_observed_cases:
        rows.extend(
            [
                {
                    "seed": seed,
                    "scope": "epidemic",
                    "key": "all",
                    "metric": "observed_detected_infections",
                    "date": row["date"],
                    "value": row["detected_infections"],
                },
                {
                    "seed": seed,
                    "scope": "epidemic",
                    "key": "all",
                    "metric": "observed_reported_cases",
                    "date": row["date"],
                    "value": row["reported_cases"],
                },
            ]
        )
    for row in observed.daily_observed_parish:
        rows.append(
            {
                "seed": seed,
                "scope": "parish",
                "key": row["parish"],
                "metric": "observed_reported_cases",
                "date": row["date"],
                "value": row["new_reported_cases"],
            }
        )
    for row in observed.daily_observed_age:
        rows.append(
            {
                "seed": seed,
                "scope": "age",
                "key": row["age_band"],
                "metric": "observed_reported_cases",
                "date": row["date"],
                "value": row["new_reported_cases"],
            }
        )
    return tuple(rows)


def _run_replicate_job(job: dict[str, Any]) -> ReplicateOutput:
    """Run one replicate; errors become explicit failed records."""

    started = time.perf_counter()
    seed = int(job["seed"])
    try:
        from .network_schemas import NetworkGenerationConfig
        from .outbreak_schemas import OutbreakRunConfig

        network_config = NetworkGenerationConfig.model_validate(job["network_config"]).model_copy(
            update={"seed": seed}
        )
        generated = generate_networks(
            network_config,
            job["m2_input"],
            job["m3_input"],
            Path(job["root"]),
        )
        run_config = OutbreakRunConfig.model_validate(job["base_run_config"]).model_copy(
            update={"seed": seed}
        )
        parameters = RespiratoryParameterSet.model_validate(job["parameters"])
        observation_config = ObservationConfig.model_validate(job["observation_config"])
        latent = run_outbreak(generated, run_config, parameters)
        observed = observe_latent_run(latent, observation_config)
        return ReplicateOutput(
            seed=seed,
            status="passed",
            latent_logical_content_hash=latent.logical_content_hash,
            observation_logical_content_hash=observed.logical_content_hash,
            m4_logical_content_hash=generated.logical_content_hash,
            runtime_seconds=time.perf_counter() - started,
            trajectories=_trajectory_rows(latent, observed, seed),
            error=None,
        )
    except Exception as exc:  # pragma: no cover - exercised through failure test injection
        return ReplicateOutput(
            seed=seed,
            status="failed",
            latent_logical_content_hash=None,
            observation_logical_content_hash=None,
            m4_logical_content_hash=None,
            runtime_seconds=time.perf_counter() - started,
            trajectories=(),
            error=f"{type(exc).__name__}: {exc}",
        )


def _summary_rows(
    trajectories: dict[int, tuple[dict[str, Any], ...]],
    lower_quantile: float,
    upper_quantile: float,
    *,
    requested_replicates: int | None = None,
    horizon: tuple[str, ...] | None = None,
) -> tuple[dict[str, Any], ...]:
    successful_replicates = len(trajectories)
    requested = requested_replicates if requested_replicates is not None else successful_replicates
    indexed = {
        seed: {
            (row["scope"], row["key"], row["metric"], row["date"]): float(row["value"])
            for row in rows
        }
        for seed, rows in trajectories.items()
    }
    metric_keys = sorted(
        {
            (row["scope"], row["key"], row["metric"])
            for rows in trajectories.values()
            for row in rows
        }
    )
    dates = tuple(
        horizon or sorted({row["date"] for rows in trajectories.values() for row in rows})
    )
    summary: list[dict[str, Any]] = []
    for scope, key, metric in metric_keys:
        for when in dates:
            values = [
                indexed[seed].get((scope, key, metric, when), 0.0) for seed in sorted(indexed)
            ]
            if not values:
                continue
            quantiles = np.quantile(
                np.asarray(values, dtype=float),
                [lower_quantile, 0.5, upper_quantile],
                method="linear",
            )
            summary.append(
                {
                    "scope": scope,
                    "key": key,
                    "metric": metric,
                    "date": when,
                    "lower_quantile": lower_quantile,
                    "median": float(quantiles[1]),
                    "upper_quantile": upper_quantile,
                    "lower_value": float(quantiles[0]),
                    "upper_value": float(quantiles[2]),
                    "replicate_count": len(values),
                    "requested_replicates": requested,
                    "successful_replicates": successful_replicates,
                    "contributing_replicates": len(values),
                }
            )
    return tuple(summary)


def available_physical_memory_bytes() -> int | None:
    """Return discoverable physical memory without adding a psutil dependency."""

    try:
        page_size = int(os.sysconf("SC_PAGE_SIZE"))
        page_count = int(os.sysconf("SC_PHYS_PAGES"))
    except (AttributeError, OSError, TypeError, ValueError):
        return None
    return page_size * page_count if page_size > 0 and page_count > 0 else None


def safe_worker_bound(
    requested_workers: int,
    *,
    estimated_worker_memory_bytes: int = 1_100_000_000,
    memory_safety_fraction: float = 0.6,
    available_memory_bytes: int | None = None,
    cpu_count: int | None = None,
) -> int:
    """Bound workers by memory and CPU, retaining at least one worker."""

    if requested_workers < 1 or estimated_worker_memory_bytes < 1:
        raise ValueError("worker and memory estimates must be positive")
    if not 0 < memory_safety_fraction <= 1:
        raise ValueError("memory_safety_fraction must be in (0, 1]")
    cpu_bound = max(1, cpu_count or (os.cpu_count() or 1))
    memory = (
        available_memory_bytes
        if available_memory_bytes is not None
        else available_physical_memory_bytes()
    )
    if memory is None:
        memory_bound = requested_workers
    else:
        memory_bound = max(
            1,
            int(memory * memory_safety_fraction // estimated_worker_memory_bytes),
        )
    return max(1, min(requested_workers, cpu_bound, memory_bound))


def run_ensemble(
    root: Path,
    generated: GeneratedNetworks,
    parameters: RespiratoryParameterSet,
    base_run_config: Any,
    observation_config: ObservationConfig,
    replicate_seeds: tuple[int, ...],
    *,
    ensemble_id: str,
    workers: int = 1,
    lower_quantile: float = 0.025,
    upper_quantile: float = 0.975,
    estimated_worker_memory_bytes: int = 1_100_000_000,
    memory_safety_fraction: float = 0.6,
    allow_unsafe_workers: bool = False,
) -> EnsembleResult:
    """Run explicit seeds sequentially or in a bounded process pool."""

    from .outbreak_schemas import OutbreakRunConfig

    base_run_config = OutbreakRunConfig.model_validate(base_run_config)
    config = EnsembleConfig(
        ensemble_id=ensemble_id,
        base_run_config=base_run_config,
        observation_config=observation_config,
        replicate_seeds=replicate_seeds,
        workers=workers,
        estimated_worker_memory_bytes=estimated_worker_memory_bytes,
        memory_safety_fraction=memory_safety_fraction,
        allow_unsafe_workers=allow_unsafe_workers,
        lower_quantile=lower_quantile,
        upper_quantile=upper_quantile,
    )
    started = time.perf_counter()
    before_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    source_root = (
        root if (root / "data" / "sources.yaml").exists() else Path(__file__).resolve().parents[2]
    )
    job_base = {
        # ``root`` is normally the project root.  Tests and library callers
        # may use a temporary output directory, so fall back to the package's
        # project root for the M4 source registry required during seeded
        # network regeneration.
        "root": str(source_root.resolve()),
        "m2_input": generated.m2_input,
        "m3_input": generated.m3_input,
        # Keep the validated model objects across the worker boundary.  Their
        # date/tuple fields are intentionally strict, and a JSON round-trip
        # would turn those types into strings/lists before validation.
        "network_config": generated.config,
        "base_run_config": base_run_config,
        "parameters": parameters,
        "observation_config": observation_config,
    }
    jobs = [{**job_base, "seed": seed} for seed in config.replicate_seeds]
    requested_workers = config.workers
    safe_bound = (
        requested_workers
        if config.allow_unsafe_workers
        else safe_worker_bound(
            requested_workers,
            estimated_worker_memory_bytes=config.estimated_worker_memory_bytes,
            memory_safety_fraction=config.memory_safety_fraction,
        )
    )
    actual_workers = min(requested_workers, safe_bound)
    parallelism = "sequential"
    parallelism_fallback_reason: str | None = None
    if actual_workers == 1:
        outputs = [_run_replicate_job(job) for job in jobs]
        if requested_workers > 1:
            parallelism = "sequential_memory_bound"
    else:
        try:
            context = mp.get_context("spawn")
            with ProcessPoolExecutor(max_workers=actual_workers, mp_context=context) as pool:
                futures = [pool.submit(_run_replicate_job, job) for job in jobs]
                outputs = [future.result() for future in futures]
            parallelism = "process_pool_spawn"
        except (NotImplementedError, OSError, PermissionError, RuntimeError) as exc:
            # Some constrained macOS runners deny the semaphore limit probe
            # used by ProcessPoolExecutor.  This is an execution-environment
            # limitation, not a replicate result; preserve deterministic
            # semantics with an explicit, diagnostic sequential fallback.
            outputs = [_run_replicate_job(job) for job in jobs]
            parallelism = "sequential_fallback"
            parallelism_fallback_reason = f"{type(exc).__name__}: {exc}"

    records = tuple(
        EnsembleReplicateRecord(
            seed=output.seed,
            status=output.status,
            latent_run_logical_content_hash=output.latent_logical_content_hash,
            observation_logical_content_hash=output.observation_logical_content_hash,
            m4_logical_content_hash=output.m4_logical_content_hash,
            runtime_seconds=output.runtime_seconds,
            error=output.error,
        )
        for output in outputs
    )
    successful_trajectories = {
        output.seed: output.trajectories for output in outputs if output.status == "passed"
    }
    summary = _summary_rows(
        successful_trajectories,
        config.lower_quantile,
        config.upper_quantile,
        requested_replicates=len(config.replicate_seeds),
    )
    successful = sum(output.status == "passed" for output in outputs)
    failed = len(outputs) - successful
    status = "passed" if failed == 0 else ("partial" if successful else "failed")
    diagnostics: dict[str, Any] = {
        "status": status,
        "ensemble_id": config.ensemble_id,
        "replicate_seeds": list(config.replicate_seeds),
        "replicate_count": len(outputs),
        "successful_replicates": successful,
        "failed_replicates": failed,
        "requested_workers": requested_workers,
        "actual_workers": actual_workers,
        "parallelism": parallelism,
        "worker_bound": {
            "safe_upper_bound": safe_bound,
            "estimated_worker_memory_bytes": config.estimated_worker_memory_bytes,
            "memory_safety_fraction": config.memory_safety_fraction,
            "available_physical_memory_bytes": available_physical_memory_bytes(),
            "cpu_count": os.cpu_count(),
            "override_used": config.allow_unsafe_workers,
        },
        "quantile_method": "numpy.quantile(method='linear')",
        "quantile_configuration": {
            "lower": config.lower_quantile,
            "median": 0.5,
            "upper": config.upper_quantile,
        },
        "platform": platform.platform(),
        "failed_replica_errors": {
            str(output.seed): output.error for output in outputs if output.error
        },
        "date_grid": {
            "complete": failed == 0,
            "zero_fill_semantics": (
                "absent metric/date rows in successful replicates are explicit zeroes"
            ),
        },
        "stream_ownership": {
            "population": "fixed parent M2 artifact; coupled across matched scenarios",
            "m2_m3_structure": "fixed parent M3 artifact; coupled across matched scenarios",
            "network": "derived from replicate seed and network configuration",
            "disease": "derived from replicate seed and disease/network path",
            "observation": "derived from replicate seed, observation seed and config identity",
            "attribution": "stable seed/timestep/target key inside the disease module",
        },
        "matched_seed_semantics": {
            "matched_seed_means": "both scenarios start with the same declared integer seed",
            "true_common_random_numbers": (
                "only claimed for streams whose keys and event paths remain coupled"
            ),
        },
    }
    if parallelism_fallback_reason is not None:
        diagnostics["parallelism_fallback_reason"] = parallelism_fallback_reason
    logical_content_hash = sha256_bytes(
        canonical_json_bytes(
            {
                "config": config.model_dump(mode="json"),
                # Runtime and memory are benchmark metadata, not logical
                # ensemble content; excluding them keeps same-seed reruns
                # content-addressable despite normal timing jitter.
                "replicates": [
                    record.model_dump(mode="json", exclude={"runtime_seconds"})
                    for record in records
                ],
                "summary": summary,
                "trajectories": successful_trajectories,
            }
        )
    )
    runtime_seconds = time.perf_counter() - started
    peak_memory_bytes = max(before_memory, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    diagnostics["benchmark"] = {
        "runtime_seconds": runtime_seconds,
        "peak_memory_bytes": peak_memory_bytes,
        "python_version": platform.python_version(),
    }
    return EnsembleResult(
        config=config,
        replicate_records=records,
        replicate_trajectories=successful_trajectories,
        summary=summary,
        diagnostics=diagnostics,
        logical_content_hash=logical_content_hash,
        runtime_seconds=runtime_seconds,
        peak_memory_bytes=peak_memory_bytes,
        m2_logical_content_hash=generated.m2_input.manifest.logical_content_hash,
        m3_logical_content_hash=generated.m3_input.manifest.logical_content_hash,
        disease_parameter_hash=sha256_bytes(
            canonical_json_bytes(parameters.model_dump(mode="json"))
        ),
    )


def _ensemble_config_hash(result: EnsembleResult) -> str:
    return sha256_bytes(canonical_json_bytes(result.config.model_dump(mode="json")))


def compare_ensembles(
    ensemble_a: EnsembleResult,
    ensemble_b: EnsembleResult,
    *,
    comparison_id: str,
) -> ComparisonResult:
    """Compare two immutable configurations while preserving seed pairing."""

    started = time.perf_counter()
    a_by_seed = {record.seed: record for record in ensemble_a.replicate_records}
    b_by_seed = {record.seed: record for record in ensemble_b.replicate_records}
    seeds = tuple(
        dict.fromkeys((*ensemble_a.config.replicate_seeds, *ensemble_b.config.replicate_seeds))
    )
    rows: list[dict[str, Any]] = []
    paired = 0
    missing = 0
    for seed in seeds:
        record_a = a_by_seed.get(seed)
        record_b = b_by_seed.get(seed)
        if (
            record_a is None
            or record_b is None
            or record_a.status != "passed"
            or record_b.status != "passed"
        ):
            missing += 1
            rows.append(
                {
                    "seed": seed,
                    "scope": "pair",
                    "key": "seed",
                    "metric": "pair_status",
                    "date": None,
                    "status": "missing_or_failed",
                    "value_a": None,
                    "value_b": None,
                    "difference": None,
                }
            )
            continue
        paired += 1
        a_rows = {
            (row["scope"], row["key"], row["metric"], row["date"]): row["value"]
            for row in ensemble_a.replicate_trajectories[seed]
        }
        b_rows = {
            (row["scope"], row["key"], row["metric"], row["date"]): row["value"]
            for row in ensemble_b.replicate_trajectories[seed]
        }
        for key in sorted(set(a_rows) | set(b_rows)):
            value_a = a_rows.get(key)
            value_b = b_rows.get(key)
            rows.append(
                {
                    "seed": seed,
                    "scope": key[0],
                    "key": key[1],
                    "metric": key[2],
                    "date": key[3],
                    "status": (
                        "paired"
                        if value_a is not None and value_b is not None
                        else "missing_metric"
                    ),
                    "value_a": value_a,
                    "value_b": value_b,
                    "difference": value_b - value_a
                    if value_a is not None and value_b is not None
                    else None,
                }
            )
    status = "passed" if missing == 0 else ("partial" if paired else "failed")
    paired_records = [
        (a_by_seed[seed], b_by_seed[seed])
        for seed in seeds
        if seed in a_by_seed
        and seed in b_by_seed
        and a_by_seed[seed].status == "passed"
        and b_by_seed[seed].status == "passed"
    ]
    m2_coupled = ensemble_a.m2_logical_content_hash == ensemble_b.m2_logical_content_hash
    m3_coupled = ensemble_a.m3_logical_content_hash == ensemble_b.m3_logical_content_hash
    network_coupled = bool(paired_records) and all(
        record_a.m4_logical_content_hash == record_b.m4_logical_content_hash
        for record_a, record_b in paired_records
    )
    disease_coupled = bool(paired_records) and all(
        record_a.latent_run_logical_content_hash == record_b.latent_run_logical_content_hash
        for record_a, record_b in paired_records
    )
    observation_config_hash_a = sha256_bytes(
        canonical_json_bytes(ensemble_a.config.observation_config.model_dump(mode="json"))
    )
    observation_config_hash_b = sha256_bytes(
        canonical_json_bytes(ensemble_b.config.observation_config.model_dump(mode="json"))
    )
    observation_stream_key_coupled = observation_config_hash_a == observation_config_hash_b
    observation_output_coupled = bool(paired_records) and all(
        record_a.observation_logical_content_hash == record_b.observation_logical_content_hash
        for record_a, record_b in paired_records
    )
    diagnostics = {
        "status": status,
        "seed_order": list(seeds),
        "paired_seed_count": paired,
        "missing_or_failed_pair_count": missing,
        "pairing_preserved": True,
        "stream_coupling": {
            "population": m2_coupled,
            "m2_m3_structure": m3_coupled,
            "network": network_coupled,
            "disease": disease_coupled,
            "observation_stream_key": observation_stream_key_coupled,
            "observation_outputs": observation_output_coupled,
            "event_path_divergence_may_break_later_coupling": not disease_coupled,
            "interpretation": (
                "Equal seeds provide matched starts; true CRN coupling is claimed only "
                "where stream keys and event paths remain equal."
            ),
        },
    }
    logical_content_hash = sha256_bytes(
        canonical_json_bytes(
            {
                "comparison_id": comparison_id,
                "config_a_hash": _ensemble_config_hash(ensemble_a),
                "config_b_hash": _ensemble_config_hash(ensemble_b),
                "rows": rows,
            }
        )
    )
    return ComparisonResult(
        comparison_id=comparison_id,
        ensemble_a=ensemble_a,
        ensemble_b=ensemble_b,
        paired_rows=tuple(rows),
        diagnostics=diagnostics,
        logical_content_hash=logical_content_hash,
        runtime_seconds=time.perf_counter() - started,
    )
