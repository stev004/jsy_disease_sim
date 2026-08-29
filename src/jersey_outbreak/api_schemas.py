"""Versioned application-facing contracts for the Milestone 9 API.

These models deliberately compose the existing scientific contracts instead of
repeating their enums and validation rules.  HTTP callers may submit inline
JSON models, but never paths, import names, or executable commands.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any, Literal

from pydantic import Field, field_validator, model_validator
from pydantic.types import StrictBool, StrictInt

from .contracts import NonEmptyString, StrictModel
from .intervention_schemas import ScenarioConfig
from .observation_schemas import ObservationConfig
from .outbreak_schemas import OutbreakRunConfig, RespiratoryParameterSet
from .population_schemas import PopulationMode

API_VERSION = "v1"
API_SCHEMA_VERSION = "m9-1.0"
JOB_REGISTRY_SCHEMA_VERSION = 1
MAX_DATASET_ROWS = 10_000
DEFAULT_DATASET_LIMIT = 1_000

JobKind = Literal["scenario_run", "scenario_compare", "ensemble"]
JobState = Literal[
    "QUEUED",
    "RUNNING",
    "SUCCEEDED",
    "FAILED",
    "CANCEL_REQUESTED",
    "CANCELLED",
    "INTERRUPTED",
]
JobPhase = Literal[
    "queued",
    "validating",
    "preparing",
    "running",
    "writing_artifacts",
    "verifying",
    "complete",
    "failed",
    "cancelled",
    "interrupted",
]


_DATE_FIELDS = {
    "start_date",
    "end_date",
    "arrival_date",
    "departure_date",
    "active_start",
    "active_end",
    "absence_start_date",
    "return_date",
}


def _normalize_json_dates(value: object) -> object:
    """Convert ISO date strings at the HTTP boundary for strict child models."""

    if isinstance(value, dict):
        return {
            key: (
                date.fromisoformat(item)
                if key in _DATE_FIELDS and isinstance(item, str)
                else _normalize_json_dates(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_normalize_json_dates(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_normalize_json_dates(item) for item in value)
    return value


def _normalize_http_date(value: object) -> object:
    if isinstance(value, str):
        return date.fromisoformat(value)
    return value


class ScenarioValidationRequest(StrictModel):
    """A synchronous validation request containing one inline scenario."""

    scenario: dict[str, Any]


class ScenarioRunRequest(StrictModel):
    """One asynchronous scenario, baseline, intervention, or travel run."""

    kind: Literal["scenario_run"]
    mode: PopulationMode = "ci"
    seed: StrictInt = 123
    start_date: date = date(2025, 1, 6)
    duration_days: StrictInt = Field(default=30, ge=1, le=366)
    scenario: ScenarioConfig | None = None
    parameters: RespiratoryParameterSet | None = None
    observation_config: ObservationConfig | None = None
    run_config: OutbreakRunConfig | None = None

    _normalize_start_date = field_validator("start_date", mode="before")(_normalize_http_date)
    _normalize_nested_dates = field_validator(
        "scenario", "parameters", "observation_config", "run_config", mode="before"
    )(_normalize_json_dates)


class ScenarioCompareRequest(StrictModel):
    """A matched-seed comparison of two existing scenario configurations."""

    kind: Literal["scenario_compare"]
    mode: PopulationMode = "ci"
    replicate_seeds: tuple[StrictInt, ...] = (123,)
    start_date: date = date(2025, 1, 6)
    duration_days: StrictInt = Field(default=30, ge=1, le=366)
    baseline: ScenarioConfig | None = None
    treated: ScenarioConfig
    comparison_id: NonEmptyString = "m9-comparison"
    parameters: RespiratoryParameterSet | None = None
    observation_config: ObservationConfig | None = None
    workers: StrictInt = Field(default=1, ge=1, le=32)
    allow_unsafe_workers: StrictBool = False

    _normalize_start_date = field_validator("start_date", mode="before")(_normalize_http_date)
    _normalize_nested_dates = field_validator(
        "baseline", "treated", "parameters", "observation_config", mode="before"
    )(_normalize_json_dates)

    @field_validator("replicate_seeds", mode="before")
    @classmethod
    def normalize_seeds(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_seeds(self) -> ScenarioCompareRequest:
        value = self
        if not value.replicate_seeds or any(seed < 0 for seed in value.replicate_seeds):
            raise ValueError("replicate_seeds must contain at least one non-negative seed")
        if len(set(value.replicate_seeds)) != len(value.replicate_seeds):
            raise ValueError("replicate_seeds must be unique and explicitly ordered")
        return value


class EnsembleJobRequest(StrictModel):
    """An M6/M7/M8-compatible deterministic ensemble request."""

    kind: Literal["ensemble"]
    mode: PopulationMode = "ci"
    replicate_seeds: tuple[StrictInt, ...] = (101, 102, 103)
    start_date: date = date(2025, 1, 6)
    duration_days: StrictInt = Field(default=30, ge=1, le=366)
    ensemble_id: NonEmptyString = "m9-ensemble"
    scenario: ScenarioConfig | None = None
    parameters: RespiratoryParameterSet | None = None
    observation_config: ObservationConfig | None = None
    run_config: OutbreakRunConfig | None = None
    workers: StrictInt = Field(default=1, ge=1, le=32)
    allow_unsafe_workers: StrictBool = False

    _normalize_start_date = field_validator("start_date", mode="before")(_normalize_http_date)
    _normalize_nested_dates = field_validator(
        "scenario", "parameters", "observation_config", "run_config", mode="before"
    )(_normalize_json_dates)

    @field_validator("replicate_seeds", mode="before")
    @classmethod
    def normalize_seeds(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_seeds(self) -> EnsembleJobRequest:
        value = self
        if not value.replicate_seeds or any(seed < 0 for seed in value.replicate_seeds):
            raise ValueError("replicate_seeds must contain at least one non-negative seed")
        if len(set(value.replicate_seeds)) != len(value.replicate_seeds):
            raise ValueError("replicate_seeds must be unique and explicitly ordered")
        return value


JobRequest = Annotated[
    ScenarioRunRequest | ScenarioCompareRequest | EnsembleJobRequest,
    Field(discriminator="kind"),
]


class APIArtifact(StrictModel):
    """A logical, job-owned scientific artifact reference."""

    role: NonEmptyString
    artifact_type: NonEmptyString
    artifact_id: NonEmptyString
    manifest_path: NonEmptyString
    scenario_hash: str | None = None
    latent_hash: str | None = None
    bundle_hash: str | None = None
    logical_content_hash: str | None = None
    verification_status: Literal["passed", "failed"]
    size_bytes: StrictInt = Field(ge=0)
    datasets: list[NonEmptyString] = Field(default_factory=list)


class APIResultManifest(StrictModel):
    """Application manifest; it is separate from M5–M8 scientific manifests."""

    schema_version: Literal["m9-1.0"] = "m9-1.0"
    job_id: NonEmptyString
    job_kind: JobKind
    request_hash: NonEmptyString
    state: Literal["SUCCEEDED"]
    started_at: NonEmptyString
    finished_at: NonEmptyString
    engine_git_commit: str | None = None
    dirty_worktree_flag: StrictBool
    output_artifacts: list[APIArtifact]
    scientific_hashes: dict[str, str | None] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)


class DatasetQuery(StrictModel):
    """Bounded, non-SQL dataset query controls."""

    start_date: date | None = None
    end_date: date | None = None
    limit: StrictInt = Field(default=DEFAULT_DATASET_LIMIT, ge=1, le=MAX_DATASET_ROWS)
    offset: StrictInt = Field(default=0, ge=0)
    parish: str | None = None
    route_id: str | None = None
    age_band: str | None = None
    intervention_id: str | None = None
    scope: str | None = None
    metric: str | None = None
    key: str | None = None
    seed: StrictInt | None = Field(default=None, ge=0)


class APIErrorBody(StrictModel):
    code: NonEmptyString
    message: NonEmptyString
    details: dict[str, Any] | None = None
    request_id: str | None = None


def request_payload(request: Any) -> dict[str, Any]:
    """Return canonical JSON-compatible request data for hashing/persistence."""

    return request.model_dump(mode="json", exclude_none=False)
