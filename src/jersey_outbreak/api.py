"""Local versioned HTTP API for the Jersey Outbreak Simulator."""

from __future__ import annotations

import csv
import json
import math
import os
import subprocess
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Any, get_args

import pyarrow.parquet as pq
from fastapi import FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from . import __version__
from .api_schemas import (
    API_SCHEMA_VERSION,
    API_VERSION,
    DEFAULT_DATASET_LIMIT,
    MAX_DATASET_ROWS,
    DatasetQuery,
    JobKind,
    JobRequest,
    JobState,
    ScenarioValidationRequest,
    _normalize_json_dates,
)
from .execution_adapter import _path_inside
from .intervention_schemas import InterventionType
from .job_manager import JobManager, JobSubmissionError
from .job_registry import (
    IdempotencyConflictError,
    InvalidJobTransitionError,
    JobNotFoundError,
    RegistryError,
)
from .network_schemas import ROUTE_FAMILIES
from .outbreak_schemas import ROUTE_IDS
from .population_schemas import DEFAULT_MODE_TARGETS
from .travel_schemas import TRAVEL_ROUTE_IDS, TravelMode


def _error(code: str, message: str, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"code": code, "message": message, "details": details}


def _safe_validation_errors(exc: ValidationError | RequestValidationError) -> list[Any]:
    """Make Pydantic issue context JSON-safe without exposing a traceback."""

    return json.loads(json.dumps(exc.errors(), default=str))


def _git_identity(root: Path) -> tuple[str | None, bool]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False
        )
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        return commit.stdout.strip() or None, bool(status_result.stdout.strip())
    except OSError:
        return None, True


def _public_job(manager: JobManager, job: dict[str, Any]) -> dict[str, Any]:
    envelope = job.get("canonical_request") or {}
    request = envelope.get("request", envelope)
    artifacts = manager.artifacts(job["job_id"]) if job["state"] == "SUCCEEDED" else []
    return {
        "job_id": job["job_id"],
        "kind": job["job_kind"],
        "state": job["state"],
        "phase": job["phase"],
        "created_at": job["created_at"],
        "started_at": job["started_at"],
        "finished_at": job["finished_at"],
        "progress_fraction": job["progress_fraction"],
        "request_hash": job["request_hash"],
        "request": request,
        "scenario_hash": job["scenario_hash"],
        "latent_hash": job["latent_hash"],
        "bundle_hash": job["bundle_hash"],
        "error": (
            {"code": job["error_code"], "message": job["error_message"]}
            if job["error_code"]
            else None
        ),
        "artifact_count": len(artifacts),
        "verification_status": job["verification_status"],
        "worker_pid": job["worker_pid"],
        "last_heartbeat": job["last_heartbeat"],
        "exit_status": job["exit_status"],
        "result_manifest_path": job["result_manifest_path"],
        "result_manifest_hash": job["result_manifest_hash"],
        "engine_git_commit": job["engine_git_commit"],
        "dirty_worktree_flag": bool(job["dirty_worktree_flag"])
        if job["dirty_worktree_flag"] is not None
        else None,
        "status_url": f"/api/{API_VERSION}/jobs/{job['job_id']}",
    }


def _parquet_type(field: Any) -> str:
    return str(field.type)


def _dataset_metadata(path: Path) -> dict[str, Any]:
    parquet = pq.ParquetFile(path)
    metadata = parquet.metadata
    fields = [{"name": field.name, "type": _parquet_type(field)} for field in parquet.schema_arrow]
    date_min: str | None = None
    date_max: str | None = None
    if "date" in parquet.schema_arrow.names:
        date_index = parquet.schema_arrow.names.index("date")
        for row_group_index in range(metadata.num_row_groups):
            statistics = metadata.row_group(row_group_index).column(date_index).statistics
            if statistics is None or statistics.min is None or statistics.max is None:
                continue
            low = str(statistics.min)
            high = str(statistics.max)
            date_min = low if date_min is None else min(date_min, low)
            date_max = high if date_max is None else max(date_max, high)
    return {
        "columns": fields,
        "row_count": metadata.num_rows,
        "date_range": {"start": date_min, "end": date_max} if date_min else None,
        "file_size_bytes": path.stat().st_size,
    }


