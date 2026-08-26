"""Frozen official staffing evidence and regulatory rules for M4.1.

This module is deliberately separate from route generation.  The numeric school
controls come from two Government of Jersey FOI releases.  The care controls
come from Appendix 4 of the 2026 Jersey Care Commission standard and describe
regulatory minima, not observed rosters.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .data_pipeline import DataBuildError, load_source_registry
from .hashing import sha256_file

StaffingProvenanceStatus = Literal[
    "observed",
    "regulatory_minimum",
    "derived",
    "structural_assumption",
    "synthetic",
    "unknown",
]

EDUCATION_2024_SOURCE = "education_staff_2024_foi_html"
EDUCATION_2025_SOURCE = "education_staff_2025_foi_html"
CARE_2026_SOURCE = "care_commission_accommodation_standards_2026_pdf"


@dataclass(frozen=True)
class SchoolStaffingEvidence:
    """Observed CYPES education staffing controls and their universes."""

    children_2024: int
    teacher_fte_2024: float
    teaching_assistant_fte_2024: float
    teacher_fte_2025: float
    teaching_assistant_fte_2025: float
    heads_deputies_fte_2025: float
    source_ids: tuple[str, ...]
    source_hashes: dict[str, str]
    source_universe_2024: str
    source_universe_2025: str
    primary_reference: str


@dataclass(frozen=True)
class CareStaffingEvidence:
    """Regulatory minima from the Care Commission accommodation standard."""

    source_id: str
    source_sha256: str
    source_scope: str
    non_nursing_support_day_ratio: tuple[int, int]
    non_nursing_support_night_ratio: tuple[int, int]
    nursing_support_day_ratio: tuple[int, int]
    nursing_support_night_ratio: tuple[int, int]
    specialist_dementia_support_day_ratio: tuple[int, int]
    specialist_dementia_support_night_ratio: tuple[int, int]
    nursing_nurse_table: tuple[tuple[str, int, int], ...]
    nursing_rule_notes: tuple[str, ...]
    provenance_status: StaffingProvenanceStatus = "regulatory_minimum"


@dataclass(frozen=True)
class StaffingEvidence:
    school: SchoolStaffingEvidence
    care: CareStaffingEvidence


def _verify_text_tokens(path: Path, tokens: tuple[str, ...]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise DataBuildError(f"cannot read frozen staffing source {path}: {exc}") from exc
    missing = [token for token in tokens if token not in text]
    if missing:
        raise DataBuildError(
            f"staffing source {path} is missing expected official values: {missing}"
        )


def _verify_source(context, source_id: str) -> str:
    source = context.source(source_id)
    if source.status != "official":
        raise DataBuildError(f"staffing source is not marked official: {source_id}")
    path = context.artifact_path(source_id)
    if source.sha256 is None or not path.is_file():
        raise DataBuildError(f"staffing source snapshot is unavailable: {source_id}")
    actual_hash = sha256_file(path)
    if actual_hash != source.sha256:
        raise DataBuildError(f"staffing source hash mismatch: {path}")
    return actual_hash


def load_staffing_evidence(root: Path) -> StaffingEvidence:
    """Validate frozen official snapshots and return typed controls."""

    context = load_source_registry(root.resolve())
    education_2024_hash = _verify_source(context, EDUCATION_2024_SOURCE)
    education_2025_hash = _verify_source(context, EDUCATION_2025_SOURCE)
    care_hash = _verify_source(context, CARE_2026_SOURCE)
    _verify_text_tokens(
        context.artifact_path(EDUCATION_2024_SOURCE),
        ("14,061", "1052.45", "457.82", "14 February 2024"),
    )
    _verify_text_tokens(
        context.artifact_path(EDUCATION_2025_SOURCE),
        ("86.00", "983.30", "507.15", "16 July 2025"),
    )
    care_path = context.artifact_path(CARE_2026_SOURCE)
    if care_path.stat().st_size < 100_000:
        raise DataBuildError(f"care standard snapshot is unexpectedly small: {care_path}")

    school = SchoolStaffingEvidence(
        children_2024=14_061,
        teacher_fte_2024=1052.45,
        teaching_assistant_fte_2024=457.82,
        teacher_fte_2025=983.30,
        teaching_assistant_fte_2025=507.15,
        heads_deputies_fte_2025=86.00,
        source_ids=(EDUCATION_2024_SOURCE, EDUCATION_2025_SOURCE),
        source_hashes={
            EDUCATION_2024_SOURCE: education_2024_hash,
            EDUCATION_2025_SOURCE: education_2025_hash,
        },
        source_universe_2024=(
            "Government of Jersey education universe reported in January 2024 school census: "
            "Government primary and secondary schools, special schools, non-provided schools, "
            "Highlands College Years 12/13 and Electively Home Educated children."
        ),
        source_universe_2025=(
            "CYPES department payroll FTE as at 16 July 2025; the response reports pay groups "
            "within CYPES and is not a whole-island education workforce headcount."
        ),
        primary_reference=(
            "2025-07-16 CYPES FTE table; 2024 release retained for universe comparison"
        ),
    )
    care = CareStaffingEvidence(
        source_id=CARE_2026_SOURCE,
        source_sha256=care_hash,
        source_scope="Care and support services with accommodation; Appendix 4",
        non_nursing_support_day_ratio=(1, 10),
        non_nursing_support_night_ratio=(1, 15),
        nursing_support_day_ratio=(1, 5),
        nursing_support_night_ratio=(1, 10),
        specialist_dementia_support_day_ratio=(1, 5),
        specialist_dementia_support_night_ratio=(1, 10),
        nursing_nurse_table=(
            ("up_to_10", 1, 1),
            ("over_10_to_20", 1, 0),
            ("over_20_to_40", 2, 1),
            ("over_40", 3, 2),
        ),
        nursing_rule_notes=(
            "The over-10-to-20 nurse row is the base minimum; acute-care cases have higher "
            "requirements under the standard.",
            "The standard permits an on-call nurse exception for some stable settings with "
            "up to five people previously receiving personal care; it is not applied here.",
            "Registered nurses are not substituted by nursing support workers under the "
            "general table.",
        ),
    )
    return StaffingEvidence(school=school, care=care)


def ceil_ratio(numerator: int, denominator: int) -> int:
    """Return the minimum whole staff count satisfying a ratio."""

    if numerator < 0 or denominator <= 0:
        raise ValueError("ratio inputs must be non-negative numerator and positive denominator")
    return math.ceil(numerator / denominator)


def nursing_nurse_minimum(nursing_residents: int) -> tuple[int, int]:
    """Return Appendix 4's minimum day/night nurse counts for a setting."""

    if nursing_residents <= 0:
        raise ValueError("nursing_residents must be positive")
    if nursing_residents <= 10:
        return 1, 1
    if nursing_residents <= 20:
        return 1, 0
    if nursing_residents <= 40:
        return 2, 1
    return 3, 2


def care_minimums(setting_type: str, resident_count: int) -> dict[str, int | str | bool]:
    """Calculate non-specialist regulatory minima for one supported care home."""

    if resident_count <= 0:
        raise ValueError("resident_count must be positive")
    lowered = setting_type.lower()
    if "without nursing" in lowered:
        category = "non_nursing"
        support_day = ceil_ratio(resident_count, 10)
        support_night = ceil_ratio(resident_count, 15)
        nurse_day = nurse_night = 0
    elif "with nursing" in lowered:
        category = "nursing"
        support_day = ceil_ratio(resident_count, 5)
        support_night = ceil_ratio(resident_count, 10)
        nurse_day, nurse_night = nursing_nurse_minimum(resident_count)
    else:
        raise ValueError(f"unsupported care-home category: {setting_type}")
    return {
        "category": category,
        "resident_count": resident_count,
        "support_day_required": support_day,
        "support_night_required": support_night,
        "nurse_day_required": nurse_day,
        "nurse_night_required": nurse_night,
        "specialist_dementia_applied": False,
    }
