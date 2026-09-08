import csv
from pathlib import Path

import pytest

import jersey_outbreak.data_pipeline as data_pipeline
from jersey_outbreak.data_pipeline import DataBuildError, build_canonical

ROOT = Path(__file__).resolve().parents[1]


def test_measure_dictionary_has_one_row_per_canonical_source(tmp_path: Path) -> None:
    output_dir = tmp_path / "processed"
    build_canonical(ROOT, output_dir)

    canonical_sources: dict[tuple[str, str], set[str]] = {}
    for table_name in data_pipeline._DICTIONARY_TABLES:
        with (output_dir / f"{table_name}.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            if table_name == "covid_weekly_vaccination":
                measure = f"{row['dose']}:{row['metric']}"
            elif table_name == "covid_weekly_eligible_population":
                measure = "eligible_population"
            elif table_name in {
                "population_estimates_annual",
                "population_denominators_by_age_band",
            }:
                measure = "count"
            elif "measure" in row:
                measure = row["measure"]
            else:
                measure = next(
                    column
                    for column in data_pipeline._DICTIONARY_VALUE_COLUMNS[table_name]
                    if column in row
                )
            canonical_sources.setdefault((table_name, measure), set()).add(row["source_id"])

    with (output_dir / "measure_dictionary.csv").open(newline="", encoding="utf-8") as handle:
        dictionary_rows = list(csv.DictReader(handle))

    for pair, source_ids in canonical_sources.items():
        if len(source_ids) < 2:
            continue
        rows = [row for row in dictionary_rows if (row["table"], row["measure"]) == pair]
        assert len(rows) == len(source_ids)
        assert {row["cited_source_id"] for row in rows} == source_ids

    age_rows = [
        row for row in dictionary_rows if row["table"] == "age_sex" and row["measure"] == "count"
    ]
    assert len(age_rows) == 2
    assert len({row["event_date_definition"] for row in age_rows}) == 2


def test_measure_dictionary_rejects_duplicate_source_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_read_csv_rows = data_pipeline.read_csv_rows

    def read_synthetic_rows(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
        rows = original_read_csv_rows(path, required_columns)
        if path.name == "measure_dictionary.csv":
            rows.append(dict(rows[0]))
        return rows

    monkeypatch.setattr(data_pipeline, "read_csv_rows", read_synthetic_rows)
    with pytest.raises(DataBuildError, match="duplicate measure dictionary key"):
        build_canonical(ROOT, tmp_path / "processed")


def test_measure_dictionary_rejects_missing_canonical_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_read_csv_rows = data_pipeline.read_csv_rows

    def read_synthetic_rows(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
        rows = original_read_csv_rows(path, required_columns)
        if path.name == "measure_dictionary.csv":
            rows = [
                row
                for row in rows
                if not (
                    row["table"] == "age_sex"
                    and row["measure"] == "count"
                    and row["source_id"] == "jersey_population_2024_manual_fixture"
                )
            ]
        return rows

    monkeypatch.setattr(data_pipeline, "read_csv_rows", read_synthetic_rows)
    with pytest.raises(DataBuildError, match="source keys differ from built tables"):
        build_canonical(ROOT, tmp_path / "processed")