def _safe_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _safe_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_json(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "isoformat") and not isinstance(value, (str, bytes)):
        try:
            return value.isoformat()
        except (AttributeError, TypeError):
            pass
    if hasattr(value, "item"):
        return _safe_json(value.item())
    return value


def _matches(row: dict[str, Any], query: DatasetQuery) -> bool:
    row_date = row.get("date")
    if row_date is not None:
        row_date_text = str(row_date)
        if query.start_date is not None and row_date_text < query.start_date.isoformat():
            return False
        if query.end_date is not None and row_date_text > query.end_date.isoformat():
            return False
    elif query.start_date is not None or query.end_date is not None:
        return False
    for field in (
        "parish",
        "route_id",
        "age_band",
        "intervention_id",
        "scope",
        "metric",
        "key",
    ):
        expected = getattr(query, field)
        if expected is not None and str(row.get(field)) != expected:
            return False
    return query.seed is None or row.get("seed") == query.seed


def _row_sort_key(row: dict[str, Any]) -> tuple[str, str]:
    return (
        str(row.get("date") or ""),
        json.dumps(_safe_json(row), sort_keys=True, separators=(",", ":")),
    )


def _read_bounded(path: Path, query: DatasetQuery) -> tuple[list[dict[str, Any]], int]:
    """Stream Parquet batches and retain only the bounded page window."""

    keep = query.offset + query.limit
    selected: list[dict[str, Any]] = []
    total = 0
    parquet = pq.ParquetFile(path)
    for batch in parquet.iter_batches(batch_size=2048):
        for raw in batch.to_pylist():
            row = _safe_json(raw)
            if not _matches(row, query):
                continue
            total += 1
            selected.append(row)
        # Every generated JOS dataset is written in a stable logical order.
        # Sorting after each batch keeps memory bounded while preserving the
        # canonical order for the page window.
        selected.sort(key=_row_sort_key)
        if len(selected) > keep:
            del selected[keep:]
    selected.sort(key=_row_sort_key)
    return selected[query.offset : query.offset + query.limit], total


def _dataset_path(
    manager: JobManager, job_id: str, dataset_name: str
) -> tuple[Path, str, dict[str, Any]]:
    if not dataset_name or dataset_name in {".", ".."}:
        raise ValueError("invalid dataset name")
    if "/" in dataset_name or "\\" in dataset_name or Path(dataset_name).is_absolute():
        raise ValueError("dataset names must be logical allow-listed names")
    artifacts = manager.artifacts(job_id)
    matches: list[tuple[str, dict[str, Any]]] = []
    for artifact in artifacts:
        names = artifact.get("datasets", [])
        for name in names:
            logical = f"{artifact['role']}:{name}" if len(artifacts) > 1 else name
            if dataset_name == logical:
                matches.append((name, artifact))
    if not matches:
        raise KeyError(dataset_name)
    name, artifact = matches[0]
    job_dir = manager._job_dir(job_id)
    manifest_path = _path_inside(job_dir / artifact["manifest_path"], job_dir)
    artifact_dir = manifest_path.parent
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    # Resolve the file only from the scientific manifest's allow-list.
    allowed: list[Path] = []
    for record in manifest_payload.get("output_artifacts", []):
        candidate = Path(str(record["path"]))
        if not candidate.is_absolute():
            candidate = artifact_dir / candidate
        try:
            candidate = _path_inside(candidate, artifact_dir)
        except ValueError:
            continue
        if candidate.suffix == ".parquet" and candidate.stem == name and candidate.is_file():
            allowed.append(candidate)
    if len(allowed) != 1:
        raise KeyError(dataset_name)
    return allowed[0], logical, artifact


def _load_parishes(root: Path) -> list[str]:
    path = root / "data" / "processed" / "parish_population.csv"
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return sorted({row["parish"] for row in csv.DictReader(handle) if row.get("parish")})
    except (OSError, KeyError):
        return []


