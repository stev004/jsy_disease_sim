from __future__ import annotations

import csv
import hashlib
import json
import math
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import yaml

import jersey_outbreak.phase0_campaign as campaign
from jersey_outbreak.observation_scheduler import observation_stream_seed
from jersey_outbreak.observation_schemas import ObservationConfig
from jersey_outbreak.outbreak_schemas import OutbreakRunConfig

ROOT = Path(__file__).resolve().parents[1]
PHASE0_CONFIG = ROOT / "configs/calibration/v13_phase0_synthetic.yaml"
PHASE0B_CONFIG = ROOT / "configs/calibration/v13_phase0b_synthetic.yaml"
PHASE0_PREDECLARATION = ROOT / campaign.PHASE0_PROFILE.predeclaration_path
PHASE0B_PREDECLARATION = ROOT / campaign.PHASE0B_PROFILE.predeclaration_path
G29_RULING = ROOT / campaign.G29_RULING_PATH
OWNER_RULING = ROOT / campaign.PHASE0B_OWNER_RULING_PATH


def _profiles() -> tuple[campaign.ProfileDiagnostic, ...]:
    return tuple(
        campaign.ProfileDiagnostic(
            dimension=name,
            values=(0.0, 1.0, 2.0),
            profiled_objectives=(0.0, 1.0, 2.0),
            minimum=0.0,
            second_minimum=1.0,
            numerical_tie=False,
            relative_gap=1.0,
            identified=True,
        )
        for name in campaign.P01_DIMENSION_NAMES
    )


def _selected_fit(cell: campaign.CandidateCell, *, tie: bool = False) -> campaign.BlindFitResult:
    minimizers = (cell, cell) if tie else (cell,)
    return campaign.BlindFitResult(
        loss_surface=(),
        minimum_objective=1.0,
        global_minimizers=minimizers,
        numerical_tie=tie,
        tie_tolerance=1e-12,
        selected=None if tie else cell,
        profiles=_profiles(),
        identified=not tie,
        estimate_hash="a" * 64,
    )


def _zero_table(config: campaign.CampaignConfig) -> campaign.ObservedTables:
    dates = campaign.observation_dates(
        config.start_date, config.duration_days, config.observation_horizon_tail_days
    )
    zeros = (0.0,) * len(dates)
    return campaign.ObservedTables(dates, zeros, zeros)


def test_phase0b_profile_is_independently_frozen_and_workload_is_exact(
    tmp_path: Path,
) -> None:
    config = campaign.CampaignConfig.from_yaml(PHASE0B_CONFIG)
    plan = campaign.guard_workload(config)
    assert config.campaign_id == "v13-phase0b"
    assert len(config.candidate_grid) == 625
    assert config.expected_predeclaration_sha256 == campaign.PHASE0B_PREDECLARATION_SHA256
    assert config.owner_ruling_path == campaign.PHASE0B_OWNER_RULING_PATH
    assert config.owner_ruling_sha256 == campaign.PHASE0B_OWNER_RULING_SHA256
    assert all(
        isinstance(value, str)
        for declaration in config.declaration["dimensions"].values()
        for value in (
            declaration["truth"],
            *declaration["candidates"],
            declaration["tolerance"],
            declaration["bias_limit"],
        )
    )
    assert config.dimension_map["asymptomatic_detection_probability"].candidate_decimals == (
        Decimal("0.10"),
        Decimal("0.175"),
        Decimal("0.25"),
        Decimal("0.325"),
        Decimal("0.40"),
    )
    assert plan.as_dict()["p0_1_grid_cells"] == 625
    assert plan.as_dict()["p0_2_wrong_delay_cells"] == 625
    assert plan.as_dict()["p0_2_wrong_regime_cells"] == 75
    assert plan.as_dict()["p0_3_cells"] == 9
    assert plan.as_dict()["total_cells"] == 1334
    assert plan.p01_latent_calls == 80
    assert plan.total_latent_calls == 107
    assert plan.p01_observation_transforms == 1880
    assert plan.total_observation_transforms == 4007
    assert plan.distinct_network_seed_builds == 8
    assert plan.implemented_cells == plan.total_cells
    assert plan.implemented_latent_calls == plan.total_latent_calls
    assert plan.implemented_observation_transforms == plan.total_observation_transforms
    assert (
        campaign.validate_predeclaration(
            PHASE0B_PREDECLARATION, campaign.PHASE0B_PREDECLARATION_SHA256
        )
        == campaign.PHASE0B_PREDECLARATION_SHA256
    )
    assert campaign.validate_owner_ruling(OWNER_RULING, config) == (
        campaign.PHASE0B_OWNER_RULING_SHA256
    )

    changed_config = yaml.safe_load(PHASE0B_CONFIG.read_text(encoding="utf-8"))
    changed_config["dimensions"]["beta"]["tolerance"] = "0.020"
    changed_path = tmp_path / "changed-config.yaml"
    changed_path.write_text(yaml.safe_dump(changed_config, sort_keys=False), encoding="utf-8")
    with pytest.raises(campaign.CampaignError, match="frozen declaration changed"):
        campaign.CampaignConfig.from_yaml(changed_path)

    changed_declaration = tmp_path / "changed-predeclaration.md"
    changed_declaration.write_bytes(PHASE0B_PREDECLARATION.read_bytes() + b"\n")
    with pytest.raises(campaign.CampaignError, match="predeclaration SHA-256 mismatch"):
        campaign.validate_predeclaration(changed_declaration, config.expected_predeclaration_sha256)
    changed_ruling = tmp_path / "changed-owner-ruling.md"
    changed_ruling.write_bytes(OWNER_RULING.read_bytes() + b"\n")
    with pytest.raises(campaign.CampaignError, match="model-owner ruling SHA-256 mismatch"):
        campaign.validate_owner_ruling(changed_ruling, config)


