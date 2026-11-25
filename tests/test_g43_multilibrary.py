from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import date, timedelta
from decimal import Decimal, localcontext
from itertools import product
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml

from jersey_outbreak import g35b_design_study as g35b
from jersey_outbreak import g43_constants as frozen
from jersey_outbreak import g43_multilibrary as study
from jersey_outbreak import g43_recompute as audit
from jersey_outbreak import phase0_campaign as phase0
from jersey_outbreak.observation_scheduler import observation_stream_seed
from jersey_outbreak.observation_schemas import ObservationConfig
from jersey_outbreak.outbreak_schemas import OutbreakRunConfig

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/calibration/v13_g43_multilibrary.yaml"
PREDECLARATION = ROOT / frozen.PREDECLARATION_PATH
HISTORICAL = Path(__file__).parent / "fixtures/g43/historical_g35b.json"

_WORK_FIELDS = (
    "builds",
    "latent_calls",
    "observation_transforms",
    "candidate_cells",
    "gate_loss_evaluations",
    "gate_blind_records",
    "descriptive_loss_evaluations",
    "descriptive_blind_records",
    "serosurvey_samples",
)
_SHARED = dict(zip(_WORK_FIELDS, (20, 20, 20, 0, 0, 0, 0, 0, 0), strict=True))
_LIBRARY = dict(zip(_WORK_FIELDS, (12, 300, 7500, 625, 12500, 20, 62500, 100, 0), strict=True))
_TOTALS = dict(zip(_WORK_FIELDS, (92, 1820, 45020, 3750, 75000, 120, 375000, 600, 0), strict=True))
_TARGET_SEEDS = tuple(range(86001, 86021))
_DIMENSIONS = (
    "beta",
    "inoculation_day_offset",
    "symptomatic_detection_probability",
    "asymptomatic_detection_probability",
)
_TRUTH = phase0.CandidateCell(0.08, 2, 0.75, 0.25)


def _committed(path: Path, commit: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{commit}:{path.relative_to(ROOT).as_posix()}"], cwd=ROOT
    )


@pytest.fixture(scope="module")
def frozen_document() -> str:
    return _committed(PREDECLARATION, "fc16adcb3f8817eb2630ae5a31cd0508990bebd2").decode()


def test_config_lf_bytes_match_independent_digest() -> None:
    content = CONFIG.read_bytes()
    assert b"\r" not in content
    assert hashlib.sha256(content).hexdigest() == frozen.CONFIG_SHA256
    assert study.StudyConfig.from_yaml(CONFIG) == study.StudyConfig()


def test_config_digest_comment_no_longer_marks_commit_pending() -> None:
    assert "pending the director's commit" not in Path(frozen.__file__).read_text()


def test_final_seed_and_hash_table_matches_frozen_commit(frozen_document: str) -> None:
    table = frozen_document.split("### Final seed table (92 seeds)\n")[1].split(
        "### Unused reserves"
    )[0]
    parsed_seeds = []
    parsed_hashes = {}
    replacements = set()
    for line in table.splitlines():
        if not line.startswith(("| target |", "| candidate |")):
            continue
        role, library, batch, position, process, observation, built, _, *hashes = (
            cell.strip() for cell in line.strip("|").split("|")
        )
        assert built == "BUILT"
        if role == "target":
            assert library == batch == "–"
            parsed_seeds.append((None, None, int(position), int(process), int(observation)))
        else:
            parsed_seeds.append(
                (int(library), int(batch), int(position), int(process.split()[0]), int(observation))
            )
            if process.endswith(" (replacement)"):
                replacements.add(
                    (int(library), int(position), int(process.split()[0]), int(observation))
                )
        parsed_hashes[parsed_seeds[-1][3]] = tuple(value.strip("`") for value in hashes)
    assert len(parsed_seeds) == len(parsed_hashes) == 92
    assert tuple(parsed_seeds) == frozen.FINAL_SEEDS
    assert parsed_hashes == frozen.PROCESS_HASHES
    assert replacements == {(3, 1, 87351, 99301), (3, 5, 87352, 99305), (5, 6, 87551, 99506)}


def test_earlier_and_retired_seed_sets_match_frozen_commit(frozen_document: str) -> None:
    earlier = frozen_document.split("**Disjointness.**", 1)[1].split("The G43 series", 1)[0]
    bounds = tuple((int(low), int(high)) for low, high in re.findall(r"`(\d{5})–(\d{5})`", earlier))
    assert bounds == frozen.EARLIER_SEED_RANGES
    assert len(frozen.EARLIER_SEEDS) == 208
    flat = frozen_document.split("## 19.", 1)[1]
    process, observation = flat.split("**Non-building seeds")
    declared_processes = set(map(int, re.findall(r"\b\d{5}\b", process)))
    declared_observations = set(map(int, re.findall(r"\b\d{5}\b", observation)))
    assert declared_processes == (
        {row.process for row in frozen.FINAL_SEEDS}
        | set(frozen.UNUSED_RESERVE_SEEDS)
        | set(frozen.EXCLUDED_PRIMARY_SEEDS)
    )
    assert declared_observations == {row.observation for row in frozen.FINAL_SEEDS}
    assert len(declared_processes) == 138
    assert len(declared_observations) == 92
    assert len(declared_processes | declared_observations) == 230
    assert not (declared_processes | declared_observations) & frozen.EARLIER_SEEDS


def test_predeclaration_uses_frozen_commit_and_independent_digest() -> None:
    assert study.validate_predeclaration(PREDECLARATION) == (
        "67c3c7c03c1ec0f6176e430098c702a913368de51a9e8793c145094255b71094"
    )


@pytest.mark.parametrize(
    "modification, message",
    [("tampered", "differs from committed"), ("crlf", "must match committed LF bytes")],
)
def test_predeclaration_rejects_modified_checkout(
    monkeypatch: pytest.MonkeyPatch, modification: str, message: str
) -> None:
    original_read = Path.read_bytes
    raw = original_read(PREDECLARATION)
    altered = raw + b"\n" if modification == "tampered" else raw.replace(b"\n", b"\r\n")
    monkeypatch.setattr(
        Path, "read_bytes", lambda path: altered if path == PREDECLARATION else original_read(path)
    )
    with pytest.raises(study.CampaignError, match=message):
        study.validate_predeclaration(PREDECLARATION)


def test_predeclaration_rejects_uncommitted_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Expose an LF copy at an untracked path in the repository to the byte reader.
    path = PREDECLARATION.parent / "uncommitted-g43-test.md"
    copy = tmp_path / path.name
    copy.write_bytes(PREDECLARATION.read_bytes())
    original_read = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: original_read(copy if p == path else p))
    with pytest.raises(study.CampaignError, match="cannot verify committed"):
        study.validate_predeclaration(path)


def test_predeclaration_rejects_uncommitted_symlink(tmp_path: Path) -> None:
    path = tmp_path / PREDECLARATION.name
    path.symlink_to(PREDECLARATION)
    with pytest.raises(study.CampaignError, match="must be a committed repository file"):
        study.validate_predeclaration(path)


def test_predeclaration_rejects_different_committed_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    original = subprocess.check_output
    altered = b"different repository document\n"

    def git_output(args: list[str], **kwargs: Any) -> bytes:
        if "show" in args:
            assert args[-1] == (
                "fc16adcb3f8817eb2630ae5a31cd0508990bebd2:"
                "docs/research/v1_3/2026-11-20-g43-predeclaration.md"
            )
            return altered
        return original(args, **kwargs)

    monkeypatch.setattr(subprocess, "check_output", git_output)
    monkeypatch.setattr(Path, "read_bytes", lambda _: altered)
    with pytest.raises(study.CampaignError, match="predeclaration SHA-256 mismatch"):
        study.validate_predeclaration(PREDECLARATION)


def _leaf_paths(value: Any, path: tuple[str | int, ...] = ()) -> list[tuple[str | int, ...]]:
    if isinstance(value, dict):
        return [leaf for key, child in value.items() for leaf in _leaf_paths(child, (*path, key))]
    if isinstance(value, list):
        return [
            leaf for index, child in enumerate(value) for leaf in _leaf_paths(child, (*path, index))
        ]
    return [path]


def _changed_value(value: Any) -> Any:
    if type(value) is bool:
        return not value
    if type(value) is int:
        return value + 1000000
    if isinstance(value, str):
        return value + "_changed"
    assert value is None
    return 123


@pytest.fixture(scope="module")
def yaml_payload() -> dict[str, Any]:
    return yaml.safe_load(CONFIG.read_bytes())


@pytest.mark.parametrize("path", _leaf_paths(yaml.safe_load(CONFIG.read_bytes())))
def test_every_frozen_payload_leaf_mutation_is_rejected(
    yaml_payload: dict[str, Any], path: tuple[str | int, ...]
) -> None:
    payload = deepcopy(yaml_payload)
    parent: Any = payload
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = _changed_value(parent[path[-1]])
    with pytest.raises(study.CampaignError, match="frozen declaration"):
        study.validate_frozen_payload(payload)


@pytest.mark.parametrize("earlier", sorted(frozen.EARLIER_SEEDS))
def test_overlap_with_any_earlier_seed_is_rejected(
    yaml_payload: dict[str, Any], earlier: int
) -> None:
    payload = deepcopy(yaml_payload)
    payload["seeds"]["target_process_seeds"][0] = earlier
    with pytest.raises(study.BudgetError, match="seed overlap with an earlier"):
        study.validate_frozen_payload(payload)


@pytest.mark.parametrize("site", ("target", "other_library", "unused_reserve", "excluded_primary"))
def test_study_seed_overlap_is_rejected(yaml_payload: dict[str, Any], site: str) -> None:
    payload = deepcopy(yaml_payload)
    seeds = payload["seeds"]
    other_sources = {
        "target": seeds["target_observation_seeds"],
        "other_library": seeds["candidate_libraries"]["L6"]["batch4"]["observation_seeds"],
        "unused_reserve": seeds["unused_reserve_process_seeds"],
        "excluded_primary": seeds["excluded_primary_process_seeds"],
    }
    seeds["candidate_libraries"]["L1"]["batch1"]["process_seeds"][0] = other_sources[site][0]
    with pytest.raises(study.BudgetError, match="seed overlap within the study"):
        study.validate_frozen_payload(payload)


@pytest.mark.parametrize("change", ("missing", "unknown", "wrong_type", "length", "key_type"))
def test_frozen_payload_requires_exact_structure_and_types(
    yaml_payload: dict[str, Any], change: str
) -> None:
    payload = deepcopy(yaml_payload)
    if change == "missing":
        del payload["fixed_scenario"]["waning_enabled"]
    elif change == "unknown":
        payload["implementation"]["retry_on_error"] = True
    elif change == "wrong_type":
        payload["implementation"]["retries"] = False
    elif change == "length":
        payload["dimensions"]["beta"]["candidates"].pop()
    else:
        payload["process_hashes"][86001] = payload["process_hashes"].pop("86001")
    with pytest.raises(study.CampaignError, match="frozen declaration"):
        study.validate_frozen_payload(payload)


@pytest.mark.parametrize(
    "change,error",
    [
        ("crlf", "study config must use LF bytes"),
        ("duplicate", "study config SHA-256 mismatch"),
        ("earlier seed", "seed overlap with an earlier or retired seed set"),
    ],
)
def test_cli_fails_closed_with_plain_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], change: str, error: str
) -> None:
    content = CONFIG.read_bytes()
    if change == "crlf":
        content = content.replace(b"\n", b"\r\n")
    elif change == "duplicate":
        content += b"mode: ci\n"
    else:
        content = content.replace(b"- 86001\n", b"- 96030\n", 1)
    config = tmp_path / "invalid.yaml"
    config.write_bytes(content)
    assert (
        study.main(["dry-run", "--config", str(config), "--predeclaration", str(PREDECLARATION)])
        == 1
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() == error


def test_dry_run_reports_all_three_exact_workload_columns(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        study.main(["dry-run", "--config", str(CONFIG), "--predeclaration", str(PREDECLARATION)])
        == 0
    )
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "predeclaration_sha256": "67c3c7c03c1ec0f6176e430098c702a913368de51a9e8793c145094255b71094",
        "mode": "ci",
        "latent_days": 30,
        "calendar_dates": 34,
        "shared_panel": _SHARED,
        "libraries": {f"L{number}": _LIBRARY for number in range(1, 7)},
        "totals": _TOTALS,
    }


@pytest.mark.parametrize(
    "cap, message",
    [("SHARED_CAPS", "shared-panel"), ("LIBRARY_CAPS", "L1"), ("TOTAL_CAPS", "total")],
)
def test_workload_rejects_mismatch_in_each_cap_column(
    monkeypatch: pytest.MonkeyPatch, cap: str, message: str
) -> None:
    counts = getattr(frozen, cap)
    monkeypatch.setattr(frozen, cap, (*counts[:-1], 1))
    with pytest.raises(study.BudgetError, match=f"predicted {message} work differs"):
        study.plan_workload(study.StudyConfig())


@pytest.mark.parametrize(
    "change", ({"mode": "full"}, {"duration_days": 31}, {"observation_horizon_tail_days": 3})
)
def test_workload_rejects_runtime_mode_or_calendar_change(change: dict[str, Any]) -> None:
    with pytest.raises(study.BudgetError, match="runtime config differs"):
        study.plan_workload(replace(study.StudyConfig(), **change))


