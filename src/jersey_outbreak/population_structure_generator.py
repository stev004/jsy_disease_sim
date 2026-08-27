"""Deterministic, disease-agnostic Milestone 3 structure generation."""

from __future__ import annotations

import math
import resource
import time
from dataclasses import dataclass
from typing import Any

import numpy as np

from .data_pipeline import DataBuildError
from .population_controls import allocate_proportional
from .population_structure_artifacts import M2PopulationInput, logical_structure_hash
from .population_structure_controls import (
    StructureControls,
    load_structure_controls,
    scaled_private_job_target,
    scaled_structure_targets,
)
from .population_structure_schemas import (
    JobAssignmentRecord,
    ResidentStructureRecord,
    SchoolAssignmentRecord,
    SchoolClassRecord,
    SchoolRecord,
    StructureGenerationConfig,
    WorkplaceRecord,
    WorkplaceTeamRecord,
)

SEMI_URBAN_PARISHES = {"St Saviour", "St Clement"}
DESTINATION_CATEGORIES = ("St Helier", "Semi-urban parishes", "Rural parishes")
SCHOOL_NOMINAL_CAPACITY = {"primary": 240, "secondary": 500, "special": 90}
SCHOOL_CLASS_SIZE = {"primary": 25, "secondary": 25, "special": 10}
BAND_LIMITS = {
    "1": (1, 1),
    "2-5": (2, 5),
    "6-9": (6, 9),
    "10-19": (10, 19),
    "20-49": (20, 49),
    # The source is right-censored at 50+; this upper bound is structural.
    "50+": (50, 500),
}
TOLERANCES = {
    "exact": 0,
    "destination_share": 0.01,
    "commute_share": 0.06,
    "multi_job_share": 0.005,
}


@dataclass
class GeneratedStructure:
    config: StructureGenerationConfig
    controls: StructureControls
    m2_input: M2PopulationInput
    resident_structure: list[dict[str, Any]]
    schools: list[dict[str, Any]]
    classes: list[dict[str, Any]]
    school_assignments: list[dict[str, Any]]
    workplaces: list[dict[str, Any]]
    workplace_teams: list[dict[str, Any]]
    job_assignments: list[dict[str, Any]]
    diagnostics: dict[str, Any]
    logical_content_hash: str
    runtime_seconds: float
    peak_memory_bytes: int | None


def _school_kind(school_type: str) -> str:
    lowered = school_type.lower()
    if "special" in lowered:
        return "special"
    if "primary" in lowered:
        return "primary"
    if "secondary" in lowered:
        return "secondary"
    raise DataBuildError(f"unsupported school type: {school_type}")


def _school_year(age: int, kind: str) -> str:
    if kind == "primary":
        return f"P{age - 3}"
    if kind == "secondary":
        return f"S{age - 10}"
    return f"SP{age - 3}"


def _school_age_allowed(age: int, kind: str) -> bool:
    if kind == "primary":
        return 4 <= age <= 11
    if kind == "secondary":
        return 11 <= age <= 17
    return 4 <= age <= 18


def _allocate_school_sizes(total: int, nominal_capacity: int) -> list[int]:
    school_count = max(1, math.ceil(total / nominal_capacity))
    return list(
        allocate_proportional(total, {str(index): 1 for index in range(school_count)}).values()
    )


