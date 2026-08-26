import json

from typer.testing import CliRunner

from jersey_outbreak.cli import app


def test_demo_cli_writes_machine_readable_summary_and_manifest(tmp_path) -> None:
    result = CliRunner().invoke(app, ["demo", "--seed", "123", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0, result.stdout
    summary = json.loads(result.stdout)
    run_directory = tmp_path / "demo_seed_123"
    summary_path = run_directory / "summary.json"
    manifest_path = run_directory / "run_manifest.json"
    assert summary_path.exists()
    assert manifest_path.exists()
    assert json.loads(summary_path.read_text()) == summary
    manifest = json.loads(manifest_path.read_text())
    assert manifest["starsim_version"] == "3.5.2"
    assert manifest["summary_sha256"]
    assert manifest["declared_deterministic_outputs"] == [
        "summary.seed",
        "summary.starsim_version",
        "summary.time_series",
        "summary.final",
    ]


def test_data_build_cli_writes_quality_report(tmp_path) -> None:
    result = CliRunner().invoke(app, ["data", "build", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0, result.stdout
    assert (tmp_path / "quality_report.json").exists()
    assert (tmp_path / "quality_report.md").exists()
