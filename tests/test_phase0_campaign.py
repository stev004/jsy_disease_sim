from __future__ import annotations

import inspect
import math
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from jersey_outbreak.phase0_campaign import (
    FIT_PROCESS_SEEDS,
    PREDECLARATION_SHA256,
    BudgetError,
    CampaignBlockedError,
    CampaignConfig,
    CandidateCell,
    ObservedTables,
    ProfileDiagnostic,
    RecoveryRow,
    TruthDiagnostics,
    dry_run,
    evaluate_p01,
    fit_blind,
    guard_workload,
    join_truth_evaluation,
    minimum_distance_loss,
    observation_dates,
    observed_tables_from_events,
    plan_workload,
    score_complete_grid,
    sha256_file,
    truth_diagnostics_from_events,
    validate_observation_calendar,
    write_research_bundle,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "calibration" / "v13_phase0_synthetic.yaml"
PREDECLARATION_PATH = Path("/home/steven/jos-p0-predeclaration.md")


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
