"""Strict observation-model contracts for the C3 causal timeline."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic.types import StrictFloat, StrictInt

from .contracts import ArtifactRecord, NonEmptyString, StrictModel

ObservationStatus = Literal[
    "observed",
    "derived",
    "literature_prior",
    "calibrated",
    "scenario_assumption",
]


class ObservationParameter(StrictModel):
    """One observation parameter with its evidence metadata."""

    parameter_id: NonEmptyString
    value: StrictFloat | None = None
    distribution: NonEmptyString
    units: NonEmptyString
    status: ObservationStatus
    source_ids: list[NonEmptyString] = Field(default_factory=list)
    valid_range: tuple[StrictFloat, StrictFloat] | None = None
    notes: NonEmptyString

    @field_validator("valid_range", mode="before")
    @classmethod
    def normalize_range(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_parameter(self) -> ObservationParameter:
        if self.valid_range is not None:
            low, high = self.valid_range
            if low > high:
                raise ValueError("observation parameter valid_range is reversed")
            if self.value is not None and not low <= self.value <= high:
                raise ValueError("observation parameter value is outside valid_range")
        return self


class ReportingDelayDistribution(StrictModel):
    """A non-negative delay distribution in whole days.

    The class name is retained for compatibility with the M6 public contract;
    it is also used for symptom-onset and detection/testing delays.
    """

    kind: Literal["fixed", "discrete"] = "fixed"
    days: tuple[StrictInt, ...] = (0,)
    probabilities: tuple[StrictFloat, ...] | None = None
    units: NonEmptyString = "days"
    valid_range: tuple[StrictInt, StrictInt] = (0, 366)
    status: ObservationStatus = "scenario_assumption"
    source_ids: list[NonEmptyString] = Field(default_factory=list)
    notes: NonEmptyString = "Synthetic reporting delay for the M6 demonstration."

    @field_validator("days", "probabilities", "valid_range", mode="before")
    @classmethod
    def normalize_sequences(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("days")
    @classmethod
    def validate_days(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if not value or any(day < 0 for day in value):
            raise ValueError("reporting delays must contain at least one non-negative day")
        return value

    @model_validator(mode="after")
    def validate_distribution(self) -> ReportingDelayDistribution:
        low, high = self.valid_range
        if low < 0 or low > high or any(day < low or day > high for day in self.days):
            raise ValueError("delay values must fall inside valid_range")
        if self.kind == "fixed":
            if len(self.days) != 1:
                raise ValueError("fixed reporting delay requires exactly one day")
            if self.probabilities is not None:
                raise ValueError("fixed reporting delay cannot have probabilities")
        else:
            if self.probabilities is None or len(self.probabilities) != len(self.days):
                raise ValueError("discrete delay probabilities must match delay values")
            if any(probability < 0 for probability in self.probabilities):
                raise ValueError("delay probabilities must be non-negative")
            if abs(sum(self.probabilities) - 1.0) > 1e-9:
                raise ValueError("discrete delay probabilities must sum to one")
        return self


DelayDistribution = ReportingDelayDistribution


class ObservationConfig(StrictModel):
    """Immutable controls for transforming one latent M5 run into observations."""

    schema_version: Literal["1.2"] = "1.2"
    observation_config_id: NonEmptyString
    parameters: dict[NonEmptyString, ObservationParameter]
    reporting_delay: ReportingDelayDistribution
    detection_delay: ReportingDelayDistribution = Field(
        default_factory=lambda: ReportingDelayDistribution(
            kind="fixed",
            days=(0,),
            status="scenario_assumption",
            notes="Generic same-day testing delay for the demonstration.",
        )
    )
    analysis_horizon_tail_days: StrictInt | None = Field(default=None, ge=0)
    day_of_week_effect: tuple[StrictFloat, ...] = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
    observation_seed: StrictInt = 0

    @field_validator("day_of_week_effect", mode="before")
    @classmethod
    def normalize_day_effect(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("observation_seed")
    @classmethod
    def validate_seed(cls, value: int) -> int:
        if value < 0:
            raise ValueError("observation_seed must be non-negative")
        return value

    @field_validator("day_of_week_effect")
    @classmethod
    def validate_day_effect(cls, value: tuple[float, ...]) -> tuple[float, ...]:
        if len(value) != 7:
            raise ValueError("day_of_week_effect must contain Monday-to-Sunday values")
        if any(effect < 0 or effect > 1 for effect in value):
            raise ValueError("day_of_week_effect values must be in [0, 1]")
        return value

    @model_validator(mode="after")
    def validate_required_parameters(self) -> ObservationConfig:
        required = {
            "symptomatic_detection_probability",
            "asymptomatic_detection_probability",
        }
        if not required <= set(self.parameters):
            raise ValueError(f"observation parameters must include {sorted(required)}")
        for key, parameter in self.parameters.items():
            if parameter.parameter_id != key:
                raise ValueError("observation parameter_id must match its mapping key")
        return self

    @model_validator(mode="after")
    def validate_horizon_tail(self) -> ObservationConfig:
        if self.analysis_horizon_tail_days is not None:
            if self.analysis_horizon_tail_days < 0:
                raise ValueError("analysis_horizon_tail_days must be non-negative")
            maximum_delay = sum(
                max(distribution.days)
                for distribution in (
                    self.detection_delay,
                    self.reporting_delay,
                )
            )
            if self.analysis_horizon_tail_days < maximum_delay:
                raise ValueError(
                    "analysis_horizon_tail_days must cover the maximum configured delay tail"
                )
        return self

    def numeric(self, name: str) -> float:
        """Return a required numeric observation parameter."""

        entry = self.parameters.get(name)
        if entry is None or entry.value is None:
            raise ValueError(f"observation parameter {name!r} does not have a numeric value")
        return float(entry.value)


class ObservationArtifactManifest(StrictModel):
    """Manifest for a standalone latent-to-observed transformation."""

    manifest_schema_version: Literal["1.2"] = "1.2"
    artifact_id: NonEmptyString
    generator_version: NonEmptyString = "6.2.0"
    latent_run_logical_content_hash: NonEmptyString
    latent_m5_artifact_id: NonEmptyString | None = None
    observation_config_id: NonEmptyString
    observation_config_hash: NonEmptyString
    observation_seed: StrictInt
    logical_content_hash: NonEmptyString
    status: Literal["passed", "failed"]
    diagnostics_status: Literal["passed", "failed"]
    created_at: NonEmptyString
    git_commit: str | None = None
    dirty_worktree_flag: bool
    runtime_seconds: StrictFloat
    output_artifacts: list[ArtifactRecord]

    @field_validator(
        "latent_run_logical_content_hash",
        "observation_config_hash",
        "logical_content_hash",
    )
    @classmethod
    def validate_hash(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("observation hashes must be lowercase 64-character hex digests")
        return value

    @model_validator(mode="after")
    def validate_runtime(self) -> ObservationArtifactManifest:
        if self.observation_seed < 0 or self.runtime_seconds < 0:
            raise ValueError("observation seed and runtime must be non-negative")
        return self