def _truth_diagnostics() -> phase0.TruthDiagnostics:
    return phase0.TruthDiagnostics(
        inoculation_acquisitions=10,
        local_secondary_infections=1,
        symptomatic_reports=1,
        asymptomatic_reports=1,
        nonzero_combined_report_dates=3,
        chronology_passed=True,
        latent_incidence_conservation_passed=True,
        namespace_passed=True,
        complete=True,
        raw_values={
            "natural_history": {"chronology_passed": True},
            "latent_states": {"conserved": True},
            "observation_chronology_and_conservation": {
                "no_report_before_infection": True,
                "latent_incidence_conservation": True,
            },
        },
    )


def _panel(first: phase0.TruthDiagnostics | None = None) -> study.SharedPanelEvaluation:
    rows = dict.fromkeys(_TARGET_SEEDS, _truth_diagnostics())
    if first is not None:
        rows[_TARGET_SEEDS[0]] = first
    return study.evaluate_shared_panel(rows, evidence=study.IntegrityEvidence(True, True, _SHARED))


def _rows() -> list[study.BlindRecord]:
    profiles = tuple(
        phase0.ProfileDiagnostic(name, (), (), 0.0, 1.0, False, 1.0, True) for name in _DIMENSIONS
    )
    return [
        study.BlindRecord(seed, "0" * 64, _TRUTH, profiles, False, 625) for seed in _TARGET_SEEDS
    ]


def _evaluate(
    rows: list[study.BlindRecord], panel: study.SharedPanelEvaluation | None = None
) -> study.RecoveryEvaluation:
    return study.evaluate_recovery(
        rows, shared_panel=panel or _panel(), evidence=study.IntegrityEvidence(True, True, _LIBRARY)
    )


def _unidentified(row: study.BlindRecord, dim: str) -> study.BlindRecord:
    return replace(
        row,
        profiles=tuple(
            replace(p, identified=False) if p.dimension == dim else p for p in row.profiles
        ),
    )


@pytest.mark.parametrize(
    "field,below",
    [
        ("inoculation_acquisitions", 9),
        ("local_secondary_infections", 0),
        ("symptomatic_reports", 0),
        ("asymptomatic_reports", 0),
        ("nonzero_combined_report_dates", 2),
    ],
)
def test_p2_conditions_are_computed_and_reported_separately(field: str, below: int) -> None:
    panel = _panel(replace(_truth_diagnostics(), **{field: below}))
    assert panel.predicates == {"P1": True, "P2": False, "P3": True, "P9": True, "P10": True}
    assert panel.failed_conditions == {86001: (field,)}


@pytest.mark.parametrize(
    "section, flag, condition",
    [
        ("natural_history", "chronology_passed", "natural_history.chronology_passed"),
        ("latent_states", "conserved", "states.conserved"),
        (
            "observation_chronology_and_conservation",
            "no_report_before_infection",
            "no_report_before_infection",
        ),
        (
            "observation_chronology_and_conservation",
            "latent_incidence_conservation",
            "latent_incidence_conservation",
        ),
    ],
)
@pytest.mark.parametrize("value", (False, None, "true"))
def test_p3_requires_each_raw_input_even_when_grouped_flags_pass(
    section: str, flag: str, condition: str, value: bool | str | None
) -> None:
    diagnostics = _truth_diagnostics()
    raw = deepcopy(diagnostics.raw_values)
    if value is None:
        del raw[section][flag]
    else:
        raw[section][flag] = value
    panel = _panel(replace(diagnostics, raw_values=raw))
    assert panel.predicates == {"P1": True, "P2": True, "P3": False, "P9": True, "P10": True}
    assert panel.failed_conditions == {86001: (condition,)}


def test_completion_and_namespace_are_not_p2_inputs() -> None:
    inputs = replace(_truth_diagnostics(), complete=False, namespace_passed=False)
    assert not inputs.viable
    panel = _panel(inputs)
    assert panel.predicates == {"P1": False, "P2": True, "P3": True, "P9": False, "P10": True}


def test_missing_evidence_and_rosters_fail_closed() -> None:
    panel = study.evaluate_shared_panel(dict.fromkeys(_TARGET_SEEDS, _truth_diagnostics()))
    assert panel.predicates == {"P1": False, "P2": True, "P3": True, "P9": False, "P10": False}
    evaluation = study.evaluate_recovery(_rows(), shared_panel=_panel())
    assert evaluation.library_integrity == {"P1": False, "P9": False, "P10": False}
    assert evaluation.recovery_met and not evaluation.nonrecovery_ok and evaluation.status == "FAIL"
    rows = _rows()
    assert not _evaluate(rows[:-1]).library_integrity["P1"]
    rows[0] = rows[1]
    assert not _evaluate(rows).library_integrity["P1"]
    assert _evaluate(rows).mean_bias == dict.fromkeys(_DIMENSIONS)
    rows = _rows()
    rows[0] = replace(rows[0], estimate_hash="", scored_cell_count=624)
    assert _evaluate(rows).library_integrity == {"P1": False, "P9": False, "P10": True}


@pytest.mark.parametrize("field", _WORK_FIELDS)
def test_p10_requires_exact_operational_work_including_descriptive_scoring(field: str) -> None:
    measured = {**_LIBRARY}
    del measured[field]
    for candidate in (
        measured,
        {**_LIBRARY, field: _LIBRARY[field] + 1},
        {**_LIBRARY, field: float(_LIBRARY[field])},
    ):
        evaluation = study.evaluate_recovery(
            _rows(), shared_panel=_panel(), evidence=study.IntegrityEvidence(True, True, candidate)
        )
        assert evaluation.library_integrity == {"P1": True, "P9": True, "P10": False}
        assert evaluation.recovery_met


@pytest.mark.parametrize("hits,passes", [(16, True), (15, False)])
@pytest.mark.parametrize("dimension", _DIMENSIONS)
def test_twenty_target_dimension_hit_endpoint(hits: int, passes: bool, dimension: str) -> None:
    rows = _rows()
    for index in range(hits, 20):
        rows[index] = _unidentified(rows[index], dimension)
    result = _evaluate(rows)
    assert result.hits[dimension] == hits
    assert result.predicates["P5"] is passes
    assert result.boundary_counts[dimension] == 0


@pytest.mark.parametrize("joint,passes", [(12, True), (11, False)])
def test_twenty_target_joint_endpoint(joint: int, passes: bool) -> None:
    rows = _rows()
    for index in range(joint, 20):
        rows[index] = _unidentified(rows[index], _DIMENSIONS[(index - joint) % 4])
    result = _evaluate(rows)
    assert result.joint_hits == joint
    assert result.predicates["P6"] is passes
    assert result.predicates["P5"]


@pytest.mark.parametrize("boundary,passes", [(4, True), (5, False)])
@pytest.mark.parametrize(
    "dimension,edge,safe",
    [
        ("beta", 0.04, 0.10),
        ("inoculation_day_offset", 0, 3),
        ("symptomatic_detection_probability", 0.50, 0.875),
        ("asymptomatic_detection_probability", 0.10, 0.325),
    ],
)
def test_twenty_target_boundary_endpoint_is_independent_of_hits(
    boundary: int, passes: bool, dimension: str, edge: float, safe: float
) -> None:
    rows = [_unidentified(row, dimension) for row in _rows()]
    for index in range(20):
        selected = replace(_TRUTH, **{dimension: edge if index < boundary else safe})
        rows[index] = replace(rows[index], selected=selected)
    result = _evaluate(rows)
    assert result.hits[dimension] == 0
    assert result.boundary_counts[dimension] == boundary
    assert sum(row.boundary_flags[dimension] for row in result.rows) == boundary
    assert result.predicates["P8"] is passes
    assert not result.predicates["P5"]


@pytest.mark.parametrize(
    "name,low,high,limit",
    list(
        zip(
            _DIMENSIONS,
            (0.06, 1, 0.625, 0.175),
            (0.10, 3, 0.875, 0.325),
            map(Decimal, ("0.01", "0.5", "0.0625", "0.0375")),
            strict=True,
        )
    ),
)
@pytest.mark.parametrize("sign", (-1, 1))
def test_twenty_target_decimal_tolerance_and_bias_endpoints(
    name: str, low: float, high: float, limit: Decimal, sign: int
) -> None:
    rows = _rows()
    selected = replace(_TRUTH, **{name: low if sign < 0 else high})
    for index in range(10):
        rows[index] = replace(rows[index], selected=selected)
    result = _evaluate(rows)
    assert result.hits[name] == 20
    assert result.mean_bias[name] == sign * limit
    assert Decimal(result.bias_margins[name]) == 0
    assert result.predicates["P7"]
    rows[10] = replace(rows[10], selected=selected)
    assert not _evaluate(rows).predicates["P7"]


@pytest.mark.parametrize("positive,expected", [(10, "0"), (15, "0.0375")])
def test_twenty_target_decimal_bias_cancellation_is_exact(positive: int, expected: str) -> None:
    rows = _rows()
    for index, row in enumerate(rows):
        rows[index] = replace(
            row,
            selected=replace(
                _TRUTH, asymptomatic_detection_probability=0.325 if index < positive else 0.175
            ),
        )
    with localcontext() as context:
        context.prec = 2  # The caller's Decimal context must have no effect.
        result = _evaluate(rows)
    assert result.mean_bias["asymptomatic_detection_probability"] == Decimal(expected)
    assert result.hits["asymptomatic_detection_probability"] == 20
    assert result.predicates["P7"]


def test_global_tie_and_undefined_bias_are_reported_separately() -> None:
    rows = _rows()
    rows[0] = replace(rows[0], selected=None, numerical_tie=True)
    result = _evaluate(rows)
    assert not result.predicates["P4"]
    assert not result.predicates["P7"]
    assert result.mean_bias == dict.fromkeys(_DIMENSIONS)
    assert result.tie_count == 1
    assert result.joint_hits == 19
    assert all(value == 0 for value in result.boundary_counts.values())


@pytest.mark.parametrize(
    "arm,verdict,hits,joint,boundaries,biases",
    [
        ("B", "FAIL", (10, 7, 9, 10), 7, (0, 3, 0, 0), ("0.002", "0.1", "-0.0125", "-0.0075")),
        ("i", "PASS", (10, 8, 8, 10), 6, (0, 2, 0, 0), ("0", "-0.2", "0", "0")),
    ],
)
def test_historical_blind_records_reproduce_confirmed_exit_audit(
    arm: str,
    verdict: str,
    hits: tuple[int, ...],
    joint: int,
    boundaries: tuple[int, ...],
    biases: tuple[str, ...],
) -> None:
    # Expected findings and work caps are independently transcribed from exit-audit
    # sections 2, 4 and 5. Recovery inputs come from the retained bundle projection.
    fixture = json.loads(HISTORICAL.read_bytes())
    sources = fixture["source_sha256"]
    assert fixture["bundle_sha256sums_sha256"] == (
        "e6649a4b32289ad32cec7862ed79ea75a5123d0231178bebf0db78f0fd54c8fc"
    )
    audit = fixture["audit"]
    audit_bytes = _committed(ROOT / audit["path"], audit["commit"])
    assert (
        hashlib.sha256(audit_bytes).hexdigest()
        == audit["sha256"]
        == ("cf758f26a50986f04c7549ffbb855387d515230739f4f0cd9a27372bec617595")
    )
    assert audit["verdict"] == "CONFIRMED"
    assert b"JOS G35-B CAMPAIGN EXIT AUDIT: CONFIRMED" in audit_bytes
    assert len(sources) == 27 and all(
        re.fullmatch("[0-9a-f]{64}", digest) for digest in sources.values()
    )

    shared = fixture["shared_panel"]
    seeds = tuple(range(82001, 82011))
    assert tuple(shared["target_seeds"]) == seeds
    truth = {
        int(seed): phase0.TruthDiagnostics(
            **{key: value for key, value in row.items() if key != "viable"}
        )
        for seed, row in shared["truth_diagnostics"].items()
    }
    assert len(truth) == 10 and truth.keys() == set(seeds)
    # G35-B charged the shared target work to B and i reused that panel.
    # Split measured B work using the ten retained completed truth runs.
    completed = sum(item.complete for item in truth.values())
    shared_measured = {
        "builds": completed,
        "latent_calls": completed,
        "observation_transforms": completed,
        "cells": 0,
        "serosurvey_samples": 0,
    }
    shared_caps = {
        "builds": 10,
        "latent_calls": 10,
        "observation_transforms": 10,
        "cells": 0,
        "serosurvey_samples": 0,
    }
    panel = study.evaluate_shared_panel(
        truth,
        expected_target_seeds=seeds,
        expected_work=shared_caps,
        evidence=study.IntegrityEvidence(
            shared["completion_confirmed"], shared["provenance_confirmed"], shared_measured
        ),
    )
    assert all(panel.predicates.values())

    historical_arm = fixture["arms"][arm]
    records = historical_arm["gate_records"]
    assert tuple(map(int, records)) == seeds
    rows = []
    for seed in seeds:
        record = records[str(seed)]
        readback = record["readback_entry"]
        assert readback["target_seed"] == seed and readback["role"] == "gate"
        assert sources[record["source"]] == readback["sha256"]
        assert record["estimate_hash"] == readback["estimate_hash"]
        selected = (
            None if record["selected"] is None else phase0.CandidateCell(**record["selected"])
        )
        profiles = tuple(
            phase0.ProfileDiagnostic(
                **{
                    **profile,
                    "values": tuple(profile["values"]),
                    "profiled_objectives": tuple(profile["profiled_objectives"]),
                }
            )
            for profile in record["profiles"]
        )
        rows.append(
            study.BlindRecord(
                seed,
                record["estimate_hash"],
                selected,
                profiles,
                record["numerical_tie"],
                record["scored_cell_count"],
            )
        )
    counts = historical_arm["work"]
    measured = counts["measured"]
    assert counts["measured_equals_planned"] is True and measured == counts["planned"]
    caps = (
        {
            "builds": 13,
            "latent_calls": 85,
            "observation_transforms": 1885,
            "cells": 625,
            "serosurvey_samples": 0,
        }
        if arm == "B"
        else {
            "builds": 9,
            "latent_calls": 225,
            "observation_transforms": 5625,
            "cells": 625,
            "serosurvey_samples": 0,
        }
    )
    assert measured == caps
    if arm == "B":
        measured = {key: value - shared_measured[key] for key, value in measured.items()}
        caps = {key: value - shared_caps[key] for key, value in caps.items()}
    result = study.evaluate_recovery(
        rows,
        shared_panel=panel,
        expected_work=caps,
        evidence=study.IntegrityEvidence(
            historical_arm["completion_confirmed"], historical_arm["provenance_confirmed"], measured
        ),
    )
    assert result.status == verdict
    assert set(result.predicates) == {f"P{index}" for index in range(1, 11)}
    assert result.nonrecovery_ok
    assert {key for key, passed in result.predicates.items() if not passed} == (
        {"P5", "P8"} if arm == "B" else set()
    )
    assert tuple(result.hits[name] for name in _DIMENSIONS) == hits
    assert result.joint_hits == joint
    assert tuple(result.boundary_counts[name] for name in _DIMENSIONS) == boundaries
    assert tuple(result.mean_bias[name] for name in _DIMENSIONS) == tuple(map(Decimal, biases))


