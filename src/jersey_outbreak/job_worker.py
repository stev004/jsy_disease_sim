"""Fixed internal worker entrypoint for persisted M9 jobs.

The scheduler passes only a job identifier, state directory, and the known
project root.  The worker reloads the canonical request from disk; it never
accepts an arbitrary command or module supplied by HTTP.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .api_schemas import APIResultCandidate, CandidateArtifact
from .execution_adapter import execute_job, observed_engine_identity, parse_request
from .hashing import canonical_json_bytes, sha256_bytes
from .job_finalizer import FinalizationError, JobFinalizer
from .job_registry import JobRegistry


class WorkerCancelled(RuntimeError):
    """Raised when the registry observes a cancellation request."""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _atomic_json(path: Path, payload: Any) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _bounded_error_message(exc: Exception) -> str:
    return "Scientific worker execution failed; inspect the bounded local worker log"


def run_worker(*, job_id: str, state_dir: Path, project_root: Path) -> int:
    registry = JobRegistry(state_dir / "jobs.sqlite")
    job_directory = (state_dir / "jobs" / job_id).resolve()
    request_path = job_directory / "request.json"
    try:
        job = registry.get_job(job_id)
        if job["state"] != "RUNNING":
            return 2
        envelope = json.loads(request_path.read_text(encoding="utf-8"))
        request_hash = sha256_bytes(
            canonical_json_bytes(
                {"schema_version": envelope["schema_version"], "request": envelope["request"]}
            )
        )
        if request_hash != job["request_hash"]:
            raise ValueError("persisted request hash does not match the registry")
        request = parse_request(envelope["request"])
        submitted = envelope.get("submitted_engine_identity", {})
        observed = observed_engine_identity(project_root)
        if not submitted.get("engine_git_commit") or not observed.get("engine_git_commit"):
            raise ValueError("worker and API engine Git commits must be explicit")
        if submitted["engine_git_commit"] != observed["engine_git_commit"] or bool(
            submitted.get("dirty_worktree_flag")
        ) is not bool(observed.get("dirty_worktree_flag")):
            raise ValueError("worker and API engine identities do not match")
        registry.update_fields(
            job_id,
            {
                "engine_git_commit": observed.get("engine_git_commit"),
                "dirty_worktree_flag": int(bool(observed.get("dirty_worktree_flag"))),
                "last_heartbeat": _now(),
            },
        )

        last_phase: str | None = None

        def progress(phase: str, message: str) -> None:
            nonlocal last_phase
            current = registry.get_job(job_id)
            if current["state"] != "RUNNING":
                raise WorkerCancelled
            registry.update_fields(job_id, {"phase": phase, "last_heartbeat": _now()})
            if phase != last_phase:
                registry.add_event(job_id, "phase_changed", message, {"phase": phase})
                last_phase = phase

        result = execute_job(
            request.model_dump(mode="json"),
            root=project_root,
            job_directory=job_directory,
            progress=progress,
        )
        current = registry.get_job(job_id)
        if current["state"] != "RUNNING":
            raise WorkerCancelled
        finished_at = _now()
        candidate = APIResultCandidate(
            job_id=job_id,
            job_kind=request.kind,
            request_hash=job["request_hash"],
            started_at=job["started_at"] or finished_at,
            finished_at=finished_at,
            engine_git_commit=str(observed["engine_git_commit"]),
            dirty_worktree_flag=bool(observed.get("dirty_worktree_flag")),
            output_artifacts=[
                CandidateArtifact(role=item["role"], manifest_path=item["manifest_path"])
                for item in result.artifacts
            ],
        )
        _atomic_json(job_directory / "result_candidate.json", candidate.model_dump(mode="json"))
        progress("finalizing", "Re-reading and finalizing persisted scientific output")
        JobFinalizer(registry=registry, state_dir=state_dir, project_root=project_root).finalize(
            job_id
        )
        return 0
    except WorkerCancelled:
        try:
            if registry.get_job(job_id)["state"] == "CANCEL_REQUESTED":
                registry.transition(
                    job_id,
                    "CANCELLED",
                    phase="cancelled",
                    event_type="job_cancelled",
                    event_message="Worker stopped after cancellation request",
                )
        except Exception:
            pass
        return 2
    except Exception as exc:
        try:
            current = registry.get_job(job_id)
            if current["state"] == "CANCEL_REQUESTED":
                registry.transition(
                    job_id,
                    "CANCELLED",
                    phase="cancelled",
                    event_type="job_cancelled",
                    event_message="Cancellation finalized after worker interruption",
                )
            elif current["state"] == "RUNNING":
                registry.transition(
                    job_id,
                    "FAILED",
                    phase="failed",
                    fields={
                        "error_code": exc.code
                        if isinstance(exc, FinalizationError)
                        else "worker_execution_failed",
                        "error_message": _bounded_error_message(exc),
                        "error_details": json.dumps(
                            {"exception_type": type(exc).__name__, "message": str(exc)[:1000]},
                            sort_keys=True,
                        ),
                        "exit_status": 1,
                    },
                    event_type="job_failed",
                    event_message="Worker failed before a verified result was registered",
                    event_metadata={"exception_type": type(exc).__name__},
                )
        except Exception:
            pass
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Internal JOS M9 job worker")
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    arguments = parser.parse_args()
    return run_worker(
        job_id=arguments.job_id,
        state_dir=arguments.state_dir,
        project_root=arguments.project_root,
    )


if __name__ == "__main__":  # pragma: no cover - exercised by subprocess tests
    raise SystemExit(main())
