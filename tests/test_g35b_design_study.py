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


def test_config_lf_bytes_match_independent_digest() -> None:
    content = CONFIG.read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(content).hexdigest() == frozen.CONFIG_SHA256
    assert _payload()["implementation"]["implemented_arms"] == ["B", "i", "ii", "iii"]


@pytest.fixture
def committed_campaign_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Emulate the director's future commit of the edited config, without committing."""
    original = study.committed_document_bytes

    def committed(path: Path, **kwargs: Any) -> bytes:
        if path.resolve() == CONFIG.resolve():
            return CONFIG.read_bytes().replace(b"\r\n", b"\n")
        return original(path, **kwargs)

    monkeypatch.setattr(study, "committed_document_bytes", committed)


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


def test_exact_dry_run_and_execute_requires_arguments(capsys: Any) -> None:
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


@pytest.mark.parametrize("hook", [study.arm_i, study.arm_ii, study.arm_iii])
def test_factor_hooks_have_explicit_implementation_boundary(hook: Any) -> None:
    # Implemented arms require completed baseline inputs; no implicit campaign.
    assert set(inspect.signature(hook).parameters) == {"baseline", "config", "work_dir", "root"}
    with pytest.raises(TypeError, match="required positional arguments"):
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


@pytest.mark.parametrize(
    "values,expected_range,expected_median",
    [((9.0, 1.0, 3.0, 5.0), 8.0, 4.0), ((2.0,) * 4, 0.0, 2.0)],
)
def test_four_batch_spread_hand_fixture(
    values: tuple[float, ...], expected_range: float, expected_median: float
) -> None:
    assert study.batch_objective_spread(values) == {
        "label": "stochastic_replicate_variation",
        "range": expected_range,
        "median": expected_median,
    }
    with pytest.raises(study.CampaignError, match="four"):
        study.batch_objective_spread(values[:3])


def test_four_batch_offset_agreement_uses_offset_profiles() -> None:
    target = phase0.ObservedTables(("2025-01-06",), (0.0,), (0.0,))
    high = replace(target, symptomatic=(3.0,), asymptomatic=(3.0,))
    other = replace(TRUTH, inoculation_day_offset=3)
    # Nuisance beta ties globally, but offset 2 uniquely minimizes P(o).
    grid = tuple(replace(cell, beta=beta) for beta in (0.08, 0.10) for cell in (TRUTH, other))

    def fit_at(offset: int | None) -> Any:
        return study.fit_blind(
            target,
            grid,
            {
                c: (target if offset is None or c.inoculation_day_offset == offset else high,) * 3
                for c in grid
            },
            R=3,
            T=1,
        )

    tied_global = fit_at(2)
    tied_profile = fit_at(None)
    different = fit_at(3)
    profile = next(p for p in tied_global.profiles if p.dimension == "inoculation_day_offset")
    assert tied_global.numerical_tie and tied_global.selected is None
    assert profile.identified and not profile.numerical_tie
    assert study.batch_offset_agreement((tied_global,) * 4)
    assert not study.batch_offset_agreement((tied_global,) * 3 + (tied_profile,))
    assert not study.batch_offset_agreement((tied_global,) * 3 + (different,))
    assert not study.batch_offset_agreement((tied_global,) * 3)
    detail = study._offset_descriptive(tied_global)
    assert detail["reprofiled_offset"] == 2
    assert not detail["offset_profile_tie"]
    assert detail["offset_profile_identified"]
    assert detail["global_selected_offset"] is None
    assert study._offset_descriptive(tied_profile)["reprofiled_offset"] is None
    assert study._offset_descriptive(tied_profile)["offset_profile_tie"]
    # Identification is disclosed, never required for agreement.
    unidentified = replace(
        tied_global,
        profiles=tuple(replace(p, identified=False) for p in tied_global.profiles),
    )
    assert study.batch_offset_agreement((unidentified,) * 4)
    assert not study._offset_descriptive(unidentified)["offset_profile_identified"]


def test_descriptive_counter_checks_exact_scaled_work() -> None:
    assert study.plan_workload(study.StudyConfig())["descriptive_loss_evaluations"] == 31250
    target = phase0.ObservedTables(("2025-01-06",), (0.0,), (0.0,))
    fit = study.fit_blind(target, (TRUTH,), {TRUTH: (target,) * 3}, R=3, T=1)
    # Five descriptive fits × two mock targets × one cell; the R=12 gate is separate.
    counter = study.DescriptiveLossCounter(5 * 2 * 1)
    with pytest.raises(study.BudgetError, match="exact cap"):
        counter.check_exact()
    for _ in range(10):
        counter.record(fit)
    counter.check_exact()
    assert counter.measured == 10
    with pytest.raises(study.BudgetError, match="cap exceeded"):
        counter.record(fit)


