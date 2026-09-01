"""Strict Milestone 5 run and artifact contracts."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator
from pydantic.types import StrictBool, StrictFloat, StrictInt, StrictStr

from .contracts import ArtifactRecord, NonEmptyString, StrictModel
from .network_schemas import RouteKind
from .population_schemas import PopulationMode

ROUTE_IDS: tuple[RouteKind, ...] = (
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


def _default_route_multipliers() -> dict[str, float]:
    return {str(route_id): 1.0 for route_id in ROUTE_IDS}


class ParameterEntry(StrictModel):
    """One disease parameter and its evidence metadata."""

    value: StrictFloat | None = None
    distribution: NonEmptyString
    units: NonEmptyString
    status: Literal[
        "observed",
        "derived",
        "literature_prior",
        "calibrated",
        "scenario_assumption",
    ]
    source_ids: list[NonEmptyString] = Field(default_factory=list)
    valid_range: tuple[StrictFloat, StrictFloat] | None = None
    notes: NonEmptyString

    @model_validator(mode="after")
    def validate_range(self) -> ParameterEntry:
        if self.valid_range is not None:
            low, high = self.valid_range
            if low > high:
                raise ValueError("parameter valid_range lower bound exceeds upper bound")
            if self.value is not None and not low <= self.value <= high:
                raise ValueError("parameter value is outside valid_range")
        return self


class DurationSpecification(StrictModel):
    """One versioned natural-history stage duration and its provenance."""

    schema_version: Literal["1.1"] = "1.1"
    family: Literal["constant", "gamma"]
    mean_days: StrictFloat = Field(gt=0)
    cv: StrictFloat | None = Field(default=None, gt=0)
    units: Literal["days"] = "days"
    status: Literal[
        "observed",
        "derived",
        "literature_prior",
        "calibrated",
        "scenario_assumption",
    ]
    source_ids: list[NonEmptyString] = Field(default_factory=list)
    notes: NonEmptyString

    @model_validator(mode="after")
    def validate_family(self) -> DurationSpecification:
        if self.family == "constant" and self.cv is not None:
            raise ValueError("constant durations must not define cv")
        if self.family == "gamma" and self.cv is None:
            raise ValueError("gamma durations require a strictly positive cv")
        return self


class RespiratoryParameterSet(StrictModel):
    """Versioned, pathogen-neutral respiratory parameter metadata."""

    schema_version: Literal["1.1"] = "1.1"
    parameter_set_id: NonEmptyString
    module: Literal["generic_respiratory_seirs"] = "generic_respiratory_seirs"
    parameters: dict[NonEmptyString, ParameterEntry]
    durations: dict[Literal["latent", "infectious", "immunity"], DurationSpecification]
    route_multipliers: dict[str, StrictFloat]

    @field_validator("durations")
    @classmethod
    def validate_durations(
        cls, value: dict[str, DurationSpecification]
    ) -> dict[str, DurationSpecification]:
        if set(value) != {"latent", "infectious", "immunity"}:
            raise ValueError("durations must cover exactly latent, infectious and immunity")
        return value

    @field_validator("route_multipliers")
    @classmethod
    def validate_route_multipliers(cls, value: dict[str, float]) -> dict[str, float]:
        if set(value) != set(ROUTE_IDS):
            raise ValueError("route_multipliers must cover exactly the 11 M4 route IDs")
        if any(multiplier < 0 for multiplier in value.values()):
            raise ValueError("route multipliers must be non-negative")
        return value

    def numeric(self, name: str) -> float:
        """Return a required numeric parameter value."""

        entry = self.parameters.get(name)
        if entry is None or entry.value is None:
            raise ValueError(f"parameter {name!r} does not have a numeric value")
        return float(entry.value)


class OutbreakRunConfig(StrictModel):
    """Strict controls for one latent generic respiratory run."""

    schema_version: Literal["1.1"] = "1.1"
    generator_version: NonEmptyString = "11.1.0"
    mode: PopulationMode
    seed: StrictInt
    start_date: date = date(2025, 1, 6)
    duration_days: StrictInt = Field(default=30, ge=1, le=366)
    dt_days: StrictFloat = Field(default=1.0, gt=0)
    parameter_set_id: NonEmptyString = "respiratory-demo-v1.1"
    initial_seed_count: StrictInt = Field(default=1, ge=0)
    initial_prevalence: StrictFloat | None = Field(default=None, ge=0, le=1)
    import_schedule: dict[str, StrictInt] = Field(default_factory=dict)
    import_rate_per_day: StrictFloat = Field(default=0.0, ge=0)
    beta: StrictFloat = Field(default=0.08, ge=0, le=1)
    latent_duration: DurationSpecification = Field(
        default_factory=lambda: DurationSpecification(
            family="constant",
            mean_days=2.0,
            status="scenario_assumption",
            notes="Pathogen-neutral demonstration comparator.",
        )
    )
    infectious_duration: DurationSpecification = Field(
        default_factory=lambda: DurationSpecification(
            family="constant",
            mean_days=5.0,
            status="scenario_assumption",
            notes="Pathogen-neutral demonstration comparator.",
        )
    )
    immunity_duration: DurationSpecification = Field(
        default_factory=lambda: DurationSpecification(
            family="constant",
            mean_days=30.0,
            status="scenario_assumption",
            notes="Used only by the explicit V1 waning comparator.",
        )
    )
    symptomatic_probability: StrictFloat = Field(default=0.6, ge=0, le=1)
    waning_enabled: StrictBool = False
    route_multipliers: dict[str, StrictFloat] = Field(default_factory=_default_route_multipliers)

    @field_validator("seed")
    @classmethod
    def validate_seed(cls, value: int) -> int:
        if value < 0:
            raise ValueError("seed must be non-negative")
        return value

    @field_validator("import_schedule")
    @classmethod
    def validate_import_schedule(cls, value: dict[str, int]) -> dict[str, int]:
        if any(count < 0 for count in value.values()):
            raise ValueError("import schedule counts must be non-negative")
        return value

    @field_validator("route_multipliers")
    @classmethod
    def validate_route_multipliers(cls, value: dict[str, float]) -> dict[str, float]:
        if set(value) != set(ROUTE_IDS):
            raise ValueError("route_multipliers must cover exactly the 11 M4 route IDs")
        if any(multiplier < 0 for multiplier in value.values()):
            raise ValueError("route multipliers must be non-negative")
        return value

    @model_validator(mode="after")
    def validate_initialization(self) -> OutbreakRunConfig:
        if self.initial_prevalence is not None and self.initial_seed_count != 0:
            raise ValueError("set either initial_seed_count or initial_prevalence, not both")
        return self


class OutbreakArtifactManifest(StrictModel):
    """Versioned provenance manifest for one completed M5 run."""

    manifest_schema_version: Literal["1.0", "1.1", "1.2"] = "1.2"
    artifact_id: NonEmptyString
    generator_version: NonEmptyString
    module: Literal["generic_respiratory_seirs"] = "generic_respiratory_seirs"
    mode: PopulationMode
    seed: StrictInt
    start_date: date
    duration_days: StrictInt
    dt_days: StrictFloat
    starsim_version: Literal["3.5.2"] = "3.5.2"
    m2_artifact_id: NonEmptyString
    m2_logical_content_hash: StrictStr
    m3_artifact_id: NonEmptyString
    m3_logical_content_hash: StrictStr
    m4_artifact_id: NonEmptyString
    m4_logical_content_hash: StrictStr
    parameter_set_id: NonEmptyString
    parameter_set_hash: StrictStr
    config_hash: StrictStr
    logical_content_hash: StrictStr
    validation_level: Literal["demonstration"] = "demonstration"
    diagnostics_status: Literal["passed", "failed"]
    seed_specification: dict[str, Any]
    import_specification: dict[str, Any]
    attribution_totals: dict[str, int]
    created_at: str
    git_commit: StrictStr | None = None
    dirty_worktree_flag: StrictBool
    runtime_seconds: StrictFloat
    peak_memory_bytes: StrictInt | None = None
    output_artifacts: list[ArtifactRecord]

    @field_validator(
        "m2_logical_content_hash",
        "m3_logical_content_hash",
        "m4_logical_content_hash",
        "parameter_set_hash",
        "config_hash",
        "logical_content_hash",
    )
    @classmethod
    def validate_hash(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("hashes must be lowercase 64-character hexadecimal digests")
        return value

    @model_validator(mode="after")
    def validate_runtime(self) -> OutbreakArtifactManifest:
        if self.seed < 0 or self.duration_days < 1 or self.runtime_seconds < 0:
            raise ValueError("seed, duration and runtime must be valid non-negative values")
        return self
