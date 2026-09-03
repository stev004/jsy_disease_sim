"""Single fail-closed success gate for normal and restart M9 job completion."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .api_schemas import APIArtifact, APIResultCandidate, APIResultManifest, ScientificHashes
from .ensemble_schemas import EnsembleConfig
from .execution_adapter import (
    _normalize_scenario,
    _observation,
    _parameters,
    _run_config,
    default_run_config,
    parse_request,
)
from .hashing import canonical_json_bytes, sha256_bytes
from .job_registry import JobRegistry
from .scientific_hashes import m6_ensemble_config_hash, m6_ensemble_config_payload
from .scientific_verification import VerifiedScientificArtifact, verify_scientific_artifact


class FinalizationError(RuntimeError):
    """A structured, fail-closed rejection at the successful-terminal gate."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _atomic_json(path: Path, payload: Any) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _inside(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise FinalizationError(
            "artifact_path_escape", "scientific artifact path escaped the job artifact root"
        ) from exc
    return resolved


def _expected_roles(request: Any) -> dict[str, str]:
    if request.kind == "ensemble":
        return {"ensemble": "m6_ensemble"}
    if request.kind == "scenario_compare":
        return {
            "baseline": "m6_ensemble",
            "treated": "m6_ensemble",
            "comparison": "m6_comparison",
        }
    if request.scenario is None:
        return {"scientific_result": "m5_outbreak"}
    travel = request.scenario.travel
    if travel is not None and travel.mode in {"explicit_travel", "both"}:
        return {"scientific_result": "m8_travel"}
    return {"scientific_result": "m7_intervention"}


def _artifact_reference(
    *, role: str, verified: VerifiedScientificArtifact, job_directory: Path
) -> APIArtifact:
    manifest_path = verified.artifact_directory / "manifest.json"
    return APIArtifact(
        role=role,
        artifact_type=verified.artifact_type,
        artifact_id=verified.artifact_id,
        manifest_path=str(manifest_path.relative_to(job_directory)),
        scenario_hash=verified.scenario_hash,
        latent_hash=verified.latent_hash,
        bundle_hash=verified.bundle_hash,
        logical_content_hash=verified.logical_content_hash,
        verification_status="passed",
        size_bytes=verified.size_bytes,
        datasets=list(verified.datasets),
    )


def _authoritative_summary(
    request: Any, verified: dict[str, VerifiedScientificArtifact]
) -> dict[str, Any]:
    if request.kind == "scenario_run":
        artifact = verified["scientific_result"]
        payload = artifact.manifest_payload
        return {
            "mode": request.mode,
            "seed": request.seed,
            "horizon_days": request.duration_days,
            "artifact_type": artifact.artifact_type,
            "runtime_seconds": payload.get("runtime_seconds"),
        }
    if request.kind == "ensemble":
        payload = verified["ensemble"].manifest_payload
        return {
            "replicate_count": payload["replicate_count"],
            "successful_replicates": payload["successful_replicates"],
            "failed_replicates": payload["failed_replicates"],
            "execution_mode": payload["execution_mode"],
            "runtime_seconds": payload["runtime_seconds"],
        }
    payload = verified["comparison"].manifest_payload
    return {
        "paired_seed_count": payload["paired_count"],
        "missing_or_failed_pair_count": payload["missing_or_failed_pairs"],
        "runtime_seconds": payload["runtime_seconds"],
    }