def test_arm_i_generation_nesting_counts_retention_and_blind_join(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, baseline_fakes: Any
) -> None:
    calls = baseline_fakes
    tables_by_transform = {}

    def distinct_observation(latent: Any, config: ObservationConfig) -> Any:
        result = calls["fake_observe"](latent, config)
        # Distinct report counts make a misplaced replicate observable in the library.
        if latent.config.seed >= 83001:
            result.observation_events *= latent.config.seed - 83000
        cell = phase0.CandidateCell(
            latent.config.beta,
            (date.fromisoformat(next(iter(latent.config.import_schedule))) - date(2025, 1, 6)).days,
            config.parameters["symptomatic_detection_probability"].value,
            config.parameters["asymptomatic_detection_probability"].value,
        )
        tables_by_transform[cell, latent.config.seed] = phase0.observed_tables_from_events(
            result.observation_events, dates=phase0.observation_dates(date(2025, 1, 6), 30)
        )
        return result

    monkeypatch.setattr(study, "observe_latent_run", distinct_observation)
    baseline = study.generate_baseline(CONFIG, PREDECLARATION, tmp_path / "B", root=ROOT)
    baseline_blind_bytes = {seed: path.read_bytes() for seed, path in baseline.blind_paths.items()}
    observed_before = len(calls["observe"])
    original_fit, original_loss = study.fit_blind, study.loss
    fit_inputs, loss_counts = [], {3: 0, 6: 0, 12: 0}
    persisted = []
    original_persist = study.persist_blind_estimate

    def counted_loss(target: Any, predictions: Any, R: int, T: int) -> float:
        loss_counts[R] += 1
        return original_loss(target, predictions, R, T)

    def recording_fit(*args: Any, **kwargs: Any) -> Any:
        assert len(calls["observe"]) == observed_before + 5625
        assert any(args[0] is table for table in baseline.target_tables.values())
        assert set(kwargs) == {"R", "T", "candidate_config_hashes"}
        assert kwargs["T"] == 34
        assert tuple(args[1]) == baseline.config.candidate_grid
        assert set(args[2]) == set(args[1])
        assert all(len(tables) == kwargs["R"] for tables in args[2].values())
        fit_inputs.append((args, kwargs))
        return original_fit(*args, **kwargs)

    def recording_persist(path: Path, fit: Any) -> str:
        persisted.append(path)
        return original_persist(path, fit)

    class UnreadTruth(dict):
        def __getitem__(self, key: Any) -> Any:
            raise AssertionError("generation must not read target latent events")

    with monkeypatch.context() as blind:
        blind.setattr(study, "fit_blind", recording_fit)
        blind.setattr(study, "loss", counted_loss)
        blind.setattr(study, "persist_blind_estimate", recording_persist)
        guarded_baseline = replace(baseline, target_outputs=UnreadTruth(baseline.target_outputs))
        generation = study.arm_i(guarded_baseline, baseline.config, tmp_path / "i", root=ROOT)
    assert generation.baseline is guarded_baseline
    generation = replace(generation, baseline=baseline)
    assert len(fit_inputs) == len(persisted) == 60  # 10 gate + 50 descriptive, no duplicate R=12.
    assert [kwargs["R"] for _, kwargs in fit_inputs] == [12, 3, 3, 3, 3, 6] * 10
    assert loss_counts == {3: 25000, 6: 6250, 12: 6250}
    assert generation.measured == {
        "cells": 625,
        "latent_calls": 225,
        "observation_transforms": 5625,
        "serosurvey_samples": 0,
        "builds": 9,
    }
    assert calls["build"][13:] == list(range(83004, 83013))
    assert len(calls["latent"]) == 85 + 225
    assert len(calls["observe"]) == 1885 + 5625
    assert len(generation.generated_parents) == 9
    assert len(generation.candidate_latents) == 225
    assert len(generation.replicate_provenance) == 5625
    assert study.ARM_I_REPLICATE_ORDER == tuple(range(83001, 83013))
    assert all(
        baseline.blind_paths[s].read_bytes() == content
        for s, content in baseline_blind_bytes.items()
    )
    by_cell = {cell: [] for cell in baseline.config.candidate_grid}
    for record in (*baseline.replicate_provenance, *generation.replicate_provenance):
        by_cell[phase0.CandidateCell(**record["cell"])].append(record)
    for cell, tables in generation.candidate_prediction_library.items():
        assert len(tables) == 12
        assert all(
            a is b
            for a, b in zip(tables[:3], baseline.candidate_prediction_library[cell], strict=True)
        )
        assert tuple(r["process_seed"] for r in by_cell[cell]) == study.ARM_I_REPLICATE_ORDER
        assert tuple(r["observation_seed"] for r in by_cell[cell]) == tuple(range(93001, 93013))
        assert [r["batch"] for r in by_cell[cell]] == [
            name for name, _, _ in frozen.CANDIDATE_BATCHES for _ in range(3)
        ]
        for record, table in zip(by_cell[cell], tables, strict=True):
            seed = record["process_seed"]
            assert table == tables_by_transform[cell, seed]
            assert (
                record["table_sha256"]
                == hashlib.sha256(phase0._compact_json_bytes(table.as_dict())).hexdigest()
            )
            assert record["observation_config"]["observation_config_id"] == "v13-g35b-fit"
            assert record["run_config"]["seed"] == seed
            assert record["observation_rng"]["stream_fingerprint"]
            assert (
                tuple(record["population_lineage"][key] for key in ("m2", "m3", "m4"))
                == frozen.PROCESS_HASHES[seed]
            )
            assert record["population_lineage"]["population_fallback_m2"] is False
            assert record["population_lineage"]["population_fallback_m3"] is False
    for seed in range(83004, 83013):
        observed = [
            (latent, config)
            for latent, config in calls["observe"][observed_before:]
            if latent.config.seed == seed
        ]
        assert len(observed) == 625
        assert len({id(latent) for latent, _ in observed}) == 25
        assert {config.observation_seed for _, config in observed} == {seed + 10000}
        assert {config.observation_config_id for _, config in observed} == {"v13-g35b-fit"}
    for seed, fit in generation.blind_fits.items():
        direct = original_fit(
            baseline.target_tables[seed],
            baseline.config.candidate_grid,
            generation.candidate_prediction_library,
            R=12,
            T=34,
            candidate_config_hashes=generation.candidate_config_hashes,
        )
        assert fit == direct
        assert (
            generation.descriptive_fits[seed, "A"].loss_surface
            == baseline.blind_fits[seed].loss_surface
        )
        assert generation.descriptive_fits[seed, "A"] == baseline.blind_fits[seed]
        assert json.loads(generation.blind_paths[seed].read_bytes()) == fit.as_dict()
    for key, fit in generation.descriptive_fits.items():
        study._verify_blind_readback(
            generation.descriptive_paths[key], fit, generation.descriptive_file_hashes[key]
        )
        seed, batch = key
        start, stop = {
            "A": (0, 3),
            "B_prime": (3, 6),
            "C_prime": (6, 9),
            "D_prime": (9, 12),
            "A_union_B_prime": (0, 6),
        }[batch]
        expected_library = {
            cell: tables[start:stop]
            for cell, tables in generation.candidate_prediction_library.items()
        }
        expected_hashes = {
            cell: hashlib.sha256(
                phase0._compact_json_bytes(
                    [
                        {"run": record["run_config"], "observation": record["observation_config"]}
                        for record in records[start:stop]
                    ]
                )
            ).hexdigest()
            for cell, records in by_cell.items()
        }
        assert fit == original_fit(
            baseline.target_tables[seed],
            baseline.config.candidate_grid,
            expected_library,
            R=stop - start,
            T=34,
            candidate_config_hashes=expected_hashes,
        )
    description = generation.descriptives
    assert json.loads(generation.descriptives_path.read_bytes()) == description
    assert description["descriptive_loss_evaluations"] == 31250
    assert len(description["targets"]) == 10
    assert "interval" not in json.dumps(description).lower()
    # Flat detection dimensions tie globally, but every batch's offset profile
    # uniquely minimizes at the same offset for all ten fixture targets.
    assert description["four_batch_offset_agreement_count"] == 10
    for target in description["targets"]:
        assert set(target["reprofiled_offsets"]) == {
            "A",
            "B_prime",
            "C_prime",
            "D_prime",
            "A_union_B_prime",
            "all_twelve",
        }
        seed = target["target_seed"]
        assert (
            target["reprofiled_offsets"]["all_twelve"]["estimate_hash"]
            == generation.blind_fits[seed].estimate_hash
        )
        for index, spread in enumerate(target["fixed_tuple_spreads"]):
            values = sorted(
                generation.descriptive_fits[seed, batch].loss_surface[index].objective
                for batch, _, _ in frozen.CANDIDATE_BATCHES
            )
            assert spread["label"] == "stochastic_replicate_variation"
            assert spread["range"] == values[3] - values[0]
            assert spread["median"] == (values[1] + values[2]) / 2
    assert len(generation.disclosures["latent_runtimes"]) == 225
    assert generation.disclosures["fallback_built_targets"] == 2
    assert generation.disclosures["fallback_built_candidates"] == 0

    evaluated = []
    original_evaluate = study.evaluate_recovery

    def recording_evaluate(rows: Any, **kwargs: Any) -> Any:
        assert len(rows) == 10 and all(isinstance(row, phase0.RecoveryRow) for row in rows)
        assert set(kwargs) == {"execution_complete", "provenance_verified", "measured_equals_caps"}
        assert all(
            row.estimate_hash == generation.blind_fits[row.target_seed].estimate_hash
            for row in rows
        )
        evaluated.append((rows, kwargs))
        return original_evaluate(rows, **kwargs)

    monkeypatch.setattr(study, "evaluate_recovery", recording_evaluate)
    evaluation = study.join_arm_i(generation, tmp_path / "joined")
    assert len(evaluated) == 1
    assert evaluation.predicates["1_complete"] and evaluation.predicates["10_measured_caps"]
    assert evaluation.predicates["2_truth_viability"] and evaluation.predicates["9_provenance"]
    assert json.loads((tmp_path / "joined/g35b_i_descriptives.json").read_bytes()) == description
    assert (
        json.loads((tmp_path / "joined/g35b_i_disclosures.json").read_bytes())["measured_counters"]
        == generation.measured
    )
    with (tmp_path / "joined/g35b_i_recovery.csv").open() as handle:
        records = list(csv.DictReader(handle))
    assert len(records) == 40
    assert {r["target_seed"] for r in records if r["population_fallback_m2"] == "TRUE"} == {"82003"}
    assert {r["target_seed"] for r in records if r["population_fallback_m3"] == "TRUE"} == {"82007"}
    # Changing valid descriptives and fallback disclosures cannot feed gating.
    altered_description = {**description, "four_batch_offset_agreement_count": 0}
    altered_path = tmp_path / "altered-descriptives.json"
    altered_bytes = phase0._compact_json_bytes(altered_description)
    altered_path.write_bytes(altered_bytes)
    altered_baseline = replace(
        baseline,
        parent_lineage={
            seed: {**lineage, "population_fallback_m2": True, "population_fallback_m3": True}
            for seed, lineage in baseline.parent_lineage.items()
        },
    )
    altered = replace(
        generation,
        baseline=altered_baseline,
        descriptives=altered_description,
        descriptives_path=altered_path,
        descriptives_file_hash=hashlib.sha256(altered_bytes).hexdigest(),
    )
    assert study.join_arm_i(altered, tmp_path / "altered").predicates == evaluation.predicates
    assert evaluated[0] == evaluated[1]
    incomplete = replace(generation, candidate_latents={})
    assert not study.join_arm_i(incomplete, tmp_path / "incomplete-i").predicates["1_complete"]
    wrong_work = replace(generation, measured=baseline.measured)
    assert not study.join_arm_i(wrong_work, tmp_path / "wrong-work-i").predicates[
        "10_measured_caps"
    ]

    # A corrupt final-target record must stop before *any* target truth access.
    def forbidden_truth(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("all arm-(i) read-backs must precede truth")

    monkeypatch.setattr(study, "_truth_diagnostics_from_result", forbidden_truth)
    guarded = replace(generation, baseline=guarded_baseline)
    for path in (
        generation.blind_paths[82010],
        generation.descriptive_paths[82010, "D_prime"],
        generation.descriptive_paths[82010, "A_union_B_prime"],
        generation.descriptives_path,
    ):
        original = path.read_bytes()
        path.write_text("{}")
        with pytest.raises(study.CampaignError, match="read-back"):
            study.join_arm_i(guarded, tmp_path / "corrupt-i")
        path.write_bytes(original)


@pytest.mark.parametrize(
    "kind,tool",
    [
        ("builds", "build_parent"),
        ("latent_calls", "run_outbreak"),
        ("observation_transforms", "observe_latent_run"),
    ],
)
def test_arm_i_reserves_exception_slot_without_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, baseline_fakes: Any, kind: str, tool: str
) -> None:
    baseline = study.generate_baseline(CONFIG, PREDECLARATION, tmp_path / "B", root=ROOT)
    counter = study.WorkCounter("i")
    monkeypatch.setattr(study, "WorkCounter", lambda arm: counter if arm == "i" else None)
    calls = []

    def fails(*args: Any, **kwargs: Any) -> None:
        assert counter.measured[kind] == 1
        calls.append(args)
        raise RuntimeError("mock dispatch failed")

    monkeypatch.setattr(study, tool, fails)
    with pytest.raises((study.CampaignError, RuntimeError), match="mock dispatch failed"):
        study.arm_i(baseline, baseline.config, tmp_path / "i", root=ROOT)
    assert len(calls) == counter.measured[kind] == 1


def test_arm_i_verifies_new_parent_before_latent_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, baseline_fakes: Any
) -> None:
    baseline = study.generate_baseline(CONFIG, PREDECLARATION, tmp_path / "B", root=ROOT)

    def damaged(*args: Any, **kwargs: Any) -> Any:
        result = baseline_fakes["fake_build"](*args, **kwargs)
        result.generated.logical_content_hash = "wrong"
        return result

    monkeypatch.setattr(study, "build_parent", damaged)
    with pytest.raises(study.CampaignError, match="logical hash mismatch for 83004"):
        study.arm_i(baseline, baseline.config, tmp_path / "i", root=ROOT)
    assert len(baseline_fakes["latent"]) == 85
    assert len(baseline_fakes["observe"]) == 1885


def test_arm_i_rejects_incomplete_baseline_before_new_work(
    tmp_path: Path, baseline_fakes: Any
) -> None:
    baseline = study.generate_baseline(CONFIG, PREDECLARATION, tmp_path / "B", root=ROOT)
    with pytest.raises(study.CampaignError, match="completed baseline"):
        study.arm_i(replace(baseline, measured={}), baseline.config, tmp_path / "i", root=ROOT)
    assert len(baseline_fakes["build"]) == 13


def _install_arm_ii_fakes(calls: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    def run49(parent: Any, config: OutbreakRunConfig, parameters: Any) -> Any:
        assert isinstance(config, OutbreakRunConfig)
        assert config.duration_days == 49 and config.mode == "ci"
        assert config.seed == parent.config.seed
        assert config.initial_seed_count == 0 and config.import_rate_per_day == 0.0
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
        start = config.start_date
        return SimpleNamespace(
            generated=parent,
            config=config,
            logical_content_hash="latent49-mocked",
            transmission_events=tuple(
                [{"imported": True, "infection_date": (start + timedelta(days=2)).isoformat()}] * 10
                + [
                    {
                        "source_kind": "local",
                        "infection_date": (start + timedelta(days=8)).isoformat(),
                    },
                    {
                        "source_kind": "local",
                        "infection_date": (start + timedelta(days=45)).isoformat(),
                    },
                ]
            ),
            daily_epidemic=[
                {"date": (start + timedelta(days=t)).isoformat(), "new_infections": int(t == 41)}
                for t in range(49)
            ],
            diagnostics={
                "natural_history": {"chronology_passed": True},
                "states": {"conserved": True},
                "benchmark": {"runtime_seconds": 0.49},
            },
        )

    def observe49(latent: Any, config: ObservationConfig) -> Any:
        assert latent.config.duration_days == 49
        result = calls["fake_observe"](latent, config)
        result.observation_events.append({"report_date": "2025-02-27", "symptomatic": True})
        return result

    monkeypatch.setattr(study, "run_outbreak", run49)
    monkeypatch.setattr(study, "observe_latent_run", observe49)


@pytest.fixture
def arm_ii_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, baseline_fakes: Any) -> Any:
    baseline = study.generate_baseline(CONFIG, PREDECLARATION, tmp_path / "work", root=ROOT)
    # Supply faithful prefix dates without changing the U1/U2 fixture or its assertions.
    for output in baseline.target_outputs.values():
        output[0].transmission_events = tuple(
            {**event, "infection_date": "2025-01-08" if event.get("imported") else "2025-01-14"}
            for event in output[0].transmission_events
        )
    _install_arm_ii_fakes(baseline_fakes, monkeypatch)
    return baseline, baseline_fakes


@pytest.mark.parametrize("duration", [30, 48, 50, 56])
def test_arm_ii_rejects_nonfrozen_h_before_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, duration: int
) -> None:
    with pytest.raises(study.BudgetError, match="H = 49"):
        study._ArmIIConstructorConfig(duration_days=duration)
    # Even a modified declaration with a consistent H+4 calendar cannot dispatch.
    monkeypatch.setattr(
        frozen,
        "ARM_CAPS",
        tuple(
            (arm, R, duration, duration + 4, *rest) if arm == "ii" else (arm, R, H, T, *rest)
            for arm, R, H, T, *rest in frozen.ARM_CAPS
        ),
    )
    with pytest.raises(study.BudgetError, match="H = 49"):
        study.arm_ii(None, study.StudyConfig(), tmp_path, root=ROOT)  # type: ignore[arg-type]


