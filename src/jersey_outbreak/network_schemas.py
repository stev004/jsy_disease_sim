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
    generator_version: NonEmptyString = "4.1.0"
    mode: PopulationMode
    seed: StrictInt
    start_date: date = date(2025, 1, 6)
    snapshot_dates: tuple[date, ...] = (
        date(2025, 1, 6),
        date(2025, 1, 11),
        date(2025, 8, 11),
    )
    enabled_route_families: tuple[RouteFamily, ...] = ROUTE_FAMILIES
    school_cross_class_contacts: StrictInt = Field(default=3, ge=0, le=20)
    workplace_transient_contacts: StrictInt = Field(default=3, ge=0, le=20)
    community_indoor_contacts: StrictInt = Field(default=3, ge=0, le=20)
    community_outdoor_contacts: StrictInt = Field(default=2, ge=0, le=20)
    bus_cohort_capacity: StrictInt = Field(default=24, ge=2, le=60)
    shared_vehicle_capacity: StrictInt = Field(default=4, ge=2, le=8)
    care_cohort_capacity: StrictInt = Field(default=8, ge=2, le=20)
    school_term_months: tuple[StrictInt, ...] = (1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12)
    indoor_weight: StrictFloat = Field(default=0.35, ge=0, le=1)
    outdoor_weight: StrictFloat = Field(default=0.15, ge=0, le=1)
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

    @field_validator("snapshot_dates")
    @classmethod
    def validate_snapshot_dates(cls, value: tuple[date, ...]) -> tuple[date, ...]:
        if not value:
            raise ValueError("snapshot_dates must not be empty")
        if len(set(value)) != len(value):
            raise ValueError("snapshot_dates must not contain duplicates")
        return tuple(sorted(value))

    @field_validator("school_term_months")
    @classmethod
    def validate_school_term_months(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if not value or any(month < 1 or month > 12 for month in value):
            raise ValueError("school_term_months must contain months from 1 to 12")
        return tuple(sorted(set(value)))

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

    manifest_schema_version: Literal["1.0"] = "1.0"
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
