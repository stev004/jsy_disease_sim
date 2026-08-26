"""Deterministic, disease-agnostic synthetic population generation for Milestone 2."""

from __future__ import annotations

import math
import resource
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np

from .data_pipeline import DataBuildError
from .population_controls import (
    PopulationControls,
    allocate_proportional,
    build_parish_age_sex_targets,
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
MIN_GENERATION_GAP = 15
MAX_COUPLE_AGE_GAP = 25
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
    "Single adult": 1,
    # The source household categories do not publish a hard maximum size.
    # Keep single-person categories fixed, while allowing residual ``other``
    # members to remain plausible in couple households when exact parish
    # population totals leave a small local remainder.
    "Couple (adult)": 8,
    "Single parent (with dependent children)": 6,
    "Single parent (all children 16 years or more)": 5,
    "Couple with dependent children": 7,
    "Couple with children (all children 16 years or more)": 6,
    "Couple (one pensioner)": 8,
    "Single pensioner": 1,
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
    allowed_types: set[str] | None = None,
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
        # Residual household members are not independently classified by the
        # source.  They can be attached to any household type while retaining
        # the explicit ``other`` role rather than being forced into an invalid
        # household-size residual.
        eligible_types = set(HOUSEHOLD_BASE_ROLES)
        if allowed_types is not None:
            eligible_types &= allowed_types
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


def _assign_housing_attributes(
    households: list[dict[str, Any]], controls: PopulationControls, rng: np.random.Generator
) -> None:
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

    all_island_rate = controls.housing_controls["households_without_car_or_van"] / 100
    st_helier_rate = controls.housing_controls["st_helier_households_without_car_or_van"] / 100
    total_no_car = _round_half_up(len(households) * all_island_rate)
    by_parish: dict[str, list[int]] = {}
    for index, household in enumerate(households):
        by_parish.setdefault(household["home_parish"], []).append(index)
    st_helier = by_parish.get("St Helier", [])
    st_no_car = _round_half_up(len(st_helier) * st_helier_rate)
    other_parishes = {
        parish: indices for parish, indices in by_parish.items() if parish != "St Helier"
    }
    residual = total_no_car - st_no_car
    capacity = sum(len(indices) for indices in other_parishes.values())
    if residual < 0 or residual > capacity:
        raise DataBuildError("parish car-access controls cannot be satisfied")
    other_targets = allocate_proportional(
        residual,
        {parish: controls.parish_no_car_weights.get(parish, 0.01) for parish in other_parishes},
    )
    if any(other_targets[parish] > len(indices) for parish, indices in other_parishes.items()):
        raise DataBuildError("parish car-access allocation exceeded a parish household count")
    no_car: set[int] = set()
    if st_no_car:
        no_car.update(int(index) for index in rng.choice(st_helier, st_no_car, replace=False))
    for parish, indices in other_parishes.items():
        count = other_targets[parish]
        if count:
            no_car.update(int(index) for index in rng.choice(indices, count, replace=False))
    for index, household in enumerate(households):
        household["car_access"] = "no_car" if index in no_car else "car"


def _rebalance_household_parishes(
    households: list[dict[str, Any]],
    private_parishes: dict[str, int],
    private_age_sex_by_parish: dict[str, dict[tuple[int, str], int]],
) -> None:
    """Keep synthetic household structures within each parish's private capacity."""

    def total(parish: str) -> int:
        return sum(len(row["_roles"]) for row in households if row["home_parish"] == parish)

    for _ in range(len(households) + 1):
        over = max(private_parishes, key=lambda parish: total(parish) - private_parishes[parish])
        under = min(private_parishes, key=lambda parish: total(parish) - private_parishes[parish])
        surplus = total(over) - private_parishes[over]
        capacity = private_parishes[under] - total(under)
        if surplus <= 0:
            break
        candidates = [
            row
            for row in households
            if row["home_parish"] == over and len(row["_roles"]) <= capacity
        ]
        if not candidates:
            raise DataBuildError("household parish capacity cannot be reconciled")
        row = max(candidates, key=lambda item: (len(item["_roles"]), item["household_id"]))
        row["home_parish"] = under
    else:
        raise DataBuildError("household parish capacity balancing exceeded its iteration bound")

    senior_capacity = {
        parish: sum(count for (age, _sex), count in pool.items() if age >= PENSIONER_AGE)
        for parish, pool in private_age_sex_by_parish.items()
    }
    child_capacity = {
        parish: sum(count for (age, _sex), count in pool.items() if age < DEPENDENCY_AGE)
        for parish, pool in private_age_sex_by_parish.items()
    }
    for role_name, capacity_by_parish, role_types in (
        (
            "pensioner",
            senior_capacity,
            {"Couple (one pensioner)", "Single pensioner", "Two or more pensioners"},
        ),
        (
            "dependent_child",
            child_capacity,
            {"Single parent (with dependent children)", "Couple with dependent children"},
        ),
    ):
        for _ in range(len(households) + 1):
            counts = {
                parish: sum(
                    row["_roles"].count(role_name)
                    for row in households
                    if row["home_parish"] == parish
                )
                for parish in private_parishes
            }
            donor = max(counts, key=lambda parish: counts[parish] - capacity_by_parish[parish])
            receiver = min(counts, key=lambda parish: counts[parish] - capacity_by_parish[parish])
            if counts[donor] <= capacity_by_parish[donor]:
                break
            candidates = [
                row
                for row in households
                if row["home_parish"] == donor
                and row["household_type"] in role_types
                and row["_roles"].count(role_name) > 0
                and total(receiver) + len(row["_roles"]) <= private_parishes[receiver]
            ]
            if not candidates:
                raise DataBuildError(
                    f"{role_name} household allocation cannot be reconciled by parish"
                )
            row = min(candidates, key=lambda item: (len(item["_roles"]), item["household_id"]))
            row["home_parish"] = receiver
        else:
            raise DataBuildError(f"{role_name} parish balancing exceeded its iteration bound")


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
    age_weight: Callable[[int], float] | None = None,
) -> tuple[int, str]:
    candidates = [
        key
        for key, count in remaining.items()
        if count > 0 and minimum_age <= key[0] <= maximum_age
    ]
    if not candidates:
        oldest = max(
            (age for age, _sex in remaining if remaining[(age, _sex)]),
            default=-1,
        )
        raise DataBuildError(
            f"age/sex pool cannot satisfy role constraint {minimum_age}-{maximum_age}; "
            f"remaining={sum(remaining.values())}, oldest={oldest}"
        )
    weights = np.array(
        [
            remaining[key] * (age_weight(key[0]) if age_weight is not None else 1)
            for key in candidates
        ],
        dtype=float,
    )
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


