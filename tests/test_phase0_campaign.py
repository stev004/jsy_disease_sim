from __future__ import annotations

import inspect
import math
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest
import yaml

from jersey_outbreak.phase0_campaign import (
    FIT_PROCESS_SEEDS,
    PREDECLARATION_SHA256,
    BudgetError,
    CampaignBlockedError,
    CampaignConfig,
    CampaignError,
    CandidateCell,
    ExecutionEvidence,
    ObservedTables,
    ProfileDiagnostic,
    RecoveryRow,
    TruthDiagnostics,
    candidate_config_hash,
    dry_run,
    evaluate_p01,
    fit_blind,
    guard_workload,
    join_truth_evaluation,
    minimum_distance_loss,
    observation_dates,
    observed_tables_from_events,
    plan_workload,
    run_p01_campaign,
    score_complete_grid,
    sha256_file,
    truth_diagnostics_from_events,
    validate_observation_calendar,
    write_research_bundle,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "calibration" / "v13_phase0_synthetic.yaml"
REPOSITORY_PREDECLARATION_PATH = (
    ROOT / "docs" / "research" / "v1_3" / "2026-09-21-phase0-predeclaration.md"
)
PREDECLARATION_PATH = REPOSITORY_PREDECLARATION_PATH


def _config() -> CampaignConfig:
    return CampaignConfig.from_yaml(CONFIG_PATH)


def _tables(value: float, *, dates: tuple[str, ...] = ("2025-01-06",)) -> ObservedTables:
    return ObservedTables(dates, (value,), (value,))


def _prediction_library(
    *, target: CandidateCell | None = None, flat: bool = False, near_flat: bool = False
) -> tuple[ObservedTables, dict[CandidateCell, tuple[ObservedTables, ...]]]:
    grid = _config().candidate_grid
    target = target or grid[0]
    dates = observation_dates(date(2025, 1, 6), 30, 4)
    target_table: ObservedTables | None = None
    library: dict[CandidateCell, tuple[ObservedTables, ...]] = {}
    for index, cell in enumerate(grid):
        if flat:
            value = 0.0
        elif near_flat:
            value = 1.0 + index * 0.01
        else:
            value = float(index)
        table = ObservedTables(dates, (value,) * len(dates), (value,) * len(dates))
        library[cell] = (table, table, table)
        if cell == target:
            target_table = table
    assert target_table is not None
    return target_table, library


def _identified_profiles() -> tuple[ProfileDiagnostic, ...]:
    names = (
        "beta",
        "inoculation_day_offset",
        "symptomatic_detection_probability",
        "asymptomatic_detection_probability",
    )
    return tuple(
        ProfileDiagnostic(
            dimension=name,
            values=(0.0, 1.0, 2.0),
            profiled_objectives=(0.0, 1.0, 2.0),
            minimum=0.0,
            second_minimum=1.0,
            numerical_tie=False,
            relative_gap=1.0,
            identified=True,
        )
        for name in names
    )


def _diagnostics(*, chronology: bool = True) -> TruthDiagnostics:
    return TruthDiagnostics(
        inoculation_acquisitions=10,
        local_secondary_infections=1,
        symptomatic_reports=1,
        asymptomatic_reports=1,
        nonzero_combined_report_dates=3,
        chronology_passed=chronology,
        latent_incidence_conservation_passed=True,
    )


def test_p0_1_config_and_workload_are_exact() -> None:
    config = _config()
    plan = plan_workload(config)
    assert config.expected_predeclaration_sha256 == PREDECLARATION_SHA256
    assert len(config.candidate_grid) == 81
    assert config.target_process_seeds == (42001, 42002, 42003, 42004, 42005)
    assert config.candidate_process_seeds == FIT_PROCESS_SEEDS
    assert plan.p01_cells == 81
    assert plan.p01_latent_calls == 32
    assert plan.p01_observation_transforms == 248
    assert plan.total_cells == 198
    assert plan.total_latent_calls == 59
    assert plan.total_observation_transforms == 599
    assert plan.distinct_network_seed_builds == 8


def test_p0_1_dry_run_does_not_call_simulation_or_observation(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import jersey_outbreak.phase0_campaign as campaign

    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("dry-run called a simulation or observation transform")

    monkeypatch.setattr(campaign, "run_outbreak", fail_if_called, raising=False)
    monkeypatch.setattr(campaign, "observe_latent_run", fail_if_called, raising=False)
    plan = dry_run(CONFIG_PATH, PREDECLARATION_PATH)
    output = capsys.readouterr().out
    assert plan.total_cells == 198
    assert '"p0_1_grid_cells": 81' in output
    assert '"p0_1_latent_calls": 32' in output
    assert '"p0_1_observation_transforms": 248' in output
    assert '"total_latent_outbreak_calls": 59' in output
    assert '"total_observation_transforms": 599' in output


def test_objective_matches_hand_computation() -> None:
    target = ObservedTables(("2025-01-06",), (1.0,), (4.0,))
    candidate = ObservedTables(("2025-01-06",), (0.0,), (1.0,))
    expected = 0.5 * (
        (math.sqrt(1.0 + 3 / 8) - math.sqrt(0.0 + 3 / 8)) ** 2
        + (math.sqrt(4.0 + 3 / 8) - math.sqrt(1.0 + 3 / 8)) ** 2
    )
    assert minimum_distance_loss(target, (candidate, candidate, candidate)) == pytest.approx(
        expected
    )


def test_objective_averages_replicate_square_roots_before_loss() -> None:
    target = ObservedTables(("2025-01-06",), (4.0,), (4.0,))
    predictions = (
        ObservedTables(("2025-01-06",), (0.0,), (0.0,)),
        ObservedTables(("2025-01-06",), (1.0,), (1.0,)),
        ObservedTables(("2025-01-06",), (9.0,), (9.0,)),
    )
    mean_of_roots = sum(math.sqrt(value + 3 / 8) for value in (0.0, 1.0, 9.0)) / 3
    expected = (math.sqrt(4.0 + 3 / 8) - mean_of_roots) ** 2
    square_root_of_mean = (math.sqrt((0.0 + 1.0 + 9.0) / 3 + 3 / 8) - math.sqrt(4.0 + 3 / 8)) ** 2
    assert minimum_distance_loss(target, predictions) == pytest.approx(expected)
    assert expected != pytest.approx(square_root_of_mean)


def test_blind_fit_has_no_truth_interface_and_scores_all_cells() -> None:
    target, library = _prediction_library()
    fit = fit_blind(target, _config().candidate_grid, library)
    assert len(fit.loss_surface) == 81
    assert fit.selected == _config().candidate_grid[0]
    assert fit.numerical_tie is False
    assert len(fit.estimate_hash) == 64
    parameter_names = set(inspect.signature(fit_blind).parameters)
    assert not parameter_names & {
        "truth",
        "truth_metadata",
        "target_seed",
        "latent_events",
        "latent_hash",
    }
    assert "config" not in parameter_names


def test_complete_grid_enforcement_rejects_missing_cell() -> None:
    target, library = _prediction_library()
    grid = _config().candidate_grid
    with pytest.raises(ValueError, match="complete predeclared 81-cell"):
        fit_blind(target, grid[:-1], {cell: library[cell] for cell in grid[:-1]})
    with pytest.raises(ValueError, match="incomplete"):
        score_complete_grid(target, grid, {cell: library[cell] for cell in grid[:-1]})


def test_tie_is_explicitly_failed_and_near_flat_profile_is_not_identified() -> None:
    target, flat_library = _prediction_library(flat=True)
    tie = fit_blind(target, _config().candidate_grid, flat_library)
    assert tie.numerical_tie is True
    assert tie.selected is None
    assert tie.identified is False
    assert len(tie.global_minimizers) == 81

    _, near_library = _prediction_library(near_flat=True)
    near_target = ObservedTables(
        observation_dates(date(2025, 1, 6), 30, 4), (100.0,) * 34, (100.0,) * 34
    )
    near = fit_blind(near_target, _config().candidate_grid, near_library)
    assert near.numerical_tie is False
    assert near.selected == _config().candidate_grid[-1]
    assert near.identified is False
    assert any(not profile.identified for profile in near.profiles)


def test_channel_date_completeness_and_event_conversion() -> None:
    dates = observation_dates(date(2025, 1, 6), 3, 4)
    events = (
        {"report_date": dates[0], "symptomatic": True},
        {"report_date": dates[2], "symptomatic": False},
    )
    tables = observed_tables_from_events(events, dates=dates)
    assert tables.dates == dates
    assert tables.symptomatic == (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    assert tables.asymptomatic == (0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0)
    with pytest.raises(ValueError, match="outside"):
        observed_tables_from_events(
            ({"report_date": "2030-01-01", "symptomatic": True},), dates=dates
        )
    with pytest.raises(ValueError, match="complete"):
        ObservedTables(dates[:-1], (0.0,) * len(dates), (0.0,) * len(dates))
    validate_observation_calendar(
        tables=ObservedTables(observation_dates(date(2025, 1, 6), 30, 4), (0.0,) * 34, (0.0,) * 34),
        start_date=date(2025, 1, 6),
        duration_days=30,
        tail_days=4,
    )
    with pytest.raises(ValueError, match="fixed complete"):
        validate_observation_calendar(
            tables=ObservedTables(("2025-01-06",), (0.0,), (0.0,)),
            start_date=date(2025, 1, 6),
            duration_days=30,
            tail_days=4,
        )


def test_truth_diagnostics_and_chronology_failure_propagate() -> None:
    tables = ObservedTables(("2025-01-06", "2025-01-07", "2025-01-08"), (1, 0, 1), (0, 1, 1))
    events = tuple({"imported": True} for _ in range(10)) + ({"source_kind": "local"},)
    diagnostics = truth_diagnostics_from_events(
        events,
        tables,
        chronology_passed=False,
        latent_incidence_conservation_passed=True,
    )
    assert diagnostics.viable is False
    assert diagnostics.inoculation_acquisitions == 10
    assert diagnostics.nonzero_combined_report_dates == 3


def test_coverage_bias_boundary_and_joint_predicates_are_descriptive() -> None:
    truth = CandidateCell(0.08, 2, 0.75, 0.25)
    rows = tuple(
        RecoveryRow(
            target_seed=42001 + index,
            estimate_hash=f"{index + 1:064x}",
            selected=CandidateCell(0.12 if index else 0.08, 2, 0.75, 0.25),
            profiles=_identified_profiles(),
            numerical_tie=False,
            truth=truth,
            truth_diagnostics=_diagnostics(),
        )
        for index in range(5)
    )
    evaluation = evaluate_p01(rows)
    assert evaluation.coverage["beta"] == 1.0
    assert evaluation.bias["beta"] == pytest.approx(0.032)
    assert evaluation.boundary_counts["beta"] == 4
    assert evaluation.joint_coverage == 1.0
    assert evaluation.predicates["coverage_beta"] is True
    assert evaluation.predicates["bias_beta"] is False
    assert evaluation.predicates["boundary_beta"] is False
    assert evaluation.status == "FAIL"

    failed_truth = replace(rows[0], truth_diagnostics=_diagnostics(chronology=False))
    assert (
        evaluate_p01((failed_truth, *rows[1:])).predicates[
            "observation_chronology_and_conservation"
        ]
        is False
    )


def test_truth_is_joined_only_after_hashed_blind_estimate() -> None:
    target, library = _prediction_library()
    fit = fit_blind(target, _config().candidate_grid, library)
    row = join_truth_evaluation(
        fit,
        target_seed=42001,
        truth=CandidateCell(0.08, 2, 0.75, 0.25),
        truth_diagnostics=_diagnostics(),
    )
    assert row.estimate_hash == fit.estimate_hash
    assert row.signed_error("beta") == pytest.approx(-0.04)
    assert row.absolute_error("beta") == pytest.approx(0.04)


def test_budget_guard_rejects_mode_duration_overlap_and_retry() -> None:
    config = _config()
    with pytest.raises(BudgetError, match="forbidden"):
        guard_workload(config, retries=1)
    with pytest.raises(BudgetError, match="overlap"):
        guard_workload(
            replace(
                config,
                target_process_seeds=(FIT_PROCESS_SEEDS[0],) + config.target_process_seeds[1:],
            )
        )
    with pytest.raises(BudgetError, match="mode"):
        guard_workload(replace(config, mode="full"))
    with pytest.raises(BudgetError, match="duration"):
        guard_workload(replace(config, duration_days=31))
    oversized = replace(
        config,
        dimensions=(
            replace(config.dimensions[0], candidates=(0.04, 0.08, 0.12, 0.16)),
            *config.dimensions[1:],
        ),
    )
    with pytest.raises(BudgetError, match="81-cell"):
        guard_workload(oversized)


def test_execute_is_fail_closed_before_p0_2_and_p0_3() -> None:
    import jersey_outbreak.phase0_campaign as campaign

    with pytest.raises(CampaignBlockedError, match="p0_2a.*p0_2b.*p0_3"):
        campaign.execute_campaign(CONFIG_PATH, PREDECLARATION_PATH, Path("/tmp/unused-p0-1"))


def test_research_bundle_is_standalone_and_file_hashed(tmp_path: Path) -> None:
    output = write_research_bundle(
        tmp_path / "bundle",
        campaign_config_path=CONFIG_PATH,
        predeclaration_path=PREDECLARATION_PATH,
        seed_ledger=[{"role": "target", "process_seed": 42001}],
        candidate_loss_surfaces={"42001": [{"objective": None, "status": "not_run"}]},
        p01_recovery_rows=[{"status": "not_run", "estimate": None}],
        p02_misspecification_rows=[],
        p03_profile={"status": "not_run", "factor_estimate": None},
        campaign_summary={"status": "PASS", "calibration_claim": "forbidden"},
        input_hashes={"source_config": "a" * 64},
    )
    expected = {
        "campaign_config.yaml",
        "predeclaration.sha256",
        "seed_ledger.json",
        "candidate_loss_surfaces.json",
        "p0_1_recovery.csv",
        "p0_2_misspecification.csv",
        "p0_3_profile.json",
        "campaign_summary.json",
        "SHA256SUMS",
    }
    assert {path.name for path in output.iterdir()} == expected
    summary = (output / "campaign_summary.json").read_text(encoding="utf-8")
    assert '"status": "UNEXECUTED"' in summary
    assert '"calibration_claim": null' in summary
    assert "CalibrationArtifactManifest" not in summary
    sums = (output / "SHA256SUMS").read_text(encoding="utf-8")
    assert f"{sha256_file(output / 'campaign_config.yaml')}  campaign_config.yaml" in sums
    assert "SHA256SUMS  " not in sums
    for line in sums.splitlines():
        digest, name = line.split("  ", 1)
        assert sha256_file(output / name) == digest


def test_predeclaration_fixture_is_repository_relative_and_portable() -> None:
    assert sha256_file(REPOSITORY_PREDECLARATION_PATH) == PREDECLARATION_SHA256


@pytest.mark.parametrize(
    ("section", "key", "value"),
    (
        ("identifiability", "profile_gap", 0.10),
        ("acceptance", "descriptive_coverage_minimum", 1.0),
    ),
)
def test_changed_frozen_declaration_fields_are_rejected(
    tmp_path: Path, section: str, key: str, value: object
) -> None:
    payload = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    payload[section][key] = value
    changed = tmp_path / "changed.yaml"
    changed.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(CampaignError, match="frozen|declaration|profile|coverage"):
        CampaignConfig.from_yaml(changed)


def test_missing_workload_and_undeclared_target_seeds_cannot_pass() -> None:
    truth = CandidateCell(0.08, 2, 0.75, 0.25)
    rows = tuple(
        RecoveryRow(
            target_seed=42001 + index,
            estimate_hash=f"{index + 1:064x}",
            selected=truth,
            profiles=_identified_profiles(),
            numerical_tie=False,
            truth=truth,
            truth_diagnostics=replace(_diagnostics(), namespace_passed=True, complete=True),
            namespace_passed=True,
        )
        for index in range(5)
    )
    assert evaluate_p01(rows).status == "FAIL"
    evidence = ExecutionEvidence(
        target_process_seeds=(99901, 99902, 99903, 99904, 99905),
        target_observation_seeds=(52001, 52002, 52003, 52004, 52005),
        candidate_process_seeds=FIT_PROCESS_SEEDS,
        candidate_observation_seeds=(53001, 53002, 53003),
        target_observation_config_id="v13-phase0-target",
        candidate_observation_config_id="v13-phase0-fit",
        target_runs_complete=True,
        candidate_cells_complete=True,
        calendars_complete=True,
        configs_complete=True,
        namespaces_complete=True,
        measured_latent_calls=32,
        measured_observation_transforms=248,
    )
    assert (
        evaluate_p01(
            rows, config=_config(), workload=plan_workload(_config()), evidence=evidence
        ).status
        == "FAIL"
    )
    valid_evidence = replace(
        evidence,
        target_process_seeds=(42001, 42002, 42003, 42004, 42005),
    )
    assert (
        evaluate_p01(
            rows,
            config=_config(),
            workload=plan_workload(_config()),
            evidence=valid_evidence,
        ).status
        == "PASS"
    )


def test_candidate_provenance_hash_includes_constructed_declaration() -> None:
    cell = _config().candidate_grid[0]
    baseline = candidate_config_hash(cell, config=_config())
    changed = replace(_config(), reporting_delay_days=0)
    assert candidate_config_hash(cell, config=changed) != baseline


def test_research_bundle_rejects_nonempty_destination_without_mutation(
    tmp_path: Path,
) -> None:
    output = tmp_path / "bundle"
    output.mkdir()
    sentinel = output / "sentinel"
    sentinel.write_bytes(b"keep me")
    before = sentinel.read_bytes()
    with pytest.raises(CampaignError, match="nonempty"):
        write_research_bundle(
            output,
            campaign_config_path=CONFIG_PATH,
            predeclaration_path=REPOSITORY_PREDECLARATION_PATH,
            seed_ledger=[],
            candidate_loss_surfaces={},
        )
    assert sentinel.read_bytes() == before
    assert tuple(output.iterdir()) == (sentinel,)


def test_mocked_p01_path_persists_estimates_before_truth_join(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The generation path is callable under fakes but never runs in this test suite."""
    import jersey_outbreak.phase0_campaign as campaign

    calls: list[tuple[str, int, int | None]] = []

    class FakeConfig:
        def __init__(self, **values: object) -> None:
            self.__dict__.update(values)

        def model_copy(self, *, update: dict[str, object]) -> FakeConfig:
            values = dict(self.__dict__)
            values.update(update)
            return FakeConfig(**values)

        def model_dump(self, mode: str = "json") -> dict[str, object]:
            del mode
            return dict(self.__dict__)

    class FakeParameter:
        def __init__(self, value: float) -> None:
            self.value = value

        def model_copy(self, *, update: dict[str, object]) -> FakeParameter:
            result = FakeParameter(self.value)
            result.__dict__.update(update)
            return result

    class FakeParent:
        generated = object()

    class FakeLatent:
        logical_content_hash = "latent-hash"
        diagnostics = {
            "natural_history": {"chronology_passed": True},
            "states": {"conserved": True},
        }
        transmission_events = tuple([{"imported": True}] * 10 + [{"source_kind": "local"}])

    class FakeObserved:
        diagnostics = {
            "no_report_before_infection": True,
            "latent_incidence_conservation": True,
        }

        def __init__(self, observation_config: FakeConfig) -> None:
            self.observation_events = [
                {"report_date": "2025-01-06", "symptomatic": True},
                {"report_date": "2025-01-07", "symptomatic": False},
                {"report_date": "2025-01-08", "symptomatic": True},
            ]
            self.config = observation_config

    def fake_load_parameter_set(root: Path) -> object:
        calls.append(("load_parameters", 0, None))
        return object()

    def fake_load_observation_config(root: Path) -> FakeConfig:
        return FakeConfig(
            observation_config_id="observation-demo",
            observation_seed=0,
            parameters={
                "symptomatic_detection_probability": FakeParameter(0.75),
                "asymptomatic_detection_probability": FakeParameter(0.25),
            },
            reporting_delay=FakeConfig(kind="fixed", days=(2,)),
            detection_delay=FakeConfig(kind="fixed", days=(0,)),
            analysis_horizon_tail_days=None,
            day_of_week_effect=(1.0,) * 7,
            model_marker="observation",
        )

    def fake_default_run_config(
        mode: str, seed: int, parameters: object, **kwargs: object
    ) -> FakeConfig:
        del parameters
        return FakeConfig(
            mode=mode,
            seed=seed,
            initial_seed_count=10,
            import_schedule={},
            import_rate_per_day=0.0,
            beta=0.08,
            symptomatic_probability=0.6,
            waning_enabled=False,
            latent_duration=FakeConfig(family="constant", mean_days=2.0),
            infectious_duration=FakeConfig(family="constant", mean_days=5.0),
            route_multipliers={
                "household": 1.0,
                "school_class": 1.0,
                "school_cross_class": 1.0,
                "workplace_team": 1.0,
                "workplace_transient": 1.0,
                "care_resident": 1.0,
                "care_staff": 1.0,
                "shared_vehicle": 1.0,
                "bus": 1.0,
                "community_indoor": 1.0,
                "community_outdoor": 1.0,
            },
            **kwargs,
        )

    def fake_build_parent(
        root: Path, mode: str, seed: int, destination: Path, **kwargs: object
    ) -> FakeParent:
        del root, mode, destination, kwargs
        calls.append(("build_parent", seed, None))
        return FakeParent()

    def fake_run_outbreak(parent: object, run_config: FakeConfig, parameters: object) -> FakeLatent:
        del parent, parameters
        calls.append(("run_outbreak", run_config.seed, None))
        return FakeLatent()

    def fake_observe(latent: FakeLatent, observation_config: FakeConfig) -> FakeObserved:
        del latent
        calls.append(
            (
                "observe",
                observation_config.observation_seed,
                observation_config.observation_config_id,
            )
        )
        return FakeObserved(observation_config)

    original_persist = campaign.persist_blind_estimate
    original_fit = campaign.fit_blind

    def recording_persist(path: Path, fit: object) -> str:
        calls.append(("persist", int(path.stem), None))
        return original_persist(path, fit)  # type: ignore[arg-type]

    def recording_fit(*args: object, **kwargs: object) -> object:
        calls.append(("fit_blind", len(args[1]), None))
        return original_fit(*args, **kwargs)  # type: ignore[arg-type]

    original_join = campaign.join_truth_evaluation

    def recording_join(*args: object, **kwargs: object) -> RecoveryRow:
        calls.append(("join", int(kwargs["target_seed"]), None))
        return original_join(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(campaign, "load_parameter_set", fake_load_parameter_set)
    monkeypatch.setattr(campaign, "load_observation_config", fake_load_observation_config)
    monkeypatch.setattr(campaign, "default_run_config", fake_default_run_config)
    monkeypatch.setattr(campaign, "build_parent", fake_build_parent)
    monkeypatch.setattr(campaign, "run_outbreak", fake_run_outbreak)
    monkeypatch.setattr(campaign, "observe_latent_run", fake_observe)
    monkeypatch.setattr(campaign, "persist_blind_estimate", recording_persist)
    monkeypatch.setattr(campaign, "fit_blind", recording_fit)
    monkeypatch.setattr(campaign, "join_truth_evaluation", recording_join)

    result = run_p01_campaign(
        CONFIG_PATH,
        REPOSITORY_PREDECLARATION_PATH,
        tmp_path / "campaign-work",
    )
    assert len(result.target_tables) == 5
    assert len(result.candidate_prediction_library) == 81
    assert result.execution_evidence.measured_latent_calls == 32
    assert result.execution_evidence.measured_observation_transforms == 248
    assert sum(kind == "build_parent" for kind, _, _ in calls) == 8
    assert sum(kind == "run_outbreak" for kind, _, _ in calls) == 32
    assert sum(kind == "observe" for kind, _, _ in calls) == 248
    assert sum(kind == "persist" for kind, _, _ in calls) == 5
    assert sum(kind == "fit_blind" for kind, _, _ in calls) == 5
    assert {count for kind, count, _ in calls if kind == "fit_blind"} == {81}
    assert {seed for kind, seed, _ in calls if kind == "build_parent"} == {
        42001,
        42002,
        42003,
        42004,
        42005,
        43001,
        43002,
        43003,
    }
    assert {namespace for kind, _, namespace in calls if kind == "observe"} == {
        "v13-phase0-target",
        "v13-phase0-fit",
    }
    assert {seed for kind, seed, _ in calls if kind == "observe"} == {
        52001,
        52002,
        52003,
        52004,
        52005,
        53001,
        53002,
        53003,
    }
    first_join = next(index for index, call in enumerate(calls) if call[0] == "join")
    assert all(call[0] != "join" for call in calls[:first_join])

    def fail_persist(path: Path, fit: object) -> str:
        del path, fit
        raise CampaignError("forced estimate persistence failure")

    monkeypatch.setattr(campaign, "persist_blind_estimate", fail_persist)
    calls.clear()
    with pytest.raises(CampaignError, match="forced estimate persistence failure"):
        run_p01_campaign(
            CONFIG_PATH,
            REPOSITORY_PREDECLARATION_PATH,
            tmp_path / "failed-campaign-work",
        )
    assert not any(call[0] == "join" for call in calls)
