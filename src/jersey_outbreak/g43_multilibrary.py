"""Frozen G43 declaration, generation, blind fitting and recovery evaluation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from datetime import date
from decimal import Context, Decimal, Inexact, localcontext
from itertools import groupby, product
from operator import attrgetter
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any, Literal, TypedDict, cast

import yaml  # type: ignore[import-untyped]

from . import g43_constants as frozen
from . import g43_recompute as audit
from .g35b_design_study import (
    STOCHASTIC_REPLICATE_VARIATION,
    _compare,
    _contains_key,
    _fit_scored_grid,
    _fixed_run_provenance,
    _GenerationAdapter,
    _offset_descriptive,
    _persist_fit,
    _require_clean_worktree,
    _verify_blind_readback,
    batch_objective_spread,
    batch_offset_agreement,
    committed_document_bytes,
    loss,
)
from .g35b_design_study import StudyConfig as _AdapterConfig
from .g35b_design_study import WorkCounter as _AdapterCounter
from .network_generator import GeneratedNetworks
from .observation import ObservationRunResult
from .observation_schemas import ObservationConfig
from .outbreak_runner import OutbreakRunResult, load_parameter_set
from .outbreak_schemas import OutbreakRunConfig, RespiratoryParameterSet
from .parent_build import build_parent
from .phase0_campaign import (
    P01_ROUTE_IDS,
    BlindFitResult,
    BudgetError,
    CampaignError,
    CandidateCell,
    DimensionSpec,
    ObservedTables,
    ProfileDiagnostic,
    TruthDiagnostics,
    _compact_json_bytes,
    _namespace_passes,
    _truth_diagnostics_from_result,
    observation_dates,
)


def _work_counts(values: Sequence[int]) -> dict[str, int]:
    return dict(zip(frozen.WORK_FIELDS, values, strict=True))


_DIMENSIONS = tuple(
    DimensionSpec(
        name,
        float(truth),
        tuple(map(float, grid)),
        float(tolerance),
        float(bias_limit),
        Decimal(truth),
        tuple(map(Decimal, grid)),
        Decimal(tolerance),
        Decimal(bias_limit),
    )
    for name, truth, grid, tolerance, bias_limit in frozen.DIMENSIONS
)
_START_DATE = date(2025, 1, 6)
_TAIL_DAYS = 4
_IMPORT_ATTEMPTS = 10
_POPULATION_SIZE = 3000
_TARGET_CONFIG_ID = "v13-g43-target"
_FIT_CONFIG_ID = "v13-g43-fit"
_TARGET_PROCESS_SEEDS = tuple(row.process for row in frozen.FINAL_SEEDS if row.library is None)


def _seed_payload(rows: Sequence[frozen.FinalSeed]) -> dict[str, Any]:
    targets = [row for row in rows if row.library is None]
    return {
        "target_process_seeds": [row.process for row in targets],
        "target_observation_seeds": [row.observation for row in targets],
        "candidate_libraries": {
            f"L{library}": {
                f"batch{batch}": {
                    "process_seeds": [
                        row.process for row in rows if (row.library, row.batch) == (library, batch)
                    ],
                    "observation_seeds": [
                        row.observation
                        for row in rows
                        if (row.library, row.batch) == (library, batch)
                    ],
                }
                for batch in range(1, frozen.BATCH_COUNT + 1)
            }
            for library in range(1, frozen.LIBRARY_COUNT + 1)
        },
        "unused_reserve_process_seeds": list(frozen.UNUSED_RESERVE_SEEDS),
        "excluded_primary_process_seeds": list(frozen.EXCLUDED_PRIMARY_SEEDS),
        "target_observation_config_id": _TARGET_CONFIG_ID,
        "candidate_observation_config_id": _FIT_CONFIG_ID,
        "optimizer_seed": None,
    }


def frozen_payload() -> dict[str, Any]:
    """Build the expected payload from the independent declaration controls."""
    return {
        "campaign_id": "v13-g43",
        "expected_predeclaration_sha256": frozen.PREDECLARATION_SHA256,
        "mode": "ci",
        "start_date": _START_DATE.isoformat(),
        "latent_days": frozen.LATENT_DAYS,
        "calendar_dates": frozen.CALENDAR_DATES,
        "observation_horizon_tail_days": _TAIL_DAYS,
        "dimensions": {
            name: {
                "truth": truth,
                "candidates": list(grid),
                "tolerance": tolerance,
                "bias_limit": bias_limit,
            }
            for name, truth, grid, tolerance, bias_limit in frozen.DIMENSIONS
        },
        "fixed_scenario": {
            "population_size": _POPULATION_SIZE,
            "initial_seed_count": 0,
            "inoculation_attempts": _IMPORT_ATTEMPTS,
            "inoculation_schedule": "start_date_plus_offset",
            "import_schedule": "empty_except_inoculation",
            "background_import_rate_per_day": "0",
            "route_multipliers": dict.fromkeys(P01_ROUTE_IDS, "1.0"),
            "symptomatic_probability": "0.6",
            "latent_duration_days": 2,
            "infectious_duration_days": 5,
            "waning_enabled": False,
            "seasonality": "absent",
            "interventions": "absent",
        },
        "observation": {
            "channels": ["symptomatic", "asymptomatic"],
            "source": "observation_events",
            "fields": ["report_date", "symptomatic"],
            "detection_delay_days": 0,
            "reporting_delay_days": 2,
            "weekday_effect": ["1.0"] * 7,
            "common_random_numbers": True,
        },
        "objective": {
            "name": "square_root_minimum_distance",
            "poisson_variance_stabilizer": "0.375",
            "candidate_replicate_mean": "arithmetic_mean_of_roots",
            "channel_weight": "equal",
            "date_weight": "equal",
            "all_cells_scored_before_selection": True,
        },
        "identifiability": {
            "tie_scale": "0.000000000001",
            "profile_gap": "0.05",
            "profile_denominator_floor": "0.000000000001",
            "tied_global_minimum": "fail",
        },
        "acceptance": {
            "targets": frozen.TARGET_COUNT,
            "libraries": frozen.LIBRARY_COUNT,
            "hits_fraction": [4, 5],
            "joint_fraction": [3, 5],
            "boundary_fraction": [1, 5],
            "inoculation_acquisitions": _IMPORT_ATTEMPTS,
            "minimum_local_secondary_infections": 1,
            "minimum_reports_per_channel": 1,
            "minimum_nonzero_combined_dates": 3,
        },
        "seeds": _seed_payload(frozen.FINAL_SEEDS),
        "process_hashes": {
            str(seed): dict(zip(("m2", "m3", "m4"), hashes, strict=True))
            for seed, hashes in frozen.PROCESS_HASHES.items()
        },
        "work_caps": {
            "shared_panel": _work_counts(frozen.SHARED_CAPS),
            "per_library": _work_counts(frozen.LIBRARY_CAPS),
            "totals": _work_counts(frozen.TOTAL_CAPS),
        },
        "implementation": {
            "retries": 0,
            "replacement_seeds": False,
            "adaptive_grid": False,
            "pruning": False,
            "early_stopping": False,
        },
    }


def _check_seed_overlap(seeds: Mapping[str, Any]) -> None:
    try:
        all_seeds = [
            *seeds["target_process_seeds"],
            *seeds["target_observation_seeds"],
            *seeds["unused_reserve_process_seeds"],
            *seeds["excluded_primary_process_seeds"],
            *(
                seed
                for library in seeds["candidate_libraries"].values()
                for batch in library.values()
                for key in ("process_seeds", "observation_seeds")
                for seed in batch[key]
            ),
        ]
        unique = set(all_seeds)
    except (KeyError, TypeError, AttributeError) as exc:
        raise CampaignError("invalid frozen declaration seed structure") from exc
    if len(unique) != len(all_seeds):
        raise BudgetError("seed overlap within the study declaration")
    if unique & frozen.EARLIER_SEEDS:
        raise BudgetError("seed overlap with an earlier or retired seed set")


def validate_frozen_payload(payload: Any) -> None:
    """Require every field, value and scalar type of the frozen declaration."""
    if not isinstance(payload, dict):
        raise CampaignError("config must be a YAML mapping")
    seeds = payload.get("seeds")
    if not isinstance(seeds, dict):
        raise CampaignError("invalid frozen declaration seed structure")
    _check_seed_overlap(seeds)
    _compare(payload, frozen_payload())


@dataclass(frozen=True)
class StudyConfig:
    """Runtime view of the G43 payload after its exact checks."""

    mode: str = "ci"
    start_date: date = _START_DATE
    duration_days: int = frozen.LATENT_DAYS
    observation_horizon_tail_days: int = _TAIL_DAYS
    seeds: tuple[frozen.FinalSeed, ...] = frozen.FINAL_SEEDS
    initial_seed_count: int = 0
    inoculation_attempts: int = _IMPORT_ATTEMPTS
    import_rate_per_day: float = 0.0
    route_multipliers: tuple[tuple[str, float], ...] = tuple((name, 1.0) for name in P01_ROUTE_IDS)
    symptomatic_probability: float = 0.6
    waning_enabled: bool = False
    reporting_delay_days: int = 2
    weekday_effect: tuple[float, ...] = (1.0,) * 7
    target_observation_config_id: str = _TARGET_CONFIG_ID
    candidate_observation_config_id: str = _FIT_CONFIG_ID

    @classmethod
    def from_yaml(cls, path: Path) -> StudyConfig:
        try:
            content = path.read_bytes()
            if b"\r" in content:
                raise CampaignError("study config must use LF bytes")
            payload = yaml.safe_load(content)
        except (OSError, yaml.YAMLError) as exc:
            raise CampaignError(f"cannot read study config: {exc}") from exc
        validate_frozen_payload(payload)
        if hashlib.sha256(content).hexdigest() != frozen.CONFIG_SHA256:
            raise CampaignError("study config SHA-256 mismatch")
        return cls()

    @property
    def dimensions(self) -> tuple[DimensionSpec, ...]:
        return _DIMENSIONS

    @property
    def candidate_grid(self) -> tuple[CandidateCell, ...]:
        return tuple(
            CandidateCell(beta, int(offset), sym, asym)
            for beta, offset, sym, asym in product(*(spec.candidates for spec in self.dimensions))
        )


def validate_predeclaration(path: Path) -> str:
    """Verify the supplied LF checkout against the independent freeze blob."""
    if path.is_symlink():
        raise CampaignError("predeclaration must be a committed repository file")
    content = committed_document_bytes(path, commit=frozen.PREDECLARATION_COMMIT)
    # The unchanged G35-B helper accepts CRLF checkouts. G43 requires LF here.
    if path.read_bytes() != content:
        raise CampaignError("predeclaration checkout must match committed LF bytes")
    digest = hashlib.sha256(content).hexdigest()
    if digest != frozen.PREDECLARATION_SHA256:
        raise CampaignError(f"predeclaration SHA-256 mismatch: {digest}")
    return digest


def plan_workload(config: StudyConfig) -> dict[str, Any]:
    """Count declared operations without dispatch and require all three §9 cap columns."""
    if config != StudyConfig():
        raise BudgetError("runtime config differs from the frozen declaration")
    seeds = _seed_payload(config.seeds)
    _check_seed_overlap(seeds)
    dates = observation_dates(
        config.start_date, config.duration_days, config.observation_horizon_tail_days
    )
    if config.mode != "ci" or config.duration_days != 30 or len(dates) != 34:
        raise BudgetError("predicted mode or calendar differs from §9")

    n = len(seeds["target_process_seeds"])
    cells = len(config.candidate_grid)
    latent_tuples = math.prod(len(spec.candidates) for spec in config.dimensions[:2])
    shared = _work_counts((n, n, n, 0, 0, 0, 0, 0, 0))
    if shared != _work_counts(frozen.SHARED_CAPS):
        raise BudgetError("predicted shared-panel work differs from exact caps")

    libraries = {}
    for name, batches in seeds["candidate_libraries"].items():
        if any(len(batch["process_seeds"]) != frozen.BATCH_SIZE for batch in batches.values()):
            raise BudgetError(f"predicted {name} batch size differs from the frozen declaration")
        replicates = sum(len(batch["process_seeds"]) for batch in batches.values())
        descriptive_fits_per_target = len(batches) + 1  # four single batches and batches 1∪2
        counts = _work_counts(
            (
                replicates,
                replicates * latent_tuples,
                replicates * cells,
                cells,
                n * cells,
                n,
                descriptive_fits_per_target * n * cells,
                descriptive_fits_per_target * n,
                0,
            )
        )
        if counts != _work_counts(frozen.LIBRARY_CAPS):
            raise BudgetError(f"predicted {name} work differs from exact caps")
        libraries[name] = counts

    totals = {
        key: shared[key] + sum(counts[key] for counts in libraries.values())
        for key in frozen.WORK_FIELDS
    }
    if totals != _work_counts(frozen.TOTAL_CAPS):
        raise BudgetError("predicted total work differs from exact caps")
    return {
        "mode": config.mode,
        "latent_days": config.duration_days,
        "calendar_dates": len(dates),
        "shared_panel": shared,
        "libraries": libraries,
        "totals": totals,
    }


_LIBRARY_NUMBERS = tuple(range(1, frozen.LIBRARY_COUNT + 1))
_REPLICATES = frozen.BATCH_COUNT * frozen.BATCH_SIZE
_BATCH_SLICES = {
    f"batch{batch}": slice((batch - 1) * frozen.BATCH_SIZE, batch * frozen.BATCH_SIZE)
    for batch in range(1, frozen.BATCH_COUNT + 1)
}
_GATE_FIT = "all_twelve"
_REFERENCE_SLICES = {**_BATCH_SLICES, "batches_1_2": slice(0, 2 * frozen.BATCH_SIZE)}
_FIT_SLICES = {_GATE_FIT: slice(0, _REPLICATES), **_REFERENCE_SLICES}
_TIMED_PHASES = ("build", "latent", "transform", "scoring", "retention")


class WorkLedger:
    """Operational §9 counters. Reservations survive exceptions at dispatch."""

    def __init__(self) -> None:
        self._caps: dict[int | None, dict[str, int]] = {
            None: _work_counts(frozen.SHARED_CAPS),
            **{number: _work_counts(frozen.LIBRARY_CAPS) for number in _LIBRARY_NUMBERS},
        }
        self._counts = {scope: dict.fromkeys(frozen.WORK_FIELDS, 0) for scope in self._caps}
        self._total_caps = _work_counts(frozen.TOTAL_CAPS)
        self._totals = dict.fromkeys(frozen.WORK_FIELDS, 0)
        self.phase_seconds = {scope: dict.fromkeys(_TIMED_PHASES, 0.0) for scope in self._caps}
        self.latent_runtimes: dict[int | None, list[dict[str, Any]]] = {
            scope: [] for scope in self._caps
        }
        self.fallbacks: dict[int | None, dict[int, dict[str, bool]]] = {
            scope: {} for scope in self._caps
        }

    @contextmanager
    def time_phase(self, library: int | None, phase: str) -> Iterator[None]:
        started = time.perf_counter()
        try:
            yield
        finally:
            self.phase_seconds[library][phase] += time.perf_counter() - started

    def reserve(self, library: int | None, kind: str) -> None:
        counts = self._counts[library]
        if (
            counts[kind] >= self._caps[library][kind]
            or self._totals[kind] >= self._total_caps[kind]
        ):
            scope = "shared panel" if library is None else f"L{library}"
            raise BudgetError(f"{scope} {kind} cap reached before dispatch")
        counts[kind] += 1
        self._totals[kind] += 1

    def measured(self, library: int | None) -> dict[str, int]:
        return dict(self._counts[library])

    @property
    def totals(self) -> dict[str, int]:
        return dict(self._totals)

    def require_exact(self) -> None:
        if not IntegrityEvidence(measured_work=self._counts[None]).work_matches(self._caps[None]):
            raise BudgetError("measured shared-panel work differs from exact caps")
        for number in _LIBRARY_NUMBERS:
            if not IntegrityEvidence(measured_work=self._counts[number]).work_matches(
                self._caps[number]
            ):
                raise BudgetError(f"measured L{number} work differs from exact caps")
        if not IntegrityEvidence(measured_work=self._totals).work_matches(self._total_caps):
            raise BudgetError("measured total work differs from exact caps")


@dataclass(frozen=True)
class _ScopedCounter:
    ledger: WorkLedger
    library: int | None

    def dispatch(self, kind: str) -> None:
        self.ledger.reserve(self.library, kind)


def _verified_parent(
    root: Path, work_dir: Path, seed: int, counter: _ScopedCounter
) -> GeneratedNetworks:
    counter.dispatch("builds")
    parent = build_parent(root, "ci", seed, work_dir / "parents" / str(seed), write_m4=True)
    try:
        generated = parent.generated
        m2 = generated.m2_input.manifest
        m3 = generated.m3_input.manifest
        m4 = generated.config
        hashes = (m2.logical_content_hash, m3.logical_content_hash, generated.logical_content_hash)
        if hashes != frozen.PROCESS_HASHES[seed]:
            raise CampaignError(f"parent logical hash mismatch for {seed}")
        if any(stage.seed != seed or stage.mode != "ci" for stage in (m2, m3, m4)):
            raise CampaignError(f"parent seed or mode mismatch for {seed}")
    except (AttributeError, KeyError) as exc:
        raise CampaignError(f"parent metadata missing for {seed}") from exc
    return generated


def _adapter_for_seed(
    config: StudyConfig,
    root: Path,
    parameters: RespiratoryParameterSet,
    work_dir: Path,
    seed: int,
    counter: _ScopedCounter,
) -> tuple[_GenerationAdapter, dict[str, Any]]:
    # M5 consumes the loaded parent. Its build artifacts can be transient (§9).
    with TemporaryDirectory(dir=work_dir, prefix=".parent-") as scratch:
        with counter.ledger.time_phase(counter.library, "build"):
            parent = _verified_parent(root, Path(scratch), seed, counter)
        lineage = _parent_lineage(parent)
    counter.ledger.fallbacks[counter.library][seed] = {key: lineage[key] for key in _FALLBACK_KEYS}
    # The unchanged adapter uses only Phase-0 constructor fields and dispatch(kind).
    return _GenerationAdapter(
        cast(_AdapterConfig, config),
        root,
        parameters,
        {seed: parent},
        cast(_AdapterCounter, counter),
        counter.ledger.phase_seconds[counter.library],
        counter.ledger.latent_runtimes[counter.library],
    ), lineage


def _parent_lineage(parent: GeneratedNetworks) -> dict[str, Any]:
    m2, m3 = parent.m2_input, parent.m3_input
    diagnostics = [
        json.loads((stage.artifact_directory / "diagnostics.json").read_bytes())
        for stage in (m2, m3)
    ]
    if any(not isinstance(payload, dict) for payload in diagnostics):
        raise CampaignError("parent diagnostics must be objects")
    return {
        "m2": m2.manifest.logical_content_hash,
        "m3": m3.manifest.logical_content_hash,
        "m4": parent.logical_content_hash,
        "population_fallback_m2": _contains_key(
            diagnostics[0], "private_assignment_residual_fallback"
        ),
        "population_fallback_m3": _contains_key(
            diagnostics[1], "destination_reassignment_fallback"
        ),
    }


def _latent_for(
    adapter: _GenerationAdapter, seed: int, cell: CandidateCell
) -> tuple[OutbreakRunResult, OutbreakRunConfig]:
    latent, requested = adapter.latent_for(seed, cell)
    if not _fixed_run_provenance(latent, requested, seed, cell, frozen.LATENT_DAYS):
        raise CampaignError("latent metadata differs from the frozen run controls")
    try:
        population_size = latent.diagnostics["benchmark"]["n_agents"]
    except (AttributeError, KeyError, TypeError) as exc:
        raise CampaignError("latent result missing benchmark.n_agents metadata") from exc
    if type(population_size) is not int or population_size != _POPULATION_SIZE:
        raise CampaignError("latent population size differs from the frozen run controls")
    return latent, requested


def _observation_controls_match(
    config: ObservationConfig, seed: int, config_id: str, cell: CandidateCell
) -> bool:
    return (
        config.observation_seed == seed
        and config.observation_config_id == config_id
        and config.analysis_horizon_tail_days == _TAIL_DAYS
        and config.reporting_delay.kind == "fixed"
        and config.reporting_delay.days == (2,)
        and config.detection_delay.kind == "fixed"
        and config.detection_delay.days == (0,)
        and config.day_of_week_effect == (1.0,) * 7
        and config.parameters["symptomatic_detection_probability"].value
        == cell.symptomatic_detection_probability
        and config.parameters["asymptomatic_detection_probability"].value
        == cell.asymptomatic_detection_probability
    )


def _observe(
    adapter: _GenerationAdapter,
    latent: OutbreakRunResult,
    run: OutbreakRunConfig,
    seed: int,
    config_id: str,
    cell: CandidateCell,
) -> tuple[ObservationRunResult, ObservationConfig, ObservedTables]:
    try:
        result, requested, table = adapter.observe(latent, run, seed, config_id, cell)
        if not _observation_controls_match(result.config, seed, config_id, cell):
            raise CampaignError("observation metadata differs from the frozen controls")
    except (AttributeError, KeyError, TypeError) as exc:
        raise CampaignError("observation result missing metadata or events") from exc
    return result, requested, table


@dataclass(frozen=True)
class _TargetTable:
    path: Path
    sha256: str

    def read(self) -> tuple[ObservedTables, str]:
        content = self.path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if digest != self.sha256:
            raise CampaignError(f"shared target table SHA-256 mismatch for {self.path.name}")
        payload = json.loads(content)
        table = ObservedTables(
            tuple(payload["dates"]), tuple(payload["symptomatic"]), tuple(payload["asymptomatic"])
        )
        if table.dates != observation_dates(_START_DATE, frozen.LATENT_DAYS, _TAIL_DAYS):
            raise CampaignError("shared target table calendar differs from the frozen declaration")
        return table, digest


@dataclass(frozen=True)
class _TargetRun:
    table: _TargetTable
    latent: OutbreakRunResult
    observed: ObservationRunResult
    requested_run: OutbreakRunConfig
    requested_observation: ObservationConfig
    population_lineage: Mapping[str, Any]


def _result_provenance(
    row: frozen.FinalSeed,
    cell: CandidateCell,
    latent: OutbreakRunResult,
    observed: ObservationRunResult,
    requested_run: Mapping[str, Any],
    requested_observation: ObservationConfig,
    table_sha256: str,
    population_lineage: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "library": row.library,
        "batch": row.batch,
        "position": row.position,
        "process_seed": row.process,
        "observation_seed": row.observation,
        "cell": cell.as_dict(),
        "table_sha256": table_sha256,
        "population_lineage": population_lineage,
        "parent_network_seed": latent.generated.config.seed,
        "n_agents": latent.diagnostics["benchmark"]["n_agents"],
        "requested_run_config": requested_run,
        "returned_run_config": latent.config.model_dump(mode="json"),
        "requested_observation_config": requested_observation.model_dump(mode="json"),
        "returned_observation_config": observed.config.model_dump(mode="json"),
        "observation_rng": observed.diagnostics["observation_rng"],
    }


def _truth_cell() -> CandidateCell:
    beta, offset, sym, asym = (spec.truth for spec in _DIMENSIONS)
    return CandidateCell(beta, int(offset), sym, asym)


def _generate_targets(
    config: StudyConfig,
    work_dir: Path,
    root: Path,
    parameters: RespiratoryParameterSet,
    ledger: WorkLedger,
) -> dict[int, _TargetRun]:
    counter = _ScopedCounter(ledger, None)
    target_dir = work_dir / "targets"
    target_dir.mkdir()
    targets = {}
    truth = _truth_cell()
    for row in config.seeds:
        if row.library is not None:
            continue
        seed = row.process
        adapter, lineage = _adapter_for_seed(config, root, parameters, work_dir, seed, counter)
        latent, run = _latent_for(adapter, seed, truth)
        run_payload = run.model_dump(mode="json")
        observed, obs, table = _observe(
            adapter, latent, run, row.observation, config.target_observation_config_id, truth
        )
        if run.model_dump(mode="json") != run_payload:
            raise CampaignError("latent metadata changed during observation transforms")
        with ledger.time_phase(None, "retention"):
            content = _compact_json_bytes(table.as_dict())
            file = _TargetTable(target_dir / f"{seed}.json", hashlib.sha256(content).hexdigest())
            file.path.write_bytes(content)
        targets[seed] = _TargetRun(file, latent, observed, run, obs, lineage)
    return targets


@dataclass(frozen=True)
class _FitFile:
    fit: BlindFitResult
    sha256: str
    target_sha256: str

    def blind_record(self, seed: int) -> BlindRecord:
        return BlindRecord(
            seed,
            self.fit.estimate_hash,
            self.fit.selected,
            self.fit.profiles,
            self.fit.numerical_tie,
            len(self.fit.loss_surface),
        )


def _fit_path(directory: Path, name: str, seed: int) -> Path:
    if name == _GATE_FIT:
        return directory / "blind_estimates" / f"{seed}.json"
    return directory / "descriptive_estimates" / name / f"{seed}.json"


def _score_fit(
    target: ObservedTables,
    grid: tuple[CandidateCell, ...],
    predictions: Mapping[CandidateCell, Sequence[ObservedTables]],
    hashes: Mapping[CandidateCell, str],
    replicates: int,
    counter: _ScopedCounter,
    work_kind: str,
) -> BlindFitResult:
    def score(cell: CandidateCell) -> float:
        counter.dispatch(work_kind)
        return loss(target, predictions[cell], replicates, frozen.CALENDAR_DATES)

    fit = _fit_scored_grid(grid, predictions, score, hashes)
    if tuple((row.cell, row.config_hash) for row in fit.loss_surface) != tuple(
        (cell, hashes[cell]) for cell in grid
    ):
        raise CampaignError("blind loss surface grid or config provenance mismatch")
    return fit


def _fit_library(
    directory: Path,
    targets: Mapping[int, _TargetTable],
    grid: tuple[CandidateCell, ...],
    predictions: Mapping[CandidateCell, Sequence[ObservedTables]],
    configs: Mapping[CandidateCell, Sequence[Mapping[str, Any]]],
    counter: _ScopedCounter,
) -> dict[str, dict[int, _FitFile]]:
    fits = {}
    for name, positions in _FIT_SLICES.items():
        subset = {cell: tables[positions] for cell, tables in predictions.items()}
        hashes = {
            cell: hashlib.sha256(_compact_json_bytes(entries[positions])).hexdigest()
            for cell, entries in configs.items()
        }
        group = "gate" if name == _GATE_FIT else "descriptive"
        replicates = positions.stop - positions.start
        files = {}
        for seed, source in targets.items():
            target, target_sha256 = source.read()

            with counter.ledger.time_phase(counter.library, "scoring"):
                fit = _score_fit(
                    target, grid, subset, hashes, replicates, counter, f"{group}_loss_evaluations"
                )
            with counter.ledger.time_phase(counter.library, "retention"):
                counter.dispatch(f"{group}_blind_records")
                file_sha256 = _persist_fit(_fit_path(directory, name, seed), fit)
            files[seed] = _FitFile(fit, file_sha256, target_sha256)
        fits[name] = files
    return fits


def _generate_library(
    config: StudyConfig,
    root: Path,
    parameters: RespiratoryParameterSet,
    work_dir: Path,
    number: int,
    targets: Mapping[int, _TargetTable],
    ledger: WorkLedger,
) -> dict[str, dict[int, _FitFile]]:
    counter = _ScopedCounter(ledger, number)
    directory = work_dir / f"library_{number}"
    directory.mkdir()
    grid = config.candidate_grid
    cell_indexes = {cell: index for index, cell in enumerate(grid)}
    latent_cells = tuple(
        tuple(cells) for _, cells in groupby(grid, attrgetter("beta", "inoculation_day_offset"))
    )
    predictions: dict[CandidateCell, list[ObservedTables]] = {}
    configs: dict[CandidateCell, list[Mapping[str, Any]]] = {}
    for row in config.seeds:
        if row.library != number:
            continue
        adapter, lineage = _adapter_for_seed(
            config, root, parameters, directory, row.process, counter
        )
        for cells in latent_cells:
            latent, run = _latent_for(adapter, row.process, cells[0])
            run_payload = run.model_dump(mode="json")
            for cell in cells:
                if row.position == 1:
                    counter.dispatch("candidate_cells")
                    predictions[cell] = []
                    configs[cell] = []
                observed, requested, table = _observe(
                    adapter,
                    latent,
                    run,
                    row.observation,
                    config.candidate_observation_config_id,
                    cell,
                )
                predictions[cell].append(table)
                with ledger.time_phase(number, "retention"):
                    table_payload = table.as_dict()
                    record = _result_provenance(
                        row,
                        cell,
                        latent,
                        observed,
                        run_payload,
                        requested,
                        audit.table_sha256(table_payload),
                        lineage,
                    )
                    configs[cell].append(audit.candidate_binding(record))
                    _write_json(
                        directory
                        / "candidate_tables"
                        / str(cell_indexes[cell])
                        / f"{row.position:02d}.json",
                        {**record, "table": table_payload},
                    )
            if run.model_dump(mode="json") != run_payload:
                raise CampaignError("latent metadata changed during observation transforms")
    if any(len(tables) != _REPLICATES for tables in predictions.values()):
        raise CampaignError(f"L{number} candidate replicate roster is incomplete")
    return _fit_library(directory, targets, grid, predictions, configs, counter)


@dataclass(frozen=True)
class BlindGeneration:
    """In-process inputs for the post-blind phase and the shared table files."""

    config: StudyConfig
    directory: Path
    targets: Mapping[int, _TargetRun]
    libraries: Mapping[int, Mapping[str, Mapping[int, _FitFile]]]
    ledger: WorkLedger


def generate_blind(
    config_path: Path,
    predeclaration_path: Path,
    work_dir: Path,
    *,
    root: Path,
    ledger: WorkLedger | None = None,
) -> BlindGeneration:
    """Generate the shared panel and all six libraries and persist the blind fits."""
    config = StudyConfig.from_yaml(config_path)
    validate_predeclaration(predeclaration_path)
    plan_workload(config)
    if ledger is None:
        ledger = WorkLedger()
    if any(ledger.totals.values()):
        raise BudgetError("generation requires an unused work ledger")
    work_dir.mkdir(parents=True)
    return _generate_study(config, work_dir, root, ledger)


def _generate_study(
    config: StudyConfig, work_dir: Path, root: Path, ledger: WorkLedger
) -> BlindGeneration:
    parameters = load_parameter_set(root)
    targets = _generate_targets(config, work_dir, root, parameters, ledger)
    tables = {seed: output.table for seed, output in targets.items()}
    libraries = {
        number: _generate_library(config, root, parameters, work_dir, number, tables, ledger)
        for number in _LIBRARY_NUMBERS
    }
    ledger.require_exact()
    return BlindGeneration(config, work_dir, targets, libraries, ledger)


@dataclass(frozen=True)
class IntegrityEvidence:
    """Results of completion and provenance checks, plus the operational ledger."""

    execution_complete: bool = False
    provenance_verified: bool = False
    measured_work: Mapping[str, int] | None = None

    def work_matches(self, expected: Mapping[str, int]) -> bool:
        measured = self.measured_work
        return (
            measured is not None
            and all(type(count) is int for count in measured.values())
            and measured == expected
        )


_NO_INTEGRITY_EVIDENCE = IntegrityEvidence()


@dataclass(frozen=True)
class SharedPanelEvaluation:
    target_seeds: tuple[int, ...]
    predicates: Mapping[str, bool]
    target_conditions: Mapping[int, Mapping[str, bool]]

    @property
    def failed_conditions(self) -> dict[int, tuple[str, ...]]:
        return {
            seed: tuple(name for name, passed in conditions.items() if not passed)
            for seed, conditions in self.target_conditions.items()
            if not all(conditions.values())
        }


# §7.2 and §10 use the existing four flags individually. The grouped flags on
# TruthDiagnostics cannot substitute for missing source evidence.
_P3_CONDITIONS = (
    ("natural_history", "chronology_passed", "natural_history.chronology_passed"),
    ("latent_states", "conserved", "states.conserved"),
    (
        "observation_chronology_and_conservation",
        "no_report_before_infection",
        "no_report_before_infection",
    ),
    (
        "observation_chronology_and_conservation",
        "latent_incidence_conservation",
        "latent_incidence_conservation",
    ),
)
_INTEGRITY_PREDICATES = ("P1", "P9", "P10")
_NONRECOVERY_PREDICATES = ("P1", "P2", "P3", "P9", "P10")


def _target_conditions(diagnostics: TruthDiagnostics) -> tuple[dict[str, bool], dict[str, bool]]:
    p2 = {
        "inoculation_acquisitions": diagnostics.inoculation_acquisitions == _IMPORT_ATTEMPTS,
        "local_secondary_infections": diagnostics.local_secondary_infections >= 1,
        "symptomatic_reports": diagnostics.symptomatic_reports >= 1,
        "asymptomatic_reports": diagnostics.asymptomatic_reports >= 1,
        "nonzero_combined_report_dates": diagnostics.nonzero_combined_report_dates >= 3,
    }
    p3 = {}
    for section, key, name in _P3_CONDITIONS:
        source = diagnostics.raw_values.get(section)
        p3[name] = isinstance(source, Mapping) and source.get(key) is True
    return p2, p3


def evaluate_shared_panel(
    diagnostics: Mapping[int, TruthDiagnostics],
    *,
    evidence: IntegrityEvidence = _NO_INTEGRITY_EVIDENCE,
    expected_target_seeds: Sequence[int] = _TARGET_PROCESS_SEEDS,
    expected_work: Mapping[str, int] | None = None,
) -> SharedPanelEvaluation:
    """Evaluate shared predicates once. Historical evidence supplies its own roster and caps."""
    seeds = tuple(expected_target_seeds)
    if not seeds or len(set(seeds)) != len(seeds):
        raise CampaignError("expected target roster must be nonempty and unique")
    complete_roster = diagnostics.keys() == set(seeds)
    conditions = {
        seed: _target_conditions(diagnostics[seed]) for seed in seeds if seed in diagnostics
    }
    predicates = {
        "P1": complete_roster
        and evidence.execution_complete is True
        and all(row.complete is True for row in diagnostics.values()),
        "P2": complete_roster and all(all(p2.values()) for p2, _ in conditions.values()),
        "P3": complete_roster and all(all(p3.values()) for _, p3 in conditions.values()),
        "P9": complete_roster
        and evidence.provenance_verified is True
        and all(row.namespace_passed is True for row in diagnostics.values()),
        "P10": evidence.work_matches(
            _work_counts(frozen.SHARED_CAPS) if expected_work is None else expected_work
        ),
    }
    return SharedPanelEvaluation(
        seeds, predicates, {seed: {**p2, **p3} for seed, (p2, p3) in conditions.items()}
    )


@dataclass(frozen=True)
class BlindRecord:
    """Recovery inputs projected from a retained blind record after read-back."""

    target_seed: int
    estimate_hash: str
    selected: CandidateCell | None
    profiles: tuple[ProfileDiagnostic, ...]
    numerical_tie: bool
    scored_cell_count: int


@dataclass(frozen=True)
class TargetRecovery:
    target_seed: int
    selected: CandidateCell | None
    numerical_tie: bool
    signed_errors: Mapping[str, Decimal | None]
    identified: Mapping[str, bool]
    hits: Mapping[str, bool]
    boundary_flags: Mapping[str, bool]

    @property
    def joint_hit(self) -> bool:
        return all(self.hits.values())


@dataclass(frozen=True)
class RecoveryEvaluation:
    shared_panel: SharedPanelEvaluation
    library_integrity: Mapping[str, bool]
    recovery: Mapping[str, bool]
    hits: Mapping[str, int]
    joint_hits: int
    boundary_counts: Mapping[str, int]
    mean_bias: Mapping[str, Decimal | None]
    count_margins: tuple[int, ...]
    bias_margins: Mapping[str, str | None]
    tie_count: int
    rows: tuple[TargetRecovery, ...]

    @property
    def predicates(self) -> dict[str, bool]:
        return {
            **self.recovery,
            "P2": self.shared_panel.predicates["P2"],
            "P3": self.shared_panel.predicates["P3"],
            **{
                key: self.shared_panel.predicates[key] and self.library_integrity.get(key) is True
                for key in _INTEGRITY_PREDICATES
            },
        }

    @property
    def nonrecovery_ok(self) -> bool:
        return all(self.predicates[key] for key in _NONRECOVERY_PREDICATES)

    @property
    def recovery_met(self) -> bool:
        return all(self.recovery.values())

    @property
    def status(self) -> Literal["PASS", "FAIL"]:
        return "PASS" if self.nonrecovery_ok and self.recovery_met else "FAIL"

    @property
    def min_count_margin(self) -> int:
        return min(self.count_margins)

    @property
    def at_threshold(self) -> bool:
        return 0 in self.count_margins


def _target_recovery(row: BlindRecord) -> TargetRecovery:
    identified_names = {profile.dimension for profile in row.profiles if profile.identified is True}
    errors = {}
    identified = {}
    hits = {}
    boundaries = {}
    for spec in _DIMENSIONS:
        name = spec.name
        selected = None if row.selected is None else spec.exact_value(getattr(row.selected, name))
        error = None if selected is None else selected - spec.exact_truth()
        errors[name] = error
        identified[name] = not row.numerical_tie and name in identified_names
        hits[name] = identified[name] and error is not None and abs(error) <= spec.exact_tolerance()
        grid = spec.exact_candidates()
        boundaries[name] = selected in (grid[0], grid[-1])
    return TargetRecovery(
        row.target_seed, row.selected, row.numerical_tie, errors, identified, hits, boundaries
    )


def _mean_bias(rows: Sequence[TargetRecovery], dimension: str, n: int) -> Decimal | None:
    errors = [error for row in rows if (error := row.signed_errors[dimension]) is not None]
    if len(errors) != n:
        return None
    try:
        return sum(errors, Decimal(0)) / Decimal(n)
    except Inexact as exc:
        # §7.9 line 342 requires exact decimal reporting. Both declared panel sizes
        # (lines 150–160 and 728) have finite decimal means on the frozen grid.
        raise NotImplementedError("exact decimal reporting for a nonterminating mean bias") from exc


def evaluate_recovery(
    rows: Sequence[BlindRecord],
    *,
    shared_panel: SharedPanelEvaluation,
    evidence: IntegrityEvidence = _NO_INTEGRITY_EVIDENCE,
    expected_work: Mapping[str, int] | None = None,
) -> RecoveryEvaluation:
    """Compute the N-target gate from blind records and verified shared and library evidence."""
    seeds = shared_panel.target_seeds
    complete_roster = _complete_roster(rows, seeds)
    library_integrity = {
        "P1": complete_roster
        and evidence.execution_complete is True
        and all(
            type(row.scored_cell_count) is int and row.scored_cell_count == frozen.CELLS
            for row in rows
        ),
        "P9": complete_roster
        and evidence.provenance_verified is True
        and all(
            row.estimate_hash
            and len(row.profiles) == len(_DIMENSIONS)
            and {profile.dimension for profile in row.profiles}
            == {spec.name for spec in _DIMENSIONS}
            for row in rows
        ),
        "P10": evidence.work_matches(
            _work_counts(frozen.LIBRARY_CAPS) if expected_work is None else expected_work
        ),
    }
    return RecoveryEvaluation(
        shared_panel, library_integrity, **_recovery_metrics(rows, len(seeds), complete_roster)
    )


def _complete_roster(rows: Sequence[BlindRecord], expected: Sequence[int]) -> bool:
    return len(rows) == len(expected) and {row.target_seed for row in rows} == set(expected)


class _RecoveryMetrics(TypedDict):
    recovery: Mapping[str, bool]
    hits: Mapping[str, int]
    joint_hits: int
    boundary_counts: Mapping[str, int]
    mean_bias: Mapping[str, Decimal | None]
    count_margins: tuple[int, ...]
    bias_margins: Mapping[str, str | None]
    tie_count: int
    rows: tuple[TargetRecovery, ...]


def _recovery_metrics(
    rows: Sequence[BlindRecord], n: int, complete_roster: bool
) -> _RecoveryMetrics:
    """The identical exact P4–P8 computation for gates and ungated references."""

    # Exact arithmetic through the last comparison, independent of the caller's Decimal context.
    with localcontext(Context(traps=[Inexact])):
        target_rows = tuple(_target_recovery(row) for row in rows)
        hits = {spec.name: sum(row.hits[spec.name] for row in target_rows) for spec in _DIMENSIONS}
        joint = sum(row.joint_hit for row in target_rows)
        # §7.1 P8 has its own flags and counts, independent of P5.
        boundaries = {
            spec.name: sum(row.boundary_flags[spec.name] for row in target_rows)
            for spec in _DIMENSIONS
        }
        means = {
            spec.name: _mean_bias(target_rows, spec.name, n) if complete_roster else None
            for spec in _DIMENSIONS
        }
        bias_margins = {
            spec.name: None
            if (bias := means[spec.name]) is None
            else spec.exact_bias_limit() - abs(bias)
            for spec in _DIMENSIONS
        }
        tie_count = sum(row.numerical_tie for row in target_rows)
        recovery = {
            "P4": complete_roster and tie_count == 0,
            "P5": complete_roster and all(5 * count >= 4 * n for count in hits.values()),
            "P6": complete_roster and 5 * joint >= 3 * n,
            "P7": all(margin is not None and margin >= 0 for margin in bias_margins.values()),
            "P8": complete_roster and all(5 * count <= n for count in boundaries.values()),
        }
    count_margins = (
        *(count - (4 * n + 4) // 5 for count in hits.values()),
        joint - (3 * n + 4) // 5,
        *(n // 5 - count for count in boundaries.values()),
    )
    return {
        "recovery": recovery,
        "hits": hits,
        "joint_hits": joint,
        "boundary_counts": boundaries,
        "mean_bias": means,
        "count_margins": count_margins,
        "bias_margins": {
            name: None if margin is None else str(margin) for name, margin in bias_margins.items()
        },
        "tie_count": tie_count,
        "rows": target_rows,
    }


ReadingClass = Literal["CONSISTENT-PASS", "MIXED", "CONSISTENT-FAIL", "NO-READING"]


@dataclass(frozen=True)
class VoidCampaign:
    cause: str
    campaign_status: Literal["VOID"] = "VOID"


@dataclass(frozen=True)
class SharedPanelFailure:
    failed_conditions: Mapping[int, tuple[str, ...]]
    cause: Literal["shared_panel"] = "shared_panel"


@dataclass(frozen=True)
class IntactCampaign:
    reading_class: ReadingClass
    libraries: tuple[RecoveryEvaluation, ...]
    k: int
    k_prime: int
    cause: SharedPanelFailure | None = None

    @property
    def verdicts(self) -> tuple[Literal["PASS", "FAIL"], ...]:
        return tuple(library.status for library in self.libraries)


def classify_campaign(
    libraries: Sequence[RecoveryEvaluation],
    *,
    campaign_exception: bool = False,
    established_departure: bool = False,
) -> VoidCampaign | IntactCampaign:
    """Apply §7.3 precedence and clarification 1 before selecting any reading class."""
    if campaign_exception:
        return VoidCampaign("campaign_exception")
    if established_departure:
        return VoidCampaign("established_departure")
    if len(libraries) != frozen.LIBRARY_COUNT:
        return VoidCampaign("P1: incomplete library evaluations")

    panel = libraries[0].shared_panel
    if any(library.shared_panel != panel for library in libraries):
        return VoidCampaign("P9: inconsistent shared panel")
    failed_integrity = [
        f"shared panel {key}"
        for key in _INTEGRITY_PREDICATES
        if panel.predicates.get(key) is not True
    ]
    failed_integrity.extend(
        f"L{number} {key}"
        for number, library in enumerate(libraries, 1)
        for key in _INTEGRITY_PREDICATES
        if library.library_integrity.get(key) is not True
    )
    if failed_integrity:
        return VoidCampaign(", ".join(failed_integrity))

    k_prime = sum(library.recovery_met for library in libraries)
    k = sum(library.status == "PASS" for library in libraries)
    if not panel.predicates["P2"] or not panel.predicates["P3"]:
        return IntactCampaign(
            "NO-READING", tuple(libraries), k, k_prime, SharedPanelFailure(panel.failed_conditions)
        )
    reading_class: ReadingClass = "MIXED"
    if k == frozen.LIBRARY_COUNT:
        reading_class = "CONSISTENT-PASS"
    elif k == 0:
        reading_class = "CONSISTENT-FAIL"
    return IntactCampaign(reading_class, tuple(libraries), k, k_prime)


def _failed_library_predicates(number: int, library: RecoveryEvaluation) -> str:
    n = len(library.shared_panel.target_seeds)
    hits = ", ".join(f"{name}={count}/{n}" for name, count in library.hits.items())
    bias = ", ".join(
        f"{name}={'undefined' if value is None else value}"
        for name, value in library.mean_bias.items()
    )
    boundaries = ", ".join(f"{name}={count}/{n}" for name, count in library.boundary_counts.items())
    details = {
        "P4": f"{library.tie_count}/{n} ties",
        "P5": hits,
        "P6": f"{library.joint_hits}/{n} joint hits",
        "P7": bias,
        "P8": boundaries,
    }
    failures = [f"{key} ({details[key]})" for key, passed in library.recovery.items() if not passed]
    return f"L{number}: {', '.join(failures)}"


def reading(campaign: VoidCampaign | IntactCampaign) -> str | None:
    """Fill only the fields in the frozen §7.4 readings."""
    if isinstance(campaign, VoidCampaign):
        return None
    if campaign.cause is not None:
        conditions = "; ".join(
            f"{seed}: {', '.join(names)}"
            for seed, names in campaign.cause.failed_conditions.items()
        )
        return (
            "No reading on library dependence is issued. All six library gates are FAIL because "
            "a predicate that does not involve the candidate library failed on the shared panel "
            f"({conditions}), so this panel could not discriminate among candidate-library draws "
            "by gate outcome. The six per-library verdicts stand as computed and are not "
            "reclassified; no target is removed and the panel is not regenerated. Predicates 4–8 "
            f"were met by {campaign.k_prime} of six libraries; this is reported descriptively and "
            "licenses nothing."
        )
    if campaign.reading_class == "CONSISTENT-PASS":
        margin = min(library.min_count_margin for library in campaign.libraries)
        at_threshold = sum(library.at_threshold for library in campaign.libraries)
        return (
            "All six independently drawn R = 12 candidate libraries passed the frozen G35-B "
            "arm-(i) recovery gate on the same 20 shared synthetic targets. In six draws on this "
            "one target panel, the gate verdict was not observed to depend on which library was "
            "drawn. This is a count, not a pass rate, not a reliability finding and not an "
            "interval: six passes in six draws do not rule out that a substantial fraction of "
            "libraries, for example one in five or three in ten, would fail on this panel, and "
            "nothing is shown for any other target panel, scenario, grid, objective or level of R. "
            f"Smallest count margin across the six libraries: {margin} target(s); libraries with "
            f"at least one count exactly at its inclusive threshold: {at_threshold} of 6. "
            "This authorizes no real-data fitting. It is no more than input to a later gate "
            "decided by Steven."
        )
    failed = "; ".join(
        _failed_library_predicates(number, library)
        for number, library in enumerate(campaign.libraries, 1)
        if library.status == "FAIL"
    )
    if campaign.reading_class == "MIXED":
        margin = min(
            library.min_count_margin for library in campaign.libraries if library.status == "PASS"
        )
        k = campaign.k
        return (
            f"{k} of six independently drawn R = 12 candidate libraries passed the frozen G35-B "
            f"arm-(i) recovery gate and {frozen.LIBRARY_COUNT - k} failed it, on byte-identical "
            "targets. On this target panel the gate verdict depended on which candidate library "
            "was drawn. This is a direct observation, not a statistical inference. "
            "Four-dimensional recovery under this gate is therefore not shown to be a property of "
            f"the level R = 12 on this panel. The observed count is {k} of six. The library pass "
            "probability on this panel remains unknown. Failing libraries and their failed "
            "predicates: "
            f"{failed}. Smallest count margin among the passing libraries: {margin} target(s). "
            "The G35-B arm-(i) PASS remains a screening result only."
        )
    return (
        "None of six independently drawn R = 12 candidate libraries passed the frozen G35-B "
        "arm-(i) recovery gate on the same 20 shared synthetic targets, with every shared-panel "
        "and integrity predicate satisfied. In six draws on this one target panel, R = 12 did not "
        "produce four-dimensional recovery, and no dependence of the verdict on the library was "
        f"observed. Failed predicates per library: {failed}. "
        "None of these six libraries reproduced "
        "the G35-B recovery result. The campaigns differed in libraries, target draws and panel "
        "size. This comparison does not identify which difference mattered. Zero of six is a "
        "count, not a pass rate and not an interval, and it says nothing about other levels of R. "
        "The G35-B arm-(i) PASS remains a screening result only and its verdict is not changed."
    )


def reference_triggers(
    reading_class: ReadingClass | Literal["VOID"], *, k_prime: int, m: int
) -> tuple[bool, bool]:
    """Return S1 and S2 trigger values, in that order."""
    if reading_class in ("VOID", "NO-READING"):
        return False, False
    if not (type(k_prime) is int and 0 <= k_prime <= 6 and type(m) is int and 0 <= m <= 24):
        raise CampaignError("reference counts must be integers within their declared ranges")
    return m > 0 and 4 * k_prime <= m, m == 24


def reference_sentences(
    reading_class: ReadingClass | Literal["VOID"], *, k_prime: int, m: int
) -> tuple[str, ...]:
    s1, s2 = reference_triggers(reading_class, k_prime=k_prime, m=m)
    sentences = []
    if s1:
        sentences.append(
            "On this panel the six R = 12 libraries did not meet predicates 4–8 proportionally "
            "more often than their own twenty-four R = 3 batches "
            f"(R = 12: {k_prime} of 6; R = 3: {m} of 24)."
        )
    if s2:
        sentences.append(
            "Every R = 3 batch also met predicates 4–8 on this panel; R = 12 is not shown to be "
            "necessary here."
        )
    return tuple(sentences)


_DESCRIPTIVE = "descriptive_not_a_gate"


@dataclass(frozen=True)
class ReferenceEvaluation:
    replicates: int
    hits: Mapping[str, int]
    joint_hits: int
    boundary_counts: Mapping[str, int]
    mean_bias: Mapping[str, str | None]
    tie_count: int
    criteria_4_to_8_met: bool
    label: str = _DESCRIPTIVE


@dataclass(frozen=True)
class ReferenceSummary:
    libraries: Mapping[int, Mapping[str, ReferenceEvaluation]]
    k_prime: int
    m: int
    m_by_library: Mapping[int, int]
    libraries_not_met_with_a_batch_met: int
    s1: bool
    s2: bool
    sentences: tuple[str, ...]
    label: str = _DESCRIPTIVE


def _decimal_strings(values: Mapping[str, Decimal | None]) -> dict[str, str | None]:
    return {name: None if value is None else str(value) for name, value in values.items()}


def _reference_evaluation(rows: Sequence[BlindRecord], replicates: int) -> ReferenceEvaluation:
    metrics = _recovery_metrics(
        rows, frozen.TARGET_COUNT, _complete_roster(rows, _TARGET_PROCESS_SEEDS)
    )
    return ReferenceEvaluation(
        replicates,
        metrics["hits"],
        metrics["joint_hits"],
        metrics["boundary_counts"],
        _decimal_strings(metrics["mean_bias"]),
        metrics["tie_count"],
        all(metrics["recovery"].values()),
    )


def _summarize_references(
    campaign: IntactCampaign, references: Mapping[int, Mapping[str, ReferenceEvaluation]]
) -> ReferenceSummary:
    m_by_library = {
        number: sum(references[number][batch].criteria_4_to_8_met for batch in _BATCH_SLICES)
        for number in _LIBRARY_NUMBERS
    }
    m = sum(m_by_library.values())
    k_prime = campaign.k_prime
    missed_with_a_batch_met = sum(
        not library.recovery_met and m_by_library[number] > 0
        for number, library in zip(_LIBRARY_NUMBERS, campaign.libraries, strict=True)
    )
    s1, s2 = reference_triggers(campaign.reading_class, k_prime=k_prime, m=m)
    return ReferenceSummary(
        references,
        k_prime,
        m,
        m_by_library,
        missed_with_a_batch_met,
        s1,
        s2,
        reference_sentences(campaign.reading_class, k_prime=k_prime, m=m),
    )


def _predicate_descriptive(evaluation: RecoveryEvaluation) -> dict[str, Any]:
    return {
        "label": _DESCRIPTIVE,
        "predicates": evaluation.predicates,
        "hits": evaluation.hits,
        "joint_hits": evaluation.joint_hits,
        "boundary_counts": evaluation.boundary_counts,
        "mean_bias": _decimal_strings(evaluation.mean_bias),
        "count_margins": evaluation.count_margins,
        "min_count_margin": evaluation.min_count_margin,
        "at_threshold": evaluation.at_threshold,
        "bias_margins": evaluation.bias_margins,
    }


def _matrix_descriptives(
    libraries: Sequence[RecoveryEvaluation],
    fits: Mapping[int, Mapping[str, Mapping[int, _FitFile]]],
) -> dict[str, Any]:
    matrix = []
    summaries = []
    for rows in zip(*(library.rows for library in libraries), strict=True):
        seed = rows[0].target_seed
        offsets = tuple(
            _offset_descriptive(fits[number][_GATE_FIT][seed].fit)["reprofiled_offset"]
            for number in _LIBRARY_NUMBERS
        )
        matrix.append(
            tuple(
                {
                    "label": _DESCRIPTIVE,
                    "selected": None if row.selected is None else row.selected.as_dict(),
                    "joint_hit": row.joint_hit,
                    "hits": row.hits,
                    "identified": row.identified,
                    "boundary_flags": row.boundary_flags,
                    "numerical_tie": row.numerical_tie,
                    "reprofiled_offset": offset,
                }
                for row, offset in zip(rows, offsets, strict=True)
            )
        )
        summaries.append(
            {
                "label": _DESCRIPTIVE,
                "target_seed": seed,
                "joint_hits": sum(row.joint_hit for row in rows),
                "offset_hits": sum(row.hits["inoculation_day_offset"] for row in rows),
                "distinct_selected_offsets": len(
                    {
                        row.selected.inoculation_day_offset
                        for row in rows
                        if row.selected is not None
                    }
                ),
                "all_six_offsets_agree": None not in offsets and len(set(offsets)) == 1,
            }
        )
    return {
        "label": _DESCRIPTIVE,
        "target_seeds": _TARGET_PROCESS_SEEDS,
        "library_numbers": _LIBRARY_NUMBERS,
        "matrix": matrix,
        "row_summaries": summaries,
    }


def _batch_descriptives(files: Mapping[str, Mapping[int, _FitFile]]) -> dict[str, Any]:
    targets = []
    for seed in files[_GATE_FIT]:
        fits = {name: records[seed].fit for name, records in files.items()}
        batches = tuple(fits[name] for name in _BATCH_SLICES)
        targets.append(
            {
                "label": STOCHASTIC_REPLICATE_VARIATION,
                "target_seed": seed,
                "four_batch_offsets_agree": batch_offset_agreement(batches),
                "reprofiled_offsets": {
                    name: {"label": _DESCRIPTIVE, **_offset_descriptive(fit)}
                    for name, fit in fits.items()
                },
                "fixed_tuple_spreads": [
                    {
                        "cell": rows[0].cell.as_dict(),
                        **batch_objective_spread([row.objective for row in rows]),
                    }
                    for rows in zip(*(batch.loss_surface for batch in batches), strict=True)
                ],
            }
        )
    return {
        "label": STOCHASTIC_REPLICATE_VARIATION,
        "four_batch_offset_agreement_count": sum(
            row["four_batch_offsets_agree"] for row in targets
        ),
        "targets": targets,
    }


def _read_back_all(generation: BlindGeneration) -> dict[int, ObservedTables]:
    """Check the complete frozen roster and independently re-read every file (§6)."""
    generation.ledger.require_exact()
    if tuple(generation.targets) != _TARGET_PROCESS_SEEDS:
        raise CampaignError("shared target roster differs from the frozen declaration")
    tables = {}
    target_hashes = {}
    for seed, target in generation.targets.items():
        if target.table.path != generation.directory / "targets" / f"{seed}.json":
            raise CampaignError("shared target table path differs from its declared position")
        with generation.ledger.time_phase(None, "retention"):
            tables[seed], target_hashes[seed] = target.table.read()

    if tuple(generation.libraries) != _LIBRARY_NUMBERS:
        raise CampaignError("blind library roster differs from the frozen declaration")
    for number, fits in generation.libraries.items():
        if fits.keys() != _FIT_SLICES.keys():
            raise CampaignError(f"L{number} blind fit roster is incomplete")
        directory = generation.directory / f"library_{number}"
        for name, records in fits.items():
            if tuple(records) != _TARGET_PROCESS_SEEDS:
                raise CampaignError(f"L{number} {name} blind target roster is incomplete")
            for seed, record in records.items():
                if record.target_sha256 != target_hashes[seed]:
                    raise CampaignError(f"L{number} {name} used different target table bytes")
                with generation.ledger.time_phase(number, "retention"):
                    _verify_blind_readback(
                        _fit_path(directory, name, seed), record.fit, record.sha256
                    )
    return tables


def _library_evidence(
    generation: BlindGeneration, number: int, fits: Mapping[str, Mapping[int, _FitFile]]
) -> IntegrityEvidence:
    grid = StudyConfig().candidate_grid
    roster = [
        (
            number,
            row.batch,
            row.position,
            row.process,
            row.observation,
            frozen.PROCESS_HASHES[row.process],
        )
        for row in frozen.FINAL_SEEDS
        if row.library == number and row.batch is not None
    ]
    directory = generation.directory / f"library_{number}"
    dates = observation_dates(_START_DATE, frozen.LATENT_DAYS, _TAIL_DAYS)
    with generation.ledger.time_phase(number, "retention"):
        complete, provenance, records = audit.read_candidate_library(
            directory, [cell.as_dict() for cell in grid], roster, dates
        )
    complete &= all(
        len(record.fit.loss_surface) == frozen.CELLS
        for view in fits.values()
        for record in view.values()
    )
    if provenance:
        bindings = [[audit.candidate_binding(record) for record in rows] for rows in records]
        for name, positions in _FIT_SLICES.items():
            expected = tuple(
                (cell, audit.binding_hash(rows[positions]))
                for cell, rows in zip(grid, bindings, strict=True)
            )
            provenance &= all(
                tuple((row.cell, row.config_hash) for row in record.fit.loss_surface) == expected
                for record in fits[name].values()
            )
    return IntegrityEvidence(complete, provenance, generation.ledger.measured(number))


@dataclass(frozen=True)
class StudyEvaluation:
    campaign: IntactCampaign
    truth_diagnostics: Mapping[int, TruthDiagnostics]
    predicate_descriptives: Mapping[int, Mapping[str, Any]]
    matrix_descriptives: Mapping[str, Any]
    batch_descriptives: Mapping[int, Mapping[str, Any]]
    references: ReferenceSummary


def evaluate_after_blind(generation: BlindGeneration) -> StudyEvaluation | VoidCampaign:
    """Complete the global read-back barrier before accessing any target truth."""
    plan_workload(generation.config)
    tables = _read_back_all(generation)
    diagnostics = {}
    target_pairs = {
        row.process: row.observation for row in frozen.FINAL_SEEDS if row.library is None
    }
    truth = _truth_cell()
    dates = observation_dates(_START_DATE, frozen.LATENT_DAYS, _TAIL_DAYS)
    provenance_verified = True
    for seed, target in generation.targets.items():
        namespace_passed = _namespace_passes(
            target.latent, target.observed, target.requested_run, target.requested_observation
        )
        provenance_verified &= (
            namespace_passed
            and _fixed_run_provenance(
                target.latent, target.requested_run, seed, truth, frozen.LATENT_DAYS
            )
            and _observation_controls_match(
                target.observed.config, target_pairs[seed], _TARGET_CONFIG_ID, truth
            )
            and tuple(target.population_lineage[key] for key in ("m2", "m3", "m4"))
            == frozen.PROCESS_HASHES[seed]
            and type(target.latent.diagnostics["benchmark"]["n_agents"]) is int
            and target.latent.diagnostics["benchmark"]["n_agents"] == _POPULATION_SIZE
        )
        returned = _truth_diagnostics_from_result(
            target.latent, target.observed, tables[seed], namespace_passed=namespace_passed
        )
        latent_days = getattr(target.latent, "daily_epidemic", None)
        observed_days = getattr(target.observed, "daily_observed_cases", None)
        complete = (
            isinstance(latent_days, list)
            and len(latent_days) == frozen.LATENT_DAYS
            and getattr(getattr(target.latent, "config", None), "duration_days", None)
            == frozen.LATENT_DAYS
            and tables[seed].dates == dates
            and isinstance(observed_days, list)
            and tuple(row.get("date") for row in observed_days) == dates
        )
        diagnostics[seed] = replace(returned, complete=complete)

    panel = evaluate_shared_panel(
        diagnostics,
        evidence=IntegrityEvidence(
            all(row.complete for row in diagnostics.values()),
            provenance_verified,
            generation.ledger.measured(None),
        ),
    )
    evaluations = {
        number: evaluate_recovery(
            tuple(record.blind_record(seed) for seed, record in fits[_GATE_FIT].items()),
            shared_panel=panel,
            evidence=_library_evidence(generation, number, fits),
        )
        for number, fits in generation.libraries.items()
    }
    campaign = classify_campaign(tuple(evaluations.values()))
    if isinstance(campaign, VoidCampaign):
        return campaign

    references = {
        number: {
            name: _reference_evaluation(
                tuple(record.blind_record(seed) for seed, record in fits[name].items()),
                positions.stop - positions.start,
            )
            for name, positions in _REFERENCE_SLICES.items()
        }
        for number, fits in generation.libraries.items()
    }
    return StudyEvaluation(
        campaign,
        diagnostics,
        {number: _predicate_descriptive(value) for number, value in evaluations.items()},
        _matrix_descriptives(campaign.libraries, generation.libraries),
        {number: _batch_descriptives(fits) for number, fits in generation.libraries.items()},
        _summarize_references(campaign, references),
    )


_STATUS_PREFIX = (
    "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); "
    "G35-B: B FAIL, i PASS, ii FAIL, iii FAIL"
)


def status_phrase(
    campaign: VoidCampaign | IntactCampaign | None = None, *, declaration_frozen: bool = True
) -> str:
    """Return §7.11's phrase. State files own the pending-audit annotation."""
    if campaign is None:
        return _STATUS_PREFIX + ("; G43: not run" if declaration_frozen else "")
    if isinstance(campaign, VoidCampaign):
        return _STATUS_PREFIX + "; G43: VOID"
    return (
        _STATUS_PREFIX
        + "; G43: "
        + ", ".join(f"L{number} {verdict}" for number, verdict in enumerate(campaign.verdicts, 1))
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_compact_json_bytes(value))


