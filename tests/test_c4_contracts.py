"""Adversarial C4 tests for causal detections and metric-aware ensembles."""

from __future__ import annotations

import inspect
import json
from concurrent.futures import Future
from concurrent.futures.process import BrokenProcessPool
from datetime import date, timedelta
from pathlib import Path

import pytest
from typer.testing import CliRunner

from jersey_outbreak import cli as cli_module
from jersey_outbreak import ensemble as ensemble_module
from jersey_outbreak.ensemble import (
    DEFAULT_PARENT_RESERVE_BYTES,
    DEFAULT_PER_WORKER_BYTES,
    DEFAULT_USABLE_FRACTION,
    ReplicateOutput,
    _completed_grid_rows,
    _replicate_state_path,
    _summary_rows,
    _worker_bound_terms,
    run_ensemble,
    safe_worker_bound,
)
from jersey_outbreak.ensemble_artifacts import write_ensemble_artifact
from jersey_outbreak.network_generator import generate_networks
from jersey_outbreak.network_schemas import NetworkGenerationConfig
from jersey_outbreak.observation import observe_latent_run
from jersey_outbreak.observation_scheduler import DetectionEvent, ObservationScheduler
from jersey_outbreak.observation_schemas import ObservationConfig, ReportingDelayDistribution
from jersey_outbreak.outbreak_runner import run_outbreak

ROOT = Path(__file__).resolve().parents[1]


def _delay(*days: int, probabilities: tuple[float, ...] | None = None):
    return ReportingDelayDistribution(
        kind="fixed" if len(days) == 1 else "discrete",
        days=days,
        probabilities=probabilities,
        status="scenario_assumption",
        notes="Controlled C4 test delay.",
    )


def _observation_config(
    base: ObservationConfig,
    *,
    detection_probability: float = 1.0,
    detection_delay: ReportingDelayDistribution | None = None,
) -> ObservationConfig:
    parameters = {
        key: parameter.model_copy(
            update={
                "value": (
                    detection_probability
                    if key.endswith("detection_probability")
                    else parameter.value
                )
            }
        )
        for key, parameter in base.parameters.items()
    }
    return base.model_copy(
        update={
            "observation_config_id": "c4-runtime-probe",
            "parameters": parameters,
            "detection_delay": detection_delay or _delay(0),
            "reporting_delay": _delay(0),
            "day_of_week_effect": (1.0,) * 7,
            "analysis_horizon_tail_days": None,
        }
    )


class ProbeConsumer:
    def __init__(self) -> None:
        self.events: list[DetectionEvent] = []

    def consume_detection(self, event: DetectionEvent) -> None:
        self.events.append(event)


def _scheduler(m6_network, config: ObservationConfig, *, seed: int = 123, consumer=None):
    agent_ids = m6_network.agent_ids
    return ObservationScheduler(
        latent_seed=seed,
        start_date=date(2025, 1, 6),
        config=config,
        agent_id_by_uid={uid: agent_id for uid, agent_id in enumerate(agent_ids)},
        resident_by_agent_id={
            row["agent_id"]: row for row in m6_network.m3_input.resident_structure
        },
        consumer=consumer,
    )


def _infection(m6_network, uid: int, when: str = "2025-01-06") -> dict:
    infection_date = date.fromisoformat(when)
    infectious_start = infection_date + timedelta(days=1)
    return {
        "infected_uid": uid,
        "infected_agent_id": m6_network.agent_ids[uid],
        "infector_uid": None,
        "date": when,
        "infection_date": when,
        "infectious_start_date": infectious_start.isoformat(),
        "symptomatic": True,
        "symptom_onset_date": infectious_start.isoformat(),
        "recovery_date": (infectious_start + timedelta(days=3)).isoformat(),
        "source_kind": "seeded",
        "route_id": "seeded",
    }


