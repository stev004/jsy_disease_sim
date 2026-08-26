"""Deterministic, disease-agnostic synthetic population generation for Milestone 2."""

from __future__ import annotations

import math
import resource
import time
from dataclasses import dataclass
from typing import Any

import numpy as np

from .data_pipeline import DataBuildError
from .population_controls import (
    PopulationControls,
    allocate_proportional,
    load_population_controls,
    scale_counts,
)
from .population_schemas import (
    CommunalSettingRecord,
    HouseholdRecord,
    PopulationGenerationConfig,
    ResidentRecord,
)

DEPENDENCY_AGE = 16
PENSIONER_AGE = 65
TOLERANCES = {
    "population_count": 0,
    "parish_count": 0,
    "age_band_count": 0,
    "sex_count": 0,
    "household_count": 0,
    "household_type_count": 0,
    "communal_resident_count": 0,
    "housing_proportion": 0.01,
}

HOUSEHOLD_BASE_ROLES: dict[str, tuple[str, ...]] = {
    "Single adult": ("adult",),
    "Couple (adult)": ("adult", "partner"),
    "Single parent (with dependent children)": ("parent", "dependent_child"),
    "Single parent (all children 16 years or more)": ("parent", "adult_child"),
    "Couple with dependent children": ("adult", "partner", "dependent_child"),
    "Couple with children (all children 16 years or more)": (
        "adult",
        "partner",
        "adult_child",
    ),
    "Couple (one pensioner)": ("adult", "pensioner"),
    "Single pensioner": ("pensioner",),
    "Two or more pensioners": ("pensioner", "pensioner"),
    "Two or more unrelated persons": ("unrelated_adult", "unrelated_adult"),
    "Other": ("adult", "other"),
}
HOUSEHOLD_MAX_SIZE = {
    "Single parent (with dependent children)": 6,
    "Single parent (all children 16 years or more)": 5,
    "Couple with dependent children": 7,
    "Couple with children (all children 16 years or more)": 6,
    "Two or more pensioners": 5,
    "Two or more unrelated persons": 5,
    "Other": 8,
}


@dataclass
class GeneratedPopulation:
    config: PopulationGenerationConfig
    controls: PopulationControls
    residents: list[dict[str, Any]]
    households: list[dict[str, Any]]
    communal_settings: list[dict[str, Any]]
    diagnostics: dict[str, Any]
    logical_content_hash: str
    runtime_seconds: float
    peak_memory_bytes: int | None


def _round_half_up(value: float) -> int:
    return int(math.floor(value + 0.5))


def _mode_age_sex_counts(controls: PopulationControls, target: int) -> dict[tuple[int, str], int]:
    labels = {f"{age}|{sex}": count for (age, sex), count in controls.full_age_sex_counts.items()}
    scaled = scale_counts(labels, target)
    return {
        (int(label.split("|", 1)[0]), label.split("|", 1)[1]): count
        for label, count in scaled.items()
    }


def _new_household(household_id: str, household_type: str, parish: str) -> dict[str, Any]:
    roles = list(HOUSEHOLD_BASE_ROLES[household_type])
    return {
        "household_id": household_id,
        "household_type": household_type,
        "home_parish": parish,
        "_roles": roles,
        "dwelling_type": None,
        "crowding_band": None,
        "car_access": None,
    }


