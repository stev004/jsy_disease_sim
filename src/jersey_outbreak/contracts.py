"""Strict, versioned contracts used by the Milestone 0 spike."""

from __future__ import annotations

from datetime import date, datetime
from math import isfinite
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.types import StrictBool, StrictFloat, StrictInt, StrictStr

ModelVersion = Literal["1.0"]
EvidenceStatus = Literal["official", "literature", "derived", "fixture"]
ParameterStatus = Literal[
    "observed",
    "derived",
    "literature_prior",
    "calibrated",
    "scenario_assumption",
]
ValidationLevel = Literal[
    "compatibility_spike",
    "demonstration",
    "calibrated_reconstruction",
    "prospective_forecast",
]

NonEmptyString = Annotated[StrictStr, Field(min_length=1)]
PositiveInt = Annotated[StrictInt, Field(gt=0)]
NonNegativeInt = Annotated[StrictInt, Field(ge=0)]


class StrictModel(BaseModel):
    """Base class preventing silent coercion and unknown contract fields."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        validate_assignment=True,
    )


class ProjectConfig(StrictModel):
    """Project-level metadata and scientific guardrails."""

    schema_version: ModelVersion = "1.0"
    project_name: NonEmptyString = "Jersey Outbreak Simulator"
    engine_name: NonEmptyString = "Starsim"
    engine_version: NonEmptyString = "3.5.2"
    validation_level: ValidationLevel = "compatibility_spike"
    synthetic_people_only: StrictBool = True


class RunSettings(StrictModel):
    """Engine-independent run controls for the current spike."""

    label: NonEmptyString
    start: StrictFloat
    stop: StrictFloat
    dt: StrictFloat
    unit: Literal["day", "week", "month", "year"]
    seed: StrictInt
    n_replicates: PositiveInt = 1

    @model_validator(mode="after")
    def validate_time_window(self) -> RunSettings:
        if self.stop <= self.start:
            raise ValueError("stop must be greater than start")
        if self.dt <= 0:
            raise ValueError("dt must be positive")
        if self.seed < 0:
            raise ValueError("seed must be non-negative")
        return self


class PopulationConfig(StrictModel):
    """Population artifact reference without implementing population synthesis."""

    artifact_id: NonEmptyString
    mode: Literal["ci", "scaled", "full", "demo"]


class DiseaseConfig(StrictModel):
    """Disease module and parameter-set identifiers."""

    module: NonEmptyString
    parameter_set: NonEmptyString


class ScenarioConfig(StrictModel):
    """Declarative scenario controls; Milestone 0 has no interventions."""

    interventions: list[NonEmptyString] = Field(default_factory=list)


class ObservationConfig(StrictModel):
    """Observation-model switch, retained for the later contract boundary."""

    enabled: StrictBool = False


class OutputConfig(StrictModel):
    """Requested output products for one run."""

    parish_daily: StrictBool = False
    route_attribution: StrictBool = False
    agent_snapshots: StrictBool = False


class RunConfig(StrictModel):
    """Complete versioned run configuration."""

    schema_version: ModelVersion = "1.0"
    run: RunSettings
    population: PopulationConfig
    disease: DiseaseConfig
    scenario: ScenarioConfig = Field(default_factory=ScenarioConfig)
    observation: ObservationConfig = Field(default_factory=ObservationConfig)
    outputs: OutputConfig = Field(default_factory=OutputConfig)


class SourceRecord(StrictModel):
    """A source reference prepared for future immutable source registries."""

    source_id: NonEmptyString
    title: NonEmptyString
    publisher: NonEmptyString
    url: NonEmptyString
    retrieved_at: date
    reference_period: NonEmptyString
    license: NonEmptyString
    status: EvidenceStatus
    acquisition_method: Literal["automated", "manual", "unavailable"] = "automated"
    local_snapshot: NonEmptyString | None = None
    sha256: StrictStr | None = None
    evidence_source_id: NonEmptyString | None = None
    notes: StrictStr | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if not value.startswith(("https://", "http://")):
            raise ValueError("url must use http:// or https://")
        return value

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str | None) -> str | None:
        if value is not None and (
            len(value) != 64 or any(c not in "0123456789abcdef" for c in value)
        ):
            raise ValueError("sha256 must be a lowercase 64-character hexadecimal digest")
        return value


class DiseaseParameterProvenance(StrictModel):
    """A numeric disease parameter with separate evidence metadata."""

    distribution: NonEmptyString
    mean: StrictFloat | None = None
    sigma: StrictFloat | None = None
    status: ParameterStatus
    source_ids: list[NonEmptyString] = Field(default_factory=list)
    valid_range: tuple[StrictFloat, StrictFloat] | None = None
    notes: NonEmptyString

    @model_validator(mode="after")
    def validate_numeric_metadata(self) -> DiseaseParameterProvenance:
        numeric_values = [value for value in (self.mean, self.sigma) if value is not None]
        if any(not isfinite(value) for value in numeric_values):
            raise ValueError("numeric parameter metadata must be finite")
        if self.sigma is not None and self.sigma < 0:
            raise ValueError("sigma must be non-negative")
        if self.valid_range is not None:
            low, high = self.valid_range
            if low > high:
                raise ValueError("valid_range lower bound must not exceed upper bound")
            if self.mean is not None and not low <= self.mean <= high:
                raise ValueError("mean must fall within valid_range")
        return self


class ArtifactRecord(StrictModel):
    """Hash and size metadata for a generated artifact."""

    path: NonEmptyString
    sha256: StrictStr
    size_bytes: NonNegativeInt

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("sha256 must be a lowercase 64-character hexadecimal digest")
        return value


class RunManifest(StrictModel):
    """Reproducibility metadata emitted for every completed run."""

    manifest_schema_version: ModelVersion = "1.0"
    run_id: NonEmptyString
    created_at: datetime
    status: Literal["completed", "failed"]
    git_commit: StrictStr | None = None
    dirty_worktree_flag: StrictBool
    python_version: NonEmptyString
    starsim_version: NonEmptyString
    dependency_lock_hash: NonEmptyString
    config_hash: StrictStr
    population_artifact_id: NonEmptyString | None = None
    population_artifact_hash: StrictStr | None = None
    source_manifest_hash: StrictStr | None = None
    parameter_set_id: NonEmptyString
    parameter_set_hash: StrictStr
    replicate_seeds: list[StrictInt]
    start: StrictFloat
    stop: StrictFloat
    dt: StrictFloat
    runtime_seconds: StrictFloat
    peak_memory_bytes: NonNegativeInt | None = None
    validation_level: ValidationLevel
    output_artifacts: list[ArtifactRecord]
    declared_deterministic_outputs: list[NonEmptyString]
    summary_sha256: StrictStr

    @field_validator("created_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return value

    @field_validator("config_hash", "parameter_set_hash", "summary_sha256")
    @classmethod
    def validate_hashes(cls, value: str) -> str:
        if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("hashes must be lowercase 64-character hexadecimal digests")
        return value

    @model_validator(mode="after")
    def validate_run_metadata(self) -> RunManifest:
        if self.stop <= self.start:
            raise ValueError("stop must be greater than start")
        if self.dt <= 0:
            raise ValueError("dt must be positive")
        if self.runtime_seconds < 0:
            raise ValueError("runtime_seconds must be non-negative")
        if not self.replicate_seeds:
            raise ValueError("replicate_seeds must not be empty")
        if any(seed < 0 for seed in self.replicate_seeds):
            raise ValueError("replicate seeds must be non-negative")
        return self
