"""Deterministic Milestone 6 ensemble and matched-seed comparison runners."""

from __future__ import annotations

import multiprocessing as mp
import platform
import resource
import time
from collections import defaultdict
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
) -> tuple[dict[str, Any], ...]:
    grouped: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for rows in trajectories.values():
        for row in rows:
            grouped[(row["scope"], row["key"], row["metric"], row["date"])].append(
                float(row["value"])
            )
    summary: list[dict[str, Any]] = []
    for (scope, key, metric, when), values in sorted(grouped.items()):
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
            }
        )
    return tuple(summary)


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
    parallelism = "sequential"
    parallelism_fallback_reason: str | None = None
    if config.workers == 1:
        outputs = [_run_replicate_job(job) for job in jobs]
    else:
        try:
            context = mp.get_context("spawn")
            with ProcessPoolExecutor(max_workers=config.workers, mp_context=context) as pool:
                futures = [pool.submit(_run_replicate_job, job) for job in jobs]
                outputs = [future.result() for future in futures]
            parallelism = "process_pool_spawn"
        except (NotImplementedError, PermissionError) as exc:
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
        "worker_count": config.workers,
        "parallelism": parallelism,
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
    diagnostics = {
        "status": status,
        "seed_order": list(seeds),
        "paired_seed_count": paired,
        "missing_or_failed_pair_count": missing,
        "pairing_preserved": True,
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