def test_arm_ii_calendar_in_loss_and_fit() -> None:
    dates = phase0.observation_dates(date(2025, 1, 6), 49, 4)
    assert len(dates) == 53 and dates[-1] == "2025-02-27"
    table = phase0.ObservedTables(dates, (0.0,) * 53, (0.0,) * 53)
    late = replace(table, symptomatic=(0.0,) * 52 + (3.0,))
    # A contribution on the final tail date is scored with denominator 2*53.
    expected = (math.sqrt(3.0 + 3.0 / 8.0) - math.sqrt(3.0 / 8.0)) ** 2 / (2.0 * 53)
    assert study.loss(late, (table,) * 3, 3, 53) == expected
    fit = study.fit_blind(late, (TRUTH,), {TRUTH: (table,) * 3}, R=3, T=53)
    assert fit.minimum_objective == expected
    for wrong in (34, 52, 54):
        with pytest.raises(study.CampaignError, match="date count"):
            study.loss(table, (table,) * 3, 3, wrong)
        with pytest.raises(study.CampaignError, match="date count"):
            study.fit_blind(table, (TRUTH,), {TRUTH: (table,) * 3}, R=3, T=wrong)
    shorter = phase0.ObservedTables(dates[:34], (0.0,) * 34, (0.0,) * 34)
    shifted = replace(table, dates=phase0.observation_dates(date(2025, 1, 7), 49, 4))
    for other in (shorter, shifted):
        with pytest.raises(study.CampaignError, match="calendar"):
            study.fit_blind(table, (TRUTH,), {TRUTH: (other,) * 3}, R=3, T=53)


@pytest.mark.parametrize("change", [None, "event", "report", "channel"])
def test_prefix_identity_sorted_inclusive_cutoff_and_mismatches(change: str | None) -> None:
    start = date(2025, 1, 6)
    dates = phase0.observation_dates(start, 30)
    baseline = phase0.ObservedTables(dates, (0.0,) * 29 + (1.0,) + (0.0,) * 4, (0.0,) * 34)
    extended = phase0.ObservedTables(
        phase0.observation_dates(start, 49), baseline.symptomatic[:30] + (9.0,) * 23, (0.0,) * 53
    )
    events = [
        {"infection_date": "2025-01-08", "infected_agent_id": "a", "imported": True},
        {"infection_date": "2025-02-04", "infected_agent_id": "b", "source_kind": "local"},
    ]
    later = [{"infected_agent_id": "later", "infection_date": "2025-02-05"}, *reversed(events)]
    if change == "event":
        later[1] = {**later[1], "infected_agent_id": "changed"}
    if change == "report":
        extended = replace(extended, symptomatic=(0.0,) * 53)
    if change == "channel":
        extended = replace(
            extended, symptomatic=(0.0,) * 53, asymptomatic=(0.0,) * 29 + (1.0,) + (0.0,) * 23
        )
    result = study.prefix_identity(events, later, baseline, extended, start_date=start)
    assert result["prefix_last_date"] == "2025-02-04"
    assert result["result"] == ("identical" if change is None else "not identical")
    assert result["label"] == (
        "identical" if change is None else "seed-stream matched, realization not matched"
    )
    assert (result["transmission_sha256"]["B"] == result["transmission_sha256"]["ii"]) == (
        change != "event"
    )
    assert (result["report_count_sha256"]["B"] == result["report_count_sha256"]["ii"]) == (
        change not in {"report", "channel"}
    )
    # Independently serialize sorted full rows, including the event on day 29.
    assert (
        result["transmission_sha256"]["B"]
        == hashlib.sha256(
            (
                json.dumps(
                    sorted(
                        events,
                        key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")),
                    ),
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            ).encode()
        ).hexdigest()
    )


@pytest.mark.parametrize(
    "pulses,peak,crossed",
    [
        ({0: 3, 1: 2, 7: 3}, 1, True),  # trailing maxima 5 at days 1..6 and 7: earliest wins
        ({0: 1, 20: 1}, 0, True),  # separated equal maxima
        ({41: 4}, 41, True),
        ({42: 4}, 42, False),
        ({48: 4}, 48, False),
        ({}, 0, True),
    ],
)
def test_manipulation_check_hand_fixtures(pulses: Any, peak: int, crossed: bool) -> None:
    daily = [{"new_infections": pulses.get(t, 0)} for t in range(49)]
    assert study.manipulation_check(daily) == {"latent_peak_day": peak, "peak_crossed": crossed}


def test_arm_ii_generation_counts_retention_and_join(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, arm_ii_inputs: Any
) -> None:
    baseline, calls = arm_ii_inputs
    before = {seed: path.read_bytes() for seed, path in baseline.blind_paths.items()}
    original_fit = study.fit_blind
    fits, persisted = [], []
    original_persist = study.persist_blind_estimate

    def recording_fit(*args: Any, **kwargs: Any) -> Any:
        assert len(calls["latent"]) == 170 and len(calls["observe"]) == 3770
        assert kwargs["R"] == 3 and kwargs["T"] == 53
        assert all(len(table.dates) == 53 for tables in args[2].values() for table in tables)
        fits.append(args)
        return original_fit(*args, **kwargs)

    def recording_persist(path: Path, fit: Any) -> str:
        persisted.append(path)
        return original_persist(path, fit)

    class UnreadTruth(dict):
        def __getitem__(self, key: Any) -> Any:
            raise AssertionError("generation must not read target latent truth")

    with monkeypatch.context() as blind:
        blind.setattr(study, "fit_blind", recording_fit)
        blind.setattr(study, "persist_blind_estimate", recording_persist)
        guarded = replace(baseline, target_outputs=UnreadTruth(baseline.target_outputs))
        generation = study.arm_ii(guarded, baseline.config, tmp_path / "work", root=ROOT)
    assert generation.baseline is guarded
    generation = replace(generation, baseline=baseline)
    assert generation.config == baseline.config == study.StudyConfig()
    assert generation.generated_parents is baseline.generated_parents
    assert generation.parent_lineage is baseline.parent_lineage
    assert len(calls["build"]) == 13
    assert len(fits) == len(persisted) == 10
    assert generation.measured == {
        "cells": 625,
        "latent_calls": 85,
        "observation_transforms": 1885,
        "serosurvey_samples": 0,
        "builds": 0,
    }
    assert len(generation.candidate_latents) == 75
    assert len(generation.replicate_provenance) == 1875
    for seed, path in generation.blind_paths.items():
        assert path == tmp_path / "work/arm_ii/blind_estimates" / f"{seed}.json"
        study._verify_blind_readback(
            path, generation.blind_fits[seed], generation.blind_file_hashes[seed]
        )
        assert baseline.blind_paths[seed].read_bytes() == before[seed]
        assert generation.target_tables[seed].dates == phase0.observation_dates(
            date(2025, 1, 6), 49
        )
        assert generation.blind_fits[seed] == original_fit(
            generation.target_tables[seed],
            baseline.config.candidate_grid,
            generation.candidate_prediction_library,
            R=3,
            T=53,
            candidate_config_hashes=generation.candidate_config_hashes,
        )
    for seed in (*range(82001, 82011), *range(83001, 83004)):
        observed = [
            (latent, obs) for latent, obs in calls["observe"][1885:] if latent.config.seed == seed
        ]
        assert len(observed) == (1 if seed < 83000 else 625)
        assert len({id(latent) for latent, _ in observed}) == (1 if seed < 83000 else 25)
        for latent, obs in observed:
            assert latent.generated is baseline.generated_parents[seed]
            assert latent.config.duration_days == 49
            assert obs.observation_seed == seed + 10000
            assert obs.observation_config_id == (
                "v13-g35b-target" if seed < 83000 else "v13-g35b-fit"
            )
    records_by_cell: dict[Any, list[Any]] = {cell: [] for cell in baseline.config.candidate_grid}
    for record in generation.replicate_provenance:
        records_by_cell[phase0.CandidateCell(**record["cell"])].append(record)
    for cell, tables in generation.candidate_prediction_library.items():
        records = records_by_cell[cell]
        assert tuple(record["process_seed"] for record in records) == (83001, 83002, 83003)
        assert tuple(record["observation_seed"] for record in records) == (93001, 93002, 93003)
        for table, record in zip(tables, records, strict=True):
            seed = record["process_seed"]
            latent, run = generation.candidate_latents[seed, cell.beta, cell.inoculation_day_offset]
            assert record["run_config"] == run.model_dump(mode="json")
            assert record["run_config"]["duration_days"] == 49
            assert record["observation_config"]["observation_config_id"] == "v13-g35b-fit"
            assert record["batch"] == "A"
            assert record["population_lineage"] is baseline.parent_lineage[seed]
            assert record["observation_rng"]["stream_fingerprint"]
            assert (
                record["table_sha256"]
                == hashlib.sha256(phase0._compact_json_bytes(table.as_dict())).hexdigest()
            )
        assert (
            generation.candidate_config_hashes[cell]
            == hashlib.sha256(
                phase0._compact_json_bytes(
                    [
                        {"run": r["run_config"], "observation": r["observation_config"]}
                        for r in records
                    ]
                )
            ).hexdigest()
        )
    assert generation.disclosures["phase_wall_time_seconds"]["build"] == 0.0
    assert set(generation.disclosures["phase_wall_time_seconds"]) == {
        "build",
        "latent",
        "transform",
        "scoring",
    }
    assert generation.disclosures["arm_wall_time_seconds"] >= sum(
        generation.disclosures["phase_wall_time_seconds"].values()
    )
    assert len(generation.disclosures["latent_runtimes"]) == 85
    assert all(r["runtime_seconds"] == 0.49 for r in generation.disclosures["latent_runtimes"])
    assert generation.disclosures["fallback_built_targets"] == 2
    assert generation.disclosures["fallback_built_candidates"] == 0

    evaluated = []
    original_evaluate, original_truth = (
        study.evaluate_recovery,
        study._truth_diagnostics_from_result,
    )

    def recording_truth(latent: Any, observed: Any, table: Any, **kwargs: Any) -> Any:
        seed = latent.config.seed
        assert latent is generation.target_outputs[seed][0]
        assert table is generation.target_tables[seed] and len(table.dates) == 53
        assert latent.config.duration_days == 49
        return original_truth(latent, observed, table, **kwargs)

    def recording_evaluate(rows: Any, **kwargs: Any) -> Any:
        assert set(kwargs) == {"execution_complete", "provenance_verified", "measured_equals_caps"}
        assert all(isinstance(row, phase0.RecoveryRow) for row in rows)
        evaluated.append((rows, kwargs))
        return original_evaluate(rows, **kwargs)

    monkeypatch.setattr(study, "evaluate_recovery", recording_evaluate)
    monkeypatch.setattr(study, "_truth_diagnostics_from_result", recording_truth)
    evaluation = study.join_arm_ii(generation, tmp_path / "joined")
    assert evaluation.predicates["1_complete"] and evaluation.predicates["10_measured_caps"]
    assert evaluation.predicates["2_truth_viability"] and evaluation.predicates["9_provenance"]
    description = json.loads((tmp_path / "joined/g35b_ii_descriptives.json").read_bytes())
    assert description["factor_delivered"] == "factor delivered for 10/10 targets"
    assert all(
        t["prefix_identity"]["result"] == "identical" and t["latent_peak_day"] == 41
        for t in description["targets"]
    )
    assert "interval" not in json.dumps(description).lower()
    assert (
        json.loads((tmp_path / "joined/g35b_ii_disclosures.json").read_bytes())
        == generation.disclosures
    )
    with (tmp_path / "joined/g35b_ii_recovery.csv").open() as handle:
        serial = list(csv.DictReader(handle))
    assert len(serial) == 40
    assert {r["target_seed"] for r in serial if r["population_fallback_m2"] == "TRUE"} == {"82003"}
    assert {r["target_seed"] for r in serial if r["population_fallback_m3"] == "TRUE"} == {"82007"}
    # Only the descriptive surfaces change; evaluate_recovery receives identical inputs.
    for output in baseline.target_outputs.values():
        output[0].transmission_events = ()
    for output in generation.target_outputs.values():
        output[0].daily_epidemic = [{"new_infections": int(t == 42)} for t in range(49)]
    assert study.join_arm_ii(generation, tmp_path / "changed").predicates == evaluation.predicates
    assert evaluated[0] == evaluated[1]
    changed = json.loads((tmp_path / "changed/g35b_ii_descriptives.json").read_bytes())
    assert changed["factor_delivered"] == "factor delivered for 0/10 targets"
    assert all(
        t["prefix_identity"]["label"] == "seed-stream matched, realization not matched"
        for t in changed["targets"]
    )
    assert not study.join_arm_ii(
        replace(generation, candidate_latents={}), tmp_path / "missing"
    ).predicates["1_complete"]
    assert not study.join_arm_ii(
        replace(generation, measured=baseline.measured), tmp_path / "counts"
    ).predicates["10_measured_caps"]

    def forbidden_truth(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("every arm-(ii) read-back must precede all truth access")

    monkeypatch.setattr(study, "_truth_diagnostics_from_result", forbidden_truth)
    generation.blind_paths[82010].write_text("{}")
    with pytest.raises(study.CampaignError, match="read-back"):
        study.join_arm_ii(
            replace(generation, target_outputs=UnreadTruth(generation.target_outputs)),
            tmp_path / "corrupt",
        )


@pytest.mark.parametrize(
    "call_index,damage", [(1, "missing"), (1, "duration"), (11, "duration"), (85, "duration")]
)
def test_arm_ii_requires_returned_49_day_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arm_ii_inputs: Any,
    call_index: int,
    damage: str,
) -> None:
    baseline, calls = arm_ii_inputs
    original = study.run_outbreak
    count = 0

    def damaged(*args: Any, **kwargs: Any) -> Any:
        nonlocal count
        result = original(*args, **kwargs)
        count += 1
        if count == call_index:
            if damage == "missing":
                del result.config
            else:
                result.config = result.config.model_copy(update={"duration_days": 30})
        return result

    monkeypatch.setattr(study, "run_outbreak", damaged)
    with pytest.raises(study.CampaignError, match="returned config/parent metadata"):
        study.arm_ii(baseline, baseline.config, tmp_path / "ii", root=ROOT)
    assert count == call_index and len(calls["build"]) == 13


def test_arm_ii_preserves_baseline_and_arm_i_records_in_shared_work_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, baseline_fakes: Any
) -> None:
    baseline = study.generate_baseline(CONFIG, PREDECLARATION, tmp_path / "B", root=ROOT)
    first = study.arm_i(baseline, baseline.config, tmp_path, root=ROOT)
    paths = [
        *baseline.blind_paths.values(),
        *first.blind_paths.values(),
        *first.descriptive_paths.values(),
        first.descriptives_path,
    ]
    content = {path: path.read_bytes() for path in paths}
    _install_arm_ii_fakes(baseline_fakes, monkeypatch)
    second = study.arm_ii(baseline, baseline.config, tmp_path, root=ROOT)
    assert all(path.read_bytes() == original for path, original in content.items())
    assert not set(second.blind_paths.values()).intersection(paths)