def _choose_adult_pair(
    remaining: dict[tuple[int, str], int],
    rng: np.random.Generator,
    minimum_age: int = 18,
    maximum_age: int = 95,
) -> tuple[tuple[int, str], tuple[int, str]]:
    candidates = [
        key
        for key, count in remaining.items()
        if count > 0 and minimum_age <= key[0] <= maximum_age
    ]
    rng.shuffle(candidates)
    for left in candidates:
        partners = [
            key
            for key, count in remaining.items()
            if count - (key == left) > 0
            and minimum_age <= key[0] <= maximum_age
            and abs(key[0] - left[0]) <= MAX_COUPLE_AGE_GAP
        ]
        if partners:
            right = partners[int(rng.integers(0, len(partners)))]
            remaining[left] -= 1
            remaining[right] -= 1
            return left, right
    raise DataBuildError("could not form a couple within the configured age-gap bound")


def _draw_non_pensioner_role(
    remaining: dict[tuple[int, str], int],
    rng: np.random.Generator,
    role: str,
) -> tuple[int, str]:
    """Prefer working-age slots while preserving the explicit pensioner pool."""

    minimum_age, maximum_age = _role_age_bounds(role)
    if role == "adult_child":
        # Preserve the narrow 16–17 band for adult children before drawing
        # from the shared working-age pool.  Otherwise late household draws
        # can strand only age-17 residents for an adult role.
        young_adult_child_count = sum(
            count for (age, _sex), count in remaining.items() if count > 0 and 16 <= age <= 17
        )
        if young_adult_child_count:
            maximum_age = 17
    working_age_count = sum(
        count
        for (age, _sex), count in remaining.items()
        if count > 0 and minimum_age <= age <= min(64, maximum_age)
    )
    if working_age_count:
        maximum_age = min(maximum_age, 64)
    return _draw_age_sex(remaining, rng, minimum_age=minimum_age, maximum_age=maximum_age)


