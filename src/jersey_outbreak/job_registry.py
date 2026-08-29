"""SQLite-backed persistent registry for Milestone 9 application jobs."""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .api_schemas import JOB_REGISTRY_SCHEMA_VERSION, JobState
from .hashing import canonical_json_bytes, sha256_bytes


class RegistryError(RuntimeError):
    """Base class for persistent job-registry errors."""


class JobNotFoundError(RegistryError):
    """Raised when a job identifier is not present."""


class InvalidJobTransitionError(RegistryError):
    """Raised when a state transition is not legal."""


class IdempotencyConflictError(RegistryError):
    """Raised when one idempotency key is reused for another request."""


LEGAL_TRANSITIONS: dict[str, set[str]] = {
    "QUEUED": {"RUNNING", "CANCELLED"},
    # SUCCEEDED is deliberately absent.  Only finalize_success() may publish
    # verified output and the terminal successful state.
    "RUNNING": {"FAILED", "CANCEL_REQUESTED", "INTERRUPTED"},
    "CANCEL_REQUESTED": {"CANCELLED", "INTERRUPTED"},
    "SUCCEEDED": set(),
    "FAILED": set(),
    "CANCELLED": set(),
    "INTERRUPTED": set(),
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _decode(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    for key in ("canonical_request", "error_details", "metadata"):
        if item.get(key) is not None:
            item[key] = json.loads(item[key])
    return item


class JobRegistry:
    """Small transactional registry with versioned schema and WAL mode."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path.resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
            isolation_level=None,
            check_same_thread=False,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=30000")
        try:
            yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._lock, self._connection() as connection:
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if version > JOB_REGISTRY_SCHEMA_VERSION:
                raise RegistryError(
                    f"unsupported future job registry schema version {version}; "
                    f"maximum supported is {JOB_REGISTRY_SCHEMA_VERSION}"
                )
            if version == 0:
                connection.execute("PRAGMA journal_mode=WAL")
                connection.execute("PRAGMA synchronous=NORMAL")
                connection.executescript(
                    """
                    CREATE TABLE jobs (
                        job_id TEXT PRIMARY KEY,
                        job_kind TEXT NOT NULL,
                        state TEXT NOT NULL,
                        canonical_request TEXT NOT NULL,
                        request_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        started_at TEXT,
                        finished_at TEXT,
                        phase TEXT NOT NULL,
                        progress_fraction REAL,
                        worker_pid INTEGER,
                        exit_status INTEGER,
                        error_code TEXT,
                        error_message TEXT,
                        error_details TEXT,
                        scenario_hash TEXT,
                        latent_hash TEXT,
                        bundle_hash TEXT,
                        result_manifest_path TEXT,
                        result_manifest_hash TEXT,
                        verification_status TEXT,
                        last_heartbeat TEXT,
                        engine_git_commit TEXT,
                        dirty_worktree_flag INTEGER,
                        submitted_engine_commit TEXT NOT NULL,
                        submitted_dirty_worktree_flag INTEGER NOT NULL,
                        worker_observed_engine_commit TEXT,
                        worker_observed_dirty_worktree_flag INTEGER,
                        idempotency_key TEXT UNIQUE
                    );
                    CREATE INDEX jobs_created_idx ON jobs(created_at, job_id);
                    CREATE INDEX jobs_state_idx ON jobs(state, created_at, job_id);
                    CREATE INDEX jobs_request_hash_idx ON jobs(request_hash);
                    CREATE TABLE job_events (
                        event_id TEXT PRIMARY KEY,
                        job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        message TEXT NOT NULL,
                        metadata TEXT NOT NULL
                    );
                    CREATE INDEX job_events_job_idx ON job_events(job_id, timestamp, event_id);
                    CREATE TABLE job_artifacts (
                        artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
                        role TEXT NOT NULL,
                        artifact_type TEXT NOT NULL,
                        scientific_artifact_id TEXT NOT NULL,
                        manifest_path TEXT NOT NULL,
                        metadata TEXT NOT NULL,
                        UNIQUE(job_id, manifest_path)
                    );
                    CREATE TABLE idempotency_keys (
                        idempotency_key TEXT PRIMARY KEY,
                        request_hash TEXT NOT NULL,
                        job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE
                    );
                    PRAGMA user_version=2;
                    """
                )
            elif version == 1:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("ALTER TABLE jobs ADD COLUMN submitted_engine_commit TEXT")
                connection.execute(
                    "ALTER TABLE jobs ADD COLUMN submitted_dirty_worktree_flag INTEGER"
                )
                connection.execute("ALTER TABLE jobs ADD COLUMN worker_observed_engine_commit TEXT")
                connection.execute(
                    "ALTER TABLE jobs ADD COLUMN worker_observed_dirty_worktree_flag INTEGER"
                )
                connection.execute("PRAGMA user_version=2")
                connection.commit()

    @staticmethod
    def _new_job_id() -> str:
        return str(uuid.uuid4())

    def create_job(
        self,
        *,
        job_kind: str,
        canonical_request: dict[str, Any],
        request_hash: str,
        submitted_engine_commit: str,
        submitted_dirty_worktree_flag: bool,
        idempotency_key: str | None = None,
    ) -> tuple[dict[str, Any], bool]:
        """Create a queued job, returning ``(job, already_existed)``."""

        identity = canonical_request.get("submitted_engine_identity")
        if not isinstance(identity, dict):
            raise RegistryError("canonical request has no submitted engine identity")
        if (
            not submitted_engine_commit
            or identity.get("engine_git_commit") != submitted_engine_commit
            or identity.get("dirty_worktree_flag") is not submitted_dirty_worktree_flag
        ):
            raise RegistryError("submitted engine identity does not match canonical request")
        if request_hash != self.request_hash(canonical_request):
            raise RegistryError("request hash does not bind the canonical submission")

        job_id = self._new_job_id()
        created_at = utc_now()
        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if idempotency_key is not None:
                prior = connection.execute(
                    "SELECT request_hash, job_id FROM idempotency_keys WHERE idempotency_key=?",
                    (idempotency_key,),
                ).fetchone()
                if prior is not None:
                    if prior["request_hash"] != request_hash:
                        connection.rollback()
                        raise IdempotencyConflictError(
                            "Idempotency-Key was already used for a different canonical request"
                        )
                    row = connection.execute(
                        "SELECT * FROM jobs WHERE job_id=?", (prior["job_id"],)
                    ).fetchone()
                    connection.commit()
                    if row is None:  # pragma: no cover - protected by foreign keys
                        raise RegistryError("idempotency key points to a missing job")
                    return _decode(row), True
            connection.execute(
                """
                INSERT INTO jobs (
                    job_id, job_kind, state, canonical_request, request_hash,
                    created_at, phase, submitted_engine_commit,
                    submitted_dirty_worktree_flag, idempotency_key
                ) VALUES (?, ?, 'QUEUED', ?, ?, ?, 'queued', ?, ?, ?)
                """,
                (
                    job_id,
                    job_kind,
                    _json(canonical_request),
                    request_hash,
                    created_at,
                    submitted_engine_commit,
                    int(submitted_dirty_worktree_flag),
                    idempotency_key,
                ),
            )
            if idempotency_key is not None:
                connection.execute(
                    "INSERT INTO idempotency_keys VALUES (?, ?, ?)",
                    (idempotency_key, request_hash, job_id),
                )
            self._insert_event(
                connection,
                job_id,
                "job_submitted",
                "Job accepted and queued",
                {"job_kind": job_kind, "request_hash": request_hash},
                timestamp=created_at,
            )
            connection.commit()
            row = connection.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None:  # pragma: no cover - insert just succeeded
                raise RegistryError("job insert did not produce a row")
            return _decode(row), False

    def get_job(self, job_id: str) -> dict[str, Any]:
        with self._lock, self._connection() as connection:
            row = connection.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            raise JobNotFoundError(job_id)
        return _decode(row)

    def list_jobs(
        self,
        *,
        state: str | None = None,
        kind: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if state is not None:
            clauses.append("state=?")
            values.append(state)
        if kind is not None:
            clauses.append("job_kind=?")
            values.append(kind)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        values.extend([limit, offset])
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM jobs {where} ORDER BY created_at DESC, job_id DESC "
                "LIMIT ? OFFSET ?",
                values,
            ).fetchall()
        return [_decode(row) for row in rows]

    def count_jobs(self, *, state: str | None = None, kind: str | None = None) -> int:
        clauses: list[str] = []
        values: list[Any] = []
        if state is not None:
            clauses.append("state=?")
            values.append(state)
        if kind is not None:
            clauses.append("job_kind=?")
            values.append(kind)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._lock, self._connection() as connection:
            return int(
                connection.execute(f"SELECT COUNT(*) FROM jobs {where}", values).fetchone()[0]
            )

    def _insert_event(
        self,
        connection: sqlite3.Connection,
        job_id: str,
        event_type: str,
        message: str,
        metadata: dict[str, Any] | None = None,
        *,
        timestamp: str | None = None,
    ) -> None:
        connection.execute(
            "INSERT INTO job_events VALUES (?, ?, ?, ?, ?, ?)",
            (
                str(uuid.uuid4()),
                job_id,
                timestamp or utc_now(),
                event_type,
                message[:1000],
                _json(metadata or {}),
            ),
        )

    def add_event(
        self, job_id: str, event_type: str, message: str, metadata: dict[str, Any] | None = None
    ) -> None:
        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._require_job(connection, job_id)
            self._insert_event(connection, job_id, event_type, message, metadata)
            connection.commit()

    def events(self, job_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
        with self._lock, self._connection() as connection:
            self._require_job(connection, job_id)
            rows = connection.execute(
                """
                SELECT event_id, job_id, timestamp, event_type, message, metadata
                FROM job_events WHERE job_id=? ORDER BY rowid ASC LIMIT ?
                """,
                (job_id, limit),
            ).fetchall()
        return [
            {
                "event_id": row["event_id"],
                "job_id": row["job_id"],
                "timestamp": row["timestamp"],
                "type": row["event_type"],
                "message": row["message"],
                "metadata": json.loads(row["metadata"]),
            }
            for row in rows
        ]

    def _require_job(self, connection: sqlite3.Connection, job_id: str) -> sqlite3.Row:
        row = connection.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            raise JobNotFoundError(job_id)
        return row

    def transition(
        self,
        job_id: str,
        target: JobState,
        *,
        phase: str | None = None,
        progress_fraction: float | None = None,
        fields: dict[str, Any] | None = None,
        event_type: str | None = None,
        event_message: str | None = None,
        event_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Atomically apply one legal state transition."""

        fields = fields or {}
        allowed_fields = {
            "exit_status",
            "error_code",
            "error_message",
            "error_details",
            "last_heartbeat",
        }
        forbidden = sorted(set(fields) - allowed_fields)
        if forbidden:
            raise RegistryError(f"transition field update is not allowed for: {forbidden}")
        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = self._require_job(connection, job_id)
            current = str(row["state"])
            if target not in LEGAL_TRANSITIONS[current]:
                connection.rollback()
                raise InvalidJobTransitionError(f"{current} -> {target} is not a legal transition")
            updates: dict[str, Any] = {"state": target}
            if phase is not None:
                updates["phase"] = phase
            if progress_fraction is not None:
                updates["progress_fraction"] = progress_fraction
            updates.update(fields)
            if target in {"SUCCEEDED", "FAILED", "CANCELLED", "INTERRUPTED"}:
                updates["finished_at"] = utc_now()
                updates["worker_pid"] = None
            assignments = ", ".join(f"{key}=?" for key in updates)
            connection.execute(
                f"UPDATE jobs SET {assignments} WHERE job_id=?",
                [*updates.values(), job_id],
            )
            self._insert_event(
                connection,
                job_id,
                event_type or f"job_{target.lower()}",
                event_message or f"Job state changed to {target}",
                event_metadata,
            )
            connection.commit()
            result = connection.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if result is None:  # pragma: no cover
                raise RegistryError("job disappeared during transition")
            return _decode(result)

    def update_fields(self, job_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "phase",
            "progress_fraction",
            "worker_pid",
            "last_heartbeat",
        }
        forbidden = sorted(set(fields) - allowed)
        if forbidden:
            raise RegistryError(f"operational field update is not allowed for: {forbidden}")
        if not fields:
            return self.get_job(job_id)
        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._require_job(connection, job_id)
            assignments = ", ".join(f"{key}=?" for key in fields)
            connection.execute(
                f"UPDATE jobs SET {assignments} WHERE job_id=?", [*fields.values(), job_id]
            )
            connection.commit()
            row = connection.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if row is None:  # pragma: no cover
            raise JobNotFoundError(job_id)
        return _decode(row)

    def set_worker_observed_identity_once(
        self,
        job_id: str,
        *,
        engine_commit: str,
        dirty_worktree_flag: bool,
    ) -> dict[str, Any]:
        """Atomically persist one worker observation, allowing identical replay only."""

        if not engine_commit or not isinstance(dirty_worktree_flag, bool):
            raise RegistryError("worker-observed engine identity is incomplete")
        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = self._require_job(connection, job_id)
            observed_commit = row["worker_observed_engine_commit"]
            observed_dirty = row["worker_observed_dirty_worktree_flag"]
            if observed_commit is not None or observed_dirty is not None:
                if observed_commit == engine_commit and bool(observed_dirty) is dirty_worktree_flag:
                    connection.commit()
                    return _decode(row)
                connection.rollback()
                raise RegistryError("worker-observed engine identity is already immutable")
            if row["state"] != "RUNNING":
                connection.rollback()
                raise RegistryError("worker identity may only be observed for a RUNNING job")
            connection.execute(
                """
                UPDATE jobs
                SET worker_observed_engine_commit=?, worker_observed_dirty_worktree_flag=?
                WHERE job_id=? AND worker_observed_engine_commit IS NULL
                    AND worker_observed_dirty_worktree_flag IS NULL
                """,
                (engine_commit, int(dirty_worktree_flag), job_id),
            )
            if connection.execute("SELECT changes()").fetchone()[0] != 1:
                connection.rollback()
                raise RegistryError("worker-observed engine identity was written concurrently")
            connection.commit()
            result = connection.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if result is None:  # pragma: no cover
            raise JobNotFoundError(job_id)
        return _decode(result)

    def claim_next_queued(self) -> dict[str, Any] | None:
        """Claim exactly one FIFO job under a write transaction."""

        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM jobs WHERE state='QUEUED' ORDER BY created_at ASC, job_id ASC "
                "LIMIT 1"
            ).fetchone()
            if row is None:
                connection.commit()
                return None
            job_id = row["job_id"]
            started_at = utc_now()
            connection.execute(
                """
                UPDATE jobs SET state='RUNNING', phase='preparing', started_at=?,
                    last_heartbeat=? WHERE job_id=? AND state='QUEUED'
                """,
                (started_at, started_at, job_id),
            )
            if connection.execute("SELECT changes()").fetchone()[0] != 1:
                connection.rollback()
                return None
            self._insert_event(
                connection,
                job_id,
                "job_started",
                "Job claimed by the local scheduler",
                {"phase": "preparing"},
                timestamp=started_at,
            )
            connection.commit()
            claimed = connection.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        return None if claimed is None else _decode(claimed)

    def request_cancel(self, job_id: str) -> tuple[dict[str, Any], str]:
        """Request cancellation and return ``(job, action)``."""

        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = self._require_job(connection, job_id)
            state = str(row["state"])
            if state == "QUEUED":
                target = "CANCELLED"
                connection.execute(
                    "UPDATE jobs SET state=?, phase=?, finished_at=?, worker_pid=NULL "
                    "WHERE job_id=?",
                    (target, "cancelled", utc_now(), job_id),
                )
                self._insert_event(connection, job_id, "job_cancelled", "Queued job cancelled")
                action = "cancelled"
            elif state == "RUNNING":
                connection.execute(
                    "UPDATE jobs SET state=?, phase=? WHERE job_id=?",
                    ("CANCEL_REQUESTED", "running", job_id),
                )
                self._insert_event(
                    connection,
                    job_id,
                    "cancel_requested",
                    "Cancellation requested for running worker",
                )
                action = "requested"
            elif state in {"CANCEL_REQUESTED", "CANCELLED"}:
                action = "already_cancelled"
            else:
                connection.rollback()
                raise InvalidJobTransitionError(f"cannot cancel job in state {state}")
            connection.commit()
            updated = connection.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if updated is None:  # pragma: no cover
            raise JobNotFoundError(job_id)
        return _decode(updated), action

    def finalize_success(
        self,
        job_id: str,
        *,
        fields: dict[str, Any],
        artifacts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Atomically publish verified artifacts, events, and SUCCEEDED.

        This is the registry's only successful-terminal transition.  Repeating
        the same completed finalization is idempotent and emits no events.
        """

        required = {
            "finished_at",
            "result_manifest_path",
            "result_manifest_hash",
            "verification_status",
        }
        allowed = required | {
            "scenario_hash",
            "latent_hash",
            "bundle_hash",
            "last_heartbeat",
        }
        missing = sorted(required - fields.keys())
        forbidden = sorted(set(fields) - allowed)
        if forbidden:
            raise RegistryError(
                f"successful finalization field update is not allowed for: {forbidden}"
            )
        if missing or fields.get("verification_status") != "passed":
            raise RegistryError(f"verified success fields are incomplete: {missing}")
        if not artifacts:
            raise RegistryError("verified success requires at least one scientific artifact")
        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = self._require_job(connection, job_id)
            if row["state"] == "SUCCEEDED":
                if row["result_manifest_hash"] == fields["result_manifest_hash"]:
                    connection.commit()
                    current = connection.execute(
                        "SELECT * FROM jobs WHERE job_id=?", (job_id,)
                    ).fetchone()
                    if current is None:  # pragma: no cover
                        raise RegistryError("job disappeared during finalization")
                    return _decode(current)
                connection.rollback()
                raise InvalidJobTransitionError(
                    "completed job cannot be finalized with a different result"
                )
            if row["state"] != "RUNNING":
                connection.rollback()
                raise InvalidJobTransitionError(
                    f"{row['state']} -> SUCCEEDED is not a legal finalization"
                )
            if (
                row["submitted_engine_commit"] is None
                or row["submitted_dirty_worktree_flag"] is None
                or row["worker_observed_engine_commit"] is None
                or row["worker_observed_dirty_worktree_flag"] is None
                or row["submitted_engine_commit"] != row["worker_observed_engine_commit"]
                or bool(row["submitted_dirty_worktree_flag"])
                is not bool(row["worker_observed_dirty_worktree_flag"])
            ):
                connection.rollback()
                raise RegistryError("immutable submitted and worker engine identities do not match")
            connection.execute("DELETE FROM job_artifacts WHERE job_id=?", (job_id,))
            for artifact in artifacts:
                connection.execute(
                    """
                    INSERT INTO job_artifacts
                    (job_id, role, artifact_type, scientific_artifact_id, manifest_path, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_id,
                        artifact["role"],
                        artifact["artifact_type"],
                        artifact["artifact_id"],
                        artifact["manifest_path"],
                        _json(artifact),
                    ),
                )
                self._insert_event(
                    connection,
                    job_id,
                    "artifact_written",
                    "Scientific artifact is present on disk",
                    {"artifact_id": artifact["artifact_id"], "role": artifact["role"]},
                )
                self._insert_event(
                    connection,
                    job_id,
                    "artifact_verified",
                    "Scientific artifact passed content-aware verification",
                    {"artifact_id": artifact["artifact_id"], "role": artifact["role"]},
                )
            updates = {
                "state": "SUCCEEDED",
                "phase": "complete",
                "progress_fraction": None,
                "worker_pid": None,
                "exit_status": 0,
                "engine_git_commit": row["submitted_engine_commit"],
                "dirty_worktree_flag": row["submitted_dirty_worktree_flag"],
                **fields,
            }
            assignments = ", ".join(f"{key}=?" for key in updates)
            connection.execute(
                f"UPDATE jobs SET {assignments} WHERE job_id=? AND state='RUNNING'",
                [*updates.values(), job_id],
            )
            if connection.execute("SELECT changes()").fetchone()[0] != 1:
                connection.rollback()
                raise InvalidJobTransitionError("job state changed during successful finalization")
            self._insert_event(
                connection,
                job_id,
                "job_completed",
                "Job completed after result-manifest and scientific verification",
                {"result_manifest_hash": fields["result_manifest_hash"]},
            )
            connection.commit()
            current = connection.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if current is None:  # pragma: no cover
            raise RegistryError("job disappeared during finalization")
        return _decode(current)

    def artifacts(self, job_id: str) -> list[dict[str, Any]]:
        with self._lock, self._connection() as connection:
            self._require_job(connection, job_id)
            rows = connection.execute(
                "SELECT metadata FROM job_artifacts WHERE job_id=? ORDER BY artifact_id ASC",
                (job_id,),
            ).fetchall()
        return [json.loads(row["metadata"]) for row in rows]

    def reconcile_stale_jobs(
        self, *, failures: dict[str, dict[str, str]] | None = None
    ) -> list[str]:
        """Mark every remaining active job terminal after finalization attempts."""

        failures = failures or {}
        reconciled: list[str] = []
        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                "SELECT job_id, state FROM jobs WHERE state IN ('RUNNING', 'CANCEL_REQUESTED')"
            ).fetchall()
            for row in rows:
                job_id = str(row["job_id"])
                target = "CANCELLED" if row["state"] == "CANCEL_REQUESTED" else "INTERRUPTED"
                phase = "cancelled" if target == "CANCELLED" else "interrupted"
                failure = failures.get(job_id, {}) if target == "INTERRUPTED" else {}
                error_code = (
                    failure.get("error_code", "worker_interrupted")
                    if target == "INTERRUPTED"
                    else None
                )
                error_message = (
                    failure.get("error_message", "Active worker was not manageable after restart")
                    if target == "INTERRUPTED"
                    else None
                )
                connection.execute(
                    "UPDATE jobs SET state=?, phase=?, finished_at=?, worker_pid=NULL, "
                    "error_code=?, error_message=? "
                    "WHERE job_id=?",
                    (
                        target,
                        phase,
                        utc_now(),
                        error_code,
                        error_message,
                        job_id,
                    ),
                )
                self._insert_event(
                    connection,
                    job_id,
                    "job_interrupted" if target == "INTERRUPTED" else "job_cancelled",
                    "Active job reconciled after API restart",
                    {"error_code": error_code} if error_code else None,
                )
                reconciled.append(job_id)
            connection.commit()
        return reconciled

    def request_hash(self, canonical_request: dict[str, Any]) -> str:
        """Expose the registry's canonical hash helper for callers/tests."""

        return sha256_bytes(canonical_json_bytes(canonical_request))
