"""Deterministic Milestone 6 ensemble and matched-seed comparison runners."""

from __future__ import annotations

import json
import multiprocessing as mp
import os
import platform
import resource
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from contextlib import ExitStack
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

import numpy as np

from .ensemble_schemas import EnsembleConfig, EnsembleReplicateRecord
from .hashing import canonical_json_bytes, sha256_bytes, sha256_file
from .intervention_schemas import ScenarioConfig
from .network_generator import GeneratedNetworks, generate_networks
from .observation import ObservationRunResult, observe_latent_run
from .observation_schemas import ObservationConfig
from .outbreak_runner import OutbreakRunResult, run_outbreak
from .outbreak_schemas import RespiratoryParameterSet
from .scientific_hashes import (
    m6_comparison_logical_hash,
    m6_ensemble_config_hash,
    m6_ensemble_logical_hash,
)

MetricSemantic = Literal["incidence", "cumulative", "state"]
CellSemantic = Literal[
    "observed",
    "structural_zero",
    "carried_forward",
    "outside_metric_horizon",
    "failed_replicate",
    "non_contributor",
]

METRIC_SEMANTICS: dict[str, MetricSemantic] = {
    "latent_new_infections": "incidence",
    "latent_local_infections": "incidence",
    "observed_detected_infections": "incidence",
    "observed_reported_cases": "incidence",
    "latent_cumulative_infections": "cumulative",
    "latent_attack_rate": "cumulative",
    "latent_cumulative_incidence_per_capita": "cumulative",
    "latent_ever_infected_fraction": "cumulative",
    "latent_prevalence": "state",
    "intervention_active_agents": "state",
    "intervention_active_households": "state",
    "intervention_active_settings": "state",
    "intervention_route_active": "state",
    "intervention_affected_routes": "state",
    "intervention_affected_residents": "state",
    "intervention_affected_staff": "state",
    "intervention_currently_protected": "state",
    "intervention_new_activations": "incidence",
    "intervention_new_releases": "incidence",
    "intervention_wfh_entries": "incidence",
    "intervention_wfh_exits": "incidence",
    "intervention_vaccine_doses": "incidence",
    "intervention_protection_effective": "incidence",
    "intervention_protection_waned": "incidence",
}

DEFAULT_PARENT_RESERVE_BYTES = 3 * 1024**3
DEFAULT_USABLE_FRACTION = 0.85
# The 180-day Stage-B campaign measured a full process at 2.73 GB including
# parents; the worker steady state was approximately 2.1 GB, so 3.0 GiB adds
# peak headroom. See docs/runs/2026-09-04-r8-stageB-campaign.json.
DEFAULT_PER_WORKER_BYTES = 3 * 1024**3

_REPLICATE_STATE_DIRECTORY = ".replicates-in-progress"


def _empirical_quantile_resolvable(sample_count: int, quantile: float) -> bool:
    """Return whether an empirical interior quantile has one observation in its tail."""

    return quantile in {0.0, 1.0} or sample_count * min(quantile, 1.0 - quantile) >= 1.0


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
    scenario_hash: str | None = None
    intervention_config_hashes: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class EnsembleResult:
    """An ensemble with explicit replicate records and tidy summaries."""

    config: EnsembleConfig
    replicate_records: tuple[EnsembleReplicateRecord, ...]
    replicate_trajectories: dict[int, tuple[dict[str, Any], ...]]
    replicate_grid: tuple[dict[str, Any], ...]
    summary: tuple[dict[str, Any], ...]
    diagnostics: dict[str, Any]
    logical_content_hash: str
    runtime_seconds: float
    peak_memory_bytes: int | None
    m2_logical_content_hash: str
    m3_logical_content_hash: str
    disease_parameter_hash: str
    scenario_hash: str | None = None