def _allocate_extra_roles(
    households: list[dict[str, Any]],
    category: str,
    amount: int,
    rng: np.random.Generator,
    parish: str | None = None,
) -> int:
    if amount <= 0:
        return 0
    if category == "dependent_child":
        eligible_types = {
            "Single parent (with dependent children)",
            "Couple with dependent children",
        }
        role = "dependent_child"
    elif category == "pensioner":
        eligible_types = {"Two or more pensioners"}
        role = "pensioner"
    elif category == "adult_child":
        eligible_types = {
            "Single parent (all children 16 years or more)",
            "Couple with children (all children 16 years or more)",
        }
        role = "adult_child"
    elif category == "unrelated_adult":
        eligible_types = {"Two or more unrelated persons"}
        role = "unrelated_adult"
    elif category == "other":
        eligible_types = {"Other"}
        role = "other"
    else:
        raise DataBuildError(f"unknown household extra-role category: {category}")
    remaining = amount
    while remaining:
        candidates = [
            index
            for index, household in enumerate(households)
            if household["household_type"] in eligible_types
            and (parish is None or household["home_parish"] == parish)
            and len(household["_roles"]) < HOUSEHOLD_MAX_SIZE[household["household_type"]]
        ]
        if not candidates:
            raise DataBuildError(
                f"cannot allocate {remaining} required {category} household members "
                "within plausible sizes"
            )
        capacities = np.array(
            [
                HOUSEHOLD_MAX_SIZE[households[index]["household_type"]]
                - len(households[index]["_roles"])
                for index in candidates
            ],
            dtype=float,
        )
        chosen = int(rng.choice(candidates, p=capacities / capacities.sum()))
        households[chosen]["_roles"].append(role)
        remaining -= 1
    return amount


def _assign_housing_attributes(households: list[dict[str, Any]], rng: np.random.Generator) -> None:
    dwelling_counts = allocate_proportional(
        len(households), {"house": 55.0, "flat": 44.0, "other": 1.0}
    )
    crowding_counts = allocate_proportional(
        len(households), {"overcrowded": 4.0, "underoccupied": 26.4, "standard": 69.6}
    )

    dwelling_labels = [label for label, count in dwelling_counts.items() for _ in range(count)]
    crowding_labels = [label for label, count in crowding_counts.items() for _ in range(count)]
    rng.shuffle(dwelling_labels)
    rng.shuffle(crowding_labels)
    for index, household in enumerate(households):
        household["dwelling_type"] = dwelling_labels[index]
        household["crowding_band"] = crowding_labels[index]

    total_no_car = max(_round_half_up(len(households) * 0.16), 0)
    st_helier = [
        index
        for index, household in enumerate(households)
        if household["home_parish"] == "St Helier"
    ]
    st_no_car = _round_half_up(len(st_helier) * 0.30)
    total_no_car = max(total_no_car, st_no_car)
    other_indices = [index for index in range(len(households)) if index not in set(st_helier)]
    other_no_car = total_no_car - st_no_car
    if other_no_car > len(other_indices):
        raise DataBuildError(
            "car-access controls cannot be satisfied for the generated household counts"
        )
    no_car: set[int] = set()
    if st_no_car:
        no_car.update(int(index) for index in rng.choice(st_helier, st_no_car, replace=False))
    if other_no_car:
        no_car.update(
            int(index) for index in rng.choice(other_indices, other_no_car, replace=False)
        )
    for index, household in enumerate(households):
        household["car_access"] = "no_car" if index in no_car else "car"


