"""Milestone 1 source registry validation and canonical aggregate build.

The pipeline deliberately stops at aggregate controls.  It never creates
individuals, settings, contacts or disease-model state.
"""

from __future__ import annotations

import csv
import json
import math
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import model_validator

from .canonical_schemas import (
    AgeSexRow,
    CanonicalProvenance,
    CommunalSettingRow,
    CommuteModeRow,
    CovidCurrentSummaryRow,
    CovidDailySurveillanceRow,
    CovidJhuDailyRow,
    CovidSerosurveyRow,
    CovidWeeklyEligiblePopulationRow,
    CovidWeeklyVaccinationRow,
    DerivedControlRow,
    EmploymentSectorRow,
    HouseholdTypeRow,
    MeasureRow,
    ParishAgeSexRow,
    ParishPopulationRow,
    PassengerArrivalRow,
    PopulationEstimateAnnualRow,
    PopulationTotalRow,
    SchoolStudentRow,
    WorkplaceDestinationRow,
    WorkplaceSizeRow,
)
from .contracts import SourceRecord, StrictModel
from .hashing import sha256_file


class DataBuildError(ValueError):
    """Raised when a source or canonical table violates its contract."""


class SourceRegistry(StrictModel):
    """Strict top-level shape of ``data/sources.yaml``."""

    sources: list[SourceRecord]

    @model_validator(mode="after")
    def validate_unique_ids(self) -> SourceRegistry:
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("source_id values must be unique")
        return self


@dataclass(frozen=True)
class SourceContext:
    root: Path
    registry: SourceRegistry

    @property
    def by_id(self) -> dict[str, SourceRecord]:
        return {source.source_id: source for source in self.registry.sources}

    def source(self, source_id: str) -> SourceRecord:
        try:
            return self.by_id[source_id]
        except KeyError as exc:
            raise DataBuildError(f"unknown source_id: {source_id}") from exc

    def artifact_path(self, source_id: str) -> Path:
        source = self.source(source_id)
        if source.local_snapshot is None:
            raise DataBuildError(f"source has no local_snapshot: {source_id}")
        return self.root / source.local_snapshot

    def provenance(
        self,
        source_id: str,
        *,
        locator: str,
        transformation_id: str,
        observation_status: str = "observed",
        reference_period: str | None = None,
    ) -> dict[str, Any]:
        source = self.source(source_id)
        if source.sha256 is None:
            raise DataBuildError(f"source has no sha256: {source_id}")
        return {
            "schema_version": "1.0",
            "source_id": source_id,
            "source_sha256": source.sha256,
            "evidence_source_id": source.evidence_source_id,
            "reference_period": reference_period or source.reference_period,
            "observation_status": observation_status,
            "source_locator": locator,
            "transformation_id": transformation_id,
        }


def load_source_registry(root: Path) -> SourceContext:
    """Load and strictly validate the repository source registry."""

    registry_path = root / "data" / "sources.yaml"
    try:
        raw = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        registry = SourceRegistry.model_validate(raw)
    except (OSError, yaml.YAMLError, TypeError, ValueError) as exc:
        raise DataBuildError(f"invalid source registry {registry_path}: {exc}") from exc
    context = SourceContext(root=root, registry=registry)
    validate_source_snapshots(context)
    return context


def validate_source_snapshots(context: SourceContext) -> list[dict[str, Any]]:
    """Check local snapshot presence, hashes and manual-evidence references."""

    source_ids = set(context.by_id)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    for source in context.registry.sources:
        if source.evidence_source_id is not None and source.evidence_source_id not in source_ids:
            errors.append(
                f"{source.source_id}: evidence_source_id does not exist: "
                f"{source.evidence_source_id}"
            )
        if source.local_snapshot is None or source.sha256 is None:
            checks.append(
                {
                    "source_id": source.source_id,
                    "status": "unavailable",
                    "local_snapshot": source.local_snapshot,
                }
            )
            continue
        path = context.root / source.local_snapshot
        if not path.is_file():
            errors.append(f"{source.source_id}: local snapshot is missing: {path}")
            checks.append(
                {
                    "source_id": source.source_id,
                    "status": "failed",
                    "local_snapshot": source.local_snapshot,
                }
            )
            continue
        actual_hash = sha256_file(path)
        if actual_hash != source.sha256:
            errors.append(
                f"{source.source_id}: SHA-256 mismatch; registry={source.sha256}, "
                f"actual={actual_hash}"
            )
            status = "failed"
        else:
            status = "passed"
        checks.append(
            {
                "source_id": source.source_id,
                "status": status,
                "local_snapshot": source.local_snapshot,
                "sha256": actual_hash,
                "acquisition_method": source.acquisition_method,
            }
        )
    if errors:
        raise DataBuildError("source snapshot validation failed: " + " | ".join(errors))
    return checks


def read_csv_rows(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
    """Read a UTF-8 CSV and fail on missing columns or malformed row width."""

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, strict=True)
            headers = {
                str(header).strip() for header in (reader.fieldnames or []) if header is not None
            }
            missing = required_columns - headers
            if missing:
                raise DataBuildError(f"{path}: missing required columns: {sorted(missing)}")
            rows: list[dict[str, str]] = []
            for line_number, raw_row in enumerate(reader, start=2):
                if None in raw_row:
                    raise DataBuildError(f"{path}:{line_number}: unexpected extra CSV fields")
                row = {
                    str(key).strip(): (value or "").strip()
                    for key, value in raw_row.items()
                    if key is not None
                }
                rows.append(row)
            return rows
    except (OSError, csv.Error) as exc:
        raise DataBuildError(f"cannot read {path}: {exc}") from exc


_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


def parse_number(
    raw: str, *, path: Path, field: str, allow_blank: bool = False
) -> int | float | None:
    """Parse published numeric text without accepting arbitrary coercion."""

    token = raw.strip().replace(",", "")
    if not token:
        if allow_blank:
            return None
        raise DataBuildError(f"{path}: blank numeric value in {field}")
    if not _NUMBER_RE.fullmatch(token):
        raise DataBuildError(f"{path}: malformed numeric value {raw!r} in {field}")
    value = float(token) if any(char in token for char in ".eE") else int(token)
    if isinstance(value, float) and not math.isfinite(value):
        raise DataBuildError(f"{path}: non-finite numeric value in {field}")
    return value


def parse_int(raw: str, *, path: Path, field: str, allow_blank: bool = False) -> int | None:
    value = parse_number(raw, path=path, field=field, allow_blank=allow_blank)
    if value is None:
        return None
    if isinstance(value, float) and not value.is_integer():
        raise DataBuildError(f"{path}: expected integer value in {field}, got {raw!r}")
    return int(value)


_POSITIVE_LESS_THAN_RE = re.compile(r"^<\s*(\d[\d,]*)$")


def parse_published_value(
    raw: str, *, path: Path, field: str
) -> tuple[int | float | None, str, int | None]:
    """Parse a published value while preserving missing and suppressed cells."""

    token = raw.strip()
    if not token or token == "-1":
        return None, "not_reported", None
    match = _POSITIVE_LESS_THAN_RE.fullmatch(token)
    if match:
        upper_bound = parse_int(match.group(1), path=path, field=field)
        if upper_bound is None:
            raise DataBuildError(f"{path}: blank suppression bound in {field}")
        return None, "positive_less_than", upper_bound
    return parse_number(token, path=path, field=field), "reported", None


def _required(row: dict[str, str], field: str, path: Path) -> str:
    value = row.get(field, "").strip()
    if not value:
        raise DataBuildError(f"{path}: blank required field {field}")
    return value


def _iso_date(raw: str, *, path: Path, field: str) -> str:
    value = _required({field: raw}, field, path)
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise DataBuildError(f"{path}: invalid ISO date {value!r} in {field}") from exc
    if parsed.isoformat() != value:
        raise DataBuildError(f"{path}: non-canonical ISO date {value!r} in {field}")
    return value


def _manual_rows(context: SourceContext, source_id: str) -> tuple[Path, list[dict[str, str]]]:
    path = context.artifact_path(source_id)
    return path, read_csv_rows(path, {"measure", "value", "reference_period", "source_locator"})


