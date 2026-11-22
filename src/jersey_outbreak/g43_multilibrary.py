"""Frozen G43 declaration, generation, blind fitting and recovery evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Context, Decimal, Inexact, localcontext
from itertools import groupby, product
from operator import attrgetter
from pathlib import Path
from typing import Any, Literal, TypedDict, cast

import yaml  # type: ignore[import-untyped]

from . import g43_constants as frozen
from .g35b_design_study import (
    STOCHASTIC_REPLICATE_VARIATION,
    _compare,
    _fit_scored_grid,
    _fixed_run_provenance,
    _GenerationAdapter,
    _offset_descriptive,
    _persist_fit,
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
        if self._counts[None] != self._caps[None]:
            raise BudgetError("measured shared-panel work differs from exact caps")
        for number in _LIBRARY_NUMBERS:
            if self._counts[number] != self._caps[number]:
                raise BudgetError(f"measured L{number} work differs from exact caps")
        if self._totals != self._total_caps:
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
) -> _GenerationAdapter:
    parent = _verified_parent(root, work_dir, seed, counter)
    # The unchanged adapter uses only Phase-0 constructor fields and dispatch(kind).
    return _GenerationAdapter(
        cast(_AdapterConfig, config),
        root,
        parameters,
        {seed: parent},
        cast(_AdapterCounter, counter),
        {"latent": 0.0, "transform": 0.0},
        [],
    )


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
        adapter = _adapter_for_seed(config, root, parameters, work_dir, seed, counter)
        latent, run = _latent_for(adapter, seed, truth)
        run_payload = run.model_dump(mode="json")
        observed, obs, table = _observe(
            adapter, latent, run, row.observation, config.target_observation_config_id, truth
        )
        if run.model_dump(mode="json") != run_payload:
            raise CampaignError("latent metadata changed during observation transforms")
        content = _compact_json_bytes(table.as_dict())
        file = _TargetTable(target_dir / f"{seed}.json", hashlib.sha256(content).hexdigest())
        file.path.write_bytes(content)
        targets[seed] = _TargetRun(file, latent, observed, run, obs)
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

            fit = _score_fit(
                target, grid, subset, hashes, replicates, counter, f"{group}_loss_evaluations"
            )
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
    grid = config.candidate_grid
    latent_cells = tuple(
        tuple(cells) for _, cells in groupby(grid, attrgetter("beta", "inoculation_day_offset"))
    )
    predictions: dict[CandidateCell, list[ObservedTables]] = {}
    configs: dict[CandidateCell, list[Mapping[str, Any]]] = {}
    for row in config.seeds:
        if row.library != number:
            continue
        adapter = _adapter_for_seed(config, root, parameters, directory, row.process, counter)
        for cells in latent_cells:
            latent, run = _latent_for(adapter, row.process, cells[0])
            run_payload = run.model_dump(mode="json")
            for cell in cells:
                if row.position == 1:
                    counter.dispatch("candidate_cells")
                    predictions[cell] = []
                    configs[cell] = []
                observed, _, table = _observe(
                    adapter,
                    latent,
                    run,
                    row.observation,
                    config.candidate_observation_config_id,
                    cell,
                )
                predictions[cell].append(table)
                configs[cell].append(
                    {"run": run_payload, "observation": observed.config.model_dump(mode="json")}
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
                _verify_blind_readback(_fit_path(directory, name, seed), record.fit, record.sha256)
    return tables


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
        )
        diagnostics[seed] = _truth_diagnostics_from_result(
            target.latent, target.observed, tables[seed], namespace_passed=namespace_passed
        )

    panel = evaluate_shared_panel(
        diagnostics,
        evidence=IntegrityEvidence(True, provenance_verified, generation.ledger.measured(None)),
    )
    evaluations = {
        number: evaluate_recovery(
            tuple(record.blind_record(seed) for seed, record in fits[_GATE_FIT].items()),
            shared_panel=panel,
            evidence=IntegrityEvidence(True, True, generation.ledger.measured(number)),
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
    args = parser.parse_args(argv)
    try:
        dry_run(args.config, args.predeclaration)
    except (CampaignError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