def _target_raw_truth(target: _TargetRun) -> dict[str, Any]:
    latent, observed = target.latent, target.observed
    return {
        "transmission_events": latent.transmission_events,
        "daily_epidemic": latent.daily_epidemic,
        "natural_history": latent.diagnostics["natural_history"],
        "states": latent.diagnostics["states"],
        "observation_events": observed.observation_events,
        "daily_observed_cases": observed.daily_observed_cases,
        "benchmark": {"n_agents": latent.diagnostics["benchmark"]["n_agents"]},
        "observation_diagnostics": {
            key: observed.diagnostics[key]
            for key in (
                "no_report_before_infection",
                "chronology_violations",
                "latent_incidence_conservation",
                "latent_incidence_conservation_difference",
            )
            if key in observed.diagnostics
        },
    }


_P3_SOURCE_NOTES = {
    "natural_history.chronology_passed": {
        "raw_rows": ["transmission_events"],
        "source": "src/jersey_outbreak/outbreak_runner.py:513–524",
    },
    "states.conserved": {
        "raw_rows": ["daily_epidemic", "benchmark.n_agents"],
        "source": "src/jersey_outbreak/outbreak_runner.py:453–456,488",
    },
    "no_report_before_infection": {
        "raw_rows": ["observation_events"],
        "source": "src/jersey_outbreak/observation.py:277–309,326",
    },
    "latent_incidence_conservation": {
        "raw_rows": ["daily_observed_cases", "observation_events"],
        "source": "src/jersey_outbreak/observation.py:306–308,328–329",
    },
}


