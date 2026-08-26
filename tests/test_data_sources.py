from pathlib import Path

import pytest
from pydantic import ValidationError

from jersey_outbreak.data_pipeline import (
    DataBuildError,
    SourceContext,
    SourceRegistry,
    load_source_registry,
    parse_int,
    read_csv_rows,
    validate_source_snapshots,
)

ROOT = Path(__file__).resolve().parents[1]


def test_source_registry_is_strict_and_all_snapshots_match() -> None:
    context = load_source_registry(ROOT)
    checks = validate_source_snapshots(context)
    assert len(context.registry.sources) == 17
    assert all(check["status"] == "passed" for check in checks)
    assert all(source.sha256 and source.local_snapshot for source in context.registry.sources)
    assert all(
        Path(source.local_snapshot).parts[2] == source.source_id
        for source in context.registry.sources
    )


def test_source_registry_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        SourceRegistry.model_validate({"sources": [], "unexpected": True})


def test_source_snapshot_hash_mismatch_fails() -> None:
    context = load_source_registry(ROOT)
    altered = context.registry.sources[0].model_copy(update={"sha256": "0" * 64})
    altered_context = SourceContext(ROOT, SourceRegistry(sources=[altered]))
    with pytest.raises(DataBuildError, match="SHA-256 mismatch"):
        validate_source_snapshots(altered_context)


def test_csv_contract_rejects_missing_columns_and_malformed_numbers(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.csv"
    malformed.write_text("name,value\nrow,not-a-number\n", encoding="utf-8")
    with pytest.raises(DataBuildError, match="missing required columns"):
        read_csv_rows(malformed, {"name", "value", "required"})
    with pytest.raises(DataBuildError, match="malformed numeric"):
        parse_int("not-a-number", path=malformed, field="value")

    malformed.write_text('name,value\n"unterminated,4\n', encoding="utf-8")
    with pytest.raises(DataBuildError, match="cannot read"):
        read_csv_rows(malformed, {"name", "value"})
