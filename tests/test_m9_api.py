"""Focused Milestone 9 API and persistent-job contracts."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from fastapi.testclient import TestClient

from jersey_outbreak.api import create_app
from jersey_outbreak.api_schemas import ScenarioRunRequest
from jersey_outbreak.job_manager import JobManager
from jersey_outbreak.job_registry import InvalidJobTransitionError, JobRegistry
from jersey_outbreak.job_worker import run_worker
from jersey_outbreak.outbreak_runner import run_outbreak

ROOT = Path(__file__).resolve().parents[1]


def test_registry_state_machine_and_fifo_atomic_claim(tmp_path: Path) -> None:
    registry = JobRegistry(tmp_path / "jobs.sqlite")
    jobs = [
        registry.create_job(
            job_kind="scenario_run",
            canonical_request={"kind": "scenario_run", "n": index},
            request_hash=f"{index:064x}",
        )[0]
        for index in range(3)
    ]
    claimed: list[str] = []
    barrier = threading.Barrier(3)

    def claim() -> None:
        barrier.wait()
        job = registry.claim_next_queued()
        if job is not None:
            claimed.append(job["job_id"])

    threads = [threading.Thread(target=claim) for _ in range(2)]
    for thread in threads:
        thread.start()
    barrier.wait()
    for thread in threads:
        thread.join()
    assert len(claimed) == 2
    assert len(set(claimed)) == 2
    assert claimed[0] in {jobs[0]["job_id"], jobs[1]["job_id"]}
    assert registry.get_job(jobs[2]["job_id"])["state"] == "QUEUED"
    with pytest.raises(InvalidJobTransitionError):
        registry.transition(jobs[2]["job_id"], "FAILED")


def test_registry_hash_persistence_idempotency_and_restart_reconciliation(tmp_path: Path) -> None:
    registry = JobRegistry(tmp_path / "jobs.sqlite")
    canonical = {"schema_version": "m9-1.0", "request": {"kind": "scenario_run"}}
    first, existed = registry.create_job(
        job_kind="scenario_run",
        canonical_request=canonical,
        request_hash=registry.request_hash(canonical),
        idempotency_key="same-request",
    )
    assert not existed
    again, existed = registry.create_job(
        job_kind="scenario_run",
        canonical_request=canonical,
        request_hash=registry.request_hash(canonical),
        idempotency_key="same-request",
    )
    assert existed and again["job_id"] == first["job_id"]
    stale = registry.claim_next_queued()
    assert stale is not None
    registry.reconcile_stale_jobs()
    assert registry.get_job(stale["job_id"])["state"] == "INTERRUPTED"
    assert registry.get_job(first["job_id"])["canonical_request"] == canonical


def test_api_contract_validation_errors_idempotency_and_cors(tmp_path: Path) -> None:
    app = create_app(
        state_dir=tmp_path,
        project_root=ROOT,
        start_scheduler=False,
        cors_origins=["http://localhost:3000"],
    )
    with TestClient(app) as client:
        assert client.get("/health").json()["api_version"] == "v1"
        capabilities = client.get("/api/v1/capabilities").json()
        assert capabilities["scheduler"]["effective_max_concurrent_jobs"] == 1
        assert "school_class" in capabilities["resident_route_ids"]
        assert "disabled" in capabilities["travel_modes"]
        schema = client.get("/openapi.json").json()
        assert "/api/v1/jobs" in schema["paths"]
        assert "/api/v1/jobs/{job_id}/datasets/{dataset_name}" in schema["paths"]

        valid = client.post(
            "/api/v1/scenarios/validate",
            json={
                "scenario": {
                    "schema_version": "7.0",
                    "scenario_id": "valid",
                    "start_date": "2025-01-06",
                    "interventions": [],
                }
            },
        )
        assert valid.status_code == 200
        assert valid.json()["valid"] is True
        invalid = client.post(
            "/api/v1/scenarios/validate",
            json={
                "scenario": {
                    "schema_version": "7.0",
                    "scenario_id": "invalid",
                    "interventions": [{"intervention_id": "closure", "type": "school_closure"}],
                }
            },
        )
        assert invalid.status_code == 200
        assert invalid.json()["valid"] is False

        body = {
            "kind": "scenario_run",
            "mode": "ci",
            "seed": 123,
            "start_date": "2025-01-06",
            "duration_days": 1,
        }
        first = client.post("/api/v1/jobs", json=body, headers={"Idempotency-Key": "abc"})
        second = client.post("/api/v1/jobs", json=body, headers={"Idempotency-Key": "abc"})
        conflict = client.post(
            "/api/v1/jobs",
            json={**body, "seed": 124},
            headers={"Idempotency-Key": "abc"},
        )
        assert first.status_code == second.status_code == 202
        assert first.json()["job_id"] == second.json()["job_id"]
        assert second.json()["already_exists"] is True
        assert conflict.status_code == 409
        assert conflict.json()["code"] == "idempotency_conflict"
        job_id = first.json()["job_id"]
        assert client.post(f"/api/v1/jobs/{job_id}/cancel").json()["state"] == "CANCELLED"
        assert client.post(f"/api/v1/jobs/{job_id}/cancel").json()["idempotent"] is True
        assert client.get("/api/v1/jobs/unknown").status_code == 404
        cors = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert cors.headers["access-control-allow-origin"] == "http://localhost:3000"


def _fake_completed_job(manager: JobManager) -> str:
    request = ScenarioRunRequest(kind="scenario_run")
    job = manager.submit(request)
    job_id = job["job_id"]
    assert manager.registry.claim_next_queued() is not None
    job_dir = manager._job_dir(job_id)
    artifact_dir = job_dir / "artifacts" / "fake"
    artifact_dir.mkdir(parents=True)
    data_path = artifact_dir / "daily_epidemic.parquet"
    pq.write_table(
        pa.Table.from_pylist(
            [
                {"date": "2025-01-07", "parish": "St Helier", "value": 2.0},
                {"date": "2025-01-06", "parish": "St Helier", "value": None},
                {"date": "2025-01-08", "parish": "Trinity", "value": 3.0},
            ]
        ),
        data_path,
    )
    manifest_path = artifact_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "artifact_id": "fake-artifact",
                "module": "generic_respiratory_seirs",
                "output_artifacts": [{"path": "daily_epidemic.parquet"}],
            }
        ),
        encoding="utf-8",
    )
    artifact = {
        "role": "scientific_result",
        "artifact_type": "m5_outbreak",
        "artifact_id": "fake-artifact",
        "manifest_path": "artifacts/fake/manifest.json",
        "verification_status": "passed",
        "size_bytes": data_path.stat().st_size,
        "datasets": ["daily_epidemic"],
    }
    manager.registry.replace_artifacts(job_id, [artifact])
    manager.registry.transition(job_id, "SUCCEEDED", phase="complete")
    return job_id


def test_bounded_dataset_read_and_path_safety(tmp_path: Path) -> None:
    app = create_app(state_dir=tmp_path, project_root=ROOT, start_scheduler=False)
    with TestClient(app) as client:
        job_id = _fake_completed_job(app.state.job_manager)
        response = client.get(
            f"/api/v1/jobs/{job_id}/datasets/daily_epidemic",
            params={"start_date": "2025-01-06", "limit": 1},
        )
        assert response.status_code == 200
        assert response.json()["rows"] == [
            {"date": "2025-01-06", "parish": "St Helier", "value": None}
        ]
        filtered = client.get(
            f"/api/v1/jobs/{job_id}/datasets/daily_epidemic",
            params={"parish": "St Helier", "limit": 10},
        )
        assert filtered.json()["total"] == 2
        for bad_name in ("../daily_epidemic", "../../etc/passwd", "/etc/passwd"):
            assert client.get(f"/api/v1/jobs/{job_id}/datasets/{bad_name}").status_code in {
                400,
                404,
            }
        assert client.get(f"/api/v1/jobs/{job_id}/datasets/not-present").status_code == 404


def test_direct_and_api_worker_scientific_equivalence(
    tmp_path: Path, m6_network, m6_base_config, m6_parameters
) -> None:
    """The worker path must preserve direct M5 hashes and daily epidemic rows."""

    direct = run_outbreak(m6_network, m6_base_config, m6_parameters)
    app = create_app(state_dir=tmp_path, project_root=ROOT)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/jobs",
            json={
                "kind": "scenario_run",
                "mode": "ci",
                "seed": 123,
                "duration_days": m6_base_config.duration_days,
            },
        )
        job_id = response.json()["job_id"]
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            job = client.get(f"/api/v1/jobs/{job_id}").json()
            if job["state"] in {"SUCCEEDED", "FAILED", "CANCELLED", "INTERRUPTED"}:
                break
            time.sleep(0.25)
        assert job["state"] == "SUCCEEDED", job
        assert job["latent_hash"] == direct.latent_outcome_hash
        artifact = client.get(f"/api/v1/jobs/{job_id}/artifacts").json()["artifacts"][0]
        assert artifact["latent_hash"] == direct.latent_outcome_hash
        assert artifact["bundle_hash"] == direct.artifact_bundle_hash
        rows = client.get(
            f"/api/v1/jobs/{job_id}/datasets/daily_epidemic", params={"limit": 10_000}
        ).json()["rows"]
        assert rows == direct.daily_epidemic


def test_running_cancellation_terminates_worker_and_preserves_api(tmp_path: Path) -> None:
    app = create_app(state_dir=tmp_path, project_root=ROOT)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/jobs",
            json={
                "kind": "scenario_run",
                "mode": "scaled",
                "seed": 987,
                "start_date": "2025-01-06",
                "duration_days": 366,
            },
        )
        job_id = response.json()["job_id"]
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            job = client.get(f"/api/v1/jobs/{job_id}").json()
            if job["state"] == "RUNNING":
                break
            time.sleep(0.05)
        assert job["state"] == "RUNNING", job
        assert client.post(f"/api/v1/jobs/{job_id}/cancel").json()["state"] == ("CANCEL_REQUESTED")
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            job = client.get(f"/api/v1/jobs/{job_id}").json()
            if job["state"] in {"CANCELLED", "FAILED", "SUCCEEDED", "INTERRUPTED"}:
                break
            time.sleep(0.1)
        assert job["state"] == "CANCELLED", job
        assert job["artifact_count"] == 0
        assert job["result_manifest_path"] is None
        assert client.get("/health").status_code == 200
        duplicate = client.post(f"/api/v1/jobs/{job_id}/cancel").json()
        assert duplicate["idempotent"] is True


def test_worker_failure_isolated_and_persisted(tmp_path: Path) -> None:
    app = create_app(state_dir=tmp_path, project_root=ROOT, start_scheduler=False)
    with TestClient(app) as client:
        submitted = client.post(
            "/api/v1/jobs",
            json={"kind": "scenario_run", "mode": "ci", "seed": 501, "duration_days": 1},
        ).json()
        job_id = submitted["job_id"]
        manager = app.state.job_manager
        assert manager.registry.claim_next_queued()["job_id"] == job_id
        request_path = manager._job_dir(job_id) / "request.json"
        persisted = json.loads(request_path.read_text(encoding="utf-8"))
        persisted["request"]["seed"] = 999
        request_path.write_text(json.dumps(persisted), encoding="utf-8")
        assert run_worker(job_id=job_id, state_dir=tmp_path, project_root=ROOT) == 1
        job = client.get(f"/api/v1/jobs/{job_id}").json()
        assert job["state"] == "FAILED"
        assert job["error"]["code"] == "worker_execution_failed"
        assert job["artifact_count"] == 0
        assert client.get("/health").status_code == 200