def _retain_targets(generation: BlindGeneration, evaluation: StudyEvaluation | None) -> None:
    directory = generation.directory / "targets"
    provenance = []
    diagnostics = {}
    for row in frozen.FINAL_SEEDS:
        if row.library is not None:
            continue
        target = generation.targets[row.process]
        provenance.append(
            _result_provenance(
                row,
                _truth_cell(),
                target.latent,
                target.observed,
                target.requested_run.model_dump(mode="json"),
                target.requested_observation,
                target.table.sha256,
                target.population_lineage,
            )
        )
        _write_json(directory / "latent_truth" / f"{row.process}.json", _target_raw_truth(target))
        if evaluation is not None:
            returned = evaluation.truth_diagnostics[row.process]
            p2, p3 = _target_conditions(returned)
            diagnostics[row.process] = {**returned.as_dict(), "conditions": {**p2, **p3}}
    _write_json(directory / "target_provenance.json", provenance)
    if evaluation is not None:
        _write_json(directory / "truth_diagnostics.json", diagnostics)
    _write_json(
        directory / "auditor_recompute_notes.json",
        {
            "recomputable": {
                "P2": {
                    "inoculation_acquisitions": ["transmission_events.imported"],
                    "local_secondary_infections": ["transmission_events.source_kind"],
                    "symptomatic_reports": [
                        "observation_events.report_date",
                        "observation_events.symptomatic",
                    ],
                    "asymptomatic_reports": [
                        "observation_events.report_date",
                        "observation_events.symptomatic",
                    ],
                    "nonzero_combined_report_dates": ["observation_events.report_date"],
                    "source": "src/jersey_outbreak/phase0_campaign.py:2333–2362",
                },
                "P3": _P3_SOURCE_NOTES,
            },
            "internally_checkable_only": {
                "P2": [],
                "P3": [],
                "reported_flags": (
                    "Retained diagnostics in each latent_truth JSON and truth_diagnostics.json "
                    "permit comparison with the independently recomputed flags."
                ),
            },
        },
    )