@pytest.mark.parametrize("damage", ["measured", "target_parent", "candidate_parent"])
def test_arm_ii_requires_completed_baseline_before_new_work(
    tmp_path: Path, arm_ii_inputs: Any, damage: str
) -> None:
    baseline, calls = arm_ii_inputs
    if damage == "measured":
        baseline = replace(baseline, measured={})
    else:
        seed = 82010 if damage == "target_parent" else 83003
        baseline = replace(
            baseline,
            generated_parents={
                s: parent for s, parent in baseline.generated_parents.items() if s != seed
            },
        )
    with pytest.raises(study.CampaignError, match="completed baseline"):
        study.arm_ii(baseline, baseline.config, tmp_path / "ii", root=ROOT)
    assert len(calls["latent"]) == 85 and len(calls["observe"]) == 1885


def test_serosurvey_a5_golden_digest_order() -> None:
    """SHA-256 UTF-8 digests for the literal 83001|95001|v13-g35b-sero-fit|serosurvey| prefix.

    a: 8ea8574d6eaeb5714a985e56e26739d36a43ade92b51a7a9e69dcee5ac5de3df
    b: 8e36fc4e584ced0135c919d0d46496d23413a5190f328d6509c0387165adba8a
    c: 1d785c7e6d769ba49982d0130bcb9f9759b16e7882bd0b7214f565a22bc9563f
    d: a2bca54f2a3dc00d69eda00f9edf6c3aa50cacd3e3bac5e88320e8d3c7319038
    e: f69ba99743b9e0b4b916e6dea3597e5b44b26bf9e4183244fd7fe5192162dda1
    Ascending hexadecimal order is therefore c, b, a, d, e.
    """
    assert study.serosurvey_sample_ids(tuple("abcde"), 83001, 95001, "v13-g35b-sero-fit", 5) == (
        "c",
        "b",
        "a",
        "d",
        "e",
    )
    assert study.serosurvey_sample_ids(tuple("edcba"), 83001, 95001, "v13-g35b-sero-fit", 3) == (
        "c",
        "b",
        "a",
    )


def test_serosurvey_census_independent_daily_crosscheck_and_inclusive_date() -> None:
    events = [
        {"infected_agent_id": "a", "infection_date": "2025-01-06", "seeded": True},
        {"infected_agent_id": "b", "infection_date": "2025-01-08", "imported": True},
        {"infected_agent_id": "c", "infection_date": "2025-02-04", "source_kind": "local"},
        {"infected_agent_id": "d", "infection_date": "2025-02-05", "source_kind": "local"},
    ]
    # Eight residents, three unique infected by d: the independent daily fraction is 3/8.
    latent = SimpleNamespace(
        generated=SimpleNamespace(agent_ids=tuple("abcdefgh")),
        transmission_events=events,
        daily_epidemic=[{"date": "2025-02-04", "ever_infected_fraction": 0.375}],
    )
    observed = study.observe_serosurvey(
        latent,
        process_seed=82001,
        serosurvey_seed=94001,
        config_id="v13-g35b-sero-target",
        n=8,
        survey_date=date(2025, 2, 4),
    )
    assert observed.k == latent.daily_epidemic[0]["ever_infected_fraction"] * 8 == 3
    assert dict(zip(observed.sampled_agent_ids, observed.ever_infected, strict=True)) == {
        "a": True,
        "b": True,
        "c": True,
        "d": False,
        "e": False,
        "f": False,
        "g": False,
        "h": False,
    }


def test_serosurvey_repeat_episode_counts_unique_identity() -> None:
    # This deliberately waning-enabled fixture has two episodes of the same resident.
    parameters = study.load_parameter_set(ROOT)
    config = phase0._run_config_for_cell(study.StudyConfig(), parameters, 82001, TRUTH)
    config = config.model_copy(update={"waning_enabled": True})
    assert isinstance(config, OutbreakRunConfig) and config.waning_enabled
    latent = SimpleNamespace(
        config=config,
        generated=SimpleNamespace(agent_ids=("a", "b", "c", "d")),
        transmission_events=[
            {
                "infected_agent_id": "a",
                "infection_date": "2025-01-08",
                "natural_history_episode_index": 0,
            },
            {
                "infected_agent_id": "a",
                "infection_date": "2025-02-04",
                "natural_history_episode_index": 1,
            },
        ],
        daily_epidemic=[
            {"date": "2025-02-04", "ever_infected_fraction": 0.25, "cumulative_infections": 2}
        ],
    )
    observation = study.observe_serosurvey(
        latent,
        process_seed=82001,
        serosurvey_seed=94001,
        config_id="v13-g35b-sero-target",
        n=4,
        survey_date=date(2025, 2, 4),
    )
    assert observation.k == latent.daily_epidemic[0]["ever_infected_fraction"] * 4 == 1
    assert observation.k != latent.daily_epidemic[0]["cumulative_infections"] == 2


def test_serosurvey_sampling_depends_only_on_seed_keys_and_resident_frame() -> None:
    ids = tuple(str(i) for i in range(1000))
    latent = SimpleNamespace(generated=SimpleNamespace(agent_ids=ids), transmission_events=[])
    kwargs = dict(
        process_seed=83001,
        serosurvey_seed=95001,
        config_id="v13-g35b-sero-fit",
        n=400,
        survey_date=date(2025, 2, 4),
    )
    before = study.observe_serosurvey(latent, **kwargs)
    latent.transmission_events = [
        {"infected_agent_id": a, "infection_date": "2025-01-06"} for a in ids
    ]
    after = study.observe_serosurvey(latent, **kwargs)
    assert before.sampled_agent_ids == after.sampled_agent_ids
    assert before.k == 0 and after.k == 400
    for key, value in (
        ("process_seed", 83002),
        ("serosurvey_seed", 95002),
        ("config_id", "different"),
    ):
        changed = study.observe_serosurvey(latent, **{**kwargs, key: value})
        assert set(changed.sampled_agent_ids) != set(before.sampled_agent_ids)
    latent.generated.agent_ids = tuple(f"new-{a}" for a in ids)
    assert set(study.observe_serosurvey(latent, **kwargs).sampled_agent_ids).isdisjoint(
        before.sampled_agent_ids
    )


def test_anscombe_z_hand_computation_exact() -> None:
    """For k=100,n=400: math.sqrt(400.5)*math.asin(math.sqrt(100.375/400.75)).

    This gives the binary float literal 10.489326893582062. Independently reduce
    the rational inputs to sqrt(801/2) * asin(sqrt(803/3206)).
    """
    expected = math.sqrt(801 / 2) * math.asin(math.sqrt(803 / 3206))
    assert study.anscombe_z(100, 400) == expected == 10.489326893582062


@pytest.mark.parametrize("k,n", [(-1, 400), (401, 400), (0, 0), (1.0, 400), (True, 400)])
def test_anscombe_rejects_invalid_counts(k: Any, n: int) -> None:
    with pytest.raises(study.CampaignError, match="integer"):
        study.anscombe_z(k, n)


def test_augmented_loss_literal_report_loss_plus_one_datum_exactly() -> None:
    target, grid, library = _library(3, 34)
    predictions = library[grid[300]]
    ks = (75, 125, 180)

    # Independently write the transform and the ordered three-replicate mean.
    def z(k: int) -> float:
        return math.sqrt(400.5) * math.asin(math.sqrt((k + 0.375) / 400.75))

    S = (z(100) - (z(75) + z(125) + z(180)) / 3) ** 2
    assert study.serosurvey_squared_residual(100, 400, ks) == S
    assert study.augmented_loss(target, predictions, 100, 400, ks) == (
        study.loss(target, predictions, 3, 34) + S / (2 * 34)
    )
    with pytest.raises(study.CampaignError, match="three ordered"):
        study.augmented_loss(target, predictions, 100, 400, ks[:2])
    with pytest.raises(study.CampaignError, match="replicate count"):
        study.augmented_loss(target, predictions[:2], 100, 400, ks)


