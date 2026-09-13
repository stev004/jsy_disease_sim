from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

import jersey_outbreak.bundle_selftest as bundle_selftest_module
import jersey_outbreak.outbreak_runner as outbreak_runner_module
from jersey_outbreak.bundle_selftest import IdentityRecord
from jersey_outbreak.intervention_artifacts import write_intervention_artifact
from jersey_outbreak.intervention_schemas import ScenarioConfig
from jersey_outbreak.network_schemas import NetworkGenerationConfig
from jersey_outbreak.outbreak_runner import default_run_config, run_outbreak
from jersey_outbreak.scientific_verification import verify_scientific_artifact
from jersey_outbreak.travel import run_travel_outbreak
from jersey_outbreak.travel_artifacts import write_travel_artifact
from jersey_outbreak.travel_schemas import TravelConfig
from jersey_outbreak.verification_archive import (
    verify_verification_archive,
    write_verification_archive,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def v121_m7_bundle(tmp_path: Path, m6_network, m6_parameters, m6_base_config) -> tuple[Path, Path]:
    bundle = tmp_path / "bundle"
    artifact_root = bundle / "artifacts"
    config = m6_base_config.model_copy(update={"duration_days": 2})
    scenario = ScenarioConfig(
        scenario_id="v121-bundle-selftest",
        start_date=config.start_date,
        duration_days=config.duration_days,
    )
    result = run_outbreak(m6_network, config, m6_parameters, scenario=scenario)
    template = write_intervention_artifact(result, ROOT, artifact_root)
    return bundle, template.artifact_directory


def _travel_config() -> TravelConfig:
    return TravelConfig.model_validate(
        {
            "mode": "explicit_travel",
            "daily_arrivals": {"2025-01-06:AIRPORT": 1},
            "visitor_fraction": 1.0,
            "returning_resident_fraction": 0.0,
            "day_visitor_fraction": 0.0,
            "staying_with_resident_fraction": 0.5,
            "party_sizes": [1],
            "party_probabilities": [1.0],
            "stay_duration_days": 1,
            "stay_duration_jitter_days": 0,
        }
    )


def test_school_route_horizon_is_validated_at_config_time() -> None:
    with pytest.raises(ValueError) as error:
        NetworkGenerationConfig(
            mode="ci",
            seed=123,
            start_date=date(2025, 7, 6),
            duration_days=180,
        )
    assert "school route date range 2025-07-06 to 2026-01-01" in str(error.value)
    assert "is outside school calendar year 2025" in str(error.value)

    inside = NetworkGenerationConfig(
        mode="ci",
        seed=123,
        start_date=date(2025, 7, 5),
        duration_days=1,
    )
    assert inside.duration_days == 1


def test_run_outbreak_rejects_school_horizon_before_starsim(
    m6_network, m6_parameters, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = default_run_config("ci", 123, m6_parameters).model_copy(
        update={"start_date": date(2025, 7, 6), "duration_days": 180}
    )
    sim_calls = 0

    def fail_if_constructed(*args: object, **kwargs: object) -> None:
        nonlocal sim_calls
        sim_calls += 1
        raise AssertionError("Starsim must not be constructed for an invalid school horizon")

    monkeypatch.setattr(outbreak_runner_module, "build_starsim_disease_sim", fail_if_constructed)
    with pytest.raises(ValueError, match="school route date range 2025-07-06 to 2026-01-01"):
        run_outbreak(m6_network, config, m6_parameters)
    assert sim_calls == 0


def test_m8_scientific_verifier_binds_artifact_id(
    tmp_path: Path, m6_network, m6_base_config, m6_parameters
) -> None:
    result = run_travel_outbreak(
        m6_network,
        m6_base_config.model_copy(update={"duration_days": 2}),
        m6_parameters,
        _travel_config(),
    )
    artifact = write_travel_artifact(result, ROOT, tmp_path / "artifacts")
    assert verify_scientific_artifact(artifact.artifact_directory).artifact_id == (
        artifact.manifest.artifact_id
    )
    manifest_path = artifact.artifact_directory / "manifest.json"
    payload = json.loads(manifest_path.read_text())
    payload["artifact_id"] = "altered-m8-artifact-id"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match="M8 artifact ID does not bind"):
        verify_scientific_artifact(artifact.artifact_directory)


def test_m7_diagnostics_status_is_derived(
    tmp_path: Path, m6_network, m6_base_config, m6_parameters
) -> None:
    config = m6_base_config.model_copy(update={"duration_days": 1})
    scenario = ScenarioConfig(
        scenario_id="v121-status",
        start_date=config.start_date,
        duration_days=config.duration_days,
    )
    result = run_outbreak(m6_network, config, m6_parameters, scenario=scenario)
    result.diagnostics["status"] = "failed"
    artifact = write_intervention_artifact(result, ROOT, tmp_path / "m7")
    assert artifact.manifest.diagnostics_status == "failed"


def test_verification_archive_status_is_derived(tmp_path: Path) -> None:
    archive = write_verification_archive(
        ROOT,
        tmp_path,
        verification_id="v121-failed-archive",
        parent_hashes={"m4": "a" * 64},
        layer_hashes={"m2": "b" * 64},
        command_results={"pytest": "failed"},
        require_clean=False,
    )
    assert archive.manifest.status == "failed"
    assert verify_verification_archive(archive.archive_directory / "manifest.json")["status"] == (
        "failed"
    )


def test_bundle_selftest_logical_hash_ignores_volatile_fields(
    v121_m7_bundle: tuple[Path, Path],
) -> None:
    bundle, artifact = v121_m7_bundle
    from typer.testing import CliRunner

    from jersey_outbreak.cli import app

    runner = CliRunner()
    first = runner.invoke(app, ["verify", "bundle-selftest", str(artifact)])
    second = runner.invoke(app, ["verify", "bundle-selftest", str(artifact)])
    assert first.exit_code == second.exit_code == 0
    transcripts = sorted((bundle / "verification").glob("relocation-selftest-*.json"))
    assert len(transcripts) == 2
    first_payload = json.loads(transcripts[0].read_text())
    second_payload = json.loads(transcripts[1].read_text())
    assert first_payload["logical_content_hash"] == second_payload["logical_content_hash"]


def test_bundle_selftest_reports_mutated_copy_hash_dictionary(
    v121_m7_bundle: tuple[Path, Path], monkeypatch
) -> None:
    bundle, artifact = v121_m7_bundle
    original = bundle_selftest_module._identity
    calls = 0

    def mutate_copy(verified, artifact_directory, elapsed):
        nonlocal calls
        identity = original(verified, artifact_directory, elapsed)
        if calls == 0:
            hashes = dict(identity.hashes)
            hashes["logical_content_hash"] = "0" * 64
            identity = IdentityRecord(
                artifact_type=identity.artifact_type,
                artifact_id=identity.artifact_id,
                hashes=hashes,
                wall_time_seconds=identity.wall_time_seconds,
            )
        calls += 1
        return identity

    monkeypatch.setattr(bundle_selftest_module, "_identity", mutate_copy)
    from typer.testing import CliRunner

    from jersey_outbreak.cli import app

    result = CliRunner().invoke(app, ["verify", "bundle-selftest", str(artifact)])
    assert result.exit_code == 1, result.output
    transcripts = sorted((bundle / "verification").glob("relocation-selftest-*.json"))
    payload = json.loads(transcripts[-1].read_text())
    assert payload["status"] == "failed"
    assert payload["identities"]["agreement"]["hashes"] is False
