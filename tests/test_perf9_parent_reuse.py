"""PERF-9 verified M2/M3 reuse contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jersey_outbreak import parent_build
from jersey_outbreak.ensemble import run_ensemble
from jersey_outbreak.parent_build import build_parent

ROOT = Path(__file__).resolve().parents[1]


def _cold_parent(output: Path):
    return build_parent(ROOT, "ci", 123, output, write_m4=True)


def test_verified_parent_reuse_skips_generators_and_preserves_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cold = _cold_parent(tmp_path / "cold")
    calls: list[str] = []

    def unexpected_population(*args: object, **kwargs: object) -> object:
        calls.append("m2")
        raise AssertionError("verified reuse unexpectedly regenerated M2")

    def unexpected_structure(*args: object, **kwargs: object) -> object:
        calls.append("m3")
        raise AssertionError("verified reuse unexpectedly regenerated M3")

    monkeypatch.setattr(parent_build, "generate_population", unexpected_population)
    monkeypatch.setattr(parent_build, "generate_structure", unexpected_structure)
    reused = build_parent(
        ROOT,
        "ci",
        123,
        tmp_path / "reused",
        write_m4=True,
        reuse_from=tmp_path / "cold",
    )

    assert calls == []
    assert reused.generated.m2_input.manifest.logical_content_hash == (
        cold.generated.m2_input.manifest.logical_content_hash
    )
    assert reused.generated.m3_input.manifest.logical_content_hash == (
        cold.generated.m3_input.manifest.logical_content_hash
    )
    assert reused.generated.logical_content_hash == cold.generated.logical_content_hash
    assert reused.generated.diagnostics["provenance"] == cold.generated.diagnostics["provenance"]
    assert reused.m4_artifact is not None
    assert cold.m4_artifact is not None
    assert reused.m4_artifact.manifest.logical_content_hash == (
        cold.m4_artifact.manifest.logical_content_hash
    )


@pytest.mark.parametrize(
    "tamper",
    ["m2_table", "m3_table", "m2_logical_manifest", "m3_logical_manifest", "config_manifest"],
)
def test_tampered_parent_is_rejected_and_cold_built(
    tmp_path: Path, tamper: str, capsys: pytest.CaptureFixture[str]
) -> None:
    cold = _cold_parent(tmp_path / "cold")
    m2_directory = cold.generated.m2_input.artifact_directory
    m3_directory = cold.generated.m3_input.artifact_directory
    if tamper == "m2_table":
        path = m2_directory / "residents.parquet"
        payload = bytearray(path.read_bytes())
        payload[-1] ^= 1
        path.write_bytes(payload)
    elif tamper == "m3_table":
        path = m3_directory / "resident_structure.parquet"
        payload = bytearray(path.read_bytes())
        payload[-1] ^= 1
        path.write_bytes(payload)
    else:
        manifest_path = (
            m3_directory / "manifest.json"
            if tamper == "m3_logical_manifest"
            else m2_directory / "manifest.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["logical_content_hash" if "logical_manifest" in tamper else "config_hash"] = (
            "0" * 64
        )
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    rebuilt = build_parent(
        ROOT,
        "ci",
        123,
        tmp_path / "rebuilt",
        write_m4=False,
        reuse_from=tmp_path / "cold",
    )

    assert rebuilt.generated.m2_input.artifact_directory != m2_directory
    assert "PARENT REUSE: REJECTED" in capsys.readouterr().err


def test_mismatched_seed_rejects_reuse_and_builds_requested_parent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _cold_parent(tmp_path / "cold")

    rebuilt = build_parent(ROOT, "ci", 124, tmp_path / "rebuilt", reuse_from=tmp_path / "cold")

    assert rebuilt.generated.m2_input.manifest.seed == 124
    assert rebuilt.generated.m3_input.manifest.seed == 124
    assert "no exact M2/M3 manifest pair" in capsys.readouterr().err


def test_initializer_parallel_replicates_match_sequential(
    m6_network,
    m6_parameters,
    m6_base_config,
    m6_observation_config,
    tmp_path: Path,
) -> None:
    seeds = (123, 124, 125, 126)
    base_config = m6_base_config.model_copy(update={"duration_days": 7})
    sequential = run_ensemble(
        tmp_path / "sequential",
        m6_network,
        m6_parameters,
        base_config,
        m6_observation_config,
        seeds,
        ensemble_id="perf9-equality",
        workers=1,
    )
    parallel = run_ensemble(
        tmp_path / "parallel",
        m6_network,
        m6_parameters,
        base_config,
        m6_observation_config,
        seeds,
        ensemble_id="perf9-equality",
        workers=2,
        allow_unsafe_workers=True,
    )

    assert sequential.logical_content_hash == parallel.logical_content_hash
    assert sequential.replicate_trajectories == parallel.replicate_trajectories
    for sequential_record, parallel_record in zip(
        sequential.replicate_records, parallel.replicate_records, strict=True
    ):
        assert sequential_record.seed == parallel_record.seed
        assert sequential_record.status == parallel_record.status
        assert sequential_record.latent_run_logical_content_hash == (
            parallel_record.latent_run_logical_content_hash
        )
        assert sequential_record.observation_logical_content_hash == (
            parallel_record.observation_logical_content_hash
        )
        assert sequential_record.m4_logical_content_hash == parallel_record.m4_logical_content_hash
    assert parallel.diagnostics["execution_mode"] == "process_pool_spawn"
    assert parallel.diagnostics["actual_workers"] == 2
    assert (
        parallel.diagnostics["job_payload_bytes_after"]
        < (parallel.diagnostics["job_payload_bytes_before"])
    )
