"""Strict ensemble and paired-comparison contracts for C3."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic.types import StrictBool, StrictFloat, StrictInt

from .contracts import ArtifactRecord, NonEmptyString, StrictModel
from .intervention_schemas import ScenarioConfig
from .observation_schemas import ObservationConfig
from .outbreak_schemas import OutbreakRunConfig

M6_ENSEMBLE_ARTIFACT_SCHEMA_VERSION: Literal["1.5"] = "1.5"


class EnsembleConfig(StrictModel):
    """Explicit replicate seed ownership and quantile controls."""

    schema_version: Literal["1.0"] = "1.0"
    ensemble_id: NonEmptyString
    generator_version: NonEmptyString = "6.2.0"
    base_run_config: OutbreakRunConfig
    observation_config: ObservationConfig
    scenario: ScenarioConfig | None = None
    replicate_seeds: tuple[StrictInt, ...] = Field(min_length=1)
    workers: StrictInt = Field(default=1, ge=1, le=32)
    # Measured full-mode worker reached 3.36 GB anon-rss at the second 2026-09-02
    # OOM kill (13:02Z); estimate rounded up.
    estimated_worker_memory_bytes: StrictInt = Field(default=3_500_000_000, gt=0)
    memory_safety_fraction: StrictFloat = Field(default=0.6, gt=0, le=1)
    allow_unsafe_workers: StrictBool = False
    lower_quantile: StrictFloat = Field(default=0.025, ge=0, le=1)
    upper_quantile: StrictFloat = Field(default=0.975, ge=0, le=1)

    @field_validator("replicate_seeds", mode="before")
    @classmethod
    def normalize_seeds(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("replicate_seeds")
    @classmethod
    def validate_seeds(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if any(seed < 0 for seed in value):
            raise ValueError("replicate seeds must be non-negative")
        if len(set(value)) != len(value):
            raise ValueError("replicate seeds must be unique and explicitly ordered")
        return value

    @model_validator(mode="after")
    def validate_quantiles(self) -> EnsembleConfig:
        if self.lower_quantile > self.upper_quantile:
            raise ValueError("lower_quantile must not exceed upper_quantile")
        return self


class EnsembleReplicateRecord(StrictModel):
    """Truthful status and hashes for one replicate."""

    seed: StrictInt
    status: Literal["passed", "failed"]
    latent_run_logical_content_hash: NonEmptyString | None = None
    observation_logical_content_hash: NonEmptyString | None = None
    m4_logical_content_hash: NonEmptyString | None = None
    scenario_hash: NonEmptyString | None = None
    intervention_config_hashes: dict[str, NonEmptyString] = Field(default_factory=dict)
    runtime_seconds: StrictFloat = 0.0
    error: str | None = None

    @model_validator(mode="after")
    def validate_status(self) -> EnsembleReplicateRecord:
        if self.seed < 0 or self.runtime_seconds < 0:
            raise ValueError("replicate seed and runtime must be non-negative")
        if self.status == "passed" and (
            self.latent_run_logical_content_hash is None
            or self.observation_logical_content_hash is None
        ):
            raise ValueError("passed replicate must retain latent and observation hashes")
        if self.status == "failed" and not self.error:
            raise ValueError("failed replicate must record an error")
        return self


class EnsembleArtifactManifest(StrictModel):
    """Manifest for a complete or explicitly partial ensemble."""

    manifest_schema_version: Literal["1.2", "1.3", "1.4", "1.5"] = (
        M6_ENSEMBLE_ARTIFACT_SCHEMA_VERSION
    )
    artifact_id: NonEmptyString
    logical_content_hash: NonEmptyString
    generator_version: NonEmptyString = "6.2.0"
    ensemble_id: NonEmptyString
    status: Literal["passed", "partial", "failed"]
    diagnostics_status: Literal["passed", "failed"]
    replicate_seeds: tuple[StrictInt, ...]
    replicate_count: StrictInt
    successful_replicates: StrictInt
    failed_replicates: StrictInt
    requested_workers: StrictInt
    planned_workers: StrictInt
    actual_workers: StrictInt
    execution_mode: NonEmptyString
    fallback_reason: str | None = None
    m2_logical_content_hash: NonEmptyString
    m3_logical_content_hash: NonEmptyString
    m4_logical_content_hashes: dict[str, NonEmptyString]
    m5_logical_content_hashes: dict[str, NonEmptyString]
    disease_parameter_hash: NonEmptyString
    observation_parameter_hash: NonEmptyString
    base_config_hash: NonEmptyString
    scenario_hash: NonEmptyString | None = None
    intervention_config_hashes: dict[str, NonEmptyString] = Field(default_factory=dict)
    quantile_configuration: dict[str, StrictFloat]
    replicate_records: list[EnsembleReplicateRecord]
    created_at: NonEmptyString
    git_commit: str | None = None
    dirty_worktree_flag: StrictBool
    runtime_seconds: StrictFloat
    peak_memory_bytes: StrictInt | None = None
    output_artifacts: list[ArtifactRecord]

    @field_validator(
        "m2_logical_content_hash",
        "m3_logical_content_hash",
        "disease_parameter_hash",
        "observation_parameter_hash",
        "base_config_hash",
        "logical_content_hash",
    )
    @classmethod
    def validate_hash(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("ensemble hashes must be lowercase 64-character hex digests")
        return value

    @model_validator(mode="after")
    def validate_counts(self) -> EnsembleArtifactManifest:
        if self.replicate_count != len(self.replicate_seeds):
            raise ValueError("replicate_count must match the explicit seed list")
        if self.successful_replicates + self.failed_replicates != self.replicate_count:
            raise ValueError("replicate status counts do not reconcile")
        if self.runtime_seconds < 0:
            raise ValueError("ensemble runtime must be non-negative")
        if not 1 <= self.actual_workers <= self.planned_workers <= self.requested_workers:
            raise ValueError("actual/planned/requested worker counts do not reconcile")
        return self


class ComparisonArtifactManifest(StrictModel):
    """Manifest for a matched-seed A/B comparison."""

    manifest_schema_version: Literal["1.0", "1.1", "1.2"] = "1.2"
    artifact_id: NonEmptyString
    logical_content_hash: NonEmptyString
    generator_version: NonEmptyString = "6.1.0"
    comparison_id: NonEmptyString
    status: Literal["passed", "partial", "failed"]
    config_a_hash: NonEmptyString
    config_b_hash: NonEmptyString
    matched_seed_list: tuple[StrictInt, ...]
    paired_count: StrictInt
    missing_or_failed_pairs: StrictInt
    created_at: NonEmptyString
    git_commit: str | None = None
    dirty_worktree_flag: StrictBool
    runtime_seconds: StrictFloat
    output_artifacts: list[ArtifactRecord]

    @field_validator("config_a_hash", "config_b_hash", "logical_content_hash")
    @classmethod
    def validate_hash(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("comparison hashes must be lowercase 64-character hex digests")
        return value
