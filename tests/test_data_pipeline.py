import base64
import csv
import datetime
import hashlib
import json
from pathlib import Path

import pytest

import jersey_outbreak.data_pipeline as data_pipeline
from jersey_outbreak.data_pipeline import DataBuildError, build_canonical, parse_published_value
from jersey_outbreak.hashing import sha256_file

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_build_reconciles_controls_and_is_repeatable(tmp_path: Path) -> None:
    output_dir = tmp_path / "processed"
    first = build_canonical(ROOT, output_dir)
    first_bytes = {path.name: path.read_bytes() for path in output_dir.iterdir() if path.is_file()}
    second = build_canonical(ROOT, output_dir)
    second_bytes = {path.name: path.read_bytes() for path in output_dir.iterdir() if path.is_file()}

    assert first["build_status"] == second["build_status"] == "passed"
    assert first_bytes == second_bytes
    assert len(first["tables"]) == 21
    assert {check["status"] for check in first["checks"]} >= {"passed", "warning"}

    with (output_dir / "household_types.csv").open(newline="", encoding="utf-8") as handle:
        household_rows = list(csv.DictReader(handle))
    assert sum(int(row["households"]) for row in household_rows) == 44583

    with (output_dir / "workplace_sizes.csv").open(newline="", encoding="utf-8") as handle:
        workplace_rows = list(csv.DictReader(handle))
    censored = [row for row in workplace_rows if row["censoring"] == "positive_less_than"]
    assert censored
    assert all(row["count"] == "" and row["upper_bound"] == "5" for row in censored)

    with (output_dir / "commute_modes.csv").open(newline="", encoding="utf-8") as handle:
        commute_rows = list(csv.DictReader(handle))
    suppressed = [row for row in commute_rows if row["censoring"] == "positive_less_than"]
    assert suppressed
    assert all(row["workers"] == "" and row["upper_bound"] == "10" for row in suppressed)
    assert sha256_file(output_dir / "quality_report.json")


def test_parse_published_value_preserves_missing_and_suppression(tmp_path: Path) -> None:
    path = tmp_path / "published.csv"
    assert parse_published_value("", path=path, field="value") == (
        None,
        "not_reported",
        None,
    )
    assert parse_published_value("-1", path=path, field="value") == (
        None,
        "not_reported",
        None,
    )
    assert parse_published_value("<5", path=path, field="value") == (
        None,
        "positive_less_than",
        5,
    )
    assert parse_published_value("< 1,000", path=path, field="value") == (
        None,
        "positive_less_than",
        1000,
    )
    assert parse_published_value("12.5", path=path, field="value") == (12.5, "reported", None)
    with pytest.raises(DataBuildError):
        parse_published_value("float;#0", path=path, field="value")


def test_covid_daily_and_summary_tables_preserve_snapshot_values(tmp_path: Path) -> None:
    output_dir = tmp_path / "processed"
    build_canonical(ROOT, output_dir)

    with (output_dir / "covid_daily_surveillance.csv").open(newline="", encoding="utf-8") as handle:
        daily_rows = list(csv.DictReader(handle))
    assert len(daily_rows) == 10087
    assert (
        sum(
            row["measure"] == "cumulative_confirmed_cases"
            and row["reporting_status"] == "not_reported"
            for row in daily_rows
        )
        == 416
    )

    with (ROOT / "data/raw/covid19_daily_surveillance_csv/covid19_daily.csv").open(
        newline="", encoding="utf-8-sig"
    ) as handle:
        raw_value = next(
            row["CasesDailyNewConfirmedCases"]
            for row in csv.DictReader(handle)
            if row["Date"] == "2020-07-30"
        )
    assert (
        next(
            row["value"]
            for row in daily_rows
            if row["date"] == "2020-07-30" and row["measure"] == "daily_new_confirmed_cases"
        )
        == raw_value
    )

    with (output_dir / "covid_current_summary.csv").open(newline="", encoding="utf-8") as handle:
        current_rows = list(csv.DictReader(handle))
    assert len(current_rows) == 5176
    assert all(row["date"] for row in current_rows)


