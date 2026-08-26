"""Milestone 2 control loading and transparent integer allocation helpers."""

from __future__ import annotations

import json
import math
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .data_pipeline import (
    DataBuildError,
    load_source_registry,
    parse_int,
    parse_number,
    read_csv_rows,
)
from .hashing import sha256_file


@dataclass(frozen=True)
class CommunalControl:
    setting_type: str
    establishments: int
    residents: int


@dataclass(frozen=True)
class PopulationControls:
    full_population_target: int
    census_population_reference: int
    full_age_sex_counts: dict[tuple[int, str], int]
    full_age_band_targets: dict[str, int]
    full_sex_targets: dict[str, int]
    parish_counts: dict[str, int]
    household_type_counts: dict[str, int]
    private_households_reference: int
    private_residents_reference: int
    communal_residents_reference: int
    communal_establishments_reference: int
    communal_categories: tuple[CommunalControl, ...]
    housing_controls: dict[str, float]
    canonical_hashes: dict[str, str]
    source_manifest_hash: str
    assumptions: tuple[str, ...]


def allocate_proportional(total: int, weights: dict[str, int | float]) -> dict[str, int]:
    """Allocate an integer total by Hamilton/largest-remainder allocation.

    Ties use the supplied insertion order, so aggregate allocation is stable
    and does not depend on a global random state.
    """

    if total < 0:
        raise DataBuildError("allocation total must be non-negative")
    if not weights:
        raise DataBuildError("allocation requires at least one category")
    numeric = {key: float(value) for key, value in weights.items()}
    if any(value < 0 for value in numeric.values()) or not any(numeric.values()):
        raise DataBuildError("allocation weights must be non-negative and not all zero")
    denominator = sum(numeric.values())
    quotas = {key: total * value / denominator for key, value in numeric.items()}
    allocation = {key: math.floor(quota) for key, quota in quotas.items()}
    remainder = total - sum(allocation.values())
    ranked = sorted(
        quotas,
        key=lambda key: (-(quotas[key] - allocation[key]), list(quotas).index(key)),
    )
    for key in ranked[:remainder]:
        allocation[key] += 1
    if sum(allocation.values()) != total:
        raise DataBuildError("integer allocation failed to reconcile")
    return allocation


def scale_counts(counts: dict[str, int], total: int) -> dict[str, int]:
    """Scale a count distribution to a mode target with exact integer sum."""

    return allocate_proportional(total, counts)


def _age_value(value: str) -> int:
    token = value.strip()
    if token == "95+":
        return 95
    try:
        age = int(token)
    except ValueError as exc:
        raise DataBuildError(f"invalid age band in canonical table: {value!r}") from exc
    if not 0 <= age <= 95:
        raise DataBuildError(f"age outside supported 0-95 range: {value!r}")
    return age


def _age_band(age: int) -> str:
    if age < 16:
        return "under_16"
    if age < 65:
        return "16_to_64"
    return "65_plus"


def _read_canonical_table(root: Path, filename: str, required: set[str]) -> list[dict[str, str]]:
    return read_csv_rows(root / "data" / "processed" / filename, required)


def _validate_canonical_inputs(root: Path) -> dict[str, str]:
    manifest_path = root / "data" / "processed" / "table_manifest.json"
    quality_path = root / "data" / "processed" / "quality_report.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        quality = json.loads(quality_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DataBuildError(f"cannot read Milestone 1 canonical manifests: {exc}") from exc
    if not isinstance(manifest, dict) or not isinstance(quality, dict):
        raise DataBuildError("Milestone 1 canonical manifests must contain JSON objects")
    if quality.get("build_status") != "passed":
        raise DataBuildError("Milestone 1 quality report is not passed")
    tables = manifest.get("tables")
    if not isinstance(tables, list):
        raise DataBuildError("canonical table manifest must contain a tables list")
    hashes: dict[str, str] = {}
    for table in tables:
        if not isinstance(table, dict):
            raise DataBuildError("canonical table manifest contains a malformed table entry")
        path_value = table.get("path")
        expected = table.get("sha256")
        if not isinstance(path_value, str) or not isinstance(expected, str):
            raise DataBuildError("canonical table manifest has malformed path or hash")
        path = root / path_value
        if not path.is_file():
            raise DataBuildError(f"canonical table is missing: {path}")
        actual = sha256_file(path)
        if actual != expected:
            raise DataBuildError(f"canonical table hash mismatch: {path}")
        hashes[path_value] = actual
    if not hashes:
        raise DataBuildError("canonical table manifest is empty")
    return hashes


