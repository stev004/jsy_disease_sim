from __future__ import annotations

import hashlib
import json
import re
import subprocess
from copy import deepcopy
from dataclasses import asdict, replace
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import pytest
import yaml

from jersey_outbreak import g43_constants as frozen
from jersey_outbreak import g43_multilibrary as study
from jersey_outbreak import phase0_campaign as phase0

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
