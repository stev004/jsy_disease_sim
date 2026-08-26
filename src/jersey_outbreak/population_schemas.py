"""Strict Milestone 2 population, household and artifact contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_validator
from pydantic.types import StrictBool, StrictFloat, StrictInt, StrictStr

from .contracts import ArtifactRecord, NonEmptyString, StrictModel

PopulationMode = Literal["ci", "scaled", "full"]
Sex = Literal["male", "female"]
HouseholdType = Literal[
    "Single adult",
    "Couple (adult)",
    "Single parent (with dependent children)",
    "Single parent (all children 16 years or more)",
    "Couple with dependent children",
    "Couple with children (all children 16 years or more)",
    "Couple (one pensioner)",
    "Single pensioner",
    "Two or more pensioners",
    "Two or more unrelated persons",
    "Other",
]
HouseholdRole = Literal[
    "adult",
    "partner",
    "parent",
    "dependent_child",
    "adult_child",
    "pensioner",
    "unrelated_adult",
    "other",
    "communal_resident",
]
DwellingType = Literal["house", "flat", "other"]
CrowdingBand = Literal["overcrowded", "standard", "underoccupied"]
CarAccess = Literal["car", "no_car"]

DEFAULT_MODE_TARGETS = {"ci": 3_000, "scaled": 15_000, "full": 104_540}


class PopulationGenerationConfig(StrictModel):
    """Stable, seed-owned configuration for a Milestone 2 population build."""

    schema_version: Literal["1.0"] = "1.0"
    generator_version: NonEmptyString = "2.0.0"
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
    def validate_target(self) -> PopulationGenerationConfig:
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


class ResidentRecord(StrictModel):
    """One synthetic resident with only Milestone 2 attributes."""

    agent_id: NonEmptyString
    age: StrictInt = Field(ge=0, le=95)
    sex: Sex
    home_parish: NonEmptyString
    household_id: NonEmptyString | None = None
    household_role: HouseholdRole
    dwelling_type: DwellingType | None = None
    crowding_band: CrowdingBand | None = None
    car_access: CarAccess | None = None
    care_setting_id: NonEmptyString | None = None

    @model_validator(mode="after")
    def validate_membership(self) -> ResidentRecord:
        private = self.household_id is not None
        communal = self.care_setting_id is not None
        if private == communal:
            raise ValueError(
                "resident must belong to exactly one private household or communal setting"
            )
        if private:
            if self.household_role == "communal_resident":
                raise ValueError("private resident cannot have communal_resident role")
            if self.dwelling_type is None or self.crowding_band is None or self.car_access is None:
                raise ValueError("private resident must carry household housing attributes")
        else:
            if self.household_role != "communal_resident":
                raise ValueError("communal resident must have communal_resident role")
            if any(
                value is not None
                for value in (self.dwelling_type, self.crowding_band, self.car_access)
            ):
                raise ValueError("communal resident cannot carry private dwelling attributes")
        return self


class HouseholdRecord(StrictModel):
    """A synthetic private household and its aggregate housing attributes."""

    household_id: NonEmptyString
    household_type: HouseholdType
    home_parish: NonEmptyString
    member_count: StrictInt = Field(gt=0, le=8)
    dwelling_type: DwellingType
    crowding_band: CrowdingBand
    car_access: CarAccess


class CommunalSettingRecord(StrictModel):
    """A synthetic communal establishment; it is not a private household."""

    setting_id: NonEmptyString
    setting_type: NonEmptyString
    home_parish: NonEmptyString
    resident_count: StrictInt = Field(ge=0)


class PopulationArtifactManifest(StrictModel):
    """Reproducibility metadata for one generated population artifact."""

    model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True)

    manifest_schema_version: Literal["1.0"] = "1.0"
    artifact_id: NonEmptyString
    generator_version: NonEmptyString
    mode: PopulationMode
    seed: StrictInt
    target_population: StrictInt
    actual_population: StrictInt
    household_count: StrictInt
    communal_resident_count: StrictInt
    created_at: datetime
    git_commit: StrictStr | None = None
    dirty_worktree_flag: StrictBool
    config_hash: StrictStr
    source_manifest_hash: StrictStr
    input_canonical_hashes: dict[str, StrictStr]
    logical_content_hash: StrictStr
    diagnostics_status: Literal["passed", "failed"]
    runtime_seconds: StrictFloat
    peak_memory_bytes: StrictInt | None = None
    output_artifacts: list[ArtifactRecord]

    @field_validator("created_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return value

    @field_validator("config_hash", "source_manifest_hash", "logical_content_hash", mode="after")
    @classmethod
    def validate_hash(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("hashes must be lowercase 64-character hexadecimal digests")
        return value

    @field_validator("input_canonical_hashes")
    @classmethod
    def validate_input_hashes(cls, value: dict[str, str]) -> dict[str, str]:
        for digest in value.values():
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError("input canonical hashes must be lowercase SHA-256 digests")
        return value

    @model_validator(mode="after")
    def validate_counts(self) -> PopulationArtifactManifest:
        if self.actual_population != self.target_population:
            raise ValueError("generated population must equal target population")
        if self.household_count < 0 or self.communal_resident_count < 0:
            raise ValueError("population counts must be non-negative")
        if self.runtime_seconds < 0:
            raise ValueError("runtime_seconds must be non-negative")
        if self.peak_memory_bytes is not None and self.peak_memory_bytes < 0:
            raise ValueError("peak_memory_bytes must be non-negative")
        if self.seed < 0:
            raise ValueError("seed must be non-negative")
        return self