def _assign_household_ages(
    household: dict[str, Any], remaining: dict[tuple[int, str], int], rng: np.random.Generator
) -> list[tuple[str, tuple[int, str]]]:
    """Assign one household as a relational unit, not as independent role draws."""

    roles = list(household["_roles"])
    children = [role for role in roles if role in {"dependent_child", "adult_child"}]
    parent_roles = [role for role in roles if role in {"parent", "adult", "partner"}]
    assigned: list[tuple[str, tuple[int, str]]] = []
    child_maximum = 95
    if children and parent_roles:
        child_minimum = max(_role_age_bounds(role)[0] for role in children)
        # Reserve the adult generation first.  The previous child-first greedy
        # allocator could consume the only compatible parent-age slots near the
        # end of a parish pool even when a valid household solution existed.
        parent_minimum = max(
            child_minimum + MIN_GENERATION_GAP,
            max(_role_age_bounds(role)[0] for role in parent_roles),
        )
        parent_maximum = 64
        available_adults = sum(
            count
            for (age, _sex), count in remaining.items()
            if parent_minimum <= age <= parent_maximum
        )
        if available_adults < len(parent_roles):
            parent_maximum = 95
        if len(parent_roles) == 2 and "partner" in parent_roles:
            candidates = [
                key
                for key, count in remaining.items()
                if count > 0 and parent_minimum <= key[0] <= parent_maximum
            ]
            pair: tuple[tuple[int, str], tuple[int, str]] | None = None
            for _ in range(500):
                left = candidates[int(rng.integers(0, len(candidates)))]
                right_candidates = [
                    key
                    for key in candidates
                    if abs(key[0] - left[0]) <= MAX_COUPLE_AGE_GAP
                    and (key != left or remaining[key] >= 2)
                ]
                if not right_candidates:
                    continue
                right = right_candidates[int(rng.integers(0, len(right_candidates)))]
                child_capacity = sum(
                    count - (1 if key == left else 0) - (1 if key == right else 0)
                    for key, count in remaining.items()
                    if child_minimum
                    <= key[0]
                    <= min(95, min(left[0], right[0]) - MIN_GENERATION_GAP)
                )
                if child_capacity >= len(children):
                    pair = (left, right)
                    break
            if pair is None:
                if all(role == "adult_child" for role in children):
                    # A raked parish age×sex pool can contain no compatible
                    # inter-generational span for a source household category
                    # (the CI St Mary pool is an example).  Preserve the source
                    # household type and member count, but do not assert an
                    # unsupported parent/child relationship for those residual
                    # members.  The relaxation is counted in diagnostics.
                    household["_roles"] = [
                        "other" if role == "adult_child" else role for role in household["_roles"]
                    ]
                    household["_role_relaxations"] = household.get("_role_relaxations", 0) + len(
                        children
                    )
                    return _assign_household_ages(household, remaining, rng)
                raise DataBuildError("could not form a parent couple for child roles")
            left, right = pair
            remaining[left] -= 1
            remaining[right] -= 1
            for role, value in zip(parent_roles, (left, right), strict=True):
                assigned.append((role, value))
            child_maximum = min(left[0], right[0]) - MIN_GENERATION_GAP
        else:
            parent_candidates = [
                key
                for key, count in remaining.items()
                if count > 0 and parent_minimum <= key[0] <= parent_maximum
            ]
            rng.shuffle(parent_candidates)
            chosen_parent = next(
                (
                    key
                    for key in parent_candidates
                    if sum(
                        count
                        for child_key, count in remaining.items()
                        if child_minimum <= child_key[0] <= key[0] - MIN_GENERATION_GAP
                    )
                    >= len(children)
                ),
                None,
            )
            if chosen_parent is None:
                if all(role == "adult_child" for role in children):
                    household["_roles"] = [
                        "other" if role == "adult_child" else role for role in household["_roles"]
                    ]
                    household["_role_relaxations"] = household.get("_role_relaxations", 0) + len(
                        children
                    )
                    return _assign_household_ages(household, remaining, rng)
                raise DataBuildError("could not form a parent for child roles")
            remaining[chosen_parent] -= 1
            assigned.append((parent_roles[0], chosen_parent))
            child_maximum = chosen_parent[0] - MIN_GENERATION_GAP
    elif len(parent_roles) == 2 and "partner" in parent_roles:
        try:
            left, right = _choose_adult_pair(remaining, rng, maximum_age=64)
        except DataBuildError:
            left, right = _choose_adult_pair(remaining, rng)
        for role, value in zip(parent_roles, (left, right), strict=True):
            assigned.append((role, value))
    else:
        for role in parent_roles:
            minimum_age, maximum_age = _role_age_bounds(role)
            if role in {"parent", "adult", "partner"}:
                value = _draw_non_pensioner_role(remaining, rng, role)
            else:
                value = _draw_age_sex(
                    remaining, rng, minimum_age=minimum_age, maximum_age=maximum_age
                )
            assigned.append((role, value))

    for role in children:
        minimum_age, maximum_age = _role_age_bounds(role)
        maximum_age = min(maximum_age, child_maximum)
        if role == "adult_child":
            young_maximum = min(17, maximum_age)
            young_count = sum(
                count
                for (age, _sex), count in remaining.items()
                if count > 0 and minimum_age <= age <= young_maximum
            )
            value = _draw_age_sex(
                remaining,
                rng,
                minimum_age=minimum_age,
                maximum_age=young_maximum if young_count else maximum_age,
            )
        else:
            value = _draw_age_sex(remaining, rng, minimum_age=minimum_age, maximum_age=maximum_age)
        assigned.append((role, value))

    for role in roles:
        if role in children or role in parent_roles:
            continue
        minimum_age, maximum_age = _role_age_bounds(role)
        assigned.append(
            (
                role,
                _draw_age_sex(remaining, rng, minimum_age=minimum_age, maximum_age=maximum_age),
            )
        )
    if len(assigned) != len(roles):
        raise DataBuildError("household age assignment did not consume every role")
    return assigned