def test_causal_interface_exercises_runtime_delivery_and_preserves_m5(
    m6_network, m6_parameters, m6_base_config, m6_observation_config
) -> None:
    config = m6_base_config.model_copy(
        update={"beta": 0.0, "duration_days": 3, "initial_seed_count": 2}
    )
    baseline = run_outbreak(m6_network, config, m6_parameters)
    probe = ProbeConsumer()
    observation_config = _observation_config(m6_observation_config)
    online = run_outbreak(
        m6_network,
        config,
        m6_parameters,
        observation_config=observation_config,
        detection_consumer=probe,
    )
    assert online.logical_content_hash == baseline.logical_content_hash
    assert online.transmission_events == baseline.transmission_events
    assert online.daily_epidemic == baseline.daily_epidemic
    assert online.observation_schedule is not None
    assert tuple(probe.events) == online.observation_schedule.delivered_detection_events
    assert len(probe.events) == 2
    natural_history_by_agent = {
        event["infected_agent_id"]: event for event in online.transmission_events
    }
    assert all(
        event.detection_date
        == (
            natural_history_by_agent[event.agent_id]["symptom_onset_date"]
            or natural_history_by_agent[event.agent_id]["infection_date"]
        )
        for event in probe.events
    )
    assert online.diagnostics["online_observation_scheduler"]["earliest_consumer_effect"] == (
        "next_timestep"
    )
    offline = observe_latent_run(online, observation_config)
    assert offline.diagnostics["detection_event_interface"]["offline_online_agreement"] is True


def test_detection_queue_never_leaks_future_and_delivers_on_declared_day(
    m6_network, m6_observation_config
) -> None:
    probe = ProbeConsumer()
    config = _observation_config(m6_observation_config, detection_delay=_delay(2))
    scheduler = _scheduler(m6_network, config, consumer=probe)
    scheduler.schedule_infection(_infection(m6_network, 0))
    assert scheduler.deliver_due(0) == ()
    assert scheduler.deliver_due(1) == ()
    assert scheduler.deliver_due(2) == ()
    assert probe.events == []
    delivered = scheduler.deliver_due(3)
    assert len(delivered) == 1
    assert delivered[0].detection_date == "2025-01-09"
    assert probe.events == list(delivered)


def test_observation_rejects_preinfectious_natural_history_onset(
    m6_network, m6_observation_config
) -> None:
    scheduler = _scheduler(m6_network, _observation_config(m6_observation_config))
    event = _infection(m6_network, 0)
    event["symptom_onset_date"] = event["infection_date"]
    with pytest.raises(ValueError, match="onset must equal infectious start"):
        scheduler.schedule_infection(event)


def test_variable_delays_reorder_notifications_by_detection_time(
    m6_network, m6_observation_config
) -> None:
    config = _observation_config(
        m6_observation_config,
        detection_delay=_delay(0, 3, probabilities=(0.5, 0.5)),
    )
    scheduler = _scheduler(m6_network, config)
    infection_order = list(range(20))
    for uid in infection_order:
        scheduler.schedule_infection(_infection(m6_network, uid))
    detections = scheduler.snapshot().detection_events
    assert [event.detection_time_index for event in detections] == sorted(
        event.detection_time_index for event in detections
    )
    delivered_uids = [event.agent_uid for event in detections]
    assert delivered_uids != infection_order
    assert any(
        earlier_uid > later_uid
        for earlier_uid, later_uid in zip(delivered_uids, delivered_uids[1:], strict=False)
    )


def test_final_day_detected_and_undetected_infections_remain_represented(
    m6_network, m6_observation_config
) -> None:
    final_event = _infection(m6_network, 0, "2025-01-08")
    detected = _scheduler(m6_network, _observation_config(m6_observation_config))
    detected.schedule_infection(final_event)
    detected_snapshot = detected.snapshot()
    assert detected_snapshot.observation_events[0]["detection_date"] == "2025-01-09"
    assert len(detected_snapshot.detection_events) == 1

    undetected = _scheduler(
        m6_network,
        _observation_config(m6_observation_config, detection_probability=0.0),
    )
    undetected.schedule_infection(final_event)
    undetected_snapshot = undetected.snapshot()
    assert len(undetected_snapshot.observation_events) == 1
    assert undetected_snapshot.observation_events[0]["detection_date"] is None
    assert undetected_snapshot.detection_events == ()


