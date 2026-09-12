"""PERF-10 regression coverage for completed-grid construction reuse."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from jersey_outbreak import cli as cli_module
from jersey_outbreak import ensemble as ensemble_module


def test_cli_ensemble_builds_completed_grid_once(
    monkeypatch,
    m6_network,
    m6_parameters,
    m6_observation_config,
    tmp_path: Path,
) -> None:
    original = ensemble_module._completed_grid_rows
    calls = 0

    def counting_grid(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(ensemble_module, "_completed_grid_rows", counting_grid)
    monkeypatch.setattr(cli_module, "_build_m4_for_m6", lambda *args, **kwargs: m6_network)
    monkeypatch.setattr(cli_module, "load_parameter_set", lambda *args, **kwargs: m6_parameters)
    monkeypatch.setattr(
        cli_module,
        "load_observation_config",
        lambda *args, **kwargs: m6_observation_config,
    )

    result = CliRunner().invoke(
        cli_module.app,
        [
            "ensemble",
            "run",
            "--mode",
            "ci",
            "--seeds",
            "101,102,103",
            "--duration-days",
            "7",
            "--workers",
            "1",
            "--ensemble-id",
            "perf10-grid-once",
            "--output-dir",
            str(tmp_path / "artifacts"),
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == 1