def test_covid_weekly_pair_set_and_quality_warnings(tmp_path: Path) -> None:
    output_dir = tmp_path / "processed"
    build_canonical(ROOT, output_dir)
    with (output_dir / "covid_weekly_vaccination.csv").open(newline="", encoding="utf-8") as handle:
        weekly_rows = list(csv.DictReader(handle))
    actual_pairs = {(row["dose"], row["age_band"]) for row in weekly_rows}
    expected_pairs = {
        ("dose_1", "all"),
        ("dose_1", "5_to_11"),
        ("dose_1", "12_to_15"),
        ("dose_1", "16_to_17"),
        ("dose_1", "17_and_under"),
        ("dose_1", "18_to_29"),
        ("dose_1", "30_to_39"),
        ("dose_1", "40_to_49"),
        ("dose_1", "50_to_54"),
        ("dose_1", "55_to_59"),
        ("dose_1", "60_to_64"),
        ("dose_1", "65_to_69"),
        ("dose_1", "70_to_74"),
        ("dose_1", "75_to_79"),
        ("dose_1", "80_plus"),
        ("dose_2", "all"),
        ("dose_2", "5_to_11"),
        ("dose_2", "12_to_15"),
        ("dose_2", "16_to_17"),
        ("dose_2", "17_and_under"),
        ("dose_2", "18_to_29"),
        ("dose_2", "30_to_39"),
        ("dose_2", "40_to_49"),
        ("dose_2", "50_to_54"),
        ("dose_2", "55_to_59"),
        ("dose_2", "60_to_64"),
        ("dose_2", "65_to_69"),
        ("dose_2", "70_to_74"),
        ("dose_2", "75_to_79"),
        ("dose_2", "80_plus"),
        ("dose_3", "all"),
        ("dose_3", "5_to_11"),
        ("dose_3", "12_to_15"),
        ("dose_3", "16_to_17"),
        ("dose_3", "18_to_29"),
        ("dose_3", "30_to_39"),
        ("dose_3", "40_to_49"),
        ("dose_3", "50_to_54"),
        ("dose_3", "55_to_59"),
        ("dose_3", "60_to_64"),
        ("dose_3", "65_to_69"),
        ("dose_3", "70_to_74"),
        ("dose_3", "75_to_79"),
        ("dose_3", "80_plus"),
        ("dose_4", "all"),
        ("dose_4", "5_to_11"),
        ("dose_4", "12_to_15"),
        ("dose_4", "16_to_17"),
        ("dose_4", "18_to_29"),
        ("dose_4", "30_to_39"),
        ("dose_4", "40_to_49"),
        ("dose_4", "50_to_54"),
        ("dose_4", "55_to_59"),
        ("dose_4", "60_to_64"),
        ("dose_4", "65_to_69"),
        ("dose_4", "70_to_74"),
        ("dose_4", "75_to_79"),
        ("dose_4", "80_plus"),
        ("autumn_2022_booster", "all"),
        ("autumn_2022_booster", "50_plus"),
        ("autumn_2022_booster", "5_to_11"),
        ("autumn_2022_booster", "12_to_15"),
        ("autumn_2022_booster", "16_to_17"),
        ("autumn_2022_booster", "18_to_29"),
        ("autumn_2022_booster", "30_to_39"),
        ("autumn_2022_booster", "40_to_49"),
        ("autumn_2022_booster", "50_to_54"),
        ("autumn_2022_booster", "55_to_59"),
        ("autumn_2022_booster", "60_to_64"),
        ("autumn_2022_booster", "65_to_69"),
        ("autumn_2022_booster", "70_to_74"),
        ("autumn_2022_booster", "75_to_79"),
        ("autumn_2022_booster", "80_plus"),
    }
    assert actual_pairs == expected_pairs

    report = json.loads((output_dir / "quality_report.json").read_text(encoding="utf-8"))
    assert any("undated row raw values: ,1165877,67397,0," in w for w in report["warnings"])
    assert any("float;#0" in w and "float;#1073672.00000000" in w for w in report["warnings"])
    assert any(
        "JHU cumulative confirmed first differences contain" in w for w in report["warnings"]
    )
    assert (
        "annual population estimates are published rounded to the nearest 10; sums are not exact"
        in report["warnings"]
    )