def test_observation_schedule_reproduces_and_varies_by_replicate_seed(
    m6_network, m6_observation_config
) -> None:
    config = _observation_config(
        m6_observation_config,
        detection_probability=0.5,
        detection_delay=_delay(0, 2, probabilities=(0.5, 0.5)),
    )
    first = _scheduler(m6_network, config, seed=123)
    same = _scheduler(m6_network, config, seed=123)
    changed = _scheduler(m6_network, config, seed=999)
    for uid in range(20):
        event = _infection(m6_network, uid)
        first.schedule_infection(event)
        same.schedule_infection(event)
        changed.schedule_infection(event)
    assert first.snapshot().observation_events == same.snapshot().observation_events
    assert first.snapshot().stream_fingerprint == same.snapshot().stream_fingerprint
    assert first.snapshot().observation_events != changed.snapshot().observation_events
    assert first.snapshot().stream_fingerprint != changed.snapshot().stream_fingerprint


def test_metric_registry_carries_cumulative_tail_and_bounds_state_horizon() -> None:
    trajectories = {
        1: (
            {
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_cumulative_infections",
                "date": "2025-01-02",
                "value": 25,
            },
            {
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_attack_rate",
                "date": "2025-01-02",
                "value": 0.25,
            },
            {
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_new_infections",
                "date": "2025-01-02",
                "value": 2,
            },
            {
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_prevalence",
                "date": "2025-01-02",
                "value": 0.1,
            },
        ),
        2: (
            {
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_cumulative_infections",
                "date": "2025-01-02",
                "value": 30,
            },
            {
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_attack_rate",
                "date": "2025-01-02",
                "value": 0.30,
            },
            {
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_new_infections",
                "date": "2025-01-02",
                "value": 4,
            },
            {
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_prevalence",
                "date": "2025-01-02",
                "value": 0.2,
            },
        ),
    }
    rows = _summary_rows(
        trajectories,
        0.25,
        0.75,
        horizon=("2025-01-02", "2025-01-03", "2025-01-04"),
    )
    cumulative = [row for row in rows if row["metric"] == "latent_cumulative_infections"]
    assert [row["median"] for row in cumulative] == [27.5, 27.5, 27.5]
    assert [row["cell_semantic"] for row in cumulative] == [
        "observed",
        "carried_forward",
        "carried_forward",
    ]
    attack = [row for row in rows if row["metric"] == "latent_attack_rate"]
    assert [row["median"] for row in attack] == [0.275, 0.275, 0.275]
    incidence = [row for row in rows if row["metric"] == "latent_new_infections"]
    assert [row["median"] for row in incidence] == [3.0, 0.0, 0.0]
    prevalence = [row for row in rows if row["metric"] == "latent_prevalence"]
    assert prevalence[0]["median"] == pytest.approx(0.15)
    assert [row["median"] for row in prevalence[1:]] == [None, None]
    assert all(
        row["cell_semantic"] == "outside_metric_horizon" and row["contributing_replicates"] == 0
        for row in prevalence[1:]
    )


def test_failed_replicates_are_visible_noncontributors_and_quantiles_exclude_them() -> None:
    trajectories = {
        1: (
            {
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_new_infections",
                "date": "2025-01-01",
                "value": 7,
            },
        )
    }
    grid = _completed_grid_rows(
        trajectories,
        successful_seeds=(1,),
        failed_seeds=(2,),
    )
    failed_cells = [row for row in grid if row["seed"] == 2]
    assert failed_cells and all(
        row["cell_semantic"] == "failed_replicate"
        and row["value"] is None
        and not row["contributes"]
        for row in failed_cells
    )
    summary = _summary_rows(trajectories, 0.25, 0.75, requested_replicates=2)
    assert summary[0]["median"] is None
    assert summary[0]["interval_class"] == "insufficient_tail"
    assert summary[0]["requested_replicates"] == 2
    assert summary[0]["successful_replicates"] == 1
    assert summary[0]["failed_replicates"] == 1
    assert summary[0]["contributing_replicates"] == 1