@pytest.mark.parametrize("flat", [False, True])
def test_serosurvey_fitter_blind_signature_and_shared_selection_rules(flat: bool) -> None:
    assert set(inspect.signature(study.fit_blind_serosurvey).parameters) == {
        "target_tables",
        "target_k",
        "n",
        "candidate_grid",
        "candidate_prediction_library",
        "candidate_k_library",
    }
    target, grid, library = _library(3, 34, flat=flat)
    # Constant exact-zero anchor makes every selection/profile/hash match the report fitter.
    ks = {cell: (0, 0, 0) for cell in grid}
    actual = study.fit_blind_serosurvey(target, 0, 400, grid, library, ks)
    expected = study.fit_blind(target, grid, library, R=3, T=34)
    assert actual == expected
    assert actual.numerical_tie is flat
    with pytest.raises(TypeError, match="unexpected keyword"):
        study.fit_blind_serosurvey(target, 0, 400, grid, library, ks, latent_run=object())
    with pytest.raises(study.CampaignError, match="incomplete"):
        study.fit_blind_serosurvey(target, 0, 400, grid, library, {})
    with pytest.raises(study.CampaignError, match="Cartesian"):
        study.fit_blind_serosurvey(
            target, 0, 400, grid[:-1], library, {c: ks[c] for c in grid[:-1]}
        )


def test_serosurvey_fitter_anchor_can_separate_report_tie() -> None:
    dates = phase0.observation_dates(date(2025, 1, 6), 30)
    table = phase0.ObservedTables(dates, (1.0,) * 34, (2.0,) * 34)
    other = replace(TRUTH, inoculation_day_offset=3)
    grid = (TRUTH, other)
    tables = {cell: (table,) * 3 for cell in grid}
    assert study.fit_blind(table, grid, tables, R=3, T=34).numerical_tie
    fit = study.fit_blind_serosurvey(
        table, 100, 400, grid, tables, {TRUTH: (90, 100, 110), other: (300, 300, 300)}
    )
    assert fit.selected == TRUTH and not fit.numerical_tie
    assert [row.objective for row in fit.loss_surface] == [
        study.augmented_loss(table, tables[cell], 100, 400, ks)
        for cell, ks in ((TRUTH, (90, 100, 110)), (other, (300, 300, 300)))
    ]


@pytest.fixture
def arm_iii_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, baseline_fakes: Any) -> Any:
    calls = baseline_fakes
    config = study.StudyConfig()
    indices = {cell: index for index, cell in enumerate(config.candidate_grid)}

    def faithful_run(parent: Any, run: OutbreakRunConfig, parameters: Any) -> Any:
        result = calls["fake_run"](parent, run, parameters)
        offset = (date.fromisoformat(next(iter(run.import_schedule))) - run.start_date).days
        # Fixed synthetic fixture, independent of the design's scientific assumptions.
        count = 750 if run.seed < 83000 else 400 + int(run.beta * 1000) + 30 * offset + run.seed % 3
        result.transmission_events = tuple(
            {
                "infected_agent_id": str(i),
                "infection_date": (
                    run.start_date + timedelta(days=offset if i < 10 else 10)
                ).isoformat(),
                "imported": i < 10,
                "source_kind": "imported" if i < 10 else "local",
                "natural_history_episode_index": 0,
            }
            for i in range(count)
        )
        result.daily_epidemic = [
            {
                "date": (run.start_date + timedelta(days=d)).isoformat(),
                "ever_infected_fraction": (0 if d < offset else 10 if d < 10 else count) / 3000,
            }
            for d in range(30)
        ]
        return result

    def distinct_observe(latent: Any, obs: ObservationConfig) -> Any:
        result = calls["fake_observe"](latent, obs)
        offset = (
            date.fromisoformat(next(iter(latent.config.import_schedule))) - latent.config.start_date
        ).days
        cell = phase0.CandidateCell(
            latent.config.beta,
            offset,
            obs.parameters["symptomatic_detection_probability"].value,
            obs.parameters["asymptomatic_detection_probability"].value,
        )
        result.observation_events *= indices[cell] + 1
        return result

    monkeypatch.setattr(study, "run_outbreak", faithful_run)
    monkeypatch.setattr(study, "observe_latent_run", distinct_observe)
    baseline = study.generate_baseline(CONFIG, PREDECLARATION, tmp_path / "work", root=ROOT)

    # Every further expensive call is forbidden; only B's returned objects are available.
    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("arm iii must reuse B without dispatch")

    for name in ("build_parent", "run_outbreak", "observe_latent_run", "load_parameter_set"):
        monkeypatch.setattr(study, name, forbidden)
    return baseline, calls


def test_arm_iii_counts_identity_retention_blind_fit_and_post_gate_descriptives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, arm_iii_inputs: Any
) -> None:
    baseline, calls = arm_iii_inputs
    before = {path: path.read_bytes() for path in baseline.blind_paths.values()}
    # Stand-ins for other arms in the shared directory must remain byte unchanged.
    for name in (
        "blind_estimates/82001.json",
        "arm_ii/blind_estimates/82001.json",
        "g35b_i_descriptives.json",
    ):
        path = tmp_path / "work" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path not in before:
            path.write_text("other-arm-sentinel")
            before[path] = path.read_bytes()
    original_observe, original_fit = study.observe_serosurvey, study.fit_blind_serosurvey
    sampled_latents, fitted = [], []

    def recording_observe(latent: Any, **kwargs: Any) -> Any:
        sampled_latents.append(latent)
        return original_observe(latent, **kwargs)

    def recording_fit(*args: Any, **kwargs: Any) -> Any:
        assert len(sampled_latents) == 85
        assert (
            isinstance(args[0], phase0.ObservedTables) and type(args[1]) is int and args[2] == 400
        )
        assert args[4] is baseline.candidate_prediction_library
        fitted.append(args)
        return original_fit(*args, **kwargs)

    def forbidden_truth(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("no truth diagnostics before join")

    with monkeypatch.context() as blind:
        blind.setattr(study, "observe_serosurvey", recording_observe)
        blind.setattr(study, "fit_blind_serosurvey", recording_fit)
        blind.setattr(study, "_truth_diagnostics_from_result", forbidden_truth)
        generation = study.arm_iii(baseline, baseline.config, tmp_path / "work", root=ROOT)
    assert generation.baseline is baseline
    assert (
        len(calls["build"]) == 13 and len(calls["latent"]) == 85 and len(calls["observe"]) == 1885
    )
    assert len(fitted) == 10
    assert all(
        sampled_latents[i] is baseline.target_outputs[s][0]
        for i, s in enumerate(baseline.config.target_process_seeds)
    )
    assert {id(latent) for latent in sampled_latents[10:]} == {
        id(pair[0]) for pair in baseline.candidate_latents.values()
    }
    assert generation.measured == {
        "cells": 625,
        "latent_calls": 0,
        "observation_transforms": 0,
        "serosurvey_samples": 85,
        "builds": 0,
    }
    assert len(generation.target_samples) == 10 and len(generation.candidate_samples) == 75
    assert all(path.read_bytes() == content for path, content in before.items())
    assert not list((tmp_path / "work").rglob("g35b_iii_descriptives.json"))
    assert study._serosurvey_provenance_verified(generation)
    for seed in baseline.config.candidate_process_seeds:
        samples = [
            s for (process, _, _), s in generation.candidate_samples.items() if process == seed
        ]
        assert len(samples) == 25 and len({s.sampled_agent_ids for s in samples}) == 1
    assert len({sample.k for sample in generation.candidate_samples.values()}) > 1
    for cell, ks in generation.candidate_k_library.items():
        assert ks == tuple(
            generation.candidate_samples[seed, cell.beta, cell.inoculation_day_offset].k
            for seed in (83001, 83002, 83003)
        )
    for seed, fit in generation.blind_fits.items():
        path = generation.blind_paths[seed]
        assert path == tmp_path / "work/arm_iii/blind_estimates" / f"{seed}.json"
        study._verify_blind_readback(path, fit, generation.blind_file_hashes[seed])
        assert fit == original_fit(
            baseline.target_tables[seed],
            generation.target_samples[seed].k,
            400,
            baseline.config.candidate_grid,
            baseline.candidate_prediction_library,
            generation.candidate_k_library,
        )
        assert fit.selected is not None
    stored = json.loads(generation.samples_path.read_bytes())
    assert len(stored["targets"]) == 10 and len(stored["candidates"]) == 75
    assert stored["design"] == generation.design
    assert stored["targets"][0]["sampled_agent_ids"] == list(
        generation.target_samples[82001].sampled_agent_ids
    )
    assert all(
        len(sample["ever_infected"]) == sample["n"] == 400
        and sum(sample["ever_infected"]) == sample["k"]
        for sample in stored["targets"] + stored["candidates"]
    )
    with pytest.raises(FileExistsError):
        study.arm_iii(baseline, baseline.config, tmp_path / "work", root=ROOT)
    assert all(path.read_bytes() == content for path, content in before.items())

    evaluated = []
    original_evaluate, original_truth = (
        study.evaluate_recovery,
        study._truth_diagnostics_from_result,
    )

    def recording_truth(latent: Any, observed: Any, table: Any, **kwargs: Any) -> Any:
        assert latent is baseline.target_outputs[latent.config.seed][0]
        return original_truth(latent, observed, table, **kwargs)

    def recording_evaluate(rows: Any, **kwargs: Any) -> Any:
        assert set(kwargs) == {"execution_complete", "provenance_verified", "measured_equals_caps"}
        assert all(isinstance(row, phase0.RecoveryRow) for row in rows)
        evaluated.append((rows, kwargs))
        return original_evaluate(rows, **kwargs)

    monkeypatch.setattr(study, "evaluate_recovery", recording_evaluate)
    monkeypatch.setattr(study, "_truth_diagnostics_from_result", recording_truth)
    evaluation = study.join_arm_iii(generation, tmp_path / "joined")
    assert all(
        evaluation.predicates[key]
        for key in (
            "1_complete",
            "2_truth_viability",
            "3_chronology_conservation",
            "9_provenance",
            "10_measured_caps",
        )
    )
    description = json.loads((tmp_path / "joined/g35b_iii_descriptives.json").read_bytes())
    assert len(description["targets"]) == 10 and len(description["candidates"]) == 75
    assert all(
        t["ever_infected_fraction"] == 0.25 and t["n_criterion_premise_met"]
        for t in description["targets"]
    )
    for target in description["targets"]:
        seed = target["target_seed"]
        fit = generation.blind_fits[seed]
        sample = generation.target_samples[seed]
        assert target["k_over_n"] == sample.k / sample.n
        assert target["z"] == study.anscombe_z(sample.k, sample.n)
        term = study.serosurvey_squared_residual(
            sample.k, 400, generation.candidate_k_library[fit.selected]
        ) / (2 * 34)
        assert target["serosurvey_term"] == term
        assert target["serosurvey_share_of_loss"] == term / fit.minimum_objective
    assert (
        json.loads((tmp_path / "joined/g35b_iii_disclosures.json").read_bytes())
        == generation.disclosures
    )
    with (tmp_path / "joined/g35b_iii_recovery.csv").open() as handle:
        serial = list(csv.DictReader(handle))
    assert len(serial) == 40
    assert {r["target_seed"] for r in serial if r["population_fallback_m2"] == "TRUE"} == {"82003"}
    assert {r["target_seed"] for r in serial if r["population_fallback_m3"] == "TRUE"} == {"82007"}
    # A7 and A10 values are unavailable until gating and cannot affect its inputs.
    for seed in baseline.config.target_process_seeds:
        baseline.target_outputs[seed][0].daily_epidemic[-1]["ever_infected_fraction"] = (
            math.nextafter(0.25, 0.0)
        )
        baseline.parent_lineage[seed]["population_fallback_m2"] = True
    changed = study.join_arm_iii(generation, tmp_path / "changed")
    assert evaluated[0] == evaluated[1] and changed.predicates == evaluation.predicates
    altered = json.loads((tmp_path / "changed/g35b_iii_descriptives.json").read_bytes())
    assert all(not t["n_criterion_premise_met"] for t in altered["targets"])
    assert not study.join_arm_iii(
        replace(generation, measured=baseline.measured), tmp_path / "counts"
    ).predicates["10_measured_caps"]


@pytest.mark.parametrize("damage", ["measured", "latents", "targets", "parents"])
def test_arm_iii_requires_completed_baseline_before_sampling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, arm_iii_inputs: Any, damage: str
) -> None:
    baseline, _ = arm_iii_inputs
    changes = {
        "measured": {"measured": {}},
        "latents": {"candidate_latents": {}},
        "targets": {"target_tables": {}},
        "parents": {"generated_parents": {}},
    }[damage]

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("no sampling of incomplete baseline")

    monkeypatch.setattr(study, "observe_serosurvey", forbidden)
    with pytest.raises(study.CampaignError, match="completed baseline"):
        study.arm_iii(replace(baseline, **changes), baseline.config, tmp_path / "iii", root=ROOT)
    assert not (tmp_path / "iii").exists()


