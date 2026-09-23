from __future__ import annotations

import csv
import hashlib
import inspect
import json
import math
from dataclasses import replace
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from jersey_outbreak.observation_scheduler import observation_stream_seed
from jersey_outbreak.observation_schemas import ObservationConfig
from jersey_outbreak.outbreak_runner import load_parameter_set
from jersey_outbreak.outbreak_schemas import OutbreakRunConfig
from jersey_outbreak.phase0_campaign import (
    FIT_PROCESS_SEEDS,
    PREDECLARATION_SHA256,
    BlindFitResult,
    BudgetError,
    CampaignBlockedError,
    CampaignConfig,
    CampaignError,
    CandidateCell,
    ExecutionEvidence,
    LossRow,
    ObservedTables,
    P02TargetResult,
    ProfileDiagnostic,
    RecoveryRow,
    TruthDiagnostics,
    aggregate_p02_detection,
    candidate_config_hash,
    dry_run,
    evaluate_p01,
    evaluate_p02_target,
    fit_blind,
    guard_workload,
    join_truth_evaluation,
    minimum_distance_loss,
    observation_dates,
    observed_tables_from_events,
    plan_workload,
    run_p01_campaign,
    run_p02_campaign,
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


def _test_ruling_config(tmp_path: Path) -> tuple[Path, Path]:
    ruling = tmp_path / "accepted-ruling-fixture.md"
    ruling.write_text("test-only accepted G29 ruling fixture\n", encoding="utf-8")
    payload = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    payload["g29_ruling_sha256"] = hashlib.sha256(ruling.read_bytes()).hexdigest()
    config_path = tmp_path / "test-only-config.yaml"
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return config_path, ruling


def test_namespace_evidence_requires_returned_metadata() -> None:
    import jersey_outbreak.phase0_campaign as campaign

    config = _config()
    parameters = load_parameter_set(ROOT)
    cell = config.candidate_grid[0]
    run_config = campaign._run_config_for_cell(config, parameters, 43001, cell)
    observation_config = campaign._observation_config_for_cell(
        ROOT, config, 53001, config.candidate_observation_config_id, cell
    )
    latent_result = SimpleNamespace(config=run_config)
    observation_rng = {
        "stream_namespace": "observation",
        "stream_key_inputs": [
            "latent_replicate_seed",
            "observation_seed",
            "observation_config_id",
        ],
        "stream_fingerprint": hashlib.sha256(
            str(observation_stream_seed(run_config.seed, observation_config)).encode()
        ).hexdigest(),
    }
    valid_observation_result = SimpleNamespace(
        latent_run=latent_result,
        config=observation_config,
        diagnostics={"observation_rng": observation_rng},
    )
    mismatched_observation_result = SimpleNamespace(
        latent_run=latent_result,
        config=observation_config.model_copy(update={"observation_seed": 53002}),
        diagnostics={"observation_rng": observation_rng},
    )

    cases = (
        ("missing result metadata", object(), object(), False),
        (
            "missing RNG diagnostics",
            latent_result,
            SimpleNamespace(latent_run=latent_result, config=observation_config, diagnostics={}),
            False,
        ),
        (
            "mismatched result metadata",
            latent_result,
            mismatched_observation_result,
            False,
        ),
        ("valid result metadata", latent_result, valid_observation_result, True),
    )
    for label, returned_latent, returned_observation, expected in cases:
        assert (
            campaign._namespace_passes(
                returned_latent, returned_observation, run_config, observation_config
            )
            is expected
        ), label


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


def _p02_fit(minimum: float, cells: tuple[CandidateCell, ...], *, tied: bool) -> BlindFitResult:
    return BlindFitResult(
        loss_surface=tuple(LossRow(cell, minimum) for cell in cells),
        minimum_objective=minimum,
        global_minimizers=cells,
        numerical_tie=tied,
        tie_tolerance=1e-12 * max(1.0, minimum),
        selected=None if tied else cells[0],
        profiles=(),
        identified=not tied,
        estimate_hash="a" * 64,
    )


def _p02_target_state(arm: str, state: str, target_seed: int = 42001) -> P02TargetResult:
    cell = CandidateCell(0.08, 2, 0.75, 0.25)
    return P02TargetResult(
        arm=arm,  # type: ignore[arg-type]
        target_seed=target_seed,
        estimate_hash="b" * 64,
        minimum_objective=1.0,
        correct_minimum_objective=1.0,
        relative_loss_degradation=0.0,
        selected=cell,
        global_minimizers=(cell,),
        numerical_tie=False,
        channel_total_error=0.0,
        clauses={},
        dimension_errors={},
        detection_state=state,  # type: ignore[arg-type]
    )


def _p02_states(arm: str, states: tuple[str, ...]) -> tuple[P02TargetResult, ...]:
    return tuple(_p02_target_state(arm, state, 42001 + index) for index, state in enumerate(states))


def _leaf_differences(left: object, right: object, prefix: str = "") -> set[str]:
    if isinstance(left, dict) and isinstance(right, dict):
        assert left.keys() == right.keys()
        return set().union(
            *(
                _leaf_differences(left[key], right[key], f"{prefix}.{key}" if prefix else key)
                for key in left
            )
        )
    if isinstance(left, list) and isinstance(right, list):
        assert len(left) == len(right)
        return set().union(
            *(
                _leaf_differences(a, b, f"{prefix}[{index}]")
                for index, (a, b) in enumerate(zip(left, right, strict=True))
            )
        )
    return set() if left == right else {prefix}


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
    assert config.g29_ruling_path == "docs/research/v1_3/2026-09-23-g29-p02-tie-ruling-ACCEPTED.md"
    assert config.g29_ruling_sha256 == (
        "06e49aaa7f21564dd6f525941633054fad39cf6714aa74aec0ef1f12dc1eb70c"
    )
    assert config.implemented_arms == ("p0_1", "p0_2a", "p0_2b")
    assert plan.implemented_cells == 189
    assert plan.implemented_latent_calls == 32
    assert plan.implemented_observation_transforms == 572
    assert plan.p02_wrong_delay_cells == 81
    assert plan.p02_wrong_regime_cells == 27
    assert plan.total_cells == 198
    assert plan.total_latent_calls == 59
    assert plan.total_observation_transforms == 599


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
    assert '"implemented_arms": [' in output
    assert '"implemented_grid_cells": 189' in output
    assert '"implemented_p0_2a_grid_cells": 81' in output
    assert '"implemented_p0_2b_grid_cells": 27' in output
    assert '"planned_p0_3_grid_cells": 9' in output
    assert '"implemented_latent_outbreak_calls": 32' in output
    assert '"implemented_observation_transforms": 572' in output
    assert '"g29_ruling_verified": false' in output


def test_p0_2_ruling_hash_is_optional_for_dry_run_and_verified_when_supplied(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import jersey_outbreak.phase0_campaign as campaign

    config_path, ruling_path = _test_ruling_config(tmp_path)
    campaign.dry_run(config_path, PREDECLARATION_PATH, ruling_path)
    output = capsys.readouterr().out
    assert hashlib.sha256(ruling_path.read_bytes()).hexdigest() in output
    assert '"g29_ruling_verified": true' in output

    wrong = tmp_path / "wrong-ruling.md"
    wrong.write_text("wrong ruling\n", encoding="utf-8")
    with pytest.raises(CampaignError, match="G29 ruling SHA-256 mismatch"):
        campaign.dry_run(config_path, PREDECLARATION_PATH, wrong)


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


def test_p0_2_grids_and_common_probability_cells_are_exact() -> None:
    from jersey_outbreak.phase0_campaign import (
        G29_RULING_PATH,
        G29_RULING_SHA256,
        _p02b_grid,
        fit_p02_blind,
    )

    config = _config()
    grid_b = _p02b_grid(config)
    assert len(config.candidate_grid) == 81
    assert len(grid_b) == 27
    assert {cell.symptomatic_detection_probability for cell in grid_b} == {0.25, 0.50, 0.75}
    assert all(
        cell.symptomatic_detection_probability == cell.asymptomatic_detection_probability
        for cell in grid_b
    )
    assert G29_RULING_PATH == config.g29_ruling_path
    assert G29_RULING_SHA256 == config.g29_ruling_sha256
    assert not set(inspect.signature(fit_p02_blind).parameters) & {
        "truth",
        "target_seed",
        "latent_events",
        "latent_hash",
        "target_latents",
    }


def test_p0_2_detection_quantities_use_declared_floors_and_inclusive_boundaries() -> None:
    config = _config()
    target = ObservedTables(("2025-01-06",), (4.0,), (4.0,))
    selected = CandidateCell(0.08, 2, 0.50, 0.50)
    candidate_prediction = ObservedTables(("2025-01-06",), (5.0,), (4.0,))
    fit = _p02_fit(1.25, (selected,), tied=False)
    result = evaluate_p02_target(
        "p0_2b",
        target_seed=42001,
        correct_minimum_objective=1.0,
        wrong_fit=fit,
        target_tables=target,
        wrong_candidate_prediction_library={selected: (candidate_prediction,) * 3},
        truth=CandidateCell(0.08, 2, 0.75, 0.25),
        config=config,
    )
    assert result.relative_loss_degradation == 0.25
    assert result.channel_total_error == 0.25
    assert result.clauses["relative_loss_degradation_at_least_0_25"] is True
    assert result.clauses["channel_total_error_at_least_0_25"] is True
    assert result.detection_state == "TRUE"

    zero_target = ObservedTables(("2025-01-06",), (0.0,), (0.0,))
    floor_prediction = ObservedTables(("2025-01-06",), (0.25,), (0.0,))
    floor_e = evaluate_p02_target(
        "p0_2b",
        target_seed=42001,
        correct_minimum_objective=0.1,
        wrong_fit=_p02_fit(0.1, (selected,), tied=False),
        target_tables=zero_target,
        wrong_candidate_prediction_library={selected: (floor_prediction,) * 3},
        truth=CandidateCell(0.08, 2, 0.75, 0.25),
        config=config,
    )
    assert floor_e.channel_total_error == 0.25
    assert floor_e.clauses["channel_total_error_at_least_0_25"] is True

    tied = (selected, CandidateCell(0.12, 4, 0.75, 0.25))
    floor_r = evaluate_p02_target(
        "p0_2b",
        target_seed=42001,
        correct_minimum_objective=0.0,
        wrong_fit=_p02_fit(2.5e-10, tied, tied=True),
        target_tables=zero_target,
        wrong_candidate_prediction_library={},
        truth=CandidateCell(0.08, 2, 0.75, 0.25),
        config=config,
    )
    assert floor_r.relative_loss_degradation == 0.25
    assert floor_r.channel_total_error is None
    assert floor_r.detection_state == "TRUE"
    assert floor_r.clauses["relative_loss_degradation_at_least_0_25"] is True
    tie_record = floor_r.as_dict()
    assert tie_record["selected_estimates"] == "null"
    assert tie_record["E_i"] is None


def test_p0_2_g29_worked_tie_examples_and_aggregates() -> None:
    config = _config()
    truth = CandidateCell(0.08, 2, 0.75, 0.25)
    tied_cells = (truth, CandidateCell(0.12, 4, 0.75, 0.25))
    target = _tables(0.0)

    resolved = evaluate_p02_target(
        "p0_2a",
        target_seed=42001,
        correct_minimum_objective=1.0,
        wrong_fit=_p02_fit(1.3, tied_cells, tied=True),
        target_tables=target,
        wrong_candidate_prediction_library={},
        truth=truth,
        config=config,
    )
    assert resolved.relative_loss_degradation == pytest.approx(0.30)
    assert resolved.detection_state == "TRUE"
    assert resolved.selected is None

    unresolved_a = evaluate_p02_target(
        "p0_2a",
        target_seed=42001,
        correct_minimum_objective=1.0,
        wrong_fit=_p02_fit(1.1, tied_cells, tied=True),
        target_tables=target,
        wrong_candidate_prediction_library={},
        truth=truth,
        config=config,
    )
    assert unresolved_a.relative_loss_degradation < 0.25
    assert unresolved_a.detection_state == "UNKNOWN"
    assert all(value is None for value in unresolved_a.dimension_errors["beta"].values())

    unresolved_b = evaluate_p02_target(
        "p0_2b",
        target_seed=42001,
        correct_minimum_objective=2.0,
        wrong_fit=_p02_fit(2.2, tied_cells, tied=True),
        target_tables=target,
        wrong_candidate_prediction_library={},
        truth=truth,
        config=config,
    )
    assert unresolved_b.relative_loss_degradation < 0.25
    assert unresolved_b.channel_total_error is None
    assert unresolved_b.detection_state == "UNKNOWN"

    states_b = _p02_states("p0_2b", ("TRUE", "TRUE", "TRUE", "FALSE", "UNKNOWN"))
    status, reason, detected, unknown, attainable = aggregate_p02_detection(states_b, arm="p0_2b")
    assert (status, reason, detected, unknown, attainable) == (
        None,
        "indeterminate_tied_minima",
        3,
        1,
        (3, 4),
    )

    pass_a, _, d_a, u_a, interval_a = aggregate_p02_detection(
        _p02_states("p0_2a", ("TRUE", "TRUE", "TRUE", "FALSE", "FALSE")),
        arm="p0_2a",
    )
    fail_a, _, d_fail_a, u_fail_a, interval_fail_a = aggregate_p02_detection(
        _p02_states("p0_2a", ("TRUE", "TRUE", "FALSE", "FALSE", "FALSE")),
        arm="p0_2a",
    )
    pass_b, _, d_b, u_b, interval_b = aggregate_p02_detection(
        _p02_states("p0_2b", ("TRUE", "TRUE", "TRUE", "TRUE", "FALSE")),
        arm="p0_2b",
    )
    fail_b, _, d_fail_b, u_fail_b, interval_fail_b = aggregate_p02_detection(
        _p02_states("p0_2b", ("TRUE", "TRUE", "TRUE", "FALSE", "FALSE")),
        arm="p0_2b",
    )
    assert (pass_a, d_a, u_a, interval_a) == ("PASS", 3, 0, (3, 3))
    assert (fail_a, d_fail_a, u_fail_a, interval_fail_a) == ("FAIL", 2, 0, (2, 2))
    assert (pass_b, d_b, u_b, interval_b) == ("PASS", 4, 0, (4, 4))
    assert (fail_b, d_fail_b, u_fail_b, interval_fail_b) == ("FAIL", 3, 0, (3, 3))
    with pytest.raises(CampaignError, match="fixed five targets"):
        aggregate_p02_detection(
            (_p02_target_state("p0_2b", "TRUE"),) * 5,
            arm="p0_2b",
        )


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


@pytest.mark.parametrize(
    ("dimension", "endpoint", "tolerance"),
    (
        ("beta", 0.04, 0.04),
        ("beta", 0.12, 0.04),
        ("inoculation_day_offset", 0, 2.0),
        ("inoculation_day_offset", 4, 2.0),
        ("symptomatic_detection_probability", 0.50, 0.25),
        ("symptomatic_detection_probability", 1.00, 0.25),
        ("asymptomatic_detection_probability", 0.10, 0.15),
        ("asymptomatic_detection_probability", 0.40, 0.15),
    ),
)
def test_recovery_tolerance_is_inclusive_at_both_frozen_grid_endpoints(
    dimension: str, endpoint: float | int, tolerance: float
) -> None:
    truth = CandidateCell(0.08, 2, 0.75, 0.25)
    endpoint_selection = replace(truth, **{dimension: endpoint})
    rows = tuple(
        RecoveryRow(
            target_seed=42001 + index,
            estimate_hash=f"{index + 1:064x}",
            selected=endpoint_selection if index == 0 else truth,
            profiles=_identified_profiles(),
            numerical_tie=False,
            truth=truth,
            truth_diagnostics=_diagnostics(),
        )
        for index in range(5)
    )

    evaluation = evaluate_p01(rows)
    endpoint_row = next(
        row
        for row in evaluation.rows
        if row["target_seed"] == 42001 and row["dimension"] == dimension
    )
    assert endpoint_row["absolute_error"] == tolerance
    assert evaluation.coverage[dimension] == 1.0
    assert evaluation.joint_coverage == 1.0


def test_asymptomatic_upper_endpoint_preserves_marginal_and_joint_coverage() -> None:
    truth = CandidateCell(0.08, 2, 0.75, 0.25)
    rows = tuple(
        RecoveryRow(
            target_seed=42001 + index,
            estimate_hash=f"{index + 1:064x}",
            selected=replace(
                truth,
                asymptomatic_detection_probability=0.40 if index == 0 else 0.25,
            ),
            profiles=_identified_profiles(),
            numerical_tie=False,
            truth=truth,
            truth_diagnostics=_diagnostics(),
        )
        for index in range(5)
    )

    evaluation = evaluate_p01(rows)
    assert evaluation.coverage["asymptomatic_detection_probability"] == 1.0
    assert evaluation.joint_coverage == 1.0


def test_three_of_five_joint_hit_boundary_counts_inclusive_upper_endpoint() -> None:
    truth = CandidateCell(0.08, 2, 0.75, 0.25)
    not_identified = tuple(replace(profile, identified=False) for profile in _identified_profiles())
    rows = tuple(
        RecoveryRow(
            target_seed=42001 + index,
            estimate_hash=f"{index + 1:064x}",
            selected=replace(
                truth,
                asymptomatic_detection_probability=0.40 if index == 0 else 0.25,
            ),
            profiles=_identified_profiles() if index < 3 else not_identified,
            numerical_tie=False,
            truth=truth,
            truth_diagnostics=_diagnostics(),
        )
        for index in range(5)
    )

    evaluation = evaluate_p01(rows)
    assert evaluation.joint_coverage == 3 / 5
    assert evaluation.predicates["joint_coverage_at_least_3_of_5"] is True


def test_declared_decimal_asymptomatic_bias_cancellation_is_exact() -> None:
    truth = CandidateCell(0.08, 2, 0.75, 0.25)
    asymptomatic_values = (0.40, 0.10, 0.25, 0.25, 0.25)
    rows = tuple(
        RecoveryRow(
            target_seed=42001 + index,
            estimate_hash=f"{index + 1:064x}",
            selected=replace(
                truth,
                asymptomatic_detection_probability=asymptomatic_values[index],
            ),
            profiles=_identified_profiles(),
            numerical_tie=False,
            truth=truth,
            truth_diagnostics=_diagnostics(),
        )
        for index in range(5)
    )

    evaluation = evaluate_p01(rows)
    asymptomatic_rows = [
        row for row in evaluation.rows if row["dimension"] == "asymptomatic_detection_probability"
    ]
    assert [row["signed_error"] for row in asymptomatic_rows] == [0.15, -0.15, 0.0, 0.0, 0.0]
    assert evaluation.bias["asymptomatic_detection_probability"] == 0.0
    assert evaluation.predicates["bias_asymptomatic_detection_probability"] is True


def test_recovery_arithmetic_preserves_blind_and_declaration_hashes() -> None:
    config = _config()
    cell = config.candidate_grid[0]
    target, library = _prediction_library()
    fit = fit_blind(target, config.candidate_grid, library)

    assert config.expected_predeclaration_sha256 == PREDECLARATION_SHA256
    assert candidate_config_hash(cell, config=config) == (
        "d3a536deb456c471baaaecec59bfd8854483cb288f96f3df22828535a26f71d0"
    )
    assert fit.estimate_hash == "2ebc1f18a5dac62ec1432fc696e8c885c63cd53e818b8d8fbce0bcf7dad7421a"


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


def test_execute_is_fail_closed_before_p0_3(tmp_path: Path) -> None:
    import jersey_outbreak.phase0_campaign as campaign

    with pytest.raises(CampaignError, match="requires a verified G29 ruling"):
        campaign.execute_campaign(CONFIG_PATH, PREDECLARATION_PATH, Path("/tmp/unused-p0-1"))
    config_path, ruling_path = _test_ruling_config(tmp_path)
    with pytest.raises(CampaignBlockedError, match="p0_3"):
        campaign.execute_campaign(
            config_path, PREDECLARATION_PATH, Path("/tmp/unused-p0-2"), ruling_path
        )


def test_research_bundle_is_standalone_and_file_hashed(tmp_path: Path) -> None:
    config_path, ruling_path = _test_ruling_config(tmp_path)
    output = write_research_bundle(
        tmp_path / "bundle",
        campaign_config_path=config_path,
        predeclaration_path=PREDECLARATION_PATH,
        ruling_path=ruling_path,
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
        "g29_ruling.md",
        "g29_ruling.sha256",
        "seed_ledger.json",
        "candidate_loss_surfaces.json",
        "p0_2_loss_surfaces.json",
        "p0_2_provenance.json",
        "p0_1_recovery.csv",
        "p0_2_misspecification.csv",
        "p0_3_profile.json",
        "campaign_summary.json",
        "SHA256SUMS",
    }
    assert {path.name for path in output.iterdir()} == expected
    summary = (output / "campaign_summary.json").read_text(encoding="utf-8")
    assert '"status": "UNEXECUTED"' in summary
    assert '"g29_ruling_verified": true' in summary
    assert hashlib.sha256(ruling_path.read_bytes()).hexdigest() in summary
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
    missing_namespace_evidence = replace(valid_evidence, namespaces_complete=False)
    failed_namespace_evaluation = evaluate_p01(
        rows,
        config=_config(),
        workload=plan_workload(_config()),
        evidence=missing_namespace_evidence,
    )
    assert failed_namespace_evaluation.status == "FAIL"
    assert (
        failed_namespace_evaluation.predicates[
            "declared_namespace_grid_objective_dates_fixed_parameters"
        ]
        is False
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
    with pytest.raises(CampaignError, match="empty before writing"):
        write_research_bundle(
            output,
            campaign_config_path=CONFIG_PATH,
            predeclaration_path=REPOSITORY_PREDECLARATION_PATH,
            seed_ledger=[],
            candidate_loss_surfaces={},
        )
    assert sentinel.read_bytes() == before
    assert tuple(output.iterdir()) == (sentinel,)


def test_p0_1_and_p0_2_mocked_paths_reuse_latents_and_persist_blind_estimates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The generation path is callable under fakes but never runs in this test suite."""
    import jersey_outbreak.phase0_campaign as campaign

    calls: list[tuple[str, int, object | None]] = []
    run_configs: list[OutbreakRunConfig] = []
    observation_configs: list[ObservationConfig] = []
    fit_inputs: list[tuple[tuple[object, ...], dict[str, object]]] = []

    class FakeParent:
        generated = object()

    class FakeLatent:
        logical_content_hash = "latent-hash"
        diagnostics = {
            "natural_history": {"chronology_passed": True},
            "states": {"conserved": True},
        }
        transmission_events = tuple([{"imported": True}] * 10 + [{"source_kind": "local"}])

        def __init__(self, run_config: OutbreakRunConfig) -> None:
            self.config = run_config

    class FakeObserved:
        diagnostics = {
            "no_report_before_infection": True,
            "latent_incidence_conservation": True,
        }

        def __init__(self, latent_run: FakeLatent, observation_config: ObservationConfig) -> None:
            self.observation_events = [
                {"report_date": "2025-01-06", "symptomatic": True},
                {"report_date": "2025-01-07", "symptomatic": False},
                {"report_date": "2025-01-08", "symptomatic": True},
            ]
            self.latent_run = latent_run
            self.config = observation_config

    def fake_build_parent(
        root: Path, mode: str, seed: int, destination: Path, **kwargs: object
    ) -> FakeParent:
        del root, mode, destination, kwargs
        calls.append(("build_parent", seed, None))
        return FakeParent()

    def fake_run_outbreak(
        parent: object, run_config: OutbreakRunConfig, parameters: object
    ) -> FakeLatent:
        del parent, parameters
        calls.append(("run_outbreak", run_config.seed, None))
        run_configs.append(run_config)
        return FakeLatent(run_config)

    def fake_observe(latent: FakeLatent, observation_config: ObservationConfig) -> FakeObserved:
        calls.append(
            (
                "observe",
                observation_config.observation_seed,
                observation_config.observation_config_id,
            )
        )
        observation_configs.append(observation_config)
        result = FakeObserved(latent, observation_config)
        result.diagnostics = {
            "no_report_before_infection": True,
            "latent_incidence_conservation": True,
            "observation_rng": {
                "stream_namespace": "observation",
                "stream_key_inputs": [
                    "latent_replicate_seed",
                    "observation_seed",
                    "observation_config_id",
                ],
                "stream_fingerprint": hashlib.sha256(
                    str(observation_stream_seed(latent.config.seed, observation_config)).encode()
                ).hexdigest(),
            },
        }
        return result

    original_persist = campaign.persist_blind_estimate
    original_fit = campaign.fit_blind

    def recording_persist(path: Path, fit: object) -> str:
        calls.append(("persist", int(path.stem), None))
        return original_persist(path, fit)  # type: ignore[arg-type]

    def recording_fit(*args: object, **kwargs: object) -> object:
        calls.append(("fit_blind", len(args[1]), None))
        fit_inputs.append((args, kwargs))
        return original_fit(*args, **kwargs)  # type: ignore[arg-type]

    original_join = campaign.join_truth_evaluation

    def recording_join(*args: object, **kwargs: object) -> RecoveryRow:
        calls.append(("join", int(kwargs["target_seed"]), None))
        return original_join(*args, **kwargs)  # type: ignore[arg-type]

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
    config = result.config
    with pytest.raises(CampaignError, match="retained candidate latent cache"):
        run_p02_campaign(
            replace(result, candidate_latents={}),
            tmp_path / "p02-missing-cache",
            root=ROOT,
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
    assert all(isinstance(item, OutbreakRunConfig) for item in run_configs)
    assert all(isinstance(item, ObservationConfig) for item in observation_configs)
    assert [item.seed for item in run_configs] == [
        42001,
        42002,
        42003,
        42004,
        42005,
        *[seed for seed in (43001, 43002, 43003) for _ in range(9)],
    ]
    assert [item.observation_seed for item in observation_configs] == [
        52001,
        52002,
        52003,
        52004,
        52005,
        *[seed for _ in range(81) for seed in (53001, 53002, 53003)],
    ]
    assert [item.observation_config_id for item in observation_configs] == [
        *(["v13-phase0-target"] * 5),
        *(["v13-phase0-fit"] * 243),
    ]
    assert all(item.mode == "ci" for item in run_configs)
    assert all(item.start_date == date(2025, 1, 6) for item in run_configs)
    assert all(item.duration_days == 30 for item in run_configs)
    assert all(item.analysis_horizon_tail_days == 4 for item in observation_configs)
    expected_dates = observation_dates(date(2025, 1, 6), 30, 4)
    assert all(table.dates == expected_dates for table in result.target_tables.values())
    assert all(
        table.dates == expected_dates
        for tables in result.candidate_prediction_library.values()
        for table in tables
    )
    assert len(fit_inputs) == 5
    assert all(
        len(args) == 3
        and all(not isinstance(value, CampaignConfig) for value in args)
        and set(kwargs) == {"candidate_config_hashes"}
        and all(not isinstance(value, CampaignConfig) for value in kwargs.values())
        for args, kwargs in fit_inputs
    )
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
    persist_positions = {
        count: index for index, (kind, count, _) in enumerate(calls) if kind == "persist"
    }
    join_positions = {
        count: index for index, (kind, count, _) in enumerate(calls) if kind == "join"
    }
    assert set(persist_positions) == {42001, 42002, 42003, 42004, 42005}
    assert set(join_positions) == set(persist_positions)
    assert all(persist_positions[seed] < join_positions[seed] for seed in persist_positions)

    p01_observation_configs = tuple(observation_configs)
    latent_calls_before_p02 = sum(kind == "run_outbreak" for kind, _, _ in calls)
    observation_calls_before_p02 = sum(kind == "observe" for kind, _, _ in calls)
    p02_result = run_p02_campaign(result, tmp_path / "p02-work", root=ROOT)
    assert set(result.candidate_latents) == {
        (seed, beta, offset)
        for seed in config.candidate_process_seeds
        for beta in config.dimension_map["beta"].candidates
        for offset in config.dimension_map["inoculation_day_offset"].candidates
    }
    assert sum(kind == "run_outbreak" for kind, _, _ in calls) == latent_calls_before_p02
    assert sum(kind == "observe" for kind, _, _ in calls) - observation_calls_before_p02 == 324
    assert observation_calls_before_p02 + 324 == 572
    assert len(observation_configs) - len(p01_observation_configs) == 324
    assert p02_result.software_status == "PASS"
    assert p02_result.misspecification_detection is None
    assert p02_result.arms["p0_2a"].measured_latent_calls == 0
    assert p02_result.arms["p0_2b"].measured_latent_calls == 0
    assert p02_result.arms["p0_2a"].measured_observation_transforms == 243
    assert p02_result.arms["p0_2b"].measured_observation_transforms == 81
    assert len(p02_result.reused_p01_target_provenance) == 5
    assert all(
        len(record["target_config_sha256"]) == 64
        and len(record["target_observation_table_sha256"]) == 64
        and len(record["observation_rng_fingerprint"]) == 64
        and record["namespace_verified"] is True
        for record in p02_result.reused_p01_target_provenance.values()
    )
    assert len(p02_result.arms["p0_2a"].candidate_prediction_library) == 81
    assert len(p02_result.arms["p0_2b"].candidate_prediction_library) == 27
    assert (
        sum(len(arm.candidate_prediction_library) for arm in p02_result.arms.values()) + 81 == 189
    )

    def payload(config: ObservationConfig) -> dict[str, object]:
        return config.model_dump(mode="json")

    p02a_configs = observation_configs[248:491]
    assert len(p02a_configs) == 243
    for p01_config, wrong_config in zip(p01_observation_configs[5:], p02a_configs, strict=True):
        assert wrong_config.observation_config_id == p01_config.observation_config_id
        assert wrong_config.observation_seed == p01_config.observation_seed
        assert wrong_config.reporting_delay.days == (0,)
        differences = _leaf_differences(payload(p01_config), payload(wrong_config))
        assert differences == {"reporting_delay.days[0]"}

    p02b_configs = observation_configs[491:]
    assert len(p02b_configs) == 81
    grid_b = campaign._p02b_grid(config)
    for cell_index, cell in enumerate(grid_b):
        common = cell.symptomatic_detection_probability
        reference = CandidateCell(
            beta=cell.beta,
            inoculation_day_offset=cell.inoculation_day_offset,
            symptomatic_detection_probability=min(
                config.dimension_map["symptomatic_detection_probability"].candidates,
                key=lambda value: (abs(value - common), value),
            ),
            asymptomatic_detection_probability=min(
                config.dimension_map["asymptomatic_detection_probability"].candidates,
                key=lambda value: (abs(value - common), value),
            ),
        )
        for replicate, wrong_config in enumerate(p02b_configs[cell_index * 3 : cell_index * 3 + 3]):
            reference_config = campaign._observation_config_for_cell(
                ROOT,
                config,
                config.candidate_observation_seeds[replicate],
                config.candidate_observation_config_id,
                reference,
            )
            assert wrong_config.observation_config_id == reference_config.observation_config_id
            assert wrong_config.observation_seed == reference_config.observation_seed
            assert wrong_config.parameters["symptomatic_detection_probability"].value == common
            assert wrong_config.parameters["asymptomatic_detection_probability"].value == common
            differences = _leaf_differences(payload(reference_config), payload(wrong_config))
            assert differences <= {
                "parameters.symptomatic_detection_probability.value",
                "parameters.asymptomatic_detection_probability.value",
            }

    p02_persisted = tuple((tmp_path / "p02-work").glob("*/blind_estimates/*.json"))
    assert len(p02_persisted) == 10
    assert all(
        json.loads(path.read_text(encoding="utf-8"))["estimate_hash"] for path in p02_persisted
    )
    bundle_config, bundle_ruling = _test_ruling_config(tmp_path)
    bundle = campaign.write_research_bundle(
        tmp_path / "p02-bundle",
        campaign_config_path=bundle_config,
        predeclaration_path=PREDECLARATION_PATH,
        ruling_path=bundle_ruling,
        seed_ledger=[],
        candidate_loss_surfaces={},
        p02_misspecification_rows=[
            row.as_dict() for arm in p02_result.arms.values() for row in arm.target_results
        ],
        p02_complete_loss_surfaces={
            arm_name: {
                str(seed): [row.as_dict() for row in surface]
                for seed, surface in arm.loss_surfaces.items()
            }
            for arm_name, arm in p02_result.arms.items()
        },
        p02_provenance=p02_result.as_dict(),
        input_hashes={"campaign_config": campaign.sha256_file(bundle_config)},
    )
    csv_lines = (bundle / "p0_2_misspecification.csv").read_text(encoding="utf-8").splitlines()
    assert len(csv_lines) == 11
    with (bundle / "p0_2_misspecification.csv").open(encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert all(row["E_i"] == "null" for row in csv_rows)
    assert all(row["estimate_beta"] == "null" for row in csv_rows)
    assert all(row["signed_error_beta"] == "null" for row in csv_rows)
    surfaces = json.loads((bundle / "p0_2_loss_surfaces.json").read_text(encoding="utf-8"))
    assert set(surfaces) == {"p0_2a", "p0_2b"}
    assert all(len(targets) == 5 for targets in surfaces.values())
    provenance = json.loads((bundle / "p0_2_provenance.json").read_text(encoding="utf-8"))
    assert len(provenance["arms"]["p0_2a"]["replicate_provenance"]) == 243
    assert len(provenance["arms"]["p0_2b"]["replicate_provenance"]) == 81

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