def _truth_failure(condition: str) -> phase0.TruthDiagnostics:
    inputs = _truth_diagnostics()
    if "P3" in condition:
        raw = {
            **inputs.raw_values,
            "observation_chronology_and_conservation": {
                "no_report_before_infection": False,
                "latent_incidence_conservation": True,
            },
        }
        inputs = replace(inputs, raw_values=raw)
    if "P2" in condition:
        inputs = replace(inputs, local_secondary_infections=0)
    return inputs


def _library_examples(
    panel: study.SharedPanelEvaluation,
) -> tuple[study.RecoveryEvaluation, study.RecoveryEvaluation]:
    passing = _rows()
    for index in range(4):
        passing[index] = _unidentified(passing[index], "beta")
    failing = passing.copy()
    failing[4] = _unidentified(failing[4], "beta")
    return _evaluate(passing, panel), _evaluate(failing, panel)


@pytest.mark.parametrize(
    "event,expected_class,expected_k",
    [
        ("campaign_exception", "VOID", None),
        ("established_departure", "VOID", None),
        ("shared_P1", "VOID", None),
        ("shared_P9", "VOID", None),
        ("shared_P10", "VOID", None),
        ("library_P1", "VOID", None),
        ("library_P9", "VOID", None),
        ("library_P10", "VOID", None),
        ("P2", "NO-READING", 0),
        ("P3", "NO-READING", 0),
        ("P2+P3", "NO-READING", 0),
        (0, "CONSISTENT-FAIL", 0),
        (1, "MIXED", 1),
        (2, "MIXED", 2),
        (3, "MIXED", 3),
        (4, "MIXED", 4),
        (5, "MIXED", 5),
        (6, "CONSISTENT-PASS", 6),
    ],
)
def test_classification_complete_partition_and_void_precedence(
    event: str | int, expected_class: str, expected_k: int | None
) -> None:
    # Shared P2 also fails in every VOID case to exercise precedence.
    panel = _panel(_truth_failure("P2" if expected_class == "VOID" else str(event)))
    if isinstance(event, str) and event.startswith("shared_"):
        panel = replace(panel, predicates={**panel.predicates, event.split("_")[1]: False})
    passing, failing = _library_examples(panel)
    recoveries = event if isinstance(event, int) else 3
    libraries = [passing] * recoveries + [failing] * (6 - recoveries)
    if isinstance(event, str) and event.startswith("library_"):
        libraries[-1] = replace(
            failing, library_integrity={**failing.library_integrity, event.split("_")[1]: False}
        )
    result = study.classify_campaign(
        libraries,
        campaign_exception=event == "campaign_exception",
        established_departure=event == "established_departure",
    )
    if expected_class == "VOID":
        assert isinstance(result, study.VoidCampaign)
        assert asdict(result) == {"campaign_status": "VOID", "cause": result.cause}
        assert result.cause
        assert study.reading(result) is None
        return
    assert isinstance(result, study.IntactCampaign)
    assert result.reading_class == expected_class
    assert result.k == expected_k and result.k_prime == recoveries
    assert result.verdicts == ("PASS",) * expected_k + ("FAIL",) * (6 - expected_k)
    if expected_class == "NO-READING":
        failures = {
            "P2": ("local_secondary_infections",),
            "P3": ("no_report_before_infection",),
            "P2+P3": ("local_secondary_infections", "no_report_before_infection"),
        }
        assert asdict(result.cause) == {
            "cause": "shared_panel",
            "failed_conditions": {86001: failures[event]},
        }
    else:
        assert result.cause is None


def test_classification_requires_every_library_and_one_shared_panel() -> None:
    good, _ = _library_examples(_panel())
    different, _ = _library_examples(_panel(_truth_failure("P2")))
    assert study.classify_campaign((good,) * 5) == study.VoidCampaign(
        "P1: incomplete library evaluations"
    )
    assert study.classify_campaign((good,) * 5 + (different,)) == study.VoidCampaign(
        "P9: inconsistent shared panel"
    )
    assert study.classify_campaign((), campaign_exception=True) == study.VoidCampaign(
        "campaign_exception"
    )


def _frozen_readings(document: str) -> dict[str, str]:
    block = document.split("### 7.4 Readings", 1)[1].split("### 7.5", 1)[0]
    return dict(re.findall(r'^\*\*([A-Z-]+)\.\*\* "([^"]+)"', block, flags=re.MULTILINE))


@pytest.mark.parametrize("case", [0, 1, 2, 3, 4, 5, 6, "P2", "P3", "P2+P3"])
def test_reading_uses_frozen_text_and_excludes_every_forbidden_word(
    frozen_document: str, case: str | int
) -> None:
    panel = _panel(_truth_failure(str(case)))
    passing, failing = _library_examples(panel)
    k = case if isinstance(case, int) else 3
    result = study.classify_campaign([passing] * k + [failing] * (6 - k))
    assert isinstance(result, study.IntactCampaign)
    text = study.reading(result)
    assert text is not None
    forbidden = ("nearly", "almost", "majority", "most", "typical", "best library")
    for word in forbidden:
        assert re.search(rf"\b{word}\b", text, flags=re.IGNORECASE) is None

    template = _frozen_readings(frozen_document)[result.reading_class]
    if isinstance(case, str):
        cause_template = re.search(r'Cause sentence, `shared_panel`: "([^"]+)"', frozen_document)[1]
        conditions = {
            "P2": "local_secondary_infections",
            "P3": "no_report_before_infection",
            "P2+P3": "local_secondary_infections, no_report_before_infection",
        }
        cause = cause_template.replace(
            "<target seeds: failed conditions>", f"86001: {conditions[case]}"
        )
        template = template.replace("<Cause sentence.>", cause).replace("<k′>", "3")
    else:
        failures = "; ".join(
            f"L{number}: P5 (beta=15/20, inoculation_day_offset=20/20, "
            "symptomatic_detection_probability=20/20, asymptomatic_detection_probability=20/20)"
            for number in range(k + 1, 7)
        )
        for slot, value in {
            "<k>": str(k),
            "<6 − k>": str(6 - k),
            "<d>": "0",
            "<n>": "6",
            "<ℓ: predicates with counts>": failures,
        }.items():
            template = template.replace(slot, value)
    assert text == template


@pytest.mark.parametrize(
    "k_prime,m,triggers",
    [
        (3, 12, (True, False)),  # 4k′ = m
        (3, 11, (False, False)),  # 4k′ = m + 1
        (6, 24, (True, True)),
        (5, 23, (True, False)),
        (0, 0, (False, False)),
    ],
)
def test_reference_trigger_integer_endpoints(
    k_prime: int, m: int, triggers: tuple[bool, bool]
) -> None:
    assert study.reference_triggers("MIXED", k_prime=k_prime, m=m) == triggers


@pytest.mark.parametrize(
    "reading_class, k_prime, eligible",
    [
        ("CONSISTENT-PASS", 6, True),
        ("MIXED", 3, True),
        ("CONSISTENT-FAIL", 0, True),
        ("NO-READING", 3, False),
        ("VOID", 0, False),
    ],
)
def test_reference_class_eligibility_and_verbatim_sentence_order(
    frozen_document: str, reading_class: study.ReadingClass | str, k_prime: int, eligible: bool
) -> None:
    source = frozen_document.split("**Disclosure sentences", 1)[1].split("For CONSISTENT-PASS", 1)[
        0
    ]
    expected = tuple(
        sentence.replace("<k′>", str(k_prime)).replace("<m>", "24")
        for sentence in re.findall(r'\*\* "([^"]+)"', source)
    )
    assert len(expected) == 2
    assert study.reference_triggers(reading_class, k_prime=k_prime, m=24) == (eligible, eligible)
    assert study.reference_sentences(reading_class, k_prime=k_prime, m=24) == (
        expected if eligible else ()
    )


def test_status_phrase_exact_lifecycle_variants() -> None:
    prefix = (
        "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); "
        "G35-B: B FAIL, i PASS, ii FAIL, iii FAIL"
    )
    assert study.status_phrase(declaration_frozen=False) == prefix
    assert study.status_phrase() == prefix + "; G43: not run"
    assert study.status_phrase(study.VoidCampaign("campaign_exception")) == prefix + "; G43: VOID"
    passing, failing = _library_examples(_panel())
    intact = study.classify_campaign([passing, failing, passing, failing, failing, passing])
    assert (
        study.status_phrase(intact)
        == prefix + "; G43: L1 PASS, L2 FAIL, L3 PASS, L4 FAIL, L5 FAIL, L6 PASS"
    )
    shared_failure, _ = _library_examples(_panel(_truth_failure("P3")))
    assert study.status_phrase(study.classify_campaign([shared_failure] * 6)) == (
        prefix + "; G43: L1 FAIL, L2 FAIL, L3 FAIL, L4 FAIL, L5 FAIL, L6 FAIL"
    )


# §8's final positions, including the three replacements and their original observation IDs.
_MOCK_LIBRARY_SEEDS = (
    tuple(range(87101, 87113)),
    tuple(range(87201, 87213)),
    (87351, 87302, 87303, 87304, 87352, *range(87306, 87313)),
    tuple(range(87401, 87413)),
    (87501, 87502, 87503, 87504, 87505, 87551, *range(87507, 87513)),
    tuple(range(87601, 87613)),
)
_MOCK_REPLICATES = {
    seed: (library, position, 99000 + 100 * library + position)
    for library, seeds in enumerate(_MOCK_LIBRARY_SEEDS, 1)
    for position, seed in enumerate(seeds, 1)
}
_MOCK_GRID = (
    (0.04, 0.06, 0.08, 0.10, 0.12),
    tuple(range(5)),
    (0.50, 0.625, 0.75, 0.875, 1.00),
    (0.10, 0.175, 0.25, 0.325, 0.40),
)
_MOCK_START = date(2025, 1, 6)
_MOCK_DATES = tuple((_MOCK_START + timedelta(days=index)).isoformat() for index in range(34))
_MOCK_LATENT_COUNT = 60


@pytest.fixture(scope="module")
def declared_process_hashes(frozen_document: str) -> dict[int, tuple[str, ...]]:
    table = frozen_document.split("### Final seed table (92 seeds)\n")[1].split(
        "### Unused reserves"
    )[0]
    hashes = {}
    for line in table.splitlines():
        if line.startswith(("| target |", "| candidate |")):
            fields = [item.strip() for item in line.strip("|").split("|")]
            hashes[int(fields[4].split()[0])] = tuple(item.strip("`") for item in fields[-3:])
    assert len(hashes) == 92
    return hashes


class _MockLatent(SimpleNamespace):
    @property
    def transmission_events(self) -> list[dict[str, Any]]:
        self.on_truth(self.config.seed)
        return [
            {
                "imported": index < 10,
                "source_kind": "import" if index < 10 else "local",
                "infection_date": _MOCK_DATES[2],
                "infectious_start_date": _MOCK_DATES[4],
                "recovery_date": _MOCK_DATES[9],
                "symptomatic": index % 2 == 0,
                "symptom_onset_date": _MOCK_DATES[4] if index % 2 == 0 else None,
                "infected_uid": index,
            }
            for index in range(_MOCK_LATENT_COUNT)
        ]