@dataclass(frozen=True)
class ComparisonResult:
    """Paired output for two ensembles evaluated on their seed identities."""

    comparison_id: str
    ensemble_a: EnsembleResult
    ensemble_b: EnsembleResult
    paired_rows: tuple[dict[str, Any], ...]
    paired_summary: tuple[dict[str, Any], ...]
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
                {
                    "seed": seed,
                    "scope": "epidemic",
                    "key": "all",
                    "metric": "latent_cumulative_incidence_per_capita",
                    "date": row["date"],
                    "value": row["cumulative_incidence_per_capita"],
                },
                {
                    "seed": seed,
                    "scope": "epidemic",
                    "key": "all",
                    "metric": "latent_ever_infected_fraction",
                    "date": row["date"],
                    "value": row["ever_infected_fraction"],
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
    for row in latent.intervention_state:
        state_metrics = {
            "intervention_active_agents": "active_agents",
            "intervention_active_households": "active_households",
            "intervention_active_settings": "active_settings",
            "intervention_route_active": "route_intervention_active",
            "intervention_affected_routes": "affected_routes",
            "intervention_affected_residents": "affected_residents",
            "intervention_affected_staff": "affected_staff",
            "intervention_currently_protected": "currently_protected",
            "intervention_new_activations": "new_activations",
            "intervention_new_releases": "new_releases",
            "intervention_wfh_entries": "new_wfh_entries",
            "intervention_wfh_exits": "wfh_exits",
            "intervention_vaccine_doses": "doses_administered",
            "intervention_protection_effective": "protection_became_effective",
            "intervention_protection_waned": "protection_waned",
        }
        rows.extend(
            {
                "seed": seed,
                "scope": "intervention",
                "key": row["intervention_id"],
                "metric": metric,
                "date": row["date"],
                "value": row[field],
            }
            for metric, field in state_metrics.items()
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
        scenario = (
            ScenarioConfig.model_validate(job["scenario"]).model_copy(update={"seed": seed})
            if job.get("scenario") is not None
            else None
        )
        latent = run_outbreak(
            generated,
            run_config,
            parameters,
            observation_config=observation_config,
            scenario=scenario,
        )
        observed = observe_latent_run(latent, observation_config)
        return ReplicateOutput(
            seed=seed,
            status="passed",
            latent_logical_content_hash=latent.logical_content_hash,
            observation_logical_content_hash=observed.logical_content_hash,
            m4_logical_content_hash=generated.logical_content_hash,
            scenario_hash=latent.scenario_hash,
            intervention_config_hashes=latent.intervention_diagnostics.get(
                "intervention_config_hashes", {}
            ),
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


def _git_commit_identity(root: Path) -> str | None:
    """Return the code commit used for checkpoint provenance, when available."""

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        result = None
    commit = result.stdout.strip() if result is not None else ""
    if commit:
        return commit
    try:
        return f"source:{sha256_file(Path(__file__))}"
    except OSError:
        return None


def _replicate_provenance(
    *,
    seed: int,
    base_config_hash: str,
    code_identity: str | None,
    m2_hash: str,
    m3_hash: str,
) -> dict[str, Any]:
    """Build the complete identity tuple required to trust one checkpoint."""

    return {
        "replicate_seed": seed,
        "base_config_hash": base_config_hash,
        "code_identity": code_identity,
        "m2_logical_content_hash": m2_hash,
        "m3_logical_content_hash": m3_hash,
    }


def _replicate_state_path(root: Path, ensemble_id: str, seed: int) -> Path:
    # Namespace checkpoints by ensemble so concurrent or successive ensembles
    # sharing a seed can never overwrite each other's completed work.
    safe_ensemble = "".join(c if c.isalnum() or c in "-_." else "_" for c in ensemble_id)
    return root / _REPLICATE_STATE_DIRECTORY / safe_ensemble / f"seed-{seed}.json"


def _replicate_output_payload(output: ReplicateOutput) -> dict[str, Any]:
    payload = asdict(output)
    payload["trajectories"] = [dict(row) for row in output.trajectories]
    return payload


def _persist_replicate_output(
    path: Path, provenance: dict[str, Any], output: ReplicateOutput
) -> None:
    """Atomically checkpoint one resolved result outside the artifact tree."""

    from .execution_adapter import _atomic_write_json

    output_payload = _replicate_output_payload(output)
    _atomic_write_json(
        path,
        {
            "provenance": provenance,
            "output": output_payload,
            "output_sha256": sha256_bytes(canonical_json_bytes(output_payload)),
        },
    )


def _read_replicate_output(
    path: Path, expected_provenance: dict[str, Any]
) -> ReplicateOutput | None:
    """Read a checkpoint only when its complete identity and content validate."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("checkpoint is not an object")
        if payload.get("provenance") != expected_provenance:
            return None
        output_payload = payload.get("output")
        if not isinstance(output_payload, dict):
            raise ValueError("checkpoint output is not an object")
        if payload.get("output_sha256") != sha256_bytes(canonical_json_bytes(output_payload)):
            raise ValueError("checkpoint output digest mismatch")
        required = {
            "seed",
            "status",
            "latent_logical_content_hash",
            "observation_logical_content_hash",
            "m4_logical_content_hash",
            "runtime_seconds",
            "trajectories",
            "error",
            "scenario_hash",
            "intervention_config_hashes",
        }
        if set(output_payload) != required:
            raise ValueError("checkpoint output fields are incomplete")
        trajectories = output_payload["trajectories"]
        if not isinstance(trajectories, list) or not all(
            isinstance(row, dict) for row in trajectories
        ):
            raise ValueError("checkpoint trajectories are invalid")
        output = ReplicateOutput(
            seed=output_payload["seed"],
            status=output_payload["status"],
            latent_logical_content_hash=output_payload["latent_logical_content_hash"],
            observation_logical_content_hash=output_payload["observation_logical_content_hash"],
            m4_logical_content_hash=output_payload["m4_logical_content_hash"],
            runtime_seconds=output_payload["runtime_seconds"],
            trajectories=tuple(trajectories),
            error=output_payload["error"],
            scenario_hash=output_payload["scenario_hash"],
            intervention_config_hashes=output_payload["intervention_config_hashes"],
        )
        if output.seed != expected_provenance["replicate_seed"]:
            raise ValueError("checkpoint seed does not match provenance")
        if output.status not in {"passed", "failed"}:
            raise ValueError("checkpoint status is invalid")
        if output.status == "passed" and (
            not output.latent_logical_content_hash
            or not output.observation_logical_content_hash
            or output.error is not None
        ):
            raise ValueError("passed checkpoint is invalid")
        if output.status == "failed" and not output.error:
            raise ValueError("failed checkpoint has no error")
        return output
    except (OSError, TypeError, ValueError, KeyError):
        return None


def _load_replicate_checkpoints(
    root: Path,
    ensemble_id: str,
    expected_provenance: dict[int, dict[str, Any]],
) -> tuple[dict[int, ReplicateOutput], int]:
    """Load matching checkpoints and count malformed or stale files reported."""

    state_directory = _replicate_state_path(root, ensemble_id, 0).parent
    if not state_directory.exists():
        return {}, 0
    resumed: dict[int, ReplicateOutput] = {}
    ignored = 0
    for path in sorted(state_directory.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            provenance = raw.get("provenance") if isinstance(raw, dict) else None
            seed = provenance.get("replicate_seed") if isinstance(provenance, dict) else None
        except (OSError, TypeError, ValueError):
            seed = None
        expected = expected_provenance.get(seed) if isinstance(seed, int) else None
        output = _read_replicate_output(path, expected) if expected is not None else None
        if output is None or output.seed in resumed:
            ignored += 1
            continue
        resumed[output.seed] = output
    return resumed, ignored


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
    failed_replicates = max(0, requested - successful_replicates)
    grid = _completed_grid_rows(
        trajectories,
        successful_seeds=tuple(sorted(trajectories)),
        failed_seeds=(),
        horizon=horizon,
    )
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for row in grid:
        group_key = (row["scope"], row["key"], row["metric"], row["date"])
        grouped.setdefault(group_key, []).append(row)
    summary: list[dict[str, Any]] = []
    for (scope, key, metric, when), cells in sorted(grouped.items()):
        values = [float(cell["value"]) for cell in cells if cell["contributes"]]
        semantics = {
            semantic: sum(cell["cell_semantic"] == semantic for cell in cells)
            for semantic in (
                "observed",
                "structural_zero",
                "carried_forward",
                "outside_metric_horizon",
                "non_contributor",
            )
        }
        present_semantics = [name for name, count in semantics.items() if count]
        cell_semantic = present_semantics[0] if len(present_semantics) == 1 else "mixed"
        lower_value = median = upper_value = None
        tail_ranks = [
            len(values) * min(quantile, 1.0 - quantile)
            for quantile in (lower_quantile, upper_quantile)
            if quantile not in {0.0, 1.0}
        ]
        tail_rank = min(tail_ranks, default=float(len(values)))
        median_resolvable = _empirical_quantile_resolvable(len(values), 0.5)
        tails_resolvable = all(
            _empirical_quantile_resolvable(len(values), quantile)
            for quantile in (lower_quantile, upper_quantile)
        )
        if values:
            if median_resolvable:
                median = float(np.quantile(np.asarray(values, dtype=float), 0.5, method="linear"))
            if tails_resolvable:
                quantiles = np.quantile(
                    np.asarray(values, dtype=float),
                    [lower_quantile, upper_quantile],
                    method="linear",
                )
                lower_value, upper_value = (float(value) for value in quantiles)
        summary.append(
            {
                "scope": scope,
                "key": key,
                "metric": metric,
                "metric_semantic": METRIC_SEMANTICS[metric],
                "date": when,
                "cell_semantic": cell_semantic,
                "lower_quantile": lower_quantile,
                "median": median,
                "upper_quantile": upper_quantile,
                "lower_value": lower_value,
                "upper_value": upper_value,
                "interval_class": (
                    "stochastic_replicate_quantile" if tails_resolvable else "insufficient_tail"
                ),
                "quantile_method": "numpy.quantile(method='linear')",
                "tail_rank": tail_rank,
                "replicate_count": len(values),
                "requested_replicates": requested,
                "successful_replicates": successful_replicates,
                "failed_replicates": failed_replicates,
                "contributing_replicates": len(values),
                "observed_replicates": semantics["observed"],
                "structural_zero_replicates": semantics["structural_zero"],
                "carried_forward_replicates": semantics["carried_forward"],
                "outside_metric_horizon_replicates": semantics["outside_metric_horizon"],
                "non_contributing_replicates": (
                    semantics["outside_metric_horizon"]
                    + semantics["non_contributor"]
                    + failed_replicates
                ),
            }
        )
    return tuple(summary)


def _completed_grid_rows(
    trajectories: dict[int, tuple[dict[str, Any], ...]],
    *,
    successful_seeds: tuple[int, ...],
    failed_seeds: tuple[int, ...],
    horizon: tuple[str, ...] | None = None,
) -> tuple[dict[str, Any], ...]:
    """Complete the replicate/date grid according to explicit metric semantics."""

    metric_keys = sorted(
        {
            (row["scope"], row["key"], row["metric"])
            for rows in trajectories.values()
            for row in rows
        }
    )
    unknown = sorted({metric for _scope, _key, metric in metric_keys} - METRIC_SEMANTICS.keys())
    if unknown:
        raise ValueError(f"metrics are missing semantic registration: {unknown}")
    dates = tuple(
        horizon or sorted({row["date"] for rows in trajectories.values() for row in rows})
    )
    indexed = {
        seed: {
            (row["scope"], row["key"], row["metric"], row["date"]): float(row["value"])
            for row in rows
        }
        for seed, rows in trajectories.items()
    }
    rows: list[dict[str, Any]] = []
    for seed in (*successful_seeds, *failed_seeds):
        failed = seed in failed_seeds
        seed_index = indexed.get(seed, {})
        for scope, key, metric in metric_keys:
            semantic = METRIC_SEMANTICS[metric]
            observations = sorted(
                (date_key, value)
                for (row_scope, row_key, row_metric, date_key), value in seed_index.items()
                if (row_scope, row_key, row_metric) == (scope, key, metric)
            )
            observation_map = dict(observations)
            for when in dates:
                value: float | None = None
                cell_semantic: CellSemantic
                contributes = False
                if failed:
                    cell_semantic = "failed_replicate"
                elif when in observation_map:
                    value = observation_map[when]
                    cell_semantic = "observed"
                    contributes = True
                elif not observations:
                    cell_semantic = "non_contributor"
                elif semantic == "incidence":
                    value = 0.0
                    cell_semantic = "structural_zero"
                    contributes = True
                elif semantic == "cumulative":
                    previous = [item for item in observations if item[0] < when]
                    if previous:
                        value = previous[-1][1]
                        cell_semantic = "carried_forward"
                    else:
                        value = 0.0
                        cell_semantic = "structural_zero"
                    contributes = True
                elif when < observations[0][0] or when > observations[-1][0]:
                    cell_semantic = "outside_metric_horizon"
                else:
                    cell_semantic = "non_contributor"
                rows.append(
                    {
                        "seed": seed,
                        "scope": scope,
                        "key": key,
                        "metric": metric,
                        "metric_semantic": semantic,
                        "date": when,
                        "value": value,
                        "cell_semantic": cell_semantic,
                        "contributes": contributes,
                    }
                )
    return tuple(rows)


def available_physical_memory_bytes() -> int | None:
    """Return discoverable physical memory without adding a psutil dependency."""

    try:
        page_size = int(os.sysconf("SC_PAGE_SIZE"))
        page_count = int(os.sysconf("SC_PHYS_PAGES"))
    except (AttributeError, OSError, TypeError, ValueError):
        return None
    return page_size * page_count if page_size > 0 and page_count > 0 else None


def available_cpu_count() -> int:
    """Return CPUs available to this process, respecting scheduler affinity."""

    try:
        return max(1, len(os.sched_getaffinity(0)))
    except (AttributeError, OSError):
        process_cpu_count = getattr(os, "process_cpu_count", None)
        if process_cpu_count is not None:
            count = process_cpu_count()
            if count is not None:
                return max(1, count)
        return max(1, os.cpu_count() or 1)


def _worker_bound_terms(
    requested_workers: int,
    *,
    parent_reserve_bytes: int,
    usable_fraction: float,
    per_worker_bytes: int,
    available_memory_bytes: int | None,
    cpu_count: int | None,
) -> dict[str, int | float | None]:
    if requested_workers < 1 or parent_reserve_bytes < 0 or per_worker_bytes < 1:
        raise ValueError("worker and memory estimates must be positive")
    if not 0 < usable_fraction <= 1:
        raise ValueError("usable_fraction must be in (0, 1]")
    cpu_bound = max(1, cpu_count) if cpu_count is not None else available_cpu_count()
    memory = (
        available_memory_bytes
        if available_memory_bytes is not None
        else available_physical_memory_bytes()
    )
    usable_memory = None if memory is None else max(0, memory - parent_reserve_bytes)
    memory_bound = (
        requested_workers
        if usable_memory is None
        else max(1, int(usable_memory * usable_fraction // per_worker_bytes))
    )
    resulting_bound = max(1, min(requested_workers, cpu_bound, memory_bound))
    return {
        "parent_reserve_bytes": parent_reserve_bytes,
        "usable_fraction": usable_fraction,
        "per_worker_bytes": per_worker_bytes,
        "available_memory_bytes": memory,
        "usable_memory_bytes": usable_memory,
        "memory_bound": memory_bound,
        "cpu_bound": cpu_bound,
        "resulting_bound": resulting_bound,
    }


def safe_worker_bound(
    requested_workers: int,
    *,
    parent_reserve_bytes: int = DEFAULT_PARENT_RESERVE_BYTES,
    usable_fraction: float = DEFAULT_USABLE_FRACTION,
    per_worker_bytes: int = DEFAULT_PER_WORKER_BYTES,
    available_memory_bytes: int | None = None,
    cpu_count: int | None = None,
    # Retained as execution-only aliases for callers of the pre-R8 interface.
    estimated_worker_memory_bytes: int | None = None,
    memory_safety_fraction: float | None = None,
) -> int:
    """Bound workers by an explicit parent reserve, memory budget and CPU."""

    if estimated_worker_memory_bytes is not None:
        per_worker_bytes = estimated_worker_memory_bytes
    if memory_safety_fraction is not None:
        usable_fraction = memory_safety_fraction
    terms = _worker_bound_terms(
        requested_workers,
        parent_reserve_bytes=parent_reserve_bytes,
        usable_fraction=usable_fraction,
        per_worker_bytes=per_worker_bytes,
        available_memory_bytes=available_memory_bytes,
        cpu_count=cpu_count,
    )
    resulting_bound = terms["resulting_bound"]
    if resulting_bound is None:
        raise RuntimeError("worker-bound calculation produced no resulting bound")
    return int(resulting_bound)


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
    estimated_worker_memory_bytes: int = DEFAULT_PER_WORKER_BYTES,
    memory_safety_fraction: float = DEFAULT_USABLE_FRACTION,
    allow_unsafe_workers: bool = False,
    scenario: ScenarioConfig | None = None,
    parent_reserve_bytes: int = DEFAULT_PARENT_RESERVE_BYTES,
    usable_fraction: float | None = None,
    per_worker_bytes: int | None = None,
) -> EnsembleResult:
    """Run explicit seeds sequentially or in a bounded process pool."""

    from .outbreak_schemas import OutbreakRunConfig

    base_run_config = OutbreakRunConfig.model_validate(base_run_config)
    if per_worker_bytes is not None:
        estimated_worker_memory_bytes = per_worker_bytes
    if usable_fraction is not None:
        memory_safety_fraction = usable_fraction
    config = EnsembleConfig(
        ensemble_id=ensemble_id,
        base_run_config=base_run_config,
        observation_config=observation_config,
        scenario=scenario,
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
    base_config_hash = m6_ensemble_config_hash(config.model_dump(mode="json"))
    m2_hash = generated.m2_input.manifest.logical_content_hash
    m3_hash = generated.m3_input.manifest.logical_content_hash
    code_identity = _git_commit_identity(source_root)
    expected_provenance = {
        seed: _replicate_provenance(
            seed=seed,
            base_config_hash=base_config_hash,
            code_identity=code_identity,
            m2_hash=m2_hash,
            m3_hash=m3_hash,
        )
        for seed in config.replicate_seeds
    }
    outputs_by_seed, ignored_checkpoints = _load_replicate_checkpoints(
        root, config.ensemble_id, expected_provenance
    )
    resumed_count = len(outputs_by_seed)
    pending_seeds = tuple(seed for seed in config.replicate_seeds if seed not in outputs_by_seed)
    print(
        "ENSEMBLE RESUME: "
        f"resumed={resumed_count} run={len(pending_seeds)} ignored={ignored_checkpoints}",
        file=sys.stderr,
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
        "scenario": scenario,
    }
    jobs = [
        {**job_base, "seed": seed, "provenance": expected_provenance[seed]}
        for seed in pending_seeds
    ]
    requested_workers = config.workers
    worker_bound_terms = _worker_bound_terms(
        requested_workers,
        parent_reserve_bytes=parent_reserve_bytes,
        usable_fraction=config.memory_safety_fraction,
        per_worker_bytes=config.estimated_worker_memory_bytes,
        available_memory_bytes=None,
        cpu_count=None,
    )
    resulting_bound = worker_bound_terms["resulting_bound"]
    if resulting_bound is None:
        raise RuntimeError("worker-bound calculation produced no resulting bound")
    safe_bound = requested_workers if config.allow_unsafe_workers else int(resulting_bound)
    planned_workers = min(requested_workers, safe_bound)
    if planned_workers < requested_workers:
        print(
            "ENSEMBLE WARNING: workers bounded "
            f"requested={requested_workers} planned={planned_workers}",
            file=sys.stderr,
        )
    actual_workers = planned_workers
    execution_mode = "sequential"
    fallback_reason: str | None = None
    persisted_count = 0
    if not jobs:
        actual_workers = 1
        execution_mode = "resume_only"
    elif planned_workers == 1:
        for job in jobs:
            output = _run_replicate_job(job)
            _persist_replicate_output(
                _replicate_state_path(root, config.ensemble_id, output.seed),
                job["provenance"],
                output,
            )
            outputs_by_seed[output.seed] = output
            persisted_count += 1
        if requested_workers > 1:
            execution_mode = "sequential_memory_bound"
    else:
        pool_stack = ExitStack()
        try:
            context = mp.get_context("spawn")
            pool = pool_stack.enter_context(
                ProcessPoolExecutor(max_workers=planned_workers, mp_context=context)
            )
        except (NotImplementedError, OSError, PermissionError, RuntimeError) as exc:
            pool_stack.close()
            # Some constrained macOS runners deny the semaphore limit probe
            # used by ProcessPoolExecutor.  This is an execution-environment
            # limitation, not a replicate result; preserve deterministic
            # semantics with an explicit, diagnostic sequential fallback.
            print(
                "ENSEMBLE WARNING: process pool unavailable "
                f"({type(exc).__name__}: {exc}); actual_workers=1; "
                f"running {len(jobs)} replicates sequentially",
                file=sys.stderr,
            )
            for job in jobs:
                output = _run_replicate_job(job)
                _persist_replicate_output(
                    _replicate_state_path(root, config.ensemble_id, output.seed),
                    job["provenance"],
                    output,
                )
                outputs_by_seed[output.seed] = output
                persisted_count += 1
            actual_workers = 1
            execution_mode = "sequential_fallback"
            fallback_reason = f"{type(exc).__name__}: {exc}"
        else:
            future_jobs = {}
            try:
                for job in jobs:
                    future_jobs[pool.submit(_run_replicate_job, job)] = job
                for future in as_completed(future_jobs):
                    job = future_jobs[future]
                    output = future.result()
                    _persist_replicate_output(
                        _replicate_state_path(root, config.ensemble_id, output.seed),
                        job["provenance"],
                        output,
                    )
                    outputs_by_seed[output.seed] = output
                    persisted_count += 1
            except BrokenProcessPool as exc:
                # A pool can report broken after one or more futures completed;
                # collect any already-done successful/failure records before
                # aborting so those records remain resumable.
                for future, job in future_jobs.items():
                    if not future.done():
                        continue
                    try:
                        output = future.result()
                    except Exception:
                        continue
                    if output.seed in outputs_by_seed:
                        continue
                    _persist_replicate_output(
                        _replicate_state_path(root, config.ensemble_id, output.seed),
                        job["provenance"],
                        output,
                    )
                    outputs_by_seed[output.seed] = output
                    persisted_count += 1
                message = (
                    f"ensemble worker pool broke: {exc}; relaunch with fewer workers; "
                    f"persisted completed outputs={persisted_count}; "
                    "re-invocation will resume them"
                )
                print(f"ENSEMBLE ERROR: {message}", file=sys.stderr)
                raise RuntimeError(message) from exc
            finally:
                pool_stack.close()
            execution_mode = "process_pool_spawn"

    outputs = [outputs_by_seed[seed] for seed in config.replicate_seeds]
    records = tuple(
        EnsembleReplicateRecord(
            seed=output.seed,
            status=output.status,
            latent_run_logical_content_hash=output.latent_logical_content_hash,
            observation_logical_content_hash=output.observation_logical_content_hash,
            m4_logical_content_hash=output.m4_logical_content_hash,
            scenario_hash=output.scenario_hash,
            intervention_config_hashes=output.intervention_config_hashes,
            runtime_seconds=output.runtime_seconds,
            error=output.error,
        )
        for output in outputs
    )
    successful_trajectories = {
        output.seed: output.trajectories for output in outputs if output.status == "passed"
    }
    successful_seeds = tuple(output.seed for output in outputs if output.status == "passed")
    failed_seeds = tuple(output.seed for output in outputs if output.status == "failed")
    replicate_grid = _completed_grid_rows(
        successful_trajectories,
        successful_seeds=successful_seeds,
        failed_seeds=failed_seeds,
    )
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
        "planned_workers": planned_workers,
        "actual_workers": actual_workers,
        "execution_mode": execution_mode,
        "fallback_reason": fallback_reason,
        "parallelism": execution_mode,
        "worker_bound": {
            "safe_upper_bound": safe_bound,
            "honest_resulting_bound": worker_bound_terms["resulting_bound"],
            "parent_reserve_bytes": worker_bound_terms["parent_reserve_bytes"],
            "usable_fraction": worker_bound_terms["usable_fraction"],
            "per_worker_bytes": worker_bound_terms["per_worker_bytes"],
            "usable_memory_bytes": worker_bound_terms["usable_memory_bytes"],
            "memory_bound": worker_bound_terms["memory_bound"],
            "cpu_bound": worker_bound_terms["cpu_bound"],
            "resulting_bound": worker_bound_terms["resulting_bound"],
            "estimated_worker_memory_bytes": config.estimated_worker_memory_bytes,
            "memory_safety_fraction": config.memory_safety_fraction,
            "available_physical_memory_bytes": worker_bound_terms["available_memory_bytes"],
            "cpu_count": worker_bound_terms["cpu_bound"],
            "override_used": config.allow_unsafe_workers,
        },
        "resumed_replicates": resumed_count,
        "run_replicates": len(pending_seeds),
        "ignored_replicate_checkpoints": ignored_checkpoints,
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
        "scenario_config_hash": scenario.config_hash if scenario is not None else None,
        "replicate_scenario_run_hashes": {
            str(output.seed): output.scenario_hash
            for output in outputs
            if output.status == "passed" and output.scenario_hash is not None
        },
        "date_grid": {
            "complete": True,
            "metric_semantics": dict(sorted(METRIC_SEMANTICS.items())),
            "incidence": "missing valid cells are structural zeroes",
            "cumulative": "missing later cells carry the most recent value forward",
            "state": "cells beyond actual state evolution are outside_metric_horizon",
            "failures": "failed replicate cells are non-contributing, never zero",
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
    if fallback_reason is not None:
        diagnostics["parallelism_fallback_reason"] = fallback_reason
    logical_content_hash = m6_ensemble_logical_hash(
        config=config.model_dump(mode="json"),
        replicate_records=[record.model_dump(mode="json") for record in records],
        summary=list(summary),
        trajectories=successful_trajectories,
        replicate_grid=list(replicate_grid),
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
        replicate_grid=replicate_grid,
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
        scenario_hash=(
            sha256_bytes(
                canonical_json_bytes(
                    {
                        str(record.seed): record.scenario_hash
                        for record in records
                        if record.status == "passed" and record.scenario_hash is not None
                    }
                )
            )
            if scenario is not None
            else None
        ),
    )


def _ensemble_config_hash(result: EnsembleResult) -> str:
    return m6_ensemble_config_hash(result.config.model_dump(mode="json"))


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
    paired_groups: dict[tuple[str, str, str, str], list[float]] = {}
    for row in rows:
        if row["status"] != "paired" or row["difference"] is None:
            continue
        group_key = (row["scope"], row["key"], row["metric"], row["date"])
        paired_groups.setdefault(group_key, []).append(float(row["difference"]))
    paired_summary: list[dict[str, Any]] = []
    lower_quantile = ensemble_a.config.lower_quantile
    upper_quantile = ensemble_a.config.upper_quantile
    for (scope, summary_key, metric, when), differences in sorted(paired_groups.items()):
        values = np.asarray(differences, dtype=float)
        median_resolvable = _empirical_quantile_resolvable(len(differences), 0.5)
        median = float(np.quantile(values, 0.5, method="linear")) if median_resolvable else None
        tail_ranks = [
            len(differences) * min(quantile, 1.0 - quantile)
            for quantile in (lower_quantile, upper_quantile)
            if quantile not in {0.0, 1.0}
        ]
        tail_rank = min(tail_ranks, default=float(len(differences)))
        tails_resolvable = all(
            _empirical_quantile_resolvable(len(differences), quantile)
            for quantile in (lower_quantile, upper_quantile)
        )
        lower: float | None = None
        upper: float | None = None
        if tails_resolvable:
            lower_value, upper_value = np.quantile(
                values, [lower_quantile, upper_quantile], method="linear"
            )
            lower, upper = float(lower_value), float(upper_value)
        paired_summary.append(
            {
                "scope": scope,
                "key": summary_key,
                "metric": metric,
                "date": when,
                "paired_count": len(differences),
                "requested_pair_count": len(seeds),
                "missing_or_failed_pair_count": len(seeds) - len(differences),
                "lower_quantile": lower_quantile,
                "lower_difference": lower,
                "median_difference": median,
                "upper_quantile": upper_quantile,
                "upper_difference": upper,
                "interval_class": (
                    "paired_stochastic_replicate_quantile"
                    if tails_resolvable
                    else "insufficient_tail"
                ),
                "quantile_method": "numpy.quantile(method='linear')",
                "tail_rank": tail_rank,
                "mean_difference": float(values.mean()),
                "fraction_negative": float(np.mean(values < 0)),
                "fraction_zero": float(np.mean(values == 0)),
                "fraction_positive": float(np.mean(values > 0)),
                "coupling_caveat": (
                    "Equal seeds provide matched starts; event-path divergence may break "
                    "later common-random-number coupling."
                ),
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
        "paired_summary_row_count": len(paired_summary),
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
    logical_content_hash = m6_comparison_logical_hash(
        comparison_id=comparison_id,
        config_a_hash=_ensemble_config_hash(ensemble_a),
        config_b_hash=_ensemble_config_hash(ensemble_b),
        rows=rows,
        summary=paired_summary,
    )
    return ComparisonResult(
        comparison_id=comparison_id,
        ensemble_a=ensemble_a,
        ensemble_b=ensemble_b,
        paired_rows=tuple(rows),
        paired_summary=tuple(paired_summary),
        diagnostics=diagnostics,
        logical_content_hash=logical_content_hash,
        runtime_seconds=time.perf_counter() - started,
    )
