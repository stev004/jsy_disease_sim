"""Strict synthetic-recovery calibration contracts for the bounded C3 harness."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic.types import StrictBool, StrictFloat, StrictInt

from .contracts import ArtifactRecord, NonEmptyString, StrictModel


class CalibrationConfig(StrictModel):
    """Predeclared bounds for delay and transmission-beta recovery experiments."""

    schema_version: Literal["1.1"] = "1.1"
    study_id: NonEmptyString
    hidden_parameter: Literal["reporting_delay_days", "transmission_beta"] = "reporting_delay_days"
    candidate_min_days: StrictInt = Field(default=0, ge=0)
    candidate_max_days: StrictInt = Field(default=4, ge=0)
    trial_count: StrictInt = Field(default=5, ge=1, le=100)
    study_seed: StrictInt = Field(default=2026, ge=0)
    synthetic_truth_delay_days: StrictInt = Field(default=2, ge=0)
    recovery_tolerance_days: StrictInt = Field(default=1, ge=0)
    heldout_seed: StrictInt = Field(default=124, ge=0)
    candidate_beta_values: tuple[StrictFloat, ...] = (0.04, 0.06, 0.08, 0.10, 0.12)
    synthetic_truth_beta: StrictFloat = Field(default=0.08, ge=0, le=1)
    recovery_tolerance_beta: StrictFloat = Field(default=0.021, ge=0, le=1)
    training_replicate_seeds: tuple[StrictInt, ...] = (123, 124)
    heldout_replicate_seeds: tuple[StrictInt, ...] = (125,)

    @field_validator(
        "candidate_beta_values",
        "training_replicate_seeds",
        "heldout_replicate_seeds",
        mode="before",
    )
    @classmethod
    def normalize_sequences(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("candidate_beta_values")
    @classmethod
    def validate_beta_values(cls, value: tuple[float, ...]) -> tuple[float, ...]:
        if not value or any(beta < 0 or beta > 1 for beta in value):
            raise ValueError("candidate beta values must be non-empty and in [0, 1]")
        if len(set(value)) != len(value):
            raise ValueError("candidate beta values must be unique")
        return value

    @field_validator("training_replicate_seeds", "heldout_replicate_seeds")
    @classmethod
    def validate_replicate_seeds(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if not value or any(seed < 0 for seed in value) or len(set(value)) != len(value):
            raise ValueError("calibration replicate seeds must be non-negative and unique")
        return value

    @model_validator(mode="after")
    def validate_bounds(self) -> CalibrationConfig:
        if self.hidden_parameter == "transmission_beta":
            if self.trial_count != len(self.candidate_beta_values):
                raise ValueError("beta recovery requires one trial per candidate beta")
            if self.synthetic_truth_beta not in self.candidate_beta_values:
                raise ValueError("synthetic truth beta must be one of the candidate values")
            return self
        if self.candidate_min_days > self.candidate_max_days:
            raise ValueError("candidate delay lower bound exceeds upper bound")
        expected_trials = self.candidate_max_days - self.candidate_min_days + 1
        if self.trial_count != expected_trials:
            raise ValueError("the grid recovery harness requires one trial per integer candidate")
        return self


class CalibrationArtifactManifest(StrictModel):
    """Manifest for a synthetic calibration experiment, including all trials."""

    manifest_schema_version: Literal["1.1"] = "1.1"
    artifact_id: NonEmptyString
    generator_version: NonEmptyString = "6.1.0"
    study_id: NonEmptyString
    status: Literal["passed", "failed"]
    target_latent_run_logical_content_hash: NonEmptyString
    heldout_latent_run_logical_content_hash: NonEmptyString
    calibration_config_hash: NonEmptyString
    disease_parameter_hash: NonEmptyString
    observation_parameter_hash: NonEmptyString
    logical_content_hash: NonEmptyString
    trial_count: StrictInt
    parameter_name: NonEmptyString = "reporting_delay_days"
    recovered_parameter_value: StrictFloat
    synthetic_truth_value: StrictFloat
    recovery_error: StrictFloat
    recovery_tolerance: StrictFloat
    recovery_error_days: StrictInt | None = None
    recovery_tolerance_days: StrictInt | None = None
    heldout_objective: StrictFloat
    heldout_recovery_error: StrictFloat
    heldout_recovery_error_days: StrictInt | None = None
    heldout_passed: StrictBool
    created_at: NonEmptyString
    git_commit: str | None = None
    dirty_worktree_flag: StrictBool
    runtime_seconds: StrictFloat
    output_artifacts: list[ArtifactRecord]

    @field_validator(
        "target_latent_run_logical_content_hash",
        "heldout_latent_run_logical_content_hash",
        "calibration_config_hash",
        "disease_parameter_hash",
        "observation_parameter_hash",
        "logical_content_hash",
    )
    @classmethod
    def validate_hash(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("calibration hashes must be lowercase 64-character hex digests")
        return value

    @model_validator(mode="after")
    def validate_results(self) -> CalibrationArtifactManifest:
        if self.trial_count < 1 or self.recovered_parameter_value < 0:
            raise ValueError("calibration results must be non-negative")
        if self.recovery_error < 0 or self.recovery_tolerance < 0:
            raise ValueError("calibration recovery errors must be non-negative")
        if self.recovery_error_days is not None and self.recovery_error_days < 0:
            raise ValueError("legacy delay recovery error must be non-negative")
        if self.recovery_tolerance_days is not None and self.recovery_tolerance_days < 0:
            raise ValueError("legacy delay recovery tolerance must be non-negative")
        if self.heldout_recovery_error < 0:
            raise ValueError("heldout calibration recovery error must be non-negative")
        if self.runtime_seconds < 0 or self.heldout_objective < 0:
            raise ValueError("calibration runtime/objective must be non-negative")
        return self
