"""Milestone 3 control loading from the frozen Milestone 1 aggregate tables."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .data_pipeline import DataBuildError, parse_int, read_csv_rows
from .population_controls import PopulationControls, allocate_proportional, load_population_controls


@dataclass(frozen=True)
class StructureControls:
    population: PopulationControls
    school_targets: dict[str, int]
    employment_worker_targets: dict[str, int]
    employment_sector_sex_targets: dict[tuple[str, str], int]
    workplace_cell_counts: dict[tuple[str, str], int]
    workplace_band_counts: dict[str, int]
    commute_by_parish: dict[str, dict[str, int]]
    destination_controls: dict[str, float]
    conditional_destination_modes: dict[str, dict[str, float]]
    all_commute_targets: dict[str, int]
    full_worker_target: int
    full_private_job_target: int
    full_school_target: int
    full_workplace_target: int
    additional_job_rate: float
    canonical_hashes: dict[str, str]
    assumptions: tuple[str, ...]


def _integer(row: dict[str, str], field: str) -> int:
    value = parse_int(row.get(field, ""), path=Path("canonical table"), field=field)
    if value is None:
        raise DataBuildError(f"blank integer control: {field}")
    return value


def _float(row: dict[str, str], field: str) -> float:
    raw = row.get(field, "").strip()
    try:
        return float(raw)
    except ValueError as exc:
        raise DataBuildError(f"invalid numeric control: {field}={raw!r}") from exc


def _scale(total: int, reference: int, target: int) -> int:
    return int(round(total * target / reference))


def load_structure_controls(root: Path) -> StructureControls:
    """Validate M1 inputs and load only the controls required by Milestone 3."""

    root = root.resolve()
    population = load_population_controls(root)
    processed = root / "data" / "processed"

    school_rows = read_csv_rows(processed / "school_students.csv", {"school_type", "students"})
    school_targets = {
        row["school_type"]: _integer(row, "students")
        for row in school_rows
        if row["school_type"] != "Total"
    }
    school_total = sum(school_targets.values())
    if not school_targets or school_total <= 0:
        raise DataBuildError("school controls are empty")

    employment_rows = read_csv_rows(
        processed / "employment_sectors.csv", {"measure", "sector", "sex", "value"}
    )
    employment_worker_targets = {
        row["sector"]: _integer(row, "value")
        for row in employment_rows
        if row["measure"] == "resident_workers" and row["sex"] == "all" and row["sector"] != "All"
    }
    full_worker_target = sum(employment_worker_targets.values())
    if full_worker_target != 57_338:
        raise DataBuildError("resident-worker controls do not reconcile to 57,338")
    employment_sector_sex_targets = {
        (row["sector"], row["sex"]): _integer(row, "value")
        for row in employment_rows
        if row["measure"] == "resident_workers"
        and row["sex"] in {"male", "female"}
        and row["sector"] != "All"
    }
    if sum(employment_sector_sex_targets.values()) != full_worker_target:
        raise DataBuildError("sector-by-sex resident-worker controls do not reconcile")
    private_job_rows = [
        row
        for row in employment_rows
        if row["measure"] == "jobs" and row["sector"] == "Private sector"
    ]
    if len(private_job_rows) != 1:
        raise DataBuildError("private filled-job control is missing")
    full_private_job_target = _integer(private_job_rows[0], "value")

    workplace_rows = read_csv_rows(
        processed / "workplace_sizes.csv",
        {"sector", "size_band", "count", "upper_bound", "censoring"},
    )
    workplace_cell_counts = {
        (row["sector"], row["size_band"]): _integer(row, "count")
        for row in workplace_rows
        if row["sector"] != "Total private sector undertakings" and row["count"]
    }
    workplace_band_counts = {
        row["size_band"]: _integer(row, "count")
        for row in workplace_rows
        if row["sector"] == "Total private sector undertakings" and row["count"]
    }
    full_workplace_target = sum(workplace_band_counts.values())
    if full_workplace_target != 8_500:
        raise DataBuildError("workplace controls do not reconcile to 8,500 undertakings")
    if not workplace_cell_counts:
        raise DataBuildError("workplace size controls are empty")

    destination_rows = read_csv_rows(
        processed / "workplace_destination.csv", {"measure", "category", "subcategory", "value"}
    )
    destination_controls = {
        row["subcategory"]: _float(row, "value")
        for row in destination_rows
        if row["category"] == "workers_working_in"
    }
    if set(destination_controls) != {"St Helier", "Semi-urban parishes", "Rural parishes"}:
        raise DataBuildError("workplace destination controls are incomplete")
    if round(sum(destination_controls.values()), 6) != 100:
        raise DataBuildError("workplace destination controls do not sum to 100 percent")

    conditional_destination_modes: dict[str, dict[str, float]] = defaultdict(dict)
    for row in destination_rows:
        if row["category"] != "workers_working_in":
            conditional_destination_modes[row["category"]][row["subcategory"]] = _float(
                row, "value"
            )

    commute_rows = read_csv_rows(
        processed / "commute_modes.csv", {"parish", "mode", "workers", "upper_bound"}
    )
    commute_by_parish: dict[str, dict[str, int]] = defaultdict(dict)
    for row in commute_rows:
        if row["workers"]:
            commute_by_parish[row["parish"]][row["mode"]] = _integer(row, "workers")
    all_commute_targets = dict(commute_by_parish.get("All Parishes", {}))
    if not all_commute_targets:
        raise DataBuildError("all-parish commute controls are empty")

    assumptions = (
        "2021 resident-worker totals define a synthetic unique-worker universe; "
        "2025 filled-job controls are not used to redefine unique workers.",
        "Worker, school and workplace counts are scaled from the 2024 full-population "
        "target for reduced modes.",
        "School IDs, workplace IDs, classes and teams are synthetic because no frozen "
        "institution-level rolls or employer identities are available.",
        "Primary school ages are structurally assigned to ages 4-11; secondary ages "
        "11-17; special-school placement permits ages 4-18 without diagnoses.",
        "Total workplace size-band counts are scaled separately from resident-worker "
        "sector controls; the published sector-by-size rows do not exactly reconcile "
        "to the total row, so no unsupported cross-tab is imposed. The right-censored "
        "50+ band uses a structural 50-500 employee range.",
        "Semi-urban parishes are represented by St Saviour and St Clement only; St Brelade "
        "is retained in the rural destination category in accordance with the C1 geography rule. "
        "the remaining non-St-Helier parishes are rural for destination allocation.",
        "The 66/13/21 workplace destination split is applied to synthetic workers; "
        "it is not presented as a contemporary observed count.",
        "The 2021 work-from-home share is a baseline scenario assumption because it "
        "was measured during COVID guidance.",
        "Approximately 7 percent of workers receive one bounded secondary job; "
        "secondary jobs preserve the primary sector and use a one-day schedule.",
        "Car mode is conservatively disallowed for residents without household car "
        "access; the canonical aggregate car category does not distinguish drivers "
        "from passengers.",
        "Resident-worker employment controls are observed by sector and sex from the 2021 "
        "industry/sex table; no compatible Jersey employment-by-age headcount table is frozen. "
        "Age selection therefore uses an explicit structural labour-force propensity, with "
        "65+ employment capped by that scenario weight rather than treated as observed.",
        "The 8,500 workplace size controls describe private undertakings, while the 57,338 "
        "resident-worker controls describe unique resident workers and the 2025 private-job "
        "control describes filled jobs. These universes remain separate metadata fields; "
        "no whole-economy employer crosswalk is claimed, so synthetic workplace public/private "
        "classification remains unknown.",
    )
    return StructureControls(
        population=population,
        school_targets=school_targets,
        employment_worker_targets=employment_worker_targets,
        employment_sector_sex_targets=employment_sector_sex_targets,
        workplace_cell_counts=workplace_cell_counts,
        workplace_band_counts=workplace_band_counts,
        commute_by_parish=dict(commute_by_parish),
        destination_controls=destination_controls,
        conditional_destination_modes={
            category: dict(values) for category, values in conditional_destination_modes.items()
        },
        all_commute_targets=all_commute_targets,
        full_worker_target=full_worker_target,
        full_private_job_target=full_private_job_target,
        full_school_target=school_total,
        full_workplace_target=full_workplace_target,
        additional_job_rate=0.07,
        canonical_hashes=population.canonical_hashes,
        assumptions=assumptions,
    )


def scaled_structure_targets(
    controls: StructureControls, target_population: int
) -> tuple[dict[str, int], int, dict[str, int], int]:
    """Return exact school, worker, workplace and secondary-job targets."""

    school = allocate_proportional(
        _scale(
            controls.full_school_target,
            controls.population.full_population_target,
            target_population,
        ),
        controls.school_targets,
    )
    workers = _scale(
        controls.full_worker_target,
        controls.population.census_population_reference,
        target_population,
    )
    workplaces = allocate_proportional(
        _scale(
            controls.full_workplace_target,
            controls.population.full_population_target,
            target_population,
        ),
        controls.workplace_band_counts,
    )
    secondary_jobs = int(round(workers * controls.additional_job_rate))
    return school, workers, workplaces, secondary_jobs