def _write_recovery_csv(
    path: Path, library: RecoveryEvaluation, targets: Mapping[int, _TargetRun]
) -> None:
    rows = []
    for row in library.rows:
        lineage = targets[row.target_seed].population_lineage
        rows.append(
            {
                "target_seed": row.target_seed,
                "numerical_tie": row.numerical_tie,
                "joint_hit": row.joint_hit,
                **library.shared_panel.target_conditions[row.target_seed],
                **{f"predicate_{key}": value for key, value in library.predicates.items()},
                **{
                    f"{name}_{key}": values.get(key)
                    for name, values in (
                        ("selected", {} if row.selected is None else row.selected.as_dict()),
                        ("signed_error", row.signed_errors),
                        ("identified", row.identified),
                        ("hit", row.hits),
                        ("boundary", row.boundary_flags),
                    )
                    for key in _DIMENSIONS_NAMES
                },
                **{key: lineage[key] for key in _FALLBACK_KEYS},
            }
        )
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


_DIMENSIONS_NAMES = tuple(spec.name for spec in _DIMENSIONS)
_FALLBACK_KEYS = ("population_fallback_m2", "population_fallback_m3")


def _retain_blind_indexes(generation: BlindGeneration) -> None:
    for number, views in generation.libraries.items():
        directory = generation.directory / f"library_{number}"
        with generation.ledger.time_phase(number, "retention"):
            _write_json(
                directory / "blind_readback_hashes.json",
                [
                    {
                        "view": view,
                        "target_seed": seed,
                        "path": _fit_path(directory, view, seed).relative_to(directory).as_posix(),
                        "sha256": record.sha256,
                        "estimate_hash": record.fit.estimate_hash,
                        "target_sha256": record.target_sha256,
                    }
                    for view, files in views.items()
                    for seed, record in files.items()
                ],
            )