def test_phase0b_seed_sets_are_disjoint_and_guard_uses_phase0_constants() -> None:
    config = campaign.CampaignConfig.from_yaml(PHASE0B_CONFIG)
    seed_sets = (
        set(config.target_process_seeds),
        set(config.target_observation_seeds),
        set(config.candidate_process_seeds),
        set(config.candidate_observation_seeds),
    )
    phase0_seed_sets = (
        set(campaign.TARGET_PROCESS_SEEDS),
        set(campaign.TARGET_OBSERVATION_SEEDS),
        set(campaign.FIT_PROCESS_SEEDS),
        set(campaign.FIT_OBSERVATION_SEEDS),
    )
    assert not any(
        left & right for index, left in enumerate(seed_sets) for right in seed_sets[index + 1 :]
    )
    assert not any(left & right for left in seed_sets for right in phase0_seed_sets)
    overlapped = replace(
        config,
        target_process_seeds=(campaign.TARGET_PROCESS_SEEDS[0], *config.target_process_seeds[1:]),
    )
    with pytest.raises(campaign.BudgetError, match="other frozen profile"):
        campaign.guard_workload(overlapped)
    with pytest.raises(campaign.BudgetError, match="duration"):
        campaign.guard_workload(replace(config, duration_days=31))
    oversized_dimensions = (
        replace(
            config.dimension_map["beta"],
            candidates=config.dimension_map["beta"].candidates[:-1],
        ),
        *config.dimensions[1:],
    )
    with pytest.raises(campaign.BudgetError, match="frozen-profile cell count"):
        campaign.guard_workload(replace(config, dimensions=oversized_dimensions))