def _find_value(
    rows: Iterable[dict[str, str]], measure: str, *, source_id: str | None = None
) -> float:
    for row in rows:
        if row.get("measure") == measure and (
            source_id is None or row.get("source_id") == source_id
        ):
            value = parse_number(row.get("value", ""), path=Path("canonical table"), field="value")
            if value is None:
                break
            return float(value)
    raise DataBuildError(f"canonical control not found: {measure}")


def _integer_value(row: dict[str, str], field: str) -> int:
    value = parse_int(row.get(field, ""), path=Path("canonical table"), field=field)
    if value is None:
        raise DataBuildError(f"blank integer control: {field}")
    return value


def _build_full_age_sex_counts(
    detailed: dict[tuple[int, str], int],
    age_targets: dict[str, int],
    sex_targets: dict[str, int],
) -> dict[tuple[int, str], int]:
    """Rake 2021 detailed age/sex shape to 2024 broad age and sex marginals."""

    bands = ("under_16", "16_to_64", "65_plus")
    sexes = ("male", "female")
    band_weights = {
        band: {
            sex: sum(
                count
                for (age, cell_sex), count in detailed.items()
                if _age_band(age) == band and cell_sex == sex
            )
            for sex in sexes
        }
        for band in bands
    }
    matrix = {band: {sex: float(band_weights[band][sex]) for sex in sexes} for band in bands}
    for _ in range(100):
        for band in bands:
            row_total = sum(matrix[band].values())
            if row_total <= 0:
                raise DataBuildError(f"no detailed age/sex weight for {band}")
            for sex in sexes:
                matrix[band][sex] *= age_targets[band] / row_total
        for sex in sexes:
            column_total = sum(matrix[band][sex] for band in bands)
            if column_total <= 0:
                raise DataBuildError(f"no detailed age/sex weight for {sex}")
            for band in bands:
                matrix[band][sex] *= sex_targets[sex] / column_total
    cell_targets: dict[tuple[str, str], int] = {}
    for band in bands:
        male_count = allocate_proportional(
            age_targets[band], {sex: matrix[band][sex] for sex in sexes}
        )["male"]
        cell_targets[(band, "male")] = male_count
        cell_targets[(band, "female")] = age_targets[band] - male_count
    if any(sum(cell_targets[(band, sex)] for band in bands) != sex_targets[sex] for sex in sexes):
        raise DataBuildError("raked age/sex table failed to reconcile sex margins")

    result: dict[tuple[int, str], int] = {}
    for band in bands:
        for sex in sexes:
            weights = {
                str(age): count
                for (age, cell_sex), count in detailed.items()
                if _age_band(age) == band and cell_sex == sex
            }
            allocated = allocate_proportional(cell_targets[(band, sex)], weights)
            result.update({(int(age), sex): count for age, count in allocated.items()})
    if sum(result.values()) != sum(age_targets.values()):
        raise DataBuildError("raked age/sex table failed to reconcile total population")
    return result