def _provenance(
    context: SourceContext,
    source_id: str,
    row: dict[str, str],
    transformation_id: str,
    *,
    observation_status: str = "observed",
) -> dict[str, Any]:
    return context.provenance(
        source_id,
        locator=_required(row, "source_locator", context.artifact_path(source_id)),
        transformation_id=transformation_id,
        observation_status=observation_status,
        reference_period=_required(row, "reference_period", context.artifact_path(source_id)),
    )


def _validated_rows[ModelT: CanonicalProvenance](
    model: type[ModelT], rows: list[dict[str, Any]]
) -> list[ModelT]:
    try:
        return [model.model_validate(row) for row in rows]
    except ValueError as exc:
        raise DataBuildError(
            f"canonical row validation failed for {model.__name__}: {exc}"
        ) from exc


def _csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return format(value, ".15g")
    return str(value)


def _write_table[ModelT: CanonicalProvenance](
    output_dir: Path,
    filename: str,
    model: type[ModelT],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    validated = _validated_rows(model, rows)
    columns = list(model.model_fields)
    path = output_dir / filename
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in validated:
            values = row.model_dump(mode="python")
            writer.writerow({column: _csv_value(values.get(column)) for column in columns})
    return {
        "path": str(path.relative_to(output_dir.parent.parent)),
        "rows": len(validated),
        "sha256": sha256_file(path),
        "columns": columns,
    }


def _normalize_parish(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().replace("St.", "St")).strip()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _add_check(
    checks: list[dict[str, Any]],
    name: str,
    actual: int | float,
    expected: int | float,
    *,
    tolerance: int | float = 0,
    warning: bool = False,
) -> str:
    difference = actual - expected
    passed = abs(difference) <= tolerance
    status = "passed" if passed and not warning else "warning" if passed or warning else "failed"
    checks.append(
        {
            "name": name,
            "status": status,
            "actual": actual,
            "expected": expected,
            "difference": difference,
            "tolerance": tolerance,
        }
    )
    if status == "failed":
        raise DataBuildError(
            f"reconciliation failed for {name}: actual={actual}, expected={expected}"
        )
    return status


_COVID_DAILY_MEASURES = (
    ("daily_new_confirmed_cases", "CasesDailyNewConfirmedCases", "cases"),
    ("cumulative_confirmed_cases", "CasesTotalConfirmedPositiveCases", "cases"),
    ("symptomatic_cases", "CasesSymptomatic", "cases"),
    ("asymptomatic_cases", "CasesAsymptomatic", "cases"),
    ("current_known_active_cases", "CasesCurrentKnownActiveCases", "cases"),
    ("seven_day_rate_per_100k", "CasesSeven7DayNumberper100000", "per_100000"),
    ("cumulative_tests", "TestsTotaltests", "tests"),
    (
        "tests_reason_symptomatic",
        "TestsReasonfortestseekinghealthcaresymptomatic",
        "tests",
    ),
    ("tests_reason_inbound_travel", "TestsReasonforTestInboundTravel", "tests"),
    (
        "tests_reason_on_island_screening",
        "TestsReasonforTestOnIslandSurveillanceScreening",
        "tests",
    ),
    ("cumulative_deaths", "MortalityTotalDeaths", "deaths"),
)

_COVID_CURRENT_MEASURES = (
    ("cumulative_tests", "TestsTotalTests", "tests"),
    ("cumulative_confirmed_cases", "CasesTotalConfirmedPositiveCases", "cases"),
    ("seven_day_rate_per_100k", "CasesSeven7DayNumberper100000", "per_100000"),
    ("cumulative_deaths", "MortalityTotalDeaths", "deaths"),
)

_VACCINATION_EXCLUSIONS = frozenset(
    {
        "VaccinationsTotalNumberDoses",
        "VaccinationsDosesPer100PeopleInPopulation",
        "EligiblePopulation",
        "7DayRatePercentageChange",
        "InboundTravel",
        "On-islandSurveillanceScreening",
        "SeekingHealthcareSymptomatic",
        "DateTime",
        "DateTimeShort",
        "Note",
    }
)
_VACCINATION_DOSES = {
    "FirstDose": "dose_1",
    "SecondDose": "dose_2",
    "ThirdDose": "dose_3",
    "FourthDose": "dose_4",
    "AutumnBooster2022": "autumn_2022_booster",
}
_VACCINATION_AGE_BANDS = {
    "5to11years": "5_to_11",
    "12to15years": "12_to_15",
    "16to17years": "16_to_17",
    "17yearsandunder": "17_and_under",
    "18to29years": "18_to_29",
    "30to39years": "30_to_39",
    "40to49years": "40_to_49",
    "50to54years": "50_to_54",
    "55to59years": "55_to_59",
    "60to64years": "60_to_64",
    "65to69years": "65_to_69",
    "70to74years": "70_to_74",
    "75to79years": "75_to_79",
    "80yearsandover": "80_plus",
}
_VACCINATION_DIRECT_COLUMNS = {
    **{
        f"VaccinationsTotalNumber{source_dose}Vaccinations": (
            dose,
            "all",
            "cumulative_doses",
        )
        for source_dose, dose in _VACCINATION_DOSES.items()
        if source_dose != "AutumnBooster2022"
    },
    **{
        f"VaccinationsTotalNumber{source_dose}VaccinationsPercentage": (
            dose,
            "all",
            "percent_population",
        )
        for source_dose, dose in _VACCINATION_DOSES.items()
        if source_dose != "AutumnBooster2022"
    },
    "VaccinationsTotalNumberAutumnBooster2022": (
        "autumn_2022_booster",
        "all",
        "cumulative_doses",
    ),
    "VaccinationsTotalNumberAutumnBooster2022Percentage50plus": (
        "autumn_2022_booster",
        "50_plus",
        "percent_population",
    ),
}
_SEROSURVEY_MEASURES = (
    "estimated_population_prevalence_percent",
    "estimated_population_prevalence_ci95_half_width_percent",
    "observed_unweighted_prevalence_percent",
    "weighted_unadjusted_prevalence_percent",
    "households_tested",
    "individuals_tested",
    "response_rate_households_percent",
    "response_rate_individuals_percent",
    "assumed_test_sensitivity_percent",
    "assumed_test_sensitivity_ci95_low_percent",
    "assumed_test_sensitivity_ci95_high_percent",
    "assumed_test_specificity_percent",
    "minimum_age_years",
)

_JHU_DATE_COUNT = 1143
_JHU_FIRST_NONZERO_DATE = "2020-03-22"
_JHU_FIRST_NONZERO_VALUE = 12
_JHU_FINAL_CONFIRMED = 66391
_POPULATION_ESTIMATE_YEAR_COUNT = 14
_POPULATION_ESTIMATE_ROWS_PER_YEAR = 101


def _vaccination_column_spec(column: str, path: Path) -> tuple[str, str, str]:
    direct = _VACCINATION_DIRECT_COLUMNS.get(column)
    if direct is not None:
        return direct
    match = re.fullmatch(
        r"(VaccinationsTotalVaccinationDoses|VaccinationsPercentagePopulationVaccinated)"
        r"(FirstDose|SecondDose|ThirdDose|FourthDose|AutumnBooster2022)(.+)",
        column,
    )
    if match:
        metric_prefix, source_dose, source_age_band = match.groups()
        try:
            dose = _VACCINATION_DOSES[source_dose]
            age_band = _VACCINATION_AGE_BANDS[source_age_band]
        except KeyError as exc:
            raise DataBuildError(f"{path}: unmapped vaccination column {column!r}") from exc
        metric = (
            "cumulative_doses"
            if metric_prefix == "VaccinationsTotalVaccinationDoses"
            else "percent_population"
        )
        return dose, age_band, metric
    raise DataBuildError(f"{path}: unmapped vaccination column {column!r}")


def _jhu_jersey_row(rows: list[dict[str, str]], path: Path, measure: str) -> dict[str, str]:
    matches = [
        row
        for row in rows
        if row.get("Province/State") == "Jersey" and row.get("Country/Region") == "United Kingdom"
    ]
    if len(matches) != 1:
        state = "absent" if not matches else "duplicated"
        raise DataBuildError(f"{path}: Jersey/United Kingdom {measure} row is {state}")
    return matches[0]


def _jhu_int(raw: str, *, path: Path, field: str) -> int:
    value, status, _ = parse_published_value(raw, path=path, field=field)
    if status != "reported" or value is None:
        raise DataBuildError(f"{path}: JHU value is not reported in {field}")
    if isinstance(value, float) and not value.is_integer():
        raise DataBuildError(f"{path}: JHU value is not an integer in {field}")
    return int(value)


def _jhu_date_header(raw: str, *, path: Path) -> str:
    if not re.fullmatch(r"\d{1,2}/\d{1,2}/\d{2}", raw):
        raise DataBuildError(f"{path}: unparsable JHU date header {raw!r}")
    try:
        return datetime.strptime(raw, "%m/%d/%y").date().isoformat()
    except ValueError as exc:
        raise DataBuildError(f"{path}: unparsable JHU date header {raw!r}") from exc


def _covid_jhu_tables(
    context: SourceContext,
    checks: list[dict[str, Any]],
    daily_tables: list[dict[str, Any]],
    warnings: list[str],
) -> list[dict[str, Any]]:
    confirmed_source = "jhu_csse_confirmed_global_csv"
    deaths_source = "jhu_csse_deaths_global_csv"
    confirmed_path = context.artifact_path(confirmed_source)
    deaths_path = context.artifact_path(deaths_source)
    confirmed_rows = read_csv_rows(confirmed_path, {"Province/State", "Country/Region"})
    deaths_rows = read_csv_rows(deaths_path, {"Province/State", "Country/Region"})
    confirmed_row = _jhu_jersey_row(confirmed_rows, confirmed_path, "confirmed")
    deaths_row = _jhu_jersey_row(deaths_rows, deaths_path, "deaths")
    confirmed_headers = list(confirmed_rows[0]) if confirmed_rows else []
    deaths_headers = list(deaths_rows[0]) if deaths_rows else []
    if len(confirmed_headers) < 5 or len(deaths_headers) < 5:
        raise DataBuildError("JHU global files have no date columns")
    date_headers = confirmed_headers[4:]
    death_date_headers = deaths_headers[4:]
    if date_headers != death_date_headers:
        raise DataBuildError("JHU confirmed and deaths date headers differ")
    iso_dates = [_jhu_date_header(header, path=confirmed_path) for header in date_headers]
    if len(set(iso_dates)) != len(iso_dates):
        raise DataBuildError(f"{confirmed_path}: duplicate JHU date headers")
    confirmed_values = [
        _jhu_int(confirmed_row[header], path=confirmed_path, field=header)
        for header in date_headers
    ]
    death_values = [
        _jhu_int(deaths_row[header], path=deaths_path, field=header) for header in date_headers
    ]
    tables: list[dict[str, Any]] = []
    for iso_date, header, confirmed_value, death_value in zip(
        iso_dates, date_headers, confirmed_values, death_values, strict=True
    ):
        tables.extend(
            [
                {
                    **context.provenance(
                        confirmed_source,
                        locator=f"csv_row_Jersey_col_{header}",
                        transformation_id="jhu_csv_observed_v1",
                    ),
                    "date": iso_date,
                    "measure": "cumulative_confirmed_cases",
                    "value": confirmed_value,
                    "unit": "cases",
                },
                {
                    **context.provenance(
                        deaths_source,
                        locator=f"csv_row_Jersey_col_{header}",
                        transformation_id="jhu_csv_observed_v1",
                    ),
                    "date": iso_date,
                    "measure": "cumulative_deaths",
                    "value": death_value,
                    "unit": "deaths",
                },
            ]
        )
    negative_days = 0
    for index, iso_date in enumerate(iso_dates):
        previous_date = iso_dates[index - 1] if index else "starting_cumulative"
        daily_value = (
            confirmed_values[index]
            if index == 0
            else confirmed_values[index] - confirmed_values[index - 1]
        )
        if daily_value < 0:
            negative_days += 1
        tables.append(
            {
                **context.provenance(
                    confirmed_source,
                    locator=f"derived_from_{iso_date}_and_{previous_date}",
                    transformation_id="jhu_first_difference_v1",
                    observation_status="derived",
                ),
                "date": iso_date,
                "measure": "daily_new_confirmed_cases",
                "value": daily_value,
                "unit": "cases",
            }
        )
    warnings.append(
        "JHU cumulative confirmed first differences contain "
        f"{negative_days} negative days; published corrections are preserved without clipping."
    )
    _add_check(checks, "covid_jhu_dates", len(date_headers), _JHU_DATE_COUNT)
    first_nonzero_index = next(
        (index for index, value in enumerate(confirmed_values) if value > 0), None
    )
    if first_nonzero_index is None:
        raise DataBuildError(f"{confirmed_path}: Jersey confirmed series has no nonzero date")
    first_nonzero_date = iso_dates[first_nonzero_index]
    first_check = _add_check(
        checks,
        "covid_jhu_first_nonzero_confirmed",
        confirmed_values[first_nonzero_index],
        _JHU_FIRST_NONZERO_VALUE,
    )
    checks[-1]["details"] = (
        f"first_date={first_nonzero_date}; expected_date={_JHU_FIRST_NONZERO_DATE}; "
        f"status={first_check}"
    )
    if first_nonzero_date != _JHU_FIRST_NONZERO_DATE:
        raise DataBuildError(
            "reconciliation failed for covid_jhu_first_nonzero_confirmed date: "
            f"actual={first_nonzero_date}, expected={_JHU_FIRST_NONZERO_DATE}"
        )
    _add_check(checks, "covid_jhu_final_confirmed", confirmed_values[-1], _JHU_FINAL_CONFIRMED)
    govje_final = next(
        (
            row
            for row in daily_tables
            if row["date"] == "2023-02-01" and row["measure"] == "cumulative_confirmed_cases"
        ),
        None,
    )
    if govje_final is None or govje_final["value"] is None:
        raise DataBuildError("JHU versus Government of Jersey cross-check has no published value")
    jhu_final_index = iso_dates.index("2023-02-01")
    _add_check(
        checks,
        "covid_jhu_vs_govje_cumulative_2023_02_01",
        confirmed_values[jhu_final_index],
        govje_final["value"],
        tolerance=0,
        warning=True,
    )
    return tables


def _population_estimate_table(
    context: SourceContext, checks: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    source_id = "annual_population_estimates_by_age_sex_csv"
    path = context.artifact_path(source_id)
    raw_rows = read_csv_rows(path, {"Year", "Age", "Male", "Female"})
    if not raw_rows:
        raise DataBuildError(f"{path}: no annual population estimate rows")
    tables: list[dict[str, Any]] = []
    years: set[int] = set()
    rows_per_year: dict[int, int] = {}
    seen: set[tuple[int, str]] = set()
    for raw_row in raw_rows:
        year = parse_int(raw_row["Year"], path=path, field="Year")
        if year is None:
            raise DataBuildError(f"{path}: blank Year")
        age = _required(raw_row, "Age", path)
        key = (year, age)
        if key in seen:
            raise DataBuildError(f"{path}: duplicate year/age row {year}/{age}")
        seen.add(key)
        years.add(year)
        rows_per_year[year] = rows_per_year.get(year, 0) + 1
        parsed: dict[str, tuple[int, str, int | None]] = {}
        for column in ("Male", "Female"):
            value, status, upper_bound = parse_published_value(
                raw_row[column], path=path, field=column
            )
            if value is None:
                raise DataBuildError(f"{path}: {column} is not reported for {year}/{age}")
            if isinstance(value, float) and not value.is_integer():
                raise DataBuildError(f"{path}: {column} is not an integer for {year}/{age}")
            parsed[column] = (int(value), status, upper_bound)
            tables.append(
                {
                    **context.provenance(
                        source_id,
                        locator=f"csv_row_{year}_age_{age}_col_{column}",
                        transformation_id="annual_estimates_observed_v1",
                    ),
                    "year": year,
                    "age": age,
                    "sex": column.lower(),
                    "count": int(value),
                    "reporting_status": status,
                    "upper_bound": upper_bound,
                }
            )
        tables.append(
            {
                **context.provenance(
                    source_id,
                    locator=f"derived_from_{year}_age_{age}_Male_and_Female",
                    transformation_id="annual_estimates_sex_sum_v1",
                    observation_status="derived",
                ),
                "year": year,
                "age": age,
                "sex": "all",
                "count": parsed["Male"][0] + parsed["Female"][0],
                "reporting_status": "reported",
                "upper_bound": None,
            }
        )
    _add_check(checks, "population_estimates_years", len(years), _POPULATION_ESTIMATE_YEAR_COUNT)
    if len(set(rows_per_year.values())) != 1:
        raise DataBuildError(f"{path}: annual population age-row counts differ by year")
    _add_check(
        checks,
        "population_estimates_rows_per_year",
        next(iter(rows_per_year.values())),
        _POPULATION_ESTIMATE_ROWS_PER_YEAR,
    )
    census_source = "census_2021_age_gender_csv"
    census_path = context.artifact_path(census_source)
    census_total = 0
    for census_row in read_csv_rows(census_path, {"Age", "All"}):
        value = parse_int(census_row["All"], path=census_path, field="All")
        if value is None:
            raise DataBuildError(f"{census_path}: blank All value")
        census_total += value
    estimate_2021_total = sum(
        row["count"] for row in tables if row["year"] == 2021 and row["sex"] == "all"
    )
    _add_check(
        checks,
        "population_estimates_2021_vs_census_total",
        estimate_2021_total,
        census_total,
        tolerance=0,
        warning=True,
    )
    return tables


def _covid_tables(
    context: SourceContext, checks: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]] | str]:
    warnings: list[str] = []

    daily_source = "covid19_daily_surveillance_csv"
    daily_path = context.artifact_path(daily_source)
    daily_required = {"Date", "TestsTotalNegativeTests"}
    daily_required.update(column for _, column, _ in _COVID_DAILY_MEASURES)
    daily_raw_rows = read_csv_rows(daily_path, daily_required)
    negative_tests_values = [row["TestsTotalNegativeTests"] for row in daily_raw_rows]
    rendered_count = sum(value.startswith("float;#") for value in negative_tests_values)
    zero_rendered_count = sum(value == "float;#0" for value in negative_tests_values)
    special_rendered_count = sum(
        value == "float;#1073672.00000000" for value in negative_tests_values
    )
    warnings.append(
        "covid daily surveillance anomaly: TestsTotalNegativeTests is excluded because "
        f"{rendered_count} of {len(negative_tests_values)} cells use SharePoint "
        "calculated-field rendering, including "
        f"{zero_rendered_count} cells rendered as float;#0 and "
        f"{special_rendered_count} cell rendered as float;#1073672.00000000."
    )
    daily_prepared = [
        (_iso_date(row["Date"], path=daily_path, field="Date"), row) for row in daily_raw_rows
    ]
    daily_dates = [value for value, _ in daily_prepared]
    if len(set(daily_dates)) != len(daily_dates):
        raise DataBuildError(f"{daily_path}: duplicate Date values")
    daily_tables: list[dict[str, Any]] = []
    for date_value, row in sorted(daily_prepared):
        for measure, column, unit in _COVID_DAILY_MEASURES:
            value, reporting_status, upper_bound = parse_published_value(
                row[column], path=daily_path, field=column
            )
            daily_tables.append(
                {
                    **context.provenance(
                        daily_source,
                        locator=f"csv_row_{date_value}_col_{column}",
                        transformation_id="csv_covid_daily_surveillance_long_v1",
                    ),
                    "date": date_value,
                    "measure": measure,
                    "value": value,
                    "unit": unit,
                    "reporting_status": reporting_status,
                    "upper_bound": upper_bound,
                }
            )
    _add_check(checks, "covid_daily_rows", len(daily_raw_rows), 917)
    _add_check(
        checks,
        "covid_daily_not_reported_cumulative_cases",
        sum(
            row["measure"] == "cumulative_confirmed_cases"
            and row["reporting_status"] == "not_reported"
            for row in daily_tables
        ),
        416,
    )

    current_source = "covid19_current_summary_csv"
    current_path = context.artifact_path(current_source)
    current_columns = [
        "Date",
        "TestsTotalTests",
        "CasesTotalConfirmedPositiveCases",
        "CasesSeven7DayNumberper100000",
        "MortalityTotalDeaths",
    ]
    current_raw_rows = read_csv_rows(current_path, set(current_columns))
    current_prepared: list[tuple[str, dict[str, str]]] = []
    undated_raw_rows: list[str] = []
    for row in current_raw_rows:
        if not row["Date"]:
            undated_raw_rows.append(",".join(row[column] for column in current_columns))
            continue
        current_prepared.append((_iso_date(row["Date"], path=current_path, field="Date"), row))
    for raw_row in undated_raw_rows:
        warnings.append(f"covid current summary undated row raw values: {raw_row}")
    _add_check(checks, "covid_current_dated_rows", len(current_prepared), 1294)
    _add_check(checks, "covid_current_summary_undated_rows", len(undated_raw_rows), 1)
    current_tables: list[dict[str, Any]] = []
    for date_value, row in sorted(current_prepared):
        for measure, column, unit in _COVID_CURRENT_MEASURES:
            value, reporting_status, upper_bound = parse_published_value(
                row[column], path=current_path, field=column
            )
            current_tables.append(
                {
                    **context.provenance(
                        current_source,
                        locator=f"csv_row_{date_value}_col_{column}",
                        transformation_id="csv_covid_current_summary_long_v1",
                    ),
                    "date": date_value,
                    "measure": measure,
                    "value": value,
                    "unit": unit,
                    "reporting_status": reporting_status,
                    "upper_bound": upper_bound,
                }
            )
    daily_final = next(
        row
        for row in daily_tables
        if row["date"] == "2023-02-01" and row["measure"] == "cumulative_confirmed_cases"
    )
    current_final = next(
        row
        for row in current_tables
        if row["date"] == "2023-02-01" and row["measure"] == "cumulative_confirmed_cases"
    )
    if daily_final["value"] is None or current_final["value"] is None:
        raise DataBuildError("COVID final cumulative cases cross-check has no published value")
    _add_check(
        checks,
        "covid_final_cumulative_cases_daily_vs_current",
        daily_final["value"],
        current_final["value"],
        tolerance=0,
        warning=True,
    )

    weekly_source = "covid19_weekly_vaccination_csv"
    weekly_path = context.artifact_path(weekly_source)
    weekly_raw_rows = read_csv_rows(weekly_path, {"Date", "EligiblePopulation"})
    if not weekly_raw_rows:
        raise DataBuildError(f"{weekly_path}: no weekly vaccination rows")
    weekly_columns = list(weekly_raw_rows[0])
    vaccination_specs: list[tuple[str, tuple[str, str, str]]] = []
    for column in weekly_columns:
        if column == "Date" or column in _VACCINATION_EXCLUSIONS:
            continue
        vaccination_specs.append((column, _vaccination_column_spec(column, weekly_path)))
    _add_check(
        checks,
        "covid_weekly_columns_mapped_or_excluded",
        1 + len(vaccination_specs) + len(_VACCINATION_EXCLUSIONS.intersection(weekly_columns)),
        155,
    )
    weekly_prepared = [
        (_iso_date(row["Date"], path=weekly_path, field="Date"), row) for row in weekly_raw_rows
    ]
    weekly_tables: list[dict[str, Any]] = []
    eligible_tables: list[dict[str, Any]] = []
    for week_ending, row in sorted(weekly_prepared):
        eligible_value, eligible_status, eligible_upper_bound = parse_published_value(
            row["EligiblePopulation"], path=weekly_path, field="EligiblePopulation"
        )
        if isinstance(eligible_value, float):
            if not eligible_value.is_integer():
                raise DataBuildError(f"{weekly_path}: non-integer EligiblePopulation")
            eligible_value = int(eligible_value)
        eligible_tables.append(
            {
                **context.provenance(
                    weekly_source,
                    locator=f"csv_row_{week_ending}_col_EligiblePopulation",
                    transformation_id="csv_covid_weekly_eligible_population_v1",
                ),
                "week_ending": week_ending,
                "value": eligible_value,
                "unit": "persons",
                "reporting_status": eligible_status,
                "upper_bound": eligible_upper_bound,
            }
        )
        for column, (dose, age_band, metric) in vaccination_specs:
            value, reporting_status, upper_bound = parse_published_value(
                row[column], path=weekly_path, field=column
            )
            weekly_tables.append(
                {
                    **context.provenance(
                        weekly_source,
                        locator=f"csv_row_{week_ending}_col_{column}",
                        transformation_id="csv_covid_weekly_vaccination_long_v1",
                    ),
                    "week_ending": week_ending,
                    "dose": dose,
                    "age_band": age_band,
                    "metric": metric,
                    "value": value,
                    "reporting_status": reporting_status,
                    "upper_bound": upper_bound,
                }
            )
    _add_check(checks, "covid_weekly_rows", len(weekly_raw_rows), 132)
    warnings.append(
        "vaccination percentages are publisher-computed against an unstated denominator "
        "per band; not recomputed here"
    )

    serosurvey_source = "sars_cov2_serosurvey_2020_manual_fixture"
    serosurvey_path = context.artifact_path(serosurvey_source)
    serosurvey_columns = {
        "measure",
        "value",
        "unit",
        "population",
        "reference_period",
        "source_locator",
        "note",
    }
    serosurvey_raw_rows = read_csv_rows(serosurvey_path, serosurvey_columns)
    actual_measures = [_required(row, "measure", serosurvey_path) for row in serosurvey_raw_rows]
    if len(actual_measures) != len(_SEROSURVEY_MEASURES) or set(actual_measures) != set(
        _SEROSURVEY_MEASURES
    ):
        raise DataBuildError(
            f"{serosurvey_path}: fixture measures do not match the canonical measure list"
        )
    serosurvey_tables: list[dict[str, Any]] = []
    for row in serosurvey_raw_rows:
        serosurvey_tables.append(
            {
                **_provenance(
                    context,
                    serosurvey_source,
                    row,
                    "manual_pdf_transcription_v1",
                ),
                "measure": _required(row, "measure", serosurvey_path),
                "value": parse_number(row["value"], path=serosurvey_path, field="value"),
                "unit": _required(row, "unit", serosurvey_path),
                "population": _required(row, "population", serosurvey_path),
                "note": _required(row, "note", serosurvey_path),
            }
        )
    _add_check(checks, "covid_serosurvey_measures", len(serosurvey_tables), 13)
    jhu_tables = _covid_jhu_tables(context, checks, daily_tables, warnings)

    return {
        "covid_daily_surveillance": daily_tables,
        "covid_current_summary": current_tables,
        "covid_weekly_vaccination": weekly_tables,
        "covid_serosurvey_2020": serosurvey_tables,
        "covid_weekly_eligible_population": eligible_tables,
        "covid_jhu_daily": jhu_tables,
        "covid_warnings": warnings,
    }