def test_controlled_process_fallback_warning_reports_actual_single_worker(
    monkeypatch,
    m6_network,
    m6_parameters,
    m6_base_config,
    m6_observation_config,
    tmp_path,
    capsys,
) -> None:
    def fake_job(job):
        seed = int(job["seed"])
        return ReplicateOutput(
            seed=seed,
            status="passed",
            latent_logical_content_hash="a" * 64,
            observation_logical_content_hash="b" * 64,
            m4_logical_content_hash="c" * 64,
            runtime_seconds=0.0,
            trajectories=(
                {
                    "seed": seed,
                    "scope": "epidemic",
                    "key": "all",
                    "metric": "latent_new_infections",
                    "date": "2025-01-01",
                    "value": 1,
                },
            ),
            error=None,
        )

    class BrokenPool:
        def __init__(self, *args, **kwargs):
            raise PermissionError("controlled semaphore denial")

    monkeypatch.setattr(ensemble_module, "_run_replicate_job", fake_job)
    monkeypatch.setattr(ensemble_module, "ProcessPoolExecutor", BrokenPool)
    result = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        (123, 124),
        ensemble_id="c4-controlled-fallback",
        workers=2,
        allow_unsafe_workers=True,
    )
    assert result.diagnostics["requested_workers"] == 2
    assert result.diagnostics["planned_workers"] == 2
    assert result.diagnostics["actual_workers"] == 1
    assert result.diagnostics["execution_mode"] == "sequential_fallback"
    assert "controlled semaphore denial" in result.diagnostics["fallback_reason"]
    stderr = capsys.readouterr().err
    assert "ENSEMBLE WARNING: process pool unavailable" in stderr
    assert "controlled semaphore denial" in stderr
    assert "actual_workers=1" in stderr
    assert "running 2 replicates sequentially" in stderr
    artifact = write_ensemble_artifact(result, ROOT, tmp_path)
    manifest = json.loads((artifact.artifact_directory / "manifest.json").read_text())
    assert manifest["requested_workers"] == 2
    assert manifest["planned_workers"] == 2
    assert manifest["actual_workers"] == 1
    assert manifest["execution_mode"] == "sequential_fallback"


def test_broken_pool_aborts_without_sequential_fallback(
    monkeypatch,
    m6_network,
    m6_parameters,
    m6_base_config,
    m6_observation_config,
    tmp_path,
    capsys,
) -> None:
    class BrokenPool:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def submit(self, *args, **kwargs):
            raise BrokenProcessPool("worker died")

    monkeypatch.setattr(ensemble_module, "ProcessPoolExecutor", BrokenPool)
    with pytest.raises(RuntimeError, match="ensemble worker pool broke"):
        run_ensemble(
            tmp_path,
            m6_network,
            m6_parameters,
            m6_base_config,
            m6_observation_config,
            (123, 124),
            ensemble_id="c4-broken-pool",
            workers=2,
            allow_unsafe_workers=True,
        )
    stderr = capsys.readouterr().err
    assert "ENSEMBLE ERROR: ensemble worker pool broke" in stderr
    assert "worker died" in stderr
    assert "relaunch with fewer workers" in stderr


def test_bounded_warning_is_emitted_for_memory_bound_workers(
    monkeypatch,
    m6_network,
    m6_parameters,
    m6_base_config,
    m6_observation_config,
    tmp_path,
    capsys,
) -> None:
    def fake_job(job):
        return ReplicateOutput(
            seed=int(job["seed"]),
            status="failed",
            latent_logical_content_hash=None,
            observation_logical_content_hash=None,
            m4_logical_content_hash=None,
            runtime_seconds=0.0,
            trajectories=(),
            error="controlled bounded-worker test",
        )

    monkeypatch.setattr(ensemble_module, "_run_replicate_job", fake_job)
    monkeypatch.setattr(ensemble_module, "available_physical_memory_bytes", lambda: 2_000_000_000)
    result = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        (123,),
        ensemble_id="c4-bounded-warning",
        workers=4,
        estimated_worker_memory_bytes=1_000_000_000,
    )
    assert result.diagnostics["planned_workers"] == 1
    stderr = capsys.readouterr().err
    assert "ENSEMBLE WARNING: workers bounded" in stderr
    assert "requested=4 planned=1" in stderr