def _retain_scientific_outputs(
    generation: BlindGeneration, evaluation: StudyEvaluation, across: Mapping[str, Any]
) -> None:
    for number, library in enumerate(evaluation.campaign.libraries, 1):
        directory = generation.directory / f"library_{number}"
        with generation.ledger.time_phase(number, "retention"):
            _write_recovery_csv(
                directory / f"g43_L{number}_recovery.csv", library, generation.targets
            )
            _write_json(
                directory / "recovery_evaluation.json",
                {
                    **evaluation.predicate_descriptives[number],
                    "groups": {
                        "shared_panel": library.shared_panel.predicates,
                        "library_integrity": library.library_integrity,
                        "recovery": library.recovery,
                    },
                    "nonrecovery_ok": library.nonrecovery_ok,
                    "recovery_met": library.recovery_met,
                    "tie_count": library.tie_count,
                    "scientific_status": library.status,
                },
            )
            _write_json(
                directory / f"g43_L{number}_descriptives.json",
                evaluation.batch_descriptives[number],
            )
            _write_json(
                directory / "reference_evaluations.json",
                {
                    "label": _DESCRIPTIVE,
                    "m_library": evaluation.references.m_by_library[number],
                    "evaluations": {
                        name: asdict(record)
                        for name, record in evaluation.references.libraries[number].items()
                    },
                },
            )
    _write_json(generation.directory / "g43_matrices.json", evaluation.matrix_descriptives)
    _write_json(generation.directory / "g43_across_library.json", across)


