"""Frozen G43 declaration, dry-run and post-blind recovery evaluation."""

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
from itertools import product
from pathlib import Path
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]

from . import g43_constants as frozen
from .g35b_design_study import _compare, committed_document_bytes
from .phase0_campaign import (
    P01_ROUTE_IDS,
    BudgetError,
    CampaignError,
    CandidateCell,
    DimensionSpec,
    ProfileDiagnostic,
    TruthDiagnostics,
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
            "population_size": 3000,
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
    n = len(seeds)
    row_seeds = tuple(row.target_seed for row in rows)
    complete_roster = len(row_seeds) == n and set(row_seeds) == set(seeds)
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
    return RecoveryEvaluation(
        shared_panel,
        library_integrity,
        recovery,
        hits,
        joint,
        boundaries,
        means,
        count_margins,
        {name: None if margin is None else str(margin) for name, margin in bias_margins.items()},
        tie_count,
        target_rows,
    )


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
