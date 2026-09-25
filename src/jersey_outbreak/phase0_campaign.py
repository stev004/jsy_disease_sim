"""Standalone, blind Phase-0 synthetic-recovery machinery.

This module is deliberately separate from the scalar calibration contracts. It
contains the P0-1 scoring boundary and the frozen Phase-0 workload declaration;
it does not alter, or write through, any existing simulation or calibration
artifact schema.

The campaign executor composes the frozen P0-1, P0-2, and P0-3 arms. Dry-run
calculates the complete budget without calling a simulator or observation transform.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import sys
import tempfile
import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path, PurePosixPath
from typing import Any, Literal, cast

import yaml  # type: ignore[import-untyped]

from .calibration import _profile_beta_nuisance, _record_argmin_shifts
from .observation import load_observation_config, observe_latent_run
from .observation_scheduler import observation_stream_seed
from .observation_schemas import ObservationConfig
from .outbreak_runner import default_run_config, load_parameter_set, run_outbreak
from .outbreak_schemas import OutbreakRunConfig, RespiratoryParameterSet
from .parent_build import build_parent
from .population_schemas import PopulationMode

PREDECLARATION_SHA256 = "ef67fe49903c3984ca98679eb0470878bc25523baca3bc23a63e4ae7d983a104"
PHASE0B_PREDECLARATION_PATH = "docs/research/v1_3/2026-09-25-phase0b-predeclaration.md"
PHASE0B_PREDECLARATION_SHA256 = "ec8df64630dd50c83b0866a096fba4980453c34232d18114129587274f257451"
G29_RULING_PATH = "docs/research/v1_3/2026-09-23-g29-p02-tie-ruling-ACCEPTED.md"
G29_RULING_SHA256 = "06e49aaa7f21564dd6f525941633054fad39cf6714aa74aec0ef1f12dc1eb70c"
PHASE0B_OWNER_RULING_PATH = "docs/research/v1_3/2026-09-25-phase0b-owner-ruling-ACCEPTED.md"
PHASE0B_OWNER_RULING_SHA256 = "ea15ea558bd7b6bea962f55b2cf83f44c13cf6f7b07da1f3bab03598a1f98a39"
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
P02B_COMMON_PROBABILITY_GRID: tuple[float, ...] = (0.25, 0.50, 0.75)
P03_BETA_GRID: tuple[float, ...] = (0.04, 0.08, 0.16)
P03_ROUTE_FACTOR_GRID: tuple[float, ...] = (0.5, 1.0, 2.0)
PHASE0B_P02B_COMMON_PROBABILITY_GRID: tuple[str, ...] = ("0.25", "0.50", "0.75")
PHASE0B_P03_BETA_GRID: tuple[str, ...] = ("0.04", "0.08", "0.16")
PHASE0B_P03_ROUTE_FACTOR_GRID: tuple[str, ...] = ("0.5", "1.0", "2.0")
P03_OBSERVATION_TRANSFORMS = 27
P03_VECTOR_TOLERANCE = 1.0e-12
P03_OBJECTIVE_SPREAD_SCALE = 1.0e-12

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

PHASE0B_TARGET_PROCESS_SEEDS: tuple[int, ...] = (62001, 62002, 62003, 62004, 62005)
PHASE0B_TARGET_OBSERVATION_SEEDS: tuple[int, ...] = (72001, 72002, 72003, 72004, 72005)
PHASE0B_FIT_PROCESS_SEEDS: tuple[int, ...] = (63001, 63002, 63003)
PHASE0B_FIT_OBSERVATION_SEEDS: tuple[int, ...] = (73001, 73002, 73003)
PHASE0B_TARGET_OBSERVATION_CONFIG_ID = "v13-phase0b-target"
PHASE0B_FIT_OBSERVATION_CONFIG_ID = "v13-phase0b-fit"
PHASE0_DIMENSION_DECLARATION: tuple[tuple[str, Any, tuple[Any, ...], Any, Any], ...] = (
    ("beta", 0.08, (0.04, 0.08, 0.12), 0.04, 0.02),
    ("inoculation_day_offset", 2, (0, 2, 4), 2, 1),
    ("symptomatic_detection_probability", 0.75, (0.50, 0.75, 1.00), 0.25, 0.125),
    ("asymptomatic_detection_probability", 0.25, (0.10, 0.25, 0.40), 0.15, 0.075),
)
PHASE0B_DIMENSION_DECLARATION: tuple[tuple[str, str, tuple[str, ...], str, str], ...] = (
    ("beta", "0.08", ("0.04", "0.06", "0.08", "0.10", "0.12"), "0.02", "0.01"),
    ("inoculation_day_offset", "2", ("0", "1", "2", "3", "4"), "1", "0.5"),
    (
        "symptomatic_detection_probability",
        "0.75",
        ("0.50", "0.625", "0.75", "0.875", "1.00"),
        "0.125",
        "0.0625",
    ),
    (
        "asymptomatic_detection_probability",
        "0.25",
        ("0.10", "0.175", "0.25", "0.325", "0.40"),
        "0.075",
        "0.0375",
    ),
)
PHASE0B_CAPS: Mapping[str, int] = {
    "p0_1_grid_cells": 625,
    "p0_2_wrong_delay_cells": 625,
    "p0_2_wrong_regime_cells": 75,
    "p0_3_cells": 9,
    "total_cells": 1334,
    "truth_latent_outbreak_calls": 5,
    "p0_1_p0_2_candidate_latent_outbreak_calls": 75,
    "p0_3_latent_outbreak_calls": 27,
    "total_latent_outbreak_calls": 107,
    "p0_1_observation_transforms": 1880,
    "total_observation_transforms": 4007,
    "distinct_population_network_seed_builds": 8,
}
PHASE0_LINEAGE = {
    "phase0_verdict": "FAIL",
    "phase0_exit_audit_path": "docs/audits/2026-09-24-phase0-exit-audit-sol-FAIL.md",
    "phase0_bundle_sha256sums_sha256": (
        "72cd9a568598530923e08ce20b013d60eb7a3b26553b87c31685ad623f3faa80"
    ),
    "phase0_predeclaration_sha256": PREDECLARATION_SHA256,
    "failing_predicate": {
        "arm": "p0_1",
        "predicate": 8,
        "dimension": "inoculation_day_offset",
        "boundary_count": "2/5",
        "selections": [0, 2, 2, 2, 4],
    },
    "single_design_change": "grid resolution halved; tolerance and bias rules unchanged",
    "designed_after_phase0_results_were_observed": True,
    "no_phase0b_outcome_alters_phase0_verdict": True,
    "phase0_historical_evidence": {
        "p0_2a": "PASS (historical evidence only)",
        "p0_2b": "PASS (historical evidence only)",
        "p0_3": "PASS (historical evidence only)",
    },
}


@dataclass(frozen=True)
class FrozenProfile:
    campaign_id: str
    predeclaration_path: str
    predeclaration_sha256: str
    dimensions: tuple[tuple[str, Any, tuple[Any, ...], Any, Any], ...]
    target_process_seeds: tuple[int, ...]
    target_observation_seeds: tuple[int, ...]
    candidate_process_seeds: tuple[int, ...]
    candidate_observation_seeds: tuple[int, ...]
    target_observation_config_id: str
    candidate_observation_config_id: str
    p01_cells: int
    p02a_cells: int
    p02b_cells: int
    total_cells: int
    truth_latent_calls: int
    candidate_latent_calls: int
    p03_latent_calls: int
    total_latent_calls: int
    p01_transforms: int
    total_transforms: int
    network_builds: int
    owner_ruling_path: str | None = None
    owner_ruling_sha256: str | None = None

    @property
    def dimensions_by_name(self) -> dict[str, tuple[str, Any, tuple[Any, ...], Any, Any]]:
        return {item[0]: item for item in self.dimensions}


PHASE0_PROFILE = FrozenProfile(
    campaign_id="v13-phase0-synthetic-recovery",
    predeclaration_path="docs/research/v1_3/2026-09-21-phase0-predeclaration.md",
    predeclaration_sha256=PREDECLARATION_SHA256,
    dimensions=PHASE0_DIMENSION_DECLARATION,
    target_process_seeds=TARGET_PROCESS_SEEDS,
    target_observation_seeds=TARGET_OBSERVATION_SEEDS,
    candidate_process_seeds=FIT_PROCESS_SEEDS,
    candidate_observation_seeds=FIT_OBSERVATION_SEEDS,
    target_observation_config_id=TARGET_OBSERVATION_CONFIG_ID,
    candidate_observation_config_id=FIT_OBSERVATION_CONFIG_ID,
    p01_cells=81,
    p02a_cells=81,
    p02b_cells=27,
    total_cells=198,
    truth_latent_calls=5,
    candidate_latent_calls=27,
    p03_latent_calls=27,
    total_latent_calls=59,
    p01_transforms=248,
    total_transforms=599,
    network_builds=8,
)
PHASE0B_PROFILE = FrozenProfile(
    campaign_id="v13-phase0b",
    predeclaration_path=PHASE0B_PREDECLARATION_PATH,
    predeclaration_sha256=PHASE0B_PREDECLARATION_SHA256,
    dimensions=PHASE0B_DIMENSION_DECLARATION,
    target_process_seeds=PHASE0B_TARGET_PROCESS_SEEDS,
    target_observation_seeds=PHASE0B_TARGET_OBSERVATION_SEEDS,
    candidate_process_seeds=PHASE0B_FIT_PROCESS_SEEDS,
    candidate_observation_seeds=PHASE0B_FIT_OBSERVATION_SEEDS,
    target_observation_config_id=PHASE0B_TARGET_OBSERVATION_CONFIG_ID,
    candidate_observation_config_id=PHASE0B_FIT_OBSERVATION_CONFIG_ID,
    p01_cells=PHASE0B_CAPS["p0_1_grid_cells"],
    p02a_cells=PHASE0B_CAPS["p0_2_wrong_delay_cells"],
    p02b_cells=PHASE0B_CAPS["p0_2_wrong_regime_cells"],
    total_cells=PHASE0B_CAPS["total_cells"],
    truth_latent_calls=PHASE0B_CAPS["truth_latent_outbreak_calls"],
    candidate_latent_calls=PHASE0B_CAPS["p0_1_p0_2_candidate_latent_outbreak_calls"],
    p03_latent_calls=PHASE0B_CAPS["p0_3_latent_outbreak_calls"],
    total_latent_calls=PHASE0B_CAPS["total_latent_outbreak_calls"],
    p01_transforms=PHASE0B_CAPS["p0_1_observation_transforms"],
    total_transforms=PHASE0B_CAPS["total_observation_transforms"],
    network_builds=PHASE0B_CAPS["distinct_population_network_seed_builds"],
    owner_ruling_path=PHASE0B_OWNER_RULING_PATH,
    owner_ruling_sha256=PHASE0B_OWNER_RULING_SHA256,
)
FROZEN_PROFILES: Mapping[str, FrozenProfile] = {
    PHASE0_PROFILE.campaign_id: PHASE0_PROFILE,
    PHASE0B_PROFILE.campaign_id: PHASE0B_PROFILE,
}


def frozen_profile(campaign_id: str) -> FrozenProfile:
    try:
        return FROZEN_PROFILES[campaign_id]
    except KeyError as exc:
        raise CampaignError(f"unsupported frozen campaign id: {campaign_id!r}") from exc


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
    truth_decimal: Decimal | None = field(default=None, repr=False, compare=False)
    candidate_decimals: tuple[Decimal, ...] | None = field(default=None, repr=False, compare=False)
    tolerance_decimal: Decimal | None = field(default=None, repr=False, compare=False)
    bias_limit_decimal: Decimal | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.name or not self.candidates:
            raise CampaignError("dimension names and candidate grids must be non-empty")
        if len(set(self.candidates)) != len(self.candidates):
            raise CampaignError(f"candidate grid for {self.name!r} contains duplicates")
        if self.tolerance < 0 or self.bias_limit < 0:
            raise CampaignError(f"dimension limits for {self.name!r} must be non-negative")

    def exact_truth(self) -> Decimal:
        return (
            self.truth_decimal if self.truth_decimal is not None else _declared_decimal(self.truth)
        )

    def exact_candidates(self) -> tuple[Decimal, ...]:
        return (
            self.candidate_decimals
            if self.candidate_decimals is not None
            else tuple(_declared_decimal(value) for value in self.candidates)
        )

    def exact_tolerance(self) -> Decimal:
        return (
            self.tolerance_decimal
            if self.tolerance_decimal is not None
            else _declared_decimal(self.tolerance)
        )

    def exact_bias_limit(self) -> Decimal:
        return (
            self.bias_limit_decimal
            if self.bias_limit_decimal is not None
            else _declared_decimal(self.bias_limit)
        )

    def exact_value(self, value: float | int) -> Decimal:
        numeric = float(value)
        if numeric == float(self.truth):
            return self.exact_truth()
        for candidate, exact in zip(self.candidates, self.exact_candidates(), strict=True):
            if numeric == candidate:
                return exact
        raise CampaignError(f"value {value!r} is outside the declared {self.name} grid")


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
    g29_ruling_path: str
    g29_ruling_sha256: str
    owner_ruling_path: str | None
    owner_ruling_sha256: str | None
    implemented_arms: tuple[str, ...]
    required_arms: tuple[str, ...]
    retries: int
    adaptive_grid: bool
    replacement_seeds: bool
    declaration: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def dimension_map(self) -> dict[str, DimensionSpec]:
        return {dimension.name: dimension for dimension in self.dimensions}

    @property
    def profile(self) -> FrozenProfile:
        return frozen_profile(self.campaign_id)

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
        _validate_frozen_payload(payload)
        profile = frozen_profile(str(payload.get("campaign_id", "")))

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
            truth_decimal = _parse_dimension_decimal(raw["truth"], profile)
            candidate_decimals = tuple(
                _parse_dimension_decimal(value, profile) for value in raw["candidates"]
            )
            tolerance_decimal = _parse_dimension_decimal(raw["tolerance"], profile)
            bias_limit_decimal = _parse_dimension_decimal(raw["bias_limit"], profile)
            dimensions.append(
                DimensionSpec(
                    name=name,
                    truth=float(truth_decimal),
                    candidates=tuple(float(value) for value in candidate_decimals),
                    tolerance=float(tolerance_decimal),
                    bias_limit=float(bias_limit_decimal),
                    truth_decimal=truth_decimal,
                    candidate_decimals=candidate_decimals,
                    tolerance_decimal=tolerance_decimal,
                    bias_limit_decimal=bias_limit_decimal,
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
            g29_ruling_path=str(required("g29_ruling_path")),
            g29_ruling_sha256=str(required("g29_ruling_sha256")),
            owner_ruling_path=(
                None if "owner_ruling_path" not in payload else str(payload["owner_ruling_path"])
            ),
            owner_ruling_sha256=(
                None
                if "owner_ruling_sha256" not in payload
                else str(payload["owner_ruling_sha256"])
            ),
            implemented_arms=tuple(str(value) for value in implementation["implemented_arms"]),
            required_arms=tuple(str(value) for value in implementation["required_arms"]),
            retries=int(implementation["retries"]),
            adaptive_grid=bool(implementation["adaptive_grid"]),
            replacement_seeds=bool(implementation["replacement_seeds"]),
            declaration=json.loads(json.dumps(payload)),
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
    namespace_passed: bool = False
    complete: bool = False
    raw_values: Mapping[str, Any] = field(default_factory=dict)

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

    def as_dict(self) -> dict[str, Any]:
        return {
            "inoculation_acquisitions": self.inoculation_acquisitions,
            "local_secondary_infections": self.local_secondary_infections,
            "symptomatic_reports": self.symptomatic_reports,
            "asymptomatic_reports": self.asymptomatic_reports,
            "nonzero_combined_report_dates": self.nonzero_combined_report_dates,
            "chronology_passed": self.chronology_passed,
            "latent_incidence_conservation_passed": self.latent_incidence_conservation_passed,
            "namespace_passed": self.namespace_passed,
            "complete": self.complete,
            "viable": self.viable,
            "raw_values": _model_payload(self.raw_values),
        }


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
    namespace_passed: bool = False
    scored_cell_count: int = P01_GRID_CELLS
    exact_estimate_truth: Mapping[str, tuple[Decimal, Decimal]] = field(
        default_factory=dict, repr=False, compare=False
    )

    def _signed_error_decimal(self, dimension: str) -> Decimal | None:
        if self.selected is None:
            return None
        if dimension in self.exact_estimate_truth:
            estimate, truth = self.exact_estimate_truth[dimension]
            return estimate - truth
        estimate = _declared_decimal(getattr(self.selected, dimension))
        truth = _declared_decimal(getattr(self.truth, dimension))
        return estimate - truth

    def _absolute_error_decimal(self, dimension: str) -> Decimal | None:
        value = self._signed_error_decimal(dimension)
        return None if value is None else abs(value)

    def signed_error(self, dimension: str) -> float | None:
        value = self._signed_error_decimal(dimension)
        return None if value is None else float(value)

    def absolute_error(self, dimension: str) -> float | None:
        value = self._absolute_error_decimal(dimension)
        return None if value is None else float(value)


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
    p03_observation_transforms: int
    total_latent_calls: int
    p01_observation_transforms: int
    total_observation_transforms: int
    distinct_network_seed_builds: int
    duration_days: int
    mode: str
    implemented_arms: tuple[str, ...]
    implemented_cells: int
    implemented_latent_calls: int
    implemented_observation_transforms: int

    @property
    def p01_latent_calls(self) -> int:
        return self.truth_latent_calls + self.p01_p02_candidate_latent_calls

    def as_dict(self) -> dict[str, Any]:
        return {
            "p0_1_grid_cells": self.p01_cells,
            "p0_2_wrong_delay_cells": self.p02_wrong_delay_cells,
            "p0_2_wrong_regime_cells": self.p02_wrong_regime_cells,
            "p0_3_cells": self.p03_cells,
            "total_cells": self.total_cells,
            "truth_latent_outbreak_calls": self.truth_latent_calls,
            "p0_1_p0_2_candidate_latent_outbreak_calls": self.p01_p02_candidate_latent_calls,
            "p0_3_latent_outbreak_calls": self.p03_latent_calls,
            "p0_3_observation_transforms": self.p03_observation_transforms,
            "total_latent_outbreak_calls": self.total_latent_calls,
            "p0_1_latent_calls": self.p01_latent_calls,
            "p0_1_observation_transforms": self.p01_observation_transforms,
            "total_observation_transforms": self.total_observation_transforms,
            "distinct_population_network_seed_builds": self.distinct_network_seed_builds,
            "duration_days": self.duration_days,
            "mode": self.mode,
            "implemented_arms": list(self.implemented_arms),
            "implemented_p0_1_grid_cells": (
                self.p01_cells if "p0_1" in self.implemented_arms else 0
            ),
            "implemented_p0_2a_grid_cells": (
                self.p02_wrong_delay_cells if "p0_2a" in self.implemented_arms else 0
            ),
            "implemented_p0_2b_grid_cells": (
                self.p02_wrong_regime_cells if "p0_2b" in self.implemented_arms else 0
            ),
            "implemented_p0_3_grid_cells": self.p03_cells if "p0_3" in self.implemented_arms else 0,
            "planned_p0_3_grid_cells": self.p03_cells,
            "implemented_grid_cells": self.implemented_cells,
            "implemented_latent_outbreak_calls": self.implemented_latent_calls,
            "implemented_observation_transforms": self.implemented_observation_transforms,
            "planned_grid_cells": self.total_cells,
            "planned_latent_outbreak_calls": self.total_latent_calls,
            "planned_observation_transforms": self.total_observation_transforms,
        }


@dataclass(frozen=True)
class ExecutionEvidence:
    """Measured evidence required before a scientific P0-1 PASS is possible."""

    target_process_seeds: tuple[int, ...]
    target_observation_seeds: tuple[int, ...]
    candidate_process_seeds: tuple[int, ...]
    candidate_observation_seeds: tuple[int, ...]
    target_observation_config_id: str
    candidate_observation_config_id: str
    target_runs_complete: bool
    candidate_cells_complete: bool
    calendars_complete: bool
    configs_complete: bool
    namespaces_complete: bool
    measured_latent_calls: int | None
    measured_observation_transforms: int | None

    def matches(self, config: CampaignConfig, workload: WorkloadPlan) -> bool:
        """Check exact declared schedules and measured, rather than assumed, counts."""

        return (
            self.target_process_seeds == config.target_process_seeds
            and self.target_observation_seeds == config.target_observation_seeds
            and self.candidate_process_seeds == config.candidate_process_seeds
            and self.candidate_observation_seeds == config.candidate_observation_seeds
            and self.target_observation_config_id == config.target_observation_config_id
            and self.candidate_observation_config_id == config.candidate_observation_config_id
            and self.target_runs_complete
            and self.candidate_cells_complete
            and self.calendars_complete
            and self.configs_complete
            and self.namespaces_complete
            and self.measured_latent_calls == workload.p01_latent_calls
            and self.measured_observation_transforms == workload.p01_observation_transforms
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "target_process_seeds": list(self.target_process_seeds),
            "target_observation_seeds": list(self.target_observation_seeds),
            "candidate_process_seeds": list(self.candidate_process_seeds),
            "candidate_observation_seeds": list(self.candidate_observation_seeds),
            "target_observation_config_id": self.target_observation_config_id,
            "candidate_observation_config_id": self.candidate_observation_config_id,
            "target_runs_complete": self.target_runs_complete,
            "candidate_cells_complete": self.candidate_cells_complete,
            "calendars_complete": self.calendars_complete,
            "configs_complete": self.configs_complete,
            "namespaces_complete": self.namespaces_complete,
            "measured_latent_calls": self.measured_latent_calls,
            "measured_observation_transforms": self.measured_observation_transforms,
        }


@dataclass(frozen=True)
class P01CampaignResult:
    """P0-1 data retained for the later predeclared arms."""

    config: CampaignConfig
    workload: WorkloadPlan
    execution_evidence: ExecutionEvidence
    target_tables: Mapping[int, ObservedTables]
    target_config_hashes: Mapping[int, str]
    target_observation_hashes: Mapping[int, str]
    target_namespace_fingerprints: Mapping[int, str]
    candidate_prediction_library: Mapping[CandidateCell, tuple[ObservedTables, ...]]
    candidate_observation_hashes: Mapping[tuple[CandidateCell, int, int], str]
    candidate_config_hashes: Mapping[CandidateCell, str]
    candidate_latents: Mapping[tuple[int, float, int], tuple[Any, OutbreakRunConfig]]
    generated_parents: Mapping[int, Any]
    target_truths: Mapping[int, CandidateCell]
    target_diagnostics: Mapping[int, TruthDiagnostics]
    blind_fits: Mapping[int, BlindFitResult]
    recovery_rows: tuple[RecoveryRow, ...]
    evaluation: P01Evaluation


@dataclass(frozen=True)
class P02TargetResult:
    """One target's truth-joined P0-2 detection record."""

    arm: Literal["p0_2a", "p0_2b"]
    target_seed: int
    estimate_hash: str
    minimum_objective: float
    correct_minimum_objective: float
    relative_loss_degradation: float
    selected: CandidateCell | None
    global_minimizers: tuple[CandidateCell, ...]
    numerical_tie: bool
    channel_total_error: float | None
    clauses: Mapping[str, bool | None]
    dimension_errors: Mapping[str, Mapping[str, float | bool | None]]
    detection_state: Literal["TRUE", "FALSE", "UNKNOWN"]
    phase0b: bool = field(default=False, repr=False)

    def as_dict(self) -> dict[str, Any]:
        selected = None if self.selected is None else self.selected.as_dict()
        minimizers = [cell.as_dict() for cell in self.global_minimizers]
        row: dict[str, Any] = {
            "arm": self.arm,
            "target_seed": self.target_seed,
            "estimate_hash": self.estimate_hash,
            "selected_estimates": selected,
            "tie_record": minimizers if self.numerical_tie else None,
            "numerical_tie": self.numerical_tie,
            "wrong_minimum_objective": self.minimum_objective,
            "correct_minimum_objective": self.correct_minimum_objective,
            "R_i": self.relative_loss_degradation,
            "E_i": self.channel_total_error,
            "detection_state": self.detection_state,
        }
        row.update(
            {
                f"clause_{name}": ("UNKNOWN" if value is None else "TRUE" if value else "FALSE")
                if self.phase0b
                else value
                for name, value in self.clauses.items()
            }
        )
        for dimension, values in self.dimension_errors.items():
            for name, value in values.items():
                row[f"{name}_{dimension}"] = value
        if self.selected is None:
            row.update(
                {
                    "estimate_beta": None,
                    "estimate_inoculation_day_offset": None,
                    "estimate_symptomatic_detection_probability": None,
                    "estimate_asymptomatic_detection_probability": None,
                }
            )
        else:
            row.update(
                {f"estimate_{name}": value for name, value in self.selected.as_dict().items()}
            )
        return row