def _assign_private_residents(
    households: list[dict[str, Any]],
    private_counts_by_parish: dict[str, dict[tuple[int, str], int]],
    rng: np.random.Generator,
) -> list[dict[str, Any]]:
    residents: list[dict[str, Any]] = []
    for parish in sorted(private_counts_by_parish):
        remaining = private_counts_by_parish[parish]
        parish_households = [row for row in households if row["home_parish"] == parish]
        ordered = list(parish_households)
        rng.shuffle(ordered)
        # Couple-with-children and other constrained households get first-class
        # relational assignment; unconstrained households follow.
        ordered.sort(
            key=lambda row: (
                not any(role == "pensioner" for role in row["_roles"]),
                not any(role == "dependent_child" for role in row["_roles"]),
                not any(role in {"dependent_child", "adult_child"} for role in row["_roles"]),
                "partner" not in row["_roles"],
                row["household_id"],
            )
        )
        for household in ordered:
            try:
                assigned = _assign_household_ages(household, remaining, rng)
            except DataBuildError as exc:
                raise DataBuildError(
                    f"{exc} in parish {parish}, household {household['household_id']} "
                    f"({household['household_type']}, roles={household['_roles']})"
                ) from exc
            for role, (age, sex) in assigned:
                residents.append(
                    {
                        "agent_id": "",
                        "age": age,
                        "sex": sex,
                        "home_parish": parish,
                        "household_id": household["household_id"],
                        "household_role": role,
                        "dwelling_type": household["dwelling_type"],
                        "crowding_band": household["crowding_band"],
                        "car_access": household["car_access"],
                        "care_setting_id": None,
                    }
                )
        if any(count != 0 for count in remaining.values()):
            raise DataBuildError(f"private resident age/sex pool was not consumed in {parish}")
    rng.shuffle(residents)
    for index, resident in enumerate(residents):
        resident["agent_id"] = f"agent-m2-{index:07d}"
    return residents


