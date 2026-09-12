"""Regression tests for job submission, publication, and heartbeat ordering."""

from __future__ import annotations

import json
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from jersey_outbreak import job_manager as job_manager_module
from jersey_outbreak.api_schemas import APIResultCandidate, CandidateArtifact, ScenarioRunRequest
from jersey_outbreak.job_finalizer import JobFinalizer
from jersey_outbreak.job_manager import JobManager, _atomic_json
from jersey_outbreak.job_registry import InvalidJobTransitionError
from jersey_outbreak.outbreak_artifacts import write_outbreak_artifact

ROOT = Path(__file__).resolve().parents[1]


def _candidate_for(manager: JobManager, job_id: str, manifest_path: Path) -> None:
    job = manager.registry.get_job(job_id)
    manager.registry.set_worker_observed_identity_once(
        job_id,
        engine_commit=job["submitted_engine_commit"],
        dirty_worktree_flag=bool(job["submitted_dirty_worktree_flag"]),
    )
    candidate = APIResultCandidate(
        job_id=job_id,
        job_kind=job["job_kind"],
        request_hash=job["request_hash"],
        started_at=job["started_at"],
        finished_at="2026-08-29T12:00:00+00:00",
        engine_git_commit=job["submitted_engine_commit"],
        dirty_worktree_flag=bool(job["submitted_dirty_worktree_flag"]),
        output_artifacts=[
            CandidateArtifact(
                role="scientific_result",
                manifest_path=str(manifest_path.relative_to(manager._job_dir(job_id))),
            )
        ],
    )
    (manager._job_dir(job_id) / "result_candidate.json").write_text(
        json.dumps(candidate.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_submit_persists_request_before_scheduler_can_claim(tmp_path: Path, monkeypatch) -> None:
    manager = JobManager(state_dir=tmp_path, project_root=ROOT, poll_interval=0.01)
    manager.start()
    created = threading.Event()
    spawned = threading.Event()
    submitted: dict[str, Any] = {}
    original_create = manager.registry.create_job
    original_popen = job_manager_module.subprocess.Popen

    def observe_spawn(*args, **kwargs):
        process = original_popen(*args, **kwargs)
        spawned.set()
        return process

    monkeypatch.setattr(job_manager_module.subprocess, "Popen", observe_spawn)

    def delayed_write(path: Path, payload: object) -> None:
        if path.name == "request.json":
            if spawned.wait(timeout=0.2):
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    try:
                        if manager.get(path.parent.name)["state"] in {
                            "FAILED",
                            "CANCELLED",
                            "INTERRUPTED",
                            "SUCCEEDED",
                        }:
                            break
                    except Exception:
                        pass
                    time.sleep(0.005)
        _atomic_json(path, payload)

    monkeypatch.setattr("jersey_outbreak.job_manager._atomic_json", delayed_write)

    def observe_create(*args, **kwargs):
        result = original_create(*args, **kwargs)
        submitted["job"] = result[0]
        created.set()
        return result

    monkeypatch.setattr(manager.registry, "create_job", observe_create)

    def submit() -> None:
        try:
            submitted["result"] = manager.submit(
                ScenarioRunRequest(kind="scenario_run", mode="ci", seed=123, duration_days=1)
            )
        except BaseException as exc:  # pragma: no cover - included in assertion below
            submitted["error"] = exc

    submit_thread = threading.Thread(target=submit)
    submit_thread.start()
    try:
        assert created.wait(10)
        job_id = submitted["job"]["job_id"]
        request_path = manager._job_dir(job_id) / "request.json"
        inverted = False
        deadline = time.monotonic() + 0.3
        while time.monotonic() < deadline:
            if manager.get(job_id)["state"] == "RUNNING" and not request_path.exists():
                inverted = True
                break
            time.sleep(0.005)
        submit_thread.join(timeout=30)
        assert not submit_thread.is_alive()
        assert "error" not in submitted, submitted.get("error")
        submitted_job = submitted["result"]
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            job = manager.get(submitted_job["job_id"])
            if job["state"] in {"SUCCEEDED", "FAILED", "CANCELLED", "INTERRUPTED"}:
                break
            time.sleep(0.05)
        if inverted:
            assert job["state"] == "FAILED"
            assert job["error_code"] == "worker_execution_failed"
        assert inverted is False, (
            "scheduler claimed before request persistence: "
            f"final state={job['state']}, error={job['error_code']}"
        )
        assert job["state"] == "SUCCEEDED", job
    finally:
        manager.close()


def test_missing_head_request_fails_alone_and_scheduler_continues(
    tmp_path: Path, monkeypatch
) -> None:
    manager = JobManager(state_dir=tmp_path, project_root=ROOT, poll_interval=0.01)
    first = manager.submit(
        ScenarioRunRequest(kind="scenario_run", mode="ci", seed=601, duration_days=1)
    )
    second = manager.submit(
        ScenarioRunRequest(kind="scenario_run", mode="ci", seed=602, duration_days=1)
    )
    first_id = str(first["job_id"])
    second_id = str(second["job_id"])
    (manager._job_dir(first_id) / "request.json").unlink()
    spawned_ids: list[str] = []
    original_popen = job_manager_module.subprocess.Popen

    def observe_spawn(*args, **kwargs):
        command = args[0]
        job_id = command[command.index("--job-id") + 1]
        spawned_ids.append(job_id)
        return original_popen(*args, **kwargs)

    monkeypatch.setattr(job_manager_module.subprocess, "Popen", observe_spawn)
    manager.start()
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            states = {manager.get(first_id)["state"], manager.get(second_id)["state"]}
            if states <= {"FAILED", "CANCELLED", "INTERRUPTED", "SUCCEEDED"}:
                break
            time.sleep(0.01)
        first_job = manager.get(first_id)
        second_job = manager.get(second_id)
        assert first_job["state"] == "FAILED", first_job
        assert first_job["error_code"] == "request_not_persisted"
        assert any(event["type"] == "job_failed" for event in manager.events(first_id))
        assert first_id not in spawned_ids
        assert second_job["state"] == "SUCCEEDED", second_job
        assert second_id in spawned_ids
    finally:
        manager.close()


def test_result_manifest_is_not_published_before_registry_success(
    tmp_path: Path, m6_latent_run, monkeypatch
) -> None:
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    job = manager.submit(ScenarioRunRequest(kind="scenario_run", duration_days=8))
    job_id = job["job_id"]
    manager.registry.claim_next_queued()
    artifact = write_outbreak_artifact(m6_latent_run, ROOT, manager._job_dir(job_id) / "artifacts")
    _candidate_for(manager, job_id, artifact.artifact_directory / "manifest.json")

    original_finalize = manager.registry.finalize_success

    def cancel_before_registry_transition(*args, **kwargs):
        manager.registry.request_cancel(job_id)
        return original_finalize(*args, **kwargs)

    monkeypatch.setattr(manager.registry, "finalize_success", cancel_before_registry_transition)
    with pytest.raises(InvalidJobTransitionError):
        JobFinalizer(registry=manager.registry, state_dir=tmp_path, project_root=ROOT).finalize(
            job_id
        )

    job_directory = manager._job_dir(job_id)
    assert not (job_directory / "result_manifest.json").exists()
    assert not list(job_directory.glob(".result_manifest.json.*.staged"))
    assert manager.registry.get_job(job_id)["state"] == "CANCEL_REQUESTED"


class _AliveProcess:
    pid = 999_999_991

    def poll(self) -> None:
        return None

    def wait(self, timeout: float | None = None) -> int:
        raise AssertionError("the fake process should not be waited on")


def test_supervisor_does_not_refresh_worker_heartbeat(tmp_path: Path) -> None:
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    job = manager.submit(ScenarioRunRequest(kind="scenario_run", duration_days=1))
    job_id = job["job_id"]
    manager.registry.claim_next_queued()
    old_heartbeat = (datetime.now(UTC) - timedelta(seconds=30)).isoformat()
    manager.registry.update_fields(job_id, {"last_heartbeat": old_heartbeat})
    manager._processes[job_id] = _AliveProcess()

    manager._reap()

    assert manager.registry.get_job(job_id)["last_heartbeat"] == old_heartbeat


def test_explicit_heartbeat_stall_policy_interrupts_stalled_worker(
    tmp_path: Path, monkeypatch
) -> None:
    manager = JobManager(
        state_dir=tmp_path,
        project_root=ROOT,
        heartbeat_stall_timeout=1.0,
    )
    job = manager.submit(ScenarioRunRequest(kind="scenario_run", duration_days=1))
    job_id = job["job_id"]
    manager.registry.claim_next_queued()
    old_heartbeat = (datetime.now(UTC) - timedelta(seconds=30)).isoformat()
    manager.registry.update_fields(job_id, {"last_heartbeat": old_heartbeat})
    manager._processes[job_id] = _AliveProcess()
    monkeypatch.setattr(manager, "_terminate_process", lambda _job_id: None)

    manager._reap()

    stalled = manager.registry.get_job(job_id)
    assert stalled["state"] == "INTERRUPTED"
    assert stalled["error_code"] == "worker_stalled"
    assert stalled["last_heartbeat"] == old_heartbeat
