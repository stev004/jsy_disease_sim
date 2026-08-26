"""Deterministic M4.1 school and care staffing allocation.

The allocator layers synthetic institutional roles onto existing M2/M3 agents.
It never edits M3 jobs or creates additional residents.  Official FTE and
regulatory-minimum inputs are kept in :mod:`staffing_evidence`; every placement
in this module is explicitly structural and synthetic.
"""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .data_pipeline import DataBuildError
from .population_structure_artifacts import M2PopulationInput, M3StructureInput
from .staffing_evidence import (
    CareStaffingEvidence,
    SchoolStaffingEvidence,
    StaffingEvidence,
    care_minimums,
    load_staffing_evidence,
)

FULL_POPULATION_TARGET = 104_540
EDUCATION_HEALTH_SECTOR = "education, health, and other services"


@dataclass(frozen=True)
class StaffingAllocation:
    """Synthetic staff placements and diagnostics consumed by M4 routes."""

    school_assignments: list[dict[str, Any]]
    care_assignments: list[dict[str, Any]]
    school_staff_by_class: dict[str, list[str]]
    school_staff_by_school_year: dict[tuple[str, str], list[str]]
    care_staff_by_setting: dict[str, list[str]]
    diagnostics: dict[str, Any]
    provenance: dict[str, Any]