@pytest.mark.parametrize("record", ["blind", "samples"])
def test_arm_iii_corrupt_record_blocks_all_truth_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, arm_iii_inputs: Any, record: str
) -> None:
    baseline, _ = arm_iii_inputs
    generation = study.arm_iii(baseline, baseline.config, tmp_path / "iii", root=ROOT)
    path = generation.blind_paths[82010] if record == "blind" else generation.samples_path
    path.write_text("{}")

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("all read-backs must precede truth diagnostics")

    monkeypatch.setattr(study, "_truth_diagnostics_from_result", forbidden)
    with pytest.raises(study.CampaignError, match="read-back"):
        study.join_arm_iii(generation, tmp_path / "joined")


def test_arm_iii_common_random_numbers_assertion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, arm_iii_inputs: Any
) -> None:
    baseline, _ = arm_iii_inputs
    original = study.observe_serosurvey
    calls = 0

    def changed(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        sample = original(*args, **kwargs)
        calls += 1
        if calls == 12:
            sample = replace(sample, sampled_agent_ids=("changed", *sample.sampled_agent_ids[1:]))
        return sample

    monkeypatch.setattr(study, "observe_serosurvey", changed)
    with pytest.raises(study.CampaignError, match="common random numbers"):
        study.arm_iii(baseline, baseline.config, tmp_path / "iii", root=ROOT)
    assert calls == 12


@pytest.mark.parametrize(
    "key,value",
    [
        ("n", 401),
        ("survey_day", 28),
        ("seroconversion_lag_days", 1),
        ("sensitivity", "0.9"),
        ("specificity", "0.9"),
        ("target_serosurvey_config_id", "different"),
        ("candidate_serosurvey_config_id", "different"),
        ("target_serosurvey_seeds", list(range(94002, 94012))),
        ("candidate_serosurvey_seeds", [95002, 95003, 95004]),
    ],
)
def test_arm_iii_provenance_compares_design_to_independent_frozen_controls(
    tmp_path: Path, arm_iii_inputs: Any, key: str, value: Any
) -> None:
    baseline, _ = arm_iii_inputs
    generation = study.arm_iii(baseline, baseline.config, tmp_path / "iii", root=ROOT)
    changed = replace(generation, design={**generation.design, key: value})
    # Retain consistent bytes for the changed input: independent frozen controls must reject it.
    content = phase0._compact_json_bytes(study._serosurvey_records(changed))
    changed.samples_path.write_bytes(content)
    changed = replace(changed, samples_file_hash=hashlib.sha256(content).hexdigest())
    result = study.join_arm_iii(changed, tmp_path / "joined")
    assert not result.predicates["9_provenance"]
    assert result.predicates["10_measured_caps"]


def test_arm_iii_provenance_rejects_calendar_counts_and_candidate_k_mismatch(
    tmp_path: Path, arm_iii_inputs: Any
) -> None:
    baseline, _ = arm_iii_inputs
    generation = study.arm_iii(baseline, baseline.config, tmp_path / "iii", root=ROOT)
    cell = baseline.config.candidate_grid[0]
    assert not study._serosurvey_provenance_verified(replace(generation, target_samples={}))
    assert not study._serosurvey_provenance_verified(replace(generation, candidate_samples={}))
    assert not study._serosurvey_provenance_verified(
        replace(generation, measured={**generation.measured, "serosurvey_samples": 84})
    )
    assert not study._serosurvey_provenance_verified(
        replace(generation, candidate_k_library={**generation.candidate_k_library, cell: (0, 0, 0)})
    )
    table = baseline.target_tables[82001]
    altered = replace(
        baseline,
        target_tables={
            **baseline.target_tables,
            82001: replace(table, dates=tuple(reversed(table.dates))),
        },
    )
    assert not study.join_arm_iii(
        replace(generation, baseline=altered), tmp_path / "dates"
    ).predicates["9_provenance"]


def test_study_module_has_no_real_serosurvey_or_data_path_reference() -> None:
    for module in (study, frozen):
        source = Path(module.__file__).read_text()
        assert "covid_serosurvey" not in source
        assert "data/" not in source


OWNER_RULING = ROOT / "docs/research/v1_3/2026-10-22-g35b-owner-ruling-ACCEPTED.md"
CLARIFICATION = ROOT / frozen.CLARIFICATION_PATH


def test_baseline_candidate_returned_duration_corruption_fails_predicate_9(
    tmp_path: Path, baseline_fakes: Any
) -> None:
    generation = study.generate_baseline(CONFIG, PREDECLARATION, tmp_path / "B", root=ROOT)
    latent, _ = next(iter(generation.candidate_latents.values()))
    latent.config = latent.config.model_copy(update={"duration_days": 29})
    result = study.join_baseline(generation, tmp_path / "joined")
    assert not result.predicates["9_provenance"]
    assert result.status == "FAIL"


def test_arm_i_replicate_order_corruption_fails_predicate_9(
    tmp_path: Path, baseline_fakes: Any
) -> None:
    baseline = study.generate_baseline(CONFIG, PREDECLARATION, tmp_path / "B", root=ROOT)
    generation = study.arm_i(baseline, baseline.config, tmp_path / "i", root=ROOT)
    # Swapping different seed records preserves every config, seed set and table;
    # only the frozen order changes. The U2 literal-True check misses this.
    records = list(generation.replicate_provenance)
    records[0], records[1] = records[1], records[0]
    corrupted = replace(generation, replicate_provenance=tuple(records))
    result = study.join_arm_i(corrupted, tmp_path / "joined")
    assert not result.predicates["9_provenance"]
    assert result.status == "FAIL"


@pytest.mark.parametrize("arm", ["ii", "iii"])
@pytest.mark.parametrize("damage", ["candidate_seed", "requested_duration", "namespace", "order"])
def test_extended_arms_report_corruption_fails_predicate_9(
    tmp_path: Path, request: pytest.FixtureRequest, arm: str, damage: str
) -> None:
    baseline, _ = request.getfixturevalue(f"arm_{arm}_inputs")
    generation = getattr(study, f"arm_{arm}")(baseline, baseline.config, tmp_path / arm, root=ROOT)
    report = generation if arm == "ii" else baseline
    if arm == "iii":
        assert study._serosurvey_provenance_verified(generation)
        samples_before = generation.samples_path.read_bytes()
    join = getattr(study, f"join_arm_{arm}")
    assert join(generation, tmp_path / "valid").predicates["9_provenance"]
    records = [dict(record) for record in report.replicate_provenance]
    if damage == "candidate_seed":
        records[0]["process_seed"] = -1
    elif damage == "namespace":
        records[0]["observation_config"] = {
            **records[0]["observation_config"],
            "observation_config_id": "wrong-namespace",
        }
    elif damage == "order":
        records[0], records[1] = records[1], records[0]
    else:
        # Change only requested duration, leaving returned duration valid. The
        # old ii check misses this returned/requested disagreement.
        key = next(iter(report.candidate_latents))
        latent, requested = report.candidate_latents[key]
        report = replace(
            report,
            candidate_latents={
                **report.candidate_latents,
                key: (
                    latent,
                    requested.model_copy(update={"duration_days": 48 if arm == "ii" else 29}),
                ),
            },
        )
    report = replace(report, replicate_provenance=tuple(records))
    corrupted = report if arm == "ii" else replace(generation, baseline=report)
    if arm == "iii":
        assert study._serosurvey_provenance_verified(corrupted)
        assert corrupted.samples_path.read_bytes() == samples_before
    result = join(corrupted, tmp_path / "joined")
    assert not result.predicates["9_provenance"]
    assert result.status == "FAIL"


@pytest.mark.parametrize(
    "damage", ["target_flag_and_k", "candidate_flag_and_k", "empty_target_events"]
)
def test_serosurvey_provenance_requires_independent_latent_events(
    tmp_path: Path, arm_iii_inputs: Any, damage: str
) -> None:
    baseline, _ = arm_iii_inputs
    generation = study.arm_iii(baseline, baseline.config, tmp_path / "iii", root=ROOT)
    assert study.join_arm_iii(generation, tmp_path / "valid").predicates["9_provenance"]
    if damage == "empty_target_events":
        assert all(sample.k > 0 for sample in generation.target_samples.values())
        for output in baseline.target_outputs.values():
            output[0].transmission_events = ()
    else:
        targets = damage == "target_flag_and_k"
        samples = dict(generation.target_samples if targets else generation.candidate_samples)
        key = next(iter(samples))
        sample = samples[key]
        flags = (not sample.ever_infected[0], *sample.ever_infected[1:])
        samples[key] = replace(sample, ever_infected=flags, k=sum(flags))
        if targets:
            generation = replace(generation, target_samples=samples)
        else:
            ks = {
                cell: tuple(
                    samples[seed, cell.beta, cell.inoculation_day_offset].k
                    for seed in baseline.config.candidate_process_seeds
                )
                for cell in baseline.config.candidate_grid
            }
            generation = replace(generation, candidate_samples=samples, candidate_k_library=ks)
        assert samples[key].k == sum(samples[key].ever_infected)
        # Persist internally consistent corrupt evidence. Only the independent
        # latent events can disprove these flags.
        content = phase0._compact_json_bytes(study._serosurvey_records(generation))
        generation.samples_path.write_bytes(content)
        generation = replace(generation, samples_file_hash=hashlib.sha256(content).hexdigest())
    result = study.join_arm_iii(generation, tmp_path / "joined")
    assert not result.predicates["9_provenance"]
    assert result.status == "FAIL"


READING_CELLS = {
    ("FAIL", "PASS"): (
        "Factor X, at the declared level, coincided with four-dimensional recovery "
        "in this one synthetic campaign. Screening result only."
    ),
    ("PASS", "PASS"): (
        "The fresh-seed baseline at ten targets passed the recovery gate. "
        "Factor X is not shown to be necessary. This is not a replication of the "
        "Phase-0b design (five targets, retired seeds) and alters no Phase-0b verdict."
    ),
    ("PASS", "FAIL"): (
        "Factor X coincided with loss of recovery. Reported as an anomaly; no causal reading."
    ),
}
MULTIPLICITY_TEXT = (
    "Three arms raise the chance that at least one passes when no factor matters. "
    "Thresholds are not adjusted, because that would require numbers not justified "
    "independently of Phase 0b. Instead, a PASS reading is screening evidence only. "
    "Any later decision relying on it requires Steven's decision and a new "
    "owner-ruled, fresh-seed confirmatory predeclaration."
)


@pytest.mark.parametrize("arm", ["i", "ii", "iii"])
@pytest.mark.parametrize("B_status", ["PASS", "FAIL", "VOID"])
@pytest.mark.parametrize("X_status", ["PASS", "FAIL", "VOID"])
def test_readings_every_frozen_cell_including_void(arm: str, B_status: str, X_status: str) -> None:
    if "VOID" in (B_status, X_status):
        assert study.readings(B_status, X_status, arm) is None
        return
    if (B_status, X_status) == ("FAIL", "FAIL"):
        expected = "Factor X alone, at the declared level, did not produce recovery. " + (
            "Arm (i): evidence against Monte-Carlo noise as the sole cause."
            if arm == "i"
            else "Arms (ii)/(iii): that factor did not break the ridge at this level."
        )
    else:
        expected = READING_CELLS[B_status, X_status]
    if X_status == "PASS":
        expected += " " + MULTIPLICITY_TEXT
    assert study.readings(B_status, X_status, arm) == expected


def test_overall_readings_and_exact_a9_status_phrases() -> None:
    prefix = "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: "
    assert study.status_phrase() == prefix + "not run"
    statuses = {"B": "FAIL", "i": "PASS", "ii": "FAIL", "iii": "VOID"}
    assert study.status_phrase(statuses) == prefix + "B FAIL, i PASS, ii FAIL, iii VOID"
    assert study.overall_readings(statuses) is None
    statuses["iii"] = "FAIL"
    assert study.overall_readings(statuses) == {"i": study.readings("FAIL", "PASS", "i")}
    statuses["i"] = "FAIL"
    assert study.overall_readings(statuses) == (
        "None of the three factors, one at a time at the declared levels, made the "
        "recovery gate pass. The ridge hypothesis (H2) is not contradicted."
    )
    statuses["B"] = "PASS"
    assert study.overall_readings(statuses) is None
    with pytest.raises(ValueError):
        study.readings("SOFTWARE FAIL", "FAIL", "i")
    with pytest.raises(ValueError):
        study.status_phrase({"B": "PASS"})


@pytest.fixture
def all_arms_fakes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    baseline_fakes: Any,
    committed_campaign_config: None,
) -> dict[str, Any]:
    """Mock only execution and the source snapshot of this intentionally dirty tree."""
    calls = baseline_fakes
    calls.update({"persist": [], "truth_reads": [], "sampling": False, "generations": {}})
    original_observe_sero = study.observe_serosurvey
    original_persist = study.persist_blind_estimate
    original_diagnostics = study._truth_diagnostics_from_result
    # Acquire the existing 49-day fake, then install a dispatcher for both windows.
    _install_arm_ii_fakes(calls, monkeypatch)
    run49 = study.run_outbreak
    observe49 = study.observe_latent_run

    class GuardedLatent(SimpleNamespace):
        def __getattribute__(self, name: str) -> Any:
            if name in ("transmission_events", "daily_epidemic"):
                # Sampling is the declared observation model (§5.2), not a truth
                # join. All other reads, including ii/iii descriptives, must wait.
                if not (name == "transmission_events" and calls["sampling"]):
                    assert len(calls["persist"]) == 90, "truth before last blind record"
                    calls["truth_reads"].append(name)
            return super().__getattribute__(name)

    def fake_run(parent: Any, run: OutbreakRunConfig, parameters: Any) -> Any:
        result = (run49 if run.duration_days == 49 else calls["fake_run"])(parent, run, parameters)
        offset = (date.fromisoformat(next(iter(run.import_schedule))) - run.start_date).days
        count = 750
        result.transmission_events = tuple(
            {
                "infected_agent_id": str(i),
                "infection_date": (
                    run.start_date + timedelta(days=offset if i < 10 else 10)
                ).isoformat(),
                "imported": i < 10,
                "source_kind": "imported" if i < 10 else "local",
                "natural_history_episode_index": 0,
            }
            for i in range(count)
        )
        result.daily_epidemic = [
            {
                "date": (run.start_date + timedelta(days=d)).isoformat(),
                "ever_infected_fraction": 0.25 if d >= 10 else 0,
                # A late peak deliberately exercises the required ii reading suffix.
                "new_infections": int(d == 45),
            }
            for d in range(run.duration_days)
        ]
        return GuardedLatent(**vars(result))

    def fake_observe(latent: Any, obs: ObservationConfig) -> Any:
        return (observe49 if latent.config.duration_days == 49 else calls["fake_observe"])(
            latent, obs
        )

    def observe_sero(*args: Any, **kwargs: Any) -> Any:
        calls["sampling"] = True
        try:
            return original_observe_sero(*args, **kwargs)
        finally:
            calls["sampling"] = False

    def persist(path: Path, fit: Any) -> Any:
        result = original_persist(path, fit)
        calls["persist"].append(path)
        return result

    def diagnostics(*args: Any, **kwargs: Any) -> Any:
        assert len(calls["persist"]) == 90
        return original_diagnostics(*args, **kwargs)

    for name in ("generate_baseline", "arm_i", "arm_ii", "arm_iii"):
        original = getattr(study, name)

        def capture(*args: Any, _generate: Any = original, _name: str = name, **kwargs: Any) -> Any:
            generation = _generate(*args, **kwargs)
            calls["generations"][_name] = generation
            return generation

        monkeypatch.setattr(study, name, capture)
    monkeypatch.setattr(study, "run_outbreak", fake_run)
    monkeypatch.setattr(study, "observe_latent_run", fake_observe)
    monkeypatch.setattr(study, "observe_serosurvey", observe_sero)
    monkeypatch.setattr(study, "persist_blind_estimate", persist)
    monkeypatch.setattr(study, "_truth_diagnostics_from_result", diagnostics)
    monkeypatch.setattr(
        study,
        "_source_snapshot",
        lambda root: {
            "git_head": "mocked-source-snapshot",
            "worktree_clean": True,
            "source_and_config_sha256": {},
        },
    )
    return calls


