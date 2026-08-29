"""Adversarial M9.1 finalization and scientific-verification gates."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from fastapi.testclient import TestClient

from jersey_outbreak.api import _read_bounded, create_app
from jersey_outbreak.api_schemas import (
    APIResultCandidate,
    CandidateArtifact,
    DatasetQuery,
    ScenarioCompareRequest,
    ScenarioRunRequest,
)
from jersey_outbreak.artifact_catalog import ALL_SCIENTIFIC_DATASETS
from jersey_outbreak.ensemble import run_ensemble
from jersey_outbreak.ensemble_artifacts import write_ensemble_artifact
from jersey_outbreak.execution_adapter import AdapterResult, execute_job
from jersey_outbreak.hashing import sha256_file
from jersey_outbreak.intervention_schemas import ScenarioConfig
from jersey_outbreak.job_finalizer import FinalizationError, JobFinalizer
from jersey_outbreak.job_manager import JobManager
from jersey_outbreak.job_registry import InvalidJobTransitionError, RegistryError
from jersey_outbreak.job_worker import run_worker
from jersey_outbreak.outbreak_artifacts import write_outbreak_artifact
from jersey_outbreak.scientific_verification import verify_scientific_artifact

ROOT = Path(__file__).resolve().parents[1]


def _update_checksum(manifest_path: Path, changed_path: Path) -> None:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    record = next(
        item for item in payload["output_artifacts"] if Path(item["path"]).name == changed_path.name
    )
    record["sha256"] = sha256_file(changed_path)
    record["size_bytes"] = changed_path.stat().st_size
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _candidate_for(
    manager: JobManager, job_id: str, manifest_path: Path, *, role: str = "scientific_result"
) -> None:
    job = manager.registry.get_job(job_id)
    envelope = json.loads((manager._job_dir(job_id) / "request.json").read_text(encoding="utf-8"))
    identity = envelope["submitted_engine_identity"]
    candidate = APIResultCandidate(
        job_id=job_id,
        job_kind=job["job_kind"],
        request_hash=job["request_hash"],
        started_at=job["started_at"],
        finished_at="2026-08-29T12:00:00+00:00",
        engine_git_commit=identity["engine_git_commit"],
        dirty_worktree_flag=identity["dirty_worktree_flag"],
        output_artifacts=[
            CandidateArtifact(
                role=role,
                manifest_path=str(manifest_path.relative_to(manager._job_dir(job_id))),
            )
        ],
    )
    (manager._job_dir(job_id) / "result_candidate.json").write_text(
        json.dumps(candidate.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    )


def test_generic_transition_cannot_publish_success(tmp_path: Path) -> None:
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    job = manager.submit(ScenarioRunRequest(kind="scenario_run", duration_days=1))
    manager.registry.claim_next_queued()
    with pytest.raises(InvalidJobTransitionError):
        manager.registry.transition(job["job_id"], "SUCCEEDED")
    with pytest.raises(RegistryError, match="not allowed"):
        manager.registry.update_fields(job["job_id"], {"state": "SUCCEEDED"})
    with pytest.raises(RegistryError, match="not allowed"):
        manager.registry.transition(job["job_id"], "FAILED", fields={"state": "SUCCEEDED"})


def test_worker_reverifies_and_rejects_missing_adapter_artifact(
    tmp_path: Path, monkeypatch
) -> None:
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    job = manager.submit(ScenarioRunRequest(kind="scenario_run", duration_days=1))
    job_id = job["job_id"]
    manager.registry.claim_next_queued()
    monkeypatch.setattr(
        "jersey_outbreak.job_worker.execute_job",
        lambda *_args, **_kwargs: AdapterResult(
            (
                {
                    "role": "scientific_result",
                    "manifest_path": "artifacts/disappeared/manifest.json",
                },
            )
        ),
    )
    assert run_worker(job_id=job_id, state_dir=tmp_path, project_root=ROOT) == 1
    failed = manager.registry.get_job(job_id)
    assert failed["state"] == "FAILED"
    assert failed["error_code"] == "invalid_artifact_manifest_path"
    assert failed["result_manifest_path"] is None
    assert failed["worker_pid"] is None
    assert manager.registry.artifacts(job_id) == []


def test_cors_rejects_wildcard_and_non_loopback_origins(tmp_path: Path) -> None:
    for origins in (["*"], ["https://example.com"], ["null"]):
        with pytest.raises(ValueError, match="loopback"):
            create_app(
                state_dir=tmp_path / str(len(str(origins))),
                project_root=ROOT,
                cors_origins=origins,
                start_scheduler=False,
            )
    app = create_app(
        state_dir=tmp_path / "valid",
        project_root=ROOT,
        cors_origins=["http://127.0.0.1:3000", "http://localhost:5173"],
        start_scheduler=False,
    )
    with TestClient(app) as client:
        capabilities = client.get("/api/v1/capabilities").json()
        assert set(capabilities["dataset_names"]) == set(ALL_SCIENTIFIC_DATASETS)
        assert {
            "daily_high_risk",
            "temporary_edges",
            "seasonality_schedule",
            "visitor_population",
        } <= set(capabilities["dataset_names"])
        schema = client.get("/openapi.json").json()
        expected_models = {
            ("/health", "get"): "HealthResponse",
            ("/api/v1/capabilities", "get"): "CapabilitiesResponse",
            ("/api/v1/scenarios/validate", "post"): "ScenarioValidationResponse",
            ("/api/v1/jobs", "post"): "JobSubmissionResponse",
            ("/api/v1/jobs", "get"): "JobListResponse",
            ("/api/v1/jobs/{job_id}", "get"): "JobStatusResponse",
            ("/api/v1/jobs/{job_id}/events", "get"): "JobEventsResponse",
            ("/api/v1/jobs/{job_id}/artifacts", "get"): "JobArtifactsResponse",
            ("/api/v1/jobs/{job_id}/datasets", "get"): "JobDatasetsResponse",
            (
                "/api/v1/jobs/{job_id}/datasets/{dataset_name}",
                "get",
            ): "DatasetReadResponse",
        }
        for (path, method), model in expected_models.items():
            response_code = "202" if method == "post" and path == "/api/v1/jobs" else "200"
            response_schema = schema["paths"][path][method]["responses"][response_code]["content"][
                "application/json"
            ]["schema"]
            assert response_schema["$ref"].endswith(f"/{model}")
        assert schema["paths"]["/api/v1/jobs"]["post"]["responses"]["422"]["content"][
            "application/json"
        ]["schema"]["$ref"].endswith("/APIErrorBody")


def test_dataset_scanner_pushes_filter_projection_and_bounded_page(tmp_path: Path) -> None:
    path = tmp_path / "large.parquet"
    rows = [
        {
            "date": "2025-01-01" if index < 25_000 else "2025-01-28",
            "parish": "St Helier" if index % 2 == 0 else "Trinity",
            "value": index,
            "unrequested": f"large-{index}",
        }
        for index in range(50_000)
    ]
    pq.write_table(pa.Table.from_pylist(rows), path, row_group_size=500)
    page, total, has_more = _read_bounded(
        path,
        DatasetQuery(
            start_date=date(2025, 1, 28),
            end_date=date(2025, 1, 28),
            parish="St Helier",
            offset=10,
            limit=3,
            columns=("date", "value"),
        ),
    )
    assert total is None
    assert has_more is True
    assert [row["value"] for row in page] == [25_020, 25_022, 25_024]
    assert all(set(row) == {"date", "value"} for row in page)


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group contract")
def test_cancellation_terminates_controlled_process_tree(tmp_path: Path) -> None:
    child_pid_path = tmp_path / "child.pid"
    script = (
        "import pathlib,subprocess,sys,time;"
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']);"
        "pathlib.Path(sys.argv[1]).write_text(str(child.pid));"
        "time.sleep(60)"
    )
    parent = subprocess.Popen(
        [sys.executable, "-c", script, str(child_pid_path)],
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    manager = JobManager(state_dir=tmp_path / "state", project_root=ROOT)
    manager._processes["controlled"] = parent
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and not child_pid_path.exists():
        time.sleep(0.02)
    assert child_pid_path.exists()
    child_pid = int(child_pid_path.read_text())
    manager._terminate_process("controlled")
    assert parent.poll() is not None
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            os.kill(child_pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.02)
    else:
        pytest.fail("cancelled worker descendant remained alive")


def test_every_non_success_terminal_transition_clears_worker_pid(tmp_path: Path) -> None:
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)

    def create() -> str:
        canonical = {"schema_version": "m9-1.0", "request": {"kind": "scenario_run"}}
        return manager.registry.create_job(
            job_kind="scenario_run",
            canonical_request=canonical,
            request_hash=manager.registry.request_hash(canonical),
        )[0]["job_id"]

    queued = create()
    manager.registry.update_fields(queued, {"worker_pid": 111})
    manager.registry.request_cancel(queued)
    assert manager.registry.get_job(queued)["worker_pid"] is None

    for target in ("FAILED", "INTERRUPTED"):
        job_id = create()
        manager.registry.claim_next_queued()
        manager.registry.update_fields(job_id, {"worker_pid": 222})
        manager.registry.transition(job_id, target)
        assert manager.registry.get_job(job_id)["worker_pid"] is None

    cancelling = create()
    manager.registry.claim_next_queued()
    manager.registry.update_fields(cancelling, {"worker_pid": 333})
    manager.registry.request_cancel(cancelling)
    manager.registry.transition(cancelling, "CANCELLED")
    assert manager.registry.get_job(cancelling)["worker_pid"] is None


def test_m5_content_tamper_fails_even_with_updated_file_checksum(
    tmp_path: Path, m6_latent_run
) -> None:
    artifact = write_outbreak_artifact(m6_latent_run, ROOT, tmp_path)
    verified = verify_scientific_artifact(artifact.artifact_directory)
    assert verified.latent_hash == m6_latent_run.latent_outcome_hash
    table_path = artifact.artifact_directory / "daily_epidemic.parquet"
    rows = pq.read_table(table_path).to_pylist()
    rows[0]["susceptible"] = 0
    pq.write_table(pa.Table.from_pylist(rows), table_path)
    _update_checksum(artifact.artifact_directory / "manifest.json", table_path)
    with pytest.raises(ValueError, match="logical content hash|population conservation"):
        verify_scientific_artifact(artifact.artifact_directory)


def test_m6_content_tamper_fails_even_with_updated_file_checksum(
    tmp_path: Path, m6_network, m6_parameters, m6_base_config, m6_observation_config
) -> None:
    result = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        (123,),
        ensemble_id="m9-1-content-check",
    )
    artifact = write_ensemble_artifact(result, ROOT, tmp_path)
    assert verify_scientific_artifact(artifact.artifact_directory).bundle_hash == (
        result.logical_content_hash
    )
    table_path = artifact.artifact_directory / "ensemble_summary.parquet"
    table = pq.read_table(table_path)
    rows = table.to_pylist()
    rows[0]["median"] = float(rows[0]["median"]) + 1.0
    pq.write_table(pa.Table.from_pylist(rows, schema=table.schema), table_path)
    _update_checksum(artifact.artifact_directory / "manifest.json", table_path)
    with pytest.raises(ValueError, match="logical content hash"):
        verify_scientific_artifact(artifact.artifact_directory)


def test_restart_uses_same_finalizer_and_is_idempotent(tmp_path: Path, m6_latent_run) -> None:
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    job = manager.submit(ScenarioRunRequest(kind="scenario_run", duration_days=8))
    job_id = job["job_id"]
    manager.registry.claim_next_queued()
    artifact = write_outbreak_artifact(m6_latent_run, ROOT, manager._job_dir(job_id) / "artifacts")
    _candidate_for(manager, job_id, artifact.artifact_directory / "manifest.json")
    restarted = JobManager(state_dir=tmp_path, project_root=ROOT)
    restarted._reconcile_startup()
    completed = restarted.registry.get_job(job_id)
    assert completed["state"] == "SUCCEEDED"
    assert completed["worker_pid"] is None
    event_types = [item["type"] for item in restarted.registry.events(job_id)]
    assert event_types[-3:] == ["artifact_written", "artifact_verified", "job_completed"]
    before = list(event_types)
    JobFinalizer(registry=restarted.registry, state_dir=tmp_path, project_root=ROOT).finalize(
        job_id
    )
    assert [item["type"] for item in restarted.registry.events(job_id)] == before
    result_path = restarted._job_dir(job_id) / "result_manifest.json"
    tampered = json.loads(result_path.read_text(encoding="utf-8"))
    tampered["request_hash"] = "0" * 64
    result_path.write_text(json.dumps(tampered, indent=2, sort_keys=True) + "\n")
    with pytest.raises(FinalizationError, match="completed result identity"):
        JobFinalizer(registry=restarted.registry, state_dir=tmp_path, project_root=ROOT).finalize(
            job_id
        )


def test_restart_accepts_only_complete_valid_comparison(tmp_path: Path) -> None:
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    request = ScenarioCompareRequest(
        kind="scenario_compare",
        duration_days=1,
        replicate_seeds=(123,),
        comparison_id="m9-1-restart-comparison",
        treated=ScenarioConfig(scenario_id="m9-1-restart-treated"),
    )
    job = manager.submit(request)
    job_id = job["job_id"]
    claimed = manager.registry.claim_next_queued()
    assert claimed is not None and claimed["job_id"] == job_id
    result = execute_job(
        request.model_dump(mode="json"),
        root=ROOT,
        job_directory=manager._job_dir(job_id),
    )
    envelope = json.loads((manager._job_dir(job_id) / "request.json").read_text(encoding="utf-8"))
    identity = envelope["submitted_engine_identity"]
    candidate = APIResultCandidate(
        job_id=job_id,
        job_kind="scenario_compare",
        request_hash=job["request_hash"],
        started_at=claimed["started_at"],
        finished_at="2026-08-29T12:00:00+00:00",
        engine_git_commit=identity["engine_git_commit"],
        dirty_worktree_flag=identity["dirty_worktree_flag"],
        output_artifacts=[
            CandidateArtifact(role=item["role"], manifest_path=item["manifest_path"])
            for item in result.artifacts
        ],
    )
    (manager._job_dir(job_id) / "result_candidate.json").write_text(
        json.dumps(candidate.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    )
    restarted = JobManager(state_dir=tmp_path, project_root=ROOT)
    restarted._reconcile_startup()
    completed = restarted.registry.get_job(job_id)
    assert completed["state"] == "SUCCEEDED"
    assert {item["role"] for item in restarted.registry.artifacts(job_id)} == {
        "baseline",
        "treated",
        "comparison",
    }


@pytest.mark.parametrize("defect", ["missing", "wrong_role", "wrong_commit", "wrong_request_hash"])
def test_restart_rejects_incomplete_or_unbound_candidates(tmp_path: Path, defect: str) -> None:
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    job = manager.submit(ScenarioRunRequest(kind="scenario_run", duration_days=1))
    job_id = job["job_id"]
    manager.registry.claim_next_queued()
    request = json.loads((manager._job_dir(job_id) / "request.json").read_text(encoding="utf-8"))
    identity = request["submitted_engine_identity"]
    artifacts = (
        []
        if defect == "missing"
        else [CandidateArtifact(role="baseline", manifest_path="artifacts/no/manifest.json")]
        if defect == "wrong_role"
        else [
            CandidateArtifact(role="scientific_result", manifest_path="artifacts/no/manifest.json")
        ]
    )
    candidate = APIResultCandidate(
        job_id=job_id,
        job_kind="scenario_run",
        request_hash="0" * 64 if defect == "wrong_request_hash" else job["request_hash"],
        started_at=manager.registry.get_job(job_id)["started_at"],
        finished_at="2026-08-29T12:00:00+00:00",
        engine_git_commit=("bogus" if defect == "wrong_commit" else identity["engine_git_commit"]),
        dirty_worktree_flag=identity["dirty_worktree_flag"],
        output_artifacts=artifacts,
    )
    (manager._job_dir(job_id) / "result_candidate.json").write_text(
        json.dumps(candidate.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    )
    JobManager(state_dir=tmp_path, project_root=ROOT)._reconcile_startup()
    reconciled = manager.registry.get_job(job_id)
    assert reconciled["state"] == "INTERRUPTED"
    assert reconciled["error_code"] is not None
    assert reconciled["result_manifest_path"] is None
    assert manager.registry.artifacts(job_id) == []


@pytest.mark.parametrize(
    "defect", ["wrong_type", "request_mismatch", "artifact_commit", "expected_commit"]
)
def test_restart_rejects_real_artifact_contract_defects(
    tmp_path: Path, m6_latent_run, defect: str
) -> None:
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    request = ScenarioRunRequest(
        kind="scenario_run",
        duration_days=1 if defect == "request_mismatch" else 8,
        scenario=(ScenarioConfig(scenario_id="expects-m7") if defect == "wrong_type" else None),
    )
    job = manager.submit(request)
    job_id = job["job_id"]
    manager.registry.claim_next_queued()
    artifact = write_outbreak_artifact(m6_latent_run, ROOT, manager._job_dir(job_id) / "artifacts")
    manifest_path = artifact.artifact_directory / "manifest.json"
    if defect == "artifact_commit":
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["git_commit"] = "bogus-provenance"
        manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if defect == "expected_commit":
        request_path = manager._job_dir(job_id) / "request.json"
        envelope = json.loads(request_path.read_text(encoding="utf-8"))
        envelope["submitted_engine_identity"]["engine_git_commit"] = "bogus-expected"
        request_path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n")
    _candidate_for(manager, job_id, manifest_path)
    JobManager(state_dir=tmp_path, project_root=ROOT)._reconcile_startup()
    reconciled = manager.registry.get_job(job_id)
    assert reconciled["state"] == "INTERRUPTED"
    assert reconciled["error_code"] is not None
    assert reconciled["result_manifest_path"] is None
    assert manager.registry.artifacts(job_id) == []


def test_result_manifest_write_failure_never_succeeds(
    tmp_path: Path, m6_latent_run, monkeypatch
) -> None:
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    job = manager.submit(ScenarioRunRequest(kind="scenario_run", duration_days=8))
    job_id = job["job_id"]
    manager.registry.claim_next_queued()
    artifact = write_outbreak_artifact(m6_latent_run, ROOT, manager._job_dir(job_id) / "artifacts")
    _candidate_for(manager, job_id, artifact.artifact_directory / "manifest.json")

    def fail_write(*_args, **_kwargs) -> None:
        raise OSError("injected result-manifest write failure")

    monkeypatch.setattr("jersey_outbreak.job_finalizer._atomic_json", fail_write)
    with pytest.raises(OSError, match="injected"):
        JobFinalizer(registry=manager.registry, state_dir=tmp_path, project_root=ROOT).finalize(
            job_id
        )
    assert manager.registry.get_job(job_id)["state"] == "RUNNING"
    assert manager.registry.artifacts(job_id) == []
    assert not (manager._job_dir(job_id) / "result_manifest.json").exists()


def test_success_publication_rolls_back_on_event_failure(tmp_path: Path, monkeypatch) -> None:
    manager = JobManager(state_dir=tmp_path, project_root=ROOT)
    job = manager.submit(ScenarioRunRequest(kind="scenario_run", duration_days=1))
    job_id = job["job_id"]
    manager.registry.claim_next_queued()

    def fail_event(*_args, **_kwargs) -> None:
        raise RuntimeError("injected event failure")

    monkeypatch.setattr(manager.registry, "_insert_event", fail_event)
    with pytest.raises(RuntimeError, match="injected"):
        manager.registry.finalize_success(
            job_id,
            fields={
                "finished_at": "2026-08-29T12:00:00+00:00",
                "result_manifest_path": "result_manifest.json",
                "result_manifest_hash": "a" * 64,
                "verification_status": "passed",
                "engine_git_commit": "test",
                "dirty_worktree_flag": 1,
            },
            artifacts=[
                {
                    "role": "scientific_result",
                    "artifact_type": "m5_outbreak",
                    "artifact_id": "fixture",
                    "manifest_path": "artifacts/fixture/manifest.json",
                }
            ],
        )
    assert manager.registry.get_job(job_id)["state"] == "RUNNING"
    assert manager.registry.artifacts(job_id) == []


@pytest.mark.parametrize(
    ("payload", "expected_types"),
    [
        (
            {
                "kind": "ensemble",
                "mode": "ci",
                "replicate_seeds": [123],
                "duration_days": 1,
                "ensemble_id": "m9-1-worker-ensemble",
            },
            {"ensemble": "m6_ensemble"},
        ),
        (
            {
                "kind": "scenario_compare",
                "mode": "ci",
                "replicate_seeds": [123],
                "duration_days": 1,
                "comparison_id": "m9-1-worker-comparison",
                "treated": {
                    "scenario_id": "m9-1-treated",
                    "schema_version": "7.0",
                    "interventions": [],
                },
            },
            {
                "baseline": "m6_ensemble",
                "treated": "m6_ensemble",
                "comparison": "m6_comparison",
            },
        ),
        (
            {
                "kind": "scenario_run",
                "mode": "ci",
                "seed": 123,
                "duration_days": 1,
                "scenario": {
                    "scenario_id": "m9-1-worker-m7",
                    "schema_version": "7.0",
                    "interventions": [],
                },
            },
            {"scientific_result": "m7_intervention"},
        ),
        (
            {
                "kind": "scenario_run",
                "mode": "ci",
                "seed": 123,
                "duration_days": 1,
                "scenario": {
                    "scenario_id": "m9-1-worker-m8",
                    "schema_version": "8.0",
                    "interventions": [],
                    "travel": {"mode": "explicit_travel", "stream_scale": 0.0},
                },
            },
            {"scientific_result": "m8_travel"},
        ),
    ],
)
def test_worker_finalizer_accepts_complete_scientific_contracts(
    tmp_path: Path, payload: dict[str, object], expected_types: dict[str, str]
) -> None:
    app = create_app(state_dir=tmp_path, project_root=ROOT)
    with TestClient(app) as client:
        submitted = client.post("/api/v1/jobs", json=payload)
        assert submitted.status_code == 202, submitted.json()
        job_id = submitted.json()["job_id"]
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            job = client.get(f"/api/v1/jobs/{job_id}").json()
            if job["state"] in {"SUCCEEDED", "FAILED", "CANCELLED", "INTERRUPTED"}:
                break
            time.sleep(0.1)
        assert job["state"] == "SUCCEEDED", job
        assert job["worker_pid"] is None
        artifacts = client.get(f"/api/v1/jobs/{job_id}/artifacts").json()["artifacts"]
        assert {artifact["role"]: artifact["artifact_type"] for artifact in artifacts} == (
            expected_types
        )
        result_path = app.state.job_manager._job_dir(job_id) / "result_manifest.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        assert result["api_version"] == "v1"
        assert result["request_hash"] == job["request_hash"]
        assert result["engine_git_commit"] == job["engine_git_commit"]
        events = client.get(f"/api/v1/jobs/{job_id}/events").json()["events"]
        event_types = [event["type"] for event in events]
        assert event_types[-1] == "job_completed"
        assert "artifact_written" in event_types
        assert "artifact_verified" in event_types
        assert not any(
            event["type"] == "phase_changed" and event["metadata"].get("phase") == "complete"
            for event in events
        )
