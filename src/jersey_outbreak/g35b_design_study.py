"""Frozen synthetic G35-B study machinery; only dry-run is exposed by CLI.

Baseline generation and fitting are separated from truth joining so U2–U5 can
finish *all* arms before any truth join (§6). No calibration artifact is written.
The numerical profile and simulator-config constructors are imported unchanged
from Phase 0; the workload, objective, and ten-target gates are independent.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field, replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

from . import g35b_constants as frozen
from . import phase0_campaign as phase0
from .observation import observe_latent_run
from .outbreak_runner import load_parameter_set, run_outbreak
from .parent_build import build_parent
from .phase0_campaign import (
    BlindFitResult,
    BudgetError,
    CampaignError,
    CandidateCell,
    DimensionSpec,
    LossRow,
    ObservedTables,
    RecoveryRow,
    _estimate_hash,
    _namespace_passes,
    _observation_config_for_cell,
    _profile_dimension,
    _run_config_for_cell,
    _truth_diagnostics_from_result,
    candidate_config_hash,
    observation_dates,
    observed_tables_from_events,
    persist_blind_estimate,
)

ARM_FIELDS = (
    "replicates",
    "latent_days",
    "calendar_dates",
    "cells",
    "latent_calls",
    "observation_transforms",
    "serosurvey_samples",
    "builds",
)
TOTAL_FIELDS = ("cells", "latent_calls", "observation_transforms", "serosurvey_samples", "builds")
# Frozen §4.1/§8 order, including order *within* batches. Float sums use this order.
ARM_I_REPLICATE_ORDER = tuple(seed for _, seeds, _ in frozen.CANDIDATE_BATCHES for seed in seeds)
STOCHASTIC_REPLICATE_VARIATION = "stochastic_replicate_variation"


def frozen_payload() -> dict[str, Any]:
    """Return fresh declaration data from independent controls, never caller data."""
    return {
        "schema_version": "1.0",
        "campaign_id": "v13-g35b",
        "expected_predeclaration_sha256": frozen.PREDECLARATION_SHA256,
        "lineage": {
            "ridge_diagnostic_sha256": frozen.RIDGE_SHA256,
            "ridge_digest_source": frozen.CLARIFICATION_PATH,
        },
        "mode": "ci",
        "start_date": "2025-01-06",
        "observation_horizon_tail_days": 4,
        "dimensions": {
            name: {"truth": truth, "candidates": list(grid), "tolerance": tol, "bias_limit": bias}
            for name, truth, grid, tol, bias in frozen.DIMENSIONS
        },
        "fixed_scenario": {
            "population_size": 3000,
            "initial_seed_count": 0,
            "inoculation_attempts": 10,
            "inoculation_schedule": "start_date_plus_offset",
            "import_schedule": "empty_except_inoculation",
            "background_import_rate_per_day": "0.0",
            "route_multipliers": {name: "1.0" for name in phase0.P01_ROUTE_IDS},
            "symptomatic_probability": "0.6",
            "latent_duration_days": 2,
            "infectious_duration_days": 5,
            "waning_enabled": False,
            "seasonality": "absent",
            "interventions": "absent",
            "detection_delay_days": 0,
            "reporting_delay_days": 2,
            "weekday_effect": ["1.0"] * 7,
        },
        "observation": {
            "channels": ["symptomatic", "asymptomatic"],
            "source": "observation_events_only",
            "common_random_numbers": True,
        },
        "seeds": {
            "target_process_seeds": list(frozen.TARGET_PROCESS_SEEDS),
            "target_observation_seeds": list(frozen.TARGET_OBSERVATION_SEEDS),
            "target_serosurvey_seeds": list(frozen.TARGET_SEROSURVEY_SEEDS),
            "target_observation_config_id": "v13-g35b-target",
            "candidate_observation_config_id": "v13-g35b-fit",
            "target_serosurvey_config_id": "v13-g35b-sero-target",
            "candidate_serosurvey_config_id": "v13-g35b-sero-fit",
            "candidate_batches": {
                name: {"process_seeds": list(process), "observation_seeds": list(obs)}
                for name, process, obs in frozen.CANDIDATE_BATCHES
            },
            "candidate_serosurvey_seeds": list(frozen.FIT_SEROSURVEY_SEEDS),
            "optimizer_seed": None,
        },
        "serosurvey": {
            "n": 400,
            "survey_day": 29,
            "seroconversion_lag_days": 0,
            "sensitivity": "1",
            "specificity": "1",
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
            "lexicographic_tie_break": "forbidden",
        },
        "acceptance": {
            "targets": 10,
            "hits_multiplier": 5,
            "hits_required_multiplier": 4,
            "joint_multiplier": 5,
            "joint_required_multiplier": 3,
            "boundary_multiplier": 5,
            "boundary_maximum_multiplier": 1,
            "inoculation_acquisitions": 10,
            "minimum_local_secondary_infections": 1,
            "minimum_reports_per_channel": 1,
            "minimum_nonzero_combined_dates": 3,
        },
        "arms": {
            arm: dict(zip(ARM_FIELDS, values, strict=True)) for arm, *values in frozen.ARM_CAPS
        },
        "budget_caps": dict(zip(TOTAL_FIELDS, frozen.TOTAL_CAPS, strict=True)),
        "process_hashes": {
            seed: dict(zip(("m2", "m3", "m4"), hashes, strict=True))
            for seed, hashes in frozen.PROCESS_HASHES.items()
        },
        "implementation": {
            "implemented_arms": ["B"],
            "required_arms": ["B", "i", "ii", "iii"],
            "retries": 0,
            "replacement_seeds": False,
            "adaptive_grid": False,
            "pruning": False,
            "early_stopping": False,
        },
    }


def _compare(actual: Any, expected: Any, path: str = "config") -> None:
    if type(actual) is not type(expected):
        raise CampaignError(f"frozen declaration changed at {path}")
    if isinstance(expected, dict):
        if actual.keys() != expected.keys():
            raise CampaignError(f"frozen declaration keys changed at {path}")
        for key, value in expected.items():
            _compare(actual[key], value, f"{path}.{key}")
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise CampaignError(f"frozen declaration length changed at {path}")
        for index, value in enumerate(expected):
            _compare(actual[index], value, f"{path}[{index}]")
    elif actual != expected:
        raise CampaignError(f"frozen declaration changed at {path}")


def _seed_overlap_check(seeds: Mapping[str, Any]) -> None:
    values = [
        *seeds["target_process_seeds"],
        *seeds["target_observation_seeds"],
        *seeds["target_serosurvey_seeds"],
        *seeds["candidate_serosurvey_seeds"],
        *(
            seed
            for batch in seeds["candidate_batches"].values()
            for key in ("process_seeds", "observation_seeds")
            for seed in batch[key]
        ),
    ]
    if len(set(values)) != len(values):
        raise BudgetError("seed overlap within the study")
    if set(values).intersection(seed for group in frozen.EARLIER_SEED_SETS for seed in group):
        raise BudgetError("seed overlap with earlier campaign or retired probe")


def validate_frozen_payload(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise CampaignError("config must be a YAML mapping")
    # Exact comparison also rejects undeclared settings and wrong scalar types.
    # Check overlap first when the seed schema is intact, for a useful stop reason.
    try:
        _seed_overlap_check(payload["seeds"])
    except (KeyError, TypeError, AttributeError) as exc:
        raise CampaignError("invalid seed declaration") from exc
    _compare(payload, frozen_payload())


def _dimensions() -> tuple[DimensionSpec, ...]:
    return tuple(
        DimensionSpec(
            name,
            float(truth),
            tuple(map(float, grid)),
            float(tol),
            float(bias),
            Decimal(truth),
            tuple(map(Decimal, grid)),
            Decimal(tol),
            Decimal(bias),
        )
        for name, truth, grid, tol, bias in frozen.DIMENSIONS
    )


@dataclass(frozen=True)
class StudyConfig:
    """Only the independently frozen payload can construct a study configuration."""

    mode: str = "ci"
    start_date: date = date(2025, 1, 6)
    duration_days: int = 30
    observation_horizon_tail_days: int = 4
    initial_seed_count: int = 0
    inoculation_attempts: int = 10
    import_rate_per_day: float = 0.0
    route_multipliers: tuple[tuple[str, float], ...] = tuple(
        (name, 1.0) for name in phase0.P01_ROUTE_IDS
    )
    symptomatic_probability: float = 0.6
    waning_enabled: bool = False
    reporting_delay_days: int = 2
    weekday_effect: tuple[float, ...] = (1.0,) * 7
    target_process_seeds: tuple[int, ...] = frozen.TARGET_PROCESS_SEEDS
    target_observation_seeds: tuple[int, ...] = frozen.TARGET_OBSERVATION_SEEDS
    candidate_process_seeds: tuple[int, ...] = frozen.CANDIDATE_BATCHES[0][1]
    candidate_observation_seeds: tuple[int, ...] = frozen.CANDIDATE_BATCHES[0][2]
    target_observation_config_id: str = "v13-g35b-target"
    candidate_observation_config_id: str = "v13-g35b-fit"
    dimensions: tuple[DimensionSpec, ...] = field(default_factory=_dimensions)

    @classmethod
    def from_yaml(cls, path: Path) -> StudyConfig:
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise CampaignError(f"cannot read study config: {exc}") from exc
        validate_frozen_payload(payload)
        return cls()

    @property
    def dimension_map(self) -> dict[str, DimensionSpec]:
        return {spec.name: spec for spec in self.dimensions}

    @property
    def candidate_grid(self) -> tuple[CandidateCell, ...]:
        return tuple(
            CandidateCell(beta, int(offset), sym, asym)
            for beta in self.dimensions[0].candidates
            for offset in self.dimensions[1].candidates
            for sym in self.dimensions[2].candidates
            for asym in self.dimensions[3].candidates
        )


def committed_document_bytes(path: Path, *, commit: str = "HEAD") -> bytes:
    """Read a tracked document via git show, never hash checkout bytes.

    A CRLF checkout is accepted only after replacing CRLF with LF and proving
    equality to the committed blob. Untracked copies and all other edits fail.
    The returned bytes (and all document digests) are the committed bytes.
    """
    path = path.resolve()
    try:
        root = Path(
            subprocess.check_output(
                ["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"],
                stderr=subprocess.PIPE,
            )
            .decode()
            .strip()
        )
        relative = path.relative_to(root).as_posix()
        content = subprocess.check_output(
            ["git", "-C", str(root), "show", f"{commit}:{relative}"],
            stderr=subprocess.PIPE,
        )
        if path.read_bytes().replace(b"\r\n", b"\n") != content:
            raise CampaignError("repository document differs from committed bytes")
        return content
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise CampaignError(f"cannot verify committed repository document {path}: {exc}") from exc


def validate_predeclaration(path: Path) -> str:
    """Require the independent frozen digest of the supplied committed document."""
    actual = hashlib.sha256(committed_document_bytes(path)).hexdigest()
    if actual != frozen.PREDECLARATION_SHA256:
        raise CampaignError(f"predeclaration SHA-256 mismatch: got {actual}")
    return actual


def plan_workload(config: StudyConfig) -> dict[str, Any]:
    """Calculate new work with declared cross-arm sharing, without dispatch."""
    if config != StudyConfig():
        raise BudgetError("runtime config differs from frozen scenario, seeds or grid")
    payload = frozen_payload()
    seeds = payload["seeds"]
    _seed_overlap_check(seeds)
    cells = math.prod(len(spec.candidates) for spec in config.dimensions)
    latent_tuples = len(config.dimensions[0].candidates) * len(config.dimensions[1].candidates)
    targets = len(config.target_process_seeds)
    a = len(config.candidate_process_seeds)
    extra = sum(len(batch[1]) for batch in frozen.CANDIDATE_BATCHES[1:])
    work = (
        ("B", targets + a * latent_tuples, targets + cells * a, 0, targets + a),
        ("i", extra * latent_tuples, cells * extra, 0, extra),
        ("ii", targets + a * latent_tuples, targets + cells * a, 0, 0),
        ("iii", 0, 0, targets + a * latent_tuples, 0),
    )
    arms = {}
    for arm, latent, transforms, samples, builds in work:
        declared = payload["arms"][arm]
        calculated = {
            **declared,
            "cells": cells,
            "latent_calls": latent,
            "observation_transforms": transforms,
            "serosurvey_samples": samples,
            "builds": builds,
        }
        if calculated != declared or calculated["calendar_dates"] != calculated["latent_days"] + 4:
            raise BudgetError(f"predicted {arm} workload differs from exact caps")
        arms[arm] = calculated
    totals = {key: sum(arm[key] for arm in arms.values()) for key in TOTAL_FIELDS}
    if totals != payload["budget_caps"]:
        raise BudgetError("predicted totals differ from exact caps")
    return {
        "mode": config.mode,
        "arms": arms,
        "totals": totals,
        "gate_loss_evaluations": 4 * targets * cells,
        "descriptive_loss_evaluations": 5 * targets * cells,
    }


def loss(target: ObservedTables, predictions: Sequence[ObservedTables], R: int, T: int) -> float:
    """§6 objective, preserving Phase-0 summation order for bit-for-bit equality."""
    if type(R) is not int or R < 1 or len(predictions) != R:
        raise CampaignError("replicate count must equal positive R")
    if type(T) is not int or T < 1 or len(target.dates) != T:
        raise CampaignError("date count must equal positive T")
    if any(len(table.dates) != T or table.dates != target.dates for table in predictions):
        raise CampaignError("candidate date count/calendar differs from target T")
    total = 0.0
    for channel_index, channel in enumerate(target.channel_values):
        for time_index, target_count in enumerate(channel):
            mean = (
                sum(
                    math.sqrt(table.channel_values[channel_index][time_index] + 3.0 / 8.0)
                    for table in predictions
                )
                / R
            )
            total += (math.sqrt(target_count + 3.0 / 8.0) - mean) ** 2
    return total / (2.0 * T)


def fit_blind(
    target_tables: ObservedTables,
    candidate_grid: Sequence[CandidateCell],
    candidate_prediction_library: Mapping[CandidateCell, Sequence[ObservedTables]],
    *,
    R: int,
    T: int,
    candidate_config_hashes: Mapping[CandidateCell, str] | None = None,
) -> BlindFitResult:
    """Truth-free generalized fitting boundary: tables, grid, library and R/T only."""
    return _fit_scored_grid(
        candidate_grid,
        candidate_prediction_library,
        lambda cell: loss(target_tables, candidate_prediction_library[cell], R, T),
        candidate_config_hashes,
    )


def _fit_scored_grid(
    candidate_grid: Sequence[CandidateCell],
    candidate_prediction_library: Mapping[CandidateCell, Sequence[ObservedTables]],
    objective: Callable[[CandidateCell], float],
    candidate_config_hashes: Mapping[CandidateCell, str] | None = None,
) -> BlindFitResult:
    """Shared complete-grid validation, selection, ties, profiles and hashing."""
    grid = tuple(candidate_grid)
    if not grid or len(set(grid)) != len(grid):
        raise CampaignError("candidate grid must be nonempty and unique")
    # The declared Cartesian product must be complete; every cell is scored.
    values = {
        name: tuple(sorted({float(getattr(cell, name)) for cell in grid}))
        for name in phase0.P01_DIMENSION_NAMES
    }
    if math.prod(map(len, values.values())) != len(grid):
        raise CampaignError("candidate grid is not a complete Cartesian product")
    if set(candidate_prediction_library) != set(grid):
        raise CampaignError("candidate prediction library is incomplete")
    if candidate_config_hashes is not None and set(candidate_config_hashes) != set(grid):
        raise CampaignError("candidate config hashes are incomplete")
    surface = tuple(
        LossRow(
            cell,
            objective(cell),
            candidate_config_hashes[cell]
            if candidate_config_hashes is not None
            else candidate_config_hash(cell),
        )
        for cell in grid
    )
    minimum = min(row.objective for row in surface)
    tau = 1e-12 * max(1.0, minimum)
    minimizers = tuple(row.cell for row in surface if abs(row.objective - minimum) <= tau)
    tied = len(minimizers) > 1
    selected = None if tied else minimizers[0]
    profiles = tuple(
        _profile_dimension(surface, name, grid_values, minimum)
        for name, grid_values in values.items()
    )
    return BlindFitResult(
        surface,
        minimum,
        minimizers,
        tied,
        tau,
        selected,
        profiles,
        not tied and all(profile.identified for profile in profiles),
        _estimate_hash(selected, minimum, profiles, tied, surface),
    )


@dataclass(frozen=True)
class RecoveryEvaluation:
    status: str
    predicates: Mapping[str, bool]
    hits: Mapping[str, int]
    joint_hits: int
    boundary_counts: Mapping[str, int]
    mean_bias: Mapping[str, Decimal | None]
    rows: tuple[dict[str, Any], ...]


def evaluate_recovery(
    rows: Sequence[RecoveryRow],
    *,
    execution_complete: bool = False,
    provenance_verified: bool = False,
    measured_equals_caps: bool = False,
) -> RecoveryEvaluation:
    """§7.1 exact integer and declared-decimal gates; no fallback input exists."""
    complete = (
        len(rows) == 10 and tuple(row.target_seed for row in rows) == frozen.TARGET_PROCESS_SEEDS
    )
    hits: dict[str, int] = {}
    bias: dict[str, Decimal | None] = {}
    boundaries: dict[str, int] = {}
    target_hits: dict[int, list[bool]] = {row.target_seed: [] for row in rows}
    serialized: list[dict[str, Any]] = []
    for spec in _dimensions():
        errors = []
        hits[spec.name] = 0
        for row in rows:
            error = (
                None
                if row.selected is None
                else spec.exact_value(getattr(row.selected, spec.name)) - spec.exact_truth()
            )
            identified = not row.numerical_tie and any(
                p.dimension == spec.name and p.identified for p in row.profiles
            )
            within = error is not None and abs(error) <= spec.exact_tolerance()
            hit = identified and within
            hits[spec.name] += int(hit)
            target_hits[row.target_seed].append(hit)
            if error is not None:
                errors.append(error)
            serialized.append(
                {
                    "target_seed": row.target_seed,
                    "estimate_hash": row.estimate_hash,
                    "dimension": spec.name,
                    "estimate": None if row.selected is None else getattr(row.selected, spec.name),
                    "truth": str(spec.exact_truth()),
                    "signed_error": None if error is None else str(error),
                    "absolute_error": None if error is None else str(abs(error)),
                    "identified": identified,
                    "within_tolerance_hit": within,
                    "numerical_tie": row.numerical_tie,
                    "truth_diagnostics": row.truth_diagnostics.as_dict(),
                }
            )
        bias[spec.name] = sum(errors, Decimal(0)) / Decimal(10) if len(errors) == 10 else None
        # Independent predicate-8 path: never infer boundary flags/counts from hits.
        flags = {
            row.target_seed: row.selected is not None
            and spec.exact_value(getattr(row.selected, spec.name))
            in (spec.exact_candidates()[0], spec.exact_candidates()[-1])
            for row in rows
        }
        boundaries[spec.name] = sum(flags.values())
        for item in serialized:
            if item["dimension"] == spec.name:
                item["selected_at_grid_boundary"] = flags[item["target_seed"]]
                item["boundary_count"] = boundaries[spec.name]
    joint = sum(all(values) for values in target_hits.values())
    predicates = {
        "1_complete": complete
        and execution_complete
        and all(row.scored_cell_count == 625 for row in rows),
        "2_truth_viability": complete and all(row.truth_diagnostics.viable for row in rows),
        "3_chronology_conservation": complete
        and all(
            row.truth_diagnostics.chronology_passed
            and row.truth_diagnostics.latent_incidence_conservation_passed
            for row in rows
        ),
        "4_no_global_tie": complete and all(not row.numerical_tie for row in rows),
        "5_dimension_hits": complete and all(count * 5 >= 4 * 10 for count in hits.values()),
        "6_joint_hits": complete and joint * 5 >= 3 * 10,
        "7_bias": complete
        and all(
            bias[spec.name] is not None
            and abs(cast(Decimal, bias[spec.name])) <= spec.exact_bias_limit()
            for spec in _dimensions()
        ),
        "8_boundaries": complete and all(count * 5 <= 1 * 10 for count in boundaries.values()),
        "9_provenance": complete
        and provenance_verified
        and all(
            row.namespace_passed
            and row.truth_diagnostics.namespace_passed
            and row.truth == CandidateCell(0.08, 2, 0.75, 0.25)
            for row in rows
        ),
        "10_measured_caps": measured_equals_caps,
    }
    for item in serialized:
        item["joint_hit"] = all(target_hits[item["target_seed"]])
    return RecoveryEvaluation(
        "PASS" if all(predicates.values()) else "FAIL",
        predicates,
        hits,
        joint,
        boundaries,
        bias,
        tuple(serialized),
    )


@dataclass
class WorkCounter:
    """Reserve each call before dispatch; an exception consumes its slot, never retries."""

    arm: str
    measured: dict[str, int] = field(default_factory=lambda: {key: 0 for key in TOTAL_FIELDS})

    def dispatch(self, kind: str) -> None:
        cap = frozen_payload()["arms"][self.arm][kind]
        if self.measured[kind] >= cap:
            raise BudgetError(f"{self.arm} {kind} cap reached before dispatch")
        self.measured[kind] += 1

    def exact(self) -> bool:
        caps = frozen_payload()["arms"][self.arm]
        return all(self.measured[key] == caps[key] for key in TOTAL_FIELDS)


def _contains_key(node: Any, key: str) -> bool:
    return (
        isinstance(node, dict)
        and (key in node or any(_contains_key(value, key) for value in node.values()))
    ) or (isinstance(node, list) and any(_contains_key(value, key) for value in node))


def verify_parent(generated: Any, seed: int) -> dict[str, Any]:
    """Check returned M2/M3/M4 lineage against the independent frozen table.

    Fallback presence is read from the built M2/M3 diagnostics (clarification 1,
    item 2), retained only for disclosures and never passed to the predicates.
    """
    try:
        actual = (
            generated.m2_input.manifest.logical_content_hash,
            generated.m3_input.manifest.logical_content_hash,
            generated.logical_content_hash,
        )
        if actual != frozen.PROCESS_HASHES[seed]:
            raise CampaignError(f"predicate 1: parent logical hash mismatch for {seed}")
        for stage in (generated.m2_input, generated.m3_input):
            if stage.manifest.seed != seed or stage.manifest.mode != "ci":
                raise CampaignError("predicate 1: parent seed/mode mismatch")
        if generated.config.seed != seed or generated.config.mode != "ci":
            raise CampaignError("predicate 1: network seed/mode mismatch")
        diagnostics = [
            json.loads((stage.artifact_directory / "diagnostics.json").read_text())
            for stage in (generated.m2_input, generated.m3_input)
        ]
        if any(not isinstance(node, dict) for node in diagnostics):
            raise CampaignError("missing parent diagnostics")
        return {
            "m2": actual[0],
            "m3": actual[1],
            "m4": actual[2],
            "population_fallback_m2": _contains_key(
                diagnostics[0], "private_assignment_residual_fallback"
            ),
            "population_fallback_m3": _contains_key(
                diagnostics[1], "destination_reassignment_fallback"
            ),
        }
    except (AttributeError, KeyError, OSError, ValueError) as exc:
        raise CampaignError(f"predicate 1: parent verification failed for {seed}: {exc}") from exc


@dataclass(frozen=True)
class BaselineGeneration:
    """Retained B inputs for later arms; deliberately contains no truth-joined rows."""

    config: StudyConfig
    target_tables: Mapping[int, ObservedTables]
    # Returned results AND independently requested configs, retained for the join.
    target_outputs: Mapping[int, tuple[Any, Any, Any, Any]]
    candidate_prediction_library: Mapping[CandidateCell, tuple[ObservedTables, ...]]
    candidate_latents: Mapping[tuple[int, float, int], tuple[Any, Any]]
    generated_parents: Mapping[int, Any]
    parent_lineage: Mapping[int, Mapping[str, Any]]
    candidate_config_hashes: Mapping[CandidateCell, str]
    replicate_provenance: tuple[Mapping[str, Any], ...]
    blind_fits: Mapping[int, BlindFitResult]
    blind_paths: Mapping[int, Path]
    blind_file_hashes: Mapping[int, str]
    measured: Mapping[str, int]
    disclosures: Mapping[str, Any]


def _verify_blind_readback(path: Path, fit: BlindFitResult, file_hash: str) -> None:
    try:
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != file_hash or json.loads(content) != fit.as_dict():
            raise CampaignError("blind estimate read-back mismatch")
        if (
            _estimate_hash(
                fit.selected,
                fit.minimum_objective,
                fit.profiles,
                fit.numerical_tie,
                fit.loss_surface,
            )
            != fit.estimate_hash
        ):
            raise CampaignError("blind estimate content hash mismatch")
    except (OSError, ValueError) as exc:
        raise CampaignError(f"blind estimate read-back failed: {exc}") from exc


@dataclass
class _GenerationAdapter:
    """Shared U1 simulator adapter; returned metadata is mandatory evidence."""

    config: StudyConfig
    root: Path
    parameters: Any
    parents: Mapping[int, Any]
    counter: WorkCounter
    phase_seconds: dict[str, float]
    runtimes: list[dict[str, Any]]

    @property
    def constructor_config(self) -> phase0.CampaignConfig:
        # Unchanged Phase-0 constructors consume only this structural subset.
        return cast(phase0.CampaignConfig, self.config)

    def latent_for(self, seed: int, cell: CandidateCell) -> tuple[Any, Any]:
        run_config = _run_config_for_cell(self.constructor_config, self.parameters, seed, cell)
        self.counter.dispatch("latent_calls")
        started = time.perf_counter()
        result = run_outbreak(self.parents[seed], run_config, self.parameters)
        self.phase_seconds["latent"] += time.perf_counter() - started
        if (
            getattr(result, "config", None) != run_config
            or getattr(result, "generated", None) is not self.parents[seed]
        ):
            raise CampaignError("latent result omitted or changed returned config/parent metadata")
        try:
            runtime = result.diagnostics["benchmark"]["runtime_seconds"]
            if not math.isfinite(runtime) or runtime < 0:
                raise ValueError("invalid runtime")
            self.runtimes.append(
                {
                    "seed": seed,
                    "beta": cell.beta,
                    "offset": cell.inoculation_day_offset,
                    "runtime_seconds": runtime,
                }
            )
        except (KeyError, AttributeError, TypeError, ValueError) as exc:
            raise CampaignError("latent result missing runtime_seconds disclosure") from exc
        return result, run_config

    def observe(
        self, latent: Any, run_config: Any, seed: int, namespace: str, cell: CandidateCell
    ) -> tuple[Any, Any, ObservedTables]:
        obs = _observation_config_for_cell(
            self.root, self.constructor_config, seed, namespace, cell
        )
        self.counter.dispatch("observation_transforms")
        started = time.perf_counter()
        result = observe_latent_run(latent, obs)
        self.phase_seconds["transform"] += time.perf_counter() - started
        if not _namespace_passes(latent, result, run_config, obs):
            raise CampaignError("observation namespace evidence missing or mismatched")
        table = observed_tables_from_events(
            result.observation_events,
            dates=observation_dates(
                self.config.start_date,
                self.config.duration_days,
                self.config.observation_horizon_tail_days,
            ),
        )
        return result, obs, table


def generate_baseline(
    config_path: Path,
    predeclaration_path: Path,
    work_dir: Path,
    *,
    root: Path,
) -> BaselineGeneration:
    """Implement B's generation and blind fit, without joining any truth.

    Callable research adapter only; U1 provides no execute CLI or campaign entry.
    Future all-arm orchestration calls this, the factor hooks, then joins truth.
    """
    config = StudyConfig.from_yaml(config_path)
    validate_predeclaration(predeclaration_path)
    plan_workload(config)
    parameters = load_parameter_set(root)
    truth_cell = CandidateCell(
        config.dimensions[0].truth,
        int(config.dimensions[1].truth),
        config.dimensions[2].truth,
        config.dimensions[3].truth,
    )
    counter = WorkCounter("B")
    parents: dict[int, Any] = {}
    lineage: dict[int, Mapping[str, Any]] = {}
    phase_seconds = {key: 0.0 for key in ("build", "latent", "transform", "scoring")}
    runtimes: list[dict[str, Any]] = []
    for seed in (*config.target_process_seeds, *config.candidate_process_seeds):
        counter.dispatch("builds")
        started = time.perf_counter()
        try:
            parent = build_parent(root, "ci", seed, work_dir / "parents" / str(seed), write_m4=True)
        except Exception as exc:
            raise CampaignError(f"predicate 1: parent build failed for {seed}: {exc}") from exc
        phase_seconds["build"] += time.perf_counter() - started
        lineage[seed] = verify_parent(parent.generated, seed)
        parents[seed] = parent.generated

    adapter = _GenerationAdapter(
        config, root, parameters, parents, counter, phase_seconds, runtimes
    )
    latent_for, observe = adapter.latent_for, adapter.observe

    targets = {}
    outputs = {}
    for seed, obs_seed in zip(
        config.target_process_seeds, config.target_observation_seeds, strict=True
    ):
        latent, run_config = latent_for(seed, truth_cell)
        observed, observation_config, table = observe(
            latent, run_config, obs_seed, config.target_observation_config_id, truth_cell
        )
        targets[seed] = table
        outputs[seed] = (latent, observed, run_config, observation_config)
    latents = {}
    for seed in config.candidate_process_seeds:
        for beta in config.dimensions[0].candidates:
            for offset in config.dimensions[1].candidates:
                cell = replace(
                    config.candidate_grid[0], beta=beta, inoculation_day_offset=int(offset)
                )
                latents[seed, beta, int(offset)] = latent_for(seed, cell)
    library = {}
    hashes = {}
    provenance = []
    for cell in config.candidate_grid:
        counter.dispatch("cells")
        tables = []
        configs = []
        for seed, obs_seed in zip(
            config.candidate_process_seeds, config.candidate_observation_seeds, strict=True
        ):
            latent, run_config = latents[seed, cell.beta, cell.inoculation_day_offset]
            observed, obs, table = observe(
                latent, run_config, obs_seed, config.candidate_observation_config_id, cell
            )
            tables.append(table)
            configs.append((run_config, obs))
            provenance.append(
                {
                    "cell": cell.as_dict(),
                    "batch": "A",
                    "process_seed": seed,
                    "observation_seed": obs_seed,
                    "observation_config": obs.model_dump(mode="json"),
                    "run_config": run_config.model_dump(mode="json"),
                    "table_sha256": hashlib.sha256(
                        phase0._compact_json_bytes(table.as_dict())
                    ).hexdigest(),
                    "population_lineage": lineage[seed],
                    "observation_rng": observed.diagnostics["observation_rng"],
                }
            )
        library[cell] = tuple(tables)
        hashes[cell] = hashlib.sha256(
            phase0._compact_json_bytes(
                [
                    {"run": run.model_dump(mode="json"), "observation": obs.model_dump(mode="json")}
                    for run, obs in configs
                ]
            )
        ).hexdigest()
    if not counter.exact():
        raise BudgetError("baseline measured work differs from exact B caps")
    fits = {}
    paths = {}
    file_hashes = {}
    started = time.perf_counter()
    for seed, table in targets.items():
        fit = fit_blind(
            table, config.candidate_grid, library, R=3, T=34, candidate_config_hashes=hashes
        )
        path = work_dir / "blind_estimates" / f"{seed}.json"
        persist_blind_estimate(path, fit)
        file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        _verify_blind_readback(path, fit, file_hash)
        fits[seed], paths[seed], file_hashes[seed] = fit, path, file_hash
    phase_seconds["scoring"] += time.perf_counter() - started
    return BaselineGeneration(
        config,
        targets,
        outputs,
        library,
        latents,
        parents,
        lineage,
        hashes,
        tuple(provenance),
        fits,
        paths,
        file_hashes,
        dict(counter.measured),
        {
            "phase_wall_time_seconds": phase_seconds,
            "latent_runtimes": runtimes,
            "fallback_source": frozen.CLARIFICATION_PATH,
            "fallback_built_targets": sum(
                any(lineage[s][key] for key in ("population_fallback_m2", "population_fallback_m3"))
                for s in config.target_process_seeds
            ),
            "fallback_built_candidates": sum(
                any(lineage[s][key] for key in ("population_fallback_m2", "population_fallback_m3"))
                for s in config.candidate_process_seeds
            ),
            "measured_counters": dict(counter.measured),
        },
    )


def _baseline_execution_complete(generation: BaselineGeneration) -> bool:
    config = generation.config
    return (
        set(generation.target_tables) == set(config.target_process_seeds)
        and set(generation.target_outputs) == set(config.target_process_seeds)
        and set(generation.generated_parents)
        == set((*config.target_process_seeds, *config.candidate_process_seeds))
        and set(generation.candidate_latents)
        == {
            (seed, beta, int(offset))
            for seed in config.candidate_process_seeds
            for beta in config.dimensions[0].candidates
            for offset in config.dimensions[1].candidates
        }
        and set(generation.candidate_prediction_library) == set(config.candidate_grid)
        and all(len(tables) == 3 for tables in generation.candidate_prediction_library.values())
    )


def join_baseline(generation: BaselineGeneration, output_dir: Path) -> RecoveryEvaluation:
    """Post-generation truth join. U5 must call only after all arms finish generation."""
    config = generation.config
    plan_workload(config)
    # Re-read *all* blind records before looking at any target's latent events.
    for seed in config.target_process_seeds:
        _verify_blind_readback(
            generation.blind_paths[seed],
            generation.blind_fits[seed],
            generation.blind_file_hashes[seed],
        )
    rows = []
    truth = CandidateCell(0.08, 2, 0.75, 0.25)
    for seed in config.target_process_seeds:
        latent, observed, requested_run, requested_observation = generation.target_outputs[seed]
        namespace = _namespace_passes(latent, observed, requested_run, requested_observation)
        diagnostics = _truth_diagnostics_from_result(
            latent, observed, generation.target_tables[seed], namespace_passed=namespace
        )
        fit = generation.blind_fits[seed]
        rows.append(
            RecoveryRow(
                seed,
                fit.estimate_hash,
                fit.selected,
                fit.profiles,
                fit.numerical_tie,
                truth,
                diagnostics,
                namespace,
                len(fit.loss_surface),
            )
        )
    expected = {key: frozen_payload()["arms"]["B"][key] for key in TOTAL_FIELDS}
    complete = _baseline_execution_complete(generation)
    evaluation = evaluate_recovery(
        rows,
        execution_complete=complete,
        provenance_verified=True,
        measured_equals_caps=generation.measured == expected,
    )
    # A10 / clarification 1 item 2: add fallback disclosures *after* gating.
    serial = tuple(
        {
            **row,
            **{
                key: str(bool(generation.parent_lineage[row["target_seed"]][key])).upper()
                for key in ("population_fallback_m2", "population_fallback_m3")
            },
        }
        for row in evaluation.rows
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "g35b_B_recovery.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(serial[0]))
        writer.writeheader()
        writer.writerows(serial)
    (output_dir / "g35b_B_disclosures.json").write_bytes(
        phase0._compact_json_bytes(generation.disclosures)
    )
    return replace(evaluation, rows=serial)


def run_baseline_arm(
    config_path: Path, predeclaration_path: Path, work_dir: Path, *, root: Path
) -> tuple[BaselineGeneration, RecoveryEvaluation]:
    """Baseline-only orchestration for mock testing; never an all-arms campaign."""
    generation = generate_baseline(config_path, predeclaration_path, work_dir, root=root)
    return generation, join_baseline(generation, work_dir)


@dataclass(frozen=True)
class ArmIGeneration:
    """Blind arm-(i) results; new work only in parents, latents and provenance.

    Batch A and all targets remain owned by ``baseline``. The twelve-table
    library holds the original A table objects, followed by B′, C′ and D′.
    Descriptive records are retained separately from the ten gate estimates.
    """

    baseline: BaselineGeneration
    candidate_prediction_library: Mapping[CandidateCell, tuple[ObservedTables, ...]]
    candidate_latents: Mapping[tuple[int, float, int], tuple[Any, Any]]
    generated_parents: Mapping[int, Any]
    parent_lineage: Mapping[int, Mapping[str, Any]]
    candidate_config_hashes: Mapping[CandidateCell, str]
    replicate_provenance: tuple[Mapping[str, Any], ...]
    blind_fits: Mapping[int, BlindFitResult]
    blind_paths: Mapping[int, Path]
    blind_file_hashes: Mapping[int, str]
    descriptive_fits: Mapping[tuple[int, str], BlindFitResult]
    descriptive_paths: Mapping[tuple[int, str], Path]
    descriptive_file_hashes: Mapping[tuple[int, str], str]
    descriptives: Mapping[str, Any]
    descriptives_path: Path
    descriptives_file_hash: str
    measured: Mapping[str, int]
    disclosures: Mapping[str, Any]


def batch_objective_spread(objectives: Sequence[float]) -> dict[str, Any]:
    """Four-batch range and median: mean of the middle two sorted values."""
    if len(objectives) != 4:
        raise CampaignError("batch spread requires exactly four objectives")
    ordered = sorted(objectives)
    return {
        "label": STOCHASTIC_REPLICATE_VARIATION,
        "range": ordered[-1] - ordered[0],
        "median": (ordered[1] + ordered[2]) / 2,
    }


def batch_offset_agreement(fits: Sequence[BlindFitResult]) -> bool:
    """Identical selected offsets across four batches; a global tie never agrees."""
    return (
        len(fits) == 4
        and all(not fit.numerical_tie and fit.selected is not None for fit in fits)
        and len({fit.selected.inoculation_day_offset for fit in fits if fit.selected is not None})
        == 1
    )


@dataclass
class DescriptiveLossCounter:
    """Separate accounting of scored descriptive surfaces, excluding the gate."""

    cap: int
    measured: int = 0

    def record(self, fit: BlindFitResult) -> None:
        self.measured += len(fit.loss_surface)
        if self.measured > self.cap:
            raise BudgetError("descriptive loss evaluation cap exceeded")

    def check_exact(self) -> None:
        if self.measured != self.cap:
            raise BudgetError("descriptive loss evaluations differ from exact cap")


def _persist_fit(path: Path, fit: BlindFitResult) -> str:
    persist_blind_estimate(path, fit)
    file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    _verify_blind_readback(path, fit, file_hash)
    return file_hash


def arm_i(
    baseline: BaselineGeneration,
    config: StudyConfig,
    work_dir: Path,
    *,
    root: Path,
) -> ArmIGeneration:
    """Generate B′/C′/D′, then blind-fit the nested 3/6/12 libraries.

    No target latent events or truth diagnostics are read here. U5 must complete
    every arm's generation before calling any truth join (§6).
    """
    plan = plan_workload(config)
    expected_b = {key: plan["arms"]["B"][key] for key in TOTAL_FIELDS}
    if (
        baseline.config != config
        or baseline.measured != expected_b
        or not _baseline_execution_complete(baseline)
    ):
        raise CampaignError("arm (i) requires completed baseline generation")
    for seed in config.target_process_seeds:
        _verify_blind_readback(
            baseline.blind_paths[seed], baseline.blind_fits[seed], baseline.blind_file_hashes[seed]
        )
    counter = WorkCounter("i")
    parents: dict[int, Any] = {}
    lineage: dict[int, Mapping[str, Any]] = {}
    phase_seconds = {key: 0.0 for key in ("build", "latent", "transform", "scoring")}
    runtimes: list[dict[str, Any]] = []
    parameters = load_parameter_set(root)
    extra_seeds = ARM_I_REPLICATE_ORDER[3:]
    for seed in extra_seeds:
        counter.dispatch("builds")
        started = time.perf_counter()
        try:
            parent = build_parent(root, "ci", seed, work_dir / "parents" / str(seed), write_m4=True)
        except Exception as exc:
            raise CampaignError(f"predicate 1: parent build failed for {seed}: {exc}") from exc
        phase_seconds["build"] += time.perf_counter() - started
        lineage[seed] = verify_parent(parent.generated, seed)
        parents[seed] = parent.generated
    adapter = _GenerationAdapter(
        config, root, parameters, parents, counter, phase_seconds, runtimes
    )
    latents = {}
    for seed in extra_seeds:
        for beta in config.dimensions[0].candidates:
            for offset in config.dimensions[1].candidates:
                cell = replace(
                    config.candidate_grid[0], beta=beta, inoculation_day_offset=int(offset)
                )
                latents[seed, beta, int(offset)] = adapter.latent_for(seed, cell)

    # A's requested configs are retained in U1's per-replicate provenance.
    a_records: dict[CandidateCell, list[Mapping[str, Any]]] = {c: [] for c in config.candidate_grid}
    for record in baseline.replicate_provenance:
        a_records[CandidateCell(**record["cell"])].append(record)
    library = {}
    hashes: dict[CandidateCell, str] = {}
    provenance = []
    # Each slice retains the same ordered requested configs as its tables.
    slices = (
        ("A", 0, 3),
        ("B_prime", 3, 6),
        ("C_prime", 6, 9),
        ("D_prime", 9, 12),
        ("A_union_B_prime", 0, 6),
    )
    slice_hashes: dict[str, dict[CandidateCell, str]] = {name: {} for name, _, _ in slices}
    for cell in config.candidate_grid:
        counter.dispatch("cells")
        records = list(a_records[cell])
        tables = list(baseline.candidate_prediction_library[cell])
        if tuple(r["process_seed"] for r in records) != ARM_I_REPLICATE_ORDER[:3]:
            raise CampaignError("baseline batch A replicate order mismatch")
        for record, table in zip(records, tables, strict=True):
            if (
                record["table_sha256"]
                != hashlib.sha256(phase0._compact_json_bytes(table.as_dict())).hexdigest()
            ):
                raise CampaignError("baseline batch A table SHA-256 mismatch")
        for batch, process_seeds, observation_seeds in frozen.CANDIDATE_BATCHES[1:]:
            for seed, obs_seed in zip(process_seeds, observation_seeds, strict=True):
                latent, run_config = latents[seed, cell.beta, cell.inoculation_day_offset]
                observed, obs, table = adapter.observe(
                    latent, run_config, obs_seed, config.candidate_observation_config_id, cell
                )
                tables.append(table)
                record = {
                    "cell": cell.as_dict(),
                    "batch": batch,
                    "process_seed": seed,
                    "observation_seed": obs_seed,
                    "observation_config": obs.model_dump(mode="json"),
                    "run_config": run_config.model_dump(mode="json"),
                    "table_sha256": hashlib.sha256(
                        phase0._compact_json_bytes(table.as_dict())
                    ).hexdigest(),
                    "population_lineage": lineage[seed],
                    "observation_rng": observed.diagnostics["observation_rng"],
                }
                records.append(record)
                provenance.append(record)
        if tuple(r["process_seed"] for r in records) != ARM_I_REPLICATE_ORDER:
            raise CampaignError("arm (i) replicate order mismatch")
        library[cell] = tuple(tables)
        configs = [
            {"run": r["run_config"], "observation": r["observation_config"]} for r in records
        ]
        hashes[cell] = hashlib.sha256(phase0._compact_json_bytes(configs)).hexdigest()
        for name, start, stop in slices:
            slice_hashes[name][cell] = hashlib.sha256(
                phase0._compact_json_bytes(configs[start:stop])
            ).hexdigest()
        if slice_hashes["A"][cell] != baseline.candidate_config_hashes[cell]:
            raise CampaignError("baseline batch A config hash mismatch")
    if not counter.exact():
        raise BudgetError("arm (i) measured work differs from exact i caps")

    fits, paths, file_hashes = {}, {}, {}
    descriptive_fits, descriptive_paths, descriptive_hashes = {}, {}, {}
    descriptive_counter = DescriptiveLossCounter(plan["descriptive_loss_evaluations"])
    target_descriptives = []
    agreement = 0
    started = time.perf_counter()
    for seed, target in baseline.target_tables.items():
        fit = fit_blind(
            target, config.candidate_grid, library, R=12, T=34, candidate_config_hashes=hashes
        )
        path = work_dir / "blind_estimates" / f"{seed}.json"
        fits[seed], paths[seed], file_hashes[seed] = fit, path, _persist_fit(path, fit)
        target_fits = {"all_twelve": fit}
        for name, start, stop in slices:
            batch_library = {cell: tables[start:stop] for cell, tables in library.items()}
            batch_fit = fit_blind(
                target,
                config.candidate_grid,
                batch_library,
                R=stop - start,
                T=34,
                candidate_config_hashes=slice_hashes[name],
            )
            descriptive_counter.record(batch_fit)
            if name == "A" and batch_fit.loss_surface != baseline.blind_fits[seed].loss_surface:
                raise CampaignError(
                    "batch A descriptive surface differs from baseline gate surface"
                )
            path = work_dir / "descriptive_estimates" / name / f"{seed}.json"
            key = (seed, name)
            descriptive_fits[key], descriptive_paths[key] = batch_fit, path
            descriptive_hashes[key] = _persist_fit(path, batch_fit)
            target_fits[name] = batch_fit
        single_batches = [target_fits[name] for name, _, _ in slices[:4]]
        agrees = batch_offset_agreement(single_batches)
        agreement += int(agrees)
        target_descriptives.append(
            {
                "target_seed": seed,
                "four_batch_offsets_agree": agrees,
                "reprofiled_offsets": {
                    name: {
                        "selected_offset": None
                        if result.selected is None
                        else result.selected.inoculation_day_offset,
                        "numerical_tie": result.numerical_tie,
                        "estimate_hash": result.estimate_hash,
                        "profile": next(
                            p.as_dict()
                            for p in result.profiles
                            if p.dimension == "inoculation_day_offset"
                        ),
                    }
                    for name, result in target_fits.items()
                },
                "fixed_tuple_spreads": [
                    {
                        "cell": cell.as_dict(),
                        **batch_objective_spread(
                            [f.loss_surface[index].objective for f in single_batches]
                        ),
                    }
                    for index, cell in enumerate(config.candidate_grid)
                ],
            }
        )
    descriptive_counter.check_exact()
    phase_seconds["scoring"] += time.perf_counter() - started
    descriptives = {
        "label": STOCHASTIC_REPLICATE_VARIATION,
        "median_definition": "arithmetic mean of the middle two of four sorted batch objectives",
        "replicate_order": list(ARM_I_REPLICATE_ORDER),
        "descriptive_loss_evaluations": descriptive_counter.measured,
        "four_batch_offset_agreement_count": agreement,
        "targets": target_descriptives,
    }
    work_dir.mkdir(parents=True, exist_ok=True)
    descriptives_path = work_dir / "g35b_i_descriptives.json"
    content = phase0._compact_json_bytes(descriptives)
    descriptives_path.write_bytes(content)
    if descriptives_path.read_bytes() != content:
        raise CampaignError("arm (i) descriptives read-back mismatch")
    return ArmIGeneration(
        baseline,
        library,
        latents,
        parents,
        lineage,
        hashes,
        tuple(provenance),
        fits,
        paths,
        file_hashes,
        descriptive_fits,
        descriptive_paths,
        descriptive_hashes,
        descriptives,
        descriptives_path,
        hashlib.sha256(content).hexdigest(),
        dict(counter.measured),
        {
            "phase_wall_time_seconds": phase_seconds,
            "latent_runtimes": runtimes,
            "fallback_source": frozen.CLARIFICATION_PATH,
            "fallback_built_targets": baseline.disclosures["fallback_built_targets"],
            "fallback_built_candidates": baseline.disclosures["fallback_built_candidates"]
            + sum(
                any(lineage[s][key] for key in ("population_fallback_m2", "population_fallback_m3"))
                for s in extra_seeds
            ),
            "measured_counters": dict(counter.measured),
        },
    )


def join_arm_i(generation: ArmIGeneration, output_dir: Path) -> RecoveryEvaluation:
    """Re-verify every blind record, then join B's target truth to R=12 fits."""
    baseline = generation.baseline
    config = baseline.config
    plan = plan_workload(config)
    for seed in config.target_process_seeds:
        for result in (baseline, generation):
            _verify_blind_readback(
                result.blind_paths[seed], result.blind_fits[seed], result.blind_file_hashes[seed]
            )
        for batch, _, _ in frozen.CANDIDATE_BATCHES:
            key = (seed, batch)
            _verify_blind_readback(
                generation.descriptive_paths[key],
                generation.descriptive_fits[key],
                generation.descriptive_file_hashes[key],
            )
        key = (seed, "A_union_B_prime")
        _verify_blind_readback(
            generation.descriptive_paths[key],
            generation.descriptive_fits[key],
            generation.descriptive_file_hashes[key],
        )
    try:
        content = generation.descriptives_path.read_bytes()
        if (
            hashlib.sha256(content).hexdigest() != generation.descriptives_file_hash
            or json.loads(content) != generation.descriptives
        ):
            raise CampaignError("arm (i) descriptives read-back mismatch")
    except (OSError, ValueError) as exc:
        raise CampaignError(f"arm (i) descriptives read-back failed: {exc}") from exc
    rows = []
    for seed in config.target_process_seeds:
        latent, observed, requested_run, requested_observation = baseline.target_outputs[seed]
        namespace = _namespace_passes(latent, observed, requested_run, requested_observation)
        diagnostics = _truth_diagnostics_from_result(
            latent, observed, baseline.target_tables[seed], namespace_passed=namespace
        )
        fit = generation.blind_fits[seed]
        rows.append(
            RecoveryRow(
                seed,
                fit.estimate_hash,
                fit.selected,
                fit.profiles,
                fit.numerical_tie,
                CandidateCell(0.08, 2, 0.75, 0.25),
                diagnostics,
                namespace,
                len(fit.loss_surface),
            )
        )
    complete = (
        _baseline_execution_complete(baseline)
        and set(generation.generated_parents) == set(ARM_I_REPLICATE_ORDER[3:])
        and set(generation.candidate_latents)
        == {
            (seed, beta, int(offset))
            for seed in ARM_I_REPLICATE_ORDER[3:]
            for beta in config.dimensions[0].candidates
            for offset in config.dimensions[1].candidates
        }
        and set(generation.candidate_prediction_library) == set(config.candidate_grid)
        and all(len(tables) == 12 for tables in generation.candidate_prediction_library.values())
    )
    evaluation = evaluate_recovery(
        rows,
        execution_complete=complete,
        provenance_verified=True,
        measured_equals_caps=generation.measured
        == {key: plan["arms"]["i"][key] for key in TOTAL_FIELDS},
    )
    # A10 / clarification 1 item 2: fallback columns are attached after gating.
    serial = tuple(
        {
            **row,
            **{
                key: str(bool(baseline.parent_lineage[row["target_seed"]][key])).upper()
                for key in ("population_fallback_m2", "population_fallback_m3")
            },
        }
        for row in evaluation.rows
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "g35b_i_recovery.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(serial[0]))
        writer.writeheader()
        writer.writerows(serial)
    (output_dir / "g35b_i_descriptives.json").write_bytes(content)
    (output_dir / "g35b_i_disclosures.json").write_bytes(
        phase0._compact_json_bytes(generation.disclosures)
    )
    return replace(evaluation, rows=serial)


@dataclass(frozen=True)
class _ArmIIConstructorConfig(StudyConfig):
    """Constructor-only horizon; the study declaration and B remain at 30 days."""

    duration_days: int = next(row[2] for row in frozen.ARM_CAPS if row[0] == "ii")

    def __post_init__(self) -> None:
        if type(self.duration_days) is not int or self.duration_days != 49:
            raise BudgetError("arm (ii) requires frozen H = 49")
        if len(observation_dates(self.start_date, self.duration_days, 4)) != 53:
            raise BudgetError("arm (ii) requires the frozen 53-date calendar")


@dataclass(frozen=True)
class ArmIIGeneration(BaselineGeneration):
    """Own 49-day results and blind fits, retaining B solely for the later join."""

    baseline: BaselineGeneration


def arm_ii(
    baseline: BaselineGeneration,
    config: StudyConfig,
    work_dir: Path,
    *,
    root: Path,
) -> ArmIIGeneration:
    """Extend B's streams to frozen H, without reading any target latent truth."""
    arm_started = time.perf_counter()
    plan = plan_workload(config)
    constructor_config = _ArmIIConstructorConfig(duration_days=plan["arms"]["ii"]["latent_days"])
    expected_b = {key: plan["arms"]["B"][key] for key in TOTAL_FIELDS}
    if (
        baseline.config != config
        or baseline.measured != expected_b
        or not _baseline_execution_complete(baseline)
    ):
        raise CampaignError("arm (ii) requires completed baseline generation and all 13 parents")
    for seed in config.target_process_seeds:
        _verify_blind_readback(
            baseline.blind_paths[seed], baseline.blind_fits[seed], baseline.blind_file_hashes[seed]
        )
    # These are B's actual objects, not rebuilt or copied populations.
    parents = baseline.generated_parents
    lineage = baseline.parent_lineage
    counter = WorkCounter("ii")
    phase_seconds = {key: 0.0 for key in ("build", "latent", "transform", "scoring")}
    runtimes: list[dict[str, Any]] = []
    adapter = _GenerationAdapter(
        constructor_config,
        root,
        load_parameter_set(root),
        parents,
        counter,
        phase_seconds,
        runtimes,
    )
    truth_cell = CandidateCell(0.08, 2, 0.75, 0.25)
    targets, outputs = {}, {}
    for seed, obs_seed in zip(
        config.target_process_seeds, config.target_observation_seeds, strict=True
    ):
        # The adapter requires returned result.config == requested config (H = 49)
        # and result.generated is the exact shared parent; absent metadata fails.
        latent, run_config = adapter.latent_for(seed, truth_cell)
        observed, obs, table = adapter.observe(
            latent, run_config, obs_seed, config.target_observation_config_id, truth_cell
        )
        targets[seed] = table
        outputs[seed] = (latent, observed, run_config, obs)
    latents = {}
    for seed in config.candidate_process_seeds:
        for beta in config.dimensions[0].candidates:
            for offset in config.dimensions[1].candidates:
                cell = replace(
                    config.candidate_grid[0], beta=beta, inoculation_day_offset=int(offset)
                )
                latents[seed, beta, int(offset)] = adapter.latent_for(seed, cell)
    library, hashes = {}, {}
    provenance = []
    for cell in config.candidate_grid:
        counter.dispatch("cells")
        tables, configs = [], []
        for seed, obs_seed in zip(
            config.candidate_process_seeds, config.candidate_observation_seeds, strict=True
        ):
            latent, run_config = latents[seed, cell.beta, cell.inoculation_day_offset]
            observed, obs, table = adapter.observe(
                latent, run_config, obs_seed, config.candidate_observation_config_id, cell
            )
            tables.append(table)
            run_payload, obs_payload = (
                run_config.model_dump(mode="json"),
                obs.model_dump(mode="json"),
            )
            configs.append({"run": run_payload, "observation": obs_payload})
            provenance.append(
                {
                    "cell": cell.as_dict(),
                    "batch": "A",
                    "process_seed": seed,
                    "observation_seed": obs_seed,
                    "run_config": run_payload,
                    "observation_config": obs_payload,
                    "table_sha256": hashlib.sha256(
                        phase0._compact_json_bytes(table.as_dict())
                    ).hexdigest(),
                    "population_lineage": lineage[seed],
                    "observation_rng": observed.diagnostics["observation_rng"],
                }
            )
        library[cell] = tuple(tables)
        hashes[cell] = hashlib.sha256(phase0._compact_json_bytes(configs)).hexdigest()
    if not counter.exact():
        raise BudgetError("arm (ii) measured work differs from exact ii caps")
    fits, paths, file_hashes = {}, {}, {}
    started = time.perf_counter()
    for seed, table in targets.items():
        fit = fit_blind(
            table, config.candidate_grid, library, R=3, T=53, candidate_config_hashes=hashes
        )
        path = work_dir / "arm_ii" / "blind_estimates" / f"{seed}.json"
        fits[seed], paths[seed], file_hashes[seed] = fit, path, _persist_fit(path, fit)
    phase_seconds["scoring"] += time.perf_counter() - started
    return ArmIIGeneration(
        config,
        targets,
        outputs,
        library,
        latents,
        parents,
        lineage,
        hashes,
        tuple(provenance),
        fits,
        paths,
        file_hashes,
        dict(counter.measured),
        {
            "arm_wall_time_seconds": time.perf_counter() - arm_started,
            "phase_wall_time_seconds": phase_seconds,
            "latent_runtimes": runtimes,
            "fallback_source": frozen.CLARIFICATION_PATH,
            "fallback_built_targets": baseline.disclosures["fallback_built_targets"],
            "fallback_built_candidates": baseline.disclosures["fallback_built_candidates"],
            "measured_counters": dict(counter.measured),
        },
        baseline,
    )


def prefix_identity(
    baseline_events: Sequence[Mapping[str, Any]],
    extended_events: Sequence[Mapping[str, Any]],
    baseline_table: ObservedTables,
    extended_table: ObservedTables,
    *,
    start_date: date,
) -> dict[str, Any]:
    """Canonical sorted event rows and zero-filled date/channel counts through day 29.

    Hash every retained event field, using the same compact, sorted-key JSON
    serialization for both runs. Later infections and reports are excluded.
    A realization mismatch is descriptive only (§4.2 step 5).
    """
    last = (start_date + timedelta(days=29)).isoformat()

    def event_hash(events: Sequence[Mapping[str, Any]]) -> str:
        rows = [dict(event) for event in events if str(event["infection_date"]) <= last]
        rows.sort(key=phase0._compact_json_bytes)
        return hashlib.sha256(phase0._compact_json_bytes(rows)).hexdigest()

    def report_hash(table: ObservedTables) -> str:
        rows = sorted(
            (when, channel, count)
            for channel, values in zip(
                ("symptomatic", "asymptomatic"), table.channel_values, strict=True
            )
            for when, count in zip(table.dates, values, strict=True)
            if when <= last
        )
        return hashlib.sha256(phase0._compact_json_bytes(rows)).hexdigest()

    events = {"B": event_hash(baseline_events), "ii": event_hash(extended_events)}
    reports = {"B": report_hash(baseline_table), "ii": report_hash(extended_table)}
    identical = events["B"] == events["ii"] and reports["B"] == reports["ii"]
    return {
        "prefix_last_date": last,
        "transmission_sha256": events,
        "report_count_sha256": reports,
        "result": "identical" if identical else "not identical",
        "label": "identical" if identical else "seed-stream matched, realization not matched",
    }


def manipulation_check(daily_epidemic: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Earliest maximum of the 7-day trailing incidence sum; disclosure only."""
    H = _ArmIIConstructorConfig().duration_days
    if len(daily_epidemic) != H:
        raise CampaignError("arm (ii) manipulation check requires 49 daily rows")
    daily = [row["new_infections"] for row in daily_epidemic]
    if any(not math.isfinite(value) or value < 0 for value in daily):
        raise CampaignError("invalid daily new_infections")
    trailing = [sum(daily[max(0, t - 6) : t + 1]) for t in range(H)]
    p = trailing.index(max(trailing))
    return {"latent_peak_day": p, "peak_crossed": p <= H - 8}


def join_arm_ii(generation: ArmIIGeneration, output_dir: Path) -> RecoveryEvaluation:
    """Re-read all blind estimates, then join this arm's own 49-day truth."""
    config = generation.config
    plan = plan_workload(config)
    constructor_config = _ArmIIConstructorConfig(duration_days=plan["arms"]["ii"]["latent_days"])
    for seed in config.target_process_seeds:
        _verify_blind_readback(
            generation.blind_paths[seed],
            generation.blind_fits[seed],
            generation.blind_file_hashes[seed],
        )
    rows = []
    for seed in config.target_process_seeds:
        latent, observed, requested_run, requested_observation = generation.target_outputs[seed]
        namespace = _namespace_passes(latent, observed, requested_run, requested_observation)
        diagnostics = _truth_diagnostics_from_result(
            latent, observed, generation.target_tables[seed], namespace_passed=namespace
        )
        fit = generation.blind_fits[seed]
        rows.append(
            RecoveryRow(
                seed,
                fit.estimate_hash,
                fit.selected,
                fit.profiles,
                fit.numerical_tie,
                CandidateCell(0.08, 2, 0.75, 0.25),
                diagnostics,
                namespace,
                len(fit.loss_surface),
            )
        )
    dates = observation_dates(config.start_date, constructor_config.duration_days, 4)
    provenance_verified = (
        all(table.dates == dates for table in generation.target_tables.values())
        and all(
            table.dates == dates
            for tables in generation.candidate_prediction_library.values()
            for table in tables
        )
        and all(
            latent.config.duration_days == 49 for latent, _ in generation.candidate_latents.values()
        )
        and all(
            output[0].config.duration_days == 49 for output in generation.target_outputs.values()
        )
    )
    complete = _baseline_execution_complete(generation) and all(
        generation.generated_parents[seed] is generation.baseline.generated_parents[seed]
        for seed in generation.generated_parents
    )
    evaluation = evaluate_recovery(
        rows,
        execution_complete=complete,
        provenance_verified=provenance_verified,
        measured_equals_caps=generation.measured
        == {key: plan["arms"]["ii"][key] for key in TOTAL_FIELDS},
    )
    # Descriptive truth access occurs only after the gate; neither check is an input.
    targets = []
    for seed in config.target_process_seeds:
        latent = generation.target_outputs[seed][0]
        targets.append(
            {
                "target_seed": seed,
                "prefix_identity": prefix_identity(
                    generation.baseline.target_outputs[seed][0].transmission_events,
                    latent.transmission_events,
                    generation.baseline.target_tables[seed],
                    generation.target_tables[seed],
                    start_date=config.start_date,
                ),
                **manipulation_check(latent.daily_epidemic),
            }
        )
    delivered = sum(target["peak_crossed"] for target in targets)
    descriptives = {
        "targets": targets,
        "factor_delivered": f"factor delivered for {delivered}/10 targets",
    }
    # A10 / clarification 1 item 2: the shared parents' fallbacks never gate.
    serial = tuple(
        {
            **row,
            **{
                key: str(bool(generation.parent_lineage[row["target_seed"]][key])).upper()
                for key in ("population_fallback_m2", "population_fallback_m3")
            },
        }
        for row in evaluation.rows
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "g35b_ii_recovery.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(serial[0]))
        writer.writeheader()
        writer.writerows(serial)
    (output_dir / "g35b_ii_descriptives.json").write_bytes(phase0._compact_json_bytes(descriptives))
    (output_dir / "g35b_ii_disclosures.json").write_bytes(
        phase0._compact_json_bytes(generation.disclosures)
    )
    return replace(evaluation, rows=serial)


@dataclass(frozen=True)
class SerosurveySample:
    """One ideal-assay observation, retaining the full sampled resident evidence."""

    process_seed: int
    serosurvey_seed: int
    config_id: str
    survey_date: str
    sampled_agent_ids: tuple[str, ...]
    ever_infected: tuple[bool, ...]
    k: int
    n: int


def serosurvey_sample_ids(
    agent_ids: Sequence[str], process_seed: int, serosurvey_seed: int, config_id: str, n: int
) -> tuple[str, ...]:
    """A5 byte-exact seed-only SHA-256 ordering, independent of epidemic events."""
    if (
        type(n) is not int
        or not 0 < n <= len(agent_ids)
        or len(set(agent_ids)) != len(agent_ids)
        or any(not isinstance(agent_id, str) for agent_id in agent_ids)
        or type(process_seed) is not int
        or type(serosurvey_seed) is not int
    ):
        raise CampaignError("invalid serosurvey sampling frame, n or seeds")
    return tuple(
        sorted(
            agent_ids,
            key=lambda agent_id: hashlib.sha256(
                f"{process_seed}|{serosurvey_seed}|{config_id}|serosurvey|{agent_id}".encode()
            ).hexdigest(),
        )[:n]
    )


def observe_serosurvey(
    latent: Any,
    *,
    process_seed: int,
    serosurvey_seed: int,
    config_id: str,
    n: int,
    survey_date: date,
) -> SerosurveySample:
    """Perfect assay, zero lag: some episode by d means ever infected, once per ID."""
    ids = serosurvey_sample_ids(
        latent.generated.agent_ids, process_seed, serosurvey_seed, config_id, n
    )
    infected = {
        event["infected_agent_id"]
        for event in latent.transmission_events
        if date.fromisoformat(event["infection_date"]) <= survey_date
    }
    flags = tuple(agent_id in infected for agent_id in ids)
    return SerosurveySample(
        process_seed, serosurvey_seed, config_id, survey_date.isoformat(), ids, flags, sum(flags), n
    )


def anscombe_z(k: int, n: int) -> float:
    """Frozen §6 binomial Anscombe transform, with no fitted assay parameters."""
    if type(n) is not int or type(k) is not int or n < 1 or not 0 <= k <= n:
        raise CampaignError("serosurvey requires integer 0 <= k <= n and n > 0")
    return math.sqrt(n + 1 / 2) * math.asin(math.sqrt((k + 3 / 8) / (n + 3 / 4)))


def serosurvey_squared_residual(target_k: int, n: int, candidate_ks: Sequence[int]) -> float:
    if len(candidate_ks) != 3:
        raise CampaignError("serosurvey requires three ordered candidate replicates")
    mean_z = sum(anscombe_z(k, n) for k in candidate_ks) / 3
    return (anscombe_z(target_k, n) - mean_z) ** 2


def augmented_loss(
    target: ObservedTables,
    predictions: Sequence[ObservedTables],
    target_k: int,
    n: int,
    candidate_ks: Sequence[int],
) -> float:
    """Literal L^rep + S/(2T), preserving report-loss floating-point arithmetic."""
    S = serosurvey_squared_residual(target_k, n, candidate_ks)
    return loss(target, predictions, R=3, T=34) + S / (2 * 34)


def fit_blind_serosurvey(
    target_tables: ObservedTables,
    target_k: int,
    n: int,
    candidate_grid: Sequence[CandidateCell],
    candidate_prediction_library: Mapping[CandidateCell, Sequence[ObservedTables]],
    candidate_k_library: Mapping[CandidateCell, Sequence[int]],
) -> BlindFitResult:
    """Blind arm-(iii) boundary: observed tables/counts only; no seeds or latent runs."""
    if set(candidate_k_library) != set(candidate_grid):
        raise CampaignError("candidate serosurvey library is incomplete")
    return _fit_scored_grid(
        candidate_grid,
        candidate_prediction_library,
        lambda cell: augmented_loss(
            target_tables,
            candidate_prediction_library[cell],
            target_k,
            n,
            candidate_k_library[cell],
        ),
    )


def _serosurvey_design() -> dict[str, Any]:
    # These settings and IDs already live in U1's independent frozen payload.
    payload = frozen_payload()
    return {
        **payload["serosurvey"],
        **{
            key: payload["seeds"][key]
            for key in (
                "target_serosurvey_seeds",
                "candidate_serosurvey_seeds",
                "target_serosurvey_config_id",
                "candidate_serosurvey_config_id",
            )
        },
    }


@dataclass(frozen=True)
class ArmIIIGeneration:
    """B is retained by identity; only the serosurvey observations and fits are new."""

    baseline: BaselineGeneration
    design: Mapping[str, Any]
    target_samples: Mapping[int, SerosurveySample]
    candidate_samples: Mapping[tuple[int, float, int], SerosurveySample]
    candidate_k_library: Mapping[CandidateCell, tuple[int, ...]]
    blind_fits: Mapping[int, BlindFitResult]
    blind_paths: Mapping[int, Path]
    blind_file_hashes: Mapping[int, str]
    samples_path: Path
    samples_file_hash: str
    measured: Mapping[str, int]
    disclosures: Mapping[str, Any]


def _serosurvey_records(generation: ArmIIIGeneration) -> dict[str, Any]:
    return {
        "design": generation.design,
        "targets": [asdict(sample) for sample in generation.target_samples.values()],
        "candidates": [
            {"beta": beta, "offset": offset, **asdict(sample)}
            for (_, beta, offset), sample in generation.candidate_samples.items()
        ],
    }


def arm_iii(
    baseline: BaselineGeneration,
    config: StudyConfig,
    work_dir: Path,
    *,
    root: Path,
) -> ArmIIIGeneration:
    """Observe B's ten targets and 75 latents, then persist ten augmented blind fits."""
    started = time.perf_counter()
    plan = plan_workload(config)
    if (
        baseline.config != config
        or baseline.measured != {key: plan["arms"]["B"][key] for key in TOTAL_FIELDS}
        or not _baseline_execution_complete(baseline)
    ):
        raise CampaignError("arm (iii) requires completed baseline generation")
    for seed in config.target_process_seeds:
        _verify_blind_readback(
            baseline.blind_paths[seed], baseline.blind_fits[seed], baseline.blind_file_hashes[seed]
        )
    # A fresh arm namespace prevents overwriting any arm, including a prior iii attempt.
    destination = work_dir / "arm_iii"
    destination.mkdir(parents=True, exist_ok=False)
    counter = WorkCounter("iii")
    design = _serosurvey_design()
    survey_date = config.start_date + timedelta(days=design["survey_day"])

    def sample(
        latent: Any, requested: Any, seed: int, sero_seed: int, config_id: str
    ) -> SerosurveySample:
        if (
            latent.config != requested
            or latent.config.seed != seed
            or latent.config.start_date != config.start_date
            or latent.config.duration_days != config.duration_days
            or latent.generated is not baseline.generated_parents[seed]
        ):
            raise CampaignError("serosurvey latent metadata differs from baseline")
        counter.dispatch("serosurvey_samples")
        return observe_serosurvey(
            latent,
            process_seed=seed,
            serosurvey_seed=sero_seed,
            config_id=config_id,
            n=design["n"],
            survey_date=survey_date,
        )

    targets = {}
    for seed, sero_seed in zip(
        config.target_process_seeds, design["target_serosurvey_seeds"], strict=True
    ):
        latent, _, requested, _ = baseline.target_outputs[seed]
        targets[seed] = sample(
            latent, requested, seed, sero_seed, design["target_serosurvey_config_id"]
        )
    candidates = {}
    for seed, sero_seed in zip(
        config.candidate_process_seeds, design["candidate_serosurvey_seeds"], strict=True
    ):
        common_ids = None
        for beta in config.dimensions[0].candidates:
            for offset in config.dimensions[1].candidates:
                key = (seed, beta, int(offset))
                latent, requested = baseline.candidate_latents[key]
                observation = sample(
                    latent, requested, seed, sero_seed, design["candidate_serosurvey_config_id"]
                )
                ids = frozenset(observation.sampled_agent_ids)
                if common_ids is not None and ids != common_ids:
                    raise CampaignError("serosurvey common random numbers mismatch across cells")
                common_ids = ids
                candidates[key] = observation
    sampling_seconds = time.perf_counter() - started
    library = {}
    for cell in config.candidate_grid:
        counter.dispatch("cells")
        library[cell] = tuple(
            candidates[seed, cell.beta, cell.inoculation_day_offset].k
            for seed in config.candidate_process_seeds
        )
    if not counter.exact():
        raise BudgetError("arm (iii) measured work differs from exact iii caps")
    fits, paths, hashes = {}, {}, {}
    scoring_started = time.perf_counter()
    for seed, table in baseline.target_tables.items():
        fit = fit_blind_serosurvey(
            table,
            targets[seed].k,
            design["n"],
            config.candidate_grid,
            baseline.candidate_prediction_library,
            library,
        )
        path = destination / "blind_estimates" / f"{seed}.json"
        fits[seed], paths[seed], hashes[seed] = fit, path, _persist_fit(path, fit)
    scoring_seconds = time.perf_counter() - scoring_started
    generation = ArmIIIGeneration(
        baseline,
        design,
        targets,
        candidates,
        library,
        fits,
        paths,
        hashes,
        destination / "serosurvey_samples.json",
        "",
        dict(counter.measured),
        {
            "arm_wall_time_seconds": time.perf_counter() - started,
            "phase_wall_time_seconds": {
                "build": 0.0,
                "latent": 0.0,
                "transform": 0.0,
                "serosurvey": sampling_seconds,
                "scoring": scoring_seconds,
            },
            "latent_runtimes": [],
            "fallback_source": frozen.CLARIFICATION_PATH,
            "fallback_built_targets": baseline.disclosures["fallback_built_targets"],
            "fallback_built_candidates": baseline.disclosures["fallback_built_candidates"],
            "measured_counters": dict(counter.measured),
        },
    )
    content = phase0._compact_json_bytes(_serosurvey_records(generation))
    generation.samples_path.write_bytes(content)
    if generation.samples_path.read_bytes() != content:
        raise CampaignError("serosurvey samples read-back mismatch")
    return replace(generation, samples_file_hash=hashlib.sha256(content).hexdigest())


def _serosurvey_provenance_verified(generation: ArmIIIGeneration) -> bool:
    baseline = generation.baseline
    config = baseline.config
    design = _serosurvey_design()
    dates = observation_dates(config.start_date, config.duration_days, 4)
    if (
        generation.design != design
        or len(dates) != 34
        or any(table.dates != dates for table in baseline.target_tables.values())
        or any(
            table.dates != dates
            for tables in baseline.candidate_prediction_library.values()
            for table in tables
        )
        or set(generation.target_samples) != set(frozen.TARGET_PROCESS_SEEDS)
        or set(generation.candidate_samples) != set(baseline.candidate_latents)
        or len(generation.candidate_samples) != 75
        or generation.measured.get("serosurvey_samples") != 85
    ):
        return False
    survey_date = (config.start_date + timedelta(days=design["survey_day"])).isoformat()
    for records, seeds, sero_seeds, namespace in (
        (
            tuple(generation.target_samples.items()),
            config.target_process_seeds,
            design["target_serosurvey_seeds"],
            design["target_serosurvey_config_id"],
        ),
        (
            tuple((key[0], sample) for key, sample in generation.candidate_samples.items()),
            config.candidate_process_seeds,
            design["candidate_serosurvey_seeds"],
            design["candidate_serosurvey_config_id"],
        ),
    ):
        paired = dict(zip(seeds, sero_seeds, strict=True))
        for expected_seed, observation in records:
            if (
                observation.process_seed != expected_seed
                or observation.process_seed not in paired
                or observation.serosurvey_seed != paired[observation.process_seed]
                or observation.config_id != namespace
                or observation.survey_date != survey_date
                or observation.n != design["n"]
                or len(observation.ever_infected) != design["n"]
                or observation.k != sum(observation.ever_infected)
                or observation.sampled_agent_ids
                != serosurvey_sample_ids(
                    baseline.generated_parents[observation.process_seed].agent_ids,
                    observation.process_seed,
                    observation.serosurvey_seed,
                    namespace,
                    design["n"],
                )
            ):
                return False
    return set(generation.candidate_k_library) == set(config.candidate_grid) and all(
        generation.candidate_k_library[cell]
        == tuple(
            generation.candidate_samples[seed, cell.beta, cell.inoculation_day_offset].k
            for seed in config.candidate_process_seeds
        )
        for cell in config.candidate_grid
    )


def join_arm_iii(generation: ArmIIIGeneration, output_dir: Path) -> RecoveryEvaluation:
    """Re-verify blind records first; join B's truth, gate, then compute A7 disclosures."""
    baseline = generation.baseline
    config = baseline.config
    plan = plan_workload(config)
    for seed in config.target_process_seeds:
        _verify_blind_readback(
            generation.blind_paths[seed],
            generation.blind_fits[seed],
            generation.blind_file_hashes[seed],
        )
    try:
        content = generation.samples_path.read_bytes()
        if hashlib.sha256(
            content
        ).hexdigest() != generation.samples_file_hash or content != phase0._compact_json_bytes(
            _serosurvey_records(generation)
        ):
            raise CampaignError("serosurvey samples read-back mismatch")
    except OSError as exc:
        raise CampaignError(f"serosurvey samples read-back failed: {exc}") from exc
    rows = []
    for seed in config.target_process_seeds:
        latent, observed, requested_run, requested_observation = baseline.target_outputs[seed]
        namespace = _namespace_passes(latent, observed, requested_run, requested_observation)
        diagnostics = _truth_diagnostics_from_result(
            latent, observed, baseline.target_tables[seed], namespace_passed=namespace
        )
        fit = generation.blind_fits[seed]
        rows.append(
            RecoveryRow(
                seed,
                fit.estimate_hash,
                fit.selected,
                fit.profiles,
                fit.numerical_tie,
                CandidateCell(0.08, 2, 0.75, 0.25),
                diagnostics,
                namespace,
                len(fit.loss_surface),
            )
        )
    evaluation = evaluate_recovery(
        rows,
        execution_complete=_baseline_execution_complete(baseline),
        provenance_verified=_serosurvey_provenance_verified(generation),
        measured_equals_caps=generation.measured
        == {key: plan["arms"]["iii"][key] for key in TOTAL_FIELDS},
    )
    # A7 descriptives are first computed after gating. Decimal(str(fraction))
    # compares the exported daily fraction to exact 0.25 without an epsilon.
    targets = []
    for seed, observation in generation.target_samples.items():
        latent = baseline.target_outputs[seed][0]
        daily = [row for row in latent.daily_epidemic if row["date"] == observation.survey_date]
        if len(daily) != 1:
            raise CampaignError("serosurvey descriptive requires exactly one survey-date daily row")
        fraction = daily[0]["ever_infected_fraction"]
        if not math.isfinite(fraction) or not 0 <= fraction <= 1:
            raise CampaignError("invalid ever-infected fraction")
        fit = generation.blind_fits[seed]
        term = (
            None
            if fit.selected is None
            else serosurvey_squared_residual(
                observation.k, observation.n, generation.candidate_k_library[fit.selected]
            )
            / (2 * 34)
        )
        targets.append(
            {
                "target_seed": seed,
                "k": observation.k,
                "n": observation.n,
                "k_over_n": observation.k / observation.n,
                "z": anscombe_z(observation.k, observation.n),
                "serosurvey_term": term,
                "serosurvey_share_of_loss": None
                if term is None or fit.minimum_objective == 0
                else term / fit.minimum_objective,
                "ever_infected_fraction": fraction,
                "n_criterion_premise_met": Decimal(str(fraction)) >= Decimal("0.25"),
            }
        )
    descriptives = {
        "fraction_comparison": "Decimal(str(exported ever_infected_fraction)) >= Decimal('0.25')",
        "undefined_share": "null for a tied global minimum or zero augmented loss",
        "targets": targets,
        "candidates": [
            {
                "process_seed": seed,
                "beta": beta,
                "offset": offset,
                "k": sample.k,
                "n": sample.n,
                "k_over_n": sample.k / sample.n,
                "z": anscombe_z(sample.k, sample.n),
            }
            for (seed, beta, offset), sample in generation.candidate_samples.items()
        ],
    }
    serial = tuple(
        {
            **row,
            **{
                key: str(bool(baseline.parent_lineage[row["target_seed"]][key])).upper()
                for key in ("population_fallback_m2", "population_fallback_m3")
            },
        }
        for row in evaluation.rows
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "g35b_iii_recovery.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(serial[0]))
        writer.writeheader()
        writer.writerows(serial)
    (output_dir / "g35b_iii_descriptives.json").write_bytes(
        phase0._compact_json_bytes(descriptives)
    )
    (output_dir / "g35b_iii_disclosures.json").write_bytes(
        phase0._compact_json_bytes(generation.disclosures)
    )
    return replace(evaluation, rows=serial)


def dry_run(config_path: Path, predeclaration_path: Path) -> dict[str, Any]:
    config = StudyConfig.from_yaml(config_path)
    digest = validate_predeclaration(predeclaration_path)
    report = {"predeclaration_sha256": digest, **plan_workload(config)}
    print(json.dumps(report, indent=2))
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Frozen G35-B study dry-run (U1)")
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
