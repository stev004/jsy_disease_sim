"""Persistent FIFO scheduling and process isolation for M9 jobs."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

if os.name == "posix":
    import fcntl

    msvcrt = None
else:  # pragma: no cover - Windows is not the verification host
    fcntl = None
    try:
        import msvcrt
    except ImportError:
        msvcrt = None

from .api_schemas import API_SCHEMA_VERSION
from .execution_adapter import (
    canonical_request_envelope,
    observed_engine_identity,
    validate_job_request,
)
from .hashing import canonical_json_bytes, sha256_bytes
from .job_finalizer import FinalizationError, JobFinalizer
from .job_registry import InvalidJobTransitionError, JobNotFoundError, JobRegistry


class JobSubmissionError(RuntimeError):
    """Raised when a request cannot be persisted as a job."""


class SchedulerLockError(RuntimeError):
    """Raised when another scheduler owns the state directory."""

    def __init__(self, holder_pid: int | None) -> None:
        self.holder_pid = holder_pid
        holder = f" pid {holder_pid}" if holder_pid is not None else ""
        super().__init__(f"scheduler lock is already held{holder}")


class _ProcessHandle(Protocol):
    pid: int

    def poll(self) -> int | None: ...

    def wait(self, timeout: float | None = None) -> int: ...


class _AdoptedProcess:
    """Minimal process handle for a worker inherited across an API restart."""

    def __init__(self, pid: int) -> None:
        self.pid = pid

    def poll(self) -> int | None:
        try:
            os.kill(self.pid, 0)
        except PermissionError:
            return None
        except OSError:
            return 1
        return None

    def wait(self, timeout: float | None = None) -> int:
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            return_code = self.poll()
            if return_code is not None:
                return return_code
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(self.pid, timeout)
                time.sleep(min(0.05, remaining))
            else:
                time.sleep(0.05)


def default_state_dir() -> Path:
    """Return a durable per-user directory outside the Git worktree."""

    override = os.environ.get("JOS_STATE_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "darwin":
        return (
            Path.home() / "Library" / "Application Support" / "JerseyOutbreakSimulator"
        ).resolve()
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return (root / "JerseyOutbreakSimulator").resolve()
    return (
        Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
        / "jersey-outbreak-simulator"
    ).resolve()


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except OSError:
        return False
    return True


class JobManager:
    """Own the local scheduler and API-created worker subprocesses."""

    def __init__(
        self,
        *,
        state_dir: Path | None = None,
        project_root: Path | None = None,
        max_concurrent_jobs: int = 1,
        poll_interval: float = 0.05,
    ) -> None:
        if max_concurrent_jobs < 1:
            raise ValueError("max_concurrent_jobs must be at least one")
        self.state_dir = (state_dir or default_state_dir()).resolve()
        self.project_root = (project_root or Path(__file__).resolve().parents[2]).resolve()
        self.max_concurrent_jobs = max_concurrent_jobs
        self.poll_interval = poll_interval
        self.jobs_dir = self.state_dir / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.registry = JobRegistry(self.state_dir / "jobs.sqlite")
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._processes: dict[str, _ProcessHandle] = {}
        self._process_lock = threading.RLock()
        self._scheduler_lock_path = self.state_dir / "scheduler.lock"
        self._scheduler_lock_handle: Any | None = None
        self._scheduler_lock_kind: str | None = None
        self._started = False

    def _job_dir(self, job_id: str) -> Path:
        return (self.jobs_dir / job_id).resolve()

    @staticmethod
    def _lock_holder_pid(handle: Any) -> int | None:
        try:
            handle.seek(0)
            first_line = handle.readline().strip()
            return int(first_line)
        except (OSError, TypeError, ValueError):
            return None

    def _acquire_scheduler_lock(self) -> None:
        if self._scheduler_lock_handle is not None:
            return
        handle: Any | None = None
        lock_kind: str | None = None
        try:
            if os.name == "posix":
                handle = self._scheduler_lock_path.open("a+", encoding="utf-8")
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                lock_kind = "flock"
            elif msvcrt is not None:  # pragma: no cover - Windows is not verification host
                handle = self._scheduler_lock_path.open("a+", encoding="utf-8")
                if self._scheduler_lock_path.stat().st_size == 0:
                    handle.write("\n")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                lock_kind = "msvcrt"
            else:  # pragma: no cover - Windows is not verification host
                descriptor = os.open(
                    self._scheduler_lock_path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                )
                handle = os.fdopen(descriptor, "w+", encoding="utf-8")
                lock_kind = "exclusive"
        except FileExistsError as exc:  # pragma: no cover - Windows fallback
            if handle is not None:
                handle.close()
            try:
                holder_text = self._scheduler_lock_path.read_text(encoding="utf-8")
                holder_pid = int(holder_text.splitlines()[0])
            except (OSError, ValueError, IndexError):
                holder_pid = None
            raise SchedulerLockError(holder_pid) from exc
        except OSError as exc:
            holder_pid = self._lock_holder_pid(handle) if handle is not None else None
            if handle is not None:
                handle.close()
            raise SchedulerLockError(holder_pid) from exc

        try:
            handle.seek(0)
            handle.truncate()
            handle.write(f"{os.getpid()}\n{datetime.now(UTC).isoformat()}\n")
            handle.flush()
            os.fsync(handle.fileno())
        except OSError:
            handle.close()
            raise
        self._scheduler_lock_handle = handle
        self._scheduler_lock_kind = lock_kind

    def _release_scheduler_lock(self) -> None:
        handle = self._scheduler_lock_handle
        if handle is None:
            return
        self._scheduler_lock_handle = None
        lock_kind = self._scheduler_lock_kind
        self._scheduler_lock_kind = None
        try:
            if lock_kind == "flock":
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            elif lock_kind == "msvcrt":  # pragma: no cover - Windows is not verification host
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            handle.close()
            if lock_kind == "exclusive":  # pragma: no cover - Windows is not verification host
                try:
                    self._scheduler_lock_path.unlink()
                except FileNotFoundError:
                    pass

    def _worker_is_live(self, job: dict[str, Any]) -> bool:
        worker_pid = job.get("worker_pid")
        if not isinstance(worker_pid, int) or not _pid_is_alive(worker_pid):
            return False
        token_path = self._job_dir(str(job["job_id"])) / "worker.token"
        try:
            token_pid = token_path.read_text(encoding="utf-8").splitlines()[0].strip()
        except (OSError, UnicodeError, IndexError):
            return False
        return token_pid == str(worker_pid)

    def _adopt_worker(self, job: dict[str, Any]) -> None:
        job_id = str(job["job_id"])
        worker_pid = int(job["worker_pid"])
        with self._process_lock:
            process = self._processes.get(job_id)
            if process is not None and process.poll() is None:
                return
            self._processes[job_id] = _AdoptedProcess(worker_pid)
        self.registry.add_event(
            job_id,
            "job_adopted",
            "Live worker adopted after API restart",
            {"worker_pid": worker_pid},
        )

    def _reconcile_startup(self) -> None:
        acquired = self._scheduler_lock_handle is None
        self._acquire_scheduler_lock()
        # The same finalizer used by a live worker is the only restart path to
        # success.  Remaining stale active rows become explicitly terminal.
        try:
            finalizer = JobFinalizer(
                registry=self.registry, state_dir=self.state_dir, project_root=self.project_root
            )
            failures: dict[str, dict[str, str]] = {}
            stale_job_ids: set[str] = set()
            for job in self.registry.list_jobs(limit=10_000):
                job_id = str(job["job_id"])
                if job["state"] == "CANCEL_REQUESTED":
                    stale_job_ids.add(job_id)
                    continue
                if job["state"] != "RUNNING":
                    continue
                if (self._job_dir(job_id) / "result_candidate.json").is_file():
                    try:
                        finalizer.finalize(job_id)
                    except FinalizationError as exc:
                        failures[job_id] = {
                            "error_code": exc.code,
                            "error_message": str(exc)[:1000],
                        }
                    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
                        failures[job_id] = {
                            "error_code": "restart_finalization_failed",
                            "error_message": f"Restart finalization failed: {type(exc).__name__}",
                        }
                    if job_id in failures:
                        stale_job_ids.add(job_id)
                elif self._worker_is_live(job):
                    self._adopt_worker(job)
                else:
                    stale_job_ids.add(job_id)
            self.registry.reconcile_stale_jobs(failures=failures, only=stale_job_ids)
        except BaseException:
            if acquired:
                self._release_scheduler_lock()
            raise

    def start(self) -> None:
        if self._started:
            return
        try:
            self._reconcile_startup()
            self._stop.clear()
            self._started = True
            self._thread = threading.Thread(
                target=self._run_loop, name="jos-job-scheduler", daemon=True
            )
            self._thread.start()
        except BaseException:
            self._started = False
            self._release_scheduler_lock()
            raise

    def submit(self, request: Any, *, idempotency_key: str | None = None) -> dict[str, Any]:
        """Validate, canonicalize and persist a request before returning."""

        try:
            validated = validate_job_request(request, self.project_root)
        except Exception as exc:
            raise JobSubmissionError(f"request validation failed: {exc}") from exc
        payload = validated.model_dump(mode="json")
        identity = observed_engine_identity(self.project_root)
        submitted_commit = identity.get("engine_git_commit")
        submitted_dirty = identity.get("dirty_worktree_flag")
        if not submitted_commit or not isinstance(submitted_dirty, bool):
            raise JobSubmissionError("submission engine identity is unavailable")
        envelope = canonical_request_envelope(validated, identity)
        request_hash = sha256_bytes(canonical_json_bytes(envelope))
        job, existed = self.registry.create_job(
            job_kind=str(payload["kind"]),
            canonical_request=envelope,
            request_hash=request_hash,
            submitted_engine_commit=str(submitted_commit),
            submitted_dirty_worktree_flag=submitted_dirty,
            idempotency_key=idempotency_key,
        )
        job_dir = self._job_dir(job["job_id"])
        if not existed:
            try:
                job_dir.mkdir(parents=True, exist_ok=False)
                _atomic_json(
                    job_dir / "request.json",
                    {
                        **envelope,
                        "request_hash": request_hash,
                    },
                )
                _atomic_json(
                    job_dir / "worker_metadata.json", {"api_schema_version": API_SCHEMA_VERSION}
                )
            except OSError as exc:
                # A persisted job without its canonical request cannot safely
                # run.  Queue cancellation is the only legal terminal move.
                try:
                    self.registry.request_cancel(job["job_id"])
                except Exception:
                    pass
                raise JobSubmissionError("job request could not be persisted") from exc
        result = self.registry.get_job(job["job_id"])
        result["_already_exists"] = existed
        return result

    def get(self, job_id: str) -> dict[str, Any]:
        return self.registry.get_job(job_id)

    def list_jobs(
        self, *, state: str | None = None, kind: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        return (
            self.registry.list_jobs(state=state, kind=kind, limit=limit, offset=offset),
            self.registry.count_jobs(state=state, kind=kind),
        )

    def events(self, job_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
        return self.registry.events(job_id, limit=limit)

    def artifacts(self, job_id: str) -> list[dict[str, Any]]:
        return self.registry.artifacts(job_id)

    def cancel(self, job_id: str) -> tuple[dict[str, Any], str]:
        result = self.registry.request_cancel(job_id)
        if result[1] == "requested":
            self._terminate_process(job_id)
        return result

    def _spawn(self, job: dict[str, Any]) -> None:
        job_id = str(job["job_id"])
        job_dir = self._job_dir(job_id)
        logs_dir = job_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = logs_dir / "worker.stdout.log"
        stderr_path = logs_dir / "worker.stderr.log"
        command = [
            sys.executable,
            "-m",
            "jersey_outbreak.job_worker",
            "--job-id",
            job_id,
            "--state-dir",
            str(self.state_dir),
            "--project-root",
            str(self.project_root),
        ]
        with stdout_path.open("ab") as stdout, stderr_path.open("ab") as stderr:
            process = subprocess.Popen(
                command,
                cwd=self.project_root,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                start_new_session=(os.name == "posix"),
                shell=False,
            )
        _atomic_text(
            job_dir / "worker.token",
            f"{process.pid}\n{datetime.now(UTC).isoformat()}\n",
        )
        with self._process_lock:
            self._processes[job_id] = process
        self.registry.update_fields(
            job_id,
            {"worker_pid": process.pid, "last_heartbeat": datetime.now(UTC).isoformat()},
        )

    def _terminate_process(self, job_id: str) -> None:
        with self._process_lock:
            process = self._processes.get(job_id)
        if process is None or process.poll() is not None:
            return
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGTERM)
            else:  # pragma: no cover - Windows is not the verification host
                process.terminate()
            try:
                process.wait(timeout=0.75)
            except subprocess.TimeoutExpired:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
                process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            pass

    def _reap(self) -> None:
        with self._process_lock:
            items = list(self._processes.items())
        for job_id, process in items:
            return_code = process.poll()
            if return_code is None:
                try:
                    self.registry.update_fields(
                        job_id, {"last_heartbeat": datetime.now(UTC).isoformat()}
                    )
                except JobNotFoundError:
                    pass
                continue
            with self._process_lock:
                self._processes.pop(job_id, None)
            self._bound_logs(job_id)
            try:
                job = self.registry.get_job(job_id)
                if job["state"] == "CANCEL_REQUESTED":
                    self.registry.transition(
                        job_id,
                        "CANCELLED",
                        phase="cancelled",
                        event_type="job_cancelled",
                        event_message="Worker terminated after cancellation request",
                    )
                elif job["state"] == "RUNNING":
                    self.registry.transition(
                        job_id,
                        "FAILED",
                        phase="failed",
                        fields={
                            "exit_status": return_code,
                            "error_code": "worker_no_completion"
                            if return_code == 0
                            else "worker_process_failed",
                            "error_message": "Worker exited without a verified result"
                            if return_code == 0
                            else "Worker process exited before completing the job",
                        },
                        event_type="job_failed",
                        event_message="Worker exited without a verified successful result",
                    )
            except (JobNotFoundError, InvalidJobTransitionError):
                pass

    def _bound_logs(self, job_id: str, *, maximum_bytes: int = 1_048_576) -> None:
        """Keep only a bounded diagnostic tail for each completed worker."""

        for name in ("worker.stdout.log", "worker.stderr.log"):
            path = self._job_dir(job_id) / "logs" / name
            try:
                if path.stat().st_size > maximum_bytes:
                    with path.open("rb") as handle:
                        handle.seek(-maximum_bytes, os.SEEK_END)
                        tail = handle.read()
                    path.write_bytes(b"[log truncated to final 1 MiB]\n" + tail)
            except OSError:
                pass

    def _run_loop(self) -> None:
        while not self._stop.is_set():
            self._reap()
            with self._process_lock:
                active = len(self._processes)
                cancelling = [job_id for job_id in self._processes]
            for job_id in cancelling:
                try:
                    if self.registry.get_job(job_id)["state"] == "CANCEL_REQUESTED":
                        self._terminate_process(job_id)
                except JobNotFoundError:
                    continue
            while active < self.max_concurrent_jobs and not self._stop.is_set():
                job = self.registry.claim_next_queued()
                if job is None:
                    break
                try:
                    self._spawn(job)
                except Exception as exc:
                    try:
                        self.registry.transition(
                            job["job_id"],
                            "FAILED",
                            phase="failed",
                            fields={
                                "error_code": "worker_spawn_failed",
                                "error_message": "The worker process could not be started",
                            },
                            event_type="job_failed",
                            event_message="Worker process could not be started",
                            event_metadata={"exception_type": type(exc).__name__},
                        )
                    except InvalidJobTransitionError:
                        pass
                else:
                    active += 1
            self._stop.wait(self.poll_interval)

    def close(self) -> None:
        if not self._started:
            self._release_scheduler_lock()
            return
        try:
            self._stop.set()
            if self._thread is not None:
                self._thread.join(timeout=3)
            with self._process_lock:
                active = list(self._processes)
            for job_id in active:
                self._terminate_process(job_id)
            with self._process_lock:
                self._processes.clear()
            for job in self.registry.list_jobs(limit=10_000):
                if job["state"] == "RUNNING":
                    try:
                        self.registry.transition(
                            job["job_id"],
                            "INTERRUPTED",
                            phase="interrupted",
                            event_type="job_interrupted",
                            event_message="Active worker interrupted by API shutdown",
                        )
                    except InvalidJobTransitionError:
                        pass
                elif job["state"] == "CANCEL_REQUESTED":
                    try:
                        self.registry.transition(
                            job["job_id"],
                            "CANCELLED",
                            phase="cancelled",
                            event_type="job_cancelled",
                            event_message="Cancellation finalized during API shutdown",
                        )
                    except InvalidJobTransitionError:
                        pass
        finally:
            self._started = False
            self._release_scheduler_lock()

    def stop(self) -> None:
        """Stop the scheduler and release its state-directory lock."""

        self.close()