def _communal_age_bounds(setting_type: str) -> tuple[int, int]:
    lowered = setting_type.lower()
    if "care home" in lowered:
        return 50, 95
    if "children's home" in lowered or "childrens home" in lowered:
        return 0, 17
    if "detention" in lowered:
        return 18, 64
    if "hotel" in lowered:
        return 0, 95
    return 18, 95


def _assign_communal_residents(
    settings: list[dict[str, Any]],
    communal_counts_by_parish: dict[str, dict[tuple[int, str], int]],
    start_index: int,
    rng: np.random.Generator,
) -> tuple[list[dict[str, Any]], dict[str, dict[tuple[int, str], int]]]:
    remaining = {parish: dict(pool) for parish, pool in communal_counts_by_parish.items()}
    slots = [setting for setting in settings for _ in range(setting["resident_count"])]
    rng.shuffle(slots)
    residents: list[dict[str, Any]] = []
    for _offset, setting in enumerate(slots):
        parish = setting["home_parish"]
        minimum_age, maximum_age = _communal_age_bounds(setting["setting_type"])
        age_weight = (
            (lambda age: max(1, age - 45))
            if "care home" in setting["setting_type"].lower()
            else None
        )
        age, sex = _draw_age_sex(
            remaining[parish],
            rng,
            minimum_age=minimum_age,
            maximum_age=maximum_age,
            age_weight=age_weight,
        )
        residents.append(
            {
                "agent_id": "",
                "age": age,
                "sex": sex,
                "home_parish": parish,
                "household_id": None,
                "household_role": "communal_resident",
                "dwelling_type": None,
                "crowding_band": None,
                "car_access": None,
                "care_setting_id": setting["setting_id"],
            }
        )
    return residents, remaining