def _across_library(evaluation: StudyEvaluation) -> dict[str, Any]:
    campaign, references = evaluation.campaign, evaluation.references
    return {
        "verdicts": dict(zip(_LIBRARY_NUMBERS, campaign.verdicts, strict=True)),
        "k": campaign.k,
        "k_prime": campaign.k_prime,
        "m": references.m,
        "m_by_library": references.m_by_library,
        "libraries_not_met_with_a_batch_met": references.libraries_not_met_with_a_batch_met,
        "s1": references.s1,
        "s2": references.s2,
        "class": campaign.reading_class,
        "reading": reading(campaign),
        **({} if campaign.cause is None else {"cause": asdict(campaign.cause)}),
    }


def _seed_ledger() -> list[dict[str, Any]]:
    return [
        {
            "role": "target" if row.library is None else "candidate",
            "library": row.library,
            "batch": row.batch,
            "position": row.position,
            "process_seed": row.process,
            "observation_seed": row.observation,
            "observation_config_id": _TARGET_CONFIG_ID if row.library is None else _FIT_CONFIG_ID,
            "replaces_process_seed": frozen.REPLACEMENTS.get(row.process),
        }
        for row in frozen.FINAL_SEEDS
    ]


def _source_snapshot(root: Path) -> dict[str, Any]:
    _require_clean_worktree(root)
    git = ["git", "-C", str(root)]
    head = subprocess.check_output([*git, "rev-parse", "HEAD"]).decode().strip()
    tracked = (
        subprocess.check_output(
            [
                *git,
                "ls-tree",
                "-rz",
                "--name-only",
                head,
                "--",
                "src/jersey_outbreak",
                "configs",
            ]
        )
        .decode()
        .split("\0")
    )
    return {
        "git_head": head,
        "worktree_clean": True,
        "source_and_config_sha256": {
            name: hashlib.sha256(
                subprocess.check_output([*git, "show", f"{head}:{name}"])
            ).hexdigest()
            for name in tracked
            if Path(name).suffix in (".py", ".yaml", ".json")
        },
    }