class JobFinalizer:
    """Reconstruct authoritative success solely from persisted, verified data."""

    def __init__(self, *, registry: JobRegistry, state_dir: Path, project_root: Path) -> None:
        self.registry = registry
        self.state_dir = state_dir.resolve()
        self.project_root = project_root.resolve()

    def _load_request(self, job: dict[str, Any], job_directory: Path) -> tuple[Any, dict[str, Any]]:
        try:
            envelope = json.loads((job_directory / "request.json").read_text(encoding="utf-8"))
            canonical = {
                "schema_version": envelope["schema_version"],
                "request": envelope["request"],
                "submitted_engine_identity": envelope["submitted_engine_identity"],
            }
            if sha256_bytes(canonical_json_bytes(canonical)) != job["request_hash"]:
                raise FinalizationError("request_hash_mismatch", "persisted request hash mismatch")
            if canonical != job["canonical_request"]:
                raise FinalizationError(
                    "request_registry_mismatch", "persisted request and registry request differ"
                )
            request = parse_request(envelope["request"])
        except FinalizationError:
            raise
        except Exception as exc:
            raise FinalizationError(
                "invalid_persisted_request", "persisted request is invalid"
            ) from exc
        if request.kind != job["job_kind"]:
            raise FinalizationError(
                "job_kind_mismatch", "request kind does not match registry job kind"
            )
        submitted = envelope["submitted_engine_identity"]
        if submitted.get("engine_git_commit") != job["submitted_engine_commit"] or submitted.get(
            "dirty_worktree_flag"
        ) is not bool(job["submitted_dirty_worktree_flag"]):
            raise FinalizationError(
                "submitted_identity_mismatch",
                "persisted request identity does not match immutable registry submission",
            )
        return request, envelope

    @staticmethod
    def _authoritative_identity(job: dict[str, Any]) -> tuple[str, bool]:
        submitted_commit = job["submitted_engine_commit"]
        submitted_dirty = job["submitted_dirty_worktree_flag"]
        observed_commit = job["worker_observed_engine_commit"]
        observed_dirty = job["worker_observed_dirty_worktree_flag"]
        if submitted_commit is None or submitted_dirty is None:
            raise FinalizationError(
                "missing_submitted_engine_identity",
                "immutable submitted engine identity is absent",
            )
        if observed_commit is None or observed_dirty is None:
            raise FinalizationError(
                "missing_worker_observed_identity",
                "immutable worker-observed engine identity is absent",
            )
        if submitted_commit != observed_commit or bool(submitted_dirty) is not bool(observed_dirty):
            raise FinalizationError(
                "engine_identity_mismatch",
                "submitted and worker-observed engine identities differ",
            )
        return str(submitted_commit), bool(submitted_dirty)

    def _load_candidate(
        self,
        job: dict[str, Any],
        job_directory: Path,
        authoritative_commit: str,
        authoritative_dirty: bool,
    ) -> APIResultCandidate:
        path = job_directory / "result_candidate.json"
        try:
            candidate = APIResultCandidate.model_validate_json(path.read_bytes())
        except Exception as exc:
            raise FinalizationError(
                "invalid_result_candidate", "result candidate is missing or invalid"
            ) from exc
        if (
            candidate.job_id != job["job_id"]
            or candidate.job_kind != job["job_kind"]
            or candidate.request_hash != job["request_hash"]
        ):
            raise FinalizationError(
                "candidate_identity_mismatch", "result candidate identity mismatch"
            )
        if (
            candidate.engine_git_commit != authoritative_commit
            or candidate.dirty_worktree_flag is not authoritative_dirty
        ):
            raise FinalizationError(
                "candidate_provenance_mismatch",
                "candidate engine identity differs from immutable registry provenance",
            )
        return candidate

    def _verify_artifacts(
        self,
        request: Any,
        candidate: APIResultCandidate,
        job_directory: Path,
        submitted_commit: str,
        submitted_dirty: bool,
    ) -> dict[str, VerifiedScientificArtifact]:
        expected = _expected_roles(request)
        candidate_roles = [artifact.role for artifact in candidate.output_artifacts]
        if len(candidate_roles) != len(set(candidate_roles)) or set(candidate_roles) != set(
            expected
        ):
            raise FinalizationError(
                "artifact_role_contract_failed",
                "result candidate has missing, duplicate, or extra roles",
            )
        artifact_root = (job_directory / "artifacts").resolve()
        verified: dict[str, VerifiedScientificArtifact] = {}
        for artifact in candidate.output_artifacts:
            manifest = _inside(job_directory / artifact.manifest_path, artifact_root)
            if manifest.name != "manifest.json" or not manifest.is_file():
                raise FinalizationError(
                    "invalid_artifact_manifest_path",
                    "candidate does not identify a manifest.json file",
                )
            try:
                checked = verify_scientific_artifact(manifest.parent)
            except Exception as exc:
                raise FinalizationError(
                    "scientific_verification_failed",
                    f"{artifact.role} scientific verification failed",
                ) from exc
            if checked.artifact_type != expected[artifact.role]:
                raise FinalizationError(
                    "artifact_type_mismatch",
                    f"{artifact.role} has the wrong scientific artifact type",
                )
            if (
                not checked.engine_git_commit
                or checked.engine_git_commit != submitted_commit
                or checked.dirty_worktree_flag is not submitted_dirty
            ):
                raise FinalizationError(
                    "artifact_provenance_mismatch",
                    f"{artifact.role} scientific artifact has mismatched engine provenance",
                )
            verified[artifact.role] = checked
        return verified

    def _bind_request(self, request: Any, verified: dict[str, VerifiedScientificArtifact]) -> None:
        parameters = _parameters(self.project_root, getattr(request, "parameters", None))
        parameter_hash = sha256_bytes(canonical_json_bytes(parameters.model_dump(mode="json")))
        if request.kind == "scenario_run":
            run_config = _run_config(request, parameters)
            observation = (
                _observation(self.project_root, request.observation_config)
                if request.scenario is not None or request.observation_config is not None
                else None
            )
            scenario = _normalize_scenario(
                request.scenario,
                seed=request.seed,
                run_config=run_config,
                parameters=parameters,
                observation=observation,
            )
            artifact = verified["scientific_result"]
            declared_parameter_hash = artifact.manifest_payload.get(
                "parameter_set_hash",
                artifact.manifest_payload.get("m5_disease_config_hash"),
            )
            if declared_parameter_hash != parameter_hash:
                raise FinalizationError(
                    "artifact_request_mismatch", "scientific parameters do not match request"
                )
            if artifact.extra.get("run_config") != run_config.model_dump(mode="json"):
                raise FinalizationError(
                    "artifact_request_mismatch",
                    "scientific run configuration does not match request",
                )
            if scenario is not None and artifact.extra.get(
                "scenario_config"
            ) != scenario.model_dump(mode="json"):
                raise FinalizationError(
                    "artifact_request_mismatch", "scientific scenario does not match request"
                )
            return

        observation = _observation(self.project_root, request.observation_config)
        first_seed = request.replicate_seeds[0]
        run_config = (
            _run_config(request, parameters)
            if request.kind == "ensemble"
            else default_run_config(
                request.mode,
                first_seed,
                parameters,
                start_date=request.start_date,
                duration_days=request.duration_days,
            )
        )

        def expected_ensemble(ensemble_id: str, scenario_value: Any) -> dict[str, Any]:
            normalized = _normalize_scenario(
                scenario_value,
                seed=first_seed,
                run_config=run_config,
                parameters=parameters,
                observation=observation,
            )
            return m6_ensemble_config_payload(
                EnsembleConfig(
                    ensemble_id=ensemble_id,
                    base_run_config=run_config,
                    observation_config=observation,
                    scenario=normalized,
                    replicate_seeds=request.replicate_seeds,
                    workers=request.workers,
                    allow_unsafe_workers=request.allow_unsafe_workers,
                ).model_dump(mode="json")
            )

        if request.kind == "ensemble":
            ensemble = verified["ensemble"]
            if ensemble.manifest_payload.get("disease_parameter_hash") != parameter_hash:
                raise FinalizationError(
                    "artifact_request_mismatch", "ensemble disease parameters do not match request"
                )
            actual_config = ensemble.extra.get("ensemble_config")
            if not isinstance(actual_config, dict) or m6_ensemble_config_payload(
                actual_config
            ) != expected_ensemble(request.ensemble_id, request.scenario):
                raise FinalizationError(
                    "artifact_request_mismatch", "ensemble configuration does not match request"
                )
            return

        baseline_config = expected_ensemble(f"{request.comparison_id}-baseline", request.baseline)
        treated_config = expected_ensemble(f"{request.comparison_id}-treated", request.treated)
        if any(
            verified[role].manifest_payload.get("disease_parameter_hash") != parameter_hash
            for role in ("baseline", "treated")
        ):
            raise FinalizationError(
                "artifact_request_mismatch", "comparison disease parameters do not match request"
            )
        baseline_actual = verified["baseline"].extra.get("ensemble_config")
        if (
            not isinstance(baseline_actual, dict)
            or m6_ensemble_config_payload(baseline_actual) != baseline_config
        ):
            raise FinalizationError("artifact_request_mismatch", "baseline does not match request")
        treated_actual = verified["treated"].extra.get("ensemble_config")
        if (
            not isinstance(treated_actual, dict)
            or m6_ensemble_config_payload(treated_actual) != treated_config
        ):
            raise FinalizationError(
                "artifact_request_mismatch", "treated result does not match request"
            )
        comparison = verified["comparison"].extra.get("comparison_config", {})
        if (
            comparison.get("comparison_id") != request.comparison_id
            or comparison.get("ensemble_a_id") != baseline_config["ensemble_id"]
            or comparison.get("ensemble_b_id") != treated_config["ensemble_id"]
            or comparison.get("config_a_hash") != m6_ensemble_config_hash(baseline_config)
            or comparison.get("config_b_hash") != m6_ensemble_config_hash(treated_config)
            or comparison.get("matched_seed_list") != sorted(request.replicate_seeds)
        ):
            raise FinalizationError(
                "artifact_request_mismatch", "comparison configuration does not match request"
            )

    def finalize(self, job_id: str) -> APIResultManifest:
        job = self.registry.get_job(job_id)
        if job["state"] == "SUCCEEDED":
            authoritative_commit, authoritative_dirty = self._authoritative_identity(job)
            job_directory = (self.state_dir / "jobs" / job_id).resolve()
            try:
                path = _inside(job_directory / str(job["result_manifest_path"]), job_directory)
                result = APIResultManifest.model_validate_json(path.read_bytes())
                result_hash = sha256_bytes(canonical_json_bytes(result.model_dump(mode="json")))
            except Exception as exc:
                raise FinalizationError(
                    "completed_result_invalid", "completed result manifest is invalid"
                ) from exc
            if (
                result_hash != job["result_manifest_hash"]
                or result.job_id != job_id
                or result.request_hash != job["request_hash"]
                or result.engine_git_commit != authoritative_commit
                or result.dirty_worktree_flag is not authoritative_dirty
                or result.engine_git_commit != job["engine_git_commit"]
                or result.dirty_worktree_flag is not bool(job["dirty_worktree_flag"])
                or [item.model_dump(mode="json") for item in result.output_artifacts]
                != self.registry.artifacts(job_id)
            ):
                raise FinalizationError(
                    "completed_result_mismatch", "completed result identity does not match registry"
                )
            return result
        if job["state"] != "RUNNING":
            raise FinalizationError("invalid_finalization_state", "only RUNNING jobs may finalize")
        authoritative_commit, authoritative_dirty = self._authoritative_identity(job)
        job_directory = (self.state_dir / "jobs" / job_id).resolve()
        request, _envelope = self._load_request(job, job_directory)
        candidate = self._load_candidate(
            job,
            job_directory,
            authoritative_commit,
            authoritative_dirty,
        )
        verified = self._verify_artifacts(
            request,
            candidate,
            job_directory,
            authoritative_commit,
            authoritative_dirty,
        )
        self._bind_request(request, verified)
        references = [
            _artifact_reference(role=role, verified=verified[role], job_directory=job_directory)
            for role in _expected_roles(request)
        ]
        if request.kind == "scenario_compare":
            scientific_hashes = {
                "scenario_hash": verified["treated"].scenario_hash,
                "latent_hash": None,
                "bundle_hash": verified["comparison"].bundle_hash,
            }
        else:
            primary = next(iter(verified.values()))
            scientific_hashes = {
                "scenario_hash": primary.scenario_hash,
                "latent_hash": primary.latent_hash,
                "bundle_hash": primary.bundle_hash,
            }
        finished_at = candidate.finished_at or _now()
        result = APIResultManifest(
            job_id=job_id,
            job_kind=request.kind,
            request_hash=job["request_hash"],
            state="SUCCEEDED",
            started_at=job["started_at"] or candidate.started_at,
            finished_at=finished_at,
            engine_git_commit=authoritative_commit,
            dirty_worktree_flag=authoritative_dirty,
            output_artifacts=references,
            scientific_hashes=ScientificHashes.model_validate(scientific_hashes),
            summary=_authoritative_summary(request, verified),
        )
        result_payload = result.model_dump(mode="json")
        result_hash = sha256_bytes(canonical_json_bytes(result_payload))
        result_path = job_directory / "result_manifest.json"
        _atomic_json(result_path, result_payload)
        reread = APIResultManifest.model_validate_json(result_path.read_bytes())
        if (
            reread != result
            or sha256_bytes(canonical_json_bytes(reread.model_dump(mode="json"))) != result_hash
        ):
            raise FinalizationError(
                "result_manifest_verification_failed",
                "result manifest did not verify after writing",
            )
        self.registry.finalize_success(
            job_id,
            fields={
                "finished_at": finished_at,
                "result_manifest_path": "result_manifest.json",
                "result_manifest_hash": result_hash,
                "verification_status": "passed",
                "scenario_hash": scientific_hashes["scenario_hash"],
                "latent_hash": scientific_hashes["latent_hash"],
                "bundle_hash": scientific_hashes["bundle_hash"],
                "last_heartbeat": finished_at,
            },
            artifacts=[artifact.model_dump(mode="json") for artifact in references],
        )
        return result
