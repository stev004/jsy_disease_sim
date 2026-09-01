from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from jersey_outbreak.cli import app
from jersey_outbreak.intervention_artifacts import write_intervention_artifact
from jersey_outbreak.intervention_schemas import ScenarioConfig
from jersey_outbreak.outbreak_runner import run_outbreak
from jersey_outbreak.scientific_verification import verify_scientific_artifact

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def m7_bundle_template(
    tmp_path_factory: pytest.TempPathFactory, m6_network, m6_parameters, m6_base_config
) -> tuple[Path, Path]:
    bundle = tmp_path_factory.mktemp("bundle-selftest") / "bundle"
    artifact_root = bundle / "artifacts"
    config = m6_base_config.model_copy(update={"duration_days": 2})
    scenario = ScenarioConfig(
        scenario_id="v12-bundle-selftest",
        start_date=config.start_date,
        duration_days=config.duration_days,
    )
    result = run_outbreak(m6_network, config, m6_parameters, scenario=scenario)
    artifact = write_intervention_artifact(result, ROOT, artifact_root)
    return bundle, artifact.artifact_directory


@pytest.fixture
def m7_bundle(m7_bundle_template: tuple[Path, Path], tmp_path: Path) -> tuple[Path, Path]:
    _, template_artifact = m7_bundle_template
    bundle = tmp_path / "bundle"
    artifact_root = bundle / "artifacts"
    artifact_root.mkdir(parents=True)
    artifact = artifact_root / template_artifact.name
    shutil.copytree(template_artifact, artifact)
    return bundle, artifact


def _transcript(bundle: Path) -> tuple[Path, dict[str, object]]:
    paths = sorted((bundle / "verification").glob("relocation-selftest-*.json"))
    assert len(paths) == 1
    return paths[0], json.loads(paths[0].read_text(encoding="utf-8"))


def test_bundle_selftest_writes_passed_transcript_and_removes_copy(
    m7_bundle: tuple[Path, Path],
) -> None:
    bundle, artifact = m7_bundle
    result = CliRunner().invoke(app, ["verify", "bundle-selftest", str(artifact)])
    assert result.exit_code == 0, result.output

    transcript_path, transcript = _transcript(bundle)
    assert transcript["status"] == "passed"
    steps = transcript["steps"]
    assert isinstance(steps, list)
    assert len(steps) >= 4
    assert all(step["status"] == "passed" for step in steps)
    manifest = json.loads((artifact / "manifest.json").read_text(encoding="utf-8"))
    identities = transcript["identities"]
    assert identities["artifact_id"] == manifest["artifact_id"]
    assert identities["copy"]["hashes"]["artifact_bundle_hash"] == manifest["artifact_bundle_hash"]
    assert transcript_path.is_file()
    assert not Path(transcript["copied_to"]).exists()
    assert result.output.rstrip().endswith(f"BUNDLE_SELFTEST passed {transcript_path}")


def test_bundle_selftest_does_not_change_artifact(m7_bundle: tuple[Path, Path]) -> None:
    _, artifact = m7_bundle
    before_files = sorted(
        path.relative_to(artifact) for path in artifact.rglob("*") if path.is_file()
    )
    before_manifest = (artifact / "manifest.json").read_bytes()

    result = CliRunner().invoke(app, ["verify", "bundle-selftest", str(artifact)])
    assert result.exit_code == 0, result.output

    assert before_files == sorted(
        path.relative_to(artifact) for path in artifact.rglob("*") if path.is_file()
    )
    assert before_manifest == (artifact / "manifest.json").read_bytes()
    assert (
        verify_scientific_artifact(artifact).artifact_id
        == json.loads(before_manifest)["artifact_id"]
    )


def test_bundle_selftest_records_tampered_copy_failure(
    m7_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    _, artifact = m7_bundle
    bundle = tmp_path / "tampered-bundle"
    tampered = bundle / "artifacts" / artifact.name
    tampered.parent.mkdir(parents=True)
    shutil.copytree(artifact, tampered)
    data_path = tampered / "daily_intervention_state.parquet"
    data = bytearray(data_path.read_bytes())
    data[0] ^= 1
    data_path.write_bytes(data)

    result = CliRunner().invoke(app, ["verify", "bundle-selftest", str(tampered)])
    assert result.exit_code == 1, result.output

    _, transcript = _transcript(bundle)
    assert transcript["status"] == "failed"
    failed_steps = [step for step in transcript["steps"] if step["status"] == "failed"]
    assert failed_steps
    assert any("hash mismatch" in step["detail"] for step in failed_steps)


def test_bundle_selftest_requires_safe_transcript_location(
    m7_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    _, artifact = m7_bundle
    standalone = tmp_path / "standalone" / artifact.name
    standalone.parent.mkdir(parents=True)
    shutil.copytree(artifact, standalone)

    missing_option = CliRunner().invoke(app, ["verify", "bundle-selftest", str(standalone)])
    assert missing_option.exit_code == 2
    missing_error = missing_option.output + missing_option.stderr
    assert "--transcript-dir" in missing_error

    inside = CliRunner().invoke(
        app,
        [
            "verify",
            "bundle-selftest",
            str(artifact),
            "--transcript-dir",
            str(artifact / "verification"),
        ],
    )
    assert inside.exit_code == 2
    location_error = inside.output + inside.stderr
    assert "inside the artifact directory" in location_error