def _validate_generated(
    config: PopulationGenerationConfig,
    residents: list[dict[str, Any]],
    households: list[dict[str, Any]],
    settings: list[dict[str, Any]],
    target_parishes: dict[str, int],
    target_age_sex: dict[tuple[int, str], int],
    target_parish_age_sex: dict[tuple[str, int, str], int],
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
    generated_parish_age_sex = {
        key: sum(
            resident["home_parish"] == key[0]
            and resident["age"] == key[1]
            and resident["sex"] == key[2]
            for resident in residents
        )
        for key in target_parish_age_sex
    }
    for key, expected in target_parish_age_sex.items():
        check(f"parish_age_sex_{key[0]}_{key[1]}_{key[2]}", generated_parish_age_sex[key], expected)
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
        parents = [
            member.age
            for member in members
            if member.household_role in {"parent", "adult", "partner"}
        ]
        children = [
            member.age
            for member in members
            if member.household_role in {"dependent_child", "adult_child"}
        ]
        if children and parents and min(parents) - max(children) < MIN_GENERATION_GAP:
            raise DataBuildError(
                f"parent-child generation gap invariant failed: {household.household_id}"
            )
        if "partner" in roles and "adult" in roles and len(parents) == 2:
            if abs(parents[0] - parents[1]) > MAX_COUPLE_AGE_GAP:
                raise DataBuildError(f"couple age-gap invariant failed: {household.household_id}")
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
    target_parish_age_sex: dict[tuple[str, int, str], int],
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
    parish_age_rows = []
    for parish in target_parishes:
        for band in ("under_16", "16_to_64", "65_plus"):
            target_count = sum(
                count
                for (cell_parish, age, _sex), count in target_parish_age_sex.items()
                if cell_parish == parish and _age_band_local(age) == band
            )
            generated_count = sum(
                1
                for resident in residents
                if resident["home_parish"] == parish and _age_band_local(resident["age"]) == band
            )
            parish_age_rows.append(
                {
                    "parish": parish,
                    "age_band": band,
                    "target": target_count,
                    "generated": generated_count,
                    "difference": generated_count - target_count,
                    "status": "derived_2021_parish_age_sex_raked_to_global_controls",
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
                "target_proportion": controls.housing_controls["households_without_car_or_van"]
                / 100,
                "status": "observed_rounded_control",
            },
            "st_helier_no_car": {
                "generated_proportion": sum(
                    row["car_access"] == "no_car" and row["home_parish"] == "St Helier"
                    for row in households
                )
                / max(1, sum(row["home_parish"] == "St Helier" for row in households)),
                "target_proportion": controls.housing_controls[
                    "st_helier_households_without_car_or_van"
                ]
                / 100,
                "status": "observed_rounded_control",
            },
            "by_parish": {
                parish: {
                    "generated_proportion": sum(
                        row["car_access"] == "no_car"
                        for row in households
                        if row["home_parish"] == parish
                    )
                    / max(1, sum(row["home_parish"] == parish for row in households)),
                    "target_proportion": (
                        controls.housing_controls["st_helier_households_without_car_or_van"] / 100
                        if parish == "St Helier"
                        else None
                    ),
                    "target_basis": (
                        "observed_st_helier_control"
                        if parish == "St Helier"
                        else "derived_from_parish_worker_commute_non_car_share"
                    ),
                }
                for parish in target_parishes
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
    households_by_id: dict[str, list[dict[str, Any]]] = {}
    for resident in residents:
        household_id = resident.get("household_id")
        if household_id is not None:
            households_by_id.setdefault(household_id, []).append(resident)
    parent_child_reversals = 0
    minimum_generation_gap: int | None = None
    couple_age_gaps: list[int] = []
    for members in households_by_id.values():
        parents = [
            row["age"] for row in members if row["household_role"] in {"parent", "adult", "partner"}
        ]
        children = [
            row["age"]
            for row in members
            if row["household_role"] in {"dependent_child", "adult_child"}
        ]
        if parents and children:
            parent_child_reversals += sum(
                parent <= child for parent in parents for child in children
            )
            gap = min(parents) - max(children)
            minimum_generation_gap = (
                gap if minimum_generation_gap is None else min(minimum_generation_gap, gap)
            )
        adult = [row["age"] for row in members if row["household_role"] in {"adult", "partner"}]
        if len(adult) == 2 and any(row["household_role"] == "partner" for row in members):
            couple_age_gaps.append(abs(adult[0] - adult[1]))
    setting_type_by_id = {row["setting_id"]: row["setting_type"] for row in settings}
    communal_age_structure: dict[str, dict[str, int | None]] = {}
    for resident in residents:
        setting_id = resident.get("care_setting_id")
        if setting_id is None:
            continue
        setting_type = setting_type_by_id[setting_id]
        summary = communal_age_structure.setdefault(
            setting_type,
            {"residents": 0, "minimum_age": None, "maximum_age": None, "under_18": 0, "65_plus": 0},
        )
        age = resident["age"]
        summary["residents"] = int(summary["residents"] or 0) + 1
        summary["minimum_age"] = (
            age if summary["minimum_age"] is None else min(int(summary["minimum_age"]), age)
        )
        summary["maximum_age"] = (
            age if summary["maximum_age"] is None else max(int(summary["maximum_age"]), age)
        )
        summary["under_18"] = int(summary["under_18"] or 0) + (age < 18)
        summary["65_plus"] = int(summary["65_plus"] or 0) + (age >= 65)
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
        "parish_age_structure": {
            "status": "derived_2021_parish_age_sex_raked_to_global_controls",
            "rows": parish_age_rows,
        },
        "households": {
            "generated_household_count": len(households),
            "household_population": sum(len(row["_roles"]) for row in households),
            "mean_household_size": sum(len(row["_roles"]) for row in households) / len(households),
            "size_distribution": size_distribution,
            "type_rows": household_type_rows,
            "max_household_size": max(len(row["_roles"]) for row in households),
            "relational_age_checks": {
                "parent_child_reversals": parent_child_reversals,
                "minimum_parent_child_generation_gap": minimum_generation_gap,
                "maximum_couple_age_gap": max(couple_age_gaps, default=0),
                "relaxed_source_role_members": sum(
                    int(row.get("_role_relaxations", 0)) for row in households
                ),
            },
        },
        "housing": housing,
        "communal": {
            "generated_residents": sum(row["resident_count"] for row in settings),
            "generated_establishments": len(settings),
            "rows": communal_rows,
            "age_structure": communal_age_structure,
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
                "parish_age_sex_raking_to_global_margins_c1_v1",
                "household_type_counts_scaled_v1",
                "household_extra_member_allocation_v1",
                "housing_attribute_allocation_v1",
                "communal_setting_allocation_v1",
                "setting_specific_communal_age_allocation_c1_v1",
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
    mode_age_sex = _mode_age_sex_counts(controls, target)
    parish_age_sex_targets = build_parish_age_sex_targets(
        controls, target, target_parishes, mode_age_sex
    )
    communal_residents, private_age_sex_by_parish = _assign_communal_residents(
        settings,
        {
            parish: {
                (age, sex): count
                for (cell_parish, age, sex), count in parish_age_sex_targets.items()
                if cell_parish == parish
            }
            for parish in target_parishes
        },
        0,
        rng,
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
    _rebalance_household_parishes(households, private_parishes, private_age_sex_by_parish)
    baseline_private = sum(len(row["_roles"]) for row in households)
    private_target = target - communal_target
    if private_target - baseline_private < 0:
        raise DataBuildError("baseline household structures exceed the private population target")
    private_children_by_parish = {
        parish: sum(count for (age, _sex), count in pool.items() if age < DEPENDENCY_AGE)
        for parish, pool in private_age_sex_by_parish.items()
    }
    private_pensioners_by_parish = {
        parish: sum(count for (age, _sex), count in pool.items() if age >= PENSIONER_AGE)
        for parish, pool in private_age_sex_by_parish.items()
    }
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
        dependent_capacity = sum(
            HOUSEHOLD_MAX_SIZE[row["household_type"]] - len(row["_roles"])
            for row in households
            if row["home_parish"] == parish
            and row["household_type"]
            in {"Single parent (with dependent children)", "Couple with dependent children"}
        )
        pensioner_capacity = sum(
            HOUSEHOLD_MAX_SIZE[row["household_type"]] - len(row["_roles"])
            for row in households
            if row["home_parish"] == parish and row["household_type"] == "Two or more pensioners"
        )
        dependent_extra = min(
            max(0, private_children_by_parish[parish] - dependent_by_parish[parish]),
            parish_extra,
            dependent_capacity,
        )
        pensioner_extra = min(
            max(0, private_pensioners_by_parish[parish] - pensioner_by_parish[parish]),
            parish_extra - dependent_extra,
            pensioner_capacity,
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
            # The residual private-population remainder is not observed
            # household-role data.  Use any non-single household with
            # remaining structural capacity rather than concentrating it
            # in the small ``Other`` category in a parish with rounding
            # residuals.
            "other": set(HOUSEHOLD_BASE_ROLES) - {"Two or more pensioners", "Single pensioner"},
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
            _allocate_extra_roles(
                households, category, amount, rng, parish, allowed_types=eligible_types
            )
            remaining_extra -= amount
        if remaining_extra:
            raise DataBuildError(
                f"could not allocate {remaining_extra} plausible household members in {parish}"
            )
    _assign_housing_attributes(households, controls, rng)
    private_residents = _assign_private_residents(households, private_age_sex_by_parish, rng)
    residents = private_residents + communal_residents
    rng.shuffle(residents)
    for index, resident in enumerate(residents):
        resident["agent_id"] = f"agent-m2-{index:07d}"
    validation_checks = _validate_generated(
        config,
        residents,
        households,
        settings,
        target_parishes,
        mode_age_sex,
        parish_age_sex_targets,
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
        parish_age_sex_targets,
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