def _run_mock_campaign(output: Path) -> dict[str, Any]:
    return study.run_all_arms(
        CONFIG, PREDECLARATION, OWNER_RULING, CLARIFICATION, output, root=ROOT
    )


def _unseal_for_test_cleanup(output: Path) -> None:
    import os

    for path in [output, *output.rglob("*")]:
        os.chmod(path, path.stat().st_mode | 0o200)


def _recompute_one_target_from_bundle(directory: Path, arm: str) -> Any:
    """Cold replay of every cell, using only the retained bundle and pure fitters."""

    def table(payload: Any) -> Any:
        return phase0.ObservedTables(**{key: tuple(value) for key, value in payload.items()})

    target = table(json.loads((directory / "target_tables/82001.json").read_bytes()))
    library, hashes, grid = {}, {}, []
    for cell_dir in sorted((directory / "candidate_tables").iterdir(), key=lambda p: int(p.name)):
        records = [json.loads(path.read_bytes()) for path in sorted(cell_dir.glob("*.json"))]
        cell = phase0.CandidateCell(**records[0]["cell"])
        grid.append(cell)
        library[cell] = tuple(table(record["table"]) for record in records)
        hashes[cell] = hashlib.sha256(
            phase0._compact_json_bytes(
                [
                    {"run": record["run_config"], "observation": record["observation_config"]}
                    for record in records
                ]
            )
        ).hexdigest()
    if arm != "iii":
        return study.fit_blind(
            target,
            grid,
            library,
            R=12 if arm == "i" else 3,
            T=53 if arm == "ii" else 34,
            candidate_config_hashes=hashes,
        )
    samples = json.loads((directory / "arm_iii/serosurvey_samples.json").read_bytes())
    target_sample = next(sample for sample in samples["targets"] if sample["process_seed"] == 82001)
    counts = {
        (sample["process_seed"], sample["beta"], sample["offset"]): sample["k"]
        for sample in samples["candidates"]
    }
    k_library = {
        cell: tuple(
            counts[seed, cell.beta, cell.inoculation_day_offset] for seed in (83001, 83002, 83003)
        )
        for cell in grid
    }
    return study.fit_blind_serosurvey(
        target, target_sample["k"], target_sample["n"], grid, library, k_library
    )


def test_all_arms_barrier_distinct_records_bundle_and_scientific_fail(
    tmp_path: Path, all_arms_fakes: Any
) -> None:
    calls = all_arms_fakes
    output = tmp_path / "campaign"
    try:
        summary = _run_mock_campaign(output)
        assert summary == json.loads((output / "campaign_summary.json").read_bytes())
        assert summary["software_status"] == "PASS"
        # Flat observation fixture is a scientific FAIL; all arms still finish.
        assert summary["arms"]["B"]["scientific_status"] == "FAIL"
        assert summary["arms"]["B"]["status"] == "FAIL"
        assert calls["truth_reads"] and len(calls["persist"]) == 90
        assert len(set(calls["persist"])) == 90
        assert len(calls["build"]) == 22
        assert len(calls["latent"]) == 395 and len(calls["observe"]) == 9395
        for arm, function in (
            ("B", "generate_baseline"),
            ("i", "arm_i"),
            ("ii", "arm_ii"),
            ("iii", "arm_iii"),
        ):
            generation = calls["generations"][function]
            directory = output / ("B" if arm == "B" else f"arm_{arm}")
            assert len(generation.blind_paths) == 10
            for seed, path in generation.blind_paths.items():
                assert path.is_relative_to(directory)
                study._verify_blind_readback(
                    path, generation.blind_fits[seed], generation.blind_file_hashes[seed]
                )
            index = json.loads((directory / "blind_readback_hashes.json").read_bytes())
            assert len(index) == (60 if arm == "i" else 10)
            for record in index:
                assert (
                    hashlib.sha256((directory / record["path"]).read_bytes()).hexdigest()
                    == record["sha256"]
                )
            replay = _recompute_one_target_from_bundle(directory, arm)
            gate_record = next(
                record
                for record in index
                if record["role"] == "gate" and record["target_seed"] == 82001
            )
            assert replay.as_dict() == json.loads((directory / gate_record["path"]).read_bytes())
            assert summary["arms"][arm]["predicates"]["10_measured_caps"]
            assert summary["measured_work"]["arms"][arm]["measured_equals_planned"]
            assert summary["arms"][arm]["verdict_line"] == f"G35-B ARM {arm} RECOVERY GATE: FAIL"
            assert len(list((directory / "candidate_tables").rglob("*.json"))) == (
                7500 if arm == "i" else 1875
            )
            with (directory / f"g35b_{arm}_recovery.csv").open() as handle:
                rows = list(csv.DictReader(handle))
            assert len(rows) == 40
            assert {
                "population_fallback_m2",
                "population_fallback_m3",
                "measured_cells",
                "predicate_9_provenance",
            } <= set(rows[0])
            disclosure = summary["disclosures"][arm]
            assert disclosure["arm_wall_time_seconds"] >= 0
            assert set(disclosure["phase_wall_time_seconds"]) >= {
                "build",
                "latent",
                "transform",
                "scoring",
            }
            assert (
                len(disclosure["latent_runtimes"]) == {"B": 85, "i": 225, "ii": 85, "iii": 0}[arm]
            )
        assert summary["measured_work"]["total"]["measured_equals_planned"]
        assert summary["measured_work"]["total"]["measured"] == dict(
            zip(study.TOTAL_FIELDS, (2500, 395, 9395, 85, 22), strict=True)
        )
        assert summary["measured_work"]["gate_loss_evaluations"] == 25000
        assert summary["measured_work"]["descriptive_loss_evaluations"] == 31250
        assert summary["readings"]["ii"].endswith("factor delivered for 0/10 targets")
        assert summary["lineage"]["ridge_diagnostic_sha256"] == frozen.RIDGE_SHA256
        assert summary["lineage"]["ridge_crlf_alias"]["binding"] is False
        assert summary["spread_label"] == "stochastic_replicate_variation"
        ledger = json.loads((output / "seed_ledger.json").read_bytes())
        assert len(ledger) == 61  # 40 targets + 3 + 12 + 3 + 3 candidates.
        assert sum(row["serosurvey_seed"] is not None for row in ledger) == 13
        for path in (
            CONFIG,
            PREDECLARATION,
            OWNER_RULING,
            CLARIFICATION,
            ROOT / "docs/runs/2026-10-22-g35b-seed-precheck.json",
            ROOT / "docs/runs/2026-10-22-g35b-horizon-probe.json",
        ):
            content = (output / "frozen_inputs" / path.name).read_bytes()
            assert content == study.committed_document_bytes(path)
            assert hashlib.sha256(content).hexdigest() == summary["frozen_input_sha256"][path.name]
        samples = json.loads((output / "arm_iii/arm_iii/serosurvey_samples.json").read_bytes())
        assert len(samples["targets"]) == 10 and len(samples["candidates"]) == 75
        for sample in samples["targets"] + samples["candidates"]:
            assert (
                sample["n"]
                == len(sample["sampled_agent_ids"])
                == len(sample["ever_infected"])
                == 400
            )
            assert sample["k"] == sum(sample["ever_infected"])
        study.verify_bundle(output)
        assert all(path.stat().st_mode & 0o222 == 0 for path in [output, *output.rglob("*")])
    finally:
        if output.exists():
            _unseal_for_test_cleanup(output)


