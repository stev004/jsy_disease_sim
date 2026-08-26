"""Strict Milestone 3 membership and daytime-structure contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_validator
from pydantic.types import StrictBool, StrictFloat, StrictInt, StrictStr

from .contracts import ArtifactRecord, NonEmptyString, StrictModel
from .population_schemas import DEFAULT_MODE_TARGETS, PopulationMode

EconomicStatus = Literal[
    "child",
    "student",
    "employed",
    "unemployed",
    "retired",
    "not_in_labour_force",
]
CommuteMode = Literal["car", "motorbike", "walk", "bus", "cycle", "work_from_home", "other"]
JobRole = Literal["primary", "secondary"]
SizeBand = Literal["1", "2-5", "6-9", "10-19", "20-49", "50+"]


class StructureGenerationConfig(StrictModel):
    """Stable configuration for a seeded Milestone 3 structure build."""

    schema_version: Literal["1.0"] = "1.0"
    generator_version: NonEmptyString = "3.0.0"
    mode: PopulationMode
    seed: StrictInt
    target_population: StrictInt | None = None
    output_format: Literal["parquet"] = "parquet"

    @field_validator("seed")
    @classmethod
    def validate_seed(cls, value: int) -> int:
        if value < 0:
            raise ValueError("seed must be non-negative")
        return value

    @model_validator(mode="after")
    def validate_target(self) -> StructureGenerationConfig:
        target = (
            self.target_population
            if self.target_population is not None
            else DEFAULT_MODE_TARGETS[self.mode]
        )
        if self.mode == "ci" and not 2_000 <= target <= 5_000:
            raise ValueError("ci target_population must be between 2,000 and 5,000")
        if self.mode == "scaled" and not 10_000 <= target <= 25_000:
            raise ValueError("scaled target_population must be between 10,000 and 25,000")
        if self.mode == "full" and target != 104_540:
            raise ValueError("full target_population must be exactly 104,540")
        return self

    @property
    def resolved_target_population(self) -> int:
        return (
            self.target_population
            if self.target_population is not None
            else DEFAULT_MODE_TARGETS[self.mode]
        )


class SchoolRecord(StrictModel):
    school_id: NonEmptyString
    school_type: NonEmptyString
    nominal_capacity: StrictInt = Field(gt=0)
    pupil_count: StrictInt = Field(gt=0)


class SchoolClassRecord(StrictModel):
    class_id: NonEmptyString
    school_id: NonEmptyString
    school_year: NonEmptyString
    class_number: StrictInt = Field(gt=0)
    pupil_count: StrictInt = Field(gt=0)


class SchoolAssignmentRecord(StrictModel):
    agent_id: NonEmptyString
    school_id: NonEmptyString
    school_type: NonEmptyString
    school_year: NonEmptyString
    class_id: NonEmptyString
    age: StrictInt = Field(ge=0, le=95)


class WorkplaceRecord(StrictModel):
    workplace_id: NonEmptyString
    sector: NonEmptyString
    work_parish: NonEmptyString
    size_band: SizeBand
    employee_count: StrictInt = Field(gt=0)
    public_private: Literal["private"] = "private"
    team_count: StrictInt = Field(ge=0)


class WorkplaceTeamRecord(StrictModel):
    team_id: NonEmptyString
    workplace_id: NonEmptyString
    team_number: StrictInt = Field(gt=0)


class JobAssignmentRecord(StrictModel):
    job_id: NonEmptyString
    agent_id: NonEmptyString
    workplace_id: NonEmptyString
    job_role: JobRole
    sector: NonEmptyString
    work_parish: NonEmptyString
    team_id: NonEmptyString | None = None
    days_per_week: StrictInt = Field(gt=0, le=7)
    remote_days_per_week: StrictInt = Field(ge=0, le=7)

    @model_validator(mode="after")
    def validate_schedule(self) -> JobAssignmentRecord:
        if self.remote_days_per_week > self.days_per_week:
            raise ValueError("remote days cannot exceed job days")
        return self


class ResidentStructureRecord(StrictModel):
    """Milestone 3 attributes linked to one immutable Milestone 2 resident."""

    agent_id: NonEmptyString
    age: StrictInt = Field(ge=0, le=95)
    sex: Literal["male", "female"]
    home_parish: NonEmptyString
    car_access: Literal["car", "no_car"] | None = None
    economic_status: EconomicStatus
    employment_sector: NonEmptyString | None = None
    primary_workplace_id: NonEmptyString | None = None
    secondary_workplace_id: NonEmptyString | None = None
    work_parish: NonEmptyString | None = None
    school_id: NonEmptyString | None = None
    school_type: NonEmptyString | None = None
    school_year: NonEmptyString | None = None
    class_id: NonEmptyString | None = None
    commute_mode: CommuteMode | None = None
    work_from_home_days_per_week: StrictInt = Field(ge=0, le=5)
    primary_work_days_per_week: StrictInt = Field(ge=0, le=5)

    @model_validator(mode="after")
    def validate_structure(self) -> ResidentStructureRecord:
        school_fields = (self.school_id, self.school_type, self.school_year, self.class_id)
        if any(value is not None for value in school_fields) and any(
            value is None for value in school_fields
        ):
            raise ValueError("school assignment fields must be complete or empty")
        if self.economic_status == "student" and self.school_id is None:
            raise ValueError("student status requires a school assignment")
        if self.economic_status != "student" and self.school_id is not None:
            raise ValueError("only students may carry a school assignment")
        if self.economic_status == "employed":
            if self.primary_workplace_id is None or self.employment_sector is None:
                raise ValueError("employed status requires a primary job")
            if self.work_parish is None or self.commute_mode is None:
                raise ValueError("employed status requires work destination and commute mode")
        if self.economic_status != "employed" and any(
            value is not None
            for value in (
                self.employment_sector,
                self.primary_workplace_id,
                self.secondary_workplace_id,
                self.work_parish,
                self.commute_mode,
            )
        ):
            raise ValueError("non-employed status cannot carry job or commute fields")
        if self.economic_status != "employed" and self.primary_work_days_per_week != 0:
            raise ValueError("non-employed status cannot carry primary work days")
        if (
            self.secondary_workplace_id is not None
            and self.secondary_workplace_id == self.primary_workplace_id
        ):
            raise ValueError("secondary workplace must differ from primary workplace")
        if self.commute_mode == "work_from_home" and self.work_from_home_days_per_week == 0:
            raise ValueError("work-from-home commute mode requires remote days")
        if self.commute_mode != "work_from_home" and self.work_from_home_days_per_week != 0:
            raise ValueError("physical commute mode cannot carry full remote schedule")
        if self.secondary_workplace_id is not None and self.primary_work_days_per_week > 4:
            raise ValueError("secondary job requires a reduced primary work schedule")
        return self


class StructureArtifactManifest(StrictModel):
    """Reproducibility and provenance metadata for a Milestone 3 artifact."""

    model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True)

    manifest_schema_version: Literal["1.0"] = "1.0"
    artifact_id: NonEmptyString
    generator_version: NonEmptyString
    mode: PopulationMode
    seed: StrictInt
    target_population: StrictInt
    actual_population: StrictInt
    m2_artifact_id: NonEmptyString
    m2_manifest_hash: StrictStr
    m2_logical_content_hash: StrictStr
    config_hash: StrictStr
    canonical_input_hashes: dict[str, StrictStr]
    logical_content_hash: StrictStr
    diagnostics_status: Literal["passed", "failed"]
    created_at: datetime
    git_commit: StrictStr | None = None
    dirty_worktree_flag: StrictBool
    runtime_seconds: StrictFloat
    peak_memory_bytes: StrictInt | None = None
    output_artifacts: list[ArtifactRecord]

    @field_validator("created_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return value

    @field_validator(
        "m2_manifest_hash",
        "m2_logical_content_hash",
        "config_hash",
        "logical_content_hash",
    )
    @classmethod
    def validate_hash(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("hashes must be lowercase 64-character hexadecimal digests")
        return value

    @field_validator("canonical_input_hashes")
    @classmethod
    def validate_input_hashes(cls, value: dict[str, str]) -> dict[str, str]:
        for digest in value.values():
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError("canonical input hashes must be lowercase SHA-256 digests")
        return value

    @model_validator(mode="after")
    def validate_counts(self) -> StructureArtifactManifest:
        if self.actual_population != self.target_population:
            raise ValueError("generated population must equal target population")
        if self.seed < 0 or self.runtime_seconds < 0:
            raise ValueError("seed and runtime must be non-negative")
        if self.peak_memory_bytes is not None and self.peak_memory_bytes < 0:
            raise ValueError("peak memory must be non-negative")
        return self