def _execution_inputs(
    root: Path, config: Path, predeclaration: Path, owner: Path | None, clarification: Path | None
) -> dict[str, bytes]:
    documents = (
        (config, frozen.CONFIG_PATH, frozen.CONFIG_SHA256, "HEAD"),
        (
            predeclaration,
            frozen.PREDECLARATION_PATH,
            frozen.PREDECLARATION_SHA256,
            frozen.PREDECLARATION_COMMIT,
        ),
        (
            owner or root / frozen.OWNER_RULING_PATH,
            frozen.OWNER_RULING_PATH,
            frozen.OWNER_RULING_SHA256,
            "HEAD",
        ),
        (
            clarification or root / frozen.CLARIFICATION_PATH,
            frozen.CLARIFICATION_PATH,
            frozen.CLARIFICATION_SHA256,
            "HEAD",
        ),
        (root / frozen.PRECHECK_PATH, frozen.PRECHECK_PATH, frozen.PRECHECK_SHA256, "HEAD"),
    )
    inputs = {}
    for path, logical, expected, commit in documents:
        if path.is_symlink() or path.resolve() != (root / logical).resolve():
            raise CampaignError(f"frozen input must be the declared repository file: {path}")
        content = committed_document_bytes(path, commit=commit)
        if path.read_bytes() != content or hashlib.sha256(content).hexdigest() != expected:
            raise CampaignError(f"frozen input LF bytes or committed SHA-256 mismatch: {path}")
        inputs[Path(logical).name] = content
    return inputs


def _exit_marker_path(output_dir: Path, exit_marker: Path | None) -> Path:
    return exit_marker or output_dir.parent / "jos-g43-campaign.exit"


def _launch_checks(
    output_dir: Path, root: Path, exit_marker: Path | None, bundle_upper_bytes: int | None
) -> dict[str, Any]:
    marker = _exit_marker_path(output_dir, exit_marker)
    if marker.exists() or marker.is_symlink():
        raise CampaignError(f"campaign exit marker already exists: {marker}")
    if output_dir.is_symlink() or output_dir.resolve().is_relative_to(root.resolve()):
        raise CampaignError("campaign output must be a fresh directory outside the repository")
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise CampaignError("campaign output directory must be empty")
    if marker.resolve().is_relative_to(output_dir.resolve()):
        raise CampaignError("campaign exit marker must be outside the bundle directory")
    if not marker.parent.is_dir() or not os.access(marker.parent, os.W_OK | os.X_OK):
        raise CampaignError(
            f"campaign exit marker parent must be an existing writable directory: {marker.parent}"
        )
    default_upper = frozen.EXPLORATORY_BUNDLE_UPPER_BYTES + frozen.PARENT_BUILD_DISK_BYTES
    upper = default_upper if bundle_upper_bytes is None else bundle_upper_bytes
    if type(upper) is not int or upper < 0:
        raise CampaignError("bundle upper estimate must be a nonnegative integer of bytes")
    if upper < default_upper:
        raise CampaignError(f"bundle upper estimate must be at least {default_upper} bytes")
    host = Path("/mnt/c")
    free = shutil.disk_usage(host).free
    required = frozen.HOST_HEADROOM_BYTES + upper
    if free < required:
        raise CampaignError(
            f"host free space {free} bytes at {host} is below required {required} bytes"
        )
    return {
        "host_path": str(host),
        "host_free_bytes_before_launch": free,
        "required_free_bytes": required,
        "parent_build_disk_bytes": frozen.PARENT_BUILD_DISK_BYTES,
        "parent_builds_on_disk_at_once": 1,
        "exploratory_upper_bytes": frozen.EXPLORATORY_BUNDLE_UPPER_BYTES,
        "default_upper_bytes": default_upper,
        "upper_override_bytes": bundle_upper_bytes,
        "upper_bytes_used": upper,
    }


