"""Regression tests for shared provenance and M6 metric normalisation."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from jersey_outbreak import cli, ensemble
from jersey_outbreak.ensemble import METRIC_SEMANTICS, METRIC_TYPES
from jersey_outbreak.provenance import _git_metadata
from jersey_outbreak.scientific_hashes import (
    m6_comparison_logical_hash,
    m6_ensemble_logical_hash,
    normalize_m6_metric_value,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PROVENANCE_HELPER = SRC / "jersey_outbreak" / "provenance.py"


def test_git_provenance_has_one_definition_and_no_copies() -> None:
    definition_pattern = re.compile(
        r"^def _git_(?:metadata|identity|commit_identity)\(root: Path\)", re.MULTILINE
    )
    definitions = [
        path
        for path in SRC.rglob("*.py")
        if definition_pattern.search(path.read_text(encoding="utf-8"))
    ]
    assert definitions == [PROVENANCE_HELPER]
    for path in SRC.rglob("*.py"):
        if path == PROVENANCE_HELPER:
            continue
        assert '["git", "rev-parse", "HEAD"]' not in path.read_text(encoding="utf-8")


def test_git_provenance_fails_closed_outside_a_repository(tmp_path: Path) -> None:
    assert _git_metadata(tmp_path) == (None, True)


def test_ensemble_code_identity_uses_source_hash_outside_git(tmp_path: Path) -> None:
    ensemble_source = Path(ensemble.__file__)
    expected_source_identity = "source:" + hashlib.sha256(ensemble_source.read_bytes()).hexdigest()
    assert ensemble._code_identity(tmp_path) == expected_source_identity


def test_ensemble_code_identity_uses_commit_inside_repo() -> None:
    expected_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    assert ensemble._code_identity(ROOT) == expected_commit


def test_cli_root_is_resolved_from_package_location(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    assert cli._repo_root() == ROOT


def test_cli_command_from_outside_checkout_records_checkout_provenance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        cli.app,
        [
            "population",
            "generate",
            "--mode",
            "ci",
            "--seed",
            "123",
            "--output-dir",
            str(tmp_path / "population"),
        ],
    )
    assert result.exit_code == 0, result.output
    summary = json.loads(result.stdout)
    manifest = json.loads(
        (Path(summary["artifact_directory"]) / "manifest.json").read_text(encoding="utf-8")
    )
    expected_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    assert manifest["git_commit"] == expected_commit


def test_m6_metric_registries_have_identical_keys() -> None:
    assert set(METRIC_SEMANTICS) == set(METRIC_TYPES)


def test_m6_metric_normalizer_rejects_unregistered_metrics() -> None:
    with pytest.raises(ValueError, match="missing type registration"):
        normalize_m6_metric_value("unregistered_metric", 1)
    with pytest.raises(ValueError, match="missing type registration"):
        m6_ensemble_logical_hash(
            config={},
            replicate_records=[],
            summary=[],
            trajectories={1: [{"metric": "unregistered_metric", "value": 1.5}]},
            replicate_grid=[],
        )
    with pytest.raises(ValueError, match="missing type registration"):
        m6_comparison_logical_hash(
            comparison_id="comparison",
            config_a_hash="a",
            config_b_hash="b",
            rows=[{"metric": "unregistered_metric", "value_a": 1.5, "value_b": 2.5}],
        )


def test_m6_float_metric_is_not_truncated() -> None:
    assert normalize_m6_metric_value("latent_prevalence", 1.75) == 1.75


def test_m6_comparison_hash_preserves_base_canonicalization() -> None:
    rows = [
        {
            "seed": 17,
            "scope": "intervention",
            "key": "school",
            "metric": "intervention_route_active",
            "date": "2025-01-01",
            "status": "paired",
            "value_a": True,
            "value_b": False,
            "difference": -1,
        },
        {
            "seed": 17,
            "scope": "population",
            "key": "all",
            "metric": "latent_prevalence",
            "date": "2025-01-01",
            "status": "paired",
            "value_a": 0.25,
            "value_b": 0.5,
            "difference": 0.25,
        },
        {
            "seed": 17,
            "scope": "population",
            "key": "all",
            "metric": "latent_new_infections",
            "date": "2025-01-01",
            "status": "paired",
            "value_a": 4,
            "value_b": 7,
            "difference": 3,
        },
        {
            "seed": 18,
            "scope": "pair",
            "key": "seed",
            "metric": "pair_status",
            "date": None,
            "status": "missing_or_failed",
            "value_a": None,
            "value_b": None,
            "difference": None,
        },
    ]
    assert (
        m6_comparison_logical_hash(
            comparison_id="fixture-comparison",
            config_a_hash="config-a",
            config_b_hash="config-b",
            rows=rows,
            summary=[],
        )
        == "9579e685afb804dea42ecba2df4bd7ec0bd1c2507810fdf79745573e55aa56f2"
    )