@dataclass(frozen=True)
class P02ArmResult:
    """Software and detection outcomes for one P0-2 arm."""

    arm: Literal["p0_2a", "p0_2b"]
    software_status: Literal["PASS", "FAIL"]
    misspecification_detection: Literal["PASS", "FAIL"] | None
    detection_reason: str | None
    threshold: int
    detected: int
    unknown: int
    attainable_detection_count: tuple[int, int]
    target_results: tuple[P02TargetResult, ...]
    candidate_prediction_library: Mapping[CandidateCell, tuple[ObservedTables, ...]]
    candidate_config_hashes: Mapping[CandidateCell, str]
    loss_surfaces: Mapping[int, tuple[LossRow, ...]]
    replicate_provenance: tuple[Mapping[str, Any], ...]
    measured_latent_calls: int
    measured_observation_transforms: int
    wall_time_seconds: float = field(default=0.0, compare=False)

    def as_dict(self) -> dict[str, Any]:
        return {
            "arm": self.arm,
            "software_status": self.software_status,
            "misspecification_detection": self.misspecification_detection,
            "detection_reason": self.detection_reason,
            "threshold": self.threshold,
            "detected": self.detected,
            "unknown": self.unknown,
            "attainable_detection_count": list(self.attainable_detection_count),
            "measured_latent_calls": self.measured_latent_calls,
            "measured_observation_transforms": self.measured_observation_transforms,
            "targets": [result.as_dict() for result in self.target_results],
            "candidate_config_hashes": {
                json.dumps(cell.as_dict(), sort_keys=True): digest
                for cell, digest in self.candidate_config_hashes.items()
            },
            "replicate_provenance": list(self.replicate_provenance),
            "loss_surfaces": {
                str(seed): [row.as_dict() for row in rows]
                for seed, rows in self.loss_surfaces.items()
            },
        }


@dataclass(frozen=True)
class P02CampaignResult:
    """Mock-measurable P0-2 composition over retained P0-1 outputs."""

    arms: Mapping[str, P02ArmResult]
    software_status: Literal["PASS", "FAIL"]
    misspecification_detection: Literal["PASS", "FAIL"] | None
    overall_detection_reason: str | None
    reused_p01_target_provenance: Mapping[int, Mapping[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "software_status": self.software_status,
            "misspecification_detection": self.misspecification_detection,
            "overall_detection_reason": self.overall_detection_reason,
            "reused_p01_target_provenance": {
                str(seed): dict(record)
                for seed, record in self.reused_p01_target_provenance.items()
            },
            "arms": {name: arm.as_dict() for name, arm in self.arms.items()},
        }


@dataclass(frozen=True, order=True)
class P03Cell:
    """One beta × global route-factor point in the negative control."""

    beta: float
    global_route_factor: float

    def as_dict(self) -> dict[str, float]:
        return {"beta": self.beta, "global_route_factor": self.global_route_factor}


@dataclass(frozen=True)
class P03CampaignResult:
    """Complete P0-3 surface, prediction evidence, and structural classifier."""

    software_status: Literal["PASS", "FAIL"]
    scientific_status: Literal["PASS", "FAIL"]
    classification: str
    factor_estimate: None
    predicates: Mapping[str, bool]
    target_profiles: Mapping[int, Mapping[str, Any]]
    loss_surfaces: Mapping[int, tuple[dict[str, Any], ...]]
    prediction_hashes: Mapping[str, str]
    prediction_vectors: Mapping[str, tuple[float, ...]]
    ridge_prediction_vectors: Mapping[str, tuple[float, ...]]
    candidate_prediction_library: Mapping[P03Cell, tuple[ObservedTables, ...]]
    ridge_objectives: Mapping[int, Mapping[str, float]]
    candidate_config_hashes: Mapping[P03Cell, str]
    replicate_provenance: tuple[Mapping[str, Any], ...]
    measured_latent_calls: int
    measured_observation_transforms: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "software_status": self.software_status,
            "scientific_status": self.scientific_status,
            "classification": self.classification,
            "factor_estimate": self.factor_estimate,
            "predicates": dict(self.predicates),
            "measured_latent_calls": self.measured_latent_calls,
            "measured_observation_transforms": self.measured_observation_transforms,
            "target_profiles": {
                str(seed): dict(profile) for seed, profile in self.target_profiles.items()
            },
            "loss_surfaces": {str(seed): list(rows) for seed, rows in self.loss_surfaces.items()},
            "prediction_hashes": dict(self.prediction_hashes),
            "prediction_vectors": {
                cell: list(vector) for cell, vector in self.prediction_vectors.items()
            },
            "ridge_prediction_vectors": {
                cell: list(vector) for cell, vector in self.ridge_prediction_vectors.items()
            },
            "ridge_objectives": {
                str(seed): dict(values) for seed, values in self.ridge_objectives.items()
            },
            "candidate_config_hashes": {
                json.dumps(cell.as_dict(), sort_keys=True): digest
                for cell, digest in self.candidate_config_hashes.items()
            },
            "replicate_provenance": list(self.replicate_provenance),
        }


def _product(values: Iterable[int]) -> int:
    result = 1
    for value in values:
        result *= value
    return result


def _parse_dimension_decimal(value: Any, profile: FrozenProfile) -> Decimal:
    """Parse declared grid values before converting them to simulator floats."""

    if profile is PHASE0B_PROFILE and not isinstance(value, str):
        raise CampaignError(
            "Phase-0b grid values, tolerances and bias limits must be decimal strings"
        )
    try:
        parsed = Decimal(value if isinstance(value, str) else str(value))
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise CampaignError("dimension values must be finite decimal numbers") from exc
    if not parsed.is_finite():
        raise CampaignError("dimension values must be finite decimal numbers")
    return parsed


def _phase0b_float_grid(values: Any, expected_strings: tuple[str, ...]) -> tuple[float, ...]:
    """Parse a validated Phase-0b decimal-string grid for numeric simulator APIs."""

    if not isinstance(values, list | tuple) or tuple(values) != expected_strings:
        raise CampaignError("Phase-0b grid does not match its independent decimal-string constant")
    try:
        decimals = tuple(Decimal(value) for value in values)
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise CampaignError("Phase-0b grids must contain decimal strings") from exc
    if any(not value.is_finite() for value in decimals):
        raise CampaignError("Phase-0b grids must contain finite decimals")
    return tuple(float(value) for value in decimals)


def _p02b_common_probability_grid(config: CampaignConfig) -> tuple[float, ...]:
    if config.profile is PHASE0B_PROFILE:
        misspecification = config.declaration["misspecification"]
        assert isinstance(misspecification, Mapping)
        p02b = misspecification["p0_2b"]
        assert isinstance(p02b, Mapping)
        return _phase0b_float_grid(
            p02b["common_probability_grid"], PHASE0B_P02B_COMMON_PROBABILITY_GRID
        )
    return P02B_COMMON_PROBABILITY_GRID