def _measured_work(ledger: WorkLedger, plan: Mapping[str, Any]) -> dict[str, Any]:
    def comparison(planned: Mapping[str, int], measured: Mapping[str, int]) -> dict[str, Any]:
        return {
            "planned": planned,
            "measured": measured,
            "measured_equals_planned": IntegrityEvidence(measured_work=measured).work_matches(
                planned
            ),
        }

    return {
        "shared_panel": comparison(plan["shared_panel"], ledger.measured(None)),
        "libraries": {
            f"L{number}": comparison(plan["libraries"][f"L{number}"], ledger.measured(number))
            for number in _LIBRARY_NUMBERS
        },
        "totals": comparison(plan["totals"], ledger.totals),
    }


def _write_summary(directory: Path, summary: dict[str, Any]) -> None:
    # Include the summary and manifest themselves in the exact logical byte size.
    path = directory / "campaign_summary.json"
    other_files = [
        file
        for file in directory.rglob("*")
        if file.is_file() and file not in (path, directory / audit.SHA256SUMS)
    ]
    manifest_size = sum(
        67 + len(file.relative_to(directory).as_posix().encode()) for file in [*other_files, path]
    )
    fixed_size = sum(file.stat().st_size for file in other_files) + manifest_size
    disk = summary["disclosures"]["disk"]
    disk["bundle_size_bytes"] = 0
    while True:
        content = _compact_json_bytes(summary)
        size = fixed_size + len(content)
        if size == disk["bundle_size_bytes"]:
            path.write_bytes(content)
            return
        disk["bundle_size_bytes"] = size


def verify_bundle(output_dir: Path) -> None:
    """Check exact manifest bytes, file hashes, coverage and all write bits."""
    try:
        audit.verify_bundle(output_dir)
    except (audit.BundleError, OSError) as exc:
        raise CampaignError(str(exc)) from exc


def _seal_bundle(output_dir: Path) -> None:
    (output_dir / audit.SHA256SUMS).write_bytes(audit._manifest(output_dir, check_modes=False))
    for path in [*output_dir.rglob("*"), output_dir]:
        path.chmod(path.stat().st_mode & ~0o222)
    verify_bundle(output_dir)


def _discard_scientific_outputs(output_dir: Path) -> None:
    # Clarification 1: keep underlying evidence on VOID.
    output_dir.chmod(output_dir.stat().st_mode | 0o200)
    (output_dir / audit.SHA256SUMS).unlink(missing_ok=True)
    for path in output_dir.rglob("*"):
        if not path.is_symlink():
            path.chmod(path.stat().st_mode | 0o200)
    for name in ("g43_across_library.json", "g43_matrices.json"):
        (output_dir / name).unlink(missing_ok=True)
    for number in _LIBRARY_NUMBERS:
        directory = output_dir / f"library_{number}"
        for name in (
            f"g43_L{number}_recovery.csv",
            "recovery_evaluation.json",
            f"g43_L{number}_descriptives.json",
            "reference_evaluations.json",
        ):
            (directory / name).unlink(missing_ok=True)


def _disclosures(
    ledger: WorkLedger,
    disk: Mapping[str, Any],
    started: float,
) -> dict[str, Any]:
    def scope(number: int | None) -> dict[str, Any]:
        lineage = ledger.fallbacks[number]
        return {
            "label": _DESCRIPTIVE,
            "wall_time_seconds": ledger.phase_seconds[number],
            "latent_call_runtimes": ledger.latent_runtimes[number],
            "population_fallbacks": {
                "by_process_seed": lineage,
                "fallback_built_count": sum(any(flags.values()) for flags in lineage.values()),
            },
        }

    return {
        "label": _DESCRIPTIVE,
        "campaign_wall_time_seconds": time.perf_counter() - started,
        "shared_panel": scope(None),
        "libraries": {f"L{number}": scope(number) for number in _LIBRARY_NUMBERS},
        "disk": dict(disk),
    }


_DEFAULT_SEATS = {
    "implementer": "gpt-6.2-sol @ high",
    "reviewer": "Claude Opus 5.5 @ high",
    "substitutions": "not applicable",
}


def execute(
    config_path: Path,
    predeclaration_path: Path,
    output_dir: Path,
    *,
    root: Path,
    owner_ruling_path: Path | None = None,
    clarification_path: Path | None = None,
    exit_marker: Path | None = None,
    bundle_upper_bytes: int | None = None,
    seats: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run and seal one campaign after its §12 launch preconditions."""
    # Verify all read-only launch inputs before starting campaign work.
    disk = _launch_checks(output_dir, root, exit_marker, bundle_upper_bytes)
    marker = _exit_marker_path(output_dir, exit_marker)
    config = StudyConfig.from_yaml(config_path)
    validate_predeclaration(predeclaration_path)
    plan = plan_workload(config)
    inputs = _execution_inputs(
        root, config_path, predeclaration_path, owner_ruling_path, clarification_path
    )
    snapshot = _source_snapshot(root)
    if seats is not None and not isinstance(seats, Mapping):
        raise CampaignError("seats must be an object")
    seats = dict(_DEFAULT_SEATS if seats is None else seats)
    if (
        seats.keys() != _DEFAULT_SEATS.keys()
        or any(
            not isinstance(seats[key], str) or not seats[key] for key in ("implementer", "reviewer")
        )
        or not seats["substitutions"]
    ):
        raise CampaignError("seats require an implementer, reviewer and substitution record")
    declaration = inputs[Path(frozen.PREDECLARATION_PATH).name].decode()
    lineage = declaration[
        declaration.index("**Lineage block**") : declaration.index("## 2.")
    ].rstrip("\n")
    frozen_inputs = output_dir / "frozen_inputs"
    started = time.perf_counter()
    summary: dict[str, Any] = {}

    def finish(campaign: IntactCampaign | VoidCampaign, scientific: Mapping[str, Any]) -> None:
        summary.clear()
        summary.update(
            {
                "lineage": {"frozen_section_1": lineage, "reviewer": seats["reviewer"]},
                "seats": seats,
                "software_status": "VOID" if isinstance(campaign, VoidCampaign) else "PASS",
                **scientific,
                "status_phrase": status_phrase(campaign),
                "measured_work": _measured_work(ledger, plan),
                "disclosures": _disclosures(ledger, disk, started),
            }
        )
        _write_summary(output_dir, summary)
        _seal_bundle(output_dir)

    def write_marker(software_status: str) -> None:
        content = _compact_json_bytes(
            {"output_dir": str(output_dir.resolve()), "software_status": software_status}
        )
        with NamedTemporaryFile(mode="wb", dir=marker.parent, delete_on_close=False) as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
            stream.close()
            os.link(stream.name, marker)

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        ledger = WorkLedger()
        frozen_inputs.mkdir()
        for name, content in inputs.items():
            (frozen_inputs / name).write_bytes(content)
        _write_json(
            frozen_inputs / "sha256.json",
            {name: hashlib.sha256(content).hexdigest() for name, content in inputs.items()},
        )
        _write_json(frozen_inputs / "source_and_config_hashes.json", snapshot)
        _write_json(output_dir / "seed_ledger.json", _seed_ledger())
        generation = _generate_study(config, output_dir, root, ledger)
        evaluation = evaluate_after_blind(generation)
        _retain_blind_indexes(generation)
        with ledger.time_phase(None, "retention"):
            _retain_targets(
                generation, evaluation if isinstance(evaluation, StudyEvaluation) else None
            )
        if isinstance(evaluation, VoidCampaign):
            finish(evaluation, {"cause": evaluation.cause})
            write_marker("VOID")
            return summary
        across = _across_library(evaluation)
        _retain_scientific_outputs(generation, evaluation, across)
        finish(
            evaluation.campaign,
            {
                "scientific_status": across["verdicts"],
                "class": across["class"],
                "reading": across["reading"],
                "reference_sentences": evaluation.references.sentences,
                "exit_audit_pending": True,
            },
        )
    except BaseException as exc:
        recovery_failed = False
        try:
            _discard_scientific_outputs(output_dir)
            cause = f"{type(exc).__name__}: {exc}"
            finish(VoidCampaign("campaign_exception"), {"cause": cause})
        except BaseException as sealing_error:
            exc.add_note(f"VOID bundle sealing failed: {sealing_error!r}")
            recovery_failed = True
        # If recovery is interrupted, the sealed bundle remains the authoritative record.
        try:
            write_marker("VOID")
        except BaseException as marker_error:
            exc.add_note(f"VOID exit marker creation failed: {marker_error!r}")
            recovery_failed = True
        if recovery_failed or not isinstance(exc, Exception):
            raise
    else:
        write_marker("PASS")
    return summary


def dry_run(config_path: Path, predeclaration_path: Path) -> dict[str, Any]:
    config = StudyConfig.from_yaml(config_path)
    digest = validate_predeclaration(predeclaration_path)
    report = {"predeclaration_sha256": digest, **plan_workload(config)}
    print(json.dumps(report, indent=2))
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Frozen G43 synthetic multi-library study")
    commands = parser.add_subparsers(dest="command", required=True)
    dry = commands.add_parser("dry-run")
    dry.add_argument("--config", required=True, type=Path)
    dry.add_argument("--predeclaration", required=True, type=Path)
    run = commands.add_parser("execute")
    for option in ("config", "predeclaration", "output-dir"):
        run.add_argument(f"--{option}", required=True, type=Path)
    for option in ("owner-ruling", "clarification", "exit-marker", "seats"):
        run.add_argument(f"--{option}", type=Path)
    run.add_argument("--bundle-upper-bytes", type=int)
    args = parser.parse_args(argv)
    try:
        if args.command == "dry-run":
            dry_run(args.config, args.predeclaration)
        else:
            summary = execute(
                args.config,
                args.predeclaration,
                args.output_dir,
                root=Path(__file__).resolve().parents[2],
                owner_ruling_path=args.owner_ruling,
                clarification_path=args.clarification,
                exit_marker=args.exit_marker,
                bundle_upper_bytes=args.bundle_upper_bytes,
                seats=None if args.seats is None else json.loads(args.seats.read_bytes()),
            )
            print(summary["status_phrase"])
            if summary["software_status"] == "VOID":
                print(summary["cause"], file=sys.stderr)
                return 1
    except (CampaignError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
