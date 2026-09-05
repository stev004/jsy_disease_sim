"""Regression coverage for scheduler ownership and restart liveness."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from jersey_outbreak.api_schemas import ScenarioRunRequest
from jersey_outbreak.job_manager import JobManager, SchedulerLockError

ROOT = Path(__file__).resolve().parents[1]


def _claim_job(manager: JobManager) -> str:
    job = manager.submit(ScenarioRunRequest(kind="scenario_run", duration_days=1))
    claimed = manager.registry.claim_next_queued()
    assert claimed is not None and claimed["job_id"] == job["job_id"]
    return str(job["job_id"])


def test_startup_reconciliation_adopts_live_worker(tmp_path: Path) -> None:
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    job_id = _claim_job(manager)
    fake_worker = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        start_new_session=(os.name == "posix"),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    restarted = JobManager(state_dir=tmp_path, project_root=ROOT)
    try:
        manager.registry.update_fields(job_id, {"worker_pid": fake_worker.pid})
        (manager._job_dir(job_id) / "worker.token").write_text(
            f"{fake_worker.pid}\n{datetime.now(UTC).isoformat()}\n", encoding="utf-8"
        )
        restarted._reconcile_startup()
        assert restarted.registry.get_job(job_id)["state"] == "RUNNING"
        assert any(event["type"] == "job_adopted" for event in restarted.events(job_id))

        fake_worker.kill()
        fake_worker.wait()
        restarted._reconcile_startup()
        assert restarted.registry.get_job(job_id)["state"] == "INTERRUPTED"
    finally:
        if fake_worker.poll() is None:
            fake_worker.kill()
            fake_worker.wait()
        restarted.close()


def test_second_manager_on_same_state_dir_is_refused(tmp_path: Path) -> None:
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    second = JobManager(state_dir=tmp_path, project_root=ROOT)
    manager.start()
    try:
        with pytest.raises(SchedulerLockError) as error:
            second.start()
        assert error.value.holder_pid == os.getpid()
        manager.stop()
        second.start()
    finally:
        manager.close()
        second.close()


def test_stale_pid_without_token_is_interrupted(tmp_path: Path) -> None:
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    job_id = _claim_job(manager)
    stale_worker = subprocess.Popen(
        [sys.executable, "-c", "pass"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    stale_worker.wait()
    manager.registry.update_fields(job_id, {"worker_pid": stale_worker.pid})
    try:
        manager._reconcile_startup()
        assert manager.registry.get_job(job_id)["state"] == "INTERRUPTED"
    finally:
        manager.close()


def test_frozen_snapshots_are_marked_no_eol_conversion() -> None:
    snapshot_paths = sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "data/raw").rglob("*")
        if path.is_file()
    )
    try:
        result = subprocess.run(
            ["git", "check-attr", "text", "--", *snapshot_paths],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        pytest.skip("git is unavailable")
    results = result.stdout.splitlines()
    assert len(results) == len(snapshot_paths)
    assert all(line.endswith(" text: unset") for line in results)