def _stable_int(seed: int, *parts: object) -> int:
    payload = "|".join(str(part) for part in (seed, *parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def _ordered(ids: list[str], seed: int, *parts: object) -> list[str]:
    return sorted(ids, key=lambda agent_id: (_stable_int(seed, *parts, agent_id), agent_id))


def _allocate_counts(
    total: int, keys: list[str], weights: dict[str, float], seed: int, label: str
) -> dict[str, int]:
    """Allocate an exact integer total by largest remainder with stable ties."""

    if total < 0:
        raise ValueError("total must be non-negative")
    if not keys:
        if total:
            raise DataBuildError(f"cannot allocate {total} staff endpoints without schools")
        return {}
    positive = {key: max(0.0, float(weights.get(key, 0.0))) for key in keys}
    weight_sum = sum(positive.values())
    if weight_sum <= 0:
        positive = {key: 1.0 for key in keys}
        weight_sum = float(len(keys))
    raw = {key: total * positive[key] / weight_sum for key in keys}
    counts = {key: math.floor(raw[key]) for key in keys}
    remainder = total - sum(counts.values())
    ranked = sorted(
        keys,
        key=lambda key: (
            -(raw[key] - counts[key]),
            _stable_int(seed, "staff-allocation", label, key),
            key,
        ),
    )
    for key in ranked[:remainder]:
        counts[key] += 1
    return counts


def _fte_endpoints(fte: float, population_scale: float, fte_per_endpoint: float) -> int:
    if fte < 0 or population_scale <= 0 or fte_per_endpoint <= 0:
        raise ValueError("FTE conversion inputs must be positive except FTE")
    return math.ceil(fte * population_scale / fte_per_endpoint)


def _eligible_worker_ids(m2_input: M2PopulationInput, m3_input: M3StructureInput) -> list[str]:
    m2_by_agent = {row["agent_id"]: row for row in m2_input.residents}
    eligible: list[str] = []
    for row in m3_input.resident_structure:
        agent_id = row["agent_id"]
        sector = str(row.get("employment_sector") or "").lower()
        if (
            row["economic_status"] == "employed"
            and row["age"] >= 18
            and row.get("school_id") is None
            and m2_by_agent[agent_id].get("household_id") is not None
            and m2_by_agent[agent_id].get("care_setting_id") is None
            and EDUCATION_HEALTH_SECTOR in sector
        ):
            eligible.append(agent_id)
    return sorted(set(eligible))


def _school_staff(
    m2_input: M2PopulationInput,
    m3_input: M3StructureInput,
    evidence: SchoolStaffingEvidence,
    seed: int,
    fte_per_endpoint: float,
    include_leadership: bool,
    population_scale: float,
    used_agents: set[str],
) -> tuple[
    list[dict[str, Any]],
    dict[str, list[str]],
    dict[tuple[str, str], list[str]],
    dict[str, Any],
    set[str],
]:
    schools = sorted(m3_input.schools, key=lambda row: row["school_id"])
    classes_by_school: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in m3_input.classes:
        classes_by_school[row["school_id"]].append(row)
    for rows in classes_by_school.values():
        rows.sort(key=lambda row: row["class_id"])
    school_ids = [row["school_id"] for row in schools]
    pupil_weights = {row["school_id"]: float(row["pupil_count"]) for row in schools}
    class_weights = {
        school_id: float(len(classes_by_school[school_id])) for school_id in school_ids
    }
    role_targets = {
        "teacher": _fte_endpoints(evidence.teacher_fte_2025, population_scale, fte_per_endpoint),
        "teaching_assistant": _fte_endpoints(
            evidence.teaching_assistant_fte_2025, population_scale, fte_per_endpoint
        ),
    }
    if include_leadership:
        role_targets["head_deputy"] = _fte_endpoints(
            evidence.heads_deputies_fte_2025, population_scale, fte_per_endpoint
        )

    eligible = [
        agent_id
        for agent_id in _eligible_worker_ids(m2_input, m3_input)
        if agent_id not in used_agents
    ]
    needed = sum(role_targets.values())
    if len(eligible) < needed:
        raise DataBuildError(
            f"education-health synthetic worker pool has {len(eligible)} available agents, "
            f"but school staffing conversion requires {needed}"
        )
    eligible = _ordered(eligible, seed, "school-staff")
    school_assignments: list[dict[str, Any]] = []
    staff_by_class: dict[str, list[str]] = defaultdict(list)
    staff_by_school_year: dict[tuple[str, str], list[str]] = defaultdict(list)
    selected: set[str] = set()
    school_type_by_id = {row["school_id"]: row["school_type"] for row in schools}

    for role in ("teacher", "teaching_assistant", "head_deputy"):
        target = role_targets.get(role, 0)
        if target == 0:
            continue
        weights = class_weights if role == "teacher" else pupil_weights
        school_counts = _allocate_counts(target, school_ids, weights, seed, role)
        role_agents = eligible[:target]
        eligible = eligible[target:]
        assignment_index = 0
        for school_id in school_ids:
            school_classes = classes_by_school[school_id]
            if not school_classes:
                raise DataBuildError(f"school has no classes for staffing assignment: {school_id}")
            for _ in range(school_counts[school_id]):
                agent_id = role_agents[assignment_index]
                assignment_index += 1
                selected.add(agent_id)
                class_row = school_classes[
                    _stable_int(seed, "school-class", role, school_id, assignment_index)
                    % len(school_classes)
                ]
                class_id = class_row["class_id"] if role != "head_deputy" else None
                school_year = class_row["school_year"]
                row = {
                    "agent_id": agent_id,
                    "role": role,
                    "school_id": school_id,
                    "school_type": school_type_by_id[school_id],
                    "school_year": school_year,
                    "class_id": class_id,
                    "assignment_status": "synthetic",
                    "provenance_status": "structural_assumption",
                }
                school_assignments.append(row)
                staff_by_school_year[(school_id, school_year)].append(agent_id)
                if class_id is not None:
                    staff_by_class[class_id].append(agent_id)

    duplicate_agents = len(school_assignments) - len(selected)
    if duplicate_agents:
        raise DataBuildError("school staffing selected a synthetic agent more than once")
    type_summary: dict[str, dict[str, Any]] = {}
    for school_type in sorted({row["school_type"] for row in schools}):
        school_type_ids = {row["school_id"] for row in schools if row["school_type"] == school_type}
        pupils = sum(row["pupil_count"] for row in schools if row["school_id"] in school_type_ids)
        staff_rows = [row for row in school_assignments if row["school_id"] in school_type_ids]
        type_summary[school_type] = {
            "schools": len(school_type_ids),
            "pupils": pupils,
            "staff": len(staff_rows),
            "pupil_staff_ratio": pupils / len(staff_rows) if staff_rows else None,
            "staff_by_role": {
                role: sum(row["role"] == role for row in staff_rows) for role in role_targets
            },
        }
    staff_by_school = {
        school_id: {
            "school_type": school_type_by_id[school_id],
            "pupils": next(row["pupil_count"] for row in schools if row["school_id"] == school_id),
            "staff": sum(row["school_id"] == school_id for row in school_assignments),
            "pupil_staff_ratio": (
                next(row["pupil_count"] for row in schools if row["school_id"] == school_id)
                / sum(row["school_id"] == school_id for row in school_assignments)
            ),
        }
        for school_id in school_ids
    }
    staff_with_households = sum(
        next(row for row in m2_input.residents if row["agent_id"] == agent_id).get("household_id")
        is not None
        for agent_id in selected
    )
    diagnostics = {
        "observed_fte_controls": {
            "2024": {
                "children": evidence.children_2024,
                "teachers": evidence.teacher_fte_2024,
                "teaching_assistants": evidence.teaching_assistant_fte_2024,
            },
            "2025": {
                "teachers_and_lecturers": evidence.teacher_fte_2025,
                "teaching_assistants": evidence.teaching_assistant_fte_2025,
                "heads_and_deputies": evidence.heads_deputies_fte_2025,
            },
        },
        "source_universe_2024": evidence.source_universe_2024,
        "source_universe_2025": evidence.source_universe_2025,
        "primary_reference": evidence.primary_reference,
        "synthetic_staff_endpoints": len(selected),
        "synthetic_staff_by_role": {
            role: sum(row["role"] == role for row in school_assignments) for role in role_targets
        },
        "fte_to_endpoint_conversion": {
            "status": "derived",
            "structural_assumption_status": "structural_assumption",
            "fte_per_synthetic_endpoint": fte_per_endpoint,
            "population_scale": population_scale,
            "rule": "ceil(observed FTE * population scale / FTE per synthetic endpoint)",
            "actual_headcount_status": "unknown",
        },
        "staff_by_school_type": type_summary,
        "staff_by_school": staff_by_school,
        "class_core_memberships": {
            "classes": len(m3_input.classes),
            "classes_with_staff": len(staff_by_class),
            "staff_assignments": sum(len(staff_ids) for staff_ids in staff_by_class.values()),
            "staff_by_class": {
                class_id: len(staff_ids) for class_id, staff_ids in sorted(staff_by_class.items())
            },
        },
        "allocation_pool": {
            "employment_sector": EDUCATION_HEALTH_SECTOR,
            "eligibility": (
                "existing employed M3 adults with private-household membership, excluding "
                "pupils, communal residents and already allocated institutional staff"
            ),
            "identity_status": "synthetic_worker_overlay",
        },
        "staff_assigned_to_zero_schools": 0,
        "duplicate_staff_assignments": duplicate_agents,
        "staff_with_household_bridge_membership": staff_with_households,
        "workforce_universe_mismatch": (
            "2024 children and 2025 CYPES FTE universes are not forced to reconcile to the "
            "M1 13,991 pupil control; synthetic placement is structural only."
        ),
    }
    return (
        school_assignments,
        {key: sorted(value) for key, value in staff_by_class.items()},
        {key: sorted(value) for key, value in staff_by_school_year.items()},
        diagnostics,
        selected,
    )


def _care_staff(
    m2_input: M2PopulationInput,
    m3_input: M3StructureInput,
    evidence: CareStaffingEvidence,
    seed: int,
    coverage_multiplier: float,
    used_agents: set[str],
) -> tuple[list[dict[str, Any]], dict[str, list[str]], dict[str, Any], set[str]]:
    settings = {
        row["setting_id"]: row
        for row in m2_input.communal_settings
        if "with nursing" in row["setting_type"].lower()
        or "without nursing" in row["setting_type"].lower()
    }
    residents_by_setting: dict[str, list[str]] = defaultdict(list)
    for row in m2_input.residents:
        setting_id = row.get("care_setting_id")
        if isinstance(setting_id, str) and setting_id in settings:
            residents_by_setting[setting_id].append(row["agent_id"])
    eligible = [
        agent_id
        for agent_id in _eligible_worker_ids(m2_input, m3_input)
        if agent_id not in used_agents
    ]
    needed_total = 0
    requirements: dict[str, dict[str, Any]] = {}
    for setting_id in sorted(settings):
        resident_count = len(residents_by_setting.get(setting_id, []))
        if resident_count == 0:
            continue
        minimum = care_minimums(settings[setting_id]["setting_type"], resident_count)
        support_required = math.ceil(
            max(int(minimum["support_day_required"]), int(minimum["support_night_required"]))
            * coverage_multiplier
        )
        nurse_required = math.ceil(
            max(int(minimum["nurse_day_required"]), int(minimum["nurse_night_required"]))
            * coverage_multiplier
        )
        requirements[setting_id] = {
            **minimum,
            "support_unique_roster_required": support_required,
            "nurse_unique_roster_required": nurse_required,
            "coverage_multiplier": coverage_multiplier,
            "roster_assumption_status": "structural_assumption",
            "regulatory_status": evidence.provenance_status,
        }
        needed_total += support_required + nurse_required
    if len(eligible) < needed_total:
        raise DataBuildError(
            f"education-health synthetic worker pool has {len(eligible)} care-eligible agents, "
            f"but care roster derivation requires {needed_total}"
        )
    eligible = _ordered(eligible, seed, "care-staff")
    assignments: list[dict[str, Any]] = []
    staff_by_setting: dict[str, list[str]] = defaultdict(list)
    selected: set[str] = set()
    cursor = 0
    for setting_id in sorted(requirements):
        requirement = requirements[setting_id]
        setting_type = settings[setting_id]["setting_type"]
        for role, count in (
            ("care_support_worker", int(requirement["support_unique_roster_required"])),
            ("nurse", int(requirement["nurse_unique_roster_required"])),
        ):
            for agent_id in eligible[cursor : cursor + count]:
                cursor += 1
                if agent_id in selected:
                    raise DataBuildError("care staffing selected a synthetic agent more than once")
                selected.add(agent_id)
                assignments.append(
                    {
                        "agent_id": agent_id,
                        "role": role,
                        "setting_id": setting_id,
                        "setting_type": setting_type,
                        "assignment_status": "synthetic",
                        "provenance_status": "synthetic",
                        "regulatory_status": evidence.provenance_status,
                        "shift_pattern": "day_and_night_roster",
                    }
                )
                staff_by_setting[setting_id].append(agent_id)

    failing: list[str] = []
    staff_counts: dict[str, dict[str, int]] = {}
    for setting_id, requirement in requirements.items():
        rows = [row for row in assignments if row["setting_id"] == setting_id]
        support = sum(row["role"] == "care_support_worker" for row in rows)
        nurses = sum(row["role"] == "nurse" for row in rows)
        staff_counts[setting_id] = {
            "care_support_workers": support,
            "nurses": nurses,
        }
        if support < max(
            int(requirement["support_day_required"]), int(requirement["support_night_required"])
        ) or nurses < max(
            int(requirement["nurse_day_required"]), int(requirement["nurse_night_required"])
        ):
            failing.append(setting_id)
    m2_by_agent = {row["agent_id"]: row for row in m2_input.residents}
    care_residents = {agent_id for ids in residents_by_setting.values() for agent_id in ids}
    overlap = selected & care_residents
    if overlap:
        raise DataBuildError("care staff overlap with care residents")
    staff_with_households = sum(
        m2_by_agent[agent_id].get("household_id") is not None for agent_id in selected
    )
    category_counts = {
        "nursing": sum("with nursing" in row["setting_type"].lower() for row in settings.values()),
        "non_nursing": sum(
            "without nursing" in row["setting_type"].lower() for row in settings.values()
        ),
    }
    category_residents = {
        "nursing": sum(
            len(residents_by_setting.get(setting_id, []))
            for setting_id, row in settings.items()
            if "with nursing" in row["setting_type"].lower()
        ),
        "non_nursing": sum(
            len(residents_by_setting.get(setting_id, []))
            for setting_id, row in settings.items()
            if "without nursing" in row["setting_type"].lower()
        ),
    }
    diagnostics = {
        "source_id": evidence.source_id,
        "source_sha256": evidence.source_sha256,
        "source_scope": evidence.source_scope,
        "nursing_rule_notes": list(evidence.nursing_rule_notes),
        "regulatory_status": "regulatory_minimum",
        "nursing_establishments": category_counts["nursing"],
        "non_nursing_establishments": category_counts["non_nursing"],
        "excluded_other_communal_establishments": sum(
            "with nursing" not in row["setting_type"].lower()
            and "without nursing" not in row["setting_type"].lower()
            for row in m2_input.communal_settings
        ),
        "residents_by_category": category_residents,
        "regulatory_minimum_by_setting": requirements,
        "derived_day_night_requirements": requirements,
        "synthetic_care_support_workers": sum(
            row["role"] == "care_support_worker" for row in assignments
        ),
        "synthetic_nurses": sum(row["role"] == "nurse" for row in assignments),
        "roster_assumption": {
            "coverage_multiplier": coverage_multiplier,
            "status": "structural_assumption",
            "rule": "ceil(max(day requirement, night requirement) * coverage multiplier)",
            "interpretation": (
                "A concurrent regulatory minimum is converted to unique synthetic endpoints "
                "for a daily network; it is not an observed annual workforce headcount."
            ),
        },
        "staff_per_setting": staff_counts,
        "resident_staff_edges": (
            "bounded resident cohorts connect to assigned staff; no all-pairs setting clique"
        ),
        "cross_facility_staff": 0,
        "staff_household_community_bridge_membership": staff_with_households,
        "settings_failing_minimum": failing,
        "actual_staff_roster_status": "unknown",
    }
    return (
        assignments,
        {key: sorted(value) for key, value in staff_by_setting.items()},
        diagnostics,
        selected,
    )


def build_staffing_allocation(
    root: Path,
    m2_input: M2PopulationInput,
    m3_input: M3StructureInput,
    *,
    seed: int,
    fte_per_endpoint: float,
    care_coverage_multiplier: float,
    include_leadership: bool = True,
) -> StaffingAllocation:
    """Load evidence and deterministically allocate school/care staff endpoints."""

    evidence: StaffingEvidence = load_staffing_evidence(root)
    population_scale = m3_input.manifest.actual_population / FULL_POPULATION_TARGET
    if population_scale <= 0:
        raise DataBuildError("M3 population must be positive for staffing allocation")
    school_assignments, staff_by_class, staff_by_school_year, school_diagnostics, school_ids = (
        _school_staff(
            m2_input,
            m3_input,
            evidence.school,
            seed,
            fte_per_endpoint,
            include_leadership,
            population_scale,
            set(),
        )
    )
    care_assignments, staff_by_setting, care_diagnostics, care_ids = _care_staff(
        m2_input,
        m3_input,
        evidence.care,
        seed,
        care_coverage_multiplier,
        school_ids,
    )
    all_staff = school_ids | care_ids
    m2_ids = {row["agent_id"] for row in m2_input.residents}
    if not all_staff <= m2_ids:
        raise DataBuildError("staff allocation introduced an agent outside M2")
    if len(all_staff) != len(school_assignments) + len(care_assignments):
        raise DataBuildError("staff allocation duplicated an agent across institutional roles")

    provenance = {
        "school": {
            "source_ids": list(evidence.school.source_ids),
            "source_hashes": evidence.school.source_hashes,
            "observed_controls": {
                "teacher_fte_2024": evidence.school.teacher_fte_2024,
                "teaching_assistant_fte_2024": evidence.school.teaching_assistant_fte_2024,
                "teacher_fte_2025": evidence.school.teacher_fte_2025,
                "teaching_assistant_fte_2025": evidence.school.teaching_assistant_fte_2025,
                "heads_deputies_fte_2025": evidence.school.heads_deputies_fte_2025,
            },
            "statuses": {
                "official_fte": "observed",
                "fte_to_endpoint_conversion": "derived",
                "school_assignment": "synthetic",
                "class_assignment": "structural_assumption",
                "actual_roster": "unknown",
            },
        },
        "care": {
            "source_id": evidence.care.source_id,
            "source_sha256": evidence.care.source_sha256,
            "statuses": {
                "regulatory_ratio": "regulatory_minimum",
                "roster_derivation": "derived",
                "coverage_multiplier": "structural_assumption",
                "setting_assignment": "synthetic",
                "actual_roster": "unknown",
            },
        },
    }
    diagnostics = {
        "school": school_diagnostics,
        "care": care_diagnostics,
        "all_staff_endpoints": len(all_staff),
        "school_staff_endpoints": len(school_ids),
        "care_staff_endpoints": len(care_ids),
        "staff_role_overlap": 0,
        "worker_accounting": {
            "m3_unique_workers_unchanged": True,
            "m3_primary_jobs_unchanged": True,
            "m3_secondary_jobs_unchanged": True,
            "m3_filled_jobs_unchanged": True,
            "institutional_roles_are_overlay_memberships": True,
        },
    }
    return StaffingAllocation(
        school_assignments=school_assignments,
        care_assignments=care_assignments,
        school_staff_by_class=staff_by_class,
        school_staff_by_school_year=staff_by_school_year,
        care_staff_by_setting=staff_by_setting,
        diagnostics=diagnostics,
        provenance=provenance,
    )