def test_phase0b_dry_run_reports_all_arm_counts_and_verified_authorities(
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan = campaign.dry_run(
        PHASE0B_CONFIG,
        PHASE0B_PREDECLARATION,
        G29_RULING,
        OWNER_RULING,
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["p0_1_grid_cells"] == 625
    assert payload["p0_2_wrong_delay_cells"] == 625
    assert payload["p0_2_wrong_regime_cells"] == 75
    assert payload["p0_3_cells"] == 9
    assert payload["total_cells"] == 1334
    assert payload["p0_1_latent_calls"] == 80
    assert payload["p0_2a_latent_calls"] == payload["p0_2b_latent_calls"] == 0
    assert payload["p0_3_latent_calls"] == 27
    assert payload["total_latent_outbreak_calls"] == 107
    assert payload["p0_1_observation_transforms"] == 1880
    assert payload["p0_2a_observation_transforms"] == 1875
    assert payload["p0_2b_observation_transforms"] == 225
    assert payload["p0_3_observation_transforms"] == 27
    assert payload["total_observation_transforms"] == 4007
    assert payload["distinct_population_network_seed_builds"] == 8
    assert payload["predeclaration_verified"] is True
    assert payload["g29_ruling_verified"] is True
    assert payload["owner_ruling_verified"] is True
    assert plan.implemented_cells == plan.total_cells


def test_phase0_profile_still_validates_and_dry_runs_to_198_59_599_8(
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = campaign.CampaignConfig.from_yaml(PHASE0_CONFIG)
    plan = campaign.dry_run(PHASE0_CONFIG, PHASE0_PREDECLARATION)
    payload = json.loads(capsys.readouterr().out)
    assert config.expected_predeclaration_sha256 == campaign.PREDECLARATION_SHA256
    assert (
        payload["total_cells"],
        payload["total_latent_outbreak_calls"],
        payload["total_observation_transforms"],
        payload["distinct_population_network_seed_builds"],
    ) == (198, 59, 599, 8)
    assert plan.implemented_cells == 198


def test_phase0b_complete_625_cell_surface_is_scored_before_tie_selection() -> None:
    config = campaign.CampaignConfig.from_yaml(PHASE0B_CONFIG)
    target = _zero_table(config)
    library = {cell: (target, target, target) for cell in config.candidate_grid}
    fit = campaign.fit_blind(
        target,
        config.candidate_grid,
        library,
        expected_grid=config.candidate_grid,
    )
    assert len(fit.loss_surface) == 625
    assert fit.numerical_tie is True
    assert fit.selected is None


def test_phase0b_decimal_recovery_endpoints_are_inclusive_and_bias_cancels() -> None:
    config = campaign.CampaignConfig.from_yaml(PHASE0B_CONFIG)
    truth = campaign._truth_cell(config)
    estimates = (
        campaign.CandidateCell(0.06, 1, 0.625, 0.175),
        campaign.CandidateCell(0.10, 3, 0.875, 0.325),
        truth,
        truth,
        truth,
    )
    rows = []
    for target_seed, selected in zip(config.target_process_seeds, estimates, strict=True):
        rows.append(
            campaign.join_truth_evaluation(
                _selected_fit(selected),
                target_seed=target_seed,
                truth=truth,
                truth_diagnostics=campaign.TruthDiagnostics(
                    inoculation_acquisitions=10,
                    local_secondary_infections=1,
                    symptomatic_reports=1,
                    asymptomatic_reports=1,
                    nonzero_combined_report_dates=3,
                    chronology_passed=True,
                    latent_incidence_conservation_passed=True,
                ),
                config=config,
            )
        )
    evaluation = campaign.evaluate_p01(rows, config=config)
    for dimension in config.dimensions:
        assert evaluation.coverage[dimension.name] == 1.0
        assert evaluation.bias[dimension.name] == 0.0
        assert evaluation.predicates[f"coverage_{dimension.name}"] is True
        assert evaluation.predicates[f"bias_{dimension.name}"] is True
        assert evaluation.boundary_counts[dimension.name] == 0
    first = rows[0]
    second = rows[1]
    assert first._absolute_error_decimal("asymptomatic_detection_probability") == Decimal("0.075")
    assert second._absolute_error_decimal("asymptomatic_detection_probability") == Decimal("0.075")
    assert first._absolute_error_decimal("symptomatic_detection_probability") == Decimal("0.125")
    assert second._absolute_error_decimal("symptomatic_detection_probability") == Decimal("0.125")


def test_phase0b_p02a_independent_clauses_and_g29_tie_values() -> None:
    config = campaign.CampaignConfig.from_yaml(PHASE0B_CONFIG)
    truth = campaign._truth_cell(config)
    table = _zero_table(config)
    predictions = {truth: (table, table, table)}
    endpoint = campaign.CandidateCell(0.08, 3, 0.75, 0.25)
    endpoint_result = campaign.evaluate_p02_target(
        "p0_2a",
        target_seed=config.target_process_seeds[0],
        correct_minimum_objective=1.0,
        wrong_fit=_selected_fit(endpoint),
        target_tables=table,
        wrong_candidate_prediction_library=predictions,
        truth=truth,
        config=config,
    )
    assert endpoint_result.clauses == {
        "inoculation_day_offset_equals_4": False,
        "any_dimension_outside_p0_1_tolerance": False,
        "relative_loss_degradation_at_least_0_25": False,
    }
    assert endpoint_result.dimension_errors["inoculation_day_offset"]["outside_tolerance"] is False

    offset_four = campaign.CandidateCell(0.08, 4, 0.75, 0.25)
    boundary_result = campaign.evaluate_p02_target(
        "p0_2a",
        target_seed=config.target_process_seeds[0],
        correct_minimum_objective=1.0,
        wrong_fit=_selected_fit(offset_four),
        target_tables=table,
        wrong_candidate_prediction_library=predictions,
        truth=truth,
        config=config,
    )
    assert boundary_result.clauses["inoculation_day_offset_equals_4"] is True
    assert boundary_result.clauses["any_dimension_outside_p0_1_tolerance"] is True

    tied = campaign.evaluate_p02_target(
        "p0_2a",
        target_seed=config.target_process_seeds[0],
        correct_minimum_objective=1.0,
        wrong_fit=_selected_fit(offset_four, tie=True),
        target_tables=table,
        wrong_candidate_prediction_library=predictions,
        truth=truth,
        config=config,
    )
    assert tied.detection_state == "UNKNOWN"
    assert tied.clauses["inoculation_day_offset_equals_4"] is None
    assert tied.clauses["any_dimension_outside_p0_1_tolerance"] is None
    assert tied.clauses["relative_loss_degradation_at_least_0_25"] is False


def test_phase0b_p02b_uses_75_cells_and_exact_outside_tolerance_clauses() -> None:
    config = campaign.CampaignConfig.from_yaml(PHASE0B_CONFIG)
    grid = campaign._p02b_grid(config)
    table = _zero_table(config)
    library = {cell: (table, table, table) for cell in grid}
    fit = campaign.fit_p02_blind(
        table,
        grid,
        library,
        candidate_config_hashes={cell: "b" * 64 for cell in grid},
        arm="p0_2b",
        config=config,
    )
    assert len(grid) == 75
    assert len(fit.loss_surface) == 75
    assert fit.numerical_tie is True

    truth = campaign._truth_cell(config)
    endpoint = campaign.CandidateCell(0.10, 3, 0.50, 0.50)
    endpoint_result = campaign.evaluate_p02_target(
        "p0_2b",
        target_seed=config.target_process_seeds[0],
        correct_minimum_objective=1.0,
        wrong_fit=_selected_fit(endpoint),
        target_tables=table,
        wrong_candidate_prediction_library={endpoint: (table, table, table)},
        truth=truth,
        config=config,
    )
    assert endpoint_result.clauses["beta_outside_p0_1_tolerance"] is False
    assert endpoint_result.clauses["inoculation_day_offset_outside_p0_1_tolerance"] is False
    assert endpoint_result.detection_state == "FALSE"

    outside = campaign.CandidateCell(0.12, 4, 0.50, 0.50)
    outside_result = campaign.evaluate_p02_target(
        "p0_2b",
        target_seed=config.target_process_seeds[0],
        correct_minimum_objective=1.0,
        wrong_fit=_selected_fit(outside),
        target_tables=table,
        wrong_candidate_prediction_library={outside: (table, table, table)},
        truth=truth,
        config=config,
    )
    assert outside_result.clauses["beta_outside_p0_1_tolerance"] is True
    assert outside_result.clauses["inoculation_day_offset_outside_p0_1_tolerance"] is True

    tied_unknown = campaign.evaluate_p02_target(
        "p0_2b",
        target_seed=config.target_process_seeds[0],
        correct_minimum_objective=1.0,
        wrong_fit=_selected_fit(outside, tie=True),
        target_tables=table,
        wrong_candidate_prediction_library={outside: (table, table, table)},
        truth=truth,
        config=config,
    )
    assert tied_unknown.detection_state == "UNKNOWN"
    assert tied_unknown.clauses["channel_total_error_at_least_0_25"] is None
    assert tied_unknown.clauses["beta_outside_p0_1_tolerance"] is None
    assert tied_unknown.clauses["inoculation_day_offset_outside_p0_1_tolerance"] is None
    tied_detected = campaign.evaluate_p02_target(
        "p0_2b",
        target_seed=config.target_process_seeds[0],
        correct_minimum_objective=1.0,
        wrong_fit=replace(_selected_fit(outside, tie=True), minimum_objective=1.25),
        target_tables=table,
        wrong_candidate_prediction_library={outside: (table, table, table)},
        truth=truth,
        config=config,
    )
    assert tied_detected.detection_state == "TRUE"
    assert tied_detected.clauses["relative_loss_degradation_at_least_0_25"] is True


def test_phase0b_p03_keeps_nine_cell_design_on_fresh_candidate_seeds() -> None:
    config = campaign.CampaignConfig.from_yaml(PHASE0B_CONFIG)
    assert len(campaign._p03_grid()) == 9
    assert config.candidate_process_seeds == campaign.PHASE0B_FIT_PROCESS_SEEDS
    assert config.candidate_observation_seeds == campaign.PHASE0B_FIT_OBSERVATION_SEEDS
    assert campaign.P03_BETA_GRID == (0.04, 0.08, 0.16)
    assert campaign.P03_ROUTE_FACTOR_GRID == (0.5, 1.0, 2.0)


def test_phase0b_mocked_full_orchestration_and_bundle_cold_recomputation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = {"build": 0, "latent": 0, "observe": 0}
    run_configs: list[OutbreakRunConfig] = []
    observation_configs: list[ObservationConfig] = []

    class FakeParent:
        generated = object()

    class FakeLatent:
        logical_content_hash = "phase0b-mocked-latent-hash"
        diagnostics = {
            "natural_history": {"chronology_passed": True},
            "states": {"conserved": True},
        }
        transmission_events = tuple(
            [{"imported": True} for _ in range(10)] + [{"source_kind": "local"}]
        )

        def __init__(self, config: OutbreakRunConfig) -> None:
            self.config = config

    class FakeObserved:
        def __init__(self, latent: FakeLatent, config: ObservationConfig) -> None:
            self.latent_run = latent
            self.config = config
            self.diagnostics: dict[str, Any] = {}
            start = date.fromisoformat(next(iter(latent.config.import_schedule)))
            route_mean = sum(latent.config.route_multipliers.values()) / len(
                latent.config.route_multipliers
            )
            symptomatic = config.parameters["symptomatic_detection_probability"].value
            asymptomatic = config.parameters["asymptomatic_detection_probability"].value
            self.observation_events = [
                {"report_date": start.isoformat(), "symptomatic": True},
                {"report_date": (start + timedelta(days=1)).isoformat(), "symptomatic": False},
                {"report_date": (start + timedelta(days=2)).isoformat(), "symptomatic": True},
                *(
                    {"report_date": (start + timedelta(days=1)).isoformat(), "symptomatic": True}
                    for _ in range(round(latent.config.beta * route_mean * symptomatic * 100))
                ),
                *(
                    {"report_date": (start + timedelta(days=2)).isoformat(), "symptomatic": False}
                    for _ in range(round(latent.config.beta * route_mean * asymptomatic * 100))
                ),
            ]

    def fake_build_parent(*args: Any, **kwargs: Any) -> FakeParent:
        del args, kwargs
        calls["build"] += 1
        return FakeParent()

    def fake_run_outbreak(
        parent: Any, run_config: OutbreakRunConfig, parameters: Any
    ) -> FakeLatent:
        del parent, parameters
        calls["latent"] += 1
        run_configs.append(run_config)
        return FakeLatent(run_config)

    def fake_observe(latent: FakeLatent, config: ObservationConfig) -> FakeObserved:
        calls["observe"] += 1
        observation_configs.append(config)
        result = FakeObserved(latent, config)
        result.diagnostics = {
            "status": "passed",
            "no_report_before_infection": True,
            "chronology_violations": 0,
            "latent_incidence_conservation": True,
            "latent_incidence_conservation_difference": 0,
            "observation_rng": {
                "stream_namespace": "observation",
                "stream_key_inputs": [
                    "latent_replicate_seed",
                    "observation_seed",
                    "observation_config_id",
                ],
                "stream_fingerprint": hashlib.sha256(
                    str(observation_stream_seed(latent.config.seed, config)).encode()
                ).hexdigest(),
            },
        }
        return result

    monkeypatch.setattr(campaign, "build_parent", fake_build_parent)
    monkeypatch.setattr(campaign, "run_outbreak", fake_run_outbreak)
    monkeypatch.setattr(campaign, "observe_latent_run", fake_observe)
    bundle = tmp_path / "phase0b-mocked-bundle"
    campaign.execute_campaign(
        PHASE0B_CONFIG,
        PHASE0B_PREDECLARATION,
        bundle,
        G29_RULING,
        OWNER_RULING,
        mocked_for_test=True,
    )
    config = campaign.CampaignConfig.from_yaml(PHASE0B_CONFIG)

    assert calls == {"build": 8, "latent": 107, "observe": 4007}
    assert all(isinstance(config, OutbreakRunConfig) for config in run_configs)
    assert all(isinstance(config, ObservationConfig) for config in observation_configs)
    assert len(run_configs) == 107
    assert len(observation_configs) == 4007
    summary = json.loads((bundle / "campaign_summary.json").read_text(encoding="utf-8"))
    assert summary["measured_work"] == {
        "grid_cells": 1334,
        "latent_outbreak_calls": 107,
        "observation_transforms": 4007,
        "distinct_population_network_seed_builds": 8,
        "mode": "ci",
        "maximum_duration_days": 30,
    }
    assert summary["lineage"] == campaign.PHASE0_LINEAGE
    assert summary["overall_phase0b_status"] == "NOT_EVALUATED"
    assert "overall_phase0_status" not in summary
    p03_profile = json.loads((bundle / "p0_3_profile.json").read_text(encoding="utf-8"))
    assert p03_profile["classification"] == "NON_IDENTIFIED_STRUCTURAL"
    assert all(p03_profile["predicates"].values())
    blind_manifest = json.loads(
        (bundle / "blind_estimate_manifest.json").read_text(encoding="utf-8")
    )
    assert blind_manifest["record_count"] == 15
    assert all(
        item["persist_before_truth_join"] == "guaranteed_by_code_path"
        for item in blind_manifest["records"]
    )
    boundary_counts = summary["arms"]["p0_1"]["boundary_counts"]
    assert set(boundary_counts) == set(campaign.P01_DIMENSION_NAMES)
    assert all(isinstance(count, int) and 0 <= count <= 5 for count in boundary_counts.values())
    with (bundle / "p0_1_recovery.csv").open(encoding="utf-8", newline="") as handle:
        p01_rows = list(csv.DictReader(handle))
    assert {"selected_at_grid_boundary", "boundary_count"} <= set(p01_rows[0])
    assert all(int(row["boundary_count"]) == boundary_counts[row["dimension"]] for row in p01_rows)
    assert summary["disclosures"]["bundle_byte_size"] == sum(
        path.stat().st_size for path in bundle.rglob("*") if path.is_file()
    )
    assert set(summary["disclosures"]["wall_time_seconds_by_arm"]) == {
        "p0_1",
        "p0_2a",
        "p0_2b",
        "p0_3",
    }
    assert all(
        math.isfinite(value) and value >= 0
        for value in summary["disclosures"]["wall_time_seconds_by_arm"].values()
    )
    assert summary["disclosures"]["total_wall_time_seconds"] >= 0
    assert (bundle / "predeclaration.md").read_bytes() == PHASE0B_PREDECLARATION.read_bytes()
    assert (bundle / "phase0b_owner_ruling.md").read_bytes() == OWNER_RULING.read_bytes()
    assert campaign.sha256_file(bundle / "phase0b_owner_ruling.md") == (
        campaign.PHASE0B_OWNER_RULING_SHA256
    )

    index = json.loads((bundle / "bundle_index.json").read_text(encoding="utf-8"))
    entries = index["retained_evidence_files"]
    target_seed = 62001
    target_entry = next(
        item
        for item in entries
        if item.get("kind") == "observed_table"
        and item.get("arm") == "p0_1"
        and item.get("role") == "target"
        and item.get("process_seed") == target_seed
    )
    surfaces = json.loads((bundle / "candidate_loss_surfaces.json").read_text(encoding="utf-8"))
    surface_row = surfaces[str(target_seed)][0]
    candidate_cell = {name: surface_row[name] for name in campaign.P01_DIMENSION_NAMES}
    candidate_table_entries = [
        item
        for item in entries
        if item.get("kind") == "observed_table"
        and item.get("arm") == "p0_1"
        and item.get("role") == "candidate"
        and item.get("cell") == candidate_cell
    ]
    assert len(candidate_table_entries) == 3
    target_table = json.loads((bundle / target_entry["path"]).read_text(encoding="utf-8"))[
        "observed_tables"
    ]
    target_tables = campaign.ObservedTables(
        tuple(target_table["dates"]),
        tuple(target_table["symptomatic"]),
        tuple(target_table["asymptomatic"]),
    )
    predictions = []
    for item in candidate_table_entries:
        raw = json.loads((bundle / item["path"]).read_text(encoding="utf-8"))["observed_tables"]
        predictions.append(
            campaign.ObservedTables(
                tuple(raw["dates"]), tuple(raw["symptomatic"]), tuple(raw["asymptomatic"])
            )
        )
    recomputed = campaign.minimum_distance_loss(target_tables, predictions)
    assert recomputed == pytest.approx(surface_row["objective"], abs=1e-15)

    with (bundle / "p0_2_misspecification.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    p02a_row = next(
        row for row in rows if row["arm"] == "p0_2a" and row["target_seed"] == str(target_seed)
    )
    expected_clause_columns = {
        "clause_inoculation_day_offset_equals_4",
        "clause_any_dimension_outside_p0_1_tolerance",
        "clause_relative_loss_degradation_at_least_0_25",
    }
    assert expected_clause_columns <= set(p02a_row)
    correct_surfaces = json.loads(
        (bundle / "candidate_loss_surfaces.json").read_text(encoding="utf-8")
    )
    wrong_surfaces = json.loads((bundle / "p0_2_loss_surfaces.json").read_text(encoding="utf-8"))
    correct_minimum = min(row["objective"] for row in correct_surfaces[str(target_seed)])
    wrong_minimum = min(row["objective"] for row in wrong_surfaces["p0_2a"][str(target_seed)])
    recomputed_relative_loss = (wrong_minimum - correct_minimum) / max(correct_minimum, 1e-9)
    assert float(p02a_row["R_i"]) == pytest.approx(recomputed_relative_loss, abs=1e-15)
    relative_loss_clause = recomputed_relative_loss >= 0.25
    assert p02a_row["clause_relative_loss_degradation_at_least_0_25"] == str(relative_loss_clause)
    if p02a_row["selected_estimates"] != "null":
        selected = json.loads(p02a_row["selected_estimates"])
        offset_clause = selected["inoculation_day_offset"] == 4
        outside_clause = any(
            abs(
                config.dimension_map[name].exact_value(selected[name])
                - config.dimension_map[name].exact_truth()
            )
            > config.dimension_map[name].exact_tolerance()
            for name in campaign.P01_DIMENSION_NAMES
        )
        assert p02a_row["clause_inoculation_day_offset_equals_4"] == str(offset_clause)
        assert p02a_row["clause_any_dimension_outside_p0_1_tolerance"] == str(outside_clause)
    p02b_row = next(row for row in rows if row["arm"] == "p0_2b")
    assert {
        "clause_relative_loss_degradation_at_least_0_25",
        "clause_channel_total_error_at_least_0_25",
        "clause_beta_outside_p0_1_tolerance",
        "clause_inoculation_day_offset_outside_p0_1_tolerance",
    } <= set(p02b_row)

    for line in (bundle / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        assert campaign.sha256_file(bundle / relative) == digest