def _build_communal_settings(
    controls: PopulationControls,
    target: int,
    parish_targets: dict[str, int],
    rng: np.random.Generator,
) -> tuple[list[dict[str, Any]], int, dict[str, dict[str, int]]]:
    communal_target = _round_half_up(
        target * controls.communal_residents_reference / controls.census_population_reference
    )
    establishment_target = max(
        1,
        _round_half_up(
            target
            * controls.communal_establishments_reference
            / controls.census_population_reference
        ),
    )
    establishment_counts = allocate_proportional(
        establishment_target,
        {item.setting_type: item.establishments for item in controls.communal_categories},
    )
    active = [
        item for item in controls.communal_categories if establishment_counts[item.setting_type] > 0
    ]
    category_residents = allocate_proportional(
        communal_target,
        {item.setting_type: item.residents for item in active},
    )
    target_categories = {
        item.setting_type: {
            "establishments": establishment_counts[item.setting_type],
            "residents": category_residents.get(item.setting_type, 0),
        }
        for item in controls.communal_categories
    }
    settings: list[dict[str, Any]] = []
    for item in controls.communal_categories:
        count = establishment_counts[item.setting_type]
        residents = category_residents.get(item.setting_type, 0)
        if count == 0:
            continue
        resident_counts = allocate_proportional(
            residents,
            {str(index): 1 for index in range(count)},
        )
        for index in range(count):
            settings.append(
                {
                    "setting_id": f"setting-m2-{len(settings):06d}",
                    "setting_type": item.setting_type,
                    "home_parish": None,
                    "resident_count": resident_counts[str(index)],
                }
            )
    # Assign establishments without claiming a parish-specific communal control.
    # Remaining parish capacity is used only to keep total parish membership valid.
    remaining = dict(parish_targets)
    order = sorted(range(len(settings)), key=lambda index: -settings[index]["resident_count"])
    for index in order:
        size = settings[index]["resident_count"]
        candidates = [parish for parish, capacity in remaining.items() if capacity >= size]
        if not candidates:
            raise DataBuildError(
                "communal settings cannot be assigned without exceeding parish population"
            )
        weights = np.array([remaining[parish] + 1 for parish in candidates], dtype=float)
        parish = str(rng.choice(candidates, p=weights / weights.sum()))
        settings[index]["home_parish"] = parish
        remaining[parish] -= size
    if sum(remaining.values()) != target - communal_target:
        raise DataBuildError("communal parish capacity allocation failed to reconcile")
    return settings, communal_target, target_categories


def _draw_age_sex(
    remaining: dict[tuple[int, str], int],
    rng: np.random.Generator,
    *,
    minimum_age: int = 0,
    maximum_age: int = 95,
) -> tuple[int, str]:
    candidates = [
        key
        for key, count in remaining.items()
        if count > 0 and minimum_age <= key[0] <= maximum_age
    ]
    if not candidates:
        raise DataBuildError(
            f"age/sex pool cannot satisfy role constraint {minimum_age}-{maximum_age}"
        )
    weights = np.array([remaining[key] for key in candidates], dtype=float)
    chosen = candidates[int(rng.choice(len(candidates), p=weights / weights.sum()))]
    remaining[chosen] -= 1
    return chosen


def _role_age_bounds(role: str) -> tuple[int, int]:
    if role == "dependent_child":
        return 0, DEPENDENCY_AGE - 1
    if role == "pensioner":
        return PENSIONER_AGE, 95
    if role in {"parent", "adult", "partner", "unrelated_adult"}:
        return 18, 95
    if role == "adult_child":
        return DEPENDENCY_AGE, 95
    return 0, 95


def _assign_private_residents(
    households: list[dict[str, Any]],
    private_counts: dict[tuple[int, str], int],
    rng: np.random.Generator,
) -> list[dict[str, Any]]:
    slots = [(household, role) for household in households for role in household["_roles"]]
    remaining = dict(private_counts)
    assignments: dict[int, tuple[int, str]] = {}
    priority = {
        "dependent_child": 0,
        "pensioner": 1,
        "parent": 2,
        "adult": 2,
        "partner": 2,
        "unrelated_adult": 2,
        "adult_child": 3,
        "other": 4,
    }
    indexed = list(range(len(slots)))
    for rank in sorted(set(priority.values())):
        group = [index for index in indexed if priority[slots[index][1]] == rank]
        rng.shuffle(group)
        for index in group:
            role = slots[index][1]
            minimum_age, maximum_age = _role_age_bounds(role)
            assignments[index] = _draw_age_sex(
                remaining, rng, minimum_age=minimum_age, maximum_age=maximum_age
            )
    if any(count != 0 for count in remaining.values()):
        raise DataBuildError("private resident age/sex pool was not consumed exactly")
    residents: list[dict[str, Any]] = []
    order = list(range(len(slots)))
    rng.shuffle(order)
    for agent_index, slot_index in enumerate(order):
        household, role = slots[slot_index]
        age, sex = assignments[slot_index]
        residents.append(
            {
                "agent_id": f"agent-m2-{agent_index:07d}",
                "age": age,
                "sex": sex,
                "home_parish": household["home_parish"],
                "household_id": household["household_id"],
                "household_role": role,
                "dwelling_type": household["dwelling_type"],
                "crowding_band": household["crowding_band"],
                "car_access": household["car_access"],
                "care_setting_id": None,
            }
        )
    return residents


