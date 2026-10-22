from __future__ import annotations

import csv
import hashlib
import inspect
import json
import math
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml

from jersey_outbreak import g35b_constants as frozen
from jersey_outbreak import g35b_design_study as study
from jersey_outbreak import phase0_campaign as phase0
from jersey_outbreak.observation_scheduler import observation_stream_seed
from jersey_outbreak.observation_schemas import ObservationConfig
from jersey_outbreak.outbreak_schemas import OutbreakRunConfig

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/calibration/v13_g35b_design_study.yaml"
PREDECLARATION = ROOT / frozen.PREDECLARATION_PATH
TRUTH = phase0.CandidateCell(0.08, 2, 0.75, 0.25)


@pytest.fixture(autouse=True)
def no_expensive_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("expensive execution must be explicitly mocked")

    for name in ("build_parent", "run_outbreak", "observe_latent_run"):
        monkeypatch.setattr(study, name, forbidden)


def _payload() -> dict[str, Any]:
    return yaml.safe_load(CONFIG.read_text())


def test_independent_frozen_inputs_and_precheck_hashes() -> None:
    payload = _payload()
    assert payload == study.frozen_payload()
    assert study.StudyConfig.from_yaml(CONFIG) == study.StudyConfig()
    assert frozen.PREDECLARATION_SHA256 == (
        "2e8358abd9e275a5cf04a58b4ad76313c10964f2da06d46cd0f8a7190733216e"
    )
    assert frozen.RIDGE_SHA256 == (
        "8cf4c76612434cbd90c5de4ca9dfd1326422b94a72bd4a63ccff71e95f34908a"
    )
    assert (
        hashlib.sha256(study.committed_document_bytes(ROOT / frozen.RIDGE_PATH)).hexdigest()
        == frozen.RIDGE_SHA256
    )
    assert study.validate_predeclaration(PREDECLARATION) == frozen.PREDECLARATION_SHA256
    earlier = tuple(seed for group in frozen.EARLIER_SEED_SETS for seed in group)
    assert len(earlier) == 41
    assert set(earlier) == {
        *range(42001, 42006),
        *range(52001, 52006),
        *range(43001, 43004),
        *range(53001, 53004),
        *range(62001, 62006),
        *range(72001, 72006),
        *range(63001, 63004),
        *range(73001, 73004),
        *range(81001, 81007),
        *range(91001, 91004),
    }
    record_path = ROOT / "docs/runs/2026-10-22-g35b-seed-precheck.json"
    record = json.loads(study.committed_document_bytes(record_path))
    by_seed = {row["seed"]: row for row in record}
    assert len(payload["process_hashes"]) == 22
    for seed, hashes in payload["process_hashes"].items():
        row = by_seed[seed]
        assert row["status"] == "BUILT"
        expected = {
            artifact.split("-ci-seed")[0].rsplit("-", 1)[-1]: digest
            for artifact, digest in row["artifacts"]
        }
        assert hashes == expected
        assert tuple(hashes[key] for key in ("m2", "m3", "m4")) == frozen.PROCESS_HASHES[seed]

    # Every configured decimal stays a string; bools/integers remain their declared types.
    def no_binary_decimals(node: Any) -> None:
        assert not isinstance(node, float)
        if isinstance(node, dict):
            for value in node.values():
                no_binary_decimals(value)
        elif isinstance(node, list):
            for value in node:
                no_binary_decimals(value)

    no_binary_decimals(payload)


