"""Standalone, blind Phase-0 synthetic-recovery machinery.

This module is deliberately separate from the scalar calibration contracts. It
contains the P0-1 scoring boundary and the frozen Phase-0 workload declaration;
it does not alter, or write through, any existing simulation or calibration
artifact schema.

The campaign executor is intentionally fail-closed in this unit. P0-2 and
P0-3 are required before any arm may run, so importing this module or running
dry-run cannot call a simulator or an observation transform.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]

PREDECLARATION_SHA256 = "ef67fe49903c3984ca98679eb0470878bc25523baca3bc23a63e4ae7d983a104"
P01_GRID_CELLS = 81
P01_TARGET_COUNT = 5
P01_FIT_REPLICATE_COUNT = 3
P01_LATENT_CALLS = 32
P01_OBSERVATION_TRANSFORMS = 248
TOTAL_GRID_CELLS = 198
TOTAL_LATENT_CALLS = 59
TOTAL_OBSERVATION_TRANSFORMS = 599
DISTINCT_NETWORK_SEED_BUILDS = 8
MAX_DURATION_DAYS = 30
PROFILE_GAP = 0.05
TIE_SCALE = 1e-12
PROFILE_DENOMINATOR_FLOOR = 1e-12

P01_DIMENSION_NAMES: tuple[str, ...] = (
    "beta",
    "inoculation_day_offset",
    "symptomatic_detection_probability",
    "asymptomatic_detection_probability",
)
P01_CHANNEL_NAMES: tuple[str, ...] = ("symptomatic", "asymptomatic")
P01_ROUTE_IDS: tuple[str, ...] = (
    "household",
    "school_class",
    "school_cross_class",
    "workplace_team",
    "workplace_transient",
    "care_resident",
    "care_staff",
    "shared_vehicle",
    "bus",
    "community_indoor",
    "community_outdoor",
)
TARGET_PROCESS_SEEDS: tuple[int, ...] = (42001, 42002, 42003, 42004, 42005)
TARGET_OBSERVATION_SEEDS: tuple[int, ...] = (52001, 52002, 52003, 52004, 52005)
FIT_PROCESS_SEEDS: tuple[int, ...] = (43001, 43002, 43003)
FIT_OBSERVATION_SEEDS: tuple[int, ...] = (53001, 53002, 53003)
TARGET_OBSERVATION_CONFIG_ID = "v13-phase0-target"
FIT_OBSERVATION_CONFIG_ID = "v13-phase0-fit"
P01_START_DATE = date(2025, 1, 6)
P01_DURATION_DAYS = 30
P01_TAIL_DAYS = 4


class CampaignError(ValueError):
    """Base error for invalid declarations or pure campaign inputs."""


class BudgetError(CampaignError):
    """Raised when a workload cannot be proven to fit the frozen budget."""


class CampaignBlockedError(RuntimeError):
    """Raised when execution is requested before all arms are implemented."""


@dataclass(frozen=True)
class DimensionSpec:
    """One frozen fitted dimension and its descriptive acceptance limits."""

    name: str
    truth: float
    candidates: tuple[float, ...]
    tolerance: float
    bias_limit: float

    def __post_init__(self) -> None:
        if not self.name or not self.candidates:
            raise CampaignError("dimension names and candidate grids must be non-empty")
        if len(set(self.candidates)) != len(self.candidates):
            raise CampaignError(f"candidate grid for {self.name!r} contains duplicates")
        if self.tolerance < 0 or self.bias_limit < 0:
            raise CampaignError(f"dimension limits for {self.name!r} must be non-negative")


@dataclass(frozen=True)
class CampaignConfig:
    """Validated frozen declaration used by dry-run and the future executor."""

    campaign_id: str
    mode: str
    start_date: date
    duration_days: int
    observation_horizon_tail_days: int
    population_mode: str
    population_size: int
    initial_seed_count: int
    inoculation_attempts: int
    inoculation_schedule: str
    import_schedule: str
    import_rate_per_day: float
    route_multipliers: tuple[tuple[str, float], ...]
    symptomatic_probability: float
    latent_duration_days: float
    infectious_duration_days: float
    waning_enabled: bool
    seasonality: str
    interventions: str
    detection_delay_days: int
    reporting_delay_days: int
    weekday_effect: tuple[float, ...]
    dimensions: tuple[DimensionSpec, ...]
    target_process_seeds: tuple[int, ...]
    target_observation_seeds: tuple[int, ...]
    candidate_process_seeds: tuple[int, ...]
    candidate_observation_seeds: tuple[int, ...]
    target_observation_config_id: str
    candidate_observation_config_id: str
    expected_predeclaration_sha256: str
    implemented_arms: tuple[str, ...]
    required_arms: tuple[str, ...]
    retries: int
    adaptive_grid: bool
    replacement_seeds: bool

    @property
    def dimension_map(self) -> dict[str, DimensionSpec]:
        return {dimension.name: dimension for dimension in self.dimensions}

    @property
    def candidate_grid(self) -> tuple[CandidateCell, ...]:
        dimensions = self.dimension_map
        cells: list[CandidateCell] = []
        for beta in dimensions["beta"].candidates:
            for offset in dimensions["inoculation_day_offset"].candidates:
                for symptomatic in dimensions["symptomatic_detection_probability"].candidates:
                    for asymptomatic in dimensions["asymptomatic_detection_probability"].candidates:
                        cells.append(
                            CandidateCell(
                                beta=beta,
                                inoculation_day_offset=int(offset),
                                symptomatic_detection_probability=symptomatic,
                                asymptomatic_detection_probability=asymptomatic,
                            )
                        )
        return tuple(cells)

    @classmethod
    def from_yaml(cls, path: Path) -> CampaignConfig:
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise CampaignError(f"cannot read campaign config {path}: {exc}") from exc
        if not isinstance(payload, dict):
            raise CampaignError("campaign config must be a YAML mapping")

        def required(name: str) -> Any:
            if name not in payload:
                raise CampaignError(f"campaign config missing {name!r}")
            return payload[name]

        dimensions_payload = required("dimensions")
        if not isinstance(dimensions_payload, dict):
            raise CampaignError("dimensions must be a mapping")
        dimensions: list[DimensionSpec] = []
        for name in P01_DIMENSION_NAMES:
            raw = dimensions_payload.get(name)
            if not isinstance(raw, dict):
                raise CampaignError(f"dimension {name!r} must be a mapping")
            dimensions.append(
                DimensionSpec(
                    name=name,
                    truth=float(raw["truth"]),
                    candidates=tuple(float(value) for value in raw["candidates"]),
                    tolerance=float(raw["tolerance"]),
                    bias_limit=float(raw["bias_limit"]),
                )
            )

        fixed = required("fixed_scenario")
        seeds = required("seeds")
        budget = required("budget_caps")
        implementation = required("implementation")
        if not all(isinstance(value, dict) for value in (fixed, seeds, budget, implementation)):
            raise CampaignError("fixed_scenario, seeds, budget_caps and implementation must map")
        route_multipliers = tuple(
            (str(route), float(value)) for route, value in fixed["route_multipliers"].items()
        )
        config = cls(
            campaign_id=str(required("campaign_id")),
            mode=str(required("mode")),
            start_date=date.fromisoformat(str(required("start_date"))),
            duration_days=int(required("duration_days")),
            observation_horizon_tail_days=int(required("observation_horizon_tail_days")),
            population_mode=str(fixed["population_mode"]),
            population_size=int(fixed["population_size"]),
            initial_seed_count=int(fixed["initial_seed_count"]),
            inoculation_attempts=int(fixed["inoculation_attempts"]),
            inoculation_schedule=str(fixed["inoculation_schedule"]),
            import_schedule=str(fixed["import_schedule"]),
            import_rate_per_day=float(fixed["background_import_rate_per_day"]),
            route_multipliers=route_multipliers,
            symptomatic_probability=float(fixed["symptomatic_probability"]),
            latent_duration_days=float(fixed["latent_duration_days"]),
            infectious_duration_days=float(fixed["infectious_duration_days"]),
            waning_enabled=bool(fixed["waning_enabled"]),
            seasonality=str(fixed["seasonality"]),
            interventions=str(fixed["interventions"]),
            detection_delay_days=int(fixed["detection_delay_days"]),
            reporting_delay_days=int(fixed["reporting_delay_days"]),
            weekday_effect=tuple(float(value) for value in fixed["weekday_effect"]),
            dimensions=tuple(dimensions),
            target_process_seeds=tuple(int(value) for value in seeds["target_process_seeds"]),
            target_observation_seeds=tuple(
                int(value) for value in seeds["target_observation_seeds"]
            ),
            candidate_process_seeds=tuple(int(value) for value in seeds["candidate_process_seeds"]),
            candidate_observation_seeds=tuple(
                int(value) for value in seeds["candidate_observation_seeds"]
            ),
            target_observation_config_id=str(seeds["target_observation_config_id"]),
            candidate_observation_config_id=str(seeds["candidate_observation_config_id"]),
            expected_predeclaration_sha256=str(required("predeclaration_sha256")),
            implemented_arms=tuple(str(value) for value in implementation["implemented_arms"]),
            required_arms=tuple(str(value) for value in implementation["required_arms"]),
            retries=int(implementation["retries"]),
            adaptive_grid=bool(implementation["adaptive_grid"]),
            replacement_seeds=bool(implementation["replacement_seeds"]),
        )
        validate_campaign_config(config, budget_caps=budget)
        return config


@dataclass(frozen=True, order=True)
class CandidateCell:
    """One point on the four-dimensional P0-1 candidate grid."""

    beta: float
    inoculation_day_offset: int
    symptomatic_detection_probability: float
    asymptomatic_detection_probability: float

    def as_dict(self) -> dict[str, float | int]:
        return {
            "beta": self.beta,
            "inoculation_day_offset": self.inoculation_day_offset,
            "symptomatic_detection_probability": self.symptomatic_detection_probability,
            "asymptomatic_detection_probability": self.asymptomatic_detection_probability,
        }


@dataclass(frozen=True)
class ObservedTables:
    """Exactly two zero-filled observed channels on one complete date grid."""

    dates: tuple[str, ...]
    symptomatic: tuple[float, ...]
    asymptomatic: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.dates or len(set(self.dates)) != len(self.dates):
            raise CampaignError("observed tables require a non-empty unique date grid")
        if len(self.symptomatic) != len(self.dates) or len(self.asymptomatic) != len(self.dates):
            raise CampaignError("observed channels must cover the complete date grid")
        for channel in (self.symptomatic, self.asymptomatic):
            if any(not math.isfinite(value) or value < 0 for value in channel):
                raise CampaignError("observed counts must be finite and non-negative")

    @property
    def channel_values(self) -> tuple[tuple[float, ...], tuple[float, ...]]:
        return self.symptomatic, self.asymptomatic

    def as_dict(self) -> dict[str, Any]:
        return {
            "dates": list(self.dates),
            "symptomatic": list(self.symptomatic),
            "asymptomatic": list(self.asymptomatic),
        }


@dataclass(frozen=True)
class LossRow:
    cell: CandidateCell
    objective: float
    config_hash: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.cell.as_dict(),
            "objective": self.objective,
            "config_hash": self.config_hash,
        }


@dataclass(frozen=True)
class ProfileDiagnostic:
    dimension: str
    values: tuple[float, ...]
    profiled_objectives: tuple[float, ...]
    minimum: float
    second_minimum: float | None
    numerical_tie: bool
    relative_gap: float | None
    identified: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "values": list(self.values),
            "profiled_objectives": list(self.profiled_objectives),
            "minimum": self.minimum,
            "second_minimum": self.second_minimum,
            "numerical_tie": self.numerical_tie,
            "relative_gap": self.relative_gap,
            "identified": self.identified,
        }


@dataclass(frozen=True)
class BlindFitResult:
    """Truth-free result written before any target truth metadata is joined."""

    loss_surface: tuple[LossRow, ...]
    minimum_objective: float
    global_minimizers: tuple[CandidateCell, ...]
    numerical_tie: bool
    tie_tolerance: float
    selected: CandidateCell | None
    profiles: tuple[ProfileDiagnostic, ...]
    identified: bool
    estimate_hash: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "loss_surface": [row.as_dict() for row in self.loss_surface],
            "minimum_objective": self.minimum_objective,
            "global_minimizers": [cell.as_dict() for cell in self.global_minimizers],
            "numerical_tie": self.numerical_tie,
            "tie_tolerance": self.tie_tolerance,
            "selected": None if self.selected is None else self.selected.as_dict(),
            "profiles": [profile.as_dict() for profile in self.profiles],
            "identified": self.identified,
            "estimate_hash": self.estimate_hash,
        }


@dataclass(frozen=True)
class TruthDiagnostics:
    """Post-fit truth-run checks; never accepted by the blind fitter."""

    inoculation_acquisitions: int
    local_secondary_infections: int
    symptomatic_reports: int
    asymptomatic_reports: int
    nonzero_combined_report_dates: int
    chronology_passed: bool
    latent_incidence_conservation_passed: bool
    namespace_passed: bool = True
    complete: bool = True

    @property
    def viable(self) -> bool:
        return (
            self.complete
            and self.inoculation_acquisitions == 10
            and self.local_secondary_infections >= 1
            and self.symptomatic_reports >= 1
            and self.asymptomatic_reports >= 1
            and self.nonzero_combined_report_dates >= 3
            and self.chronology_passed
            and self.latent_incidence_conservation_passed
            and self.namespace_passed
        )


@dataclass(frozen=True)
class RecoveryRow:
    """Truth-joined descriptive row created only after a blind estimate is hashed."""

    target_seed: int
    estimate_hash: str
    selected: CandidateCell | None
    profiles: tuple[ProfileDiagnostic, ...]
    numerical_tie: bool
    truth: CandidateCell
    truth_diagnostics: TruthDiagnostics
    namespace_passed: bool = True
    scored_cell_count: int = P01_GRID_CELLS

    def signed_error(self, dimension: str) -> float | None:
        if self.selected is None:
            return None
        return float(getattr(self.selected, dimension) - getattr(self.truth, dimension))

    def absolute_error(self, dimension: str) -> float | None:
        value = self.signed_error(dimension)
        return None if value is None else abs(value)


@dataclass(frozen=True)
class P01Evaluation:
    status: Literal["PASS", "FAIL"]
    predicates: Mapping[str, bool]
    coverage: Mapping[str, float | None]
    bias: Mapping[str, float | None]
    boundary_counts: Mapping[str, int]
    joint_coverage: float | None
    rows: tuple[dict[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "predicates": dict(self.predicates),
            "coverage": dict(self.coverage),
            "bias": dict(self.bias),
            "boundary_counts": dict(self.boundary_counts),
            "joint_coverage": self.joint_coverage,
            "rows": list(self.rows),
        }


@dataclass(frozen=True)
class WorkloadPlan:
    """Calculated counts for the complete, predeclared three-arm campaign."""

    p01_cells: int
    p02_wrong_delay_cells: int
    p02_wrong_regime_cells: int
    p03_cells: int
    total_cells: int
    truth_latent_calls: int
    p01_p02_candidate_latent_calls: int
    p03_latent_calls: int
    total_latent_calls: int
    p01_observation_transforms: int
    total_observation_transforms: int
    distinct_network_seed_builds: int
    duration_days: int
    mode: str

    @property
    def p01_latent_calls(self) -> int:
        return self.truth_latent_calls + self.p01_p02_candidate_latent_calls

    def as_dict(self) -> dict[str, int | str]:
        return {
            "p0_1_grid_cells": self.p01_cells,
            "p0_2_wrong_delay_cells": self.p02_wrong_delay_cells,
            "p0_2_wrong_regime_cells": self.p02_wrong_regime_cells,
            "p0_3_cells": self.p03_cells,
            "total_cells": self.total_cells,
            "truth_latent_outbreak_calls": self.truth_latent_calls,
            "p0_1_p0_2_candidate_latent_outbreak_calls": self.p01_p02_candidate_latent_calls,
            "p0_3_latent_outbreak_calls": self.p03_latent_calls,
            "total_latent_outbreak_calls": self.total_latent_calls,
            "p0_1_latent_calls": self.p01_latent_calls,
            "p0_1_observation_transforms": self.p01_observation_transforms,
            "total_observation_transforms": self.total_observation_transforms,
            "distinct_population_network_seed_builds": self.distinct_network_seed_builds,
            "duration_days": self.duration_days,
            "mode": self.mode,
        }


def _product(values: Iterable[int]) -> int:
    result = 1
    for value in values:
        result *= value
    return result


def validate_campaign_config(config: CampaignConfig, budget_caps: Mapping[str, Any]) -> None:
    """Reject any declaration that departs from the frozen P0-1 contract."""

    if config.mode != "ci":
        raise BudgetError("Phase 0 is declared for mode 'ci' only")
    if config.duration_days > MAX_DURATION_DAYS:
        raise BudgetError("duration exceeds the frozen 30-day cap")
    if (
        config.start_date != P01_START_DATE
        or config.duration_days != P01_DURATION_DAYS
        or config.observation_horizon_tail_days != P01_TAIL_DAYS
    ):
        raise CampaignError(
            "start date, duration and observation tail do not match the declaration"
        )
    if config.population_mode != "ci" or config.population_size != 3000:
        raise CampaignError("population mode or size does not match the declaration")
    if config.initial_seed_count != 0 or config.inoculation_attempts != 10:
        raise CampaignError("initialization is not the frozen zero-seed, ten-attempt scenario")
    if (
        config.inoculation_schedule != "start_date_plus_offset"
        or config.import_schedule != "empty_except_inoculation"
        or config.import_rate_per_day != 0.0
        or config.waning_enabled
    ):
        raise CampaignError("background imports and waning must be disabled")
    if config.symptomatic_probability != 0.6:
        raise CampaignError("symptomatic probability is not the frozen 0.6 scenario value")
    if (
        config.latent_duration_days != 2.0
        or config.infectious_duration_days != 5.0
        or config.seasonality != "absent"
        or config.interventions != "absent"
        or config.detection_delay_days != 0
        or config.reporting_delay_days != 2
        or config.weekday_effect != (1.0,) * 7
    ):
        raise CampaignError("natural-history durations do not match the declaration")
    routes = dict(config.route_multipliers)
    if tuple(routes) != P01_ROUTE_IDS or any(value != 1.0 for value in routes.values()):
        raise CampaignError("all eleven route multipliers must be exactly 1.0")
    if tuple(dimension.name for dimension in config.dimensions) != P01_DIMENSION_NAMES:
        raise CampaignError("fitted dimensions must be the declared four dimensions in order")
    expected = {
        "beta": (0.08, (0.04, 0.08, 0.12), 0.04, 0.02),
        "inoculation_day_offset": (2.0, (0.0, 2.0, 4.0), 2.0, 1.0),
        "symptomatic_detection_probability": (0.75, (0.5, 0.75, 1.0), 0.25, 0.125),
        "asymptomatic_detection_probability": (0.25, (0.1, 0.25, 0.4), 0.15, 0.075),
    }
    for dimension in config.dimensions:
        truth, candidates, tolerance, bias_limit = expected[dimension.name]
        if (
            dimension.truth,
            dimension.candidates,
            dimension.tolerance,
            dimension.bias_limit,
        ) != (truth, candidates, tolerance, bias_limit):
            raise CampaignError(f"frozen numerical declaration changed for {dimension.name!r}")
    if config.target_process_seeds != TARGET_PROCESS_SEEDS:
        raise CampaignError("target process seed schedule does not match the declaration")
    if config.target_observation_seeds != TARGET_OBSERVATION_SEEDS:
        raise CampaignError("target observation seed schedule does not match the declaration")
    if config.candidate_process_seeds != FIT_PROCESS_SEEDS:
        raise CampaignError("candidate process seed schedule does not match the declaration")
    if config.candidate_observation_seeds != FIT_OBSERVATION_SEEDS:
        raise CampaignError("candidate observation seed schedule does not match the declaration")
    if config.target_observation_config_id != TARGET_OBSERVATION_CONFIG_ID:
        raise CampaignError("target observation namespace does not match the declaration")
    if config.candidate_observation_config_id != FIT_OBSERVATION_CONFIG_ID:
        raise CampaignError("candidate observation namespace does not match the declaration")
    if config.expected_predeclaration_sha256 != PREDECLARATION_SHA256:
        raise CampaignError("predeclaration SHA-256 does not match the frozen document")
    if len(config.target_process_seeds) != len(config.target_observation_seeds):
        raise CampaignError("target process and observation seeds must be paired")
    if len(config.candidate_process_seeds) != len(config.candidate_observation_seeds):
        raise CampaignError("candidate process and observation seeds must be paired")
    seed_sets = (
        set(config.target_process_seeds),
        set(config.target_observation_seeds),
        set(config.candidate_process_seeds),
        set(config.candidate_observation_seeds),
    )
    if any(
        left & right for index, left in enumerate(seed_sets) for right in seed_sets[index + 1 :]
    ):
        raise BudgetError("seed namespaces overlap")
    if config.retries != 0 or config.adaptive_grid or config.replacement_seeds:
        raise BudgetError("retries, adaptive grids and replacement seeds are forbidden")
    if config.required_arms != ("p0_1", "p0_2a", "p0_2b", "p0_3"):
        raise CampaignError("required arm declaration is incomplete or reordered")
    if config.implemented_arms != ("p0_1",):
        raise CampaignError("this unit must declare only P0-1 as implemented")
    plan = plan_workload(config)
    cap_names = {
        "p0_1_grid_cells": plan.p01_cells,
        "p0_2_wrong_delay_cells": plan.p02_wrong_delay_cells,
        "p0_2_wrong_regime_cells": plan.p02_wrong_regime_cells,
        "p0_3_cells": plan.p03_cells,
        "total_cells": plan.total_cells,
        "truth_latent_outbreak_calls": plan.truth_latent_calls,
        "p0_1_p0_2_candidate_latent_outbreak_calls": plan.p01_p02_candidate_latent_calls,
        "p0_3_latent_outbreak_calls": plan.p03_latent_calls,
        "total_latent_outbreak_calls": plan.total_latent_calls,
        "p0_1_observation_transforms": plan.p01_observation_transforms,
        "total_observation_transforms": plan.total_observation_transforms,
        "distinct_population_network_seed_builds": plan.distinct_network_seed_builds,
    }
    if any(int(budget_caps.get(name, -1)) != value for name, value in cap_names.items()):
        raise BudgetError("declared budget caps do not match the calculated workload")


def plan_workload(config: CampaignConfig) -> WorkloadPlan:
    """Calculate all three-arm counts before any simulation could be called."""

    dimension_sizes = [len(dimension.candidates) for dimension in config.dimensions]
    p01_cells = _product(dimension_sizes)
    p02_wrong_delay_cells = p01_cells
    p02_wrong_regime_cells = (
        len(config.dimension_map["beta"].candidates)
        * len(config.dimension_map["inoculation_day_offset"].candidates)
        * 3
    )
    p03_cells = 3 * 3
    truth_latent_calls = len(config.target_process_seeds)
    candidate_latent_calls = (
        len(config.candidate_process_seeds)
        * len(config.dimension_map["beta"].candidates)
        * len(config.dimension_map["inoculation_day_offset"].candidates)
    )
    p03_latent_calls = len(config.candidate_process_seeds) * p03_cells
    p01_observation_transforms = len(config.target_process_seeds) + p01_cells * len(
        config.candidate_process_seeds
    )
    total_observation_transforms = (
        p01_observation_transforms
        + p01_cells * len(config.candidate_process_seeds)
        + p02_wrong_regime_cells * len(config.candidate_process_seeds)
        + p03_cells * len(config.candidate_process_seeds)
    )
    return WorkloadPlan(
        p01_cells=p01_cells,
        p02_wrong_delay_cells=p02_wrong_delay_cells,
        p02_wrong_regime_cells=p02_wrong_regime_cells,
        p03_cells=p03_cells,
        total_cells=p01_cells + p02_wrong_delay_cells + p02_wrong_regime_cells + p03_cells,
        truth_latent_calls=truth_latent_calls,
        p01_p02_candidate_latent_calls=candidate_latent_calls,
        p03_latent_calls=p03_latent_calls,
        total_latent_calls=truth_latent_calls + candidate_latent_calls + p03_latent_calls,
        p01_observation_transforms=p01_observation_transforms,
        total_observation_transforms=total_observation_transforms,
        distinct_network_seed_builds=len(
            set(config.target_process_seeds) | set(config.candidate_process_seeds)
        ),
        duration_days=config.duration_days,
        mode=config.mode,
    )


def guard_workload(
    config: CampaignConfig,
    *,
    retries: int = 0,
    adaptive_grid: bool = False,
    replacement_seeds: bool = False,
) -> WorkloadPlan:
    """Fail closed on mode, duration, caps, overlap, retries, or replacements."""

    if retries or adaptive_grid or replacement_seeds:
        raise BudgetError("requested retries, adaptive grid, or replacement seeds are forbidden")
    seed_sets = (
        set(config.target_process_seeds),
        set(config.target_observation_seeds),
        set(config.candidate_process_seeds),
        set(config.candidate_observation_seeds),
    )
    if any(
        left & right for index, left in enumerate(seed_sets) for right in seed_sets[index + 1 :]
    ):
        raise BudgetError("seed namespaces overlap")
    plan = plan_workload(config)
    if plan.mode != "ci":
        raise BudgetError("execution mode must be ci")
    if plan.duration_days > MAX_DURATION_DAYS:
        raise BudgetError("predicted duration exceeds 30 days")
    if plan.p01_cells > P01_GRID_CELLS:
        raise BudgetError("P0-1 grid exceeds its declared 81-cell cap")
    if plan.total_cells > TOTAL_GRID_CELLS:
        raise BudgetError("total grid exceeds the declared 198-cell cap")
    if plan.total_latent_calls > TOTAL_LATENT_CALLS:
        raise BudgetError("latent outbreak calls exceed the declared 59-call cap")
    if plan.total_observation_transforms > TOTAL_OBSERVATION_TRANSFORMS:
        raise BudgetError("observation transforms exceed the declared 599-call cap")
    if plan.distinct_network_seed_builds > DISTINCT_NETWORK_SEED_BUILDS:
        raise BudgetError("network seed builds exceed the declared eight-build cap")
    return plan


def observation_dates(start_date: date, duration_days: int, tail_days: int = 4) -> tuple[str, ...]:
    """Return the fixed zero-filled latent horizon plus the explicit four-day tail."""

    if duration_days < 1 or tail_days < 0:
        raise CampaignError("duration must be positive and observation tail non-negative")
    return tuple(
        (start_date + timedelta(days=index)).isoformat()
        for index in range(duration_days + tail_days)
    )


def observed_tables_from_events(
    observation_events: Iterable[Mapping[str, Any]],
    *,
    dates: Sequence[str],
) -> ObservedTables:
    """Convert observation events to the two blind fitter channels.

    Only report_date and symptom status are used. Latent counts, truth
    parameters, target seeds, and latent hashes are intentionally not part of
    the returned fitter-facing object.
    """

    date_grid = tuple(str(value) for value in dates)
    date_index = {value: index for index, value in enumerate(date_grid)}
    symptomatic = [0.0] * len(date_grid)
    asymptomatic = [0.0] * len(date_grid)
    for event in observation_events:
        report_date = event.get("report_date")
        if report_date is None:
            continue
        key = str(report_date)
        if key not in date_index:
            raise CampaignError(f"observation report date {key!r} is outside the complete grid")
        if "symptomatic" not in event:
            raise CampaignError("observation event lacks symptom-status channel metadata")
        index = date_index[key]
        if bool(event["symptomatic"]):
            symptomatic[index] += 1.0
        else:
            asymptomatic[index] += 1.0
    return ObservedTables(date_grid, tuple(symptomatic), tuple(asymptomatic))


def validate_observation_calendar(
    tables: ObservedTables,
    *,
    start_date: date,
    duration_days: int,
    tail_days: int = 4,
) -> None:
    """Require the exact common calendar used by every target and candidate."""

    expected = observation_dates(start_date, duration_days, tail_days)
    if tables.dates != expected:
        raise CampaignError("observed tables do not use the fixed complete campaign calendar")


def _coerce_tables(value: ObservedTables | Mapping[str, Sequence[float]]) -> ObservedTables:
    if isinstance(value, ObservedTables):
        return value
    try:
        dates = tuple(str(item) for item in value["dates"])
        symptomatic = tuple(float(item) for item in value["symptomatic"])
        asymptomatic = tuple(float(item) for item in value["asymptomatic"])
    except (KeyError, TypeError, ValueError) as exc:
        raise CampaignError(
            "tables must contain dates, symptomatic and asymptomatic channels"
        ) from exc
    return ObservedTables(dates, symptomatic, asymptomatic)


def minimum_distance_loss(target: ObservedTables, predictions: Sequence[ObservedTables]) -> float:
    """Calculate the predeclared two-channel square-root minimum-distance loss."""

    target_table = _coerce_tables(target)
    if len(predictions) != P01_FIT_REPLICATE_COUNT:
        raise CampaignError("each candidate cell must have exactly three fitting replicates")
    candidate_tables = tuple(_coerce_tables(value) for value in predictions)
    if any(table.dates != target_table.dates for table in candidate_tables):
        raise CampaignError("target and candidate tables must use the same complete dates")
    loss = 0.0
    for channel_index, target_channel in enumerate(target_table.channel_values):
        for time_index, target_count in enumerate(target_channel):
            candidate_mean = (
                sum(
                    math.sqrt(table.channel_values[channel_index][time_index] + 3.0 / 8.0)
                    for table in candidate_tables
                )
                / P01_FIT_REPLICATE_COUNT
            )
            target_root = math.sqrt(target_count + 3.0 / 8.0)
            loss += (target_root - candidate_mean) ** 2
    return loss / (2.0 * len(target_table.dates))


def _default_grid() -> tuple[CandidateCell, ...]:
    dimensions = (
        (0.04, 0.08, 0.12),
        (0.0, 2.0, 4.0),
        (0.5, 0.75, 1.0),
        (0.1, 0.25, 0.4),
    )
    return tuple(
        CandidateCell(beta, int(offset), symptomatic, asymptomatic)
        for beta in dimensions[0]
        for offset in dimensions[1]
        for symptomatic in dimensions[2]
        for asymptomatic in dimensions[3]
    )


def _profile_dimension(
    surface: Sequence[LossRow], dimension: str, values: Sequence[float], minimum: float
) -> ProfileDiagnostic:
    profiled = tuple(
        min(row.objective for row in surface if float(getattr(row.cell, dimension)) == float(value))
        for value in values
    )
    profile_minimum = min(profiled)
    tau = TIE_SCALE * max(1.0, minimum)
    numerical_tie = sum(abs(value - profile_minimum) <= tau for value in profiled) > 1
    sorted_distinct = sorted({value for value in profiled if value > profile_minimum + tau})
    second = sorted_distinct[0] if sorted_distinct else None
    relative_gap = (
        None
        if second is None
        else (second - profile_minimum) / max(profile_minimum, PROFILE_DENOMINATOR_FLOOR)
    )
    return ProfileDiagnostic(
        dimension=dimension,
        values=tuple(float(value) for value in values),
        profiled_objectives=profiled,
        minimum=profile_minimum,
        second_minimum=second,
        numerical_tie=numerical_tie,
        relative_gap=relative_gap,
        identified=(not numerical_tie and relative_gap is not None and relative_gap >= PROFILE_GAP),
    )


def _estimate_hash(
    selected: CandidateCell | None,
    minimum: float,
    profiles: Sequence[ProfileDiagnostic],
    numerical_tie: bool,
    surface: Sequence[LossRow],
) -> str:
    payload = {
        "selected": None if selected is None else selected.as_dict(),
        "minimum_objective": minimum,
        "profiles": [profile.as_dict() for profile in profiles],
        "numerical_tie": numerical_tie,
        "loss_surface": [row.as_dict() for row in surface],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def candidate_config_hash(cell: CandidateCell) -> str:
    """Hash the complete frozen candidate configuration represented by one cell."""

    payload = {
        "campaign_id": "v13-phase0-synthetic-recovery",
        "mode": "ci",
        "start_date": "2025-01-06",
        "duration_days": 30,
        "initial_seed_count": 0,
        "inoculation_attempts": 10,
        "inoculation_schedule": "start_date_plus_offset",
        "background_import_rate_per_day": 0.0,
        "route_multipliers": {route: 1.0 for route in P01_ROUTE_IDS},
        "symptomatic_probability": 0.6,
        "latent_duration_days": 2,
        "infectious_duration_days": 5,
        "waning_enabled": False,
        "detection_delay_days": 0,
        "reporting_delay_days": 2,
        "weekday_effect": [1.0] * 7,
        "observation_config_id": FIT_OBSERVATION_CONFIG_ID,
        "observation_horizon_tail_days": 4,
        "candidate": cell.as_dict(),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def score_complete_grid(
    target_tables: ObservedTables | Mapping[str, Sequence[float]],
    candidate_grid: Sequence[CandidateCell],
    candidate_prediction_library: Mapping[CandidateCell, Sequence[ObservedTables]],
    *,
    require_declared_grid: bool = True,
) -> tuple[LossRow, ...]:
    """Score every declared cell, with no selection or truth-dependent shortcut."""

    target = _coerce_tables(target_tables)
    grid = tuple(candidate_grid)
    if len(set(grid)) != len(grid):
        raise CampaignError("candidate grid contains duplicate cells")
    if require_declared_grid and grid != _default_grid():
        raise CampaignError("the P0-1 fitter requires the complete predeclared 81-cell grid")
    if set(candidate_prediction_library) != set(grid):
        missing = set(grid) - set(candidate_prediction_library)
        extra = set(candidate_prediction_library) - set(grid)
        raise CampaignError(
            f"candidate prediction library is incomplete (missing={missing}, extra={extra})"
        )
    rows = tuple(
        LossRow(
            cell=cell,
            objective=minimum_distance_loss(target, candidate_prediction_library[cell]),
            config_hash=candidate_config_hash(cell),
        )
        for cell in grid
    )
    if len(rows) != len(grid):
        raise CampaignError("not all candidate cells were scored")
    return rows


def fit_blind(
    target_tables: ObservedTables | Mapping[str, Sequence[float]],
    candidate_grid: Sequence[CandidateCell],
    candidate_prediction_library: Mapping[CandidateCell, Sequence[ObservedTables]],
) -> BlindFitResult:
    """Fit one target from observed tables and candidates only.

    This signature is the scientific blind boundary. It has no truth value,
    target seed, latent event, latent hash, or truth metadata argument.
    """

    target = _coerce_tables(target_tables)
    if target.dates != observation_dates(P01_START_DATE, P01_DURATION_DAYS, P01_TAIL_DAYS):
        raise CampaignError("the P0-1 fitter requires the fixed complete campaign calendar")
    surface = score_complete_grid(
        target,
        candidate_grid,
        candidate_prediction_library,
        require_declared_grid=True,
    )
    minimum = min(row.objective for row in surface)
    tau = TIE_SCALE * max(1.0, minimum)
    minimizers = tuple(row.cell for row in surface if abs(row.objective - minimum) <= tau)
    numerical_tie = len(minimizers) > 1
    selected = None if numerical_tie else minimizers[0]
    grid_values = {
        "beta": tuple(sorted({cell.beta for cell in candidate_grid})),
        "inoculation_day_offset": tuple(
            sorted({float(cell.inoculation_day_offset) for cell in candidate_grid})
        ),
        "symptomatic_detection_probability": tuple(
            sorted({cell.symptomatic_detection_probability for cell in candidate_grid})
        ),
        "asymptomatic_detection_probability": tuple(
            sorted({cell.asymptomatic_detection_probability for cell in candidate_grid})
        ),
    }
    profiles = tuple(
        _profile_dimension(surface, dimension, values, minimum)
        for dimension, values in grid_values.items()
    )
    return BlindFitResult(
        loss_surface=surface,
        minimum_objective=minimum,
        global_minimizers=minimizers,
        numerical_tie=numerical_tie,
        tie_tolerance=tau,
        selected=selected,
        profiles=profiles,
        identified=not numerical_tie and all(profile.identified for profile in profiles),
        estimate_hash=_estimate_hash(selected, minimum, profiles, numerical_tie, surface),
    )


def join_truth_evaluation(
    fit: BlindFitResult,
    *,
    target_seed: int,
    truth: CandidateCell,
    truth_diagnostics: TruthDiagnostics,
    namespace_passed: bool = True,
) -> RecoveryRow:
    """Join truth only after the blind estimate and estimate hash exist."""

    if not fit.estimate_hash or len(fit.estimate_hash) != 64:
        raise CampaignError("blind estimate must be hashed before truth evaluation")
    return RecoveryRow(
        target_seed=target_seed,
        estimate_hash=fit.estimate_hash,
        selected=fit.selected,
        profiles=fit.profiles,
        numerical_tie=fit.numerical_tie,
        truth=truth,
        truth_diagnostics=truth_diagnostics,
        namespace_passed=namespace_passed,
        scored_cell_count=len(fit.loss_surface),
    )


def _boundary_value(value: float, dimension: DimensionSpec) -> bool:
    return value in {dimension.candidates[0], dimension.candidates[-1]}


def evaluate_p01(
    rows: Sequence[RecoveryRow],
    *,
    config: CampaignConfig | None = None,
    workload: WorkloadPlan | None = None,
) -> P01Evaluation:
    """Compute the complete P0-1 descriptive and gate predicates."""

    dimensions = (
        config.dimensions
        if config is not None
        else (
            DimensionSpec("beta", 0.08, (0.04, 0.08, 0.12), 0.04, 0.02),
            DimensionSpec("inoculation_day_offset", 2.0, (0.0, 2.0, 4.0), 2.0, 1.0),
            DimensionSpec("symptomatic_detection_probability", 0.75, (0.5, 0.75, 1.0), 0.25, 0.125),
            DimensionSpec(
                "asymptomatic_detection_probability", 0.25, (0.1, 0.25, 0.4), 0.15, 0.075
            ),
        )
    )
    expected_count = len(config.target_process_seeds) if config is not None else P01_TARGET_COUNT
    complete = (
        len(rows) == expected_count and len({row.target_seed for row in rows}) == expected_count
    )
    coverage: dict[str, float | None] = {}
    bias: dict[str, float | None] = {}
    boundary_counts: dict[str, int] = {}
    descriptive_predicates: dict[str, bool] = {}
    serial_rows: list[dict[str, Any]] = []
    for dimension in dimensions:
        values: list[float] = []
        covered = 0
        boundary_count = 0
        for row in rows:
            error = row.absolute_error(dimension.name)
            profile = next(
                (item for item in row.profiles if item.dimension == dimension.name), None
            )
            identified = profile is not None and profile.identified and not row.numerical_tie
            if identified and error is not None and error <= dimension.tolerance:
                covered += 1
            signed = row.signed_error(dimension.name)
            if signed is not None:
                values.append(signed)
            if row.selected is not None and _boundary_value(
                float(getattr(row.selected, dimension.name)), dimension
            ):
                boundary_count += 1
            serial_rows.append(
                {
                    "target_seed": row.target_seed,
                    "estimate_hash": row.estimate_hash,
                    "dimension": dimension.name,
                    "estimate": None
                    if row.selected is None
                    else getattr(row.selected, dimension.name),
                    "truth": getattr(row.truth, dimension.name),
                    "signed_error": signed,
                    "absolute_error": error,
                    "identified": identified,
                }
            )
        coverage[dimension.name] = covered / expected_count if complete else None
        bias[dimension.name] = sum(values) / len(values) if len(values) == expected_count else None
        boundary_counts[dimension.name] = boundary_count
        coverage_value = coverage[dimension.name]
        bias_value = bias[dimension.name]
        descriptive_predicates[f"coverage_{dimension.name}"] = bool(
            complete and coverage_value is not None and coverage_value >= 4 / 5
        )
        descriptive_predicates[f"bias_{dimension.name}"] = bool(
            complete and bias_value is not None and abs(bias_value) <= dimension.bias_limit
        )
        descriptive_predicates[f"boundary_{dimension.name}"] = boundary_count <= 1
    joint_hits = 0
    for row in rows:
        if row.numerical_tie:
            continue
        joint_row = True
        for dimension in dimensions:
            error = row.absolute_error(dimension.name)
            identified = any(
                profile.dimension == dimension.name and profile.identified
                for profile in row.profiles
            )
            if not identified or error is None or error > dimension.tolerance:
                joint_row = False
                break
        if joint_row:
            joint_hits += 1
    joint_coverage = joint_hits / expected_count if complete else None
    predicates: dict[str, bool] = {
        "all_target_runs_and_cells_complete": complete
        and all(row.scored_cell_count == P01_GRID_CELLS and not row.numerical_tie for row in rows),
        "truth_viability": complete and all(row.truth_diagnostics.viable for row in rows),
        "observation_chronology_and_conservation": complete
        and all(
            row.truth_diagnostics.chronology_passed
            and row.truth_diagnostics.latent_incidence_conservation_passed
            for row in rows
        ),
        "no_global_loss_minimum_tie": complete and all(not row.numerical_tie for row in rows),
        "joint_coverage_at_least_3_of_5": bool(
            complete and joint_coverage is not None and joint_coverage >= 3 / 5
        ),
        "declared_namespace_grid_objective_dates_fixed_parameters": complete
        and all(row.namespace_passed and row.truth_diagnostics.namespace_passed for row in rows),
        "workload_within_caps": workload is None
        or (
            workload.p01_cells <= P01_GRID_CELLS
            and workload.p01_latent_calls <= P01_LATENT_CALLS
            and workload.p01_observation_transforms <= P01_OBSERVATION_TRANSFORMS
        ),
    }
    predicates.update(descriptive_predicates)
    status: Literal["PASS", "FAIL"] = "PASS" if all(predicates.values()) else "FAIL"
    return P01Evaluation(
        status=status,
        predicates=predicates,
        coverage=coverage,
        bias=bias,
        boundary_counts=boundary_counts,
        joint_coverage=joint_coverage,
        rows=tuple(serial_rows),
    )


def truth_diagnostics_from_events(
    latent_events: Iterable[Mapping[str, Any]],
    observed_tables: ObservedTables,
    *,
    chronology_passed: bool,
    latent_incidence_conservation_passed: bool,
    namespace_passed: bool = True,
) -> TruthDiagnostics:
    """Build truth-run viability diagnostics after, and only after, fitting."""

    events = tuple(latent_events)
    imports = sum(bool(event.get("imported", False)) for event in events)
    local = sum(str(event.get("source_kind", "")) == "local" for event in events)
    symptomatic_reports = int(sum(observed_tables.symptomatic))
    asymptomatic_reports = int(sum(observed_tables.asymptomatic))
    nonzero_dates = sum(
        symptomatic + asymptomatic > 0
        for symptomatic, asymptomatic in zip(
            observed_tables.symptomatic, observed_tables.asymptomatic, strict=True
        )
    )
    return TruthDiagnostics(
        inoculation_acquisitions=imports,
        local_secondary_infections=local,
        symptomatic_reports=symptomatic_reports,
        asymptomatic_reports=asymptomatic_reports,
        nonzero_combined_report_dates=nonzero_dates,
        chronology_passed=chronology_passed,
        latent_incidence_conservation_passed=latent_incidence_conservation_passed,
        namespace_passed=namespace_passed,
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_predeclaration(path: Path, expected_sha256: str = PREDECLARATION_SHA256) -> str:
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise CampaignError(
            f"predeclaration SHA-256 mismatch: expected {expected_sha256}, got {actual}"
        )
    return actual


def write_research_bundle(
    output_dir: Path,
    *,
    campaign_config_path: Path,
    predeclaration_path: Path,
    seed_ledger: Sequence[Mapping[str, Any]],
    candidate_loss_surfaces: Mapping[str, Any],
    p01_recovery_rows: Sequence[Mapping[str, Any]] | None = None,
    p02_misspecification_rows: Sequence[Mapping[str, Any]] | None = None,
    p03_profile: Mapping[str, Any] | None = None,
    campaign_summary: Mapping[str, Any] | None = None,
    input_hashes: Mapping[str, str] | None = None,
) -> Path:
    """Write a standalone research bundle with file-level SHA-256 provenance."""

    output_dir.mkdir(parents=True, exist_ok=True)
    config_bytes = campaign_config_path.read_bytes()
    predeclaration_hash = validate_predeclaration(predeclaration_path)
    (output_dir / "campaign_config.yaml").write_bytes(config_bytes)
    (output_dir / "predeclaration.sha256").write_text(
        f"{predeclaration_hash}  predeclaration\n", encoding="utf-8"
    )
    (output_dir / "seed_ledger.json").write_text(
        json.dumps(list(seed_ledger), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "candidate_loss_surfaces.json").write_text(
        json.dumps(candidate_loss_surfaces, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if p01_recovery_rows is not None:
        rows = list(p01_recovery_rows)
        fields = sorted({key for row in rows for key in row}) or ["status"]
        with (output_dir / "p0_1_recovery.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    if p02_misspecification_rows is not None:
        rows = list(p02_misspecification_rows)
        fields = sorted({key for row in rows for key in row}) or ["status"]
        with (output_dir / "p0_2_misspecification.csv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    if p03_profile is not None:
        (output_dir / "p0_3_profile.json").write_text(
            json.dumps(p03_profile, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    summary = {
        **dict(campaign_summary or {}),
        "status": "UNEXECUTED",
        "real_jersey_data_used": False,
        "nominal_coverage_claim": None,
        "calibration_claim": None,
        "input_hashes": dict(input_hashes or {}),
        "campaign_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "predeclaration_sha256": predeclaration_hash,
    }
    (output_dir / "campaign_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    files = sorted(path for path in output_dir.iterdir() if path.is_file())
    sums = "".join(f"{sha256_file(path)}  {path.name}\n" for path in files)
    (output_dir / "SHA256SUMS").write_text(sums, encoding="utf-8")
    return output_dir


def dry_run(config_path: Path, predeclaration_path: Path) -> WorkloadPlan:
    """Validate and report counts without invoking simulation code."""

    config = CampaignConfig.from_yaml(config_path)
    validate_predeclaration(predeclaration_path, config.expected_predeclaration_sha256)
    plan = guard_workload(config)
    print(
        json.dumps(
            {"predeclaration_sha256": config.expected_predeclaration_sha256, **plan.as_dict()},
            indent=2,
        )
    )
    return plan


def execute_campaign(config_path: Path, predeclaration_path: Path, output_dir: Path) -> None:
    """Fail closed until every predeclared arm is implemented and reviewed."""

    config = CampaignConfig.from_yaml(config_path)
    validate_predeclaration(predeclaration_path, config.expected_predeclaration_sha256)
    guard_workload(config)
    missing = tuple(arm for arm in config.required_arms if arm not in config.implemented_arms)
    if missing:
        raise CampaignBlockedError(
            "campaign execution is fail-closed; required arms are not implemented: "
            + ", ".join(missing)
        )
    raise CampaignBlockedError("campaign execution is not enabled in this implementation")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JOS Phase-0 synthetic-recovery campaign")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("dry-run", "execute"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--config", type=Path, required=True)
        subparser.add_argument("--predeclaration", type=Path, required=True)
        if command == "execute":
            subparser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "dry-run":
            dry_run(arguments.config, arguments.predeclaration)
        else:
            execute_campaign(arguments.config, arguments.predeclaration, arguments.output_dir)
    except (CampaignError, CampaignBlockedError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