def create_app(
    *,
    state_dir: Path | None = None,
    project_root: Path | None = None,
    max_concurrent_jobs: int = 1,
    cors_origins: list[str] | None = None,
    start_scheduler: bool = True,
) -> FastAPI:
    """Create the local API application and start its persistent scheduler."""

    root = (project_root or Path(__file__).resolve().parents[2]).resolve()
    manager = JobManager(
        state_dir=state_dir,
        project_root=root,
        max_concurrent_jobs=max_concurrent_jobs,
    )
    if start_scheduler:
        manager.start()
    configured_origins = cors_origins
    if configured_origins is None:
        configured_origins = [
            item.strip()
            for item in os.environ.get(
                "JOS_CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
            ).split(",")
            if item.strip()
        ]

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        manager.close()

    app = FastAPI(
        title="Jersey Outbreak Simulator Local API",
        version=API_SCHEMA_VERSION,
        lifespan=lifespan,
        description=(
            "Local-only execution and retrieval interface over the synthetic, "
            "scientifically bounded JOS engine."
        ),
    )
    app.state.job_manager = manager
    app.state.project_root = root
    app.add_middleware(
        CORSMiddleware,
        allow_origins=configured_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Idempotency-Key"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error(
                "validation_error",
                "Request validation failed",
                details={"issues": _safe_validation_errors(exc)},
            ),
        )

    @app.exception_handler(HTTPException)
    async def http_error_handler(_request: Request, exc: Any) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, dict) else None
        return JSONResponse(
            status_code=exc.status_code,
            content=detail or _error("request_error", "The request could not be completed"),
        )

    @app.get("/health", tags=["system"])
    def health() -> dict[str, Any]:
        try:
            manager.registry.get_job("__health_probe__")
        except JobNotFoundError:
            registry_status = "ok"
        except RegistryError:
            registry_status = "error"
        return {
            "status": "ok" if registry_status == "ok" else "degraded",
            "api_version": API_VERSION,
            "api_schema_version": API_SCHEMA_VERSION,
            "registry": registry_status,
        }

    @app.get(f"/api/{API_VERSION}/capabilities", tags=["system"])
    def capabilities() -> dict[str, Any]:
        commit, dirty = _git_identity(root)
        return {
            "api_version": API_VERSION,
            "api_schema_version": API_SCHEMA_VERSION,
            "package_version": __version__,
            "engine": {
                "name": "Starsim",
                "version": "3.5.2",
                "git_commit": commit,
                "dirty_worktree_flag": dirty,
            },
            "artifact_schema_versions": {
                "m5": "1.0",
                "m6_observation": "1.1",
                "m6_ensemble": "1.2",
                "m7": "2.0",
                "m8": "2.0",
            },
            "population_presets": DEFAULT_MODE_TARGETS,
            "job_kinds": ["scenario_run", "scenario_compare", "ensemble"],
            "resident_route_ids": list(ROUTE_IDS),
            "travel_route_ids": list(TRAVEL_ROUTE_IDS),
            "route_families": list(ROUTE_FAMILIES),
            "intervention_families": list(get_args(InterventionType)),
            "travel_modes": list(get_args(TravelMode)),
            "parishes": _load_parishes(root),
            "dataset_names": [
                "daily_epidemic",
                "daily_parish",
                "daily_route",
                "daily_age",
                "transmission_events",
                "daily_intervention_state",
                "intervention_events",
                "route_effects",
                "ensemble_summary",
                "replicate_trajectories",
                "replicate_grid",
                "matched_seed_comparison",
                "daily_travel_population",
                "daily_travel_route",
                "travel_episodes",
                "travel_transmission_events",
            ],
            "scheduler": {
                "configured_max_concurrent_jobs": manager.max_concurrent_jobs,
                "effective_max_concurrent_jobs": manager.max_concurrent_jobs,
                "policy": "FIFO; one API scientific job by default",
                "worker_execution_mode": "subprocess; POSIX process group when available",
            },
            "limits": {
                "default_dataset_rows": DEFAULT_DATASET_LIMIT,
                "max_dataset_rows": MAX_DATASET_ROWS,
            },
            "state_directory": "per-user application state; exact path intentionally not exposed",
            "scientific_claim_boundary": (
                "Synthetic research engine interface; not a validated forecast."
            ),
        }

    @app.post(f"/api/{API_VERSION}/scenarios/validate", tags=["scenarios"])
    def validate_scenario(payload: ScenarioValidationRequest) -> dict[str, Any]:
        try:
            from .intervention_schemas import ScenarioConfig

            scenario = ScenarioConfig.model_validate(_normalize_json_dates(payload.scenario))
        except ValidationError as exc:
            return {"valid": False, "errors": _safe_validation_errors(exc), "warnings": []}
        except (TypeError, ValueError) as exc:
            return {"valid": False, "errors": [{"message": str(exc)}], "warnings": []}
        return {
            "valid": True,
            "errors": [],
            "warnings": [
                "Scenario values are synthetic assumptions and do not constitute a forecast."
            ],
            "normalized": scenario.model_dump(mode="json"),
            "scenario_config_hash": scenario.config_hash,
        }

    @app.post(f"/api/{API_VERSION}/jobs", status_code=status.HTTP_202_ACCEPTED, tags=["jobs"])
    def submit_job(
        request: JobRequest,
        response: Response,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, Any]:
        try:
            job = manager.submit(request, idempotency_key=idempotency_key)
        except IdempotencyConflictError as exc:
            raise __import__("fastapi").HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error("idempotency_conflict", str(exc)),
            ) from exc
        except JobSubmissionError as exc:
            raise __import__("fastapi").HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=_error("validation_error", "Job request failed scientific pre-validation"),
            ) from exc
        response.headers["Location"] = f"/api/{API_VERSION}/jobs/{job['job_id']}"
        return {
            "job_id": job["job_id"],
            "kind": job["job_kind"],
            # Submission is asynchronous: the scheduler may claim a very
            # small CI job before this response is serialized, but the
            # submission contract always starts at QUEUED.
            "state": "QUEUED",
            "request_hash": job["request_hash"],
            "status_url": f"/api/{API_VERSION}/jobs/{job['job_id']}",
            "events_url": f"/api/{API_VERSION}/jobs/{job['job_id']}/events",
            "already_exists": bool(job.get("_already_exists", False)),
        }

    @app.get(f"/api/{API_VERSION}/jobs", tags=["jobs"])
    def list_jobs(
        state: JobState | None = None,
        kind: JobKind | None = None,
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        jobs, total = manager.list_jobs(state=state, kind=kind, limit=limit, offset=offset)
        return {
            "jobs": [_public_job(manager, job) for job in jobs],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    @app.get(f"/api/{API_VERSION}/jobs/{{job_id}}", tags=["jobs"])
    def get_job(job_id: str) -> dict[str, Any]:
        try:
            return _public_job(manager, manager.get(job_id))
        except JobNotFoundError as exc:
            raise __import__("fastapi").HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_error("job_not_found", "Job was not found"),
            ) from exc

    @app.post(f"/api/{API_VERSION}/jobs/{{job_id}}/cancel", tags=["jobs"])
    def cancel_job(job_id: str) -> dict[str, Any]:
        try:
            job, action = manager.cancel(job_id)
        except JobNotFoundError as exc:
            raise __import__("fastapi").HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_error("job_not_found", "Job was not found"),
            ) from exc
        except InvalidJobTransitionError as exc:
            raise __import__("fastapi").HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error(
                    "invalid_job_transition", "Job cannot be cancelled in its current state"
                ),
            ) from exc
        return {
            "job_id": job_id,
            "state": job["state"],
            "action": action,
            "idempotent": action == "already_cancelled",
        }

    @app.get(f"/api/{API_VERSION}/jobs/{{job_id}}/events", tags=["jobs"])
    def job_events(job_id: str, limit: int = Query(default=200, ge=1, le=1_000)) -> dict[str, Any]:
        try:
            return {"job_id": job_id, "events": manager.events(job_id, limit=limit)}
        except JobNotFoundError as exc:
            raise __import__("fastapi").HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_error("job_not_found", "Job was not found"),
            ) from exc

    @app.get(f"/api/{API_VERSION}/jobs/{{job_id}}/artifacts", tags=["results"])
    def job_artifacts(job_id: str) -> dict[str, Any]:
        try:
            job = manager.get(job_id)
            return {
                "job_id": job_id,
                "artifacts": manager.artifacts(job_id) if job["state"] == "SUCCEEDED" else [],
            }
        except JobNotFoundError as exc:
            raise __import__("fastapi").HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_error("job_not_found", "Job was not found"),
            ) from exc

    @app.get(f"/api/{API_VERSION}/jobs/{{job_id}}/datasets", tags=["results"])
    def job_datasets(job_id: str) -> dict[str, Any]:
        try:
            job = manager.get(job_id)
            if job["state"] != "SUCCEEDED":
                return {"job_id": job_id, "datasets": [], "available": False}
            artifacts: list[dict[str, Any]] = manager.artifacts(job_id)
            datasets: list[dict[str, Any]] = []
            for artifact in artifacts:
                for name in artifact.get("datasets", []):
                    logical = f"{artifact['role']}:{name}" if len(artifacts) > 1 else name
                    path, _, _ = _dataset_path(manager, job_id, logical)
                    datasets.append(
                        {
                            "name": logical,
                            "artifact_role": artifact["role"],
                            "artifact_id": artifact["artifact_id"],
                            "metadata": _dataset_metadata(path),
                        }
                    )
            return {"job_id": job_id, "datasets": datasets, "available": True}
        except JobNotFoundError as exc:
            raise __import__("fastapi").HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_error("job_not_found", "Job was not found"),
            ) from exc
        except (OSError, ValueError, KeyError) as exc:
            raise __import__("fastapi").HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error("artifact_unavailable", "Verified dataset metadata is unavailable"),
            ) from exc

    @app.get(f"/api/{API_VERSION}/jobs/{{job_id}}/datasets/{{dataset_name}}", tags=["results"])
    def read_dataset(
        job_id: str,
        dataset_name: str,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = Query(default=DEFAULT_DATASET_LIMIT, ge=1, le=MAX_DATASET_ROWS),
        offset: int = Query(default=0, ge=0, le=100_000),
        parish: str | None = None,
        route_id: str | None = None,
        age_band: str | None = None,
        intervention_id: str | None = None,
        scope: str | None = None,
        metric: str | None = None,
        key: str | None = None,
        seed: int | None = Query(default=None, ge=0),
    ) -> dict[str, Any]:
        try:
            job = manager.get(job_id)
            if job["state"] != "SUCCEEDED":
                raise __import__("fastapi").HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=_error(
                        "dataset_unavailable", "Datasets are available only after verified success"
                    ),
                )
            path, logical_name, artifact = _dataset_path(manager, job_id, dataset_name)
            query = DatasetQuery(
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset,
                parish=parish,
                route_id=route_id,
                age_band=age_band,
                intervention_id=intervention_id,
                scope=scope,
                metric=metric,
                key=key,
                seed=seed,
            )
            rows, total = _read_bounded(path, query)
            return {
                "job_id": job_id,
                "dataset": logical_name,
                "artifact_id": artifact["artifact_id"],
                "metadata": _dataset_metadata(path),
                "rows": rows,
                "total": total,
                "limit": limit,
                "offset": offset,
                "next_offset": offset + limit if offset + limit < total else None,
            }
        except JobNotFoundError as exc:
            raise __import__("fastapi").HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_error("job_not_found", "Job was not found"),
            ) from exc
        except KeyError as exc:
            raise __import__("fastapi").HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_error(
                    "dataset_unavailable", "Dataset is not present in the verified artifact"
                ),
            ) from exc
        except ValueError as exc:
            raise __import__("fastapi").HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error("invalid_dataset", "Dataset name is not a safe allow-listed name"),
            ) from exc
        except (OSError, TypeError) as exc:
            raise __import__("fastapi").HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error("dataset_unavailable", "Dataset could not be read"),
            ) from exc

    return app