def _population_tables(
    context: SourceContext, checks: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    population_source = "jersey_population_2024_manual_fixture"
    population_path, population_rows = _manual_rows(context, population_source)
    population_totals: list[dict[str, Any]] = []
    age_sex: list[dict[str, Any]] = []
    by_measure: dict[str, dict[str, str]] = {}
    for row in population_rows:
        measure = _required(row, "measure", population_path)
        value = parse_number(row["value"], path=population_path, field="value")
        if value is None:
            raise DataBuildError(f"{population_path}: population value cannot be blank")
        population_totals.append(
            {
                **_provenance(context, population_source, row, "manual_pdf_transcription_v1"),
                "measure": measure,
                "value": value,
                "unit": _required(row, "unit", population_path),
            }
        )
        by_measure[measure] = row
    broad_age = {
        "age_under_16": "under_16",
        "age_16_to_64": "16_to_64",
        "age_65_plus": "65_plus",
    }
    for measure, age_band in broad_age.items():
        row = by_measure[measure]
        age_sex.append(
            {
                **_provenance(context, population_source, row, "manual_pdf_transcription_v1"),
                "age_band": age_band,
                "sex": "all",
                "count": parse_int(row["value"], path=population_path, field="value"),
            }
        )
    for measure, sex in (("sex_male", "male"), ("sex_female", "female")):
        row = by_measure[measure]
        age_sex.append(
            {
                **_provenance(context, population_source, row, "manual_pdf_transcription_v1"),
                "age_band": "all",
                "sex": sex,
                "count": parse_int(row["value"], path=population_path, field="value"),
            }
        )

    age_source = "census_2021_age_gender_csv"
    age_path = context.artifact_path(age_source)
    for row in read_csv_rows(age_path, {"Age", "Male", "Female", "All"}):
        age_band = _required(row, "Age", age_path)
        for column, sex in (("Male", "male"), ("Female", "female"), ("All", "all")):
            age_sex.append(
                {
                    **context.provenance(
                        age_source,
                        locator=f"csv_age_{age_band}",
                        transformation_id="csv_age_gender_long_v1",
                    ),
                    "age_band": age_band,
                    "sex": sex,
                    "count": parse_int(row[column], path=age_path, field=column),
                }
            )
    age_all_total = sum(
        row["count"] for row in age_sex if row["source_id"] == age_source and row["sex"] == "all"
    )
    parish_source = "census_2021_parish_population_density_csv"
    parish_path = context.artifact_path(parish_source)
    parish_rows = read_csv_rows(
        parish_path, {"Parish", "2021 population", "2021 density (person/km2)"}
    )
    parish_population: list[dict[str, Any]] = []
    parish_total = 0
    for row in parish_rows:
        parish = _required(row, "Parish", parish_path)
        population = parse_int(row["2021 population"], path=parish_path, field="2021 population")
        density = parse_number(
            row["2021 density (person/km2)"],
            path=parish_path,
            field="2021 density (person/km2)",
        )
        if parish == "TOTAL":
            if population is None:
                raise DataBuildError(f"{parish_path}: TOTAL population is blank")
            parish_total = population
            population_totals.append(
                {
                    **context.provenance(
                        parish_source,
                        locator="csv_TOTAL",
                        transformation_id="csv_parish_total_v1",
                    ),
                    "measure": "population_total",
                    "value": population,
                    "unit": "people",
                }
            )
            continue
        if population is None or density is None:
            raise DataBuildError(f"{parish_path}: parish population and density cannot be blank")
        parish_total += population
        parish_population.append(
            {
                **context.provenance(
                    parish_source,
                    locator=f"csv_{_slug(parish)}",
                    transformation_id="csv_parish_population_v1",
                ),
                "parish": parish,
                "population": population,
                "density_person_km2": density,
            }
        )
    expected_parish_total = next(
        row["value"]
        for row in population_totals
        if row["source_id"] == parish_source and row["measure"] == "population_total"
    )
    _add_check(checks, "parish_population_sum", parish_total, expected_parish_total)
    _add_check(checks, "2021_age_gender_sum", age_all_total, expected_parish_total)
    broad_total = sum(
        row["count"]
        for row in age_sex
        if row["source_id"] == population_source and row["sex"] == "all"
    )
    broad_expected = next(
        row["value"]
        for row in population_totals
        if row["source_id"] == population_source and row["measure"] == "population_total"
    )
    _add_check(checks, "2024_broad_age_sum", broad_total, broad_expected)
    sex_total = sum(
        row["count"]
        for row in age_sex
        if row["source_id"] == population_source and row["age_band"] == "all"
    )
    _add_check(checks, "2024_sex_sum", sex_total, broad_expected)

    parish_age_source = "census_2021_parish_age_sex_csv"
    parish_age_path = context.artifact_path(parish_age_source)
    parish_age_sex: list[dict[str, Any]] = []
    parish_age_rows = read_csv_rows(parish_age_path, {"Parish", "Sex", "All"})
    for row in parish_age_rows:
        parish = _required(row, "Parish", parish_age_path)
        sex = _required(row, "Sex", parish_age_path).lower()
        for column in (
            "< 5",
            "5 - 9",
            "10 - 14",
            "15 - 19",
            "20 - 24",
            "25 - 29",
            "30 - 34",
            "35 - 39",
            "40 - 44",
            "45 - 49",
            "50 - 54",
            "55 - 59",
            "60 - 64",
            "65 - 69",
            "70 - 74",
            "75 - 79",
            "80+",
            "All",
        ):
            if column not in row:
                continue
            parish_age_sex.append(
                {
                    **context.provenance(
                        parish_age_source,
                        locator=f"csv_{_slug(parish)}_{_slug(sex)}",
                        transformation_id="csv_parish_age_sex_long_v1",
                    ),
                    "parish": parish,
                    "age_band": column.replace(" ", ""),
                    "sex": sex,
                    "count": parse_int(row[column], path=parish_age_path, field=column),
                }
            )
    return {
        "population_totals": population_totals,
        "age_sex": age_sex,
        "parish_population": parish_population,
        "parish_age_sex": parish_age_sex,
    }


def _household_and_housing_tables(
    context: SourceContext,
    checks: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    manual_source = "census_2021_report_manual_fixture"
    manual_path, manual_rows = _manual_rows(context, manual_source)
    household_types: list[dict[str, Any]] = []
    communal: list[dict[str, Any]] = []
    housing: list[dict[str, Any]] = []
    destinations: list[dict[str, Any]] = []
    household_total = 0
    household_expected = 0
    for row in manual_rows:
        measure = _required(row, "measure", manual_path)
        category = _required(row, "category", manual_path)
        value = parse_number(row["value"], path=manual_path, field="value")
        if value is None:
            raise DataBuildError(f"{manual_path}: manual control value cannot be blank")
        provenance = _provenance(context, manual_source, row, "manual_pdf_transcription_v1")
        if measure == "household_type":
            household_types.append(
                {**provenance, "household_type": category, "households": int(value)}
            )
            household_total += int(value)
        elif measure == "household_count":
            household_expected = int(value)
        elif measure.startswith("communal_"):
            communal.append(
                {
                    **provenance,
                    "measure": measure.removeprefix("communal_"),
                    "setting": category,
                    "value": int(value),
                    "unit": _required(row, "unit", manual_path),
                }
            )
        elif measure == "housing_control":
            housing.append(
                {
                    **provenance,
                    "measure": category,
                    "category": "report_control",
                    "subcategory": row.get("subcategory") or None,
                    "value": value,
                    "unit": _required(row, "unit", manual_path),
                }
            )
        elif measure == "workplace_destination":
            destinations.append(
                {
                    **provenance,
                    "measure": measure,
                    "category": category,
                    "subcategory": row.get("subcategory") or None,
                    "value": value,
                    "unit": _required(row, "unit", manual_path),
                }
            )
        else:
            raise DataBuildError(f"{manual_path}: unsupported manual measure {measure!r}")
    _add_check(checks, "household_type_sum", household_total, household_expected)

    tenure_source = "census_2021_household_type_tenure_csv"
    tenure_path = context.artifact_path(tenure_source)
    tenure_rows = read_csv_rows(tenure_path, {"Household type", "All"})
    tenure_columns = [
        "Owner Occupied",
        "Social Rental",
        "Qualified Rental",
        "Staff or service accom.",
        "Registered lodging house",
        "Private lodging",
        "Other non-qualified accom.",
    ]
    for row in tenure_rows:
        category = _required(row, "Household type", tenure_path)
        for tenure in tenure_columns:
            value = parse_number(
                row.get(tenure, ""), path=tenure_path, field=tenure, allow_blank=True
            )
            if value is None:
                continue
            housing.append(
                {
                    **context.provenance(
                        tenure_source,
                        locator=f"csv_{_slug(category)}_{_slug(tenure)}",
                        transformation_id="csv_household_tenure_long_v1",
                    ),
                    "measure": "households",
                    "category": "household_type",
                    "subcategory": f"{category} | {tenure}",
                    "value": value,
                    "unit": "households",
                }
            )
    property_source = "census_2021_household_property_type_csv"
    property_path = context.artifact_path(property_source)
    property_rows = read_csv_rows(property_path, {"Property Type"})
    property_columns = [
        "Owner-occupied",
        "Social housing rent",
        "Qualified private rent",
        "Non-qualified accommodation",
    ]
    for row in property_rows:
        category = _required(row, "Property Type", property_path)
        for tenure in property_columns:
            value = parse_number(
                row.get(tenure, ""), path=property_path, field=tenure, allow_blank=True
            )
            if value is None:
                continue
            housing.append(
                {
                    **context.provenance(
                        property_source,
                        locator=f"csv_{_slug(category)}_{_slug(tenure)}",
                        transformation_id="csv_property_type_long_v1",
                    ),
                    "measure": "households",
                    "category": "property_type",
                    "subcategory": f"{category} | {tenure}",
                    "value": value,
                    "unit": "households",
                }
            )
    bedrooms_source = "census_2021_housing_persons_bedrooms_csv"
    bedrooms_path = context.artifact_path(bedrooms_source)
    bedrooms_rows = read_csv_rows(bedrooms_path, {"Tenure", "Households", "Persons"})
    bedroom_fields = {
        "Households": ("households", "households"),
        "Persons": ("persons", "people"),
        "Mean persons per household": ("mean_persons_per_household", "persons_per_household"),
        "Mean bedroooms per household": ("mean_bedrooms_per_household", "bedrooms_per_household"),
        "Mean persons per bedroom": ("mean_persons_per_bedroom", "persons_per_bedroom"),
    }
    for row in bedrooms_rows:
        category = _required(row, "Tenure", bedrooms_path)
        for field, (measure, unit) in bedroom_fields.items():
            value = parse_number(row.get(field, ""), path=bedrooms_path, field=field)
            if value is None:
                raise DataBuildError(f"{bedrooms_path}: blank {field}")
            housing.append(
                {
                    **context.provenance(
                        bedrooms_source,
                        locator=f"csv_{_slug(category)}_{_slug(field)}",
                        transformation_id="csv_bedroom_controls_long_v1",
                    ),
                    "measure": measure,
                    "category": "tenure",
                    "subcategory": category,
                    "value": value,
                    "unit": unit,
                }
            )
    overcrowding_source = "census_2021_overcrowding_csv"
    overcrowding_path = context.artifact_path(overcrowding_source)
    overcrowding_rows = read_csv_rows(overcrowding_path, {"Tenure", "2021"})
    for row in overcrowding_rows:
        category = _required(row, "Tenure", overcrowding_path)
        value = parse_number(row["2021"], path=overcrowding_path, field="2021")
        if value is None:
            raise DataBuildError(f"{overcrowding_path}: blank 2021 value")
        housing.append(
            {
                **context.provenance(
                    overcrowding_source,
                    locator=f"csv_{_slug(category)}_2021",
                    transformation_id="csv_overcrowding_2021_v1",
                ),
                "measure": "overcrowded_households",
                "category": "tenure",
                "subcategory": category,
                "value": value,
                "unit": "percent",
            }
        )
    return {
        "household_types": household_types,
        "communal_settings": communal,
        "housing_controls": housing,
        "workplace_destination": destinations,
    }


def _employment_and_workplace_tables(
    context: SourceContext,
    checks: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    employment: list[dict[str, Any]] = []
    employment_source = "census_2021_industry_sex_csv"
    employment_path = context.artifact_path(employment_source)
    employment_rows = read_csv_rows(employment_path, {"Sector", "Males", "Females", "All"})
    for row in employment_rows:
        sector = _required(row, "Sector", employment_path)
        for column, sex in (("Males", "male"), ("Females", "female"), ("All", "all")):
            value = parse_number(row[column], path=employment_path, field=column)
            if value is None:
                raise DataBuildError(f"{employment_path}: blank {column}")
            employment.append(
                {
                    **context.provenance(
                        employment_source,
                        locator=f"csv_{_slug(sector)}_{sex}",
                        transformation_id="csv_industry_sex_long_v1",
                    ),
                    "measure": "resident_workers",
                    "sector": sector,
                    "sex": sex,
                    "value": value,
                    "unit": "people",
                }
            )
    all_total = next(
        row["value"] for row in employment if row["sector"] == "All" and row["sex"] == "all"
    )
    sector_sum = sum(
        row["value"] for row in employment if row["sex"] == "all" and row["sector"] != "All"
    )
    _add_check(checks, "2021_employment_sector_sum", sector_sum, all_total)

    manual_source = "labour_market_june_2025_manual_fixture"
    manual_path, manual_rows = _manual_rows(context, manual_source)
    workplace_sizes: list[dict[str, Any]] = []
    labour_sector_total = 0
    labour_sector_expected = 0
    workplace_total: dict[str, int] = {}
    for row in manual_rows:
        measure = _required(row, "measure", manual_path)
        category = _required(row, "sector", manual_path)
        if measure == "sector_jobs":
            value = parse_int(row["value"], path=manual_path, field="value")
            if value is None:
                raise DataBuildError(f"{manual_path}: blank sector job value")
            employment.append(
                {
                    **_provenance(context, manual_source, row, "manual_pdf_transcription_v1"),
                    "measure": "jobs",
                    "sector": category,
                    "sex": None,
                    "value": value,
                    "unit": "jobs",
                }
            )
            if category == "Private sector":
                labour_sector_expected = value
            else:
                labour_sector_total += value
        elif measure == "workplace_size":
            size_band = _required(row, "size_band", manual_path)
            count = parse_int(
                row.get("value", ""), path=manual_path, field="value", allow_blank=True
            )
            upper_bound = parse_int(
                row.get("upper_bound", ""), path=manual_path, field="upper_bound", allow_blank=True
            )
            censoring = _required(row, "censoring", manual_path) if count is None else "exact"
            workplace_sizes.append(
                {
                    **_provenance(context, manual_source, row, "manual_pdf_transcription_v1"),
                    "sector": category,
                    "size_band": size_band,
                    "count": count,
                    "upper_bound": upper_bound,
                    "censoring": censoring,
                    "unit": _required(row, "unit", manual_path),
                }
            )
            if category == "Total private sector undertakings" and count is not None:
                workplace_total[size_band] = count
        else:
            raise DataBuildError(f"{manual_path}: unsupported labour measure {measure!r}")
    _add_check(
        checks,
        "2025_private_sector_jobs_sum",
        labour_sector_total,
        labour_sector_expected,
        tolerance=10,
        warning=True,
    )
    workplace_sum = sum(workplace_total.values())
    _add_check(checks, "2025_workplace_size_band_sum", workplace_sum, 8500)
    return {"employment_sectors": employment, "workplace_sizes": workplace_sizes}


def _commute_education_arrivals_tables(
    context: SourceContext,
    checks: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    commute_source = "census_2021_commute_mode_csv"
    commute_path = context.artifact_path(commute_source)
    commute_rows = read_csv_rows(commute_path, {"Parish", "All"})
    commute: list[dict[str, Any]] = []
    commute_columns = {
        "Car": "car",
        "Motorbike": "motorbike",
        "Walk": "walk",
        "Bus": "bus",
        "Cycle": "cycle",
        "Work from home": "work_from_home",
        "Other": "other",
    }
    published_all = 0
    for row in commute_rows:
        parish = _normalize_parish(_required(row, "Parish", commute_path))
        all_value = parse_int(row["All"], path=commute_path, field="All")
        if all_value is None:
            raise DataBuildError(f"{commute_path}: blank All value")
        if parish == "All Parishes":
            published_all = all_value
        for source_column, mode in commute_columns.items():
            value = parse_int(
                row.get(source_column, ""),
                path=commute_path,
                field=source_column,
                allow_blank=True,
            )
            commute.append(
                {
                    **context.provenance(
                        commute_source,
                        locator=f"csv_{_slug(parish)}_{mode}",
                        transformation_id="csv_commute_mode_long_v1",
                    ),
                    "parish": parish,
                    "mode": mode,
                    "workers": value,
                    "upper_bound": 10 if value is None else None,
                    "censoring": "positive_less_than" if value is None else "exact",
                }
            )
    all_mode_sum = sum(row["workers"] or 0 for row in commute if row["parish"] == "All Parishes")
    commute_status = _add_check(checks, "2021_commute_mode_sum", all_mode_sum, published_all)
    _add_check(
        checks,
        "2021_commute_report_rounding_difference",
        published_all,
        57338,
        tolerance=10,
        warning=True,
    )

    student_source = "education_students_by_school_type_csv"
    student_path = context.artifact_path(student_source)
    student_rows = read_csv_rows(student_path, {"Year", "Total"})
    student_row = next((row for row in student_rows if row.get("Year") == "2024"), None)
    if student_row is None:
        raise DataBuildError(f"{student_path}: required Year=2024 row is missing")
    students: list[dict[str, Any]] = []
    student_columns = [
        "Government primary",
        "Non-provided primary",
        "Government secondary",
        "Non-provided secondary",
        "Special school",
        "Total",
    ]
    student_total = 0
    for column in student_columns:
        value = parse_int(student_row[column], path=student_path, field=column)
        if value is None:
            raise DataBuildError(f"{student_path}: blank student value in {column}")
        students.append(
            {
                **context.provenance(
                    student_source,
                    locator="csv_2024",
                    transformation_id="csv_students_2024_long_v1",
                ),
                "year": 2024,
                "school_type": column,
                "students": value,
            }
        )
        if column != "Total":
            student_total += value
        else:
            student_expected = value
    _add_check(checks, "2024_student_components_sum", student_total, student_expected)

    arrivals_source = "passenger_arrivals_total_csv"
    arrivals_path = context.artifact_path(arrivals_source)
    arrivals_rows = read_csv_rows(
        arrivals_path, {"Year", "Sea arrivals", "Air arrivals", "Total arrivals"}
    )
    arrivals_row = next((row for row in arrivals_rows if row.get("Year") == "2025"), None)
    if arrivals_row is None:
        raise DataBuildError(f"{arrivals_path}: required Year=2025 row is missing")
    arrivals: list[dict[str, Any]] = []
    arrival_columns = [
        ("Sea arrivals", "sea"),
        ("Air arrivals", "air"),
        ("Total arrivals", "total"),
    ]
    arrival_values: dict[str, int] = {}
    for column, mode in arrival_columns:
        value = parse_int(arrivals_row[column], path=arrivals_path, field=column)
        if value is None:
            raise DataBuildError(f"{arrivals_path}: blank arrival value in {column}")
        arrival_values[mode] = value
        arrivals.append(
            {
                **context.provenance(
                    arrivals_source,
                    locator="csv_2025",
                    transformation_id="csv_arrivals_2025_long_v1",
                ),
                "year": 2025,
                "mode": mode,
                "passengers": value,
            }
        )
    _add_check(
        checks,
        "2025_arrivals_components_sum",
        arrival_values["sea"] + arrival_values["air"],
        arrival_values["total"],
    )
    return {
        "commute_modes": commute,
        "school_students": students,
        "passenger_arrivals": arrivals,
        "commute_rounding_status": [{"status": commute_status}],
    }


def _derived_controls(
    context: SourceContext,
    tables: dict[str, list[dict[str, Any]]],
    checks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    derived: list[dict[str, Any]] = []

    def add(
        source_id: str,
        *,
        measure: str,
        category: str,
        value: int | float,
        unit: str,
        reference: str,
        source_table: str,
        check_status: str = "passed",
    ) -> None:
        derived.append(
            {
                **context.provenance(
                    source_id,
                    locator="derived_from_canonical_tables",
                    transformation_id="canonical_derived_controls_v1",
                    observation_status="derived",
                ),
                "measure": measure,
                "category": category,
                "value": value,
                "unit": unit,
                "reference": reference,
                "source_table": source_table,
                "check_status": check_status,
            }
        )

    parish_total = next(
        row["value"]
        for row in tables["population_totals"]
        if row["source_id"] == "census_2021_parish_population_density_csv"
        and row["measure"] == "population_total"
    )
    for row in tables["parish_population"]:
        add(
            "census_2021_parish_population_density_csv",
            measure="population_share",
            category=row["parish"],
            value=row["population"] / parish_total,
            unit="proportion",
            reference="2021 parish population total",
            source_table="parish_population.csv",
        )
    household_total = next(
        row["value"]
        for row in tables["housing_controls"]
        if row["source_id"] == "census_2021_report_manual_fixture"
        and row["measure"] == "occupied_private_dwellings"
    )
    for row in tables["household_types"]:
        add(
            "census_2021_report_manual_fixture",
            measure="household_type_share",
            category=row["household_type"],
            value=row["households"] / household_total,
            unit="proportion",
            reference="2021 private household total",
            source_table="household_types.csv",
        )
    all_commute = [row for row in tables["commute_modes"] if row["parish"] == "All Parishes"]
    commute_total = sum(row["workers"] or 0 for row in all_commute)
    for row in all_commute:
        if row["workers"] is None:
            continue
        add(
            "census_2021_commute_mode_csv",
            measure="commute_mode_share",
            category=row["mode"],
            value=row["workers"] / commute_total,
            unit="proportion",
            reference="2021 all-parish published mode total",
            source_table="commute_modes.csv",
            check_status="warning" if commute_total != 57338 else "passed",
        )
    student_total = next(
        row["students"] for row in tables["school_students"] if row["school_type"] == "Total"
    )
    for row in tables["school_students"]:
        if row["school_type"] == "Total":
            continue
        add(
            "education_students_by_school_type_csv",
            measure="student_type_share",
            category=row["school_type"],
            value=row["students"] / student_total,
            unit="proportion",
            reference="2024 student total",
            source_table="school_students.csv",
        )
    arrival_total = next(
        row["passengers"] for row in tables["passenger_arrivals"] if row["mode"] == "total"
    )
    add(
        "passenger_arrivals_total_csv",
        measure="average_daily_arrivals",
        category="2025 total",
        value=arrival_total / 365,
        unit="passengers_per_day",
        reference="2025 total arrivals divided by 365",
        source_table="passenger_arrivals.csv",
    )
    derived.append(
        {
            **context.provenance(
                "census_2021_housing_persons_bedrooms_csv",
                locator="derived_source_quality_conflict",
                transformation_id="source_quality_diagnostic_v1",
                observation_status="derived",
            ),
            "measure": "mean_bedrooms_conflict",
            "category": "all_households",
            "value": 0.10,
            "unit": "bedrooms_difference",
            "reference": "report 2.47 versus CSV 2.57; report value used in manual controls",
            "source_table": "housing_controls.csv",
            "check_status": "warning",
        }
    )
    checks.append(
        {
            "name": "housing_mean_bedrooms_source_conflict",
            "status": "warning",
            "actual": 2.57,
            "expected": 2.47,
            "difference": 0.10,
            "tolerance": 0,
            "details": "conflict is retained as a quality warning; no silent normalization",
        }
    )
    return derived


def build_canonical(root: Path, output_dir: Path | None = None) -> dict[str, Any]:
    """Validate sources and deterministically rebuild all Milestone 1 tables."""

    root = root.resolve()
    context = load_source_registry(root)
    destination = output_dir or root / "data" / "processed"
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, Any]] = []
    tables: dict[str, list[dict[str, Any]]] = {}
    tables.update(_population_tables(context, checks))
    tables.update(_household_and_housing_tables(context, checks))
    tables.update(_employment_and_workplace_tables(context, checks))
    tables.update(_commute_education_arrivals_tables(context, checks))
    tables["population_estimates_annual"] = _population_estimate_table(context, checks)
    covid_tables = _covid_tables(context, checks)
    covid_warnings = covid_tables.pop("covid_warnings")
    tables.update(covid_tables)
    tables.pop("commute_rounding_status", None)
    tables["derived_controls"] = _derived_controls(context, tables, checks)

    table_models: dict[str, tuple[str, type[CanonicalProvenance]]] = {
        "population_totals": ("population_totals.csv", PopulationTotalRow),
        "age_sex": ("age_sex.csv", AgeSexRow),
        "parish_population": ("parish_population.csv", ParishPopulationRow),
        "parish_age_sex": ("parish_age_sex.csv", ParishAgeSexRow),
        "household_types": ("household_types.csv", HouseholdTypeRow),
        "housing_controls": ("housing_controls.csv", MeasureRow),
        "employment_sectors": ("employment_sectors.csv", EmploymentSectorRow),
        "workplace_sizes": ("workplace_sizes.csv", WorkplaceSizeRow),
        "workplace_destination": ("workplace_destination.csv", WorkplaceDestinationRow),
        "commute_modes": ("commute_modes.csv", CommuteModeRow),
        "school_students": ("school_students.csv", SchoolStudentRow),
        "communal_settings": ("communal_settings.csv", CommunalSettingRow),
        "passenger_arrivals": ("passenger_arrivals.csv", PassengerArrivalRow),
        "derived_controls": ("derived_controls.csv", DerivedControlRow),
        "covid_daily_surveillance": ("covid_daily_surveillance.csv", CovidDailySurveillanceRow),
        "covid_current_summary": ("covid_current_summary.csv", CovidCurrentSummaryRow),
        "covid_weekly_vaccination": ("covid_weekly_vaccination.csv", CovidWeeklyVaccinationRow),
        "covid_serosurvey_2020": ("covid_serosurvey_2020.csv", CovidSerosurveyRow),
        "covid_weekly_eligible_population": (
            "covid_weekly_eligible_population.csv",
            CovidWeeklyEligiblePopulationRow,
        ),
        "covid_jhu_daily": ("covid_jhu_daily.csv", CovidJhuDailyRow),
        "population_estimates_annual": (
            "population_estimates_annual.csv",
            PopulationEstimateAnnualRow,
        ),
    }
    table_manifest: list[dict[str, Any]] = []
    for table_name, (filename, model) in table_models.items():
        table_manifest.append(_write_table(destination, filename, model, tables[table_name]))
    manifest_path = destination / "table_manifest.json"
    manifest_payload = {"schema_version": "1.0", "tables": table_manifest}
    manifest_path.write_text(
        json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    source_checks = validate_source_snapshots(context)
    warnings = [
        (
            "2024 population source provides broad age bands and broad sex totals; "
            "detailed 2024 age-by-sex is not inferred from 2021 data."
        ),
        (
            "2021 commuting and workplace-destination controls describe the census "
            "reference period and include pandemic-era work-from-home effects."
        ),
        (
            "The 2025 labour-market sector values are jobs, not unique employees; "
            "they are not reconciled to 2021 resident workers."
        ),
        (
            "The housing CSV all-row mean bedrooms value (2.57) conflicts with the "
            "official report value (2.47); the report value is the canonical manual "
            "control and the conflict is flagged."
        ),
        (
            "Published CSV tables include rounded counts and suppressed small cells "
            "in places; raw values and suppression notes are preserved rather than imputed."
        ),
        "annual population estimates are published rounded to the nearest 10; sums are not exact",
    ]
    warnings.extend(covid_warnings)
    quality_report = {
        "schema_version": "1.0",
        "build_status": "passed",
        "source_registry": "data/sources.yaml",
        "sources": source_checks,
        "tables": table_manifest,
        "checks": checks,
        "warnings": warnings,
        "pipeline": [
            "immutable raw snapshot",
            "source-specific CSV/PDF extraction",
            "canonical long-form aggregate table",
            "validation and reconciliation",
            "derived controls and data-quality report",
        ],
    }
    report_json_path = destination / "quality_report.json"
    report_json_path.write_text(
        json.dumps(quality_report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report_md_path = destination / "quality_report.md"
    report_md_path.write_text(_quality_report_markdown(quality_report), encoding="utf-8")
    return quality_report


def _quality_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Milestone 1 data-quality report",
        "",
        f"Build status: **{report['build_status']}**",
        "",
        "## Source snapshots",
        "",
        "| Source | Status | Acquisition | SHA-256 | Snapshot |",
        "|---|---|---|---|---|",
    ]
    for source in report["sources"]:
        lines.append(
            f"| {source['source_id']} | {source['status']} | "
            f"{source.get('acquisition_method', '')} | {source.get('sha256', '')} | "
            f"{source.get('local_snapshot', '')} |"
        )
    lines.extend(["", "## Canonical tables", "", "| Table | Rows | SHA-256 |", "|---|---:|---|"])
    for table in report["tables"]:
        lines.append(f"| {table['path']} | {table['rows']} | {table['sha256']} |")
    lines.extend(["", "## Validation and reconciliation", ""])
    for check in report["checks"]:
        detail = check.get("details", "")
        detail_suffix = f" {detail}" if detail else ""
        lines.append(
            f"- **{check['status']}** `{check['name']}`: "
            f"actual={check.get('actual', '')}, expected={check.get('expected', '')}, "
            f"difference={check.get('difference', '')}.{detail_suffix}"
        )
    lines.extend(["", "## Pipeline", ""])
    for stage in report["pipeline"]:
        lines.append(f"1. {stage}")
    lines.extend(["", "## Limitations and evidence notes", ""])
    for warning in report["warnings"]:
        lines.append(f"- {warning}")
    lines.append("")
    return "\n".join(lines)
