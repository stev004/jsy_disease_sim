from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from jersey_outbreak.contracts import (
    ArtifactRecord,
    DiseaseParameterProvenance,
    ProjectConfig,
    RunConfig,
    RunManifest,
    SourceRecord,
)


def test_run_config_is_versioned_and_rejects_unknown_fields() -> None:
    assert ProjectConfig().validation_level == "compatibility_spike"
    config = RunConfig(
        run={
            "label": "test",
            "start": 2000.0,
            "stop": 2001.0,
            "dt": 1.0,
            "unit": "year",
            "seed": 123,
        },
        population={"artifact_id": "demo", "mode": "demo"},
        disease={"module": "starsim_sir_demo", "parameter_set": "demo-v0.1"},
    )
    assert config.schema_version == "1.0"
    with pytest.raises(ValidationError):
        RunConfig(
            run={
                "label": "test",
                "start": 2000.0,
                "stop": 2001.0,
                "dt": 1.0,
                "unit": "year",
                "seed": 123,
                "unexpected": True,
            },
            population={"artifact_id": "demo", "mode": "demo"},
            disease={"module": "starsim_sir_demo", "parameter_set": "demo-v0.1"},
        )


def test_strict_models_do_not_coerce_strings_to_numbers() -> None:
    with pytest.raises(ValidationError):
        RunConfig(
            run={
                "label": "test",
                "start": "2000.0",
                "stop": 2001.0,
                "dt": 1.0,
                "unit": "year",
                "seed": 123,
            },
            population={"artifact_id": "demo", "mode": "demo"},
            disease={"module": "starsim_sir_demo", "parameter_set": "demo-v0.1"},
        )


def test_source_and_parameter_provenance_contracts() -> None:
    source = SourceRecord(
        source_id="demo-source",
        title="Demo source",
        publisher="JOS",
        url="https://example.com/source",
        retrieved_at=date(2026, 8, 25),
        reference_period="demo",
        license="placeholder",
        status="fixture",
        sha256="a" * 64,
    )
    parameter = DiseaseParameterProvenance(
        distribution="fixed",
        mean=0.8,
        sigma=0.0,
        status="scenario_assumption",
        source_ids=[source.source_id],
        valid_range=(0.0, 1.0),
        notes="Demo only",
    )
    assert source.status == "fixture"
    assert parameter.mean == 0.8
    with pytest.raises(ValidationError):
        SourceRecord(
            source_id="bad",
            title="Bad",
            publisher="JOS",
            url="not-a-url",
            retrieved_at=date(2026, 8, 25),
            reference_period="demo",
            license="placeholder",
            status="fixture",
        )


def test_run_manifest_requires_hashes_and_timezone() -> None:
    kwargs = dict(
        run_id="jos-demo-test",
        created_at=datetime(2026, 8, 25, tzinfo=UTC),
        status="completed",
        dirty_worktree_flag=False,
        python_version="3.12.13",
        starsim_version="3.5.2",
        dependency_lock_hash="b" * 64,
        config_hash="c" * 64,
        parameter_set_id="demo-v0.1",
        parameter_set_hash="d" * 64,
        replicate_seeds=[123],
        start=2000.0,
        stop=2030.0,
        dt=1.0,
        runtime_seconds=0.1,
        validation_level="compatibility_spike",
        output_artifacts=[ArtifactRecord(path="summary.json", sha256="e" * 64, size_bytes=10)],
        declared_deterministic_outputs=["summary.final"],
        summary_sha256="f" * 64,
    )
    manifest = RunManifest(**kwargs)
    assert manifest.created_at.tzinfo is not None
    with pytest.raises(ValidationError):
        RunManifest(**{**kwargs, "created_at": datetime(2026, 8, 25)})