def _assign_communal_residents(
    settings: list[dict[str, Any]],
    communal_counts: dict[tuple[int, str], int],
    start_index: int,
    rng: np.random.Generator,
) -> list[dict[str, Any]]:
    remaining = dict(communal_counts)
    slots = [setting for setting in settings for _ in range(setting["resident_count"])]
    rng.shuffle(slots)
    residents: list[dict[str, Any]] = []
    for offset, setting in enumerate(slots):
        age, sex = _draw_age_sex(remaining, rng)
        residents.append(
            {
                "agent_id": f"agent-m2-{start_index + offset:07d}",
                "age": age,
                "sex": sex,
                "home_parish": setting["home_parish"],
                "household_id": None,
                "household_role": "communal_resident",
                "dwelling_type": None,
                "crowding_band": None,
                "car_access": None,
                "care_setting_id": setting["setting_id"],
            }
        )
    if any(count != 0 for count in remaining.values()):
        raise DataBuildError("communal resident age/sex pool was not consumed exactly")
    return residents


def _validate_generated(
    config: PopulationGenerationConfig,
    residents: list[dict[str, Any]],
    households: list[dict[str, Any]],
    settings: list[dict[str, Any]],
    target_parishes: dict[str, int],
    target_age_sex: dict[tuple[int, str], int],
    target_household_types: dict[str, int],
    target_communal_residents: int,
    target_private_residents: int,
) -> list[dict[str, Any]]:
    try:
        resident_models = [ResidentRecord.model_validate(row) for row in residents]
        household_models = [
            HouseholdRecord.model_validate(
                {key: value for key, value in row.items() if not key.startswith("_")}
                | {"member_count": len(row["_roles"])}
            )
            for row in households
        ]
        setting_models = [CommunalSettingRecord.model_validate(row) for row in settings]
    except ValueError as exc:
        raise DataBuildError(f"generated population schema validation failed: {exc}") from exc
    if len(resident_models) != config.resolved_target_population:
        raise DataBuildError("generated population count does not equal configured target")
    if len({resident.agent_id for resident in resident_models}) != len(resident_models):
        raise DataBuildError("agent IDs are not unique")
    if len({household.household_id for household in household_models}) != len(household_models):
        raise DataBuildError("household IDs are not unique")
    if len({setting.setting_id for setting in setting_models}) != len(setting_models):
        raise DataBuildError("communal setting IDs are not unique")
    household_lookup = {household.household_id: household for household in household_models}
    setting_lookup = {setting.setting_id: setting for setting in setting_models}
    by_household: dict[str, list[ResidentRecord]] = {}
    by_setting: dict[str, list[ResidentRecord]] = {}
    for resident in resident_models:
        if resident.household_id is not None:
            household = household_lookup.get(resident.household_id)
            if household is None:
                raise DataBuildError(
                    f"resident references unknown private household: {resident.agent_id}"
                )
            if resident.home_parish != household.home_parish:
                raise DataBuildError(f"resident and household parish mismatch: {resident.agent_id}")
            if (
                resident.dwelling_type != household.dwelling_type
                or resident.crowding_band != household.crowding_band
                or resident.car_access != household.car_access
            ):
                raise DataBuildError(
                    f"resident and household housing mismatch: {resident.agent_id}"
                )
            by_household.setdefault(resident.household_id, []).append(resident)
        if resident.care_setting_id is not None:
            setting = setting_lookup.get(resident.care_setting_id)
            if setting is None:
                raise DataBuildError(
                    f"resident references unknown communal setting: {resident.agent_id}"
                )
            if resident.home_parish != setting.home_parish:
                raise DataBuildError(
                    f"resident and communal setting parish mismatch: {resident.agent_id}"
                )
            by_setting.setdefault(resident.care_setting_id, []).append(resident)
    checks: list[dict[str, Any]] = []

    def check(name: str, actual: int | float, expected: int | float, tolerance: float = 0) -> None:
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
        if status == "failed":
            raise DataBuildError(f"population validation failed: {name}: {actual} != {expected}")

    check("population_total", len(resident_models), config.resolved_target_population)
    generated_parishes = {
        parish: sum(resident.home_parish == parish for resident in resident_models)
        for parish in target_parishes
    }
    for parish, expected in target_parishes.items():
        check(f"parish_{parish}", generated_parishes[parish], expected)
    generated_age_sex = {
        key: sum(resident.age == key[0] and resident.sex == key[1] for resident in resident_models)
        for key in target_age_sex
    }
    for key, expected in target_age_sex.items():
        check(f"age_sex_{key[0]}_{key[1]}", generated_age_sex[key], expected)
    generated_types = {
        household_type: sum(row["household_type"] == household_type for row in households)
        for household_type in target_household_types
    }
    for household_type, expected in target_household_types.items():
        check(f"household_type_{household_type}", generated_types[household_type], expected)
    check("household_count", len(households), sum(target_household_types.values()))
    check(
        "private_membership_count",
        sum(len(value) for value in by_household.values()),
        target_private_residents,
    )
    check(
        "communal_resident_count",
        sum(len(value) for value in by_setting.values()),
        target_communal_residents,
    )
    for household in household_models:
        members = by_household.get(household.household_id, [])
        if len(members) != household.member_count or not members:
            raise DataBuildError(f"household membership invariant failed: {household.household_id}")
        roles = {member.household_role for member in members}
        if (
            household.household_type
            in {
                "Single adult",
                "Single pensioner",
            }
            and len(members) != 1
        ):
            raise DataBuildError(
                f"single-person household invariant failed: {household.household_id}"
            )
        if (
            household.household_type.startswith("Couple")
            and sum(member.age >= 18 for member in members) < 2
        ):
            raise DataBuildError(f"couple adult-pair invariant failed: {household.household_id}")
        if household.household_type == "Two or more pensioners" and not all(
            member.age >= PENSIONER_AGE for member in members
        ):
            raise DataBuildError(f"pensioner household invariant failed: {household.household_id}")
        for member in members:
            if member.household_role == "dependent_child" and member.age >= DEPENDENCY_AGE:
                raise DataBuildError(
                    f"dependent-child age invariant failed: {household.household_id}"
                )
            if (
                member.household_role in {"parent", "adult", "partner", "unrelated_adult"}
                and member.age < 18
            ):
                raise DataBuildError(f"adult-role age invariant failed: {household.household_id}")
            if member.household_role == "pensioner" and member.age < PENSIONER_AGE:
                raise DataBuildError(
                    f"pensioner-role age invariant failed: {household.household_id}"
                )
        if household.household_type not in HOUSEHOLD_BASE_ROLES or not roles:
            raise DataBuildError(f"invalid household role structure: {household.household_id}")
    for setting in setting_models:
        members = by_setting.get(setting.setting_id, [])
        if len(members) != setting.resident_count:
            raise DataBuildError(
                f"communal setting membership invariant failed: {setting.setting_id}"
            )
    return checks