def test_predeclaration_crlf_normalization_proves_equality_to_git_blob(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    committed = study.committed_document_bytes(PREDECLARATION)
    original_read = Path.read_bytes

    def crlf_read(path: Path) -> bytes:
        if path == PREDECLARATION:
            return committed.replace(b"\n", b"\r\n")
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", crlf_read)
    assert study.validate_predeclaration(PREDECLARATION) == frozen.PREDECLARATION_SHA256
    copy = tmp_path / "crlf-copy.md"
    copy.write_bytes(committed.replace(b"\n", b"\r\n"))
    with pytest.raises(study.CampaignError, match="cannot verify committed"):
        study.validate_predeclaration(copy)
    monkeypatch.setattr(Path, "read_bytes", lambda _: committed + b"\n")
    with pytest.raises(study.CampaignError, match="differs from committed"):
        study.validate_predeclaration(PREDECLARATION)


def test_committed_digest_mismatch_is_hard_error(monkeypatch: pytest.MonkeyPatch) -> None:
    original = study.subprocess.check_output
    changed = b"committed different document\n"

    def changed_show(argv: list[str], **kwargs: Any) -> bytes:
        if "show" in argv:
            return changed
        return original(argv, **kwargs)

    monkeypatch.setattr(study.subprocess, "check_output", changed_show)
    monkeypatch.setattr(Path, "read_bytes", lambda _: changed)
    with pytest.raises(study.CampaignError, match="predeclaration SHA-256 mismatch"):
        study.validate_predeclaration(PREDECLARATION)


@pytest.mark.parametrize(
    "path,value",
    [
        (("expected_predeclaration_sha256",), "0" * 64),
        (("lineage", "ridge_diagnostic_sha256"), "0" * 64),
        (("dimensions", "beta", "truth"), "0.080"),
        (("dimensions", "beta", "tolerance"), 0.02),
        (("fixed_scenario", "route_multipliers", "bus"), "0.9"),
        (("arms", "ii", "latent_days"), 50),
        (("arms", "ii", "calendar_dates"), 52),
        (("arms", "i", "replicates"), 13),
        (("budget_caps", "latent_calls"), 396),
        (("seeds", "target_observation_config_id"), "wrong"),
        (("seeds", "optimizer_seed"), 123),
        (("serosurvey", "n"), 401),
        (("serosurvey", "survey_day"), 30),
        (("process_hashes", 82001, "m3"), "a" * 64),
        (("implementation", "retries"), 1),
        (("implementation", "retries"), False),
        (("implementation", "replacement_seeds"), True),
        (("implementation", "adaptive_grid"), True),
        (("implementation", "pruning"), True),
        (("implementation", "early_stopping"), True),
        (("mode",), "full"),
    ],
)
def test_frozen_payload_mutations_fail_closed(
    tmp_path: Path, path: tuple[Any, ...], value: Any
) -> None:
    payload = _payload()
    node = payload
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    changed = tmp_path / "changed.yaml"
    changed.write_text(yaml.safe_dump(payload))
    with pytest.raises(study.CampaignError, match="frozen declaration"):
        study.StudyConfig.from_yaml(changed)


@pytest.mark.parametrize(
    "overlap",
    [
        82002,
        83001,
        92001,
        94001,
        95001,
        42001,
        52001,
        43001,
        53001,
        62001,
        72001,
        63001,
        73001,
        81006,
        91003,
    ],
)
def test_dry_run_rejects_seed_overlap(tmp_path: Path, capsys: Any, overlap: int) -> None:
    payload = _payload()
    payload["seeds"]["target_process_seeds"][0] = overlap
    path = tmp_path / "overlap.yaml"
    path.write_text(yaml.safe_dump(payload))
    assert (
        study.main(["dry-run", "--config", str(path), "--predeclaration", str(PREDECLARATION)]) == 1
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "seed overlap" in captured.err


def test_new_unknown_setting_or_seed_is_rejected() -> None:
    payload = _payload()
    payload["implementation"]["retry_on_error"] = True
    with pytest.raises(study.CampaignError, match="keys changed"):
        study.validate_frozen_payload(payload)
    payload = _payload()
    payload["seeds"]["candidate_batches"]["D_prime"]["process_seeds"][0] = 123456
    with pytest.raises(study.CampaignError, match="frozen declaration"):
        study.validate_frozen_payload(payload)


def test_exact_dry_run_and_no_execute_cli(capsys: Any) -> None:
    assert (
        study.main(["dry-run", "--config", str(CONFIG), "--predeclaration", str(PREDECLARATION)])
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "ci"
    assert report["predeclaration_sha256"] == frozen.PREDECLARATION_SHA256
    assert report["arms"] == {
        "B": {
            "replicates": 3,
            "latent_days": 30,
            "calendar_dates": 34,
            "cells": 625,
            "latent_calls": 85,
            "observation_transforms": 1885,
            "serosurvey_samples": 0,
            "builds": 13,
        },
        "i": {
            "replicates": 12,
            "latent_days": 30,
            "calendar_dates": 34,
            "cells": 625,
            "latent_calls": 225,
            "observation_transforms": 5625,
            "serosurvey_samples": 0,
            "builds": 9,
        },
        "ii": {
            "replicates": 3,
            "latent_days": 49,
            "calendar_dates": 53,
            "cells": 625,
            "latent_calls": 85,
            "observation_transforms": 1885,
            "serosurvey_samples": 0,
            "builds": 0,
        },
        "iii": {
            "replicates": 3,
            "latent_days": 30,
            "calendar_dates": 34,
            "cells": 625,
            "latent_calls": 0,
            "observation_transforms": 0,
            "serosurvey_samples": 85,
            "builds": 0,
        },
    }
    assert report["totals"] == {
        "cells": 2500,
        "latent_calls": 395,
        "observation_transforms": 9395,
        "serosurvey_samples": 85,
        "builds": 22,
    }
    assert report["gate_loss_evaluations"] == 25000
    assert report["descriptive_loss_evaluations"] == 31250
    with pytest.raises(SystemExit) as exc:
        study.main(["execute"])
    assert exc.value.code == 2


@pytest.mark.parametrize(
    "hook,unit", [(study.arm_i, "U2"), (study.arm_ii, "U3"), (study.arm_iii, "U4")]
)
def test_factor_hooks_are_explicitly_unimplemented(hook: Any, unit: str) -> None:
    with pytest.raises(NotImplementedError, match=unit):
        hook()


@pytest.mark.parametrize("value", [0.0, 7.0, 10**12])
def test_loss_matches_phase0b_bit_for_bit(value: float) -> None:
    dates = phase0.observation_dates(date(2025, 1, 6), 30)
    target = phase0.ObservedTables(dates, tuple(value + i for i in range(34)), (value,) * 34)
    predictions = tuple(
        phase0.ObservedTables(dates, (value + j,) * 34, tuple(value + i * j for i in range(34)))
        for j in range(3)
    )
    assert study.loss(target, predictions, 3, 34) == phase0.minimum_distance_loss(
        target, predictions
    )


def test_r12_loss_matches_hand_computed_fraction_literal_exactly() -> None:
    # For integer counts 0, 3, 30 the roots are (1, 3, 9)*sqrt(3/8).
    # Six of each candidate give mean 6*sqrt(3/8). Both target channels are 0:
    # Fraction(3,8) * (1 - Fraction(6*3+6*9,12))**2 = 75/8 = 9.375.
    target = phase0.ObservedTables(("2025-01-06",), (0.0,), (0.0,))
    low = phase0.ObservedTables(target.dates, (3.0,), (3.0,))
    high = phase0.ObservedTables(target.dates, (30.0,), (30.0,))
    assert study.loss(target, (low,) * 6 + (high,) * 6, 12, 1) == pytest.approx(9.375, abs=0, rel=0)
    assert study.loss(target, (low,) * 6 + (high,) * 6, 12, 1) == 9.375


@pytest.mark.parametrize("R,T", [(2, 34), (12, 34), (3, 33), (0, 34), (3, 0)])
def test_loss_rejects_wrong_replicate_or_date_count(R: int, T: int) -> None:
    dates = phase0.observation_dates(date(2025, 1, 6), 30)
    table = phase0.ObservedTables(dates, (0.0,) * 34, (0.0,) * 34)
    with pytest.raises(study.CampaignError, match="count"):
        study.loss(table, (table,) * 3, R, T)


def test_loss_rejects_mismatched_prediction_calendar() -> None:
    target = phase0.ObservedTables(("2025-01-06",), (0.0,), (0.0,))
    other = replace(target, dates=("2025-01-07",))
    with pytest.raises(study.CampaignError, match="calendar"):
        study.loss(target, (other,) * 3, 3, 1)


def _library(R: int, T: int, *, flat: bool = False) -> tuple[Any, Any, Any]:
    grid = study.StudyConfig().candidate_grid
    dates = phase0.observation_dates(date(2025, 1, 6), T, 0)
    library = {}
    for index, cell in enumerate(grid):
        table = phase0.ObservedTables(
            dates, (0.0 if flat else float(index),) * T, (0.0 if flat else float(index),) * T
        )
        library[cell] = (table,) * R
    return library[grid[312]][0], grid, library


@pytest.mark.parametrize("flat", [False, True])
def test_blind_fit_equals_phase0b_exactly(flat: bool) -> None:
    target, grid, library = _library(3, 34, flat=flat)
    expected = phase0.fit_blind(target, grid, library, expected_grid=grid)
    actual = study.fit_blind(target, grid, library, R=3, T=34)
    assert actual == expected
    assert actual.as_dict() == expected.as_dict()
    assert actual.selected == (None if flat else grid[312])
    assert actual.numerical_tie is flat
    assert actual.identified is not flat


@pytest.mark.parametrize("R,T", [(12, 34), (3, 53), (12, 2)])
def test_fitter_generalizes_without_truth_interface(R: int, T: int) -> None:
    target, grid, library = _library(R, T)
    fit = study.fit_blind(target, grid, library, R=R, T=T)
    assert fit.selected == grid[312]
    assert len(fit.loss_surface) == 625
    assert set(inspect.signature(study.fit_blind).parameters) == {
        "target_tables",
        "candidate_grid",
        "candidate_prediction_library",
        "R",
        "T",
        "candidate_config_hashes",
    }
    with pytest.raises(study.CampaignError, match="Cartesian"):
        study.fit_blind(target, grid[:-1], library, R=R, T=T)
    with pytest.raises(study.CampaignError, match="incomplete"):
        study.fit_blind(target, grid, {c: library[c] for c in grid[:-1]}, R=R, T=T)


def test_float_inclusive_tie_gap_and_denominator_rules() -> None:
    # Imported pure profile code is the independent oracle; exercise float >= at 0.05.
    cells = (TRUTH, replace(TRUTH, beta=0.10))
    surface = (phase0.LossRow(cells[0], 0.0), phase0.LossRow(cells[1], 0.05 * 1e-12))
    # At 0.05e-12 the two are tied by tau, even though the denominator floor would give 0.05.
    p = study._profile_dimension(surface, "beta", (0.08, 0.10), 0.0)
    assert p.numerical_tie and not p.identified
    surface = (phase0.LossRow(cells[0], 20.0), phase0.LossRow(cells[1], 21.0))
    p = study._profile_dimension(surface, "beta", (0.08, 0.10), 20.0)
    assert p.relative_gap == 0.05 and p.identified
    adjacent = (surface[0], replace(surface[1], objective=math.nextafter(21.0, -math.inf)))
    assert not study._profile_dimension(adjacent, "beta", (0.08, 0.10), 20.0).identified


@pytest.mark.parametrize("minimum", [0.0, 2e12])
def test_global_tie_comparison_is_float_inclusive(
    minimum: float,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    grid = (TRUTH, replace(TRUTH, beta=0.10))
    table = phase0.ObservedTables(("2025-01-06",), (0.0,), (0.0,))
    library = {cell: (table,) * 12 for cell in grid}
    tau = 1e-12 * max(1.0, minimum)
    for second, tied in ((minimum + tau, True), (math.nextafter(minimum + tau, math.inf), False)):
        objectives = iter((minimum, second))
        monkeypatch.setattr(study, "loss", lambda *args, _values=objectives: next(_values))
        fit = study.fit_blind(table, grid, library, R=12, T=1)
        assert fit.tie_tolerance == tau
        assert fit.numerical_tie is tied
        assert fit.selected == (None if tied else TRUTH)


def _rows() -> tuple[phase0.RecoveryRow, ...]:
    profiles = tuple(
        phase0.ProfileDiagnostic(name, (0.0, 1.0), (0.0, 1.0), 0.0, 1.0, False, 1.0, True)
        for name in phase0.P01_DIMENSION_NAMES
    )
    diagnostics = phase0.TruthDiagnostics(10, 1, 1, 1, 3, True, True, True, True)
    return tuple(
        phase0.RecoveryRow(seed, "a" * 64, TRUTH, profiles, False, TRUTH, diagnostics, True, 625)
        for seed in frozen.TARGET_PROCESS_SEEDS
    )


def _evaluate(rows: Any) -> study.RecoveryEvaluation:
    return study.evaluate_recovery(
        rows, execution_complete=True, provenance_verified=True, measured_equals_caps=True
    )


def test_all_ten_predicates_need_execution_evidence() -> None:
    assert _evaluate(_rows()).status == "PASS"
    assert len(_evaluate(_rows()).predicates) == 10
    assert study.evaluate_recovery(_rows()).status == "FAIL"
    assert not _evaluate(_rows()[:-1]).predicates["1_complete"]
    duplicate = (_rows()[0],) + _rows()[:-1]
    assert _evaluate(duplicate).status == "FAIL"
    rows = list(_rows())
    rows[0] = replace(rows[0], selected=None, numerical_tie=True)
    result = _evaluate(rows)
    assert not result.predicates["4_no_global_tie"]
    rows = list(_rows())
    rows[0] = replace(
        rows[0], truth_diagnostics=replace(rows[0].truth_diagnostics, local_secondary_infections=0)
    )
    assert not _evaluate(rows).predicates["2_truth_viability"]
    rows[0] = replace(
        rows[0], truth_diagnostics=replace(rows[0].truth_diagnostics, chronology_passed=False)
    )
    assert not _evaluate(rows).predicates["3_chronology_conservation"]
    rows = list(_rows())
    rows[0] = replace(rows[0], truth=replace(TRUTH, beta=0.10))
    assert not _evaluate(rows).predicates["9_provenance"]


@pytest.mark.parametrize("hits,passes", [(8, True), (7, False)])
@pytest.mark.parametrize("name", phase0.P01_DIMENSION_NAMES)
def test_dimension_hit_integer_endpoint(hits: int, passes: bool, name: str) -> None:
    rows = list(_rows())
    for index in range(hits, 10):
        profiles = tuple(
            replace(p, identified=False) if p.dimension == name else p for p in rows[index].profiles
        )
        rows[index] = replace(rows[index], profiles=profiles)
    result = _evaluate(rows)
    assert result.hits[name] == hits
    assert result.predicates["5_dimension_hits"] is passes
    assert result.boundary_counts[name] == 0


@pytest.mark.parametrize("joint,passes", [(6, True), (5, False)])
def test_joint_integer_endpoint(joint: int, passes: bool) -> None:
    rows = list(_rows())
    for index in range(joint, 10):
        dimension = phase0.P01_DIMENSION_NAMES[(index - joint) % 4]
        rows[index] = replace(
            rows[index],
            profiles=tuple(
                replace(p, identified=False) if p.dimension == dimension else p
                for p in rows[index].profiles
            ),
        )
    result = _evaluate(rows)
    assert result.joint_hits == joint
    assert result.predicates["6_joint_hits"] is passes
    assert result.predicates["5_dimension_hits"]  # Marginal hits still >=8, independently.


@pytest.mark.parametrize("boundary,passes", [(2, True), (3, False)])
@pytest.mark.parametrize("dimension", range(4))
def test_boundary_integer_endpoint_is_own_code_path(
    boundary: int, passes: bool, dimension: int
) -> None:
    rows = [
        replace(row, profiles=tuple(replace(p, identified=False) for p in row.profiles))
        for row in _rows()
    ]
    spec = study.StudyConfig().dimensions[dimension]
    for index in range(boundary):
        rows[index] = replace(
            rows[index],
            selected=replace(TRUTH, **{spec.name: spec.candidates[0]}),
            profiles=tuple(replace(p, identified=False) for p in rows[index].profiles),
        )
    result = _evaluate(rows)
    assert result.boundary_counts[spec.name] == boundary
    assert result.predicates["8_boundaries"] is passes
    assert not result.predicates["5_dimension_hits"]  # No implication used to compute P8.
    assert (
        sum(
            row["selected_at_grid_boundary"] for row in result.rows if row["dimension"] == spec.name
        )
        == boundary
    )


@pytest.mark.parametrize("dimension", range(4))
@pytest.mark.parametrize("direction", [-1, 1])
def test_decimal_tolerance_and_bias_exactly_at_limits(dimension: int, direction: int) -> None:
    spec = study.StudyConfig().dimensions[dimension]
    # Five one-step signed errors and five zero errors => mean bias = half-step = limit.
    endpoint = spec.candidates[2 + direction]
    rows = tuple(
        replace(row, selected=replace(TRUTH, **{spec.name: endpoint})) if index < 5 else row
        for index, row in enumerate(_rows())
    )
    result = _evaluate(rows)
    assert result.hits[spec.name] == 10
    assert result.mean_bias[spec.name] == direction * spec.exact_bias_limit()
    assert result.predicates["7_bias"]
    assert all(row["within_tolerance_hit"] for row in result.rows)
    rows = list(rows)
    rows[5] = replace(rows[5], selected=replace(TRUTH, **{spec.name: endpoint}))
    assert not _evaluate(rows).predicates["7_bias"]


def test_decimal_cancellation_is_exact() -> None:
    rows = list(_rows())
    for index, value in enumerate((0.175, 0.325) * 5):
        rows[index] = replace(
            rows[index], selected=replace(TRUTH, asymptomatic_detection_probability=value)
        )
    result = _evaluate(rows)
    assert result.mean_bias["asymptomatic_detection_probability"] == Decimal("0")
    assert result.predicates["7_bias"]
    assert result.hits["asymptomatic_detection_probability"] == 10


@pytest.mark.parametrize("kind", study.TOTAL_FIELDS)
def test_counter_rejects_before_dispatch_and_requires_exact_count(kind: str) -> None:
    counter = study.WorkCounter("B")
    cap = {
        "cells": 625,
        "latent_calls": 85,
        "observation_transforms": 1885,
        "serosurvey_samples": 0,
        "builds": 13,
    }[kind]
    for _ in range(cap):
        counter.dispatch(kind)
    before = dict(counter.measured)
    with pytest.raises(study.BudgetError, match="before dispatch"):
        counter.dispatch(kind)
    assert counter.measured == before
    assert not counter.exact()


@pytest.fixture
def baseline_fakes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    calls: dict[str, Any] = {"build": [], "latent": [], "observe": [], "events": []}

    def fake_build(root: Path, mode: str, seed: int, destination: Path, **kwargs: Any) -> Any:
        assert root == ROOT and mode == "ci" and kwargs == {"write_m4": True}
        calls["build"].append(seed)
        calls["events"].append("build")
        m2, m3, m4 = frozen.PROCESS_HASHES[seed]
        stages = []
        for name, digest in (("m2", m2), ("m3", m3)):
            path = destination / name
            path.mkdir(parents=True)
            diagnostic = {}
            if seed == 82003 and name == "m2":
                diagnostic = {"private_assignment_residual_fallback": {"used": True}}
            if seed == 82007 and name == "m3":
                diagnostic = {"geography": {"destination_reassignment_fallback": {"used": True}}}
            (path / "diagnostics.json").write_text(json.dumps(diagnostic))
            stages.append(
                SimpleNamespace(
                    artifact_directory=path,
                    manifest=SimpleNamespace(seed=seed, mode=mode, logical_content_hash=digest),
                )
            )
        generated = SimpleNamespace(
            config=SimpleNamespace(seed=seed, mode=mode),
            m2_input=stages[0],
            m3_input=stages[1],
            logical_content_hash=m4,
            agent_ids=[str(i) for i in range(3000)],
        )
        return SimpleNamespace(generated=generated)

    def fake_run(parent: Any, config: OutbreakRunConfig, parameters: Any) -> Any:
        assert isinstance(config, OutbreakRunConfig)
        assert config.seed == parent.config.seed
        assert config.mode == "ci" and config.duration_days == 30
        assert config.initial_seed_count == 0
        assert config.import_rate_per_day == 0.0
        assert list(config.import_schedule.values()) == [10]
        assert config.latent_duration.family == "constant" and config.latent_duration.mean_days == 2
        assert (
            config.infectious_duration.family == "constant"
            and config.infectious_duration.mean_days == 5
        )
        assert config.symptomatic_probability == 0.6 and not config.waning_enabled
        assert tuple(config.route_multipliers.values()) == (1.0,) * 11
        calls["latent"].append(config)
        calls["events"].append("latent")
        return SimpleNamespace(
            generated=parent,
            config=config,
            logical_content_hash="latent-mocked",
            transmission_events=tuple([{"imported": True}] * 10 + [{"source_kind": "local"}]),
            diagnostics={
                "natural_history": {"chronology_passed": True},
                "states": {"conserved": True},
                "benchmark": {"runtime_seconds": 0.25},
            },
        )

    def fake_observe(latent: Any, config: ObservationConfig) -> Any:
        assert isinstance(config, ObservationConfig)
        assert config.reporting_delay.days == (2,) and config.detection_delay.days == (0,)
        assert config.day_of_week_effect == (1.0,) * 7
        assert config.analysis_horizon_tail_days == 4
        calls["observe"].append((latent, config))
        calls["events"].append("observe")
        start = date.fromisoformat(next(iter(latent.config.import_schedule))) + timedelta(days=4)
        return SimpleNamespace(
            latent_run=latent,
            config=config,
            observation_events=[
                {
                    "report_date": (start + timedelta(days=day)).isoformat(),
                    "symptomatic": day % 2 == 0,
                }
                for day in range(3)
            ],
            diagnostics={
                "no_report_before_infection": True,
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
            },
        )

    monkeypatch.setattr(study, "build_parent", fake_build)
    monkeypatch.setattr(study, "run_outbreak", fake_run)
    monkeypatch.setattr(study, "observe_latent_run", fake_observe)
    calls["fake_build"], calls["fake_run"], calls["fake_observe"] = (
        fake_build,
        fake_run,
        fake_observe,
    )
    return calls


def test_baseline_orchestration_counts_blind_boundary_and_disclosures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    baseline_fakes: Any,
) -> None:
    calls = baseline_fakes
    original_fit, original_persist = study.fit_blind, study.persist_blind_estimate
    original_join = study._truth_diagnostics_from_result
    inputs = []

    def recording_fit(*args: Any, **kwargs: Any) -> Any:
        calls["events"].append("fit")
        assert len(calls["observe"]) == 1885
        inputs.append((args, kwargs))
        assert isinstance(args[0], phase0.ObservedTables)
        assert len(args[1]) == len(args[2]) == 625
        assert set(kwargs) == {"R", "T", "candidate_config_hashes"}
        return original_fit(*args, **kwargs)

    def recording_persist(path: Path, fit: Any) -> str:
        calls["events"].append("persist")
        return original_persist(path, fit)

    def recording_diagnostics(*args: Any, **kwargs: Any) -> Any:
        assert calls["events"].count("persist") == 10
        calls["events"].append("join")
        return original_join(*args, **kwargs)

    monkeypatch.setattr(study, "fit_blind", recording_fit)
    monkeypatch.setattr(study, "persist_blind_estimate", recording_persist)
    monkeypatch.setattr(study, "_truth_diagnostics_from_result", recording_diagnostics)
    generation, evaluation = study.run_baseline_arm(
        CONFIG, PREDECLARATION, tmp_path / "work", root=ROOT
    )
    assert calls["build"] == [*range(82001, 82011), 83001, 83002, 83003]
    assert len(calls["latent"]) == 85
    assert len(calls["observe"]) == 1885
    assert generation.measured == {
        "cells": 625,
        "latent_calls": 85,
        "observation_transforms": 1885,
        "serosurvey_samples": 0,
        "builds": 13,
    }
    assert len(generation.candidate_latents) == 75
    assert len(generation.replicate_provenance) == 1875
    assert len(inputs) == len(generation.blind_fits) == 10
    assert max(i for i, event in enumerate(calls["events"]) if event == "persist") < min(
        i for i, event in enumerate(calls["events"]) if event == "join"
    )
    assert all(
        run.beta == 0.08 and next(iter(run.import_schedule)) == "2025-01-08"
        for run in calls["latent"][:10]
    )
    assert all(
        t.dates == phase0.observation_dates(date(2025, 1, 6), 30)
        for t in generation.target_tables.values()
    )
    for seed in (83001, 83002, 83003):
        observed = [
            (latent, config) for latent, config in calls["observe"] if latent.config.seed == seed
        ]
        assert len(observed) == 625
        assert len({id(latent) for latent, _ in observed}) == 25
        assert len({config.observation_seed for _, config in observed}) == 1
        assert {config.observation_config_id for _, config in observed} == {"v13-g35b-fit"}
    assert {config.observation_config_id for _, config in calls["observe"][:10]} == {
        "v13-g35b-target"
    }
    for seed, fit in generation.blind_fits.items():
        stored = json.loads(generation.blind_paths[seed].read_bytes())
        assert stored == fit.as_dict()
        assert (
            generation.blind_file_hashes[seed]
            == hashlib.sha256(generation.blind_paths[seed].read_bytes()).hexdigest()
        )
    assert evaluation.predicates["1_complete"]
    assert evaluation.predicates["2_truth_viability"]
    assert evaluation.predicates["3_chronology_conservation"]
    assert evaluation.predicates["9_provenance"]
    assert evaluation.predicates["10_measured_caps"]
    disclosures = generation.disclosures
    assert disclosures["fallback_built_targets"] == 2
    assert disclosures["fallback_built_candidates"] == 0
    assert len(disclosures["latent_runtimes"]) == 85
    assert set(disclosures["phase_wall_time_seconds"]) == {
        "build",
        "latent",
        "transform",
        "scoring",
    }
    with (tmp_path / "work/g35b_B_recovery.csv").open() as handle:
        records = list(csv.DictReader(handle))
    assert len(records) == 40
    assert {r["target_seed"] for r in records if r["population_fallback_m2"] == "TRUE"} == {"82003"}
    assert {r["target_seed"] for r in records if r["population_fallback_m3"] == "TRUE"} == {"82007"}
    # Fallback values cannot affect a gate: they are attached only after evaluation.
    altered = replace(
        generation,
        parent_lineage={
            seed: {**lineage, "population_fallback_m2": True, "population_fallback_m3": True}
            for seed, lineage in generation.parent_lineage.items()
        },
    )
    assert study.join_baseline(altered, tmp_path / "other").predicates == evaluation.predicates
    assert (
        json.loads((tmp_path / "work/g35b_B_disclosures.json").read_bytes())["measured_counters"]
        == generation.measured
    )
    incomplete = replace(generation, candidate_latents={})
    assert not study.join_baseline(incomplete, tmp_path / "incomplete").predicates["1_complete"]


@pytest.mark.parametrize("damage", ["m2", "m3", "m4", "missing", "build_exception"])
def test_parent_mismatch_stops_before_any_latent_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    baseline_fakes: Any,
    damage: str,
) -> None:
    def damaged(*args: Any, **kwargs: Any) -> Any:
        if damage == "build_exception":
            raise RuntimeError("synthetic build failure")
        result = baseline_fakes["fake_build"](*args, **kwargs)
        if damage in {"m2", "m3"}:
            getattr(result.generated, damage + "_input").manifest.logical_content_hash = "wrong"
        elif damage == "m4":
            result.generated.logical_content_hash = "wrong"
        else:
            del result.generated.m2_input
        return result

    monkeypatch.setattr(study, "build_parent", damaged)
    with pytest.raises(study.CampaignError, match="predicate 1"):
        study.generate_baseline(CONFIG, PREDECLARATION, tmp_path / "work", root=ROOT)
    assert not baseline_fakes["latent"] and not baseline_fakes["observe"]


@pytest.mark.parametrize("damage", ["latent_config", "observed_config", "rng", "latent_reference"])
def test_returned_metadata_is_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    baseline_fakes: Any,
    damage: str,
) -> None:
    if damage == "latent_config":

        def damaged_run(*args: Any, **kwargs: Any) -> Any:
            result = baseline_fakes["fake_run"](*args, **kwargs)
            del result.config
            return result

        monkeypatch.setattr(study, "run_outbreak", damaged_run)
    else:

        def damaged_observation(*args: Any, **kwargs: Any) -> Any:
            result = baseline_fakes["fake_observe"](*args, **kwargs)
            if damage == "observed_config":
                del result.config
            elif damage == "rng":
                del result.diagnostics["observation_rng"]
            else:
                result.latent_run = object()
            return result

        monkeypatch.setattr(study, "observe_latent_run", damaged_observation)
    with pytest.raises(study.CampaignError, match="metadata|namespace evidence"):
        study.generate_baseline(CONFIG, PREDECLARATION, tmp_path / "work", root=ROOT)
    assert len(baseline_fakes["latent"]) == 1


def test_corrupt_persisted_estimate_prevents_all_truth_joins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    baseline_fakes: Any,
) -> None:
    generation = study.generate_baseline(CONFIG, PREDECLARATION, tmp_path / "work", root=ROOT)
    assert len(baseline_fakes["latent"]) == 85
    generation.blind_paths[82010].write_text("{}")

    def forbidden_truth(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("truth join must not happen before *all* read-backs")

    monkeypatch.setattr(study, "_truth_diagnostics_from_result", forbidden_truth)
    with pytest.raises(study.CampaignError, match="read-back"):
        study.join_baseline(generation, tmp_path / "joined")


def test_runtime_config_mutation_cannot_bypass_caps() -> None:
    with pytest.raises(study.BudgetError, match="frozen"):
        study.plan_workload(replace(study.StudyConfig(), duration_days=49))