def _build_schools(
    m2: M2PopulationInput,
    controls: StructureControls,
    school_targets: dict[str, int],
    rng: np.random.Generator,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    residents_by_id = {row["agent_id"]: row for row in m2.residents}
    unassigned = set(residents_by_id)
    schools: list[dict[str, Any]] = []
    classes: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    assignment_by_agent: dict[str, dict[str, Any]] = {}
    school_index = 0

    # Allocate special placements first because their permitted age range is widest.
    ordered_types = sorted(
        school_targets, key=lambda school_type: _school_kind(school_type) != "special"
    )
    for school_type in ordered_types:
        target = school_targets[school_type]
        kind = _school_kind(school_type)
        candidates = [
            agent_id
            for agent_id in sorted(unassigned)
            if _school_age_allowed(residents_by_id[agent_id]["age"], kind)
        ]
        rng.shuffle(candidates)
        if kind == "special":
            # Age 18 is outside the primary/secondary bands and has ample
            # capacity in every supported population mode.
            candidates.sort(
                key=lambda agent_id: (
                    residents_by_id[agent_id]["age"] != 18,
                    -residents_by_id[agent_id]["age"],
                )
            )
        else:
            candidates.sort(key=lambda agent_id: residents_by_id[agent_id]["age"])
        if len(candidates) < target:
            raise DataBuildError(
                f"school control cannot be assigned without incompatible ages: {school_type}"
            )
        selected = candidates[:target]
        selected.sort()
        rng.shuffle(selected)
        sizes = _allocate_school_sizes(target, SCHOOL_NOMINAL_CAPACITY[kind])
        offset = 0
        for _school_number, pupil_count in enumerate(sizes, start=1):
            school_id = f"school-m3-{school_index:04d}"
            school_index += 1
            school_agents = selected[offset : offset + pupil_count]
            offset += pupil_count
            school = {
                "school_id": school_id,
                "school_type": school_type,
                "nominal_capacity": SCHOOL_NOMINAL_CAPACITY[kind],
                "pupil_count": pupil_count,
            }
            pupil_parish_counts: dict[str, int] = {}
            for agent_id in school_agents:
                parish = residents_by_id[agent_id]["home_parish"]
                pupil_parish_counts[parish] = pupil_parish_counts.get(parish, 0) + 1
            school["school_parish"] = min(
                pupil_parish_counts,
                key=lambda parish: (-pupil_parish_counts[parish], parish),
            )
            schools.append(school)
            by_year: dict[str, list[str]] = {}
            for agent_id in school_agents:
                age = residents_by_id[agent_id]["age"]
                by_year.setdefault(_school_year(age, kind), []).append(agent_id)
            for year in sorted(by_year):
                year_agents = by_year[year]
                rng.shuffle(year_agents)
                class_size = SCHOOL_CLASS_SIZE[kind]
                for class_number, start in enumerate(
                    range(0, len(year_agents), class_size), start=1
                ):
                    class_agents = year_agents[start : start + class_size]
                    class_id = f"{school_id}-{year}-{class_number:02d}"
                    classes.append(
                        {
                            "class_id": class_id,
                            "school_id": school_id,
                            "school_year": year,
                            "class_number": class_number,
                            "pupil_count": len(class_agents),
                        }
                    )
                    for agent_id in class_agents:
                        age = residents_by_id[agent_id]["age"]
                        assignment = {
                            "agent_id": agent_id,
                            "school_id": school_id,
                            "school_type": school_type,
                            "school_year": year,
                            "class_id": class_id,
                            "age": age,
                            "school_parish": school["school_parish"],
                        }
                        assignments.append(assignment)
                        assignment_by_agent[agent_id] = assignment
                        unassigned.remove(agent_id)
    for row in assignments:
        SchoolAssignmentRecord.model_validate(row)
    for row in schools:
        SchoolRecord.model_validate(row)
    for row in classes:
        SchoolClassRecord.model_validate(row)
    return schools, classes, assignments, assignment_by_agent


def _allocate_sizes(
    workplace_targets: dict[str, int], total_jobs: int, rng: np.random.Generator
) -> list[tuple[str, int]]:
    """Allocate exact total-band workplace sizes to the filled-job universe."""

    minimum = sum(workplace_targets[band] * BAND_LIMITS[band][0] for band in workplace_targets)
    maximum = sum(workplace_targets[band] * BAND_LIMITS[band][1] for band in workplace_targets)
    if not minimum <= total_jobs <= maximum:
        raise DataBuildError(
            f"workplace size controls cannot contain {total_jobs} jobs within {minimum}-{maximum}"
        )
    extra = total_jobs - minimum
    capacities = {
        band: count * (BAND_LIMITS[band][1] - BAND_LIMITS[band][0])
        for band, count in workplace_targets.items()
    }
    band_extra = allocate_proportional(extra, capacities) if extra else dict.fromkeys(capacities, 0)
    sizes: list[tuple[str, int]] = []
    for band, count in workplace_targets.items():
        low, high = BAND_LIMITS[band]
        extra_for_band = band_extra[band]
        values = [low] * count
        remaining = extra_for_band
        capacity_remaining = np.full(count, high - low, dtype=float)
        # The 50+ source band is right-censored.  A seeded capacity-weighted
        # allocation preserves the exact filled-job total while avoiding an
        # artificial plateau of identically sized large workplaces.
        while remaining:
            eligible = np.flatnonzero(capacity_remaining > 0)
            if len(eligible) == 0:
                raise DataBuildError(f"workplace size allocation exceeded {band} capacity")
            weights = capacity_remaining[eligible] / capacity_remaining[eligible].sum()
            take = int(rng.choice(eligible, p=weights))
            values[take] += 1
            capacity_remaining[take] -= 1
            remaining -= 1
        sizes.extend((band, size) for size in values)
    return sizes


def _allocate_nonprivate_sizes(total_jobs: int, maximum_size: int = 25) -> list[tuple[str, int]]:
    """Create bounded operational workplaces for jobs outside the private control universe."""

    if total_jobs <= 0:
        return []
    full_workplaces, remainder = divmod(total_jobs, maximum_size)
    sizes = [maximum_size] * full_workplaces
    if remainder:
        sizes.append(remainder)
    return [
        (
            "1"
            if size == 1
            else "2-5"
            if size <= 5
            else "6-9"
            if size <= 9
            else "10-19"
            if size <= 19
            else "20-49"
            if size <= 49
            else "50+",
            size,
        )
        for size in sizes
    ]


def _allocate_sector_sex_targets(
    total: int, weights: dict[tuple[str, str], int]
) -> dict[tuple[str, str], int]:
    """Use the shared allocator while retaining the canonical two-dimensional keys."""

    encoded = {f"{sector}\x1f{sex}": weight for (sector, sex), weight in weights.items()}
    allocated = allocate_proportional(total, encoded)
    return {key: allocated[f"{key[0]}\x1f{key[1]}"] for key in weights}


def _assign_workplace_sectors(
    workplaces: list[dict[str, Any]], sector_jobs: dict[str, int]
) -> None:
    """Partition workplace capacities across sectors without inventing a cross-tab."""

    remaining = dict(sector_jobs)
    for workplace in sorted(
        workplaces, key=lambda row: (-row["employee_count"], row["workplace_id"])
    ):
        candidates = [
            sector for sector, target in remaining.items() if target >= workplace["employee_count"]
        ]
        if not candidates:
            raise DataBuildError("workplace capacities cannot reconcile to sector job controls")
        sector = min(candidates, key=lambda candidate: (remaining[candidate], candidate))
        workplace["sector"] = sector
        remaining[sector] -= workplace["employee_count"]
    if any(value != 0 for value in remaining.values()):
        raise DataBuildError(f"workplace sector capacities left unreconciled: {remaining}")


def _destination_category(parish: str) -> str:
    if parish == "St Helier":
        return "St Helier"
    if parish in SEMI_URBAN_PARISHES:
        return "Semi-urban parishes"
    return "Rural parishes"


def _assign_workplace_parishes(
    workplaces: list[dict[str, Any]],
    controls: StructureControls,
    rng: np.random.Generator,
) -> None:
    # The published destination split is not cross-tabulated by sector.  Allocate it
    # across the complete filled-job universe so that a sector-specific greedy pass
    # cannot silently distort the parish concentration.
    target_jobs = allocate_proportional(
        sum(row["employee_count"] for row in workplaces), controls.destination_controls
    )
    remaining = dict(target_jobs)
    ordered = sorted(workplaces, key=lambda row: (-row["employee_count"], row["workplace_id"]))
    for row in ordered:
        candidates = [
            category
            for category in DESTINATION_CATEGORIES
            if remaining[category] >= row["employee_count"]
        ]
        if not candidates:
            candidates = [max(DESTINATION_CATEGORIES, key=lambda item: remaining[item])]
        category = max(
            candidates, key=lambda item: (remaining[item], -DESTINATION_CATEGORIES.index(item))
        )
        row["_destination_category"] = category
        remaining[category] -= row["employee_count"]
    # Small indivisible workplace sizes can leave a bounded residual; the generated
    # worker share is checked, rather than pretending an exact OD matrix exists.
    if max(abs(value) for value in remaining.values()) > 500:
        raise DataBuildError(
            f"workplace destination allocation left an implausible residual: {remaining}"
        )
    parish_weights = {
        parish: controls.population.parish_counts[parish]
        for parish in controls.population.parish_counts
        if parish != "St Helier"
    }
    semi_weights = {parish: parish_weights[parish] for parish in sorted(SEMI_URBAN_PARISHES)}
    rural_weights = {
        parish: value
        for parish, value in parish_weights.items()
        if parish not in SEMI_URBAN_PARISHES
    }
    for row in workplaces:
        category = row.pop("_destination_category")
        if category == "St Helier":
            row["work_parish"] = "St Helier"
        elif category == "Semi-urban parishes":
            row["work_parish"] = str(
                rng.choice(
                    list(semi_weights),
                    p=np.array(list(semi_weights.values())) / sum(semi_weights.values()),
                )
            )
        else:
            row["work_parish"] = str(
                rng.choice(
                    list(rural_weights),
                    p=np.array(list(rural_weights.values())) / sum(rural_weights.values()),
                )
            )


def _mode_weights(
    worker: dict[str, Any], work_parish: str, controls: StructureControls
) -> dict[str, float]:
    home = worker["home_parish"]
    if home == "St Helier" and work_parish == "St Helier":
        category = "St Helier resident and worker"
        weights = dict(controls.conditional_destination_modes.get(category, {}))
        weights["other"] = max(0, 100 - sum(weights.values()))
        return weights
    if home not in SEMI_URBAN_PARISHES and home != "St Helier" and work_parish == "St Helier":
        category = "rural resident working in town"
        weights = dict(controls.conditional_destination_modes.get(category, {}))
        weights["other"] = max(0, 100 - sum(weights.values()))
        return weights
    parish_modes = controls.commute_by_parish.get(home) or controls.all_commute_targets
    return {mode: count for mode, count in parish_modes.items() if mode != "work_from_home"}


def _assign_modes(
    worker_ids: list[str],
    workers: dict[str, dict[str, Any]],
    controls: StructureControls,
    rng: np.random.Generator,
) -> dict[str, str]:
    if not worker_ids:
        return {}
    by_context: dict[tuple[str, str], list[str]] = {}
    for agent_id in worker_ids:
        row = workers[agent_id]
        by_context.setdefault((row["home_parish"], row["work_parish"]), []).append(agent_id)
    modes: dict[str, str] = {}
    for ids in by_context.values():
        weights = _mode_weights(workers[ids[0]], workers[ids[0]]["work_parish"], controls)
        labels = list(allocate_proportional(len(ids), weights).items())
        rng.shuffle(ids)
        car_ids = [agent_id for agent_id in ids if workers[agent_id].get("car_access") == "car"]
        rng.shuffle(car_ids)
        desired_car = next((count for mode, count in labels if mode == "car"), 0)
        desired_car = min(desired_car, len(car_ids))
        assigned_car = set(car_ids[:desired_car])
        remaining_ids = [agent_id for agent_id in ids if agent_id not in assigned_car]
        remaining_labels: list[str] = []
        for mode, count in labels:
            if mode != "car":
                remaining_labels.extend([mode] * count)
            elif count > desired_car:
                remaining_labels.extend(["other"] * (count - desired_car))
        while len(remaining_labels) < len(remaining_ids):
            remaining_labels.append("other")
        remaining_labels = remaining_labels[: len(remaining_ids)]
        rng.shuffle(remaining_labels)
        modes.update({agent_id: "car" for agent_id in assigned_car})
        modes.update(dict(zip(remaining_ids, remaining_labels, strict=True)))
    return modes


def _build_diagnostics(
    controls: StructureControls,
    config: StructureGenerationConfig,
    m2: M2PopulationInput,
    resident_structure: list[dict[str, Any]],
    schools: list[dict[str, Any]],
    classes: list[dict[str, Any]],
    school_assignments: list[dict[str, Any]],
    workplaces: list[dict[str, Any]],
    workplace_teams: list[dict[str, Any]],
    jobs: list[dict[str, Any]],
    target_school_types: dict[str, int],
    target_workers: int,
    target_workplaces: dict[str, int],
    target_secondary_jobs: int,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(name: str, actual: float | int, expected: float | int, tolerance: float = 0) -> None:
        difference = actual - expected
        status = "passed" if abs(difference) <= tolerance else "failed"
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

    resident_ids = {row["agent_id"] for row in m2.residents}
    worker_rows = [row for row in resident_structure if row["economic_status"] == "employed"]
    primary_jobs = [row for row in jobs if row["job_role"] == "primary"]
    secondary_jobs = [row for row in jobs if row["job_role"] == "secondary"]
    check("population_preserved", len(resident_structure), len(m2.residents))
    check("school_assignment_count", len(school_assignments), sum(target_school_types.values()))
    check("unique_workers", len(worker_rows), target_workers)
    check("primary_job_count", len(primary_jobs), target_workers)
    check("secondary_job_count", len(secondary_jobs), target_secondary_jobs)
    check("filled_job_count", len(jobs), target_workers + target_secondary_jobs)
    private_workplaces = [
        row for row in workplaces if row["workplace_universe"] == "private_undertaking_control"
    ]
    nonprivate_workplaces = [
        row for row in workplaces if row["workplace_universe"] == "synthetic_nonprivate"
    ]
    check("private_workplace_count", len(private_workplaces), sum(target_workplaces.values()))

    school_type_rows = []
    for school_type, target in target_school_types.items():
        actual = sum(row["school_type"] == school_type for row in school_assignments)
        check(f"school_type_{school_type}", actual, target)
        school_type_rows.append({"school_type": school_type, "target": target, "generated": actual})
    invalid_school_ages = sum(
        not _school_age_allowed(row["age"], _school_kind(row["school_type"]))
        for row in school_assignments
    )
    check("invalid_school_age_placements", invalid_school_ages, 0)
    assigned_school_ids = {row["agent_id"] for row in school_assignments}
    eligible_pupils = sum(4 <= row["age"] <= 18 for row in m2.residents)
    unassigned_eligible = eligible_pupils - len(assigned_school_ids)

    sector_rows = []
    scaled_sector_sex_targets = _allocate_sector_sex_targets(
        target_workers, controls.employment_sector_sex_targets
    )
    scaled_sector_targets = {
        sector: sum(
            count
            for (cell_sector, _sex), count in scaled_sector_sex_targets.items()
            if cell_sector == sector
        )
        for sector in controls.employment_worker_targets
    }
    for sector, _target in controls.employment_worker_targets.items():
        actual = sum(row["employment_sector"] == sector for row in worker_rows)
        scaled_target = scaled_sector_targets[sector]
        check(f"worker_sector_{sector}", actual, scaled_target)
        sector_rows.append({"sector": sector, "target": scaled_target, "generated": actual})

    sector_sex_rows = []
    for (sector, sex), target in scaled_sector_sex_targets.items():
        actual = sum(
            row["employment_sector"] == sector and row["sex"] == sex for row in worker_rows
        )
        check(f"worker_sector_sex_{sector}_{sex}", actual, target)
        sector_sex_rows.append(
            {"sector": sector, "sex": sex, "target": target, "generated": actual}
        )

    worker_age_bands = {
        "18_to_24": sum(18 <= row["age"] <= 24 for row in worker_rows),
        "25_to_34": sum(25 <= row["age"] <= 34 for row in worker_rows),
        "35_to_54": sum(35 <= row["age"] <= 54 for row in worker_rows),
        "55_to_64": sum(55 <= row["age"] <= 64 for row in worker_rows),
        "65_to_74": sum(65 <= row["age"] <= 74 for row in worker_rows),
    }

    band_rows = []
    for band, target in target_workplaces.items():
        actual = sum(row["size_band"] == band for row in private_workplaces)
        check(f"workplace_band_{band}", actual, target)
        band_rows.append({"size_band": band, "target": target, "generated": actual})
    below_ten = sum(row["employee_count"] < 10 for row in private_workplaces) / max(
        1, len(private_workplaces)
    )
    single = sum(row["employee_count"] == 1 for row in private_workplaces)
    large = sum(row["employee_count"] >= 50 for row in private_workplaces)

    physical_workers = [row for row in worker_rows if row["commute_mode"] != "work_from_home"]
    destination_generated = {
        category: sum(
            _destination_category(row["work_parish"]) == category for row in physical_workers
        )
        for category in DESTINATION_CATEGORIES
    }
    destination_target = allocate_proportional(len(physical_workers), controls.destination_controls)
    for category in DESTINATION_CATEGORIES:
        actual_share = destination_generated[category] / max(1, len(physical_workers))
        target_share = controls.destination_controls[category] / 100
        check(
            f"destination_share_{category}",
            actual_share,
            target_share,
            TOLERANCES["destination_share"],
        )

    commute_generated = {
        mode: sum(row["commute_mode"] == mode for row in worker_rows)
        for mode in controls.all_commute_targets
    }
    commute_target = allocate_proportional(target_workers, controls.all_commute_targets)
    for mode, target in commute_target.items():
        check(
            f"commute_{mode}",
            commute_generated.get(mode, 0),
            target,
            max(1, target_workers * TOLERANCES["commute_share"]),
        )
    car_violations = sum(
        row["commute_mode"] == "car" and row["car_access"] != "car" for row in worker_rows
    )
    wfh_violations = sum(
        (row["commute_mode"] == "work_from_home") != (row["work_from_home_days_per_week"] == 5)
        for row in worker_rows
    )
    check("car_access_consistency", car_violations, 0)
    check("work_from_home_consistency", wfh_violations, 0)

    worker_job_ids: dict[str, list[dict[str, Any]]] = {}
    for job in jobs:
        worker_job_ids.setdefault(job["agent_id"], []).append(job)
    invalid_job_agents = sum(agent_id not in resident_ids for agent_id in worker_job_ids)
    workplace_ids = {row["workplace_id"] for row in workplaces}
    team_workplaces = {row["team_id"]: row["workplace_id"] for row in workplace_teams}
    invalid_job_workplaces = sum(job["workplace_id"] not in workplace_ids for job in jobs)
    invalid_job_teams = sum(
        job["team_id"] is not None and team_workplaces.get(job["team_id"]) != job["workplace_id"]
        for job in jobs
    )
    duplicate_workplaces = sum(
        len({job["workplace_id"] for job in values}) != len(values)
        for values in worker_job_ids.values()
    )
    schedule_conflicts = sum(
        sum(job["days_per_week"] for job in values) > 5 for values in worker_job_ids.values()
    )
    check("job_agent_references", invalid_job_agents, 0)
    check("job_workplace_references", invalid_job_workplaces, 0)
    check("job_team_references", invalid_job_teams, 0)
    check("duplicate_job_membership", duplicate_workplaces, 0)
    check("job_schedule_conflicts", schedule_conflicts, 0)
    job_universe_counts = {
        universe: sum(job["employment_universe"] == universe for job in jobs)
        for universe in ("private_undertaking_control", "synthetic_nonprivate")
    }
    expected_private_jobs = min(
        scaled_private_job_target(controls, config.resolved_target_population), len(jobs)
    )
    check("private_filled_job_control", job_universe_counts["private_undertaking_control"], expected_private_jobs)
    check(
        "synthetic_nonprivate_filled_jobs",
        job_universe_counts["synthetic_nonprivate"],
        len(jobs) - expected_private_jobs,
    )
    generated_multi_share = len(secondary_jobs) / max(1, len(worker_rows))
    check(
        "multi_job_share",
        generated_multi_share,
        controls.additional_job_rate,
        TOLERANCES["multi_job_share"],
    )
    employee_counts = {row["workplace_id"]: 0 for row in workplaces}
    for job in jobs:
        if job["workplace_id"] in employee_counts:
            employee_counts[job["workplace_id"]] += 1
    workplace_count_mismatches = sum(
        employee_counts[row["workplace_id"]] != row["employee_count"] for row in workplaces
    )
    check("workplace_employee_counts", workplace_count_mismatches, 0)
    class_ids = {row["class_id"] for row in classes}
    school_ids = {row["school_id"] for row in schools}
    class_schools = {row["class_id"]: row["school_id"] for row in classes}
    invalid_class_membership = sum(
        row["class_id"] not in class_ids
        or row["school_id"] not in school_ids
        or class_schools.get(row["class_id"]) != row["school_id"]
        for row in school_assignments
    )
    check("school_class_membership", invalid_class_membership, 0)

    status = "passed" if all(check["status"] == "passed" for check in checks) else "failed"
    return {
        "schema_version": "1.0",
        "status": status,
        "mode": config.mode,
        "generated_population": len(resident_structure),
        "schools": {
            "target_pupil_count": sum(target_school_types.values()),
            "generated_pupil_count": len(school_assignments),
            "school_count": len(schools),
            "class_count": len(classes),
            "type_rows": school_type_rows,
            "invalid_age_placements": invalid_school_ages,
            "eligible_pupils_unassigned": unassigned_eligible,
            "unassigned_explanation": (
                "The canonical school total is below all age-compatible synthetic residents "
                "aged 4-18; remaining eligible residents are not forced into school."
            ),
        },
        "employment": {
            "unique_workers": len(worker_rows),
            "primary_jobs": len(primary_jobs),
            "additional_jobs": len(secondary_jobs),
            "filled_jobs": len(jobs),
            "target_universe": (
                "2021 resident workers scaled to M2 population target; additional jobs are "
                "a 7% structural assumption"
            ),
            "sector_rows": sector_rows,
            "sector_sex_rows": sector_sex_rows,
            "age_bands": worker_age_bands,
            "age_assumption": {
                "status": "structural_assumption",
                "weights": {
                    "18_to_24": 0.45,
                    "25_to_34": 0.90,
                    "35_to_54": 1.00,
                    "55_to_64": 0.80,
                    "65_to_74": 0.18,
                },
                "source": (
                    "no compatible authoritative Jersey employment-by-age headcount table "
                    "identified"
                ),
            },
        },
        "workplaces": {
            "total": len(workplaces),
            "private_undertakings": len(private_workplaces),
            "synthetic_nonprivate_workplaces": len(nonprivate_workplaces),
            "size_band_rows": band_rows,
            "below_10_proportion": below_ten,
            "single_person": single,
            "fifty_plus": large,
            "largest_sizes": sorted((row["employee_count"] for row in workplaces), reverse=True)[
                :10
            ],
            "sector_distribution": {
                sector: sum(row["sector"] == sector for row in workplaces)
                for sector in sorted({row["sector"] for row in workplaces})
            },
            "public_private_classification": {
                value: sum(row["public_private"] == value for row in workplaces)
                for value in sorted({row["public_private"] for row in workplaces})
            },
            "universe": {
                "private_workplaces": "private_undertaking_control",
                "private_workplace_count_control": controls.full_workplace_target,
                "synthetic_nonprivate_workplaces": "derived_residual_filled_job_capacity",
                "primary_jobs": "resident_worker_primary",
                "secondary_jobs": "synthetic_secondary",
                "private_filled_job_control": controls.full_private_job_target,
                "private_filled_jobs_generated": job_universe_counts[
                    "private_undertaking_control"
                ],
                "synthetic_nonprivate_filled_jobs": job_universe_counts["synthetic_nonprivate"],
                "public_sector_job_control": "unknown_not_available_in_frozen_controls",
                "public_employer_identity": "unknown",
                "status": "operational_private_nonprivate_universes_separated",
            },
            "size_assumption": (
                "50+ undertakings use a structural 50-500 employee range because the source "
                "is right-censored."
            ),
        },
        "geography": {
            "physical_workers": len(physical_workers),
            "destination_target": destination_target,
            "destination_generated": destination_generated,
            "st_helier_physical_share": destination_generated["St Helier"]
            / max(1, len(physical_workers)),
            "wfh_workers": commute_generated.get("work_from_home", 0),
            "parish_assignment": (
                "synthetic work-parish categories weighted by canonical 66/13/21 destination "
                "controls"
            ),
            "semi_urban_parishes": sorted(SEMI_URBAN_PARISHES),
        },
        "commute": {
            "target": commute_target,
            "generated": commute_generated,
            "car_access_violations": car_violations,
            "work_from_home_violations": wfh_violations,
        },
        "multi_job": {
            "workers_with_secondary_job": len(secondary_jobs),
            "target_share": controls.additional_job_rate,
            "generated_share": generated_multi_share,
            "schedule_conflicts": schedule_conflicts,
        },
        "checks": checks,
        "tolerances": TOLERANCES,
        "provenance": {
            "canonical_input_hashes": controls.canonical_hashes,
            "m2_population_artifact_id": m2.manifest.artifact_id,
            "m2_population_logical_content_hash": m2.manifest.logical_content_hash,
            "assumptions": controls.assumptions,
            "transformations": [
                "school_type_counts_scaled_v1",
                "synthetic_school_and_class_allocation_v1",
                "resident_worker_selection_scaled_v1",
                "resident_worker_selection_age_propensity_v2",
                "resident_worker_sector_sex_allocation_v2",
                "synthetic_workplace_size_band_allocation_v3",
                "workplace_destination_category_allocation_v1",
                "conditional_commute_mode_allocation_v1",
                "bounded_secondary_job_allocation_v1",
                "private_nonprivate_filled_job_universe_partition_c1_b2_v1",
            ],
        },
    }


def generate_structure(
    root: Any,
    config: StructureGenerationConfig,
    m2_input: M2PopulationInput,
) -> GeneratedStructure:
    """Generate, validate and diagnose M3 membership and movement structure."""

    started = time.perf_counter()
    before_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    root_path = root.resolve()
    controls = load_structure_controls(root_path)
    if m2_input.manifest.mode != config.mode:
        raise DataBuildError("M3 mode does not match the M2 input artifact mode")
    if m2_input.manifest.seed != config.seed:
        raise DataBuildError("M3 seed does not match the M2 input artifact seed")
    if m2_input.manifest.actual_population != config.resolved_target_population:
        raise DataBuildError("M2 population target does not match M3 configuration")
    rng = np.random.default_rng(config.seed)
    target_school_types, target_workers, target_workplaces, target_secondary_jobs = (
        scaled_structure_targets(controls, config.resolved_target_population)
    )
    schools, classes, school_assignments, school_by_agent = _build_schools(
        m2_input, controls, target_school_types, rng
    )
    residents_by_id = {row["agent_id"]: row for row in m2_input.residents}
    workers_eligible = [
        row
        for row in m2_input.residents
        if 18 <= row["age"] <= 74 and row["agent_id"] not in school_by_agent
    ]
    if len(workers_eligible) < target_workers:
        raise DataBuildError("worker target exceeds age-eligible non-pupil residents")
    sector_sex_targets = _allocate_sector_sex_targets(
        target_workers, controls.employment_sector_sex_targets
    )
    worker_sex_targets = {
        sex: sum(
            count for (sector, cell_sex), count in sector_sex_targets.items() if cell_sex == sex
        )
        for sex in ("male", "female")
    }

    def employment_age_weight(age: int) -> float:
        # No compatible Jersey employment-by-age headcount control is frozen.
        # This is a documented structural propensity used only to avoid the
        # pre-C1 uniform 18-74 draw and its excessive 65+ employment.
        if age < 25:
            return 0.45
        if age < 35:
            return 0.90
        if age < 55:
            return 1.00
        if age < 65:
            return 0.80
        return 0.18

    selected_workers: list[dict[str, Any]] = []
    for sex, sex_target in worker_sex_targets.items():
        candidates = [row for row in workers_eligible if row["sex"] == sex]
        if len(candidates) < sex_target:
            raise DataBuildError(f"worker sex target exceeds eligible {sex} residents")
        weights = np.asarray([employment_age_weight(row["age"]) for row in candidates])
        probabilities = weights / weights.sum()
        selected_indices = rng.choice(len(candidates), sex_target, replace=False, p=probabilities)
        selected_workers.extend(candidates[int(index)] for index in selected_indices)
    rng.shuffle(selected_workers)
    worker_ids = [row["agent_id"] for row in selected_workers]
    worker_by_id = {row["agent_id"]: dict(row) for row in selected_workers}
    sector_targets = {
        sector: sum(
            count
            for (cell_sector, _sex), count in sector_sex_targets.items()
            if cell_sector == sector
        )
        for sector in controls.employment_worker_targets
    }
    worker_sector: dict[str, str] = {}
    unassigned_workers_by_sex = {
        sex: {agent_id for agent_id in worker_ids if worker_by_id[agent_id]["sex"] == sex}
        for sex in ("male", "female")
    }
    for (sector, sex), count in sector_sex_targets.items():
        ids = sorted(unassigned_workers_by_sex[sex])
        if len(ids) < count:
            raise DataBuildError(f"sector-by-sex worker allocation exceeded {sex} pool")
        rng.shuffle(ids)
        for agent_id in ids[:count]:
            worker_sector[agent_id] = sector
            unassigned_workers_by_sex[sex].remove(agent_id)
    secondary_count = min(target_secondary_jobs, target_workers)
    wfh_target = int(
        round(
            target_workers
            * controls.all_commute_targets.get("work_from_home", 0)
            / max(1, sum(controls.all_commute_targets.values()))
        )
    )
    wfh_candidates = list(worker_ids)
    rng.shuffle(wfh_candidates)
    wfh_workers = set(wfh_candidates[: min(wfh_target, len(wfh_candidates))])

    secondary_sector_targets = allocate_proportional(secondary_count, sector_targets)
    sector_job_targets = {
        sector: count + secondary_sector_targets[sector] for sector, count in sector_targets.items()
    }
    workplace_targets = target_workplaces
    total_jobs = sum(sector_job_targets.values())
    private_job_target = min(
        scaled_private_job_target(controls, config.resolved_target_population), total_jobs
    )
    nonprivate_job_target = total_jobs - private_job_target
    private_workplace_sizes = _allocate_sizes(workplace_targets, private_job_target, rng)
    nonprivate_workplace_sizes = _allocate_nonprivate_sizes(nonprivate_job_target)
    workplaces: list[dict[str, Any]] = []
    workplace_index = 0
    for band, size in private_workplace_sizes:
        workplace_id = f"workplace-m3-{workplace_index:05d}"
        workplace_index += 1
        team_count = math.ceil(size / 12) if size >= 10 else 0
        workplaces.append(
            {
                "workplace_id": workplace_id,
                "sector": "",
                "work_parish": "St Helier",
                "size_band": band,
                "employee_count": size,
                "public_private": "unknown",
                "workplace_universe": "private_undertaking_control",
                "team_count": team_count,
            }
        )
    for band, size in nonprivate_workplace_sizes:
        workplace_id = f"workplace-m3-{workplace_index:05d}"
        workplace_index += 1
        team_count = math.ceil(size / 12) if size >= 10 else 0
        workplaces.append(
            {
                "workplace_id": workplace_id,
                "sector": "",
                "work_parish": "St Helier",
                "size_band": band,
                "employee_count": size,
                "public_private": "unknown",
                "workplace_universe": "synthetic_nonprivate",
                "team_count": team_count,
            }
        )
    _assign_workplace_sectors(workplaces, sector_job_targets)
    _assign_workplace_parishes(workplaces, controls, rng)
    workplace_by_id = {row["workplace_id"]: row for row in workplaces}
    workplace_teams: list[dict[str, Any]] = []
    slots_by_workplace: dict[str, list[tuple[str, str | None]]] = {}
    for workplace in workplaces:
        teams = []
        for team_number in range(1, workplace["team_count"] + 1):
            team_id = f"{workplace['workplace_id']}-team-{team_number:02d}"
            workplace_teams.append(
                {
                    "team_id": team_id,
                    "workplace_id": workplace["workplace_id"],
                    "team_number": team_number,
                }
            )
            teams.append(team_id)
        slots_by_workplace[workplace["workplace_id"]] = [
            (workplace["workplace_id"], teams[index % len(teams)] if teams else None)
            for index in range(workplace["employee_count"])
        ]
    # Build sector slot pools after workplace parish/team assignment.
    slots_by_sector: dict[str, list[tuple[str, str | None]]] = {}
    for workplace in workplaces:
        slots_by_sector.setdefault(workplace["sector"], []).extend(
            slots_by_workplace[workplace["workplace_id"]]
        )
    jobs: list[dict[str, Any]] = []
    primary_workplace: dict[str, tuple[str, str | None]] = {}
    for sector in sorted(sector_targets):
        sector_workers = [agent_id for agent_id in worker_ids if worker_sector[agent_id] == sector]
        slots = list(slots_by_sector.get(sector, []))
        rng.shuffle(slots)
        if len(slots) < len(sector_workers):
            raise DataBuildError(f"workplace slots cannot hold primary workers in {sector}")
        rng.shuffle(sector_workers)
        for agent_id, slot in zip(sector_workers, slots[: len(sector_workers)], strict=True):
            primary_workplace[agent_id] = slot
            workplace_id, slot_team_id = slot
            workplace = workplace_by_id[workplace_id]
            remote_days = 5 if agent_id in wfh_workers else 0
            jobs.append(
                {
                    "job_id": f"job-m3-{len(jobs):07d}",
                    "agent_id": agent_id,
                    "workplace_id": workplace_id,
                    "job_role": "primary",
                    "sector": sector,
                    "work_parish": workplace["work_parish"],
                    "days_per_week": 5,
                    "remote_days_per_week": remote_days,
                    "team_id": slot_team_id,
                    "job_universe": "resident_worker_primary",
                    "employment_universe": workplace["workplace_universe"],
                }
            )
        slots_by_sector[sector] = slots[len(sector_workers) :]
    secondary_workers: set[str] = set()
    remaining_slots = [
        (sector, index, slot)
        for sector, slots in slots_by_sector.items()
        for index, slot in enumerate(slots)
    ]
    secondary_candidates = [agent_id for agent_id in worker_ids if agent_id not in wfh_workers]
    rng.shuffle(secondary_candidates)
    for _ in range(secondary_count):
        eligible = [
            agent_id
            for agent_id in secondary_candidates
            if agent_id not in secondary_workers
            and any(
                slot[0] != primary_workplace[agent_id][0]
                for _sector, _index, slot in remaining_slots
            )
        ]
        if not eligible:
            raise DataBuildError("secondary jobs cannot be assigned without workplace duplication")
        agent_id = str(rng.choice(eligible))
        primary_id = primary_workplace[agent_id][0]
        slot_index = next(
            index
            for index, (_sector, _local_index, slot) in enumerate(remaining_slots)
            if slot[0] != primary_id
        )
        sector, _local_index, (workplace_id, slot_team_id) = remaining_slots.pop(slot_index)
        slots_by_sector[sector].remove((workplace_id, slot_team_id))
        secondary_workers.add(agent_id)
        primary_jobs_for_agent = next(
            job for job in jobs if job["agent_id"] == agent_id and job["job_role"] == "primary"
        )
        primary_jobs_for_agent["days_per_week"] = 4
        workplace = workplace_by_id[workplace_id]
        jobs.append(
            {
                "job_id": f"job-m3-{len(jobs):07d}",
                "agent_id": agent_id,
                "workplace_id": workplace_id,
                "job_role": "secondary",
                "sector": workplace["sector"],
                "work_parish": workplace["work_parish"],
                "days_per_week": 1,
                "remote_days_per_week": 0,
                "team_id": slot_team_id,
                "job_universe": "synthetic_secondary",
                "employment_universe": workplace["workplace_universe"],
            }
        )
    if any(slots_by_sector.values()):
        raise DataBuildError("workplace slots were not fully consumed by generated jobs")
    for row in workplaces:
        WorkplaceRecord.model_validate(row)
    for row in workplace_teams:
        WorkplaceTeamRecord.model_validate(row)
    for row in jobs:
        JobAssignmentRecord.model_validate(row)

    primary_jobs_by_agent = {row["agent_id"]: row for row in jobs if row["job_role"] == "primary"}
    commute_workers = {
        agent_id: {
            **worker_by_id[agent_id],
            "work_parish": primary_jobs_by_agent[agent_id]["work_parish"],
            "car_access": worker_by_id[agent_id].get("car_access"),
        }
        for agent_id in worker_ids
    }
    non_wfh_modes = _assign_modes(
        [agent_id for agent_id in worker_ids if agent_id not in wfh_workers],
        commute_workers,
        controls,
        rng,
    )
    resident_structure: list[dict[str, Any]] = []
    secondary_by_agent = {row["agent_id"]: row for row in jobs if row["job_role"] == "secondary"}
    for agent_id, resident in residents_by_id.items():
        school = school_by_agent.get(agent_id)
        primary = primary_jobs_by_agent.get(agent_id)
        secondary = secondary_by_agent.get(agent_id)
        if school is not None:
            status = "student"
        elif primary is not None:
            status = "employed"
        elif resident["age"] < 18:
            status = "child"
        elif resident["age"] >= 65:
            status = "retired"
        else:
            status = "unemployed"
        row = {
            "agent_id": agent_id,
            "age": resident["age"],
            "sex": resident["sex"],
            "home_parish": resident["home_parish"],
            "car_access": resident.get("car_access"),
            "economic_status": status,
            "employment_sector": primary["sector"] if primary else None,
            "primary_workplace_id": primary["workplace_id"] if primary else None,
            "secondary_workplace_id": secondary["workplace_id"] if secondary else None,
            "work_parish": primary["work_parish"] if primary else None,
            "school_id": school["school_id"] if school else None,
            "school_type": school["school_type"] if school else None,
            "school_year": school["school_year"] if school else None,
            "class_id": school["class_id"] if school else None,
            "school_parish": school["school_parish"] if school else None,
            "commute_mode": (
                "work_from_home"
                if agent_id in wfh_workers
                else non_wfh_modes.get(agent_id)
                if primary
                else None
            ),
            "work_from_home_days_per_week": 5 if agent_id in wfh_workers else 0,
            "primary_work_days_per_week": primary["days_per_week"] if primary else 0,
        }
        ResidentStructureRecord.model_validate(row)
        resident_structure.append(row)
    diagnostics = _build_diagnostics(
        controls,
        config,
        m2_input,
        resident_structure,
        schools,
        classes,
        school_assignments,
        workplaces,
        workplace_teams,
        jobs,
        target_school_types,
        target_workers,
        target_workplaces,
        target_secondary_jobs,
    )
    if diagnostics["status"] != "passed":
        failed_checks = [
            check["name"] for check in diagnostics["checks"] if check["status"] != "passed"
        ]
        raise DataBuildError(f"Milestone 3 diagnostics did not pass: {failed_checks}")
    runtime_seconds = time.perf_counter() - started
    after_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_memory_bytes = max(before_memory, after_memory)
    generated = GeneratedStructure(
        config=config,
        controls=controls,
        m2_input=m2_input,
        resident_structure=resident_structure,
        schools=schools,
        classes=classes,
        school_assignments=school_assignments,
        workplaces=workplaces,
        workplace_teams=workplace_teams,
        job_assignments=jobs,
        diagnostics=diagnostics,
        logical_content_hash="",
        runtime_seconds=runtime_seconds,
        peak_memory_bytes=peak_memory_bytes,
    )
    generated.logical_content_hash = logical_structure_hash(generated)
    return generated