def _public_household(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if not key.startswith("_")} | {
        "member_count": len(row["_roles"])
    }


def _build_diagnostics(
    controls: PopulationControls,
    config: PopulationGenerationConfig,
    residents: list[dict[str, Any]],
    households: list[dict[str, Any]],
    settings: list[dict[str, Any]],
    validation_checks: list[dict[str, Any]],
    target_parishes: dict[str, int],
    target_age_sex: dict[tuple[int, str], int],
    target_household_types: dict[str, int],
    target_communal_categories: dict[str, dict[str, int]],
) -> dict[str, Any]:
    generated_age = {
        str(age): sum(resident["age"] == age for resident in residents) for age in range(96)
    }
    generated_broad = {
        "under_16": sum(resident["age"] < 16 for resident in residents),
        "16_to_64": sum(16 <= resident["age"] < 65 for resident in residents),
        "65_plus": sum(resident["age"] >= 65 for resident in residents),
    }
    target_broad = {
        band: sum(
            count for (age, _sex), count in target_age_sex.items() if _age_band_local(age) == band
        )
        for band in ("under_16", "16_to_64", "65_plus")
    }
    generated_sex = {
        sex: sum(resident["sex"] == sex for resident in residents) for sex in ("male", "female")
    }
    target_sex = {
        sex: sum(count for (_age, cell_sex), count in target_age_sex.items() if cell_sex == sex)
        for sex in ("male", "female")
    }
    parish_rows = []
    for parish, target in target_parishes.items():
        actual = sum(resident["home_parish"] == parish for resident in residents)
        parish_rows.append(
            {
                "parish": parish,
                "target": target,
                "generated": actual,
                "absolute_error": actual - target,
                "percentage_error": (actual - target) / target if target else 0,
                "status": "derived_2021_share_scaled",
            }
        )
    household_type_rows = []
    for household_type, target in target_household_types.items():
        actual = sum(row["household_type"] == household_type for row in households)
        household_type_rows.append(
            {
                "household_type": household_type,
                "target": target,
                "generated": actual,
                "difference": actual - target,
                "status": "derived_2021_control_scaled",
            }
        )
    size_distribution: dict[str, int] = {}
    for household in households:
        size = str(len(household["_roles"]))
        size_distribution[size] = size_distribution.get(size, 0) + 1
    housing = {
        "dwelling_type": {
            label: {
                "generated_count": sum(row["dwelling_type"] == label for row in households),
                "generated_proportion": sum(row["dwelling_type"] == label for row in households)
                / len(households),
                "target_proportion": target,
                "status": "observed_broad_control_with_other_residual",
            }
            for label, target in {"house": 0.55, "flat": 0.44, "other": 0.01}.items()
        },
        "crowding_band": {
            label: {
                "generated_count": sum(row["crowding_band"] == label for row in households),
                "generated_proportion": sum(row["crowding_band"] == label for row in households)
                / len(households),
                "target_proportion": target,
                "status": "observed_overcrowding_underoccupancy_with_standard_residual",
            }
            for label, target in {
                "overcrowded": 0.04,
                "underoccupied": 0.264,
                "standard": 0.696,
            }.items()
        },
        "car_access": {
            "all_island_no_car": {
                "generated_proportion": sum(row["car_access"] == "no_car" for row in households)
                / len(households),
                "target_proportion": 0.16,
                "status": "observed_rounded_control",
            },
            "st_helier_no_car": {
                "generated_proportion": sum(
                    row["car_access"] == "no_car" and row["home_parish"] == "St Helier"
                    for row in households
                )
                / max(1, sum(row["home_parish"] == "St Helier" for row in households)),
                "target_proportion": 0.30,
                "status": "observed_rounded_control",
            },
        },
    }
    communal_rows = []
    for setting_type, target in target_communal_categories.items():
        generated = [row for row in settings if row["setting_type"] == setting_type]
        communal_rows.append(
            {
                "setting_type": setting_type,
                "target_establishments": target["establishments"],
                "generated_establishments": len(generated),
                "target_residents": target["residents"],
                "generated_residents": sum(row["resident_count"] for row in generated),
                "status": "derived_2021_control_scaled",
            }
        )
    all_checks = list(validation_checks)
    all_checks.extend(
        [
            {
                "name": "age_broad_controls",
                "status": "passed" if generated_broad == target_broad else "failed",
                "actual": generated_broad,
                "expected": target_broad,
                "tolerance": TOLERANCES["age_band_count"],
            },
            {
                "name": "sex_controls",
                "status": "passed" if generated_sex == target_sex else "failed",
                "actual": generated_sex,
                "expected": target_sex,
                "tolerance": TOLERANCES["sex_count"],
            },
        ]
    )
    status = "passed" if all(check["status"] == "passed" for check in all_checks) else "failed"
    return {
        "schema_version": "1.0",
        "status": status,
        "mode": config.mode,
        "target_population": config.resolved_target_population,
        "generated_population": len(residents),
        "population": {
            "sex": {"target": target_sex, "generated": generated_sex},
            "age_bands": {"target": target_broad, "generated": generated_broad},
            "age_distribution": generated_age,
        },
        "parish": {"status": "derived_2021_share_scaled", "rows": parish_rows},
        "households": {
            "generated_household_count": len(households),
            "household_population": sum(len(row["_roles"]) for row in households),
            "mean_household_size": sum(len(row["_roles"]) for row in households) / len(households),
            "size_distribution": size_distribution,
            "type_rows": household_type_rows,
            "max_household_size": max(len(row["_roles"]) for row in households),
        },
        "housing": housing,
        "communal": {
            "generated_residents": sum(row["resident_count"] for row in settings),
            "generated_establishments": len(settings),
            "rows": communal_rows,
        },
        "checks": all_checks,
        "tolerances": TOLERANCES,
        "provenance": {
            "canonical_input_hashes": controls.canonical_hashes,
            "source_manifest_hash": controls.source_manifest_hash,
            "assumptions": controls.assumptions,
            "transformations": [
                "parish_share_scaled_v1",
                "population_private_communal_split_scaled_v1",
                "age_sex_raking_to_2024_marginals_v1",
                "household_type_counts_scaled_v1",
                "household_extra_member_allocation_v1",
                "housing_attribute_allocation_v1",
                "communal_setting_allocation_v1",
            ],
        },
    }