def load_population_controls(root: Path) -> PopulationControls:
    """Load and validate the Milestone 1 controls required by Milestone 2."""

    root = root.resolve()
    load_source_registry(root)
    canonical_hashes = _validate_canonical_inputs(root)
    population_rows = _read_canonical_table(
        root,
        "population_totals.csv",
        {"source_id", "measure", "value"},
    )
    full_population_target = int(
        _find_value(
            population_rows, "population_total", source_id="jersey_population_2024_manual_fixture"
        )
    )
    census_population_reference = sum(
        _integer_value(row, "population")
        for row in _read_canonical_table(root, "parish_population.csv", {"parish", "population"})
    )

    age_rows = _read_canonical_table(
        root,
        "age_sex.csv",
        {"source_id", "age_band", "sex", "count"},
    )
    detailed: dict[tuple[int, str], int] = {}
    for row in age_rows:
        if row.get("source_id") != "census_2021_age_gender_csv" or row.get("sex") not in {
            "male",
            "female",
        }:
            continue
        detailed[(_age_value(row["age_band"]), row["sex"])] = _integer_value(row, "count")
    if not detailed:
        raise DataBuildError("detailed 2021 age/sex controls are missing")
    full_age_band_targets = {
        "under_16": int(
            _find_value(
                population_rows, "age_under_16", source_id="jersey_population_2024_manual_fixture"
            )
        )
        if any(row.get("measure") == "age_under_16" for row in population_rows)
        else sum(row["count"] for row in age_rows if row.get("age_band") == "under_16"),
        "16_to_64": int(
            _find_value(
                population_rows, "age_16_to_64", source_id="jersey_population_2024_manual_fixture"
            )
        )
        if any(row.get("measure") == "age_16_to_64" for row in population_rows)
        else sum(row["count"] for row in age_rows if row.get("age_band") == "16_to_64"),
        "65_plus": int(
            _find_value(
                population_rows, "age_65_plus", source_id="jersey_population_2024_manual_fixture"
            )
        )
        if any(row.get("measure") == "age_65_plus" for row in population_rows)
        else sum(row["count"] for row in age_rows if row.get("age_band") == "65_plus"),
    }
    full_sex_targets = {
        "male": int(
            _find_value(
                population_rows, "sex_male", source_id="jersey_population_2024_manual_fixture"
            )
        ),
        "female": int(
            _find_value(
                population_rows, "sex_female", source_id="jersey_population_2024_manual_fixture"
            )
        ),
    }
    full_age_sex_counts = _build_full_age_sex_counts(
        detailed, full_age_band_targets, full_sex_targets
    )

    parish_rows = _read_canonical_table(root, "parish_population.csv", {"parish", "population"})
    parish_counts = {row["parish"]: _integer_value(row, "population") for row in parish_rows}
    household_rows = _read_canonical_table(
        root, "household_types.csv", {"household_type", "households"}
    )
    household_type_counts = {
        row["household_type"]: _integer_value(row, "households") for row in household_rows
    }
    housing_rows = _read_canonical_table(
        root,
        "housing_controls.csv",
        {"measure", "category", "value"},
    )
    housing_controls = {
        measure: _find_value(housing_rows, measure, source_id="census_2021_report_manual_fixture")
        for measure in (
            "occupied_private_dwellings",
            "persons_in_private_dwellings",
            "occupied_dwellings_that_are_houses",
            "occupied_dwellings_that_are_flats",
            "overcrowded_households",
            "under_occupied_households",
            "households_without_car_or_van",
            "st_helier_households_without_car_or_van",
        )
    }
    communal_rows = _read_canonical_table(
        root,
        "communal_settings.csv",
        {"measure", "setting", "value"},
    )
    communal_by_setting: dict[str, dict[str, int]] = {}
    for row in communal_rows:
        setting = row["setting"]
        if setting == "All":
            continue
        communal_by_setting.setdefault(setting, {})[row["measure"]] = _integer_value(row, "value")
    communal_categories = tuple(
        CommunalControl(setting, values["establishments"], values["residents"])
        for setting, values in communal_by_setting.items()
        if "establishments" in values and "residents" in values
    )
    if not communal_categories:
        raise DataBuildError("communal establishment controls are missing")
    communal_residents_reference = sum(item.residents for item in communal_categories)
    communal_establishments_reference = sum(item.establishments for item in communal_categories)
    private_households_reference = int(housing_controls["occupied_private_dwellings"])
    private_residents_reference = int(housing_controls["persons_in_private_dwellings"])
    if private_residents_reference + communal_residents_reference != census_population_reference:
        raise DataBuildError(
            "private and communal census residents do not reconcile to parish population"
        )
    assumptions = (
        "2021 detailed age/sex shape is raked to 2024 broad age and sex marginals; "
        "joint 2024 age/sex is derived.",
        "2021 parish shares are scaled to the selected population target; parish "
        "counts are derived, not observed 2024 counts.",
        "Private/communal population and household counts are scaled from the 2021 "
        "census reference population.",
        "Dwelling type uses the supported broad house/flat controls; residual rounded "
        "share is labelled other.",
        "Crowding categories treat overcrowded, underoccupied and standard as mutually "
        "exclusive for generation.",
        "Car access is generated from the all-island and St Helier no-car controls; "
        "other parish conditioning is not inferred.",
        "Communal resident age/sex is allocated independently of establishment type "
        "because no joint control is available.",
        "Binary male/female source categories are retained; no unsupported third sex "
        "category is invented.",
    )
    source_manifest_hash = sha256_file(root / "data" / "sources.yaml")
    return PopulationControls(
        full_population_target=full_population_target,
        census_population_reference=census_population_reference,
        full_age_sex_counts=full_age_sex_counts,
        full_age_band_targets=full_age_band_targets,
        full_sex_targets=full_sex_targets,
        parish_counts=parish_counts,
        household_type_counts=household_type_counts,
        private_households_reference=private_households_reference,
        private_residents_reference=private_residents_reference,
        communal_residents_reference=communal_residents_reference,
        communal_establishments_reference=communal_establishments_reference,
        communal_categories=communal_categories,
        housing_controls=housing_controls,
        canonical_hashes=canonical_hashes,
        source_manifest_hash=source_manifest_hash,
        assumptions=assumptions,
    )