def _mock_dispatches(
    monkeypatch: pytest.MonkeyPatch,
    process_hashes: dict[int, tuple[str, ...]],
    ledger: study.WorkLedger,
    *,
    on_truth: Any = None,
) -> dict[str, Any]:
    calls = {"builds": Counter(), "latent_calls": Counter(), "observation_transforms": Counter()}
    totals = Counter()

    def record(kind: str, key: Any) -> None:
        totals[kind] += 1
        assert ledger.totals[kind] == totals[kind], f"{kind} reached execution before reservation"
        calls[kind][key] += 1

    def before_truth(seed: int) -> None:
        assert on_truth is not None, f"early truth access for {seed}"
        on_truth(seed)

    def build(root: Path, mode: str, seed: int, path: Path, **options: Any) -> Any:
        record("builds", seed)
        assert root == ROOT and mode == "ci" and options == {"write_m4": True}
        assert path.name == str(seed)
        m2, m3, m4 = process_hashes[seed]
        for stage, diagnostic in (
            (
                "m2",
                {"builder": {"private_assignment_residual_fallback": {}}} if seed == 86005 else {},
            ),
            ("m3", {"builder": {"destination_reassignment_fallback": {}}} if seed == 87103 else {}),
        ):
            directory = path / stage
            directory.mkdir(parents=True)
            (directory / "diagnostics.json").write_text(json.dumps(diagnostic))
        return SimpleNamespace(
            generated=SimpleNamespace(
                config=SimpleNamespace(seed=seed, mode=mode),
                m2_input=SimpleNamespace(
                    manifest=SimpleNamespace(seed=seed, mode=mode, logical_content_hash=m2),
                    artifact_directory=path / "m2",
                ),
                m3_input=SimpleNamespace(
                    manifest=SimpleNamespace(seed=seed, mode=mode, logical_content_hash=m3),
                    artifact_directory=path / "m3",
                ),
                logical_content_hash=m4,
            )
        )

    def latent(parent: Any, config: OutbreakRunConfig, parameters: Any) -> Any:
        assert isinstance(config, OutbreakRunConfig)
        offset = (date.fromisoformat(next(iter(config.import_schedule))) - _MOCK_START).days
        record("latent_calls", (config.seed, config.beta, offset))
        assert config.seed == parent.config.seed and config.mode == parent.config.mode == "ci"
        assert config.start_date == _MOCK_START and config.duration_days == 30
        assert config.initial_seed_count == 0 and config.import_rate_per_day == 0
        assert list(config.import_schedule.values()) == [10]
        assert config.symptomatic_probability == 0.6 and not config.waning_enabled
        assert tuple(config.route_multipliers.values()) == (1.0,) * 11
        assert config.latent_duration.family == "constant" and config.latent_duration.mean_days == 2
        assert config.infectious_duration.family == "constant"
        assert config.infectious_duration.mean_days == 5
        return _MockLatent(
            config=config,
            generated=parent,
            offset=offset,
            on_truth=before_truth,
            daily_epidemic=[
                {"date": day, "susceptible": 2990, "exposed": 3, "infectious": 2, "recovered": 5}
                for day in _MOCK_DATES[:30]
            ],
            diagnostics={
                "benchmark": {"n_agents": 3000, "runtime_seconds": 0.125},
                "natural_history": {"chronology_passed": True},
                "states": {"conserved": True},
            },
        )

    def observe(result: Any, config: ObservationConfig) -> Any:
        assert isinstance(config, ObservationConfig)
        assert config.reporting_delay.kind == config.detection_delay.kind == "fixed"
        assert config.reporting_delay.days == (2,) and config.detection_delay.days == (0,)
        assert config.analysis_horizon_tail_days == 4 and config.day_of_week_effect == (1.0,) * 7
        seed = result.config.seed
        sym = config.parameters["symptomatic_detection_probability"].value
        asym = config.parameters["asymptomatic_detection_probability"].value
        cell = (result.config.beta, result.offset, sym, asym)
        record(
            "observation_transforms",
            (seed, config.observation_seed, config.observation_config_id, *cell),
        )
        events = [
            {"report_date": _MOCK_DATES[day], "symptomatic": symptomatic}
            for day, symptomatic, values, value in zip(
                (6, 7, 8, 9), (True, True, False, False), _MOCK_GRID, cell, strict=True
            )
            for _ in range(1 + 3 * values.index(value))
        ]
        if seed in _TARGET_SEEDS:
            target_position = seed - _TARGET_SEEDS[0]
            assert config.observation_seed == 98001 + target_position
            assert config.observation_config_id == "v13-g43-target"
            events.append({"report_date": _MOCK_DATES[12 + target_position], "symptomatic": True})
        else:
            library, position, observation_seed = _MOCK_REPLICATES[seed]
            assert config.observation_seed == observation_seed
            assert config.observation_config_id == "v13-g43-fit"
            events.extend(
                (
                    {"report_date": _MOCK_DATES[11 + position], "symptomatic": True},
                    {"report_date": _MOCK_DATES[24 + library], "symptomatic": False},
                )
            )
        events.extend(
            {"report_date": None, "symptomatic": False}
            for _ in range(_MOCK_LATENT_COUNT - len(events))
        )
        for event in events:
            event.update(
                {
                    "infection_date": _MOCK_DATES[2],
                    "infectious_start_date": _MOCK_DATES[4],
                    "recovery_date": _MOCK_DATES[9],
                    "symptom_onset_date": _MOCK_DATES[4] if event["symptomatic"] else None,
                    "detection_date": _MOCK_DATES[4] if event["report_date"] is not None else None,
                }
            )
        return SimpleNamespace(
            config=config,
            latent_run=result,
            observation_events=events,
            daily_observed_cases=[
                {"date": day, "latent_infections": _MOCK_LATENT_COUNT if index == 2 else 0}
                for index, day in enumerate(_MOCK_DATES)
            ],
            diagnostics={
                "status": "passed",
                "no_report_before_infection": True,
                "latent_incidence_conservation": True,
                "chronology_violations": 0,
                "latent_incidence_conservation_difference": 0,
                "observation_rng": {
                    "stream_namespace": "observation",
                    "stream_key_inputs": [
                        "latent_replicate_seed",
                        "observation_seed",
                        "observation_config_id",
                    ],
                    "stream_fingerprint": hashlib.sha256(
                        str(observation_stream_seed(seed, config)).encode()
                    ).hexdigest(),
                },
            },
        )

    monkeypatch.setattr(study, "build_parent", build)
    monkeypatch.setattr(g35b, "run_outbreak", latent)
    monkeypatch.setattr(g35b, "observe_latent_run", observe)
    return calls