def test_covid_serosurvey_table_is_transcribed_fixture(tmp_path: Path) -> None:
    output_dir = tmp_path / "processed"
    build_canonical(ROOT, output_dir)
    with (output_dir / "covid_serosurvey_2020.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 13
    assert (
        next(
            row["value"]
            for row in rows
            if row["measure"] == "estimated_population_prevalence_percent"
        )
        == "3.1"
    )


def test_covid_jhu_daily_table_matches_frozen_series(tmp_path: Path) -> None:
    output_dir = tmp_path / "processed"
    build_canonical(ROOT, output_dir)
    with (output_dir / "covid_jhu_daily.csv").open(newline="", encoding="utf-8") as handle:
        table_rows = list(csv.DictReader(handle))
    with (
        ROOT / "data/raw/jhu_csse_confirmed_global_csv/time_series_covid19_confirmed_global.csv"
    ).open(newline="", encoding="utf-8") as handle:
        raw_rows = list(csv.DictReader(handle))
    raw_jersey = [
        row
        for row in raw_rows
        if row["Province/State"] == "Jersey" and row["Country/Region"] == "United Kingdom"
    ]
    assert len(raw_jersey) == 1
    raw_dates = list(raw_rows[0])[4:]
    raw_values = [int(raw_jersey[0][raw_date]) for raw_date in raw_dates]
    expected_first_value = next(value for value in raw_values if value > 0)
    expected_last_value = raw_values[-1]

    cumulative_rows = [row for row in table_rows if row["measure"] == "cumulative_confirmed_cases"]
    daily_rows = [row for row in table_rows if row["measure"] == "daily_new_confirmed_cases"]
    assert len(cumulative_rows) == len(raw_dates) == len(daily_rows)
    assert len({row["date"] for row in table_rows}) == len(raw_dates)
    assert all(datetime.date.fromisoformat(row["date"]) for row in table_rows)
    first_nonzero = next(row for row in cumulative_rows if int(row["value"]) > 0)
    assert first_nonzero["date"] == "2020-03-22"
    assert int(first_nonzero["value"]) == expected_first_value
    assert int(cumulative_rows[-1]["value"]) == expected_last_value
    assert sum(int(row["value"]) for row in daily_rows) == expected_last_value


def test_population_estimates_annual_table_reconciles_sexes(tmp_path: Path) -> None:
    output_dir = tmp_path / "processed"
    build_canonical(ROOT, output_dir)
    with (output_dir / "population_estimates_annual.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    years = {int(row["year"]) for row in rows}
    assert years == set(range(2011, 2025))
    ages_by_year = {
        year: {row["age"] for row in rows if int(row["year"]) == year} for year in years
    }
    assert {len(ages) for ages in ages_by_year.values()} == {101}
    by_key = {(int(row["year"]), row["age"], row["sex"]): int(row["count"]) for row in rows}
    for year, ages in ages_by_year.items():
        for age in ages:
            assert (
                by_key[(year, age, "all")]
                == by_key[(year, age, "male")] + by_key[(year, age, "female")]
            )


def test_wayback_respiratory_pdf_digests_match_cdx_pins() -> None:
    expected = {
        "respiratory_epidemiological_report_wayback_20240223_pdf": (
            "VP7XXH3574O6WTH74AFNV7EJ3UOCOYW7"
        ),
        "respiratory_epidemiological_report_wayback_20240718_pdf": (
            "XXYCUEBFI7MCLMJU773M4Y2MQOYT4NB4"
        ),
        "respiratory_epidemiological_report_wayback_20260102_pdf": (
            "44QV6WTJNA3CQXZWM4CIU3TLD75T7UTK"
        ),
    }
    for source_id, digest in expected.items():
        path = next((ROOT / "data/raw" / source_id).glob("*.pdf"))
        payload = path.read_bytes()
        actual = base64.b32encode(hashlib.sha1(payload).digest()).decode()
        assert payload.startswith(b"%PDF")
        assert actual == digest


def test_unmapped_vaccination_column_fails_the_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_read_csv_rows = data_pipeline.read_csv_rows

    def read_synthetic_rows(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
        rows = original_read_csv_rows(path, required_columns)
        if path.name == "covid19_weekly_vaccination.csv":
            rows[0]["SyntheticUnmappedVaccinationColumn"] = "1"
        return rows

    monkeypatch.setattr(data_pipeline, "read_csv_rows", read_synthetic_rows)
    with pytest.raises(DataBuildError, match="unmapped vaccination column"):
        build_canonical(ROOT, tmp_path / "processed")
