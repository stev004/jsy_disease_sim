"""Strict synthetic-recovery calibration contracts for Milestone 6."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic.types import StrictBool, StrictFloat, StrictInt

from .contracts import ArtifactRecord, NonEmptyString, StrictModel


class CalibrationConfig(StrictModel):
    """Predeclared bounds for the intentionally small recovery experiment."""

    schema_version: Literal["1.0"] = "1.0"
    study_id: NonEmptyString
    hidden_parameter: Literal["reporting_delay_days"] = "reporting_delay_days"
    candidate_min_days: StrictInt = Field(default=0, ge=0)
    candidate_max_days: StrictInt = Field(default=4, ge=0)
    trial_count: StrictInt = Field(default=5, ge=1, le=100)
    study_seed: StrictInt = Field(default=2026, ge=0)
    synthetic_truth_delay_days: StrictInt = Field(default=2, ge=0)
    recovery_tolerance_days: StrictInt = Field(default=1, ge=0)
    heldout_seed: StrictInt = Field(default=124, ge=0)

    @model_validator(mode="after")
    def validate_bounds(self) -> CalibrationConfig:
        if self.candidate_min_days > self.candidate_max_days:
            raise ValueError("candidate delay lower bound exceeds upper bound")
        expected_trials = self.candidate_max_days - self.candidate_min_days + 1
        if self.trial_count != expected_trials:
            raise ValueError("the grid recovery harness requires one trial per integer candidate")
        return self


class CalibrationArtifactManifest(StrictModel):
    """Manifest for a synthetic calibration experiment, including all trials."""

    manifest_schema_version: Literal["1.0"] = "1.0"
    artifact_id: NonEmptyString
    generator_version: NonEmptyString = "6.0.0"
    study_id: NonEmptyString
    status: Literal["passed", "failed"]
    target_latent_run_logical_content_hash: NonEmptyString
    heldout_latent_run_logical_content_hash: NonEmptyString
    calibration_config_hash: NonEmptyString
    disease_parameter_hash: NonEmptyString
    observation_parameter_hash: NonEmptyString
    logical_content_hash: NonEmptyString
    trial_count: StrictInt
    recovered_parameter_value: StrictInt
    synthetic_truth_value: StrictInt
    recovery_error_days: StrictInt
    recovery_tolerance_days: StrictInt
    heldout_objective: StrictFloat
    heldout_recovery_error_days: StrictInt
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
        if self.recovery_error_days < 0 or self.recovery_tolerance_days < 0:
            raise ValueError("calibration recovery errors must be non-negative")
        if self.runtime_seconds < 0 or self.heldout_objective < 0:
            raise ValueError("calibration runtime/objective must be non-negative")
        return self
