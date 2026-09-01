"""Strict, Starsim-independent Milestone 4 route configuration contracts."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import Field, field_validator
from pydantic.types import StrictBool, StrictFloat, StrictInt, StrictStr

from .contracts import ArtifactRecord, NonEmptyString, StrictModel
from .population_schemas import PopulationMode

RouteFamily = Literal[
    "household",
    "school",
    "work",
    "care",
    "transport",
    "indoor_community",
    "outdoor_community",
]
RouteKind = Literal[
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
]
Persistence = Literal["fixed", "periodically_refreshed", "daily_sampled"]
Calendar = Literal["always", "weekday_term", "weekday", "weekday_or_weekend", "weekend"]

ROUTE_FAMILIES: tuple[RouteFamily, ...] = (
    "household",
    "school",
    "work",
    "care",
    "transport",
    "indoor_community",
    "outdoor_community",
)


class NetworkGenerationConfig(StrictModel):
    """Stable configuration for seeded route and network construction."""

    schema_version: Literal["1.0"] = "1.0"
    generator_version: NonEmptyString = "4.2.0"
    mode: PopulationMode
    seed: StrictInt
    start_date: date = date(2025, 1, 6)
    snapshot_dates: tuple[date, ...] = (
        date(2025, 1, 6),
        date(2025, 1, 11),
        date(2025, 8, 11),
    )
    enabled_route_families: tuple[RouteFamily, ...] = ROUTE_FAMILIES
    disabled_route_ids: tuple[RouteKind, ...] = ()
    school_cross_class_contacts: StrictInt = Field(default=3, ge=0, le=20)
    workplace_transient_contacts: StrictInt = Field(default=3, ge=0, le=20)
    community_indoor_contacts: StrictInt = Field(default=3, ge=0, le=20)
    community_outdoor_contacts: StrictInt = Field(default=2, ge=0, le=20)
    activity_cv: StrictFloat = Field(default=0.0, ge=0)
    contact_activity_distribution_version: NonEmptyString = "1.0"
    bus_cohort_capacity: StrictInt = Field(default=24, ge=2, le=60)
    shared_vehicle_capacity: StrictInt = Field(default=4, ge=2, le=8)
    care_cohort_capacity: StrictInt = Field(default=8, ge=2, le=20)
    shared_vehicle_enabled: StrictBool = True
    school_calendar_year: StrictInt = 2025
    school_term_periods: tuple[tuple[date, date], ...] = (
        (date(2025, 1, 6), date(2025, 3, 27)),
        (date(2025, 4, 15), date(2025, 7, 19)),
        (date(2025, 9, 3), date(2025, 12, 18)),
    )
    school_holiday_periods: tuple[tuple[date, date], ...] = (
        (date(2025, 2, 17), date(2025, 2, 21)),
        (date(2025, 5, 27), date(2025, 5, 30)),
        (date(2025, 10, 27), date(2025, 10, 31)),
    )
    indoor_weight: StrictFloat = Field(default=0.35, ge=0, le=1)
    outdoor_weight: StrictFloat = Field(default=0.15, ge=0, le=1)
    community_regular_edge_fraction: StrictFloat = Field(default=0.6, ge=0, le=1)
    community_age_mixing: tuple[tuple[StrictFloat, ...], ...] = (
        (0.25, 0.30, 0.25, 0.15, 0.05),
        (0.20, 0.35, 0.25, 0.15, 0.05),
        (0.10, 0.15, 0.45, 0.25, 0.05),
        (0.05, 0.10, 0.20, 0.50, 0.15),
        (0.05, 0.05, 0.10, 0.30, 0.50),
    )
    school_fte_per_synthetic_endpoint: StrictFloat = Field(default=0.8, gt=0, le=2)
    care_shift_coverage_multiplier: StrictFloat = Field(default=2.0, ge=1, le=4)
    include_school_leadership: StrictBool = True

    @field_validator("seed")
    @classmethod
    def validate_seed(cls, value: int) -> int:
        if value < 0:
            raise ValueError("seed must be non-negative")
        return value

    @field_validator("enabled_route_families")
    @classmethod
    def validate_enabled_route_families(
        cls, value: tuple[RouteFamily, ...]
    ) -> tuple[RouteFamily, ...]:
        if len(set(value)) != len(value):
            raise ValueError("enabled_route_families must not contain duplicates")
        return tuple(family for family in ROUTE_FAMILIES if family in value)

    @field_validator("disabled_route_ids")
    @classmethod
    def validate_disabled_route_ids(cls, value: tuple[RouteKind, ...]) -> tuple[RouteKind, ...]:
        if len(set(value)) != len(value):
            raise ValueError("disabled_route_ids must not contain duplicates")
        return tuple(sorted(value))

    @field_validator("snapshot_dates")
    @classmethod
    def validate_snapshot_dates(cls, value: tuple[date, ...]) -> tuple[date, ...]:
        if not value:
            raise ValueError("snapshot_dates must not be empty")
        if len(set(value)) != len(value):
            raise ValueError("snapshot_dates must not contain duplicates")
        return tuple(sorted(value))

    @field_validator("school_term_periods", "school_holiday_periods")
    @classmethod
    def validate_school_periods(
        cls, value: tuple[tuple[date, date], ...]
    ) -> tuple[tuple[date, date], ...]:
        if not value or any(start > end for start, end in value):
            raise ValueError("school calendar periods must contain ordered date ranges")
        years = {start.year for start, _end in value} | {end.year for _start, end in value}
        if len(years) != 1:
            raise ValueError("school calendar periods must use one reference year")
        return value

    @field_validator("community_age_mixing")
    @classmethod
    def validate_community_age_mixing(
        cls, value: tuple[tuple[float, ...], ...]
    ) -> tuple[tuple[float, ...], ...]:
        if len(value) != 5 or any(len(row) != 5 for row in value):
            raise ValueError("community_age_mixing must be a 5x5 matrix")
        if any(weight < 0 for row in value for weight in row):
            raise ValueError("community_age_mixing weights must be non-negative")
        if any(abs(sum(row) - 1.0) > 1e-6 for row in value):
            raise ValueError("each community_age_mixing row must sum to 1")
        if not any(
            value[row][column] > 0 for row in range(5) for column in range(5) if row != column
        ):
            raise ValueError("community_age_mixing must permit cross-age contacts")
        return value

    def route_family_enabled(self, family: RouteFamily) -> bool:
        return family in self.enabled_route_families


class RouteSpec(StrictModel):
    """Scientific metadata for one separable contact route."""

    route_id: NonEmptyString
    route_family: RouteFamily
    route_kind: RouteKind
    membership_source: NonEmptyString
    persistence: Persistence
    active_calendar: Calendar
    indoor: StrictBool
    relative_weight: StrictFloat = Field(ge=0, le=1)
    weight_meaning: NonEmptyString
    assumptions: tuple[NonEmptyString, ...] = ()


class NetworkManifestConfig(StrictModel):
    """Hashes and boundary identifiers embedded in a persisted M4 manifest."""

    schema_version: Literal["1.0"] = "1.0"
    m2_artifact_id: NonEmptyString
    m2_logical_content_hash: NonEmptyString
    m3_artifact_id: NonEmptyString
    m3_logical_content_hash: NonEmptyString
    starsim_version: NonEmptyString = "3.5.2"


class NetworkArtifactManifest(StrictModel):
    """Provenance manifest for a persisted Milestone 4 route artifact."""

    manifest_schema_version: Literal["1.0", "1.1"] = "1.1"
    artifact_id: NonEmptyString
    generator_version: NonEmptyString
    mode: PopulationMode
    seed: StrictInt
    target_population: StrictInt
    actual_population: StrictInt
    m2_artifact_id: NonEmptyString
    m2_logical_content_hash: StrictStr
    m3_artifact_id: NonEmptyString
    m3_logical_content_hash: StrictStr
    config_hash: StrictStr
    logical_content_hash: StrictStr
    route_logical_hashes: dict[str, StrictStr]
    starsim_version: NonEmptyString = "3.5.2"
    diagnostics_status: Literal["passed", "failed"]
    created_at: str
    git_commit: StrictStr | None = None
    dirty_worktree_flag: StrictBool
    runtime_seconds: StrictFloat
    peak_memory_bytes: StrictInt | None = None
    output_artifacts: list[ArtifactRecord]

    @field_validator("seed")
    @classmethod
    def validate_seed(cls, value: int) -> int:
        if value < 0:
            raise ValueError("seed must be non-negative")
        return value

    @field_validator(
        "m2_logical_content_hash", "m3_logical_content_hash", "config_hash", "logical_content_hash"
    )
    @classmethod
    def validate_hash(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("hashes must be lowercase 64-character hexadecimal digests")
        return value

    @field_validator("route_logical_hashes")
    @classmethod
    def validate_route_hashes(cls, value: dict[str, str]) -> dict[str, str]:
        for digest in value.values():
            cls.validate_hash(digest)
        return value

    @field_validator("runtime_seconds")
    @classmethod
    def validate_runtime(cls, value: float) -> float:
        if value < 0:
            raise ValueError("runtime_seconds must be non-negative")
        return value