def test_memory_default_uses_measured_worker_estimate() -> None:
    assert (
        inspect.signature(safe_worker_bound).parameters["parent_reserve_bytes"].default
        == DEFAULT_PARENT_RESERVE_BYTES
    )
    assert (
        inspect.signature(safe_worker_bound).parameters["usable_fraction"].default
        == DEFAULT_USABLE_FRACTION
    )
    assert (
        inspect.signature(safe_worker_bound).parameters["per_worker_bytes"].default
        == DEFAULT_PER_WORKER_BYTES
    )
    assert (
        inspect.signature(run_ensemble).parameters["parent_reserve_bytes"].default
        == DEFAULT_PARENT_RESERVE_BYTES
    )
    assert (
        inspect.signature(run_ensemble).parameters["memory_safety_fraction"].default
        == DEFAULT_USABLE_FRACTION
    )
    assert (
        inspect.signature(run_ensemble).parameters["estimated_worker_memory_bytes"].default
        == DEFAULT_PER_WORKER_BYTES
    )

    gibibyte = 1024**3
    terms = _worker_bound_terms(
        32,
        parent_reserve_bytes=3 * gibibyte,
        usable_fraction=0.85,
        per_worker_bytes=3 * gibibyte,
        available_memory_bytes=26 * gibibyte,
        cpu_count=16,
    )
    assert terms["parent_reserve_bytes"] == 3 * gibibyte
    assert terms["usable_fraction"] == 0.85
    assert terms["per_worker_bytes"] == 3 * gibibyte
    assert terms["usable_memory_bytes"] == 23 * gibibyte
    assert terms["memory_bound"] == 6  # floor((26 - 3) * 0.85 / 3)
    assert terms["cpu_bound"] == 16
    assert terms["resulting_bound"] == 6  # min(requested=32, cpu=16, memory=6)
    assert (
        safe_worker_bound(
            32,
            available_memory_bytes=26 * gibibyte,
            cpu_count=16,
        )
        == 6
    )


def _checkpoint_test_output(seed: int, value: int = 1) -> ReplicateOutput:
    return ReplicateOutput(
        seed=seed,
        status="passed",
        latent_logical_content_hash="a" * 64,
        observation_logical_content_hash="b" * 64,
        m4_logical_content_hash="c" * 64,
        runtime_seconds=0.0,
        trajectories=(
            {
                "seed": seed,
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_new_infections",
                "date": "2025-01-01",
                "value": value,
            },
        ),
        error=None,
    )


def test_matching_checkpoint_is_resumed_without_rerunning_seed(
    monkeypatch,
    m6_network,
    m6_parameters,
    m6_base_config,
    m6_observation_config,
    tmp_path,
) -> None:
    calls: list[int] = []

    def counting_job(job):
        calls.append(int(job["seed"]))
        return _checkpoint_test_output(int(job["seed"]))

    monkeypatch.setattr(ensemble_module, "_run_replicate_job", counting_job)
    cold = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        (123,),
        ensemble_id="c4-resume-match",
    )
    resumed = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        (123,),
        ensemble_id="c4-resume-match",
    )
    checkpoint_root = tmp_path / "outputs" / ".replicates-in-progress"
    checkpoint = json.loads(
        _replicate_state_path(checkpoint_root, "c4-resume-match", 123).read_text()
    )
    assert set(checkpoint["provenance"]) == {
        "replicate_seed",
        "base_config_hash",
        "code_identity",
        "m2_logical_content_hash",
        "m3_logical_content_hash",
    }
    assert calls == [123]
    assert resumed.diagnostics["resumed_replicates"] == 1
    assert cold.logical_content_hash == resumed.logical_content_hash
    assert cold.summary == resumed.summary


def test_checkpoint_with_different_base_config_hash_is_ignored_and_rerun(
    monkeypatch,
    m6_network,
    m6_parameters,
    m6_base_config,
    m6_observation_config,
    tmp_path,
) -> None:
    calls: list[int] = []

    def counting_job(job):
        calls.append(int(job["seed"]))
        return _checkpoint_test_output(int(job["seed"]))

    monkeypatch.setattr(ensemble_module, "_run_replicate_job", counting_job)
    run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        (123,),
        ensemble_id="c4-resume-mismatch",
    )
    changed_config = m6_base_config.model_copy(update={"duration_days": 7})
    rerun = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        changed_config,
        m6_observation_config,
        (123,),
        ensemble_id="c4-resume-mismatch",
    )
    assert calls == [123, 123]
    assert rerun.diagnostics["resumed_replicates"] == 0
    assert rerun.diagnostics["ignored_replicate_checkpoints"] == 1