def _age_band_local(age: int) -> str:
    if age < 16:
        return "under_16"
    if age < 65:
        return "16_to_64"
    return "65_plus"


def generate_population(root: Any, config: PopulationGenerationConfig) -> GeneratedPopulation:
    """Generate, validate and diagnose one synthetic population."""

    started = time.perf_counter()
    before_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    root_path = root.resolve()
    controls = load_population_controls(root_path)
    target = config.resolved_target_population
    rng = np.random.default_rng(config.seed)
    target_parishes = allocate_proportional(target, controls.parish_counts)
    settings, communal_target, target_communal_categories = _build_communal_settings(
        controls, target, target_parishes, rng
    )
    communal_by_parish = {
        parish: sum(
            setting["resident_count"] for setting in settings if setting["home_parish"] == parish
        )
        for parish in target_parishes
    }
    private_parishes = {
        parish: target_parishes[parish] - communal_by_parish[parish] for parish in target_parishes
    }
    if any(value < 0 for value in private_parishes.values()):
        raise DataBuildError("communal assignment exceeds parish population")
    household_target = _round_half_up(
        target * controls.private_households_reference / controls.census_population_reference
    )
    target_household_types = scale_counts(controls.household_type_counts, household_target)
    households: list[dict[str, Any]] = []
    household_index = 0
    for household_type, count in target_household_types.items():
        by_parish = allocate_proportional(count, private_parishes)
        for parish, parish_count in by_parish.items():
            for _ in range(parish_count):
                households.append(
                    _new_household(f"household-m2-{household_index:06d}", household_type, parish)
                )
                household_index += 1
    baseline_private = sum(len(row["_roles"]) for row in households)
    mode_age_sex = _mode_age_sex_counts(controls, target)
    communal_age_sex = allocate_proportional(
        communal_target,
        {f"{age}|{sex}": count for (age, sex), count in mode_age_sex.items()},
    )
    communal_age_sex = {
        (int(label.split("|", 1)[0]), label.split("|", 1)[1]): count
        for label, count in communal_age_sex.items()
    }
    private_age_sex = {key: mode_age_sex[key] - communal_age_sex[key] for key in mode_age_sex}
    private_target = target - communal_target
    if private_target - baseline_private < 0:
        raise DataBuildError("baseline household structures exceed the private population target")
    private_children = sum(
        count for (age, _sex), count in private_age_sex.items() if age < DEPENDENCY_AGE
    )
    private_pensioners = sum(
        count for (age, _sex), count in private_age_sex.items() if age >= PENSIONER_AGE
    )
    child_targets = allocate_proportional(private_children, private_parishes)
    pensioner_targets = allocate_proportional(private_pensioners, private_parishes)
    baseline_by_parish = {
        parish: sum(len(row["_roles"]) for row in households if row["home_parish"] == parish)
        for parish in private_parishes
    }
    dependent_by_parish = {
        parish: sum(
            row["_roles"].count("dependent_child")
            for row in households
            if row["home_parish"] == parish
        )
        for parish in private_parishes
    }
    pensioner_by_parish = {
        parish: sum(
            row["_roles"].count("pensioner") for row in households if row["home_parish"] == parish
        )
        for parish in private_parishes
    }
    for parish, parish_private_target in private_parishes.items():
        parish_extra = parish_private_target - baseline_by_parish[parish]
        if parish_extra < 0:
            raise DataBuildError(f"baseline households exceed private target in {parish}")
        dependent_extra = min(
            max(0, child_targets[parish] - dependent_by_parish[parish]), parish_extra
        )
        pensioner_extra = min(
            max(0, pensioner_targets[parish] - pensioner_by_parish[parish]),
            parish_extra - dependent_extra,
        )
        _allocate_extra_roles(households, "dependent_child", dependent_extra, rng, parish)
        _allocate_extra_roles(households, "pensioner", pensioner_extra, rng, parish)
        remaining_extra = parish_extra - dependent_extra - pensioner_extra
        category_types = {
            "adult_child": {
                "Single parent (all children 16 years or more)",
                "Couple with children (all children 16 years or more)",
            },
            "unrelated_adult": {"Two or more unrelated persons"},
            "other": {"Other"},
        }
        for category in ("adult_child", "unrelated_adult", "other"):
            if remaining_extra <= 0:
                break
            eligible_types = category_types[category]
            capacity = sum(
                HOUSEHOLD_MAX_SIZE[row["household_type"]] - len(row["_roles"])
                for row in households
                if row["home_parish"] == parish and row["household_type"] in eligible_types
            )
            amount = min(remaining_extra, capacity)
            _allocate_extra_roles(households, category, amount, rng, parish)
            remaining_extra -= amount
        if remaining_extra:
            raise DataBuildError(
                f"could not allocate {remaining_extra} plausible household members in {parish}"
            )
    _assign_housing_attributes(households, rng)
    private_residents = _assign_private_residents(households, private_age_sex, rng)
    communal_residents = _assign_communal_residents(
        settings, communal_age_sex, len(private_residents), rng
    )
    residents = private_residents + communal_residents
    validation_checks = _validate_generated(
        config,
        residents,
        households,
        settings,
        target_parishes,
        mode_age_sex,
        target_household_types,
        communal_target,
        target - communal_target,
    )
    diagnostics = _build_diagnostics(
        controls,
        config,
        residents,
        households,
        settings,
        validation_checks,
        target_parishes,
        mode_age_sex,
        target_household_types,
        target_communal_categories,
    )
    if diagnostics["status"] != "passed":
        raise DataBuildError("population diagnostics did not pass")
    runtime_seconds = time.perf_counter() - started
    after_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_memory_bytes = max(before_memory, after_memory)
    from .population_artifacts import logical_content_hash

    public_households = [_public_household(row) for row in households]
    public_settings = [dict(row) for row in settings]
    content_hash = logical_content_hash(residents, public_households, public_settings)
    return GeneratedPopulation(
        config=config,
        controls=controls,
        residents=residents,
        households=public_households,
        communal_settings=public_settings,
        diagnostics=diagnostics,
        logical_content_hash=content_hash,
        runtime_seconds=runtime_seconds,
        peak_memory_bytes=peak_memory_bytes,
    )