@pytest.mark.parametrize("failed_phase", ["generation", "join", "readback", "measured"])
def test_software_failure_stops_and_seals_void_without_readings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, all_arms_fakes: Any, failed_phase: str
) -> None:
    calls = all_arms_fakes
    output = tmp_path / "void"
    failures = []

    def fail(*args: Any, **kwargs: Any) -> None:
        failures.append("failed")
        raise RuntimeError("injected software exception")

    if failed_phase in ("generation", "join"):
        monkeypatch.setattr(study, "arm_i" if failed_phase == "generation" else "join_arm_i", fail)
    else:
        original = study.arm_iii

        def corrupt(*args: Any, **kwargs: Any) -> Any:
            generation = original(*args, **kwargs)
            failures.append("failed")
            if failed_phase == "readback":
                generation.blind_paths[82010].write_text("{}")
                return generation
            return replace(generation, measured={**generation.measured, "cells": 624})

        monkeypatch.setattr(study, "arm_iii", corrupt)
    try:
        with pytest.raises(study.CampaignError, match="campaign VOID"):
            _run_mock_campaign(output)
        assert failures == ["failed"]
        summary = json.loads((output / "campaign_summary.json").read_bytes())
        assert summary["software_status"] == "VOID"
        assert "readings" not in summary and "overall_reading" not in summary
        if failed_phase in ("generation", "join"):
            assert summary["error"] == {
                "class": "RuntimeError",
                "message": "injected software exception",
            }
        elif failed_phase == "readback":
            assert summary["error"]["message"] == (
                "blind estimate read-back failed: blind estimate read-back mismatch"
            )
            assert not calls["truth_reads"]
        else:
            assert summary["error"]["class"] == "BudgetError"
            assert not summary["measured_work"]["arms"]["iii"]["measured_equals_planned"]
            assert not summary["measured_work"]["total"]["measured_equals_planned"]
            assert not calls["truth_reads"]
        if failed_phase == "generation":
            assert len(calls["persist"]) == 10
            assert not calls["truth_reads"]
            assert set(calls["generations"]) == {"generate_baseline"}
            assert summary["measured_work"]["total"]["measured"] is None
            assert summary["measured_work"]["arms"]["i"]["measured"] is None
        elif failed_phase == "join":
            # The already established scientific FAIL is never rewritten as VOID.
            assert summary["arms"]["B"]["scientific_status"] == "FAIL"
            assert summary["arms"]["B"]["status"] == "FAIL"
            assert summary["arms"]["i"]["status"] == "VOID"
        study.verify_bundle(output)
        assert all(path.stat().st_mode & 0o222 == 0 for path in [output, *output.rglob("*")])
    finally:
        if output.exists():
            _unseal_for_test_cleanup(output)


@pytest.mark.parametrize(
    "document",
    ["config", "predeclaration", "owner_ruling", "clarification", "ridge", "precheck", "probe"],
)
def test_campaign_document_digest_failure_precedes_output_and_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    document: str,
    committed_campaign_config: None,
) -> None:
    original = study.committed_document_bytes
    names = {
        "config": CONFIG.name,
        "predeclaration": PREDECLARATION.name,
        "owner_ruling": OWNER_RULING.name,
        "clarification": CLARIFICATION.name,
        "ridge": Path(frozen.RIDGE_PATH).name,
        "precheck": "2026-10-22-g35b-seed-precheck.json",
        "probe": "2026-10-22-g35b-horizon-probe.json",
    }

    def corrupted(path: Path, **kwargs: Any) -> bytes:
        content = original(path, **kwargs)
        return content + b"changed" if path.name == names[document] else content

    monkeypatch.setattr(study, "committed_document_bytes", corrupted)
    with pytest.raises(study.CampaignError, match="committed SHA-256 mismatch"):
        _run_mock_campaign(tmp_path / "rejected")
    assert not (tmp_path / "rejected").exists()


def test_campaign_rejects_existing_destination_without_touching_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, committed_campaign_config: None
) -> None:
    monkeypatch.setattr(study, "_source_snapshot", lambda root: {})
    output = tmp_path / "existing"
    output.mkdir()
    with pytest.raises(study.CampaignError, match="output_dir must not exist"):
        _run_mock_campaign(output)
    assert list(output.iterdir()) == []


def test_source_snapshot_uses_clean_head_committed_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    files = {
        "src/jersey_outbreak/a.py": b"x = 1\n",
        "src/jersey_outbreak/nested/b.py": b"y = 2\n",
        "configs/example.yaml": b"example: frozen\n",
    }
    calls = []
    dirty = False

    def git_output(command: Any, **kwargs: Any) -> bytes:
        calls.append(command)
        if "status" in command:
            return b" M src/jersey_outbreak/a.py\n" if dirty else b""
        if "rev-parse" in command:
            return b"fixed-head\n"
        assert "ls-tree" in command and "fixed-head" in command
        return "\n".join(files).encode()

    def committed(path: Path, *, commit: str = "HEAD") -> bytes:
        assert commit == "fixed-head"
        return files[path.relative_to(tmp_path).as_posix()]

    monkeypatch.setattr(study.subprocess, "check_output", git_output)
    monkeypatch.setattr(study, "committed_document_bytes", committed)
    snapshot = study._source_snapshot(tmp_path)
    assert snapshot["source_and_config_sha256"] == {
        name: hashlib.sha256(content).hexdigest() for name, content in files.items()
    }
    assert snapshot["git_head"] == "fixed-head"
    assert snapshot["worktree_clean"]
    assert "status" in calls[0]
    dirty = True
    with pytest.raises(study.CampaignError, match="clean worktree"):
        study._source_snapshot(tmp_path)


@pytest.mark.parametrize("failure", [False, True])
def test_execute_cli_calls_orchestrator_and_reports_validation_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Any, failure: bool
) -> None:
    calls = []

    def mocked(*args: Any, **kwargs: Any) -> Any:
        calls.append((args, kwargs))
        if failure:
            raise study.CampaignError("frozen input rejected")
        return {
            "arms": {"B": {"verdict_line": "G35-B ARM B RECOVERY GATE: FAIL"}},
            "status_phrase": study.status_phrase({arm: "FAIL" for arm in ("B", "i", "ii", "iii")}),
        }

    monkeypatch.setattr(study, "run_all_arms", mocked)
    args = [
        "execute",
        "--config",
        str(CONFIG),
        "--predeclaration",
        str(PREDECLARATION),
        "--owner-ruling",
        str(OWNER_RULING),
        "--clarification",
        str(CLARIFICATION),
        "--output-dir",
        str(tmp_path / "output"),
    ]
    assert study.main(args) == int(failure)
    assert calls == [
        ((CONFIG, PREDECLARATION, OWNER_RULING, CLARIFICATION, tmp_path / "output"), {"root": ROOT})
    ]
    captured = capsys.readouterr()
    if failure:
        assert captured.err == "frozen input rejected\n"
    else:
        assert "G35-B ARM B RECOVERY GATE: FAIL" in captured.out
    with pytest.raises(SystemExit) as exc:
        study.main(args[:7] + args[9:])  # Omit the binding --clarification pair.
    assert exc.value.code == 2
    assert len(calls) == 1


@pytest.mark.parametrize(
    "profile,expected", [("phase0", (198, 59, 599, 8)), ("phase0b", (1334, 107, 4007, 8))]
)
def test_frozen_earlier_profiles_still_dry_run_without_execution(
    monkeypatch: pytest.MonkeyPatch, capsys: Any, profile: str, expected: tuple[int, ...]
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("frozen-profile regression must only dry-run")

    for name in ("build_parent", "run_outbreak", "observe_latent_run"):
        monkeypatch.setattr(phase0, name, forbidden)
    date_prefix = "2026-09-21" if profile == "phase0" else "2026-09-25"
    plan = phase0.dry_run(
        ROOT / f"configs/calibration/v13_{profile}_synthetic.yaml",
        ROOT / f"docs/research/v1_3/{date_prefix}-{profile}-predeclaration.md",
    )
    payload = json.loads(capsys.readouterr().out)
    assert (
        plan.total_cells,
        payload["total_latent_outbreak_calls"],
        payload["total_observation_transforms"],
        payload["distinct_population_network_seed_builds"],
    ) == expected
    assert payload == {**payload, **plan.as_dict()}


def test_phase0_campaign_is_byte_identical_to_main() -> None:
    import subprocess

    path = "src/jersey_outbreak/phase0_campaign.py"
    assert (ROOT / path).read_bytes() == subprocess.check_output(
        ["git", "show", f"main:{path}"], cwd=ROOT
    )


def test_bundle_manifest_rechecks_bytes_and_every_file(tmp_path: Path) -> None:
    output = tmp_path / "bundle"
    (output / "nested").mkdir(parents=True)
    (output / "value.json").write_text('{"value":1}\n')
    # Even an existing nested manifest is an ordinary file in the outer manifest.
    (output / "nested/SHA256SUMS").write_text("retained nested manifest\n")
    try:
        study._seal_bundle(output)
        study.verify_bundle(output)
        _unseal_for_test_cleanup(output)
        original = (output / "value.json").read_bytes()
        (output / "value.json").write_text('{"value":2}\n')
        with pytest.raises(study.CampaignError, match="SHA256SUMS mismatch"):
            study.verify_bundle(output)
        (output / "value.json").write_bytes(original)
        (output / "unlisted.json").write_text("{}")
        with pytest.raises(study.CampaignError, match="file set mismatch"):
            study.verify_bundle(output)
    finally:
        _unseal_for_test_cleanup(output)