def _p03_grids(
    config: CampaignConfig | None = None,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    if config is None or config.profile is PHASE0_PROFILE:
        return P03_BETA_GRID, P03_ROUTE_FACTOR_GRID
    negative_control = config.declaration["negative_control"]
    assert isinstance(negative_control, Mapping)
    return (
        _phase0b_float_grid(negative_control["beta_grid"], PHASE0B_P03_BETA_GRID),
        _phase0b_float_grid(
            negative_control["global_route_factor_grid"], PHASE0B_P03_ROUTE_FACTOR_GRID
        ),
    )


def _validate_frozen_payload(payload: Mapping[str, Any]) -> None:
    """Validate every field of the committed scientific declaration.

    The dataclass below contains the fields needed by the runner.  This
    separate exact comparison prevents declaration-only objective, acceptance,
    and provenance controls from being silently ignored by the runner.
    """

    expected: dict[str, Any] = {
        "schema_version": "1.0",
        "campaign_id": "v13-phase0-synthetic-recovery",
        "mode": "ci",
        "start_date": "2025-01-06",
        "duration_days": 30,
        "observation_horizon_tail_days": 4,
        "predeclaration_sha256": PREDECLARATION_SHA256,
        "g29_ruling_path": G29_RULING_PATH,
        "g29_ruling_sha256": G29_RULING_SHA256,
        "dimensions": {
            "beta": {
                "truth": 0.08,
                "candidates": [0.04, 0.08, 0.12],
                "tolerance": 0.04,
                "bias_limit": 0.02,
            },
            "inoculation_day_offset": {
                "truth": 2,
                "candidates": [0, 2, 4],
                "tolerance": 2,
                "bias_limit": 1,
            },
            "symptomatic_detection_probability": {
                "truth": 0.75,
                "candidates": [0.50, 0.75, 1.00],
                "tolerance": 0.25,
                "bias_limit": 0.125,
            },
            "asymptomatic_detection_probability": {
                "truth": 0.25,
                "candidates": [0.10, 0.25, 0.40],
                "tolerance": 0.15,
                "bias_limit": 0.075,
            },
        },
        "fixed_scenario": {
            "population_mode": "ci",
            "population_size": 3000,
            "initial_seed_count": 0,
            "inoculation_attempts": 10,
            "inoculation_schedule": "start_date_plus_offset",
            "background_import_rate_per_day": 0.0,
            "import_schedule": "empty_except_inoculation",
            "route_multipliers": {route: 1.0 for route in P01_ROUTE_IDS},
            "symptomatic_probability": 0.6,
            "latent_duration_days": 2,
            "infectious_duration_days": 5,
            "waning_enabled": False,
            "seasonality": "absent",
            "interventions": "absent",
            "detection_delay_days": 0,
            "reporting_delay_days": 2,
            "weekday_effect": [1.0] * 7,
        },
        "observation": {
            "target_detection_probabilities": {"symptomatic": 0.75, "asymptomatic": 0.25},
            "candidate_detection_probabilities_are_fitted": True,
            "channels": ["symptomatic", "asymptomatic"],
            "source": "observation_events_only",
            "no_real_jersey_data": True,
        },
        "seeds": {
            "target_process_seeds": list(TARGET_PROCESS_SEEDS),
            "target_observation_seeds": list(TARGET_OBSERVATION_SEEDS),
            "target_observation_config_id": TARGET_OBSERVATION_CONFIG_ID,
            "candidate_process_seeds": list(FIT_PROCESS_SEEDS),
            "candidate_observation_seeds": list(FIT_OBSERVATION_SEEDS),
            "candidate_observation_config_id": FIT_OBSERVATION_CONFIG_ID,
            "optimizer_seed": None,
            "replacement_seeds": False,
        },
        "objective": {
            "name": "square_root_minimum_distance",
            "poisson_variance_stabilizer": 0.375,
            "candidate_replicate_mean": "arithmetic_mean_of_three",
            "channel_weight": "equal",
            "date_weight": "equal",
            "all_cells_scored_before_selection": True,
            "likelihood": False,
        },
        "identifiability": {
            "tie_scale": 1.0e-12,
            "profile_gap": 0.05,
            "profile_denominator_floor": 1.0e-12,
            "exact_global_tie": "fail",
            "lexicographic_tie_break": "forbidden",
        },
        "misspecification": {
            "p0_2a": {
                "truth_reporting_delay_days": 2,
                "fitted_reporting_delay_days": 0,
                "grid_cells": 81,
                "common_random_number_namespace_unchanged": True,
            },
            "p0_2b": {
                "truth_detection_probabilities": {"symptomatic": 0.75, "asymptomatic": 0.25},
                "common_probability_grid": [0.25, 0.50, 0.75],
                "grid_cells": 27,
            },
            "detection": {
                "relative_loss_degradation_minimum": 0.25,
                "channel_total_error_minimum": 0.25,
                "p0_2a_minimum_detected_targets": 3,
                "p0_2b_minimum_detected_targets": 4,
                "tie_scale": 1.0e-12,
            },
        },
        "negative_control": {
            "beta_grid": [0.04, 0.08, 0.16],
            "global_route_factor_grid": [0.5, 1.0, 2.0],
            "route_multiplier_scope": "all_eleven_routes_uniformly",
            "fixed_inoculation_day_offset": 2,
            "fixed_detection_probabilities": {"symptomatic": 0.75, "asymptomatic": 0.25},
            "equal_product_route_beta": 0.08,
            "vector_tolerance": 1.0e-12,
            "objective_spread_scale": 1.0e-12,
            "structural_classification": "NON_IDENTIFIED_STRUCTURAL",
            "factor_estimate": None,
            "standard_error": "absent",
            "interval": "absent",
            "coverage": "absent",
        },
        "acceptance": {
            "descriptive_coverage_minimum": 0.8,
            "joint_coverage_minimum": 0.6,
            "boundary_fraction_maximum": 0.2,
            "truth_inoculation_acquisitions": 10,
            "truth_minimum_local_secondary_infections": 1,
            "truth_minimum_reports_per_channel": 1,
            "truth_minimum_nonzero_combined_report_dates": 3,
            "real_data_used": False,
            "nominal_coverage_claim": False,
            "calibration_claim": False,
        },
        "budget_caps": {
            "p0_1_grid_cells": 81,
            "p0_2_wrong_delay_cells": 81,
            "p0_2_wrong_regime_cells": 27,
            "p0_3_cells": 9,
            "total_cells": 198,
            "truth_latent_outbreak_calls": 5,
            "p0_1_p0_2_candidate_latent_outbreak_calls": 27,
            "p0_3_latent_outbreak_calls": 27,
            "total_latent_outbreak_calls": 59,
            "p0_1_observation_transforms": 248,
            "total_observation_transforms": 599,
            "distinct_population_network_seed_builds": 8,
            "duration_days": 30,
            "mode": "ci",
        },
        "implementation": {
            "implemented_arms": ["p0_1", "p0_2a", "p0_2b", "p0_3"],
            "required_arms": ["p0_1", "p0_2a", "p0_2b", "p0_3"],
            "retries": 0,
            "adaptive_grid": False,
            "replacement_seeds": False,
        },
    }

    profile = frozen_profile(str(payload.get("campaign_id", "")))
    expected["campaign_id"] = profile.campaign_id
    expected["predeclaration_sha256"] = profile.predeclaration_sha256
    expected["dimensions"] = {
        name: {
            "truth": truth,
            "candidates": list(candidates),
            "tolerance": tolerance,
            "bias_limit": bias_limit,
        }
        for name, truth, candidates, tolerance, bias_limit in profile.dimensions
    }
    expected["seeds"] = {
        **expected["seeds"],
        "target_process_seeds": list(profile.target_process_seeds),
        "target_observation_seeds": list(profile.target_observation_seeds),
        "target_observation_config_id": profile.target_observation_config_id,
        "candidate_process_seeds": list(profile.candidate_process_seeds),
        "candidate_observation_seeds": list(profile.candidate_observation_seeds),
        "candidate_observation_config_id": profile.candidate_observation_config_id,
    }
    expected["misspecification"]["p0_2a"]["grid_cells"] = profile.p02a_cells
    expected["misspecification"]["p0_2b"]["grid_cells"] = profile.p02b_cells
    expected["misspecification"]["p0_2b"]["common_probability_grid"] = list(
        PHASE0B_P02B_COMMON_PROBABILITY_GRID
        if profile is PHASE0B_PROFILE
        else P02B_COMMON_PROBABILITY_GRID
    )
    if profile is PHASE0B_PROFILE:
        expected["negative_control"]["beta_grid"] = list(PHASE0B_P03_BETA_GRID)
        expected["negative_control"]["global_route_factor_grid"] = list(
            PHASE0B_P03_ROUTE_FACTOR_GRID
        )
    expected["budget_caps"] = {
        **expected["budget_caps"],
        "p0_1_grid_cells": profile.p01_cells,
        "p0_2_wrong_delay_cells": profile.p02a_cells,
        "p0_2_wrong_regime_cells": profile.p02b_cells,
        "total_cells": profile.total_cells,
        "truth_latent_outbreak_calls": profile.truth_latent_calls,
        "p0_1_p0_2_candidate_latent_outbreak_calls": profile.candidate_latent_calls,
        "total_latent_outbreak_calls": profile.total_latent_calls,
        "p0_1_observation_transforms": profile.p01_transforms,
        "total_observation_transforms": profile.total_transforms,
        "distinct_population_network_seed_builds": profile.network_builds,
    }
    if profile.owner_ruling_path is not None:
        expected["owner_ruling_path"] = profile.owner_ruling_path
        expected["owner_ruling_sha256"] = profile.owner_ruling_sha256

    def compare(section: str, actual: Any, declared: Any) -> None:
        if isinstance(declared, dict):
            if not isinstance(actual, Mapping):
                raise CampaignError(f"frozen declaration section {section!r} must be a mapping")
            if set(actual) != set(declared):
                raise CampaignError(f"frozen declaration keys changed in {section!r}")
            for key, expected_value in declared.items():
                compare(f"{section}.{key}", actual[key], expected_value)
            return
        if isinstance(declared, list):
            if not isinstance(actual, list) or actual != declared:
                raise CampaignError(f"frozen declaration changed at {section}")
            return
        if type(actual) is not type(declared) or actual != declared:
            raise CampaignError(f"frozen declaration changed at {section}")

    compare("campaign", dict(payload), expected)
    if (
        not isinstance(payload.get("g29_ruling_sha256"), str)
        or len(payload["g29_ruling_sha256"]) != 64
    ):
        raise CampaignError("G29 ruling SHA-256 must be a 64-character hexadecimal digest")
    try:
        int(payload["g29_ruling_sha256"], 16)
    except ValueError as exc:
        raise CampaignError("G29 ruling SHA-256 must be hexadecimal") from exc
    routes = payload["fixed_scenario"]["route_multipliers"]
    if tuple(routes) != P01_ROUTE_IDS:
        raise CampaignError("route multipliers changed order or coverage")


def validate_campaign_config(config: CampaignConfig, budget_caps: Mapping[str, Any]) -> None:
    """Reject any declaration that departs from its independently frozen profile."""

    profile = config.profile
    if config.mode != "ci":
        message = (
            "Phase 0 is declared for mode 'ci' only"
            if profile is PHASE0_PROFILE
            else "Phase 0b is declared for mode 'ci' only"
        )
        raise BudgetError(message)
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
        name: (
            float(truth),
            tuple(float(value) for value in candidates),
            float(tolerance),
            float(bias_limit),
        )
        for name, truth, candidates, tolerance, bias_limit in profile.dimensions
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
    if config.target_process_seeds != profile.target_process_seeds:
        raise CampaignError("target process seed schedule does not match the declaration")
    if config.target_observation_seeds != profile.target_observation_seeds:
        raise CampaignError("target observation seed schedule does not match the declaration")
    if config.candidate_process_seeds != profile.candidate_process_seeds:
        raise CampaignError("candidate process seed schedule does not match the declaration")
    if config.candidate_observation_seeds != profile.candidate_observation_seeds:
        raise CampaignError("candidate observation seed schedule does not match the declaration")
    if config.target_observation_config_id != profile.target_observation_config_id:
        raise CampaignError("target observation namespace does not match the declaration")
    if config.candidate_observation_config_id != profile.candidate_observation_config_id:
        raise CampaignError("candidate observation namespace does not match the declaration")
    if config.expected_predeclaration_sha256 != profile.predeclaration_sha256:
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
    other_profile = PHASE0_PROFILE if profile is PHASE0B_PROFILE else PHASE0B_PROFILE
    other_seed_sets = (
        set(other_profile.target_process_seeds),
        set(other_profile.target_observation_seeds),
        set(other_profile.candidate_process_seeds),
        set(other_profile.candidate_observation_seeds),
    )
    if any(left & right for left in seed_sets for right in other_seed_sets):
        raise BudgetError("campaign seed namespaces overlap the other frozen profile")
    if config.retries != 0 or config.adaptive_grid or config.replacement_seeds:
        raise BudgetError("retries, adaptive grids and replacement seeds are forbidden")
    if config.required_arms != ("p0_1", "p0_2a", "p0_2b", "p0_3"):
        raise CampaignError("required arm declaration is incomplete or reordered")
    if config.g29_ruling_path != G29_RULING_PATH:
        raise CampaignError("G29 ruling path does not match the accepted ruling")
    if config.g29_ruling_sha256 != G29_RULING_SHA256:
        raise CampaignError("G29 ruling SHA-256 does not match the accepted ruling")
    if config.g29_ruling_sha256 != config.declaration.get("g29_ruling_sha256"):
        raise CampaignError("G29 ruling SHA-256 does not match the frozen config")
    if (
        config.owner_ruling_path != profile.owner_ruling_path
        or config.owner_ruling_sha256 != profile.owner_ruling_sha256
    ):
        raise CampaignError("model-owner ruling declaration does not match the frozen profile")
    negative_control = config.declaration.get("negative_control")
    if not isinstance(negative_control, Mapping):
        raise CampaignError("P0-3 negative-control declaration is missing")
    p03_beta_grid, p03_route_factor_grid = _p03_grids(config)
    if (
        tuple(float(value) for value in negative_control["beta_grid"]) != p03_beta_grid
        or tuple(float(value) for value in negative_control["global_route_factor_grid"])
        != p03_route_factor_grid
        or float(negative_control["vector_tolerance"]) != P03_VECTOR_TOLERANCE
        or float(negative_control["objective_spread_scale"]) != P03_OBJECTIVE_SPREAD_SCALE
        or negative_control["structural_classification"] != "NON_IDENTIFIED_STRUCTURAL"
        or negative_control["factor_estimate"] is not None
    ):
        raise CampaignError("P0-3 runtime controls do not match the frozen declaration")
    if config.implemented_arms != ("p0_1", "p0_2a", "p0_2b", "p0_3"):
        raise CampaignError("implemented arm declaration is incomplete or reordered")
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
    """Calculate all-arm counts before any simulation could be called."""

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
    p03_observation_transforms = P03_OBSERVATION_TRANSFORMS
    p01_observation_transforms = len(config.target_process_seeds) + p01_cells * len(
        config.candidate_process_seeds
    )
    total_observation_transforms = (
        p01_observation_transforms
        + p01_cells * len(config.candidate_process_seeds)
        + p02_wrong_regime_cells * len(config.candidate_process_seeds)
        + p03_observation_transforms
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
        p03_observation_transforms=p03_observation_transforms,
        total_latent_calls=truth_latent_calls + candidate_latent_calls + p03_latent_calls,
        p01_observation_transforms=p01_observation_transforms,
        total_observation_transforms=total_observation_transforms,
        distinct_network_seed_builds=len(
            set(config.target_process_seeds) | set(config.candidate_process_seeds)
        ),
        duration_days=config.duration_days,
        mode=config.mode,
        implemented_arms=config.implemented_arms,
        implemented_cells=(
            p01_cells
            + (p02_wrong_delay_cells if "p0_2a" in config.implemented_arms else 0)
            + (p02_wrong_regime_cells if "p0_2b" in config.implemented_arms else 0)
            + (p03_cells if "p0_3" in config.implemented_arms else 0)
        ),
        implemented_latent_calls=(
            truth_latent_calls
            + candidate_latent_calls
            + (p03_latent_calls if "p0_3" in config.implemented_arms else 0)
        ),
        implemented_observation_transforms=(
            p01_observation_transforms
            + (
                p02_wrong_delay_cells * len(config.candidate_process_seeds)
                if "p0_2a" in config.implemented_arms
                else 0
            )
            + (
                p02_wrong_regime_cells * len(config.candidate_process_seeds)
                if "p0_2b" in config.implemented_arms
                else 0
            )
            + (p03_observation_transforms if "p0_3" in config.implemented_arms else 0)
        ),
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
    profile = config.profile
    other_profile = PHASE0_PROFILE if profile is PHASE0B_PROFILE else PHASE0B_PROFILE
    other_seed_sets = (
        set(other_profile.target_process_seeds),
        set(other_profile.target_observation_seeds),
        set(other_profile.candidate_process_seeds),
        set(other_profile.candidate_observation_seeds),
    )
    if any(left & right for left in seed_sets for right in other_seed_sets):
        raise BudgetError("seed namespaces overlap the other frozen profile")
    if plan.mode != "ci":
        raise BudgetError("execution mode must be ci")
    if plan.duration_days > MAX_DURATION_DAYS:
        raise BudgetError("predicted duration exceeds 30 days")
    if plan.p01_cells != profile.p01_cells:
        if profile is PHASE0_PROFILE and plan.p01_cells > P01_GRID_CELLS:
            raise BudgetError("P0-1 grid exceeds its declared 81-cell cap")
        raise BudgetError("P0-1 grid does not match its exact frozen-profile cell count")
    if (
        plan.p02_wrong_delay_cells != profile.p02a_cells
        or plan.p02_wrong_regime_cells != profile.p02b_cells
    ):
        raise BudgetError("P0-2 grids do not match their exact frozen-profile cell counts")
    if (
        plan.p03_cells != 9
        or plan.p03_latent_calls != 27
        or plan.p03_observation_transforms != P03_OBSERVATION_TRANSFORMS
    ):
        raise BudgetError("P0-3 grid or latent calls do not match their declared caps")
    if (
        plan.total_cells != profile.total_cells
        or plan.truth_latent_calls != profile.truth_latent_calls
        or plan.p01_p02_candidate_latent_calls != profile.candidate_latent_calls
        or plan.p03_latent_calls != profile.p03_latent_calls
        or plan.total_latent_calls != profile.total_latent_calls
        or plan.p01_observation_transforms != profile.p01_transforms
        or plan.total_observation_transforms != profile.total_transforms
        or plan.distinct_network_seed_builds != profile.network_builds
    ):
        raise BudgetError("calculated workload does not match the exact frozen-profile caps")
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


def _model_payload(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _model_payload(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_model_payload(item) for item in value]
    if hasattr(value, "model_dump"):
        return _model_payload(value.model_dump(mode="json"))
    if hasattr(value, "__dict__"):
        return _model_payload(dict(value.__dict__))
    return value


def _p01_hash_config_payload(config: CampaignConfig) -> dict[str, Any]:
    """Keep accepted P0-1 input hashes stable as later-arm metadata is added."""

    payload = asdict(config)
    payload.pop("g29_ruling_path", None)
    payload.pop("g29_ruling_sha256", None)
    payload.pop("owner_ruling_path", None)
    payload.pop("owner_ruling_sha256", None)
    for dimension in payload["dimensions"]:
        dimension.pop("truth_decimal", None)
        dimension.pop("candidate_decimals", None)
        dimension.pop("tolerance_decimal", None)
        dimension.pop("bias_limit_decimal", None)
    payload["implemented_arms"] = ("p0_1",)
    declaration = dict(config.declaration)
    declaration.pop("g29_ruling_path", None)
    declaration.pop("g29_ruling_sha256", None)
    declaration.pop("misspecification", None)
    declaration.pop("negative_control", None)
    implementation = dict(declaration["implementation"])
    implementation["implemented_arms"] = ["p0_1"]
    declaration["implementation"] = implementation
    payload["declaration"] = declaration
    return payload


def candidate_config_hash(
    cell: CandidateCell,
    config: CampaignConfig | None = None,
    *,
    replicate_configs: Sequence[tuple[Any, Any]] | None = None,
) -> str:
    """Hash the actual complete candidate run and observation configurations.

    ``replicate_configs`` is supplied by the adapter after constructing each
    fixed-seed run.  The fallback remains useful for pure scoring fixtures and
    includes the complete frozen declaration rather than a hand-picked subset.
    """

    declaration = (
        _p01_hash_config_payload(config)["declaration"]
        if config is not None and config.declaration
        else {
            "campaign_id": "v13-phase0-synthetic-recovery",
            "mode": "ci",
            "start_date": "2025-01-06",
            "duration_days": 30,
            "observation_horizon_tail_days": 4,
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
            "observation": {
                "target_detection_probabilities": {
                    "symptomatic": 0.75,
                    "asymptomatic": 0.25,
                },
                "channels": ["symptomatic", "asymptomatic"],
            },
            "objective": {
                "name": "square_root_minimum_distance",
                "poisson_variance_stabilizer": 0.375,
                "candidate_replicate_mean": "arithmetic_mean_of_three",
            },
            "identifiability": {
                "tie_scale": TIE_SCALE,
                "profile_gap": PROFILE_GAP,
                "profile_denominator_floor": PROFILE_DENOMINATOR_FLOOR,
            },
        }
    )
    if replicate_configs is None:
        replicate_payload = [
            {
                "process_seed": None,
                "observation_seed": None,
                "run_config": None,
                "observation_config": {"observation_config_id": FIT_OBSERVATION_CONFIG_ID},
            }
        ]
    else:
        replicate_payload = [
            {
                "process_seed": getattr(run_config, "seed", None),
                "observation_seed": getattr(observation_config, "observation_seed", None),
                "run_config": _model_payload(run_config),
                "observation_config": _model_payload(observation_config),
            }
            for run_config, observation_config in replicate_configs
        ]
    payload = {
        "declaration": declaration,
        "campaign_config": _model_payload(_p01_hash_config_payload(config))
        if config is not None
        else None,
        "candidate": cell.as_dict(),
        "replicate_configs": replicate_payload,
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
    expected_grid: Sequence[CandidateCell] | None = None,
    candidate_config_hashes: Mapping[CandidateCell, str] | None = None,
) -> tuple[LossRow, ...]:
    """Score every declared cell, with no selection or truth-dependent shortcut."""

    target = _coerce_tables(target_tables)
    grid = tuple(candidate_grid)
    if len(set(grid)) != len(grid):
        raise CampaignError("candidate grid contains duplicate cells")
    declared_grid = tuple(expected_grid) if expected_grid is not None else _default_grid()
    if require_declared_grid and grid != declared_grid:
        if expected_grid is None:
            raise CampaignError("the P0-1 fitter requires the complete predeclared 81-cell grid")
        raise CampaignError("the fitter requires the complete frozen candidate grid")
    if set(candidate_prediction_library) != set(grid):
        missing = set(grid) - set(candidate_prediction_library)
        extra = set(candidate_prediction_library) - set(grid)
        raise CampaignError(
            f"candidate prediction library is incomplete (missing={missing}, extra={extra})"
        )
    if candidate_config_hashes is not None and set(candidate_config_hashes) != set(grid):
        raise CampaignError("candidate configuration provenance is incomplete")
    rows = tuple(
        LossRow(
            cell=cell,
            objective=minimum_distance_loss(target, candidate_prediction_library[cell]),
            config_hash=(
                candidate_config_hashes[cell]
                if candidate_config_hashes is not None
                else candidate_config_hash(cell)
            ),
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
    *,
    candidate_config_hashes: Mapping[CandidateCell, str] | None = None,
    expected_grid: Sequence[CandidateCell] | None = None,
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
        expected_grid=expected_grid,
        candidate_config_hashes=candidate_config_hashes,
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
    namespace_passed: bool = False,
    persisted_estimate_path: Path | None = None,
    config: CampaignConfig | None = None,
) -> RecoveryRow:
    """Join truth only after the blind estimate and estimate hash exist."""

    if not fit.estimate_hash or len(fit.estimate_hash) != 64:
        raise CampaignError("blind estimate must be hashed before truth evaluation")
    if persisted_estimate_path is not None:
        if not persisted_estimate_path.is_file():
            raise CampaignError("blind estimate must be persisted before truth evaluation")
        try:
            persisted = json.loads(persisted_estimate_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CampaignError("persisted blind estimate cannot be read") from exc
        if persisted.get("estimate_hash") != fit.estimate_hash:
            raise CampaignError("persisted blind estimate hash does not match the fit")
    exact_values: dict[str, tuple[Decimal, Decimal]] = {}
    if config is not None and fit.selected is not None:
        for dimension in config.dimensions:
            selected_value = float(getattr(fit.selected, dimension.name))
            estimate = next(
                (
                    decimal
                    for candidate, decimal in zip(
                        dimension.candidates, dimension.exact_candidates(), strict=True
                    )
                    if candidate == selected_value
                ),
                None,
            )
            if estimate is None:
                raise CampaignError("selected estimate is outside the exact declared grid")
            exact_values[dimension.name] = (estimate, dimension.exact_truth())
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
        exact_estimate_truth=exact_values,
    )


def _boundary_value(value: float, dimension: DimensionSpec) -> bool:
    return value in {dimension.candidates[0], dimension.candidates[-1]}


def _declared_decimal(value: float | int) -> Decimal:
    """Recover exact arithmetic for values declared on the finite decimal grid."""

    return Decimal(str(value))


def evaluate_p01(
    rows: Sequence[RecoveryRow],
    *,
    config: CampaignConfig | None = None,
    workload: WorkloadPlan | None = None,
    evidence: ExecutionEvidence | None = None,
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
    declared_target_seeds = (
        config.target_process_seeds
        if config is not None
        else tuple(row.target_seed for row in rows)
    )
    complete = len(rows) == expected_count and tuple(row.target_seed for row in rows) == tuple(
        declared_target_seeds
    )
    evidence_complete = bool(
        config is not None
        and workload is not None
        and evidence is not None
        and evidence.matches(config, workload)
    )
    coverage: dict[str, float | None] = {}
    bias: dict[str, float | None] = {}
    boundary_counts: dict[str, int] = {}
    descriptive_predicates: dict[str, bool] = {}
    serial_rows: list[dict[str, Any]] = []
    for dimension in dimensions:
        tolerance = dimension.exact_tolerance()
        bias_limit = dimension.exact_bias_limit()
        values: list[Decimal] = []
        covered = 0
        boundary_count = 0
        for row in rows:
            error = row._absolute_error_decimal(dimension.name)
            profile = next(
                (item for item in row.profiles if item.dimension == dimension.name), None
            )
            identified = profile is not None and profile.identified and not row.numerical_tie
            if identified and error is not None and error <= tolerance:
                covered += 1
            signed = row._signed_error_decimal(dimension.name)
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
                    "signed_error": None if signed is None else float(signed),
                    "absolute_error": None if error is None else float(error),
                    "identified": identified,
                }
            )
        coverage[dimension.name] = covered / expected_count if complete else None
        bias_decimal = (
            sum(values, Decimal("0")) / Decimal(len(values))
            if len(values) == expected_count
            else None
        )
        bias[dimension.name] = None if bias_decimal is None else float(bias_decimal)
        boundary_counts[dimension.name] = boundary_count
        coverage_value = coverage[dimension.name]
        descriptive_predicates[f"coverage_{dimension.name}"] = bool(
            complete and coverage_value is not None and coverage_value >= 4 / 5
        )
        descriptive_predicates[f"bias_{dimension.name}"] = bool(
            complete and bias_decimal is not None and abs(bias_decimal) <= bias_limit
        )
        descriptive_predicates[f"boundary_{dimension.name}"] = boundary_count <= 1
    joint_hits = 0
    joint_hits_by_seed: dict[int, bool] = {}
    for row in rows:
        joint_row = not row.numerical_tie
        if joint_row:
            for dimension in dimensions:
                error = row._absolute_error_decimal(dimension.name)
                identified = any(
                    profile.dimension == dimension.name and profile.identified
                    for profile in row.profiles
                )
                if not identified or error is None or error > dimension.exact_tolerance():
                    joint_row = False
                    break
        joint_hits_by_seed[row.target_seed] = joint_row
        if joint_row:
            joint_hits += 1
    if config is not None and config.profile is PHASE0B_PROFILE:
        recovery_by_seed = {row.target_seed: row for row in rows}
        for serialized in serial_rows:
            dimension = config.dimension_map[str(serialized["dimension"])]
            estimate = serialized["estimate"]
            recovery = recovery_by_seed[int(serialized["target_seed"])]
            error = recovery._absolute_error_decimal(dimension.name)
            diagnostics = recovery.truth_diagnostics
            serialized["selected_at_grid_boundary"] = estimate in {
                dimension.candidates[0],
                dimension.candidates[-1],
            }
            serialized.update(
                {
                    "within_tolerance_hit": (
                        error is not None and error <= dimension.exact_tolerance()
                    ),
                    "joint_hit": joint_hits_by_seed[recovery.target_seed],
                    "numerical_tie": recovery.numerical_tie,
                    "truth_inoculation_acquisitions": diagnostics.inoculation_acquisitions,
                    "truth_local_secondary_infections": diagnostics.local_secondary_infections,
                    "truth_symptomatic_reports": diagnostics.symptomatic_reports,
                    "truth_asymptomatic_reports": diagnostics.asymptomatic_reports,
                    "truth_nonzero_combined_report_dates": (
                        diagnostics.nonzero_combined_report_dates
                    ),
                    "truth_complete": diagnostics.complete,
                    "truth_viable": diagnostics.viable,
                    "truth_chronology_pass": diagnostics.chronology_passed,
                    "truth_latent_incidence_conservation_pass": (
                        diagnostics.latent_incidence_conservation_passed
                    ),
                    "truth_namespace_pass": diagnostics.namespace_passed,
                    "namespace_pass": recovery.namespace_passed,
                }
            )
            serialized["boundary_count"] = boundary_counts[dimension.name]
    joint_coverage = joint_hits / expected_count if complete else None
    predicates: dict[str, bool] = {
        "all_target_runs_and_cells_complete": complete
        and evidence_complete
        and all(
            row.scored_cell_count
            == (config.profile.p01_cells if config is not None else P01_GRID_CELLS)
            and not row.numerical_tie
            for row in rows
        ),
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
        and evidence_complete
        and all(row.namespace_passed and row.truth_diagnostics.namespace_passed for row in rows),
        "workload_within_caps": bool(
            workload is not None
            and evidence_complete
            and workload.p01_cells
            == (config.profile.p01_cells if config is not None else P01_GRID_CELLS)
            and workload.p01_latent_calls
            == (
                config.profile.truth_latent_calls + config.profile.candidate_latent_calls
                if config is not None
                else P01_LATENT_CALLS
            )
            and workload.p01_observation_transforms
            == (config.profile.p01_transforms if config is not None else P01_OBSERVATION_TRANSFORMS)
        ),
        "measured_execution_evidence": evidence_complete,
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
    namespace_passed: bool = False,
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


def _truth_cell(config: CampaignConfig) -> CandidateCell:
    dimensions = config.dimension_map
    return CandidateCell(
        beta=dimensions["beta"].truth,
        inoculation_day_offset=int(dimensions["inoculation_day_offset"].truth),
        symptomatic_detection_probability=dimensions["symptomatic_detection_probability"].truth,
        asymptomatic_detection_probability=dimensions["asymptomatic_detection_probability"].truth,
    )


def _run_config_for_cell(
    config: CampaignConfig,
    parameters: RespiratoryParameterSet,
    process_seed: int,
    cell: CandidateCell,
) -> OutbreakRunConfig:
    """Construct one real JOS run config from the frozen cell controls."""

    base = default_run_config(
        cast(PopulationMode, config.mode),
        process_seed,
        parameters,
        start_date=config.start_date,
        duration_days=config.duration_days,
    )
    import_date = config.start_date + timedelta(days=cell.inoculation_day_offset)
    run_config = base.model_copy(
        update={
            "initial_seed_count": config.initial_seed_count,
            "import_schedule": {import_date.isoformat(): config.inoculation_attempts},
            "import_rate_per_day": config.import_rate_per_day,
            "beta": cell.beta,
            "symptomatic_probability": config.symptomatic_probability,
            "waning_enabled": config.waning_enabled,
            "route_multipliers": dict(config.route_multipliers),
        }
    )
    if (
        run_config.mode != config.mode
        or run_config.seed != process_seed
        or run_config.start_date != config.start_date
        or run_config.duration_days != config.duration_days
        or run_config.initial_seed_count != 0
        or run_config.import_schedule != {import_date.isoformat(): 10}
        or run_config.import_rate_per_day != 0.0
        or run_config.beta != cell.beta
        or run_config.symptomatic_probability != 0.6
        or run_config.waning_enabled
        or dict(run_config.route_multipliers) != dict(config.route_multipliers)
        or getattr(run_config.latent_duration, "family", None) != "constant"
        or getattr(run_config.latent_duration, "mean_days", None) != 2.0
        or getattr(run_config.infectious_duration, "family", None) != "constant"
        or getattr(run_config.infectious_duration, "mean_days", None) != 5.0
    ):
        raise CampaignError("constructed outbreak config does not match the frozen scenario")
    return run_config


def _observation_config_for_cell(
    root: Path,
    config: CampaignConfig,
    observation_seed: int,
    config_id: str,
    cell: CandidateCell,
    *,
    reporting_delay_days: int | None = None,
) -> ObservationConfig:
    """Construct one fixed-seed observation namespace from the real schema."""

    base = load_observation_config(root)
    parameters = dict(base.parameters)
    parameters["symptomatic_detection_probability"] = parameters[
        "symptomatic_detection_probability"
    ].model_copy(update={"value": cell.symptomatic_detection_probability})
    parameters["asymptomatic_detection_probability"] = parameters[
        "asymptomatic_detection_probability"
    ].model_copy(update={"value": cell.asymptomatic_detection_probability})
    expected_reporting_delay = (
        config.reporting_delay_days if reporting_delay_days is None else reporting_delay_days
    )
    reporting_delay = base.reporting_delay.model_copy(update={"days": (expected_reporting_delay,)})
    observation = base.model_copy(
        update={
            "observation_config_id": config_id,
            "parameters": parameters,
            "observation_seed": observation_seed,
            "analysis_horizon_tail_days": config.observation_horizon_tail_days,
            "day_of_week_effect": config.weekday_effect,
            "reporting_delay": reporting_delay,
        }
    )
    if (
        observation.observation_config_id != config_id
        or observation.observation_seed != observation_seed
        or observation.analysis_horizon_tail_days != P01_TAIL_DAYS
        or observation.reporting_delay.kind != "fixed"
        or observation.reporting_delay.days != (expected_reporting_delay,)
        or observation.detection_delay.kind != "fixed"
        or observation.detection_delay.days != (0,)
        or observation.day_of_week_effect != (1.0,) * 7
    ):
        raise CampaignError("constructed observation config does not match the frozen scenario")
    return observation


def _observed_tables_from_result(result: Any) -> ObservedTables:
    try:
        events = result.observation_events
    except AttributeError as exc:
        raise CampaignError("observation adapter returned no observation_events") from exc
    return observed_tables_from_events(
        events,
        dates=observation_dates(P01_START_DATE, P01_DURATION_DAYS, P01_TAIL_DAYS),
    )


def _observed_table_sha256(table: ObservedTables) -> str:
    return hashlib.sha256(
        json.dumps(table.as_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _truth_diagnostics_from_result(
    latent_result: Any,
    observation_result: Any,
    tables: ObservedTables,
    *,
    namespace_passed: bool,
) -> TruthDiagnostics:
    latent_events = getattr(latent_result, "transmission_events", None)
    if latent_events is None:
        raise CampaignError("latent adapter returned no transmission_events")
    latent_diagnostics = getattr(latent_result, "diagnostics", {})
    observation_diagnostics = getattr(observation_result, "diagnostics", {})
    natural_history = latent_diagnostics.get("natural_history", {})
    states = latent_diagnostics.get("states", {})
    observation_rng = observation_diagnostics.get("observation_rng", {})
    latent_config = getattr(latent_result, "config", None)
    observation_config = getattr(observation_result, "config", None)
    expected_fingerprint = None
    if latent_config is not None and observation_config is not None:
        expected_fingerprint = hashlib.sha256(
            str(observation_stream_seed(latent_config.seed, observation_config)).encode("utf-8")
        ).hexdigest()
    chronology_passed = bool(
        natural_history.get("chronology_passed", False)
        and observation_diagnostics.get("no_report_before_infection", False)
    )
    conservation_passed = bool(
        states.get("conserved", False)
        and observation_diagnostics.get("latent_incidence_conservation", False)
    )
    diagnostics = truth_diagnostics_from_events(
        latent_events,
        tables,
        chronology_passed=chronology_passed,
        latent_incidence_conservation_passed=conservation_passed,
        namespace_passed=namespace_passed,
    )
    return TruthDiagnostics(
        inoculation_acquisitions=diagnostics.inoculation_acquisitions,
        local_secondary_infections=diagnostics.local_secondary_infections,
        symptomatic_reports=diagnostics.symptomatic_reports,
        asymptomatic_reports=diagnostics.asymptomatic_reports,
        nonzero_combined_report_dates=diagnostics.nonzero_combined_report_dates,
        chronology_passed=diagnostics.chronology_passed,
        latent_incidence_conservation_passed=diagnostics.latent_incidence_conservation_passed,
        namespace_passed=diagnostics.namespace_passed,
        complete=True,
        raw_values={
            "natural_history": _model_payload(natural_history),
            "latent_states": _model_payload(states),
            "observation_chronology_and_conservation": {
                key: _model_payload(observation_diagnostics.get(key))
                for key in (
                    "status",
                    "latent_event_count",
                    "reported_case_count",
                    "no_report_before_infection",
                    "chronology_violations",
                    "latent_incidence_conservation_difference",
                    "latent_incidence_conservation",
                    "analysis_horizon",
                )
                if key in observation_diagnostics
            },
            "observed_report_counts": {
                "symptomatic": diagnostics.symptomatic_reports,
                "asymptomatic": diagnostics.asymptomatic_reports,
                "nonzero_combined_dates": diagnostics.nonzero_combined_report_dates,
            },
            "namespace_verification": {
                "verified": namespace_passed,
                "process_seed": getattr(latent_config, "seed", None),
                "observation_seed": getattr(observation_config, "observation_seed", None),
                "observation_config_id": getattr(observation_config, "observation_config_id", None),
                "stream_namespace": observation_rng.get("stream_namespace"),
                "stream_key_inputs": _model_payload(observation_rng.get("stream_key_inputs")),
                "observed_fingerprint": observation_rng.get("stream_fingerprint"),
                "recomputed_fingerprint": expected_fingerprint,
            },
        },
    )


def persist_blind_estimate(path: Path, fit: BlindFitResult) -> str:
    """Durably write a truth-free estimate before any truth join is allowed."""

    if not fit.estimate_hash or len(fit.estimate_hash) != 64:
        raise CampaignError("cannot persist an unhashed blind estimate")
    expected = fit.as_dict()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        persisted = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise CampaignError(f"blind estimate read-back failed for {path.name}: {exc}") from exc
    if not isinstance(persisted, dict) or json.dumps(
        persisted, sort_keys=True, separators=(",", ":")
    ) != json.dumps(expected, sort_keys=True, separators=(",", ":")):
        raise CampaignError(f"blind estimate read-back mismatch for {path.name}")
    persisted_hash = persisted.get("estimate_hash")
    if not isinstance(persisted_hash, str):
        raise CampaignError(f"blind estimate read-back has no hash for {path.name}")
    return persisted_hash


def run_p01_campaign(
    config_path: Path,
    predeclaration_path: Path,
    work_dir: Path,
    *,
    root: Path | None = None,
) -> P01CampaignResult:
    """Run the callable P0-1 adapter against existing JOS API boundaries.

    This function is intentionally separate from the public CLI.  The CLI
    remains blocked until P0-3 and independent all-arms review are complete.
    """

    config = CampaignConfig.from_yaml(config_path)
    validate_predeclaration(predeclaration_path, config.expected_predeclaration_sha256)
    workload = guard_workload(config)
    profile = config.profile
    project_root = (root or config_path.resolve().parents[2]).resolve()
    parameters = load_parameter_set(project_root)
    target_truth = _truth_cell(config)
    process_seeds = (*config.target_process_seeds, *config.candidate_process_seeds)
    parents: dict[int, Any] = {}
    try:
        for process_seed in process_seeds:
            if len(parents) >= profile.network_builds:
                raise BudgetError("population/network seed build cap reached before dispatch")
            parents[process_seed] = build_parent(
                project_root,
                cast(PopulationMode, config.mode),
                process_seed,
                work_dir / "parents" / str(process_seed),
                write_m4=True,
            ).generated

        target_tables: dict[int, ObservedTables] = {}
        target_config_hashes: dict[int, str] = {}
        target_observation_hashes: dict[int, str] = {}
        target_namespace_fingerprints: dict[int, str] = {}
        target_outputs: dict[int, tuple[Any, Any, bool]] = {}
        measured_latent_calls = 0
        measured_observation_transforms = 0
        for process_seed, observation_seed in zip(
            config.target_process_seeds, config.target_observation_seeds, strict=True
        ):
            run_config = _run_config_for_cell(config, parameters, process_seed, target_truth)
            observation_config = _observation_config_for_cell(
                project_root,
                config,
                observation_seed,
                config.target_observation_config_id,
                target_truth,
            )
            if measured_latent_calls >= profile.truth_latent_calls + profile.candidate_latent_calls:
                raise BudgetError("P0-1 latent call cap reached before dispatch")
            latent_result = run_outbreak(parents[process_seed], run_config, parameters)
            measured_latent_calls += 1
            if measured_observation_transforms >= profile.p01_transforms:
                raise BudgetError("P0-1 observation transform cap reached before dispatch")
            observation_result = observe_latent_run(latent_result, observation_config)
            measured_observation_transforms += 1
            target_tables[process_seed] = _observed_tables_from_result(observation_result)
            target_config_hashes[process_seed] = candidate_config_hash(
                target_truth, config, replicate_configs=((run_config, observation_config),)
            )
            target_observation_hashes[process_seed] = hashlib.sha256(
                json.dumps(
                    target_tables[process_seed].as_dict(), sort_keys=True, separators=(",", ":")
                ).encode("utf-8")
            ).hexdigest()
            validate_observation_calendar(
                target_tables[process_seed],
                start_date=config.start_date,
                duration_days=config.duration_days,
                tail_days=config.observation_horizon_tail_days,
            )
            target_namespace_passed = _namespace_passes(
                latent_result, observation_result, run_config, observation_config
            )
            target_rng = observation_result.diagnostics.get("observation_rng", {})
            target_namespace_fingerprints[process_seed] = str(
                target_rng.get("stream_fingerprint", "")
            )
            target_outputs[process_seed] = (
                latent_result,
                observation_result,
                target_namespace_passed,
            )

        candidate_latents: dict[tuple[int, float, int], tuple[Any, OutbreakRunConfig]] = {}
        latent_cells = tuple(
            (beta, int(offset))
            for beta in config.dimension_map["beta"].candidates
            for offset in config.dimension_map["inoculation_day_offset"].candidates
        )
        first_candidate = config.candidate_grid[0]
        for process_seed in config.candidate_process_seeds:
            for beta, offset in latent_cells:
                latent_cell = CandidateCell(
                    beta=beta,
                    inoculation_day_offset=offset,
                    symptomatic_detection_probability=first_candidate.symptomatic_detection_probability,
                    asymptomatic_detection_probability=first_candidate.asymptomatic_detection_probability,
                )
                run_config = _run_config_for_cell(config, parameters, process_seed, latent_cell)
                if (
                    measured_latent_calls
                    >= profile.truth_latent_calls + profile.candidate_latent_calls
                ):
                    raise BudgetError("P0-1 latent call cap reached before dispatch")
                latent_result = run_outbreak(parents[process_seed], run_config, parameters)
                measured_latent_calls += 1
                candidate_latents[(process_seed, beta, offset)] = (latent_result, run_config)

        candidate_predictions: dict[CandidateCell, tuple[ObservedTables, ...]] = {}
        candidate_observation_hashes: dict[tuple[CandidateCell, int, int], str] = {}
        candidate_hashes: dict[CandidateCell, str] = {}
        candidate_namespace_passed = True
        for cell in config.candidate_grid:
            predictions: list[ObservedTables] = []
            constructed_configs: list[tuple[Any, Any]] = []
            for process_seed, observation_seed in zip(
                config.candidate_process_seeds, config.candidate_observation_seeds, strict=True
            ):
                latent_result, run_config = candidate_latents[
                    (process_seed, cell.beta, cell.inoculation_day_offset)
                ]
                observation_config = _observation_config_for_cell(
                    project_root,
                    config,
                    observation_seed,
                    config.candidate_observation_config_id,
                    cell,
                )
                if measured_observation_transforms >= profile.p01_transforms:
                    raise BudgetError("P0-1 observation transform cap reached before dispatch")
                observation_result = observe_latent_run(latent_result, observation_config)
                measured_observation_transforms += 1
                candidate_namespace_passed = candidate_namespace_passed and _namespace_passes(
                    latent_result, observation_result, run_config, observation_config
                )
                table = _observed_tables_from_result(observation_result)
                validate_observation_calendar(
                    table,
                    start_date=config.start_date,
                    duration_days=config.duration_days,
                    tail_days=config.observation_horizon_tail_days,
                )
                predictions.append(table)
                candidate_observation_hashes[(cell, process_seed, observation_seed)] = (
                    _observed_table_sha256(table)
                )
                constructed_configs.append((run_config, observation_config))
            if len(predictions) != P01_FIT_REPLICATE_COUNT:
                raise CampaignError("candidate cell did not produce exactly three replicates")
            candidate_predictions[cell] = tuple(predictions)
            candidate_hashes[cell] = candidate_config_hash(
                cell, config, replicate_configs=constructed_configs
            )

        blind_fits: dict[int, BlindFitResult] = {}
        recovery_rows: list[RecoveryRow] = []
        for process_seed in config.target_process_seeds:
            fit_kwargs: dict[str, Any] = {"candidate_config_hashes": candidate_hashes}
            if profile is PHASE0B_PROFILE:
                fit_kwargs["expected_grid"] = config.candidate_grid
            fit = fit_blind(
                target_tables[process_seed],
                config.candidate_grid,
                candidate_predictions,
                **fit_kwargs,
            )
            blind_fits[process_seed] = fit
            persist_blind_estimate(work_dir / "blind_estimates" / f"{process_seed}.json", fit)
            latent_result, observation_result, namespace_passed = target_outputs[process_seed]
            diagnostics = _truth_diagnostics_from_result(
                latent_result,
                observation_result,
                target_tables[process_seed],
                namespace_passed=namespace_passed,
            )
            recovery_rows.append(
                join_truth_evaluation(
                    fit,
                    target_seed=process_seed,
                    truth=target_truth,
                    truth_diagnostics=diagnostics,
                    namespace_passed=namespace_passed,
                    persisted_estimate_path=work_dir / "blind_estimates" / f"{process_seed}.json",
                    config=config,
                )
            )
    except CampaignError:
        raise
    except Exception as exc:
        raise CampaignError(f"P0-1 generation failed: {type(exc).__name__}: {exc}") from exc

    evidence = ExecutionEvidence(
        target_process_seeds=config.target_process_seeds,
        target_observation_seeds=config.target_observation_seeds,
        candidate_process_seeds=config.candidate_process_seeds,
        candidate_observation_seeds=config.candidate_observation_seeds,
        target_observation_config_id=config.target_observation_config_id,
        candidate_observation_config_id=config.candidate_observation_config_id,
        target_runs_complete=set(target_tables) == set(config.target_process_seeds),
        candidate_cells_complete=set(candidate_predictions) == set(config.candidate_grid)
        and all(len(value) == P01_FIT_REPLICATE_COUNT for value in candidate_predictions.values()),
        calendars_complete=all(
            table.dates
            == observation_dates(
                config.start_date, config.duration_days, config.observation_horizon_tail_days
            )
            for table in (*target_tables.values(), *candidate_predictions.values())
            for table in (table if isinstance(table, tuple) else (table,))
        ),
        configs_complete=all(len(value) == 64 for value in candidate_hashes.values()),
        namespaces_complete=all(item[2] for item in target_outputs.values())
        and candidate_namespace_passed,
        measured_latent_calls=measured_latent_calls,
        measured_observation_transforms=measured_observation_transforms,
    )
    evaluation = evaluate_p01(
        recovery_rows,
        config=config,
        workload=workload,
        evidence=evidence,
    )
    return P01CampaignResult(
        config=config,
        workload=workload,
        execution_evidence=evidence,
        target_tables=target_tables,
        target_config_hashes=target_config_hashes,
        target_observation_hashes=target_observation_hashes,
        target_namespace_fingerprints=target_namespace_fingerprints,
        candidate_prediction_library=candidate_predictions,
        candidate_observation_hashes=candidate_observation_hashes,
        candidate_config_hashes=candidate_hashes,
        candidate_latents=candidate_latents,
        generated_parents=parents,
        target_truths={seed: target_truth for seed in config.target_process_seeds},
        target_diagnostics={row.target_seed: row.truth_diagnostics for row in recovery_rows},
        blind_fits=blind_fits,
        recovery_rows=tuple(recovery_rows),
        evaluation=evaluation,
    )


def _p02b_grid(config: CampaignConfig) -> tuple[CandidateCell, ...]:
    """Return beta × inoculation × common-ascertainment candidates in declaration order."""

    probabilities = _p02b_common_probability_grid(config)
    return tuple(
        CandidateCell(beta, int(offset), probability, probability)
        for beta in config.dimension_map["beta"].candidates
        for offset in config.dimension_map["inoculation_day_offset"].candidates
        for probability in probabilities
    )


def fit_p02_blind(
    target_tables: ObservedTables | Mapping[str, Sequence[float]],
    candidate_grid: Sequence[CandidateCell],
    candidate_prediction_library: Mapping[CandidateCell, Sequence[ObservedTables]],
    *,
    candidate_config_hashes: Mapping[CandidateCell, str],
    arm: Literal["p0_2a", "p0_2b"],
    config: CampaignConfig | None = None,
) -> BlindFitResult:
    """Fit a complete wrong-model grid from observations and candidates only."""

    target = _coerce_tables(target_tables)
    if target.dates != observation_dates(P01_START_DATE, P01_DURATION_DAYS, P01_TAIL_DAYS):
        raise CampaignError("P0-2 fitter requires the fixed complete campaign calendar")
    grid = tuple(candidate_grid)
    profile = config.profile if config is not None else PHASE0_PROFILE
    common_probability_grid = (
        _p02b_common_probability_grid(config)
        if config is not None
        else P02B_COMMON_PROBABILITY_GRID
    )
    expected_count = profile.p02a_cells if arm == "p0_2a" else profile.p02b_cells
    if len(grid) != expected_count or len(set(grid)) != expected_count:
        raise CampaignError(f"{arm} fitter requires its complete {expected_count}-cell grid")
    declared_grid = config.candidate_grid if config is not None else _default_grid()
    if arm == "p0_2a" and grid != declared_grid:
        raise CampaignError("P0-2A fitter requires the complete frozen P0-1 candidate grid")
    if arm == "p0_2b":
        beta_values = tuple(sorted({cell.beta for cell in grid}))
        offset_values = tuple(sorted({cell.inoculation_day_offset for cell in grid}))
        probability_values = tuple(
            sorted({cell.symptomatic_detection_probability for cell in grid})
        )
        beta_grid = tuple(float(value) for value in profile.dimensions_by_name["beta"][2])
        offset_grid = tuple(
            int(value) for value in profile.dimensions_by_name["inoculation_day_offset"][2]
        )
        expected_grid = tuple(
            CandidateCell(beta, offset, probability, probability)
            for beta in beta_grid
            for offset in offset_grid
            for probability in common_probability_grid
        )
        if (
            beta_values != beta_grid
            or offset_values != offset_grid
            or probability_values != common_probability_grid
            or grid != expected_grid
        ):
            raise CampaignError(
                "P0-2B fitter requires the complete declared common-probability grid"
            )
    surface = score_complete_grid(
        target,
        grid,
        candidate_prediction_library,
        require_declared_grid=False,
        candidate_config_hashes=candidate_config_hashes,
    )
    if len(surface) != expected_count:
        raise CampaignError(f"{arm} fitter did not score every declared candidate")
    minimum = min(row.objective for row in surface)
    tau = TIE_SCALE * max(1.0, minimum)
    minimizers = tuple(row.cell for row in surface if abs(row.objective - minimum) <= tau)
    numerical_tie = len(minimizers) > 1
    selected = None if numerical_tie else minimizers[0]
    if arm == "p0_2a":
        profile_specs = tuple(
            (name, tuple(sorted({float(getattr(cell, name)) for cell in grid})), name)
            for name in P01_DIMENSION_NAMES
        )
    else:
        profile_specs = (
            ("beta", tuple(sorted({cell.beta for cell in grid})), "beta"),
            (
                "inoculation_day_offset",
                tuple(sorted({float(cell.inoculation_day_offset) for cell in grid})),
                "inoculation_day_offset",
            ),
            (
                "common_detection_probability",
                tuple(sorted({cell.symptomatic_detection_probability for cell in grid})),
                "symptomatic_detection_probability",
            ),
        )
    profiles: list[ProfileDiagnostic] = []
    for name, values, attribute in profile_specs:
        profiled = tuple(
            min(
                row.objective
                for row in surface
                if float(getattr(row.cell, attribute)) == float(value)
            )
            for value in values
        )
        profile_minimum = min(profiled)
        profile_tie = sum(abs(value - profile_minimum) <= tau for value in profiled) > 1
        alternatives = sorted({value for value in profiled if value > profile_minimum + tau})
        second = alternatives[0] if alternatives else None
        gap = (
            None
            if second is None
            else (second - profile_minimum) / max(profile_minimum, PROFILE_DENOMINATOR_FLOOR)
        )
        profiles.append(
            ProfileDiagnostic(
                dimension=name,
                values=values,
                profiled_objectives=profiled,
                minimum=profile_minimum,
                second_minimum=second,
                numerical_tie=profile_tie,
                relative_gap=gap,
                identified=not profile_tie and gap is not None and gap >= PROFILE_GAP,
            )
        )
    return BlindFitResult(
        loss_surface=surface,
        minimum_objective=minimum,
        global_minimizers=minimizers,
        numerical_tie=numerical_tie,
        tie_tolerance=tau,
        selected=selected,
        profiles=tuple(profiles),
        identified=not numerical_tie and all(profile.identified for profile in profiles),
        estimate_hash=_estimate_hash(selected, minimum, profiles, numerical_tie, surface),
    )


def _mean_channel_totals(predictions: Sequence[ObservedTables]) -> tuple[float, float]:
    if len(predictions) != P01_FIT_REPLICATE_COUNT:
        raise CampaignError("P0-2 channel totals require exactly three candidate replicates")
    return tuple(
        sum(sum(table.channel_values[index]) for table in predictions) / len(predictions)
        for index in range(2)
    )  # type: ignore[return-value]


def evaluate_p02_target(
    arm: Literal["p0_2a", "p0_2b"],
    *,
    target_seed: int,
    correct_minimum_objective: float,
    wrong_fit: BlindFitResult,
    target_tables: ObservedTables,
    wrong_candidate_prediction_library: Mapping[CandidateCell, Sequence[ObservedTables]],
    truth: CandidateCell,
    config: CampaignConfig,
) -> P02TargetResult:
    """Apply the declared target predicates after persisting the blind fit."""

    denominator = max(correct_minimum_objective, 1e-9)
    if (wrong_fit.numerical_tie and wrong_fit.selected is not None) or (
        not wrong_fit.numerical_tie and wrong_fit.selected is None
    ):
        raise CampaignError("P0-2 fit selected estimate does not match its tie record")
    if wrong_fit.numerical_tie != (len(wrong_fit.global_minimizers) > 1):
        raise CampaignError("P0-2 numerical tie is inconsistent with its minimizer record")
    relative_loss = (wrong_fit.minimum_objective - correct_minimum_objective) / denominator
    relative_loss_detects = relative_loss >= 0.25
    selected = wrong_fit.selected
    channel_error: float | None = None
    clauses: dict[str, bool | None]
    dimension_errors: dict[str, dict[str, float | bool | None]]
    if arm == "p0_2a":
        if wrong_fit.numerical_tie:
            estimate_detects: bool | None = None
            dimension_detects: bool | None = None
            dimension_errors = {
                dimension.name: {
                    "signed_error": None,
                    "absolute_error": None,
                    "outside_tolerance": None,
                }
                for dimension in config.dimensions
            }
        else:
            if selected is None:
                raise CampaignError("unique P0-2A minimum has no selected estimate")
            estimate_detects = selected.inoculation_day_offset == 4
            dimension_errors = {}
            for dimension in config.dimensions:
                signed = dimension.exact_value(getattr(selected, dimension.name)) - (
                    dimension.exact_value(getattr(truth, dimension.name))
                )
                absolute = abs(signed)
                outside = absolute > dimension.exact_tolerance()
                dimension_errors[dimension.name] = {
                    "signed_error": float(signed),
                    "absolute_error": float(absolute),
                    "outside_tolerance": outside,
                }
            dimension_detects = any(
                bool(values["outside_tolerance"]) for values in dimension_errors.values()
            )
        clauses = {
            "inoculation_day_offset_equals_4": estimate_detects,
            "any_dimension_outside_p0_1_tolerance": dimension_detects,
            "relative_loss_degradation_at_least_0_25": relative_loss_detects,
        }
    else:
        if wrong_fit.numerical_tie:
            channel_error_detects: bool | None = None
            beta_outside: bool | None = None
            timing_outside: bool | None = None
            dimension_errors = {
                name: {
                    "signed_error": None,
                    "absolute_error": None,
                    "outside_tolerance": None,
                }
                for name in ("beta", "inoculation_day_offset")
            }
        else:
            if selected is None:
                raise CampaignError("unique P0-2B minimum has no selected estimate")
            if selected not in wrong_candidate_prediction_library:
                raise CampaignError("selected P0-2B candidate has no prediction library entry")
            predicted_totals = _mean_channel_totals(wrong_candidate_prediction_library[selected])
            target_totals = tuple(sum(channel) for channel in target_tables.channel_values)
            channel_error = max(
                abs(predicted - target) / max(1.0, target)
                for predicted, target in zip(predicted_totals, target_totals, strict=True)
            )
            channel_error_detects = channel_error >= 0.25
            beta_tolerance = config.dimension_map["beta"].exact_tolerance()
            timing_tolerance = config.dimension_map["inoculation_day_offset"].exact_tolerance()
            beta_spec = config.dimension_map["beta"]
            timing_spec = config.dimension_map["inoculation_day_offset"]
            beta_outside = (
                abs(beta_spec.exact_value(selected.beta) - beta_spec.exact_value(truth.beta))
                > beta_tolerance
            )
            timing_outside = (
                abs(
                    timing_spec.exact_value(selected.inoculation_day_offset)
                    - timing_spec.exact_value(truth.inoculation_day_offset)
                )
                > timing_tolerance
            )
            dimension_errors = {}
            for name, estimate, actual in (
                ("beta", selected.beta, truth.beta),
                (
                    "inoculation_day_offset",
                    selected.inoculation_day_offset,
                    truth.inoculation_day_offset,
                ),
            ):
                dimension_spec = config.dimension_map[name]
                signed = dimension_spec.exact_value(estimate) - dimension_spec.exact_value(actual)
                absolute = abs(signed)
                dimension_errors[name] = {
                    "signed_error": float(signed),
                    "absolute_error": float(absolute),
                    "outside_tolerance": absolute > config.dimension_map[name].exact_tolerance(),
                }
        clauses = {
            "relative_loss_degradation_at_least_0_25": relative_loss_detects,
            "channel_total_error_at_least_0_25": channel_error_detects,
            "beta_outside_p0_1_tolerance": beta_outside,
            "inoculation_day_offset_outside_p0_1_tolerance": timing_outside,
        }
    if relative_loss_detects or any(value is True for value in clauses.values()):
        state: Literal["TRUE", "FALSE", "UNKNOWN"] = "TRUE"
    elif any(value is None for value in clauses.values()):
        state = "UNKNOWN"
    else:
        state = "FALSE"
    return P02TargetResult(
        arm=arm,
        target_seed=target_seed,
        estimate_hash=wrong_fit.estimate_hash,
        minimum_objective=wrong_fit.minimum_objective,
        correct_minimum_objective=correct_minimum_objective,
        relative_loss_degradation=relative_loss,
        selected=selected,
        global_minimizers=wrong_fit.global_minimizers,
        numerical_tie=wrong_fit.numerical_tie,
        channel_total_error=channel_error,
        clauses=clauses,
        dimension_errors=dimension_errors,
        detection_state=state,
        phase0b=config.profile is PHASE0B_PROFILE,
    )


def aggregate_p02_detection(
    target_results: Sequence[P02TargetResult],
    *,
    arm: Literal["p0_2a", "p0_2b"],
    target_process_seeds: tuple[int, ...] = TARGET_PROCESS_SEEDS,
) -> tuple[Literal["PASS", "FAIL"] | None, str | None, int, int, tuple[int, int]]:
    """Aggregate fixed-five target states without converting UNKNOWN to either result."""

    expected = 5
    threshold = 3 if arm == "p0_2a" else 4
    if (
        len(target_results) != expected
        or tuple(row.target_seed for row in target_results) != target_process_seeds
        or {row.arm for row in target_results} != {arm}
        or any(row.detection_state not in {"TRUE", "FALSE", "UNKNOWN"} for row in target_results)
    ):
        raise CampaignError(f"{arm} aggregate requires its fixed five targets")
    detected = sum(row.detection_state == "TRUE" for row in target_results)
    unknown = sum(row.detection_state == "UNKNOWN" for row in target_results)
    attainable = (detected, detected + unknown)
    if detected >= threshold:
        return "PASS", None, detected, unknown, attainable
    if detected + unknown < threshold:
        return "FAIL", None, detected, unknown, attainable
    return None, "indeterminate_tied_minima", detected, unknown, attainable


def _validate_p01_cache_for_p02(result: P01CampaignResult) -> None:
    config = result.config
    workload = result.workload
    if not result.execution_evidence.matches(config, workload):
        raise CampaignError("P0-2 requires complete P0-1 execution evidence")
    expected_seeds = set(config.target_process_seeds)
    if (
        set(result.target_tables) != expected_seeds
        or set(result.blind_fits) != expected_seeds
        or set(result.target_truths) != expected_seeds
        or set(result.target_diagnostics) != expected_seeds
        or set(result.target_config_hashes) != expected_seeds
        or set(result.target_observation_hashes) != expected_seeds
        or set(result.target_namespace_fingerprints) != expected_seeds
    ):
        raise CampaignError(
            "P0-2 requires all five P0-1 target observations, hashes, fits and truths"
        )
    if any(
        len(digest) != 64
        for digest in (
            *result.target_config_hashes.values(),
            *result.target_observation_hashes.values(),
            *result.target_namespace_fingerprints.values(),
        )
    ):
        raise CampaignError("P0-2 requires complete hashes for reused P0-1 target inputs")
    if not all(item.namespace_passed for item in result.target_diagnostics.values()):
        raise CampaignError("P0-2 requires verified P0-1 target namespaces")
    if set(result.candidate_prediction_library) != set(config.candidate_grid):
        raise CampaignError("P0-2 requires the complete retained P0-1 candidate library")
    if set(result.candidate_config_hashes) != set(config.candidate_grid) or any(
        len(digest) != 64 for digest in result.candidate_config_hashes.values()
    ):
        raise CampaignError("P0-2 requires complete P0-1 candidate configuration hashes")
    expected_latents = {
        (seed, beta, int(offset))
        for seed in config.candidate_process_seeds
        for beta in config.dimension_map["beta"].candidates
        for offset in config.dimension_map["inoculation_day_offset"].candidates
    }
    if set(result.candidate_latents) != expected_latents:
        raise CampaignError("P0-2 requires the complete retained candidate latent cache")
    if any(
        len(predictions) != P01_FIT_REPLICATE_COUNT
        for predictions in result.candidate_prediction_library.values()
    ):
        raise CampaignError("P0-2 requires three retained P0-1 prediction replicates per cell")
    expected_dates = observation_dates(
        config.start_date, config.duration_days, config.observation_horizon_tail_days
    )
    if any(table.dates != expected_dates for table in result.target_tables.values()) or any(
        table.dates != expected_dates
        for predictions in result.candidate_prediction_library.values()
        for table in predictions
    ):
        raise CampaignError("P0-2 requires complete P0-1 observation calendars")
    if any(
        not isinstance(run_config, OutbreakRunConfig)
        or getattr(latent_result, "config", None) != run_config
        for latent_result, run_config in result.candidate_latents.values()
    ):
        raise CampaignError("P0-1 retained latent metadata is incomplete or mismatched")


def run_p02_campaign(
    p01_result: P01CampaignResult,
    work_dir: Path,
    *,
    root: Path,
) -> P02CampaignResult:
    """Generate both wrong-model libraries using retained P0-1 targets and latent runs."""

    config = p01_result.config
    validate_campaign_config(config, config.declaration["budget_caps"])
    guard_workload(config)
    _validate_p01_cache_for_p02(p01_result)
    if config.implemented_arms != ("p0_1", "p0_2a", "p0_2b", "p0_3"):
        raise CampaignError("P0-2 arm declaration is incomplete")
    arm_results: dict[str, P02ArmResult] = {}
    for arm in ("p0_2a", "p0_2b"):
        arm_started = time.perf_counter()
        grid = config.candidate_grid if arm == "p0_2a" else _p02b_grid(config)
        candidate_predictions: dict[CandidateCell, tuple[ObservedTables, ...]] = {}
        candidate_hashes: dict[CandidateCell, str] = {}
        candidate_namespace_passed = True
        measured_transforms = 0
        replicate_provenance: list[dict[str, Any]] = []
        for cell in grid:
            predictions: list[ObservedTables] = []
            actual_configs: list[tuple[Any, Any]] = []
            for process_seed, observation_seed in zip(
                config.candidate_process_seeds,
                config.candidate_observation_seeds,
                strict=True,
            ):
                latent_result, run_config = p01_result.candidate_latents[
                    (process_seed, cell.beta, cell.inoculation_day_offset)
                ]
                expected_arm_transforms = len(grid) * P01_FIT_REPLICATE_COUNT
                if measured_transforms >= expected_arm_transforms:
                    raise BudgetError(f"{arm} observation transform cap reached before dispatch")
                observation_config = _observation_config_for_cell(
                    root,
                    config,
                    observation_seed,
                    config.candidate_observation_config_id,
                    cell,
                    reporting_delay_days=0 if arm == "p0_2a" else None,
                )
                observation_result = observe_latent_run(latent_result, observation_config)
                measured_transforms += 1
                namespace_passed = _namespace_passes(
                    latent_result, observation_result, run_config, observation_config
                )
                if not namespace_passed:
                    raise CampaignError(f"{arm} observation namespace evidence is incomplete")
                candidate_namespace_passed = candidate_namespace_passed and namespace_passed
                observation_rng = observation_result.diagnostics["observation_rng"]
                table = _observed_tables_from_result(observation_result)
                validate_observation_calendar(
                    table,
                    start_date=config.start_date,
                    duration_days=config.duration_days,
                    tail_days=config.observation_horizon_tail_days,
                )
                predictions.append(table)
                actual_configs.append((run_config, observation_config))
                replicate_provenance.append(
                    {
                        "arm": arm,
                        "candidate": cell.as_dict(),
                        "process_seed": process_seed,
                        "observation_seed": observation_seed,
                        "latent_result_hash": getattr(latent_result, "logical_content_hash", None),
                        "observation_config_id": observation_config.observation_config_id,
                        "observation_stream_namespace": observation_rng["stream_namespace"],
                        "observation_stream_key_inputs": list(observation_rng["stream_key_inputs"]),
                        "observation_rng_fingerprint": observation_rng["stream_fingerprint"],
                        "latent_config_sha256": hashlib.sha256(
                            json.dumps(
                                _model_payload(run_config), sort_keys=True, separators=(",", ":")
                            ).encode("utf-8")
                        ).hexdigest(),
                        "observation_config_sha256": hashlib.sha256(
                            json.dumps(
                                _model_payload(observation_config),
                                sort_keys=True,
                                separators=(",", ":"),
                            ).encode("utf-8")
                        ).hexdigest(),
                        "namespace_verified": namespace_passed,
                        "observed_table_sha256": hashlib.sha256(
                            json.dumps(
                                table.as_dict(), sort_keys=True, separators=(",", ":")
                            ).encode("utf-8")
                        ).hexdigest(),
                    }
                )
            if len(predictions) != P01_FIT_REPLICATE_COUNT:
                raise CampaignError(f"{arm} candidate did not produce three fitting replicates")
            candidate_predictions[cell] = tuple(predictions)
            candidate_hashes[cell] = candidate_config_hash(
                cell, config, replicate_configs=actual_configs
            )
        if not candidate_namespace_passed:
            raise CampaignError(f"{arm} observation namespace evidence is incomplete")
        if len(candidate_predictions) != len(grid) or set(candidate_hashes) != set(grid):
            raise CampaignError(f"{arm} candidate grid generation is incomplete")
        expected_transforms = len(grid) * P01_FIT_REPLICATE_COUNT
        if measured_transforms != expected_transforms or any(
            len(digest) != 64 for digest in candidate_hashes.values()
        ):
            raise CampaignError(f"{arm} observation or config-hash evidence is incomplete")
        for provenance in replicate_provenance:
            candidate = CandidateCell(**provenance["candidate"])
            provenance["cell_config_sha256"] = candidate_hashes[candidate]

        surfaces: dict[int, tuple[LossRow, ...]] = {}
        target_results: list[P02TargetResult] = []
        for target_seed in config.target_process_seeds:
            if arm == "p0_2a":
                fit_kwargs: dict[str, Any] = {"candidate_config_hashes": candidate_hashes}
                if config.profile is PHASE0B_PROFILE:
                    fit_kwargs["expected_grid"] = config.candidate_grid
                fit = fit_blind(
                    p01_result.target_tables[target_seed],
                    grid,
                    candidate_predictions,
                    **fit_kwargs,
                )
            else:
                fit = fit_p02_blind(
                    p01_result.target_tables[target_seed],
                    grid,
                    candidate_predictions,
                    candidate_config_hashes=candidate_hashes,
                    arm="p0_2b",
                    config=config,
                )
            if len(fit.loss_surface) != len(grid):
                raise CampaignError(f"{arm} fitter returned an incomplete loss surface")
            surfaces[target_seed] = fit.loss_surface
            estimate_path = work_dir / arm / "blind_estimates" / f"{target_seed}.json"
            persisted_hash = persist_blind_estimate(estimate_path, fit)
            if persisted_hash != fit.estimate_hash:
                raise CampaignError(f"{arm} persisted estimate hash is mismatched")
            # Truth and the correct P0-1 objective cross the blind boundary only
            # after this arm's selected estimate or explicit tie record is durable.
            target_results.append(
                evaluate_p02_target(
                    arm,
                    target_seed=target_seed,
                    correct_minimum_objective=p01_result.blind_fits[target_seed].minimum_objective,
                    wrong_fit=fit,
                    target_tables=p01_result.target_tables[target_seed],
                    wrong_candidate_prediction_library=candidate_predictions,
                    truth=p01_result.target_truths[target_seed],
                    config=config,
                )
            )
        if set(surfaces) != set(config.target_process_seeds):
            raise CampaignError(f"{arm} is missing target loss surfaces")
        detection, reason, detected, unknown, attainable = aggregate_p02_detection(
            target_results, arm=arm, target_process_seeds=config.target_process_seeds
        )
        arm_results[arm] = P02ArmResult(
            arm=arm,
            software_status="PASS",
            misspecification_detection=detection,
            detection_reason=reason,
            threshold=3 if arm == "p0_2a" else 4,
            detected=detected,
            unknown=unknown,
            attainable_detection_count=attainable,
            target_results=tuple(target_results),
            candidate_prediction_library=candidate_predictions,
            candidate_config_hashes=candidate_hashes,
            loss_surfaces=surfaces,
            replicate_provenance=tuple(replicate_provenance),
            measured_latent_calls=0,
            measured_observation_transforms=measured_transforms,
            wall_time_seconds=time.perf_counter() - arm_started,
        )
    both_software_pass = all(arm.software_status == "PASS" for arm in arm_results.values())
    if not both_software_pass:
        overall_detection: Literal["PASS", "FAIL"] | None = None
        overall_reason = "software_incomplete"
    elif all(arm.misspecification_detection == "PASS" for arm in arm_results.values()):
        overall_detection = "PASS"
        overall_reason = None
    elif any(arm.misspecification_detection == "FAIL" for arm in arm_results.values()):
        overall_detection = "FAIL"
        overall_reason = "one_or_more_arms_failed_detection"
    else:
        overall_detection = None
        overall_reason = "indeterminate_tied_minima"
    return P02CampaignResult(
        arms=arm_results,
        software_status="PASS" if both_software_pass else "FAIL",
        misspecification_detection=overall_detection,
        overall_detection_reason=overall_reason,
        reused_p01_target_provenance={
            seed: {
                "process_seed": seed,
                "observation_seed": config.target_observation_seeds[index],
                "observation_config_id": config.target_observation_config_id,
                "target_config_sha256": p01_result.target_config_hashes[seed],
                "target_observation_table_sha256": p01_result.target_observation_hashes[seed],
                "observation_rng_fingerprint": p01_result.target_namespace_fingerprints[seed],
                "namespace_verified": p01_result.target_diagnostics[seed].namespace_passed,
            }
            for index, seed in enumerate(config.target_process_seeds)
        },
    )


def _p03_grid(config: CampaignConfig | None = None) -> tuple[P03Cell, ...]:
    beta_grid, route_factor_grid = _p03_grids(config)
    return tuple(P03Cell(beta, factor) for beta in beta_grid for factor in route_factor_grid)


def _p03_ridge_cells(
    beta_grid: Sequence[float], route_factor_grid: Sequence[float]
) -> tuple[P03Cell, P03Cell, P03Cell]:
    return (
        P03Cell(beta_grid[-1], route_factor_grid[0]),
        P03Cell(beta_grid[len(beta_grid) // 2], route_factor_grid[len(route_factor_grid) // 2]),
        P03Cell(beta_grid[0], route_factor_grid[-1]),
    )


def _p03_cell_key(cell: P03Cell) -> str:
    return json.dumps(cell.as_dict(), sort_keys=True, separators=(",", ":"))


def _prediction_vector(predictions: Sequence[ObservedTables]) -> tuple[float, ...]:
    """Flatten actual replicate × channel × date vectors in declared order."""

    return tuple(
        value for table in predictions for channel in table.channel_values for value in channel
    )


def _prediction_vector_hash(vector: Sequence[float]) -> str:
    payload = json.dumps(list(vector), separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def classify_p03_structural_equivalence(
    *,
    ridge_prediction_vectors: Mapping[str, Sequence[float]],
    ridge_objectives: Mapping[int, Mapping[str, float]],
    target_profiles: Mapping[int, Mapping[str, Any]],
    factor_estimate: Any = None,
    emitted_precision_fields: Iterable[str] = (),
    expected_target_seeds: tuple[int, ...] = TARGET_PROCESS_SEEDS,
    beta_grid: Sequence[float] = P03_BETA_GRID,
    route_factor_grid: Sequence[float] = P03_ROUTE_FACTOR_GRID,
) -> tuple[str, dict[str, bool], dict[str, str]]:
    """Apply the six frozen P0-3 classifier predicates to actual evidence."""

    ridge_cells = tuple(
        _p03_cell_key(cell) for cell in _p03_ridge_cells(beta_grid, route_factor_grid)
    )
    vectors_present = all(key in ridge_prediction_vectors for key in ridge_cells)
    vectors = [
        tuple(ridge_prediction_vectors[key])
        for key in ridge_cells
        if key in ridge_prediction_vectors
    ]
    vectors_agree = (
        vectors_present
        and bool(vectors)
        and all(
            len(vector) == len(vectors[0])
            and all(
                abs(left - right) <= P03_VECTOR_TOLERANCE
                for left, right in zip(vectors[0], vector, strict=True)
            )
            for vector in vectors[1:]
        )
    )

    expected_targets = set(expected_target_seeds)
    reference_factor = route_factor_grid[len(route_factor_grid) // 2]
    objective_passed = set(ridge_objectives) == expected_targets and all(
        all(key in values for key in ridge_cells)
        and (max(values[key] for key in ridge_cells) - min(values[key] for key in ridge_cells))
        <= P03_OBJECTIVE_SPREAD_SCALE * max(1.0, min(values[key] for key in ridge_cells))
        for values in ridge_objectives.values()
    )

    expected_factors = set(route_factor_grid)
    forbidden_precision_fields = {"standard_error", "interval", "coverage"}

    def contains_false_precision(value: Any) -> bool:
        if isinstance(value, Mapping):
            return any(
                str(key) in forbidden_precision_fields or contains_false_precision(item)
                for key, item in value.items()
            )
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return any(contains_false_precision(item) for item in value)
        return False

    profiles_reported = set(target_profiles) == expected_targets
    for profile in target_profiles.values():
        try:
            argmin_by_factor = {
                float(key): float(value) for key, value in profile["argmin_by_factor"].items()
            }
            shifts = {
                float(key): float(value) for key, value in profile["argmin_shift_by_factor"].items()
            }
            reference = float(profile["argmin_shift_reference_beta"])
            profiled_rows = profile["profiled_minima"]
            profiled_betas = {float(row["transmission_beta"]) for row in profiled_rows}
            profiled_complete = len(profiled_rows) == len(beta_grid) and profiled_betas == set(
                beta_grid
            )
            profiled_complete = profiled_complete and all(
                set(float(item["nuisance_factor"]) for item in row["nuisance_profile"])
                == expected_factors
                and math.isfinite(float(row["profiled_objective"]))
                for row in profiled_rows
            )
            profile_valid = (
                set(argmin_by_factor) == expected_factors
                and set(shifts) == expected_factors
                and all(value in beta_grid for value in argmin_by_factor.values())
                and profiled_complete
                and reference == argmin_by_factor[reference_factor]
                and all(
                    abs(shifts[factor] - (argmin_by_factor[factor] - reference))
                    <= P03_VECTOR_TOLERANCE
                    for factor in expected_factors
                )
            )
        except (KeyError, TypeError, ValueError, IndexError):
            profile_valid = False
        profiles_reported = profiles_reported and profile_valid

    actual_hashes = {
        key: _prediction_vector_hash(ridge_prediction_vectors[key])
        for key in ridge_cells
        if key in ridge_prediction_vectors
    }
    hash_passed = (
        vectors_present
        and set(actual_hashes) == set(ridge_cells)
        and len({actual_hashes[key] for key in ridge_cells}) == 1
    )
    no_false_precision = (
        factor_estimate is None
        and not (forbidden_precision_fields & set(emitted_precision_fields))
        and not contains_false_precision(target_profiles)
    )
    core_predicates = {
        "equal_product_vectors_agree_within_1e_12": bool(vectors_agree),
        "ridge_objective_spread_within_threshold": bool(objective_passed),
        "per_factor_argmins_shifts_and_profiled_minima_reported": bool(profiles_reported),
        "factor_estimate_null_without_precision_fields": bool(no_false_precision),
        "target_independent_prediction_hashes_identical": bool(hash_passed),
    }
    classification = (
        "NON_IDENTIFIED_STRUCTURAL" if all(core_predicates.values()) else "NOT_CLASSIFIED"
    )
    predicates = {
        **core_predicates,
        "classification_is_non_identified_structural": classification
        == "NON_IDENTIFIED_STRUCTURAL",
    }
    return classification, predicates, actual_hashes


def _p03_run_config_for_cell(
    config: CampaignConfig,
    parameters: RespiratoryParameterSet,
    process_seed: int,
    cell: P03Cell,
) -> OutbreakRunConfig:
    truth = _truth_cell(config)
    base = _run_config_for_cell(
        config,
        parameters,
        process_seed,
        CandidateCell(
            cell.beta,
            truth.inoculation_day_offset,
            truth.symptomatic_detection_probability,
            truth.asymptomatic_detection_probability,
        ),
    )
    run_config = base.model_copy(
        update={"route_multipliers": {route: cell.global_route_factor for route in P01_ROUTE_IDS}}
    )
    if (
        run_config.beta != cell.beta
        or run_config.seed != process_seed
        or tuple(run_config.route_multipliers) != P01_ROUTE_IDS
        or any(value != cell.global_route_factor for value in run_config.route_multipliers.values())
    ):
        raise CampaignError("P0-3 run config failed the uniform route-factor contract")
    return run_config


def _p03_config_hash(
    cell: P03Cell,
    replicate_configs: Sequence[tuple[Any, Any]],
    *,
    campaign_id: str | None = None,
) -> str:
    payload = {
        "campaign": (
            "v13-phase0-p0-3-negative-control"
            if campaign_id is None
            else f"{campaign_id}-p0-3-negative-control"
        ),
        "cell": cell.as_dict(),
        "replicate_configs": [
            {
                "process_seed": run_config.seed,
                "observation_seed": observation_config.observation_seed,
                "run_config": _model_payload(run_config),
                "observation_config": _model_payload(observation_config),
            }
            for run_config, observation_config in replicate_configs
        ],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def run_p03_campaign(
    p01_result: P01CampaignResult,
    work_dir: Path,
    *,
    root: Path,
) -> P03CampaignResult:
    """Run the nine-cell control using only P0-1's targets and generated parents."""

    config = p01_result.config
    guard_workload(config)
    if config.implemented_arms != ("p0_1", "p0_2a", "p0_2b", "p0_3"):
        raise CampaignError("P0-3 arm declaration is incomplete")
    expected_seeds = set(config.candidate_process_seeds)
    if set(p01_result.generated_parents) != set(
        (*config.target_process_seeds, *config.candidate_process_seeds)
    ):
        raise CampaignError("P0-3 requires the existing P0-1 population/network builds")
    if set(p01_result.target_tables) != set(config.target_process_seeds):
        raise CampaignError("P0-3 requires the complete P0-1 target observation set")
    project_root = root.resolve()
    parameters = load_parameter_set(project_root)
    beta_grid, route_factor_grid = _p03_grids(config)
    grid = _p03_grid(config)
    latent_cache: dict[tuple[P03Cell, int], tuple[Any, OutbreakRunConfig]] = {}
    measured_latent_calls = 0
    measured_observation_transforms = 0
    latent_cap = 27
    transform_cap = P03_OBSERVATION_TRANSFORMS
    try:
        for cell in grid:
            for process_seed in config.candidate_process_seeds:
                if process_seed not in expected_seeds:
                    raise CampaignError("P0-3 process seed is outside the declared candidate pair")
                if measured_latent_calls >= latent_cap:
                    raise BudgetError("P0-3 latent call cap reached before dispatch")
                run_config = _p03_run_config_for_cell(config, parameters, process_seed, cell)
                latent = run_outbreak(
                    p01_result.generated_parents[process_seed], run_config, parameters
                )
                if getattr(latent, "config", None) != run_config:
                    raise CampaignError(
                        "P0-3 latent result omitted or changed returned config metadata"
                    )
                measured_latent_calls += 1
                latent_cache[(cell, process_seed)] = (latent, run_config)

        predictions: dict[P03Cell, tuple[ObservedTables, ...]] = {}
        config_hashes: dict[P03Cell, str] = {}
        provenance: list[dict[str, Any]] = []
        for cell in grid:
            cell_predictions: list[ObservedTables] = []
            actual_configs: list[tuple[Any, Any]] = []
            for process_seed, observation_seed in zip(
                config.candidate_process_seeds, config.candidate_observation_seeds, strict=True
            ):
                latent, run_config = latent_cache[(cell, process_seed)]
                truth = _truth_cell(config)
                observation_cell = CandidateCell(
                    cell.beta,
                    truth.inoculation_day_offset,
                    truth.symptomatic_detection_probability,
                    truth.asymptomatic_detection_probability,
                )
                observation_config = _observation_config_for_cell(
                    project_root,
                    config,
                    observation_seed,
                    config.candidate_observation_config_id,
                    observation_cell,
                )
                if measured_observation_transforms >= transform_cap:
                    raise BudgetError("P0-3 observation transform cap reached before dispatch")
                observed = observe_latent_run(latent, observation_config)
                measured_observation_transforms += 1
                if not _namespace_passes(latent, observed, run_config, observation_config):
                    raise CampaignError("P0-3 observation namespace evidence is incomplete")
                table = _observed_tables_from_result(observed)
                validate_observation_calendar(
                    table,
                    start_date=config.start_date,
                    duration_days=config.duration_days,
                    tail_days=config.observation_horizon_tail_days,
                )
                cell_predictions.append(table)
                actual_configs.append((run_config, observation_config))
                rng = observed.diagnostics["observation_rng"]
                provenance.append(
                    {
                        "candidate": cell.as_dict(),
                        "process_seed": process_seed,
                        "observation_seed": observation_seed,
                        "latent_result_hash": getattr(latent, "logical_content_hash", None),
                        "observation_config_id": observation_config.observation_config_id,
                        "observation_rng_fingerprint": rng["stream_fingerprint"],
                        "namespace_verified": True,
                        "observed_table_sha256": hashlib.sha256(
                            json.dumps(
                                table.as_dict(), sort_keys=True, separators=(",", ":")
                            ).encode()
                        ).hexdigest(),
                    }
                )
            if len(cell_predictions) != P01_FIT_REPLICATE_COUNT:
                raise CampaignError("P0-3 candidate cell did not produce exactly three replicates")
            predictions[cell] = tuple(cell_predictions)
            config_hashes[cell] = _p03_config_hash(
                cell,
                actual_configs,
                campaign_id=(config.campaign_id if config.profile is PHASE0B_PROFILE else None),
            )

        if measured_latent_calls != latent_cap or measured_observation_transforms != transform_cap:
            raise CampaignError("P0-3 measured work did not match its exact declared counts")
        if set(predictions) != set(grid) or set(config_hashes) != set(grid):
            raise CampaignError("P0-3 generated an incomplete nine-cell surface")

        loss_surfaces: dict[int, tuple[dict[str, Any], ...]] = {}
        profiles: dict[int, Mapping[str, Any]] = {}
        ridge_objectives: dict[int, Mapping[str, float]] = {}
        for target_seed in config.target_process_seeds:
            target = p01_result.target_tables[target_seed]
            objectives = {cell: minimum_distance_loss(target, predictions[cell]) for cell in grid}
            rows = tuple(
                {
                    **cell.as_dict(),
                    "objective": objectives[cell],
                    "config_hash": config_hashes[cell],
                }
                for cell in grid
            )
            loss_surfaces[target_seed] = rows
            objective_grid = {
                beta: {factor: objectives[P03Cell(beta, factor)] for factor in route_factor_grid}
                for beta in beta_grid
            }
            profile = _profile_beta_nuisance(objective_grid)
            reference_beta = profile["argmin_by_factor"][
                route_factor_grid[len(route_factor_grid) // 2]
            ]
            _record_argmin_shifts(profile, reference_beta)
            profiles[target_seed] = {
                "argmin_by_factor": profile["argmin_by_factor"],
                "argmin_shift_reference_beta": profile["argmin_shift_reference_beta"],
                "argmin_shift_by_factor": profile["argmin_shift_by_factor"],
                "max_abs_argmin_shift": profile["max_abs_argmin_shift"],
                "profiled_minima": profile["rows"],
                "global_argmin": profile["argmin"],
            }
            ridge_objectives[target_seed] = {
                _p03_cell_key(cell): objectives[cell]
                for cell in _p03_ridge_cells(beta_grid, route_factor_grid)
            }

        ridge_cells = _p03_ridge_cells(beta_grid, route_factor_grid)
        ridge_vectors = {
            _p03_cell_key(cell): _prediction_vector(predictions[cell]) for cell in ridge_cells
        }
        prediction_vectors = {
            _p03_cell_key(cell): _prediction_vector(predictions[cell]) for cell in grid
        }
        classification, predicates, prediction_hashes = classify_p03_structural_equivalence(
            ridge_prediction_vectors=ridge_vectors,
            ridge_objectives=ridge_objectives,
            target_profiles=profiles,
            factor_estimate=None,
            expected_target_seeds=config.target_process_seeds,
            beta_grid=beta_grid,
            route_factor_grid=route_factor_grid,
        )
        scientific_status: Literal["PASS", "FAIL"] = "PASS" if all(predicates.values()) else "FAIL"
        return P03CampaignResult(
            software_status="PASS",
            scientific_status=scientific_status,
            classification=classification,
            factor_estimate=None,
            predicates=predicates,
            target_profiles=profiles,
            loss_surfaces=loss_surfaces,
            prediction_hashes=prediction_hashes,
            prediction_vectors=prediction_vectors,
            ridge_prediction_vectors=ridge_vectors,
            candidate_prediction_library=predictions,
            ridge_objectives=ridge_objectives,
            candidate_config_hashes=config_hashes,
            replicate_provenance=tuple(provenance),
            measured_latent_calls=measured_latent_calls,
            measured_observation_transforms=measured_observation_transforms,
        )
    except (CampaignError, BudgetError):
        raise
    except Exception as exc:
        raise CampaignError(f"P0-3 generation failed: {type(exc).__name__}: {exc}") from exc


def _namespace_passes(
    latent_result: Any,
    observation_result: Any,
    run_config: Any,
    observation_config: Any,
) -> bool:
    """Derive namespace evidence from actual result/config metadata."""

    try:
        latent_config = latent_result.config
        observed_config = observation_result.config
        observed_latent = observation_result.latent_run
        if not isinstance(latent_config, OutbreakRunConfig) or not isinstance(
            run_config, OutbreakRunConfig
        ):
            return False
        if not isinstance(observed_config, ObservationConfig) or not isinstance(
            observation_config, ObservationConfig
        ):
            return False
        if observed_latent is not latent_result:
            return False
        if latent_config != run_config or observed_config != observation_config:
            return False

        diagnostics = observation_result.diagnostics
        if not isinstance(diagnostics, Mapping):
            return False
        rng = diagnostics.get("observation_rng")
        if not isinstance(rng, Mapping):
            return False
        expected_key_inputs = (
            "latent_replicate_seed",
            "observation_seed",
            "observation_config_id",
        )
        if rng.get("stream_namespace") != "observation":
            return False
        if tuple(rng.get("stream_key_inputs", ())) != expected_key_inputs:
            return False
        expected_fingerprint = hashlib.sha256(
            str(observation_stream_seed(run_config.seed, observation_config)).encode("utf-8")
        ).hexdigest()
        return rng.get("stream_fingerprint") == expected_fingerprint
    except (AttributeError, TypeError, ValueError, KeyError):
        return False


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_predeclaration(path: Path, expected_sha256: str = PREDECLARATION_SHA256) -> str:
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise CampaignError(
            f"predeclaration SHA-256 mismatch: expected {expected_sha256}, got {actual}"
        )
    return actual


def validate_g29_ruling(path: Path, config: CampaignConfig) -> str:
    """Verify the supplied owner ruling against its accepted frozen digest."""

    if config.g29_ruling_path != G29_RULING_PATH:
        raise CampaignError("G29 ruling path does not match the accepted ruling")
    if config.g29_ruling_sha256 != G29_RULING_SHA256:
        raise CampaignError("G29 ruling SHA-256 does not match the accepted ruling")
    try:
        actual = sha256_file(path)
    except OSError as exc:
        raise CampaignError(f"cannot read G29 ruling {path}: {exc}") from exc
    if actual != G29_RULING_SHA256:
        raise CampaignError(
            f"G29 ruling SHA-256 mismatch: expected {G29_RULING_SHA256}, got {actual}"
        )
    return actual


def validate_owner_ruling(path: Path, config: CampaignConfig) -> str:
    """Verify the Phase-0b model-owner ruling against its independent constant."""

    profile = config.profile
    if profile.owner_ruling_path is None or profile.owner_ruling_sha256 is None:
        raise CampaignError("this frozen profile has no separate model-owner ruling")
    if config.owner_ruling_path != profile.owner_ruling_path:
        raise CampaignError("model-owner ruling path does not match the frozen profile")
    if config.owner_ruling_sha256 != profile.owner_ruling_sha256:
        raise CampaignError("model-owner ruling SHA-256 does not match the frozen profile")
    actual = sha256_file(path)
    if actual != profile.owner_ruling_sha256:
        raise CampaignError(
            "model-owner ruling SHA-256 mismatch: expected "
            f"{profile.owner_ruling_sha256}, got {actual}"
        )
    return actual


def _populate_research_bundle(
    output_dir: Path,
    *,
    campaign_config_path: Path,
    predeclaration_path: Path,
    ruling_path: Path | None = None,
    owner_ruling_path: Path | None = None,
    seed_ledger: Sequence[Mapping[str, Any]],
    candidate_loss_surfaces: Mapping[str, Any],
    p01_recovery_rows: Sequence[Mapping[str, Any]] | None = None,
    p02_misspecification_rows: Sequence[Mapping[str, Any]] | None = None,
    p03_profile: Mapping[str, Any] | None = None,
    campaign_summary: Mapping[str, Any] | None = None,
    input_hashes: Mapping[str, str] | None = None,
    p02_complete_loss_surfaces: Mapping[str, Any] | None = None,
    p02_provenance: Mapping[str, Any] | None = None,
    retained_evidence_files: Mapping[str, bytes] | None = None,
    retained_evidence_index: Sequence[Mapping[str, Any]] = (),
    execution_complete: bool = False,
    mocked: bool = False,
    execution_started_at: float | None = None,
) -> Path:
    """Populate one private staging directory with bundle files."""

    if output_dir.exists():
        if not output_dir.is_dir():
            raise CampaignError(f"research bundle destination is not a directory: {output_dir}")
        if any(output_dir.iterdir()):
            raise CampaignError("research bundle destination must be empty before writing")
    config_bytes = campaign_config_path.read_bytes()
    config = CampaignConfig.from_yaml(campaign_config_path)
    profile = config.profile
    predeclaration_hash = validate_predeclaration(
        predeclaration_path, profile.predeclaration_sha256
    )
    if ruling_path is None:
        raise CampaignError("research bundle requires a verified G29 ruling")
    ruling_hash = validate_g29_ruling(ruling_path, config)
    owner_hash: str | None = None
    if profile.owner_ruling_path is not None:
        if owner_ruling_path is None:
            raise CampaignError("Phase-0b bundle requires its verified model-owner ruling")
        owner_hash = validate_owner_ruling(owner_ruling_path, config)
    elif owner_ruling_path is not None:
        raise CampaignError("Phase-0 bundle cannot include a Phase-0b model-owner ruling")
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    (output_dir / "campaign_config.yaml").write_bytes(config_bytes)
    (output_dir / "campaign_config.sha256").write_text(
        f"{hashlib.sha256(config_bytes).hexdigest()}  campaign_config.yaml\n", encoding="utf-8"
    )
    predeclaration_filename = (
        "predeclaration.md" if profile is PHASE0B_PROFILE else "predeclaration"
    )
    (output_dir / "predeclaration.sha256").write_text(
        f"{predeclaration_hash}  {predeclaration_filename}\n", encoding="utf-8"
    )
    shutil.copyfile(ruling_path, output_dir / "g29_ruling.md")
    (output_dir / "g29_ruling.sha256").write_text(
        f"{ruling_hash}  g29_ruling.md\n", encoding="utf-8"
    )
    if profile.owner_ruling_path is not None:
        shutil.copyfile(predeclaration_path, output_dir / "predeclaration.md")
        assert owner_ruling_path is not None and owner_hash is not None
        shutil.copyfile(owner_ruling_path, output_dir / "phase0b_owner_ruling.md")
        (output_dir / "phase0b_owner_ruling.sha256").write_text(
            f"{owner_hash}  phase0b_owner_ruling.md\n", encoding="utf-8"
        )
    (output_dir / "input_hashes.json").write_text(
        json.dumps(dict(input_hashes or {}), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "seed_ledger.json").write_text(
        json.dumps(list(seed_ledger), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "candidate_loss_surfaces.json").write_text(
        json.dumps(candidate_loss_surfaces, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "p0_2_loss_surfaces.json").write_text(
        json.dumps(p02_complete_loss_surfaces or {}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "p0_2_provenance.json").write_text(
        json.dumps(p02_provenance or {}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    p01_rows = list(p01_recovery_rows or [{"status": "UNEXECUTED"}])
    fields = sorted({key for row in p01_rows for key in row}) or ["status"]
    with (output_dir / "p0_1_recovery.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(p01_rows)
    rows = list(p02_misspecification_rows or [])
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with (output_dir / "p0_2_misspecification.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(
            {
                key: (
                    (
                        "UNKNOWN"
                        if value is None
                        else "TRUE"
                        if value is True
                        else "FALSE"
                        if value is False
                        else value
                    )
                    if profile is PHASE0B_PROFILE and key.startswith("clause_")
                    else "null"
                    if value is None
                    else json.dumps(value, sort_keys=True)
                    if isinstance(value, (dict, list))
                    else value
                )
                for key, value in row.items()
            }
            for row in rows
        )
    (output_dir / "p0_3_profile.json").write_text(
        json.dumps(
            p03_profile or {"software_status": "UNEXECUTED", "factor_estimate": None},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    campaign_status_key = (
        "overall_phase0b_status"
        if profile.owner_ruling_path is not None
        else "overall_phase0_status"
    )
    summary = {
        **dict(campaign_summary or {}),
        "status": (
            "UNEXECUTED"
            if not execution_complete
            else "NOT_EVALUATED"
            if mocked
            else str((campaign_summary or {}).get(campaign_status_key, "NOT_ESTABLISHED"))
        ),
        campaign_status_key: (
            "UNEXECUTED"
            if not execution_complete
            else "NOT_EVALUATED"
            if mocked
            else str((campaign_summary or {}).get(campaign_status_key, "NOT_ESTABLISHED"))
        ),
        "mocked_execution": bool(mocked),
        "real_jersey_data_used": False,
        "nominal_coverage_claim": None,
        "calibration_claim": None,
        "input_hashes": dict(input_hashes or {}),
        "campaign_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "predeclaration_sha256": predeclaration_hash,
        "g29_ruling_path": config.g29_ruling_path,
        "g29_ruling_sha256": ruling_hash,
        "g29_ruling_verified": True,
    }
    if profile.owner_ruling_path is not None:
        summary.update(
            {
                "owner_ruling_path": profile.owner_ruling_path,
                "owner_ruling_sha256": owner_hash,
                "owner_ruling_verified": True,
                "lineage": dict(PHASE0_LINEAGE),
            }
        )
    if not execution_complete or mocked:
        raw_arms = summary.get("arms", {})
        if isinstance(raw_arms, Mapping):
            summary["arms"] = {
                name: {
                    **dict(arm_summary),
                    "software_status": "MOCKED" if mocked else "NOT_EXECUTED",
                    "scientific_status": "NOT_EVALUATED",
                }
                for name, arm_summary in raw_arms.items()
            }
    (output_dir / "campaign_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for relative_name, content in sorted((retained_evidence_files or {}).items()):
        relative_path = PurePosixPath(relative_name)
        if (
            relative_path.is_absolute()
            or not relative_path.parts
            or any(part in {"", ".", ".."} for part in relative_path.parts)
            or relative_name in {"SHA256SUMS", "bundle_index.json"}
        ):
            raise CampaignError(f"invalid retained bundle path: {relative_name}")
        destination = output_dir.joinpath(*relative_path.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    output_descriptions = {
        "campaign_config.yaml": (
            "Frozen campaign controls and declared grids; verifies run settings."
        ),
        "campaign_config.sha256": "Digest for the retained frozen campaign configuration.",
        "predeclaration.sha256": "Digest of the frozen predeclaration used by the run.",
        "g29_ruling.md": "Accepted ruling bytes required for execution authorization.",
        "g29_ruling.sha256": "Digest for the retained accepted ruling.",
        "input_hashes.json": (
            "Source and configuration digests used to identify the implementation inputs."
        ),
        "seed_ledger.json": "Declared target and candidate process/observation seed assignments.",
        "candidate_loss_surfaces.json": (
            f"P0-1 per-target {profile.p01_cells}-cell objective surfaces; recompute from "
            "P0-1 target and candidate observed tables."
        ),
        "p0_1_candidate_provenance.json": (
            "P0-1 per-cell/per-replicate table hashes and config hashes."
        ),
        "p0_1_recovery.csv": "P0-1 descriptive recovery summaries and dimension-level estimates.",
        "p0_1_truth_diagnostics.json": (
            "Raw inputs for P0-1 viability, chronology, conservation, and namespace predicates."
        ),
        "p0_2_loss_surfaces.json": (
            "P0-2A and P0-2B per-target objective surfaces; recompute from retained target "
            "and arm candidate tables."
        ),
        "p0_2_provenance.json": (
            "Blind estimate hashes, candidate table provenance, selected estimates, R_i, "
            "E_i, and detection clauses."
        ),
        "p0_2_misspecification.csv": "Per-target P0-2 R_i/E_i and detection results.",
        "p0_3_profile.json": (
            "P0-3 full surfaces, per-cell prediction vectors, ridge hashes, profiles, "
            "and predicates."
        ),
        "campaign_summary.json": "Published P0-1, P0-2, P0-3, and workload predicate values.",
        "bundle_index.json": (
            "This index maps bundle outputs and retained evidence files to recomputation tasks."
        ),
        "blind_estimate_manifest.json": (
            "Estimate hashes, exact-file digests, and persist-before-truth-join event ordering."
        ),
        "SHA256SUMS": (
            "File-level digests for every other file in this bundle, including nested evidence."
        ),
    }
    if profile.owner_ruling_path is not None:
        output_descriptions.update(
            {
                "predeclaration.md": "Exact frozen Phase-0b predeclaration bytes.",
                "phase0b_owner_ruling.md": "Exact accepted Phase-0b model-owner ruling bytes.",
                "phase0b_owner_ruling.sha256": "Digest for the retained model-owner ruling.",
            }
        )
    bundle_index = {
        "schema_version": 1,
        "purpose": (
            "Map published Phase-0 results to the retained evidence needed for cold recomputation."
            if profile is PHASE0_PROFILE
            else "Map published Phase-0b results to retained evidence for cold recomputation."
        ),
        "outputs": output_descriptions,
        "retained_evidence_file_count": len(retained_evidence_index),
        "retained_evidence_files": [dict(item) for item in retained_evidence_index],
        "sha256sums_scope": (
            "Every file except SHA256SUMS itself; paths are bundle-relative POSIX paths."
        ),
    }
    (output_dir / "bundle_index.json").write_bytes(_compact_json_bytes(bundle_index))
    if profile.owner_ruling_path is not None and execution_started_at is not None:
        summary_path = output_dir / "campaign_summary.json"
        summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
        summary_payload["disclosures"]["total_wall_time_seconds"] = (
            time.perf_counter() - execution_started_at
        )
        summary_path.write_text(
            json.dumps(summary_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    files = sorted(
        (path for path in output_dir.rglob("*") if path.is_file() and path.name != "SHA256SUMS"),
        key=lambda path: path.relative_to(output_dir).as_posix(),
    )
    sums = "".join(
        f"{sha256_file(path)}  {path.relative_to(output_dir).as_posix()}\n" for path in files
    )
    (output_dir / "SHA256SUMS").write_text(sums, encoding="utf-8")
    if profile.owner_ruling_path is not None:
        summary_path = output_dir / "campaign_summary.json"
        for _ in range(8):
            bundle_byte_size = sum(
                path.stat().st_size for path in output_dir.rglob("*") if path.is_file()
            )
            summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
            summary_payload["disclosures"]["bundle_byte_size"] = bundle_byte_size
            summary_path.write_text(
                json.dumps(summary_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            files = sorted(
                (
                    path
                    for path in output_dir.rglob("*")
                    if path.is_file() and path.name != "SHA256SUMS"
                ),
                key=lambda path: path.relative_to(output_dir).as_posix(),
            )
            sums = "".join(
                f"{sha256_file(path)}  {path.relative_to(output_dir).as_posix()}\n"
                for path in files
            )
            (output_dir / "SHA256SUMS").write_text(sums, encoding="utf-8")
            verified_size = sum(
                path.stat().st_size for path in output_dir.rglob("*") if path.is_file()
            )
            if verified_size == bundle_byte_size:
                break
        else:
            raise CampaignError("Phase-0b bundle byte-size disclosure did not stabilize")
    listed_names: list[str] = []
    for line in sums.splitlines():
        digest, name = line.split("  ", 1)
        listed_names.append(name)
        listed = output_dir.joinpath(*PurePosixPath(name).parts)
        if not listed.is_file() or sha256_file(listed) != digest:
            raise CampaignError(f"SHA256SUMS verification failed for {name}")
    all_names = {
        path.relative_to(output_dir).as_posix()
        for path in output_dir.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS"
    }
    if len(listed_names) != len(set(listed_names)) or set(listed_names) != all_names:
        raise CampaignError("SHA256SUMS does not cover every bundle file exactly once")
    return output_dir


def _publish_research_bundle(
    output_dir: Path,
    *,
    campaign_config_path: Path,
    predeclaration_path: Path,
    ruling_path: Path | None = None,
    owner_ruling_path: Path | None = None,
    seed_ledger: Sequence[Mapping[str, Any]],
    candidate_loss_surfaces: Mapping[str, Any],
    p01_recovery_rows: Sequence[Mapping[str, Any]] | None = None,
    p02_misspecification_rows: Sequence[Mapping[str, Any]] | None = None,
    p03_profile: Mapping[str, Any] | None = None,
    campaign_summary: Mapping[str, Any] | None = None,
    input_hashes: Mapping[str, str] | None = None,
    p02_complete_loss_surfaces: Mapping[str, Any] | None = None,
    p02_provenance: Mapping[str, Any] | None = None,
    retained_evidence_files: Mapping[str, bytes] | None = None,
    retained_evidence_index: Sequence[Mapping[str, Any]] = (),
    execution_complete: bool = False,
    mocked: bool = False,
    execution_started_at: float | None = None,
) -> Path:
    """Atomically publish a complete standalone research bundle."""

    if output_dir.exists():
        if not output_dir.is_dir():
            raise CampaignError(f"research bundle destination is not a directory: {output_dir}")
        if any(output_dir.iterdir()):
            raise CampaignError("research bundle destination must be empty before writing")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_dir.parent))
    try:
        _populate_research_bundle(
            staging,
            campaign_config_path=campaign_config_path,
            predeclaration_path=predeclaration_path,
            ruling_path=ruling_path,
            owner_ruling_path=owner_ruling_path,
            seed_ledger=seed_ledger,
            candidate_loss_surfaces=candidate_loss_surfaces,
            p01_recovery_rows=p01_recovery_rows,
            p02_misspecification_rows=p02_misspecification_rows,
            p03_profile=p03_profile,
            campaign_summary=campaign_summary,
            input_hashes=input_hashes,
            p02_complete_loss_surfaces=p02_complete_loss_surfaces,
            p02_provenance=p02_provenance,
            retained_evidence_files=retained_evidence_files,
            retained_evidence_index=retained_evidence_index,
            execution_complete=execution_complete,
            mocked=mocked,
            execution_started_at=execution_started_at,
        )
        if output_dir.exists():
            if not output_dir.is_dir() or any(output_dir.iterdir()):
                raise CampaignError("research bundle destination changed before publication")
            output_dir.rmdir()
        os.replace(staging, output_dir)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output_dir


def write_research_bundle(
    output_dir: Path,
    *,
    campaign_config_path: Path,
    predeclaration_path: Path,
    ruling_path: Path | None = None,
    owner_ruling_path: Path | None = None,
    seed_ledger: Sequence[Mapping[str, Any]],
    candidate_loss_surfaces: Mapping[str, Any],
    p01_recovery_rows: Sequence[Mapping[str, Any]] | None = None,
    p02_misspecification_rows: Sequence[Mapping[str, Any]] | None = None,
    p03_profile: Mapping[str, Any] | None = None,
    campaign_summary: Mapping[str, Any] | None = None,
    input_hashes: Mapping[str, str] | None = None,
    p02_complete_loss_surfaces: Mapping[str, Any] | None = None,
    p02_provenance: Mapping[str, Any] | None = None,
) -> Path:
    """Write an unexecuted bundle; completed status is reserved for execute."""

    return _publish_research_bundle(
        output_dir,
        campaign_config_path=campaign_config_path,
        predeclaration_path=predeclaration_path,
        ruling_path=ruling_path,
        owner_ruling_path=owner_ruling_path,
        seed_ledger=seed_ledger,
        candidate_loss_surfaces=candidate_loss_surfaces,
        p01_recovery_rows=p01_recovery_rows,
        p02_misspecification_rows=p02_misspecification_rows,
        p03_profile=p03_profile,
        campaign_summary=campaign_summary,
        input_hashes=input_hashes,
        p02_complete_loss_surfaces=p02_complete_loss_surfaces,
        p02_provenance=p02_provenance,
        execution_complete=False,
        mocked=False,
    )


def dry_run(
    config_path: Path,
    predeclaration_path: Path,
    ruling_path: Path | None = None,
    owner_ruling_path: Path | None = None,
) -> WorkloadPlan:
    """Validate and report counts without invoking simulation code."""

    config = CampaignConfig.from_yaml(config_path)
    validate_predeclaration(predeclaration_path, config.expected_predeclaration_sha256)
    ruling_hash = validate_g29_ruling(ruling_path, config) if ruling_path is not None else None
    owner_hash = (
        validate_owner_ruling(owner_ruling_path, config) if owner_ruling_path is not None else None
    )
    if owner_ruling_path is not None and config.profile.owner_ruling_path is None:
        raise CampaignError("--owner-ruling is only declared for Phase 0b")
    plan = guard_workload(config)
    output = {
        "predeclaration_sha256": config.expected_predeclaration_sha256,
        "g29_ruling_path": config.g29_ruling_path,
        "g29_ruling_sha256": config.g29_ruling_sha256,
        "g29_ruling_verified": ruling_hash is not None,
        **plan.as_dict(),
    }
    if config.profile is PHASE0B_PROFILE:
        output.update(
            {
                "predeclaration_path": config.profile.predeclaration_path,
                "predeclaration_verified": True,
                "p0_1_latent_calls": plan.p01_latent_calls,
                "p0_2a_latent_calls": 0,
                "p0_2b_latent_calls": 0,
                "p0_2a_observation_transforms": (
                    plan.p02_wrong_delay_cells * P01_FIT_REPLICATE_COUNT
                ),
                "p0_2b_observation_transforms": (
                    plan.p02_wrong_regime_cells * P01_FIT_REPLICATE_COUNT
                ),
                "p0_3_latent_calls": plan.p03_latent_calls,
                "p0_3_observation_transforms": plan.p03_observation_transforms,
                "owner_ruling_path": config.owner_ruling_path,
                "owner_ruling_sha256": config.owner_ruling_sha256,
                "owner_ruling_verified": owner_hash is not None,
            }
        )
    print(json.dumps(output, indent=2))
    return plan


def _bundle_destination_is_available(output_dir: Path) -> None:
    if output_dir.exists():
        if not output_dir.is_dir():
            raise CampaignError(f"research bundle destination is not a directory: {output_dir}")
        if any(output_dir.iterdir()):
            raise CampaignError("research bundle destination must be empty before execution")


def _campaign_input_hashes(
    root: Path,
    config_path: Path,
    predeclaration_path: Path,
    ruling_path: Path,
    owner_ruling_path: Path | None = None,
) -> dict[str, str]:
    source_root = root / "src" / "jersey_outbreak"
    source_paths = sorted(source_root.rglob("*.py"))
    hashes = {str(path.relative_to(root)): sha256_file(path) for path in source_paths}
    for relative in (
        "configs/diseases/respiratory_seirs_demo.yaml",
        "configs/observation/observation_demo.yaml",
    ):
        hashes[relative] = sha256_file(root / relative)
    hashes["campaign_config"] = sha256_file(config_path)
    hashes["predeclaration"] = sha256_file(predeclaration_path)
    hashes["g29_ruling"] = sha256_file(ruling_path)
    if owner_ruling_path is not None:
        hashes["phase0b_owner_ruling"] = sha256_file(owner_ruling_path)
    return hashes


def _seed_ledger(config: CampaignConfig) -> list[dict[str, Any]]:
    ledger: list[dict[str, Any]] = []
    for process_seed, observation_seed in zip(
        config.target_process_seeds, config.target_observation_seeds, strict=True
    ):
        ledger.append(
            {
                "role": "target",
                "process_seed": process_seed,
                "observation_seed": observation_seed,
                "observation_config_id": config.target_observation_config_id,
            }
        )
    for process_seed, observation_seed in zip(
        config.candidate_process_seeds, config.candidate_observation_seeds, strict=True
    ):
        ledger.append(
            {
                "role": "candidate",
                "process_seed": process_seed,
                "observation_seed": observation_seed,
                "observation_config_id": config.candidate_observation_config_id,
            }
        )
    ledger.append(
        {
            "role": "p0_3_global_route_factor_cells",
            "cells": [cell.as_dict() for cell in _p03_grid(config)],
            "process_seeds": list(config.candidate_process_seeds),
            "observation_seeds": list(config.candidate_observation_seeds),
        }
    )
    return ledger


def _overall_phase0_status(arms: Mapping[str, Mapping[str, Any]]) -> str:
    """Return PASS only when every software and scientific arm status is proven PASS."""

    scientific = [str(arm.get("scientific_status", "NOT_ESTABLISHED")) for arm in arms.values()]
    software_complete = all(arm.get("software_status") == "PASS" for arm in arms.values())
    if "FAIL" in scientific:
        return "FAIL"
    if software_complete and scientific and all(status == "PASS" for status in scientific):
        return "PASS"
    return "NOT_ESTABLISHED"


def _compact_json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode("utf-8")


def _cell_identity(cell: Mapping[str, Any]) -> str:
    return json.dumps(cell, sort_keys=True, separators=(",", ":"))


def _collect_retained_evidence(
    p01_result: P01CampaignResult,
    p02_result: P02CampaignResult,
    p03_result: P03CampaignResult,
    workspace: Path,
) -> tuple[dict[str, bytes], list[dict[str, Any]]]:
    """Copy exact blind read-backs and all observed tables into bundle-ready files."""

    files: dict[str, bytes] = {}
    evidence_index: list[dict[str, Any]] = []

    def add_file(relative_path: str, content: bytes, entry: Mapping[str, Any]) -> None:
        if relative_path in files:
            raise CampaignError(f"duplicate retained evidence path: {relative_path}")
        files[relative_path] = content
        evidence_index.append(
            {
                "path": relative_path,
                "file_sha256": hashlib.sha256(content).hexdigest(),
                **dict(entry),
            }
        )

    blind_records: list[dict[str, Any]] = []
    record_groups = (
        ("p0_1", workspace / "p0_1" / "blind_estimates", p01_result.config.target_process_seeds),
        (
            "p0_2a",
            workspace / "p0_2" / "p0_2a" / "blind_estimates",
            p01_result.config.target_process_seeds,
        ),
        (
            "p0_2b",
            workspace / "p0_2" / "p0_2b" / "blind_estimates",
            p01_result.config.target_process_seeds,
        ),
    )
    for arm, source_dir, target_seeds in record_groups:
        for target_seed in target_seeds:
            source_path = source_dir / f"{target_seed}.json"
            try:
                content = source_path.read_bytes()
                record = json.loads(content)
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise CampaignError(
                    f"persisted blind estimate is unavailable for {arm}/{target_seed}"
                ) from exc
            if not isinstance(record, dict) or not isinstance(record.get("estimate_hash"), str):
                raise CampaignError(
                    f"persisted blind estimate is malformed for {arm}/{target_seed}"
                )
            relative_path = f"blind_estimates/{arm}/{target_seed}.json"
            file_sha256 = hashlib.sha256(content).hexdigest()
            entry = {
                "path": relative_path,
                "arm": arm,
                "target_seed": target_seed,
                "estimate_hash": record["estimate_hash"],
                "file_sha256": file_sha256,
                "persist_before_truth_join": "guaranteed_by_code_path",
            }
            blind_records.append(entry)
            add_file(
                relative_path,
                content,
                {
                    "kind": "blind_estimate_readback",
                    "recomputes": (
                        "Persisted truth-free selected estimate, profiles, complete surface, "
                        "and tie record."
                    ),
                    "arm": arm,
                    "target_seed": target_seed,
                    "estimate_hash": record["estimate_hash"],
                    "persist_before_truth_join": "guaranteed_by_code_path",
                    "manifest": "blind_estimate_manifest.json",
                },
            )

    blind_manifest = {
        "schema_version": 1,
        "record_count": len(blind_records),
        "runtime_event_order_recorded": False,
        "records": blind_records,
        "ordering_note": (
            "Persistence and read-back verification occur before each truth evaluation by "
            "construction of the execution code path. Runtime event order and timestamps "
            "were not recorded."
        ),
    }
    blind_manifest_bytes = _compact_json_bytes(blind_manifest)
    add_file(
        "blind_estimate_manifest.json",
        blind_manifest_bytes,
        {
            "kind": "blind_estimate_order_manifest",
            "record_count": len(blind_records),
            "recomputes": "Record identity and code-path persist-before-truth-join guarantee.",
        },
    )

    truth_diagnostics = {
        "schema_version": 1,
        "targets": [
            {
                "target_seed": seed,
                **p01_result.target_diagnostics[seed].as_dict(),
            }
            for seed in p01_result.config.target_process_seeds
        ],
    }
    truth_bytes = _compact_json_bytes(truth_diagnostics)
    add_file(
        "p0_1_truth_diagnostics.json",
        truth_bytes,
        {
            "kind": "p0_1_truth_diagnostics",
            "target_count": len(p01_result.config.target_process_seeds),
            "recomputes": "campaign_summary.json arms.p0_1.predicates.truth_viability",
        },
    )

    candidate_provenance: list[dict[str, Any]] = []
    config = p01_result.config
    expected_p01_keys: set[tuple[CandidateCell, int, int]] = set()
    for cell_index, cell in enumerate(config.candidate_grid):
        for process_seed, observation_seed in zip(
            config.candidate_process_seeds, config.candidate_observation_seeds, strict=True
        ):
            key = (cell, process_seed, observation_seed)
            expected_p01_keys.add(key)
            table = p01_result.candidate_prediction_library[cell][
                config.candidate_process_seeds.index(process_seed)
            ]
            table_sha256 = _observed_table_sha256(table)
            if p01_result.candidate_observation_hashes.get(key) != table_sha256:
                raise CampaignError(
                    "P0-1 candidate observed-table hash is incomplete or mismatched"
                )
            candidate_provenance.append(
                {
                    "cell_index": cell_index,
                    "cell": cell.as_dict(),
                    "process_seed": process_seed,
                    "observation_seed": observation_seed,
                    "cell_config_sha256": p01_result.candidate_config_hashes[cell],
                    "observed_table_sha256": table_sha256,
                }
            )
    if set(p01_result.candidate_observation_hashes) != expected_p01_keys:
        raise CampaignError("P0-1 candidate observed-table hash inventory is incomplete")
    candidate_provenance_bytes = _compact_json_bytes({"replicate_provenance": candidate_provenance})
    add_file(
        "p0_1_candidate_provenance.json",
        candidate_provenance_bytes,
        {
            "kind": "p0_1_candidate_table_provenance",
            "replicate_count": len(candidate_provenance),
            "recomputes": "Cross-check all P0-1 candidate table and cell-config digests.",
        },
    )

    def add_table(
        *,
        arm: str,
        role: str,
        cell_index: int | None,
        cell: CandidateCell | P03Cell,
        process_seed: int,
        observation_seed: int,
        table: ObservedTables,
        expected_sha256: str,
        provenance_reference: str,
    ) -> None:
        cell_payload = cell.as_dict()
        table_sha256 = _observed_table_sha256(table)
        if table_sha256 != expected_sha256:
            raise CampaignError(
                f"retained observed-table hash mismatch for {arm}/{process_seed}/{observation_seed}"
            )
        if role == "target":
            relative_path = (
                f"observed_tables/{arm}/targets/target-{process_seed}"
                f"-observation-{observation_seed}.json"
            )
        else:
            if cell_index is None:
                raise CampaignError("candidate observed-table retention requires a cell index")
            relative_path = (
                f"observed_tables/{arm}/candidates/cell-{cell_index:03d}/"
                f"process-{process_seed}-observation-{observation_seed}.json"
            )
        payload = {
            "arm": arm,
            "role": role,
            "cell_index": cell_index,
            "cell": cell_payload,
            "process_seed": process_seed,
            "observation_seed": observation_seed,
            "table_sha256": table_sha256,
            "observed_tables": table.as_dict(),
        }
        content = _compact_json_bytes(payload)
        add_file(
            relative_path,
            content,
            {
                "kind": "observed_table",
                "recomputes": (
                    "P0-1/P0-2/P0-3 objective surfaces and P0-2B E_i from target and "
                    "candidate tables."
                ),
                "arm": arm,
                "role": role,
                "cell_index": cell_index,
                "cell": cell_payload,
                "process_seed": process_seed,
                "observation_seed": observation_seed,
                "table_sha256": table_sha256,
                "provenance_reference": provenance_reference,
            },
        )

    truth_by_seed = p01_result.target_truths
    for process_seed, observation_seed in zip(
        config.target_process_seeds, config.target_observation_seeds, strict=True
    ):
        add_table(
            arm="p0_1",
            role="target",
            cell_index=None,
            cell=truth_by_seed[process_seed],
            process_seed=process_seed,
            observation_seed=observation_seed,
            table=p01_result.target_tables[process_seed],
            expected_sha256=p01_result.target_observation_hashes[process_seed],
            provenance_reference=(
                f"p0_2_provenance.json.reused_p01_target_provenance.{process_seed}"
            ),
        )

    for arm in ("p0_1", "p0_2a", "p0_2b", "p0_3"):
        grid: Sequence[CandidateCell | P03Cell]
        library: Mapping[Any, Sequence[ObservedTables]]
        provenance_lookup: Mapping[tuple[str, int, int], str]
        if arm == "p0_1":
            grid = config.candidate_grid
            library = p01_result.candidate_prediction_library
            provenance_lookup = {
                (
                    _cell_identity(item["cell"]),
                    int(item["process_seed"]),
                    int(item["observation_seed"]),
                ): str(item["observed_table_sha256"])
                for item in candidate_provenance
            }
            provenance_reference = "p0_1_candidate_provenance.json.replicate_provenance"
        elif arm in ("p0_2a", "p0_2b"):
            arm_result = p02_result.arms[arm]
            grid = config.candidate_grid if arm == "p0_2a" else _p02b_grid(config)
            library = arm_result.candidate_prediction_library
            provenance_lookup = {
                (
                    _cell_identity(item["candidate"]),
                    int(item["process_seed"]),
                    int(item["observation_seed"]),
                ): str(item["observed_table_sha256"])
                for item in arm_result.replicate_provenance
            }
            provenance_reference = f"p0_2_provenance.json.arms.{arm}.replicate_provenance"
        else:
            grid = _p03_grid(config)
            library = p03_result.candidate_prediction_library
            provenance_lookup = {
                (
                    _cell_identity(item["candidate"]),
                    int(item["process_seed"]),
                    int(item["observation_seed"]),
                ): str(item["observed_table_sha256"])
                for item in p03_result.replicate_provenance
            }
            provenance_reference = "p0_3_profile.json.replicate_provenance"

        if set(library) != set(grid):
            raise CampaignError(f"{arm} observed-table library is incomplete")
        for cell_index, candidate_cell in enumerate(cast(Sequence[CandidateCell | P03Cell], grid)):
            identity = _cell_identity(candidate_cell.as_dict())
            tables = cast(Mapping[Any, Sequence[ObservedTables]], library)[candidate_cell]
            if len(tables) != len(config.candidate_process_seeds):
                raise CampaignError(f"{arm} observed-table replicate count is incomplete")
            for replicate_index, (process_seed, observation_seed) in enumerate(
                zip(config.candidate_process_seeds, config.candidate_observation_seeds, strict=True)
            ):
                table = tables[replicate_index]
                provenance_key = (identity, process_seed, observation_seed)
                expected_sha256 = provenance_lookup.get(provenance_key)
                if expected_sha256 is None:
                    raise CampaignError(f"{arm} observed-table provenance is missing")
                add_table(
                    arm=arm,
                    role="candidate",
                    cell_index=cell_index,
                    cell=candidate_cell,
                    process_seed=process_seed,
                    observation_seed=observation_seed,
                    table=table,
                    expected_sha256=expected_sha256,
                    provenance_reference=provenance_reference,
                )

    profile = p01_result.config.profile
    expected_table_counts = {
        "p0_1": len(p01_result.config.target_process_seeds)
        + profile.p01_cells * P01_FIT_REPLICATE_COUNT,
        "p0_2a": profile.p02a_cells * P01_FIT_REPLICATE_COUNT,
        "p0_2b": profile.p02b_cells * P01_FIT_REPLICATE_COUNT,
        "p0_3": P03_OBSERVATION_TRANSFORMS,
    }
    actual_table_counts = {
        arm: sum(
            1
            for item in evidence_index
            if item.get("kind") == "observed_table" and item.get("arm") == arm
        )
        for arm in expected_table_counts
    }
    if actual_table_counts != expected_table_counts:
        raise CampaignError("retained observed-table counts do not match the declared workload")
    return files, evidence_index


def execute_campaign(
    config_path: Path,
    predeclaration_path: Path,
    output_dir: Path,
    ruling_path: Path | None = None,
    owner_ruling_path: Path | None = None,
    *,
    mocked_for_test: bool = False,
) -> Path:
    """Execute each implemented arm in order and publish one immutable bundle."""

    config = CampaignConfig.from_yaml(config_path)
    profile = config.profile
    validate_predeclaration(predeclaration_path, config.expected_predeclaration_sha256)
    if ruling_path is None:
        raise CampaignError("execute requires a verified G29 ruling supplied with --ruling")
    validate_g29_ruling(ruling_path, config)
    if profile.owner_ruling_path is not None:
        if owner_ruling_path is None:
            raise CampaignError(
                "Phase-0b execute requires the verified model-owner ruling supplied "
                "with --owner-ruling"
            )
        validate_owner_ruling(owner_ruling_path, config)
    elif owner_ruling_path is not None:
        raise CampaignError("--owner-ruling is only declared for Phase 0b")
    plan = guard_workload(config)
    _bundle_destination_is_available(output_dir)
    missing = tuple(arm for arm in config.required_arms if arm not in config.implemented_arms)
    if missing:
        raise CampaignBlockedError(
            "campaign execution is fail-closed; required arms are not implemented: "
            + ", ".join(missing)
        )
    if config.implemented_arms != config.required_arms:
        raise CampaignBlockedError("all required arms must be implemented in declared order")

    root = config_path.resolve().parents[2]
    if not (root / "src" / "jersey_outbreak").is_dir():
        root = predeclaration_path.resolve().parents[3]
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{output_dir.name}.workspace-", dir=output_dir.parent
    ) as workspace_name:
        workspace = Path(workspace_name)
        total_started = time.perf_counter()
        arm_started = time.perf_counter()
        p01_result = run_p01_campaign(
            config_path, predeclaration_path, workspace / "p0_1", root=root
        )
        p01_wall_seconds = time.perf_counter() - arm_started
        p02_result = run_p02_campaign(p01_result, workspace / "p0_2", root=root)
        arm_started = time.perf_counter()
        p03_result = run_p03_campaign(p01_result, workspace / "p0_3", root=root)
        p03_wall_seconds = time.perf_counter() - arm_started
        total_wall_seconds = time.perf_counter() - total_started

        p01_evidence = p01_result.execution_evidence
        p02a = p02_result.arms["p0_2a"]
        p02b = p02_result.arms["p0_2b"]
        if (
            p01_evidence.measured_latent_calls != plan.p01_latent_calls
            or p01_evidence.measured_observation_transforms != plan.p01_observation_transforms
            or p02a.measured_latent_calls + p02b.measured_latent_calls != 0
            or p02a.measured_observation_transforms != profile.p02a_cells * P01_FIT_REPLICATE_COUNT
            or p02b.measured_observation_transforms != profile.p02b_cells * P01_FIT_REPLICATE_COUNT
            or p03_result.measured_latent_calls != plan.p03_latent_calls
            or p03_result.measured_observation_transforms != plan.p03_observation_transforms
            or len(p01_result.generated_parents) != plan.distinct_network_seed_builds
        ):
            raise BudgetError("measured all-arms work does not match the guarded plan")
        measured_latent = (
            p01_evidence.measured_latent_calls
            + p02a.measured_latent_calls
            + p02b.measured_latent_calls
            + p03_result.measured_latent_calls
        )
        measured_transforms = (
            p01_evidence.measured_observation_transforms
            + p02a.measured_observation_transforms
            + p02b.measured_observation_transforms
            + p03_result.measured_observation_transforms
        )
        if (
            measured_latent != profile.total_latent_calls
            or measured_transforms != profile.total_transforms
        ):
            raise BudgetError("measured all-arms totals do not match the frozen profile")

        p01_scientific = p01_result.evaluation.status
        p02_scientific = {
            name: arm.misspecification_detection or "NOT_ESTABLISHED"
            for name, arm in p02_result.arms.items()
        }
        arms: dict[str, dict[str, Any]] = {
            "p0_1": {
                "software_status": "PASS",
                "scientific_status": p01_scientific,
                "predicates": dict(p01_result.evaluation.predicates),
            },
            "p0_2a": {
                "software_status": p02a.software_status,
                "scientific_status": p02_scientific["p0_2a"],
                "misspecification_detection": p02a.misspecification_detection,
                "detection_reason": p02a.detection_reason,
            },
            "p0_2b": {
                "software_status": p02b.software_status,
                "scientific_status": p02_scientific["p0_2b"],
                "misspecification_detection": p02b.misspecification_detection,
                "detection_reason": p02b.detection_reason,
            },
            "p0_3": {
                "software_status": p03_result.software_status,
                "scientific_status": p03_result.scientific_status,
                "classification": p03_result.classification,
                "predicates": dict(p03_result.predicates),
            },
        }
        if profile is PHASE0B_PROFILE:
            arms["p0_1"]["boundary_counts"] = dict(p01_result.evaluation.boundary_counts)
        overall_status = _overall_phase0_status(arms)
        summary = {
            (
                "overall_phase0b_status" if profile is PHASE0B_PROFILE else "overall_phase0_status"
            ): overall_status,
            "arms": arms,
            "workload_plan": plan.as_dict(),
            "measured_work": {
                "grid_cells": plan.total_cells,
                "latent_outbreak_calls": measured_latent,
                "observation_transforms": measured_transforms,
                "distinct_population_network_seed_builds": len(p01_result.generated_parents),
                "mode": config.mode,
                "maximum_duration_days": config.duration_days,
            },
            "execution_complete": True,
        }
        if profile is PHASE0B_PROFILE:
            summary["lineage"] = dict(PHASE0_LINEAGE)
            summary["disclosures"] = {
                "wall_time_seconds_by_arm": {
                    "p0_1": p01_wall_seconds,
                    "p0_2a": p02a.wall_time_seconds,
                    "p0_2b": p02b.wall_time_seconds,
                    "p0_3": p03_wall_seconds,
                },
                "total_wall_time_seconds": total_wall_seconds,
                "bundle_byte_size": None,
            }
        p01_surfaces = {
            str(seed): [row.as_dict() for row in fit.loss_surface]
            for seed, fit in p01_result.blind_fits.items()
        }
        p02_surfaces = {
            name: {
                str(seed): [row.as_dict() for row in rows]
                for seed, rows in arm.loss_surfaces.items()
            }
            for name, arm in p02_result.arms.items()
        }
        p02_rows = [
            {
                **result.as_dict(),
                "software_status": arm.software_status,
                "misspecification_detection": arm.misspecification_detection,
                "detection_reason": arm.detection_reason,
            }
            for arm in p02_result.arms.values()
            for result in arm.target_results
        ]
        retained_files, retained_index = _collect_retained_evidence(
            p01_result, p02_result, p03_result, workspace
        )
        hashes = _campaign_input_hashes(
            root, config_path, predeclaration_path, ruling_path, owner_ruling_path
        )
        return _publish_research_bundle(
            output_dir,
            campaign_config_path=config_path,
            predeclaration_path=predeclaration_path,
            ruling_path=ruling_path,
            owner_ruling_path=owner_ruling_path,
            seed_ledger=_seed_ledger(config),
            candidate_loss_surfaces=p01_surfaces,
            p01_recovery_rows=[dict(row) for row in p01_result.evaluation.rows],
            p02_misspecification_rows=p02_rows,
            p03_profile=p03_result.as_dict(),
            campaign_summary=summary,
            input_hashes=hashes,
            p02_complete_loss_surfaces=p02_surfaces,
            p02_provenance=p02_result.as_dict(),
            retained_evidence_files=retained_files,
            retained_evidence_index=retained_index,
            execution_complete=True,
            mocked=mocked_for_test,
            execution_started_at=total_started,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JOS Phase-0 synthetic-recovery campaign")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("dry-run", "execute"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--config", type=Path, required=True)
        subparser.add_argument("--predeclaration", type=Path, required=True)
        subparser.add_argument("--ruling", type=Path)
        subparser.add_argument("--owner-ruling", type=Path)
        if command == "execute":
            subparser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "dry-run":
            dry_run(
                arguments.config,
                arguments.predeclaration,
                arguments.ruling,
                arguments.owner_ruling,
            )
        else:
            execute_campaign(
                arguments.config,
                arguments.predeclaration,
                arguments.output_dir,
                arguments.ruling,
                arguments.owner_ruling,
            )
    except (CampaignError, CampaignBlockedError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