def test_broken_pool_keeps_completed_checkpoints_for_reinvocation(
    monkeypatch,
    m6_network,
    m6_parameters,
    m6_base_config,
    m6_observation_config,
    tmp_path,
    capsys,
) -> None:
    class MidRunBrokenPool:
        def __init__(self, *args, **kwargs):
            self.futures: list[Future] = []

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def submit(self, _worker, job):
            future = Future()
            self.futures.append(future)
            if int(job["seed"]) == 123:
                future.set_result(_checkpoint_test_output(123))
            else:
                future.set_exception(BrokenProcessPool("controlled worker death"))
            return future

    monkeypatch.setattr(ensemble_module, "ProcessPoolExecutor", MidRunBrokenPool)
    checkpoint_root = tmp_path / "outputs" / ".replicates-in-progress"
    with pytest.raises(RuntimeError, match="persisted completed outputs=1"):
        run_ensemble(
            tmp_path,
            m6_network,
            m6_parameters,
            m6_base_config,
            m6_observation_config,
            (123, 124),
            ensemble_id="c4-resume-broken",
            workers=2,
            allow_unsafe_workers=True,
        )
    assert _replicate_state_path(checkpoint_root, "c4-resume-broken", 123).exists()
    assert not _replicate_state_path(checkpoint_root, "c4-resume-broken", 124).exists()
    assert "re-invocation will resume them" in capsys.readouterr().err

    calls: list[int] = []

    def completing_job(job):
        calls.append(int(job["seed"]))
        return _checkpoint_test_output(int(job["seed"]))

    monkeypatch.setattr(ensemble_module, "_run_replicate_job", completing_job)
    result = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        m6_base_config,
        m6_observation_config,
        (123, 124),
        ensemble_id="c4-resume-broken",
        workers=1,
    )
    assert calls == [124]
    assert result.diagnostics["resumed_replicates"] == 1
    assert result.diagnostics["status"] == "passed"
    assert [record.seed for record in result.replicate_records] == [123, 124]


def test_worker_bound_uses_explicit_budget_and_affinity_inputs() -> None:
    gibibyte = 1024**3
    assert (
        safe_worker_bound(
            32,
            available_memory_bytes=26 * gibibyte,
            cpu_count=16,
            parent_reserve_bytes=3 * gibibyte,
            usable_fraction=0.85,
            per_worker_bytes=3 * gibibyte,
        )
        == 6
    )


def test_ensemble_cli_broken_pool_exits_two_with_plain_message(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(cli_module, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(cli_module, "load_parameter_set", lambda *args: object())
    monkeypatch.setattr(cli_module, "load_observation_config", lambda *args: object())
    monkeypatch.setattr(cli_module, "default_run_config", lambda *args, **kwargs: object())
    monkeypatch.setattr(cli_module, "_build_m4_for_m6", lambda *args, **kwargs: object())

    def broken_ensemble(*args, **kwargs):
        raise RuntimeError("ensemble worker pool broke: worker died; relaunch with fewer workers")

    monkeypatch.setattr(cli_module, "run_ensemble", broken_ensemble)
    result = CliRunner().invoke(cli_module.app, ["ensemble", "run"])
    assert result.exit_code == 2
    assert "ensemble worker pool broke: worker died; relaunch with fewer workers" in result.output
    assert "\x1b" not in result.output


def test_zero_community_contact_configuration_produces_zero_edges(m6_network) -> None:
    zero = generate_networks(
        NetworkGenerationConfig(
            mode="ci",
            seed=123,
            community_indoor_contacts=0,
            community_outdoor_contacts=0,
        ),
        m6_network.m2_input,
        m6_network.m3_input,
        ROOT,
    )
    for route_id in ("community_indoor", "community_outdoor"):
        assert all(
            zero.route_snapshot(route_id, snapshot_date).edges == ()
            for snapshot_date in zero.config.snapshot_dates
        )
