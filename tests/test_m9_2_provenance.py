"""Focused M9.2 immutable execution-provenance regression tests."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

import pytest

from jersey_outbreak.api_schemas import APIResultCandidate, CandidateArtifact, ScenarioRunRequest
from jersey_outbreak.execution_adapter import (
    canonical_request_envelope,
)
from jersey_outbreak.hashing import canonical_json_bytes, sha256_bytes
from jersey_outbreak.job_finalizer import FinalizationError, JobFinalizer
from jersey_outbreak.job_manager import JobManager
from jersey_outbreak.job_registry import JobRegistry, RegistryError
from jersey_outbreak.job_worker import run_worker
from jersey_outbreak.outbreak_artifacts import write_outbreak_artifact

ROOT = Path(__file__).resolve().parents[1]
ANCHOR_COMMIT = "a" * 40
SUBSTITUTE_COMMIT = "f" * 40


def _identity(commit: str, dirty: bool) -> dict[str, object]:
    return {
        "engine_git_commit": commit,
        "dirty_worktree_flag": dirty,
        "python_version": "test",
        "starsim_version": "test",
    }


def _candidate(
    manager: JobManager,
    job_id: str,
    manifest_path: Path,
    *,
    commit: str,
    dirty: bool,
) -> None:
    job = manager.registry.get_job(job_id)
    payload = APIResultCandidate(
        job_id=job_id,
        job_kind=job["job_kind"],
        request_hash=job["request_hash"],
        started_at=job["started_at"],
        finished_at="2026-08-29T12:00:00+00:00",
        engine_git_commit=commit,
        dirty_worktree_flag=dirty,
        output_artifacts=[
            CandidateArtifact(
                role="scientific_result",
                manifest_path=str(manifest_path.relative_to(manager._job_dir(job_id))),
            )
        ],
    )
    (manager._job_dir(job_id) / "result_candidate.json").write_text(
        json.dumps(payload.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _anchored_restart_fixture(
    tmp_path: Path, m6_latent_run
) -> tuple[JobManager, str, Path, str, bool]:
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    job = manager.submit(ScenarioRunRequest(kind="scenario_run", duration_days=8))
    job_id = job["job_id"]
    manager.registry.claim_next_queued()
    commit = job["submitted_engine_commit"]
    dirty = bool(job["submitted_dirty_worktree_flag"])
    artifact = write_outbreak_artifact(
        m6_latent_run,
        ROOT,
        manager._job_dir(job_id) / "artifacts",
    )
    manifest_path = artifact.artifact_directory / "manifest.json"
    _candidate(manager, job_id, manifest_path, commit=commit, dirty=dirty)
    return manager, job_id, manifest_path, commit, dirty


def test_submission_identity_is_atomic_immutable_and_hash_bound(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "jersey_outbreak.job_manager.observed_engine_identity",
        lambda _root: _identity(ANCHOR_COMMIT, False),
    )
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    job = manager.submit(ScenarioRunRequest(kind="scenario_run", duration_days=1))
    assert job["submitted_engine_commit"] == ANCHOR_COMMIT
    assert job["submitted_dirty_worktree_flag"] == 0
    assert job["worker_observed_engine_commit"] is None
    assert job["worker_observed_dirty_worktree_flag"] is None
    assert manager.registry.request_hash(job["canonical_request"]) == job["request_hash"]
    assert job["canonical_request"]["submitted_engine_identity"] == _identity(ANCHOR_COMMIT, False)
    with pytest.raises(RegistryError, match="not allowed"):
        manager.registry.update_fields(job["job_id"], {"submitted_engine_commit": "b" * 40})
    with pytest.raises(RegistryError, match="not allowed"):
        manager.registry.update_fields(job["job_id"], {"engine_git_commit": "b" * 40})

    request = ScenarioRunRequest(kind="scenario_run", duration_days=1)
    clean = canonical_request_envelope(request, _identity(ANCHOR_COMMIT, False))
    other_commit = canonical_request_envelope(request, _identity("b" * 40, False))
    dirty = canonical_request_envelope(request, _identity(ANCHOR_COMMIT, True))
    assert (
        len(
            {
                manager.registry.request_hash(clean),
                manager.registry.request_hash(other_commit),
                manager.registry.request_hash(dirty),
            }
        )
        == 3
    )


def test_worker_observed_identity_is_atomic_write_once(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "jersey_outbreak.job_manager.observed_engine_identity",
        lambda _root: _identity(ANCHOR_COMMIT, False),
    )
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    job = manager.submit(ScenarioRunRequest(kind="scenario_run", duration_days=1))
    job_id = job["job_id"]
    manager.registry.claim_next_queued()
    connections = [JobRegistry(tmp_path / "jobs.sqlite") for _ in range(2)]
    barrier = threading.Barrier(3)
    outcomes: list[str] = []

    def write(registry: JobRegistry, commit: str) -> None:
        barrier.wait()
        try:
            registry.set_worker_observed_identity_once(
                job_id,
                engine_commit=commit,
                dirty_worktree_flag=False,
            )
        except RegistryError:
            outcomes.append("rejected")
        else:
            outcomes.append(commit)

    threads = [
        threading.Thread(target=write, args=(connections[0], ANCHOR_COMMIT)),
        threading.Thread(target=write, args=(connections[1], SUBSTITUTE_COMMIT)),
    ]
    for thread in threads:
        thread.start()
    barrier.wait()
    for thread in threads:
        thread.join()
    assert outcomes.count("rejected") == 1
    persisted = manager.registry.get_job(job_id)
    winner = persisted["worker_observed_engine_commit"]
    assert winner in {ANCHOR_COMMIT, SUBSTITUTE_COMMIT}
    assert persisted["worker_observed_dirty_worktree_flag"] == 0
    manager.registry.set_worker_observed_identity_once(
        job_id,
        engine_commit=winner,
        dirty_worktree_flag=False,
    )
    loser = SUBSTITUTE_COMMIT if winner == ANCHOR_COMMIT else ANCHOR_COMMIT
    with pytest.raises(RegistryError, match="already immutable"):
        manager.registry.set_worker_observed_identity_once(
            job_id,
            engine_commit=loser,
            dirty_worktree_flag=False,
        )


@pytest.mark.parametrize("mismatch", ["commit", "dirty"])
def test_normal_worker_rejects_observed_submission_mismatch(
    tmp_path: Path, monkeypatch, mismatch: str
) -> None:
    monkeypatch.setattr(
        "jersey_outbreak.job_manager.observed_engine_identity",
        lambda _root: _identity(ANCHOR_COMMIT, False),
    )
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    job = manager.submit(ScenarioRunRequest(kind="scenario_run", duration_days=1))
    job_id = job["job_id"]
    manager.registry.claim_next_queued()
    observed_commit = SUBSTITUTE_COMMIT if mismatch == "commit" else ANCHOR_COMMIT
    observed_dirty = mismatch == "dirty"
    monkeypatch.setattr(
        "jersey_outbreak.job_worker.observed_engine_identity",
        lambda _root: _identity(observed_commit, observed_dirty),
    )
    monkeypatch.setattr(
        "jersey_outbreak.job_worker.execute_job",
        lambda *_args, **_kwargs: pytest.fail("scientific execution must not start"),
    )
    assert run_worker(job_id=job_id, state_dir=tmp_path, project_root=ROOT) == 1
    failed = manager.registry.get_job(job_id)
    assert failed["state"] == "FAILED"
    assert failed["error_code"] == "engine_identity_mismatch"
    assert failed["submitted_engine_commit"] == ANCHOR_COMMIT
    assert failed["worker_observed_engine_commit"] == observed_commit
    assert failed["worker_observed_dirty_worktree_flag"] == int(observed_dirty)


def test_valid_anchored_restart_succeeds_and_manifest_uses_anchor(
    tmp_path: Path, m6_latent_run
) -> None:
    manager, job_id, _manifest_path, commit, dirty = _anchored_restart_fixture(
        tmp_path, m6_latent_run
    )
    manager.registry.set_worker_observed_identity_once(
        job_id,
        engine_commit=commit,
        dirty_worktree_flag=dirty,
    )
    restarted = JobManager(state_dir=tmp_path, project_root=ROOT)
    restarted._reconcile_startup()
    completed = restarted.registry.get_job(job_id)
    result = json.loads(
        (restarted._job_dir(job_id) / "result_manifest.json").read_text(encoding="utf-8")
    )
    assert completed["state"] == "SUCCEEDED"
    assert completed["submitted_engine_commit"] == commit
    assert completed["worker_observed_engine_commit"] == commit
    assert bool(completed["submitted_dirty_worktree_flag"]) is dirty
    assert bool(completed["worker_observed_dirty_worktree_flag"]) is dirty
    assert completed["engine_git_commit"] == result["engine_git_commit"] == commit
    assert bool(completed["dirty_worktree_flag"]) is result["dirty_worktree_flag"] is dirty


@pytest.mark.parametrize("substitution", ["commit", "dirty"])
def test_completed_result_manifest_identity_remains_bound_to_registry(
    tmp_path: Path, m6_latent_run, substitution: str
) -> None:
    manager, job_id, _manifest_path, commit, dirty = _anchored_restart_fixture(
        tmp_path, m6_latent_run
    )
    manager.registry.set_worker_observed_identity_once(
        job_id,
        engine_commit=commit,
        dirty_worktree_flag=dirty,
    )
    manager._reconcile_startup()
    result_path = manager._job_dir(job_id) / "result_manifest.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if substitution == "commit":
        result["engine_git_commit"] = SUBSTITUTE_COMMIT
    else:
        result["dirty_worktree_flag"] = not dirty
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    substituted_hash = sha256_bytes(canonical_json_bytes(result))
    with sqlite3.connect(tmp_path / "jobs.sqlite") as connection:
        connection.execute(
            "UPDATE jobs SET result_manifest_hash=? WHERE job_id=?",
            (substituted_hash, job_id),
        )
    with pytest.raises(FinalizationError) as raised:
        JobFinalizer(registry=manager.registry, state_dir=tmp_path, project_root=ROOT).finalize(
            job_id
        )
    assert raised.value.code == "completed_result_mismatch"
    anchored = manager.registry.get_job(job_id)
    assert anchored["submitted_engine_commit"] == commit
    assert anchored["worker_observed_engine_commit"] == commit
    assert bool(anchored["submitted_dirty_worktree_flag"]) is dirty
    assert bool(anchored["worker_observed_dirty_worktree_flag"]) is dirty


def test_restart_without_worker_observation_cannot_succeed(tmp_path: Path, m6_latent_run) -> None:
    manager, job_id, _manifest_path, commit, dirty = _anchored_restart_fixture(
        tmp_path, m6_latent_run
    )
    manager._reconcile_startup()
    interrupted = manager.registry.get_job(job_id)
    assert interrupted["state"] == "INTERRUPTED"
    assert interrupted["error_code"] == "missing_worker_observed_identity"
    assert interrupted["submitted_engine_commit"] == commit
    assert bool(interrupted["submitted_dirty_worktree_flag"]) is dirty
    assert interrupted["worker_observed_engine_commit"] is None
    assert interrupted["result_manifest_path"] is None


@pytest.mark.parametrize("substitution", ["commit", "dirty"])
def test_coordinated_mutable_provenance_substitution_is_rejected(
    tmp_path: Path, m6_latent_run, substitution: str
) -> None:
    manager, job_id, manifest_path, commit, dirty = _anchored_restart_fixture(
        tmp_path, m6_latent_run
    )
    manager.registry.set_worker_observed_identity_once(
        job_id,
        engine_commit=commit,
        dirty_worktree_flag=dirty,
    )
    false_commit = SUBSTITUTE_COMMIT if substitution == "commit" else commit
    false_dirty = not dirty if substitution == "dirty" else dirty
    request_path = manager._job_dir(job_id) / "request.json"
    envelope = json.loads(request_path.read_text(encoding="utf-8"))
    envelope["submitted_engine_identity"]["engine_git_commit"] = false_commit
    envelope["submitted_engine_identity"]["dirty_worktree_flag"] = false_dirty
    request_path.write_text(
        json.dumps(envelope, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["git_commit"] = false_commit
    manifest["dirty_worktree_flag"] = false_dirty
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _candidate(
        manager,
        job_id,
        manifest_path,
        commit=false_commit,
        dirty=false_dirty,
    )
    manager._reconcile_startup()
    interrupted = manager.registry.get_job(job_id)
    assert interrupted["state"] == "INTERRUPTED"
    assert interrupted["error_code"] == "request_hash_mismatch"
    assert interrupted["submitted_engine_commit"] == commit
    assert interrupted["worker_observed_engine_commit"] == commit
    assert bool(interrupted["submitted_dirty_worktree_flag"]) is dirty
    assert bool(interrupted["worker_observed_dirty_worktree_flag"]) is dirty
    assert interrupted["engine_git_commit"] is None
    assert interrupted["result_manifest_path"] is None


@pytest.mark.parametrize("source", ["candidate_commit", "candidate_dirty", "artifact_dirty"])
def test_candidate_and_artifact_evidence_cannot_redefine_registry_anchor(
    tmp_path: Path, m6_latent_run, source: str
) -> None:
    manager, job_id, manifest_path, commit, dirty = _anchored_restart_fixture(
        tmp_path, m6_latent_run
    )
    manager.registry.set_worker_observed_identity_once(
        job_id,
        engine_commit=commit,
        dirty_worktree_flag=dirty,
    )
    if source == "candidate_commit":
        _candidate(manager, job_id, manifest_path, commit=SUBSTITUTE_COMMIT, dirty=dirty)
        expected = "candidate_provenance_mismatch"
    elif source == "candidate_dirty":
        _candidate(manager, job_id, manifest_path, commit=commit, dirty=not dirty)
        expected = "candidate_provenance_mismatch"
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["dirty_worktree_flag"] = not dirty
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        expected = "artifact_provenance_mismatch"
    with pytest.raises(FinalizationError) as raised:
        JobFinalizer(registry=manager.registry, state_dir=tmp_path, project_root=ROOT).finalize(
            job_id
        )
    assert raised.value.code == expected
    unchanged = manager.registry.get_job(job_id)
    assert unchanged["submitted_engine_commit"] == commit
    assert unchanged["worker_observed_engine_commit"] == commit
    assert bool(unchanged["submitted_dirty_worktree_flag"]) is dirty
    assert bool(unchanged["worker_observed_dirty_worktree_flag"]) is dirty
    assert unchanged["state"] == "RUNNING"
    assert unchanged["engine_git_commit"] is None


def test_success_publication_cannot_accept_provenance_overwrite(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "jersey_outbreak.job_manager.observed_engine_identity",
        lambda _root: _identity(ANCHOR_COMMIT, False),
    )
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    job = manager.submit(ScenarioRunRequest(kind="scenario_run", duration_days=1))
    job_id = job["job_id"]
    manager.registry.claim_next_queued()
    manager.registry.set_worker_observed_identity_once(
        job_id,
        engine_commit=ANCHOR_COMMIT,
        dirty_worktree_flag=False,
    )
    with pytest.raises(RegistryError, match="not allowed"):
        manager.registry.finalize_success(
            job_id,
            fields={
                "finished_at": "2026-08-29T12:00:00+00:00",
                "result_manifest_path": "result_manifest.json",
                "result_manifest_hash": "0" * 64,
                "verification_status": "passed",
                "engine_git_commit": SUBSTITUTE_COMMIT,
                "dirty_worktree_flag": 1,
            },
            artifacts=[{"artifact_id": "unreached"}],
        )
    unchanged = manager.registry.get_job(job_id)
    assert unchanged["state"] == "RUNNING"
    assert unchanged["submitted_engine_commit"] == ANCHOR_COMMIT
    assert unchanged["worker_observed_engine_commit"] == ANCHOR_COMMIT
    assert unchanged["engine_git_commit"] is None


def test_schema_v2_fresh_migration_reopen_and_future_rejection(tmp_path: Path) -> None:
    fresh_path = tmp_path / "fresh.sqlite"
    JobRegistry(fresh_path)
    with sqlite3.connect(fresh_path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 2
        columns = {row[1] for row in connection.execute("PRAGMA table_info(jobs)")}
    assert {
        "submitted_engine_commit",
        "submitted_dirty_worktree_flag",
        "worker_observed_engine_commit",
        "worker_observed_dirty_worktree_flag",
    } <= columns
    JobRegistry(fresh_path)

    migrated_path = tmp_path / "migrated.sqlite"
    with sqlite3.connect(migrated_path) as connection:
        connection.executescript(
            """
            CREATE TABLE jobs (
                job_id TEXT PRIMARY KEY,
                job_kind TEXT NOT NULL,
                state TEXT NOT NULL,
                canonical_request TEXT NOT NULL,
                request_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                phase TEXT NOT NULL,
                engine_git_commit TEXT,
                dirty_worktree_flag INTEGER
            );
            INSERT INTO jobs VALUES (
                'historical', 'scenario_run', 'SUCCEEDED', '{}', 'old-hash',
                '2026-08-29T00:00:00+00:00', 'complete', 'historical-commit', 0
            );
            PRAGMA user_version=1;
            """
        )
    migrated = JobRegistry(migrated_path).get_job("historical")
    assert migrated["state"] == "SUCCEEDED"
    assert migrated["engine_git_commit"] == "historical-commit"
    assert migrated["submitted_engine_commit"] is None
    assert migrated["submitted_dirty_worktree_flag"] is None
    assert migrated["worker_observed_engine_commit"] is None
    assert migrated["worker_observed_dirty_worktree_flag"] is None
    with sqlite3.connect(migrated_path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 2

    future_path = tmp_path / "future.sqlite"
    with sqlite3.connect(future_path) as connection:
        connection.execute("PRAGMA user_version=3")
    with pytest.raises(RegistryError, match="unsupported future"):
        JobRegistry(future_path)