def _table_bytes(table: phase0.ObservedTables) -> bytes:
    return (
        json.dumps(
            {
                "dates": table.dates,
                "symptomatic": table.symptomatic,
                "asymptomatic": table.asymptomatic,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()


@pytest.fixture(scope="module")
def mocked_full_run(
    tmp_path_factory: pytest.TempPathFactory, declared_process_hashes: dict[int, tuple[str, ...]]
) -> Any:
    directory = tmp_path_factory.mktemp("g43-mocked") / "work"
    ledger = study.WorkLedger()
    readbacks = set()
    truth_reads = []
    fit_inputs = []
    persist_paths = []
    scores = Counter()
    scope_slices = (
        tuple(range(1, 13)),
        (1, 2, 3),
        (4, 5, 6),
        (7, 8, 9),
        (10, 11, 12),
        tuple(range(1, 7)),
    )

    def on_truth(seed: int) -> None:
        assert len(readbacks) == 720 and set(persist_paths) == readbacks
        assert sum(scores.values()) == 450_000
        truth_reads.append(seed)

    def counted_loss(target: Any, predictions: Any, r: int, t: int) -> float:
        index, cell_index = divmod(sum(scores.values()), 625)
        scope, target_index = divmod(index, 20)
        library_index, slice_index = divmod(scope, 6)
        group = "gate" if slice_index == 0 else "descriptive"
        kind = f"{group}_loss_evaluations"
        scores[kind] += 1
        assert ledger.totals[kind] == scores[kind]
        positions = scope_slices[slice_index]
        assert r == len(positions) and t == 34
        if cell_index in (0, 624):
            seed = _TARGET_SEEDS[target_index]
            from_disk = (directory / "targets" / f"{seed}.json").read_bytes()
            digest = hashlib.sha256(from_disk).hexdigest()
            assert hashlib.sha256(_table_bytes(target)).hexdigest() == digest
            assert target.dates == _MOCK_DATES
            assert target.symptomatic[12 + target_index] == 1
            assert tuple(table.symptomatic.index(1, 12) - 11 for table in predictions) == positions
            assert all(
                table.asymptomatic.index(1, 24) == 25 + library_index for table in predictions
            )
            if cell_index == 0:
                fit_inputs.append((library_index + 1, slice_index, seed, digest))
        return g35b.loss(target, predictions, r, t)

    def persist(path: Path, fit: phase0.BlindFitResult) -> str:
        persist_paths.append(path)
        assert ledger.totals["gate_blind_records"] + ledger.totals[
            "descriptive_blind_records"
        ] == len(persist_paths)
        return g35b._persist_fit(path, fit)

    def readback(path: Path, fit: phase0.BlindFitResult, digest: str) -> None:
        assert len(persist_paths) == 720
        assert not truth_reads
        g35b._verify_blind_readback(path, fit, digest)
        assert path not in readbacks
        readbacks.add(path)

    def after_barrier(method: Any) -> Any:
        def checked(*args: Any, **kwargs: Any) -> Any:
            assert len(readbacks) == 720 and set(persist_paths) == readbacks
            return method(*args, **kwargs)

        return checked

    with pytest.MonkeyPatch.context() as patch:
        calls = _mock_dispatches(patch, declared_process_hashes, ledger, on_truth=on_truth)
        patch.setattr(study, "loss", counted_loss)
        patch.setattr(study, "_persist_fit", persist)
        patch.setattr(study, "_verify_blind_readback", readback)
        for name in (
            "_truth_diagnostics_from_result",
            "evaluate_shared_panel",
            "evaluate_recovery",
            "_reference_evaluation",
        ):
            patch.setattr(study, name, after_barrier(getattr(study, name)))
        gen = study.generate_blind(CONFIG, PREDECLARATION, directory, root=ROOT, ledger=ledger)
        assert not truth_reads and not readbacks
        output = study.evaluate_after_blind(gen)
    assert isinstance(output, study.StudyEvaluation)
    return SimpleNamespace(
        generation=gen,
        output=output,
        calls=calls,
        fit_inputs=fit_inputs,
        truth_reads=truth_reads,
        scores=scores,
        readbacks=readbacks,
    )


def test_mocked_generation_dispatches_frozen_rosters_and_exact_caps(mocked_full_run: Any) -> None:
    run = mocked_full_run
    assert run.calls["builds"] == Counter([*_TARGET_SEEDS, *_MOCK_REPLICATES])
    assert run.calls["latent_calls"] == Counter(
        [(seed, 0.08, 2) for seed in _TARGET_SEEDS]
        + list(product(_MOCK_REPLICATES, *_MOCK_GRID[:2]))
    )
    assert run.calls["observation_transforms"] == Counter(
        [
            (seed, 98001 + i, "v13-g43-target", 0.08, 2, 0.75, 0.25)
            for i, seed in enumerate(_TARGET_SEEDS)
        ]
        + [
            (seed, obs, "v13-g43-fit", *cell)
            for seed, (_, _, obs) in _MOCK_REPLICATES.items()
            for cell in product(*_MOCK_GRID)
        ]
    )
    assert run.scores == {"gate_loss_evaluations": 75_000, "descriptive_loss_evaluations": 375_000}
    assert run.generation.ledger.measured(None) == _SHARED
    for number in range(1, 7):
        assert run.generation.ledger.measured(number) == _LIBRARY
    assert run.generation.ledger.totals == _TOTALS


def test_every_nested_fit_uses_independently_read_shared_target_bytes(mocked_full_run: Any) -> None:
    directory = mocked_full_run.generation.directory / "targets"
    assert set(p.name for p in directory.iterdir()) == {f"{seed}.json" for seed in _TARGET_SEEDS}
    digests = {}
    for position, seed in enumerate(_TARGET_SEEDS):
        sym, asym = [0.0] * 34, [0.0] * 34
        sym[6] = sym[7] = asym[8] = asym[9] = 7.0
        sym[12 + position] = 1.0
        expected = _table_bytes(phase0.ObservedTables(_MOCK_DATES, tuple(sym), tuple(asym)))
        content = (directory / f"{seed}.json").read_bytes()
        assert content == expected
        digests[seed] = hashlib.sha256(content).hexdigest()
    assert len(set(digests.values())) == 20
    assert mocked_full_run.fit_inputs == [
        (library, view, seed, digests[seed])
        for library, view, seed in product(range(1, 7), range(6), _TARGET_SEEDS)
    ]


def test_global_barrier_reads_all_720_records_before_the_first_truth_access(
    mocked_full_run: Any,
) -> None:
    run = mocked_full_run
    assert run.truth_reads == list(_TARGET_SEEDS)
    assert len(run.readbacks) == 720
    assert sum(path.parent.name == "blind_estimates" for path in run.readbacks) == 120
    assert sum(path.parent.parent.name == "descriptive_estimates" for path in run.readbacks) == 600


def test_corrupt_last_descriptive_record_blocks_all_truth_joins(
    mocked_full_run: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    generation = mocked_full_run.generation
    last_record = generation.directory / "library_6/descriptive_estimates/batches_1_2/86020.json"
    original = last_record.read_bytes()

    def unexpected(*args: Any, **kwargs: Any) -> None:
        pytest.fail("truth join called with unreadable descriptive record")

    monkeypatch.setattr(study, "_truth_diagnostics_from_result", unexpected)
    monkeypatch.setattr(study, "evaluate_recovery", unexpected)
    try:
        last_record.write_text("{}")
        with pytest.raises(study.CampaignError, match="read-back mismatch"):
            study.evaluate_after_blind(generation)
    finally:
        last_record.write_bytes(original)


def test_changed_target_table_bytes_are_rejected_before_truth_join(mocked_full_run: Any) -> None:
    generation = mocked_full_run.generation
    path = generation.directory / "targets/86001.json"
    original = path.read_bytes()
    try:
        # Same parsed table, different bytes.
        path.write_bytes(original + b"\n")
        with pytest.raises(study.CampaignError, match="target table SHA-256 mismatch"):
            study.evaluate_after_blind(generation)
    finally:
        path.write_bytes(original)


def test_target_file_mismatch_prevents_dispatch_of_the_first_loss(tmp_path: Path) -> None:
    table = phase0.ObservedTables(_MOCK_DATES, (0.0,) * 34, (0.0,) * 34)
    original = _table_bytes(table)
    path = tmp_path / "target.json"
    path.write_bytes(original + b"\n")
    source = study._TargetTable(path, hashlib.sha256(original).hexdigest())
    ledger = study.WorkLedger()
    with pytest.raises(study.CampaignError, match="target table SHA-256 mismatch"):
        study._fit_library(
            tmp_path,
            {86001: source},
            (_TRUTH,),
            {_TRUTH: (table,) * 12},
            {_TRUTH: ({},) * 12},
            study._ScopedCounter(ledger, 1),
        )
    assert ledger.totals["gate_loss_evaluations"] == 0


@pytest.mark.parametrize(
    "stage,member,error",
    [
        ("build", "generated", "parent metadata"),
        ("build", "generated.config", "parent metadata"),
        ("build", "generated.config.seed", "parent metadata"),
        ("build", "generated.config.mode", "parent metadata"),
        ("build", "generated.m2_input", "parent metadata"),
        ("build", "generated.m2_input.manifest", "parent metadata"),
        ("build", "generated.m2_input.manifest.seed", "parent metadata"),
        ("build", "generated.m2_input.manifest.mode", "parent metadata"),
        ("build", "generated.m2_input.manifest.logical_content_hash", "parent metadata"),
        ("build", "generated.m3_input", "parent metadata"),
        ("build", "generated.m3_input.manifest", "parent metadata"),
        ("build", "generated.m3_input.manifest.seed", "parent metadata"),
        ("build", "generated.m3_input.manifest.mode", "parent metadata"),
        ("build", "generated.m3_input.manifest.logical_content_hash", "parent metadata"),
        ("build", "generated.logical_content_hash", "parent metadata"),
        ("latent", "generated", "latent result omitted"),
        ("latent", "config", "latent result omitted"),
        ("latent", "diagnostics", "runtime_seconds"),
        ("latent", "diagnostics.benchmark", "runtime_seconds"),
        ("latent", "diagnostics.benchmark.runtime_seconds", "runtime_seconds"),
        ("latent", "diagnostics.benchmark.n_agents", "n_agents metadata"),
        ("observe", "config", "namespace evidence"),
        ("observe", "latent_run", "namespace evidence"),
        ("observe", "observation_events", "observation result missing"),
        ("observe", "diagnostics", "namespace evidence"),
        ("observe", "diagnostics.observation_rng", "namespace evidence"),
        ("observe", "diagnostics.observation_rng.stream_namespace", "namespace evidence"),
        ("observe", "diagnostics.observation_rng.stream_key_inputs", "namespace evidence"),
        ("observe", "diagnostics.observation_rng.stream_fingerprint", "namespace evidence"),
    ],
)
def test_generation_rejects_missing_returned_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    declared_process_hashes: Any,
    stage: str,
    member: str,
    error: str,
) -> None:
    ledger = study.WorkLedger()
    _mock_dispatches(monkeypatch, declared_process_hashes, ledger)
    module, name = {
        "build": (study, "build_parent"),
        "latent": (g35b, "run_outbreak"),
        "observe": (g35b, "observe_latent_run"),
    }[stage]
    original = getattr(module, name)

    def missing(*args: Any, **kwargs: Any) -> Any:
        obj = result = original(*args, **kwargs)
        *ancestors, field = member.split(".")
        for part in ancestors:
            obj = obj[part] if isinstance(obj, dict) else getattr(obj, part)
        if isinstance(obj, dict):
            del obj[field]
        else:
            delattr(obj, field)
        return result

    monkeypatch.setattr(module, name, missing)
    with pytest.raises(study.CampaignError, match=error):
        study.generate_blind(CONFIG, PREDECLARATION, tmp_path / "work", root=ROOT, ledger=ledger)
    assert ledger.totals["builds"] == 1


def test_candidate_parent_compares_returned_hash_to_frozen_hash_before_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    declared_process_hashes: Any,
) -> None:
    ledger = study.WorkLedger()
    wrong_hashes = {**declared_process_hashes, 87101: ("0" * 64,) * 3}
    _mock_dispatches(monkeypatch, wrong_hashes, ledger)
    with pytest.raises(study.CampaignError, match="logical hash mismatch for 87101"):
        study.generate_blind(CONFIG, PREDECLARATION, tmp_path / "work", root=ROOT, ledger=ledger)
    assert ledger.measured(None) == _SHARED
    assert ledger.measured(1) == {**dict.fromkeys(_WORK_FIELDS, 0), "builds": 1}


def test_exception_consumes_reserved_slot_and_generation_does_not_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    declared_process_hashes: Any,
) -> None:
    ledger = study.WorkLedger()
    _mock_dispatches(monkeypatch, declared_process_hashes, ledger)
    calls = []

    def abort(parent: Any, config: OutbreakRunConfig, parameters: Any) -> None:
        calls.append(config.seed)
        assert ledger.measured(None)["latent_calls"] == 1
        raise RuntimeError("injected latent failure")

    monkeypatch.setattr(g35b, "run_outbreak", abort)
    with pytest.raises(RuntimeError, match="injected latent failure"):
        study.generate_blind(CONFIG, PREDECLARATION, tmp_path / "work", root=ROOT, ledger=ledger)
    assert calls == [86001]
    assert ledger.totals == {**dict.fromkeys(_WORK_FIELDS, 0), "builds": 1, "latent_calls": 1}
    with pytest.raises(study.BudgetError, match="unused work ledger"):
        study.generate_blind(CONFIG, PREDECLARATION, tmp_path / "second", root=ROOT, ledger=ledger)
    assert calls == [86001]


@pytest.mark.parametrize("kind", _WORK_FIELDS)
def test_work_counter_rejects_per_library_cap_even_with_remaining_total(kind: str) -> None:
    ledger = study.WorkLedger()
    for _ in range(_LIBRARY[kind]):
        ledger.reserve(3, kind)
    with pytest.raises(study.BudgetError, match=f"L3 {kind} cap reached before dispatch"):
        ledger.reserve(3, kind)
    assert ledger.totals[kind] == ledger.measured(3)[kind] == _LIBRARY[kind]
    with pytest.raises(study.BudgetError, match="measured shared-panel work differs"):
        ledger.require_exact()


@pytest.mark.parametrize("scope,match", [(None, "shared-panel"), (6, "L6"), (0, "total")])
def test_work_counter_requires_each_exact_column(scope: int | None, match: str) -> None:
    ledger = study.WorkLedger()
    for library in (None, *range(1, 7)):
        expected = _SHARED if library is None else _LIBRARY
        for kind, count in expected.items():
            for _ in range(count - int(library == scope and kind == "builds")):
                ledger.reserve(library, kind)
    if scope == 0:
        # Isolate a ledger mismatch that would otherwise require broken accounting code.
        ledger._totals["builds"] -= 1
    with pytest.raises(study.BudgetError, match=rf"measured {match} work differs"):
        ledger.require_exact()


def test_mocked_full_run_reports_d1_to_d5_using_only_the_declared_surfaces(
    mocked_full_run: Any,
) -> None:
    result = mocked_full_run.output
    assert result.campaign.reading_class == "CONSISTENT-PASS"
    assert set(result.predicate_descriptives) == set(range(1, 7))
    for item in result.predicate_descriptives.values():
        assert item["label"] == "descriptive_not_a_gate"
        assert item["predicates"] == {f"P{i}": True for i in range(1, 11)}
        assert item["hits"] == dict.fromkeys(_DIMENSIONS, 20) and item["joint_hits"] == 20
        assert item["boundary_counts"] == dict.fromkeys(_DIMENSIONS, 0)
        assert {key: Decimal(value) for key, value in item["mean_bias"].items()} == dict.fromkeys(
            _DIMENSIONS, 0
        )
        assert item["count_margins"] == (4, 4, 4, 4, 8, 4, 4, 4, 4)
        assert item["min_count_margin"] == 4 and item["at_threshold"] is False
        assert tuple(item["bias_margins"].values()) == ("0.01", "0.5", "0.0625", "0.0375")

    matrices = result.matrix_descriptives
    assert matrices["target_seeds"] == _TARGET_SEEDS
    assert matrices["library_numbers"] == tuple(range(1, 7))
    assert len(matrices["matrix"]) == len(matrices["row_summaries"]) == 20
    for seed, row, summary in zip(
        _TARGET_SEEDS, matrices["matrix"], matrices["row_summaries"], strict=True
    ):
        assert len(row) == 6
        for cell in row:
            assert cell == {
                "label": "descriptive_not_a_gate",
                "selected": _TRUTH.as_dict(),
                "joint_hit": True,
                "hits": dict.fromkeys(_DIMENSIONS, True),
                "identified": dict.fromkeys(_DIMENSIONS, True),
                "boundary_flags": dict.fromkeys(_DIMENSIONS, False),
                "numerical_tie": False,
                "reprofiled_offset": 2,
            }
        assert summary == {
            "label": "descriptive_not_a_gate",
            "target_seed": seed,
            "joint_hits": 6,
            "offset_hits": 6,
            "distinct_selected_offsets": 1,
            "all_six_offsets_agree": True,
        }

    for library, descriptives in result.batch_descriptives.items():
        assert descriptives["label"] == "stochastic_replicate_variation"
        assert descriptives["four_batch_offset_agreement_count"] == 20
        assert len(descriptives["targets"]) == 20
        fits = mocked_full_run.generation.libraries[library]
        for row in descriptives["targets"]:
            assert row["four_batch_offsets_agree"]
            assert {item["reprofiled_offset"] for item in row["reprofiled_offsets"].values()} == {2}
            assert len(row["reprofiled_offsets"]) == 6 and len(row["fixed_tuple_spreads"]) == 625
            for index, spread in enumerate(row["fixed_tuple_spreads"]):
                scored = [
                    fits[f"batch{n}"][row["target_seed"]].fit.loss_surface[index]
                    for n in range(1, 5)
                ]
                a, b, c, d = sorted(item.objective for item in scored)
                assert spread == {
                    "cell": scored[0].cell.as_dict(),
                    "label": "stochastic_replicate_variation",
                    "range": d - a,
                    "median": (b + c) / 2,
                }

    references = result.references
    assert references.label == "descriptive_not_a_gate"
    assert references.k_prime == 6 and references.m == 24
    assert references.m_by_library == dict.fromkeys(range(1, 7), 4)
    assert references.libraries_not_met_with_a_batch_met == 0
    assert (references.s1, references.s2) == (True, True)
    assert references.sentences == study.reference_sentences("CONSISTENT-PASS", k_prime=6, m=24)
    for sublibraries in references.libraries.values():
        assert {name: ref.replicates for name, ref in sublibraries.items()} == {
            "batch1": 3,
            "batch2": 3,
            "batch3": 3,
            "batch4": 3,
            "batches_1_2": 6,
        }
        for record in sublibraries.values():
            assert record.criteria_4_to_8_met and record.tie_count == 0
            assert record.hits == dict.fromkeys(_DIMENSIONS, 20) and record.joint_hits == 20
            assert record.boundary_counts == dict.fromkeys(_DIMENSIONS, 0)
            assert all(Decimal(value) == 0 for value in record.mean_bias.values())
    assert sum(mocked_full_run.scores.values()) == 450_000


@pytest.mark.parametrize("last_offset,agree", [(2, True), (None, False), (3, False)])
def test_d4_agreement_uses_unique_offset_profiles_even_with_global_ties(
    last_offset: int | None, agree: bool
) -> None:
    table = phase0.ObservedTables(("2025-01-06",), (0.0,), (0.0,))
    higher = replace(table, symptomatic=(3.0,), asymptomatic=(3.0,))
    grid = tuple(
        replace(_TRUTH, beta=beta, inoculation_day_offset=offset)
        for beta, offset in product((0.08, 0.10), (2, 3))
    )

    def fit(offset: int | None, replicates: int = 3) -> study._FitFile:
        predictions = {
            cell: (table if offset is None or cell.inoculation_day_offset == offset else higher,)
            * replicates
            for cell in grid
        }
        scored = g35b.fit_blind(table, grid, predictions, R=replicates, T=1)
        assert scored.numerical_tie and scored.selected is None
        return study._FitFile(scored, "", "")

    files = {f"batch{n}": {86001: fit(last_offset if n == 4 else 2)} for n in range(1, 5)}
    files.update({"all_twelve": {86001: fit(2, 12)}, "batches_1_2": {86001: fit(2, 6)}})
    descriptive = study._batch_descriptives(files)
    assert descriptive["four_batch_offset_agreement_count"] == int(agree)
    [record] = descriptive["targets"]
    assert record["four_batch_offsets_agree"] is agree
    assert record["reprofiled_offsets"]["batch4"]["reprofiled_offset"] == last_offset
    assert record["reprofiled_offsets"]["batch4"]["offset_profile_tie"] is (last_offset is None)


def test_d3_counts_selected_offsets_but_checks_agreement_on_reprofiled_offsets() -> None:
    grid = tuple(
        replace(_TRUTH, beta=beta, inoculation_day_offset=offset)
        for beta, offset in product((0.08, 0.10), (2, 3))
    )
    table = phase0.ObservedTables(("2025-01-06",), (0.0,), (0.0,))
    high = replace(table, symptomatic=(3.0,))

    def fit(allowed: set[phase0.CandidateCell]) -> study._FitFile:
        predictions = {cell: (table if cell in allowed else high,) * 12 for cell in grid}
        return study._FitFile(g35b.fit_blind(table, grid, predictions, R=12, T=1), "", "")

    selected = fit({_TRUTH})
    global_tie = fit({_TRUTH, replace(_TRUTH, beta=0.10)})
    profile_tie = fit(set(grid))
    shifted = fit({replace(_TRUTH, inoculation_day_offset=3)})
    parent_fits = {
        number: {"all_twelve": dict.fromkeys(_TARGET_SEEDS, selected)} for number in range(1, 7)
    }
    parent_fits[1]["all_twelve"].update({86001: global_tie, 86002: profile_tie, 86003: shifted})
    panel = _panel()
    outputs = [
        _evaluate([record.blind_record(seed) for seed, record in fits["all_twelve"].items()], panel)
        for fits in parent_fits.values()
    ]
    summaries = study._matrix_descriptives(outputs, parent_fits)["row_summaries"]
    assert [summary["distinct_selected_offsets"] for summary in summaries[:3]] == [1, 1, 2]
    assert [summary["all_six_offsets_agree"] for summary in summaries[:3]] == [True, False, False]


@pytest.mark.parametrize("failed_panel", [False, True])
@pytest.mark.parametrize("counts,m,missed", [((4, 3, 1, 4, 0, 0), 12, 2), ((4,) * 6, 24, 3)])
def test_reference_counts_wire_batch_records_to_u1_triggers(
    failed_panel: bool, counts: tuple[int, ...], m: int, missed: int
) -> None:
    panel = _panel(_truth_failure("P2")) if failed_panel else _panel()
    passing, failing = _library_examples(panel)
    campaign = study.classify_campaign([passing, failing, failing, passing, failing, passing])
    assert isinstance(campaign, study.IntactCampaign)
    met = study._reference_evaluation(_rows(), 3)
    with_tie = _rows()
    with_tie[0] = replace(with_tie[0], numerical_tie=True, selected=None)
    not_met = study._reference_evaluation(with_tie, 3)
    assert not not_met.criteria_4_to_8_met and not_met.tie_count == 1
    assert not_met.joint_hits == 19 and all(value is None for value in not_met.mean_bias.values())
    m_by_library = dict(enumerate(counts, 1))
    references = {
        number: {
            "batches_1_2": replace(met, replicates=6),
            **{f"batch{batch}": met if batch <= count else not_met for batch in range(1, 5)},
        }
        for number, count in m_by_library.items()
    }
    report = study._summarize_references(campaign, references)
    assert report.k_prime == 3 and report.m == m and report.m_by_library == m_by_library
    assert report.libraries_not_met_with_a_batch_met == missed
    assert (report.s1, report.s2) == (not failed_panel, not failed_panel and m == 24)
    assert report.sentences == study.reference_sentences(campaign.reading_class, k_prime=3, m=m)
    assert len(report.sentences) == (0 if failed_panel else 1 + int(m == 24))


def test_void_omits_all_reference_counts_and_sentences(
    mocked_full_run: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unexpected(*args: Any, **kwargs: Any) -> None:
        pytest.fail("VOID evaluated or reported references")

    monkeypatch.setattr(
        study,
        "_truth_diagnostics_from_result",
        lambda *args, **kwargs: replace(_truth_diagnostics(), namespace_passed=False),
    )
    monkeypatch.setattr(study, "_reference_evaluation", unexpected)
    monkeypatch.setattr(study, "reference_sentences", unexpected)
    result = study.evaluate_after_blind(mocked_full_run.generation)
    assert result == study.VoidCampaign("shared panel P9")
    assert set(asdict(result)) == {"cause", "campaign_status"}


def _change_candidate_table_body(payload: dict[str, Any]) -> None:
    table = payload["table"]
    recorded = payload["table_sha256"]
    assert audit.table_sha256(table) == recorded
    count = table["symptomatic"][0]
    # Preserve the numerical input to the fitter while changing the hashed JSON.
    table["symptomatic"][0] = int(count) if type(count) is float else float(count)
    assert table["symptomatic"][0] == count
    assert payload["table_sha256"] == recorded != audit.table_sha256(table)


@pytest.mark.parametrize(
    "corruption", ["seed", "namespace", "replicate_order", "table_sha256", "table_body"]
)
def test_persisted_candidate_corruption_fails_library_p9_and_voids_campaign(
    mocked_full_run: Any, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    generation = mocked_full_run.generation
    directory = generation.directory / "library_1/candidate_tables/0"
    first, second = directory / "01.json", directory / "02.json"
    # U2 has no retained candidate files. Supply the corrupted evidence there to
    # demonstrate that its post-blind P9 ignores the records altogether.
    original = first.read_bytes() if first.exists() else None
    second_original = second.read_bytes() if second.exists() else None
    directory.mkdir(parents=True, exist_ok=True)
    payload = (
        json.loads(original)
        if original
        else {
            "process_seed": 87101,
            "returned_observation_config": {"observation_config_id": "v13-g43-fit"},
            "position": 1,
            "table_sha256": "1" * 64,
        }
    )
    if corruption == "seed":
        payload["process_seed"] = 87102
    elif corruption == "namespace":
        payload["returned_observation_config"]["observation_config_id"] = "v13-g43-target"
    elif corruption == "replicate_order":
        if original is not None and second_original is not None:
            second.write_bytes(original)
        payload = json.loads(second_original) if second_original else {**payload, "position": 2}
    elif corruption == "table_sha256":
        payload["table_sha256"] = "0" * 64
    else:
        _change_candidate_table_body(payload)
    first.write_text(json.dumps(payload), encoding="utf-8")

    integrity = []
    original_evaluate = study.evaluate_recovery

    def capture(*args: Any, **kwargs: Any) -> study.RecoveryEvaluation:
        evaluation = original_evaluate(*args, **kwargs)
        integrity.append(evaluation.library_integrity)
        return evaluation

    monkeypatch.setattr(study, "evaluate_recovery", capture)
    try:
        result = study.evaluate_after_blind(generation)
        assert integrity[0]["P9"] is False
        assert all(item["P9"] for item in integrity[1:])
        assert result == study.VoidCampaign("L1 P9")
    finally:
        if original is None:
            first.unlink()
        else:
            first.write_bytes(original)
        if second_original is not None and corruption == "replicate_order":
            second.write_bytes(second_original)


def _json(path: Path) -> Any:
    return json.loads(path.read_bytes())


_INCOMPLETE_TARGETS = ["latent_29", "latent_empty", "dates_33"]


def _incomplete_target_result(
    latent_rows: list[Any],
    observed_rows: list[Any],
    corruption: str,
) -> None:
    if corruption == "latent_29":
        assert len(latent_rows) == 30
        latent_rows.pop()
    elif corruption == "latent_empty":
        latent_rows.clear()
    else:
        assert corruption == "dates_33" and len(observed_rows) == 34
        observed_rows.pop()


@pytest.mark.parametrize("corruption", _INCOMPLETE_TARGETS)
def test_incomplete_returned_target_fails_shared_p1(
    mocked_full_run: Any, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    generation = mocked_full_run.generation
    target = generation.targets[86001]
    latent_rows = list(target.latent.daily_epidemic)
    observed_rows = list(target.observed.daily_observed_cases)
    _incomplete_target_result(latent_rows, observed_rows, corruption)
    monkeypatch.setattr(target.latent, "daily_epidemic", latent_rows)
    monkeypatch.setattr(target.observed, "daily_observed_cases", observed_rows)

    panels = []
    original = study.evaluate_shared_panel

    def capture(*args: Any, **kwargs: Any) -> study.SharedPanelEvaluation:
        panel = original(*args, **kwargs)
        panels.append(panel.predicates)
        return panel

    monkeypatch.setattr(study, "evaluate_shared_panel", capture)
    result = study.evaluate_after_blind(generation)
    [predicates] = panels
    assert predicates["P1"] is False
    assert result == study.VoidCampaign("shared panel P1")


def test_incomplete_target_fails_p1_via_execution_evidence(
    mocked_full_run: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    generation = mocked_full_run.generation
    target = generation.targets[86001]
    monkeypatch.setattr(target.latent, "daily_epidemic", target.latent.daily_epidemic[:-1])
    original = study.evaluate_shared_panel

    def evaluate_without_row_completion(
        diagnostics: dict[int, phase0.TruthDiagnostics], *, evidence: study.IntegrityEvidence
    ) -> study.SharedPanelEvaluation:
        assert diagnostics[86001].complete is False
        assert evidence.execution_complete is False
        return original(
            {seed: replace(row, complete=True) for seed, row in diagnostics.items()},
            evidence=evidence,
        )

    monkeypatch.setattr(study, "evaluate_shared_panel", evaluate_without_row_completion)
    assert study.evaluate_after_blind(generation) == study.VoidCampaign("shared panel P1")


_BUNDLE_UPPER = 1_000_000_000 + 1_048_576
_REQUIRED_FREE = 5_000_000_000 + _BUNDLE_UPPER


def _mock_host_disk(patch: pytest.MonkeyPatch, free: int) -> None:
    def disk_usage(path: Path) -> SimpleNamespace:
        assert path == Path("/mnt/c")
        return SimpleNamespace(free=free)

    patch.setattr(study.shutil, "disk_usage", disk_usage)


def _execute_cli_args(output: Path) -> list[str]:
    return [
        "execute",
        "--config",
        str(CONFIG),
        "--predeclaration",
        str(PREDECLARATION),
        "--owner-ruling",
        str(ROOT / "docs/research/v1_3/2026-11-20-g43-owner-ruling.md"),
        "--output-dir",
        str(output),
    ]


@pytest.mark.parametrize("override", [0, _BUNDLE_UPPER - 1, _BUNDLE_UPPER, _BUNDLE_UPPER + 1])
def test_launch_bundle_upper_estimate_has_frozen_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, override: int
) -> None:
    output = tmp_path / "bundle"
    _mock_host_disk(monkeypatch, _REQUIRED_FREE + 1)
    if override < _BUNDLE_UPPER:
        with pytest.raises(study.CampaignError, match=f"at least {_BUNDLE_UPPER} bytes"):
            study._launch_checks(output, ROOT, None, override)
    else:
        report = study._launch_checks(output, ROOT, None, override)
        assert report["upper_bytes_used"] == override
        assert report["required_free_bytes"] == _REQUIRED_FREE + override - _BUNDLE_UPPER
    assert not output.exists()


@pytest.mark.parametrize("case", ["missing_parent", "unwritable_parent", "inside_bundle"])
def test_execute_refuses_invalid_exit_marker_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    case: str,
) -> None:
    output = tmp_path / "bundle"
    parent = output if case == "inside_bundle" else tmp_path / "markers"
    marker = parent / "campaign.exit"
    expected = "exit marker parent must be an existing writable directory"
    if case == "inside_bundle":
        output.mkdir()
        expected = "exit marker must be outside the bundle directory"
    elif case == "unwritable_parent":
        if os.geteuid() == 0:
            pytest.skip("root can write to the chmod-restricted marker parent")
        parent.mkdir()
        parent.chmod(0o500)
    _mock_host_disk(monkeypatch, _REQUIRED_FREE)
    monkeypatch.setattr(
        study, "_execution_inputs", lambda *_: pytest.fail("launch reached execution inputs")
    )

    try:
        assert study.main([*_execute_cli_args(output), "--exit-marker", str(marker)]) == 1
        assert expected in capsys.readouterr().err
        assert not marker.exists()
        if case == "inside_bundle":
            assert not list(output.iterdir())
        else:
            assert not output.exists()
    finally:
        if case == "unwritable_parent":
            parent.chmod(0o700)


@pytest.mark.parametrize("error_type", [PermissionError, KeyboardInterrupt])
def test_exit_marker_failure_preserves_sealed_intact_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mocked_full_run: Any,
    error_type: type[BaseException],
) -> None:
    output = tmp_path / "bundle"
    marker = tmp_path / "markers" / "campaign.exit"
    marker.parent.mkdir()
    failure = error_type("injected marker failure")
    generation = mocked_full_run.generation
    monkeypatch.setattr(study, "_require_clean_worktree", lambda _: None)
    monkeypatch.setattr(study, "WorkLedger", lambda: deepcopy(generation.ledger))
    monkeypatch.setattr(
        study,
        "_generate_study",
        lambda config, directory, root, ledger: replace(
            generation, config=config, directory=directory, ledger=ledger
        ),
    )
    monkeypatch.setattr(study, "evaluate_after_blind", lambda _: mocked_full_run.output)
    _mock_host_disk(monkeypatch, _REQUIRED_FREE)
    manifests = []
    open_file = io.open

    def open_marker(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        # Path.open opens the marker itself on the base. NamedTemporaryFile opens in its parent.
        if mode not in ("xb", "wb") or Path(file) not in (marker, marker.parent):
            return open_file(file, mode, *args, **kwargs)
        manifests.append((output / "SHA256SUMS").read_bytes())
        if isinstance(failure, PermissionError):
            raise failure
        stream = open_file(file, mode, *args, **kwargs)
        write = stream.write

        def interrupt_after_write(content: bytes) -> None:
            write(content)
            stream.flush()
            raise failure

        stream.write = interrupt_after_write
        return stream

    monkeypatch.setattr(io, "open", open_marker)
    with pytest.raises(error_type) as caught:
        study.execute(CONFIG, PREDECLARATION, output, root=ROOT, exit_marker=marker)
    assert caught.value is failure
    assert not list(marker.parent.iterdir())
    study.verify_bundle(output)
    summary = _json(output / "campaign_summary.json")
    assert summary["software_status"] == "PASS"
    assert summary["scientific_status"] == {f"{number}": "PASS" for number in range(1, 7)}
    assert (output / "g43_across_library.json").is_file()
    assert (output / "g43_matrices.json").is_file()
    [manifest] = manifests
    assert (output / "SHA256SUMS").read_bytes() == manifest


@pytest.fixture
def mocked_marker_run(
    monkeypatch: pytest.MonkeyPatch, mocked_full_run: Any
) -> study.StudyEvaluation:
    generation = mocked_full_run.generation
    monkeypatch.setattr(study, "_require_clean_worktree", lambda _: None)
    monkeypatch.setattr(study, "WorkLedger", lambda: deepcopy(generation.ledger))
    monkeypatch.setattr(
        study,
        "_generate_study",
        lambda config, directory, root, ledger: replace(
            generation, config=config, directory=directory, ledger=ledger
        ),
    )
    _mock_host_disk(monkeypatch, _REQUIRED_FREE)
    return mocked_full_run.output


def test_exit_marker_created_during_intact_run_is_not_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mocked_marker_run: study.StudyEvaluation
) -> None:
    output = tmp_path / "bundle"
    marker = tmp_path / "markers" / "campaign.exit"
    marker.parent.mkdir()
    existing = b"existing exit marker\n"

    def evaluate(_: study.BlindGeneration) -> study.StudyEvaluation:
        assert not marker.exists()
        marker.write_bytes(existing)
        return mocked_marker_run

    monkeypatch.setattr(study, "evaluate_after_blind", evaluate)
    with pytest.raises(FileExistsError):
        study.execute(CONFIG, PREDECLARATION, output, root=ROOT, exit_marker=marker)
    assert marker.read_bytes() == existing
    assert list(marker.parent.iterdir()) == [marker]
    study.verify_bundle(output)
    summary = _json(output / "campaign_summary.json")
    assert summary["software_status"] == "PASS"
    assert summary["scientific_status"] == {f"{number}": "PASS" for number in range(1, 7)}
    assert (output / "g43_across_library.json").is_file()
    assert (output / "g43_matrices.json").is_file()


@pytest.mark.usefixtures("mocked_marker_run")
def test_exit_marker_link_failure_preserves_sealed_shared_panel_void_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "void"
    marker = tmp_path / "markers" / "campaign.exit"
    marker.parent.mkdir()
    summary_path = output / "campaign_summary.json"
    manifest_path = output / "SHA256SUMS"
    sealed = []
    failure = OSError("injected link failure")

    def fail_link(_source: str, destination: Path) -> None:
        assert destination == marker
        sealed.append((summary_path.read_bytes(), manifest_path.read_bytes()))
        raise failure

    monkeypatch.setattr(
        study, "evaluate_after_blind", lambda _: study.VoidCampaign("shared panel P1")
    )
    monkeypatch.setattr(study.os, "link", fail_link)
    with pytest.raises(OSError) as caught:
        study.execute(CONFIG, PREDECLARATION, output, root=ROOT, exit_marker=marker)
    assert caught.value is failure
    study.verify_bundle(output)
    summary = _json(summary_path)
    assert summary["software_status"] == "VOID"
    assert summary["cause"] == "shared panel P1"
    assert sealed == [(summary_path.read_bytes(), manifest_path.read_bytes())]
    assert not list(marker.parent.iterdir())


@pytest.fixture(scope="module")
def mocked_execute_bundle(
    tmp_path_factory: pytest.TempPathFactory, declared_process_hashes: dict[int, tuple[str, ...]]
) -> Any:
    output = tmp_path_factory.mktemp("g43-bundle") / "empty"
    output.mkdir()
    ledger = study.WorkLedger()
    evaluations = []
    original = study.evaluate_after_blind

    def evaluate(generation: study.BlindGeneration) -> study.StudyEvaluation | study.VoidCampaign:
        result = original(generation)
        evaluations.append(result)
        return result

    with pytest.MonkeyPatch.context() as patch:
        _mock_dispatches(patch, declared_process_hashes, ledger, on_truth=lambda _: None)
        patch.setattr(study, "_require_clean_worktree", lambda _: None)
        patch.setattr(study, "WorkLedger", lambda: ledger)
        patch.setattr(study, "evaluate_after_blind", evaluate)
        _mock_host_disk(patch, _REQUIRED_FREE + 11)
        assert (
            study.main(
                [*_execute_cli_args(output), "--bundle-upper-bytes", str(_BUNDLE_UPPER + 11)]
            )
            == 0
        )
    [evaluation] = evaluations
    assert isinstance(evaluation, study.StudyEvaluation)
    return SimpleNamespace(
        path=output, summary=_json(output / "campaign_summary.json"), output=evaluation
    )


def test_intact_execute_creates_exit_marker_and_refuses_sibling(
    mocked_execute_bundle: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    output = mocked_execute_bundle.path
    marker = output.parent / "jos-g43-campaign.exit"
    assert _json(marker) == {"output_dir": str(output), "software_status": "PASS"}
    assert stat.S_IMODE(marker.stat().st_mode) == 0o644
    sibling = output.with_name("second")
    sibling.mkdir()
    _mock_host_disk(monkeypatch, _REQUIRED_FREE)
    monkeypatch.setattr(
        study, "_generate_study", lambda *_, **__: pytest.fail("generation dispatched")
    )
    assert study.main(_execute_cli_args(sibling)) == 1
    assert "exit marker already exists" in capsys.readouterr().err
    assert not list(sibling.iterdir())


def test_execute_seals_exact_frozen_layout_and_single_source_disclosures(
    mocked_execute_bundle: Any, frozen_document: str
) -> None:
    run = mocked_execute_bundle
    directory = run.path
    study.verify_bundle(directory)
    expected_paths = {
        "SHA256SUMS",
        "campaign_summary.json",
        "seed_ledger.json",
        "g43_matrices.json",
        "g43_across_library.json",
        "frozen_inputs/2026-11-20-g43-predeclaration.md",
        "frozen_inputs/2026-11-20-g43-owner-ruling.md",
        "frozen_inputs/2026-11-21-g43-owner-clarification-1.md",
        "frozen_inputs/2026-11-20-g43-seed-precheck.json",
        "frozen_inputs/v13_g43_multilibrary.yaml",
        "frozen_inputs/sha256.json",
        "frozen_inputs/source_and_config_hashes.json",
        "targets/target_provenance.json",
        "targets/truth_diagnostics.json",
        "targets/auditor_recompute_notes.json",
        *(f"targets/{seed}.json" for seed in _TARGET_SEEDS),
        *(f"targets/latent_truth/{seed}.json" for seed in _TARGET_SEEDS),
    }
    for number in range(1, 7):
        library = f"library_{number}"
        expected_paths.update(
            f"{library}/{name}"
            for name in (
                f"g43_L{number}_recovery.csv",
                f"g43_L{number}_descriptives.json",
                "recovery_evaluation.json",
                "reference_evaluations.json",
                "blind_readback_hashes.json",
            )
        )
        expected_paths.update(
            f"{library}/candidate_tables/{cell}/{rep:02d}.json"
            for cell, rep in product(range(625), range(1, 13))
        )
        expected_paths.update(f"{library}/blind_estimates/{seed}.json" for seed in _TARGET_SEEDS)
        expected_paths.update(
            f"{library}/descriptive_estimates/{view}/{seed}.json"
            for view, seed in product(
                ("batch1", "batch2", "batch3", "batch4", "batches_1_2"), _TARGET_SEEDS
            )
        )
    paths = [directory, *directory.rglob("*")]
    assert all(not path.stat().st_mode & 0o222 for path in paths)
    files = [path for path in paths if path.is_file()]
    assert {path.relative_to(directory).as_posix() for path in files} == expected_paths

    inputs = _json(directory / "frozen_inputs/sha256.json")
    assert set(inputs) == {
        "2026-11-20-g43-predeclaration.md",
        "2026-11-20-g43-owner-ruling.md",
        "2026-11-21-g43-owner-clarification-1.md",
        "2026-11-20-g43-seed-precheck.json",
        "v13_g43_multilibrary.yaml",
    }
    for name, digest in inputs.items():
        tracked = (
            subprocess.check_output(["git", "ls-files", "--", f"**/{name}"], cwd=ROOT)
            .decode()
            .strip()
        )
        content = subprocess.check_output(["git", "show", f"HEAD:{tracked}"], cwd=ROOT)
        assert (directory / "frozen_inputs" / name).read_bytes() == content
        assert digest == hashlib.sha256(content).hexdigest()
    source = _json(directory / "frozen_inputs/source_and_config_hashes.json")
    tracked = (
        subprocess.check_output(
            ["git", "ls-files", "-z", "src/jersey_outbreak", "configs"], cwd=ROOT
        )
        .decode()
        .split("\0")
    )
    assert set(source["source_and_config_sha256"]) == {
        name for name in tracked if Path(name).suffix in (".py", ".yaml", ".json")
    }
    for name, digest in source["source_and_config_sha256"].items():
        assert (
            hashlib.sha256(
                subprocess.check_output(["git", "show", f"{source['git_head']}:{name}"], cwd=ROOT)
            ).hexdigest()
            == digest
        )
    assert run.summary["lineage"]["frozen_section_1"] == frozen_document[
        frozen_document.index("**Lineage block**") : frozen_document.index("## 2.")
    ].rstrip("\n")
    assert run.summary["lineage"]["reviewer"] == run.summary["seats"]["reviewer"]
    assert run.summary["seats"]["substitutions"] == "not applicable"
    assert (
        run.summary["exit_audit_pending"] is True
        and "exit audit pending" not in run.summary["status_phrase"]
    )

    expected_work = {"shared_panel": _SHARED, "totals": _TOTALS}
    for scope, expected in expected_work.items():
        assert run.summary["measured_work"][scope] == {
            "measured": expected,
            "planned": expected,
            "measured_equals_planned": True,
        }
    assert run.summary["measured_work"]["libraries"] == {
        f"L{i}": {"measured": _LIBRARY, "planned": _LIBRARY, "measured_equals_planned": True}
        for i in range(1, 7)
    }
    disclosures = run.summary["disclosures"]
    assert disclosures["disk"]["default_upper_bytes"] == _BUNDLE_UPPER
    assert disclosures["disk"]["upper_override_bytes"] == _BUNDLE_UPPER + 11
    assert disclosures["disk"]["required_free_bytes"] == _REQUIRED_FREE + 11
    assert disclosures["disk"]["bundle_size_bytes"] == sum(path.stat().st_size for path in files)
    for scope, count in [
        (disclosures["shared_panel"], 20),
        *((scope, 300) for scope in disclosures["libraries"].values()),
    ]:
        assert set(scope["wall_time_seconds"]) == {
            "build",
            "latent",
            "transform",
            "scoring",
            "retention",
        }
        assert all(seconds >= 0 for seconds in scope["wall_time_seconds"].values())
        assert [entry["runtime_seconds"] for entry in scope["latent_call_runtimes"]] == [
            0.125
        ] * count
    assert disclosures["shared_panel"]["population_fallbacks"]["fallback_built_count"] == 1
    assert disclosures["libraries"]["L1"]["population_fallbacks"]["fallback_built_count"] == 1
    for name in ("target_provenance.json", "latent_truth/86001.json"):
        assert "runtime_seconds" not in (directory / "targets" / name).read_text()
    for name in (
        "candidate_tables/0/01.json",
        "g43_L1_descriptives.json",
        "reference_evaluations.json",
    ):
        assert "wall_time_seconds" not in (directory / "library_1" / name).read_text()
    with (directory / "library_1/g43_L1_recovery.csv").open() as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 20
    assert (
        rows[4]["population_fallback_m2"] == "True" and rows[4]["population_fallback_m3"] == "False"
    )
    assert rows[4]["boundary_beta"] == "False" and rows[4]["predicate_P1"] == "True"


@pytest.mark.parametrize(
    "corruption",
    ["file_byte", "manifest_byte", "missing_file", "file_write_bit", "directory_write_bit"],
)
def test_verify_bundle_rejects_corruption_and_any_remaining_write_bit(
    mocked_execute_bundle: Any, corruption: str
) -> None:
    directory = mocked_execute_bundle.path
    path = directory / ("SHA256SUMS" if corruption == "manifest_byte" else "seed_ledger.json")
    root_mode, mode = directory.stat().st_mode, path.stat().st_mode
    original = path.read_bytes()
    moved = directory.parent / "temporarily-missing.json"
    try:
        if corruption == "missing_file":
            directory.chmod(root_mode | 0o200)
            path.rename(moved)
            directory.chmod(root_mode)
        elif corruption == "directory_write_bit":
            directory.chmod(root_mode | 0o020)
        else:
            path.chmod(mode | 0o200)
            if corruption in {"file_byte", "manifest_byte"}:
                path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
                path.chmod(mode)
        with pytest.raises(study.CampaignError, match="SHA256SUMS|write bits"):
            study.verify_bundle(directory)
    finally:
        if moved.exists():
            directory.chmod(root_mode | 0o200)
            moved.rename(path)
        path.chmod(mode | 0o200)
        path.write_bytes(original)
        path.chmod(mode)
        directory.chmod(root_mode)
    study.verify_bundle(directory)


def test_stdlib_recomputes_predicates_all_reference_evaluations_and_class(
    mocked_execute_bundle: Any,
) -> None:
    run = mocked_execute_bundle
    path = Path(audit.__file__)
    imports = [
        node
        for node in ast.walk(ast.parse(path.read_bytes()))
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    assert imports
    for node in imports:
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0 and node.module is not None
            assert node.module.split(".")[0] in sys.stdlib_module_names
        else:
            assert all(alias.name.split(".")[0] in sys.stdlib_module_names for alias in node.names)
    completed = subprocess.run(
        [sys.executable, "-I", str(path), str(run.path)], check=True, capture_output=True, text=True
    )
    result = json.loads(completed.stdout)
    evaluation = run.output
    across = result["across_library"]
    assert across["k"] == evaluation.campaign.k == 6
    assert across["k_prime"] == evaluation.campaign.k_prime == 6
    assert across["m"] == evaluation.references.m == 24
    assert across["m_by_library"] == {
        str(k): v for k, v in evaluation.references.m_by_library.items()
    }
    assert across["s1"] is evaluation.references.s1 is True
    assert across["s2"] is evaluation.references.s2 is True
    assert across["class"] == evaluation.campaign.reading_class == "CONSISTENT-PASS"
    assert result["reference_sentences"] == list(evaluation.references.sentences)
    assert across["reading"] == study.reading(evaluation.campaign)
    for number, library in enumerate(evaluation.campaign.libraries, 1):
        assert result["libraries"][str(number)]["predicates"] == library.predicates
        assert result["references"][str(number)] == {
            name: asdict(record) for name, record in evaluation.references.libraries[number].items()
        }


def _rewrite_readonly_bytes(path: Path, content: bytes) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | 0o200)
    try:
        path.write_bytes(content)
    finally:
        path.chmod(mode)


@contextmanager
def _replace_sealed_json(directory: Path, path: Path, payload: Any) -> Iterator[None]:
    original = path.read_bytes()
    content = study._compact_json_bytes(payload)
    manifest = directory / "SHA256SUMS"
    original_manifest = manifest.read_bytes()
    relative = path.relative_to(directory).as_posix()
    old = f"{hashlib.sha256(original).hexdigest()}  {relative}\n".encode()
    new = f"{hashlib.sha256(content).hexdigest()}  {relative}\n".encode()
    assert original_manifest.count(old) == 1
    try:
        _rewrite_readonly_bytes(path, content)
        _rewrite_readonly_bytes(manifest, original_manifest.replace(old, new))
        yield
    finally:
        _rewrite_readonly_bytes(path, original)
        _rewrite_readonly_bytes(manifest, original_manifest)


def _assert_recomputed_void(directory: Path, cause: str) -> None:
    completed = subprocess.run(
        [sys.executable, "-I", str(Path(audit.__file__)), str(directory)],
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)
    assert result["software_status"] == "VOID"
    assert result["cause"] == cause
    assert set(result) == {"software_status", "status_phrase", "cause"}


@pytest.mark.parametrize("corruption", _INCOMPLETE_TARGETS)
def test_stdlib_recomputation_fails_shared_p1_for_incomplete_target(
    mocked_execute_bundle: Any, corruption: str
) -> None:
    directory = mocked_execute_bundle.path
    path = directory / "targets/latent_truth/86001.json"
    raw = _json(path)
    _incomplete_target_result(
        raw["daily_epidemic"],
        raw["daily_observed_cases"],
        corruption,
    )
    with _replace_sealed_json(directory, path, raw):
        _assert_recomputed_void(directory, "shared panel P1")


def test_stdlib_recomputation_fails_library_p9_for_changed_table_body(
    mocked_execute_bundle: Any,
) -> None:
    directory = mocked_execute_bundle.path
    path = directory / "library_1/candidate_tables/0/01.json"
    payload = _json(path)
    _change_candidate_table_body(payload)
    with _replace_sealed_json(directory, path, payload):
        _assert_recomputed_void(directory, "L1 P9")


@pytest.mark.parametrize(
    "source,key,field,value",
    [
        (
            "transmission_events",
            "natural_history.chronology_passed",
            "infectious_start_date",
            "2025-01-07",
        ),
        ("daily_epidemic", "states.conserved", "susceptible", 2989),
        ("observation_events", "no_report_before_infection", "report_date", "2025-01-07"),
        ("daily_observed_cases", "latent_incidence_conservation", "latent_infections", 1),
    ],
)
def test_p3_recomputation_uses_raw_source_and_detects_one_corrupted_row(
    mocked_execute_bundle: Any,
    source: str,
    key: str,
    field: str,
    value: Any,
) -> None:
    targets = mocked_execute_bundle.path / "targets"
    raw = _json(targets / "latent_truth/86001.json")
    assert set(raw) == {
        "transmission_events",
        "daily_epidemic",
        "natural_history",
        "states",
        "observation_events",
        "daily_observed_cases",
        "benchmark",
        "observation_diagnostics",
    }
    assert raw["benchmark"]["n_agents"] == 3000
    assert len(raw["transmission_events"]) == len(raw["observation_events"]) == _MOCK_LATENT_COUNT
    assert len(raw["daily_epidemic"]) == 30 and len(raw["daily_observed_cases"]) == 34
    assert raw["transmission_events"][-1]["infected_uid"] == _MOCK_LATENT_COUNT - 1
    retained = _json(targets / "truth_diagnostics.json")["86001"]["conditions"]
    expected = {
        name: passed for name, passed in retained.items() if name in audit.recompute_p3(raw)
    }
    assert (
        audit.recompute_p3(raw)
        == expected
        == {
            "natural_history.chronology_passed": raw["natural_history"]["chronology_passed"],
            "states.conserved": raw["states"]["conserved"],
            "no_report_before_infection": raw["observation_diagnostics"][
                "no_report_before_infection"
            ],
            "latent_incidence_conservation": raw["observation_diagnostics"][
                "latent_incidence_conservation"
            ],
        }
    )
    assert all(expected.values())
    raw[source][0][field] = value
    assert audit.recompute_p3(raw) == {**expected, key: False}
    notes = _json(targets / "auditor_recompute_notes.json")["recomputable"]["P3"]
    assert source in notes[key]["raw_rows"]
    assert re.search(r"\.py:\d+", notes[key]["source"])


@pytest.mark.parametrize("precondition", ["nonempty", "exit_marker", "disk"])
def test_execute_refuses_failed_launch_preconditions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    precondition: str,
) -> None:
    output = tmp_path / "bundle"
    args = _execute_cli_args(output)
    if precondition == "nonempty":
        output.mkdir()
        (output / "existing").write_text("keep")
        expected = "output directory must be empty"
    elif precondition == "exit_marker":
        (tmp_path / "jos-g43-campaign.exit").touch()
        expected = "exit marker already exists"
    else:
        expected = f"below required {_REQUIRED_FREE} bytes"
    _mock_host_disk(monkeypatch, _REQUIRED_FREE - 1)
    monkeypatch.setattr(
        study, "_generate_study", lambda *_, **__: pytest.fail("generation dispatched")
    )
    assert study.main(args) == 1
    assert expected in capsys.readouterr().err
    assert (
        (output / "existing").read_text() == "keep"
        if precondition == "nonempty"
        else not output.exists()
    )
    if precondition != "exit_marker":
        assert not (tmp_path / "jos-g43-campaign.exit").exists()


def test_execute_seals_partial_void_and_recompute_omits_science(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    declared_process_hashes: dict[int, tuple[str, ...]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "void"
    marker = tmp_path / "custom.exit"
    ledger = study.WorkLedger()
    calls = _mock_dispatches(monkeypatch, declared_process_hashes, ledger, on_truth=lambda _: None)
    monkeypatch.setattr(study, "WorkLedger", lambda: ledger)
    monkeypatch.setattr(study, "_require_clean_worktree", lambda _: None)
    _mock_host_disk(monkeypatch, _REQUIRED_FREE)
    original = g35b.run_outbreak

    def failure(parent: Any, config: OutbreakRunConfig, parameters: Any) -> Any:
        if config.seed == 86002:
            raise RuntimeError("injected dispatch failure")
        return original(parent, config, parameters)

    monkeypatch.setattr(g35b, "run_outbreak", failure)
    assert study.main([*_execute_cli_args(output), "--exit-marker", str(marker)]) == 1
    captured = capsys.readouterr()
    assert captured.out.rstrip().endswith("; G43: VOID")
    assert captured.err == "RuntimeError: injected dispatch failure\n"
    study.verify_bundle(output)
    summary = _json(output / "campaign_summary.json")
    assert summary["software_status"] == "VOID"
    assert summary["measured_work"]["shared_panel"]["measured"]["latent_calls"] == 2
    assert not summary["measured_work"]["shared_panel"]["measured_equals_planned"]
    assert summary["disclosures"]["disk"]["upper_override_bytes"] is None
    assert calls["builds"] == {86001: 1, 86002: 1}
    assert (output / "targets/86001.json").is_file()
    assert not (output / "g43_across_library.json").exists()
    assert audit.recompute_bundle(output) == {
        "software_status": "VOID",
        "status_phrase": summary["status_phrase"],
        "cause": "RuntimeError: injected dispatch failure",
    }
    assert not {"scientific_status", "class", "reading", "reference_sentences"} & summary.keys()
    assert _json(marker) == {"output_dir": str(output), "software_status": "VOID"}
    assert stat.S_IMODE(marker.stat().st_mode) == 0o644
    sibling = output.with_name("second")
    sibling.mkdir()
    assert study.main([*_execute_cli_args(sibling), "--exit-marker", str(marker)]) == 1
    assert "exit marker already exists" in capsys.readouterr().err
    assert not list(sibling.iterdir())


@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
def test_execute_seals_void_before_propagating_base_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    declared_process_hashes: dict[int, tuple[str, ...]],
    exception_type: type[BaseException],
) -> None:
    output = tmp_path / "interrupted"
    ledger = study.WorkLedger()
    calls = _mock_dispatches(monkeypatch, declared_process_hashes, ledger, on_truth=lambda _: None)
    monkeypatch.setattr(study, "WorkLedger", lambda: ledger)
    monkeypatch.setattr(study, "_require_clean_worktree", lambda _: None)
    _mock_host_disk(monkeypatch, _REQUIRED_FREE)
    original = g35b.run_outbreak
    failure = exception_type("injected termination")

    def interrupt(parent: Any, config: OutbreakRunConfig, parameters: Any) -> Any:
        if config.seed == 86002:
            raise failure
        return original(parent, config, parameters)

    monkeypatch.setattr(g35b, "run_outbreak", interrupt)
    with pytest.raises(exception_type) as caught:
        study.main(_execute_cli_args(output))
    assert caught.value is failure
    study.verify_bundle(output)
    assert calls["builds"] == {86001: 1, 86002: 1}
    assert (output / "targets/86001.json").is_file()
    summary = _json(output / "campaign_summary.json")
    assert summary["software_status"] == "VOID"
    assert summary["cause"] == f"{exception_type.__name__}: injected termination"
    assert not {"scientific_status", "class", "reading", "reference_sentences"} & summary.keys()
    assert not (output / "g43_across_library.json").exists()
    assert not (output / "g43_matrices.json").exists()
    assert _json(tmp_path / "jos-g43-campaign.exit") == {
        "output_dir": str(output),
        "software_status": "VOID",
    }


def test_first_void_finish_failure_preserves_original_error_and_rejects_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "failed-seal"
    failure = RuntimeError("injected generation error")

    def fail_generation(*args: Any) -> None:
        raise failure

    def fail_summary(directory: Path, summary: dict[str, Any]) -> None:
        assert directory == output and summary["software_status"] == "VOID"
        raise OSError("injected VOID finish error")

    monkeypatch.setattr(study, "_generate_study", fail_generation)
    monkeypatch.setattr(study, "_write_summary", fail_summary)
    monkeypatch.setattr(study, "_require_clean_worktree", lambda _: None)
    _mock_host_disk(monkeypatch, _REQUIRED_FREE)
    with pytest.raises(RuntimeError) as caught:
        study.execute(CONFIG, PREDECLARATION, output, root=ROOT)
    assert caught.value is failure
    with pytest.raises(study.CampaignError, match="SHA256SUMS|write bits"):
        study.verify_bundle(output)
    assert _json(tmp_path / "jos-g43-campaign.exit") == {
        "output_dir": str(output),
        "software_status": "VOID",
    }
