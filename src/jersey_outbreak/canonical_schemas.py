"""Strict row contracts for Milestone 1 canonical aggregate tables.

These schemas describe observed and derived aggregate controls only.  They do
not represent synthetic people, households, workplaces, schools or contacts.
"""

from __future__ import annotations

from typing import Literal

from pydantic import field_validator
from pydantic.types import StrictFloat, StrictInt, StrictStr

from .contracts import NonEmptyString, StrictModel

Number = StrictInt | StrictFloat
ObservationStatus = Literal["observed", "derived"]


class CanonicalProvenance(StrictModel):
    """Common provenance columns carried by every canonical row."""

    schema_version: Literal["1.0"] = "1.0"
    source_id: NonEmptyString
    source_sha256: StrictStr
    evidence_source_id: NonEmptyString | None = None
    reference_period: NonEmptyString
    observation_status: ObservationStatus
    source_locator: NonEmptyString
    transformation_id: NonEmptyString

    @field_validator("source_sha256")
    @classmethod
    def validate_hash(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("source_sha256 must be a lowercase 64-character hexadecimal digest")
        return value


class PopulationTotalRow(CanonicalProvenance):
    measure: NonEmptyString
    value: Number
    unit: NonEmptyString


class AgeSexRow(CanonicalProvenance):
    age_band: NonEmptyString
    sex: NonEmptyString
    count: StrictInt

    @field_validator("count")
    @classmethod
    def validate_count(cls, value: int) -> int:
        if value < 0:
            raise ValueError("age/sex count must be non-negative")
        return value


class ParishPopulationRow(CanonicalProvenance):
    parish: NonEmptyString
    population: StrictInt
    density_person_km2: StrictFloat | StrictInt

    @field_validator("population", "density_person_km2")
    @classmethod
    def validate_nonnegative(cls, value: int | float) -> int | float:
        if value < 0:
            raise ValueError("parish population and density must be non-negative")
        return value


class ParishAgeSexRow(CanonicalProvenance):
    parish: NonEmptyString
    age_band: NonEmptyString
    sex: NonEmptyString
    count: StrictInt

    @field_validator("count")
    @classmethod
    def validate_count(cls, value: int) -> int:
        if value < 0:
            raise ValueError("parish age/sex count must be non-negative")
        return value


class HouseholdTypeRow(CanonicalProvenance):
    household_type: NonEmptyString
    households: StrictInt

    @field_validator("households")
    @classmethod
    def validate_households(cls, value: int) -> int:
        if value < 0:
            raise ValueError("household count must be non-negative")
        return value


class MeasureRow(CanonicalProvenance):
    """Stable long-form row for housing and communal aggregate controls."""

    measure: NonEmptyString
    category: NonEmptyString
    subcategory: StrictStr | None = None
    value: Number
    unit: NonEmptyString


class EmploymentSectorRow(CanonicalProvenance):
    measure: NonEmptyString
    sector: NonEmptyString
    sex: StrictStr | None = None
    value: Number
    unit: NonEmptyString

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: int | float) -> int | float:
        if value < 0:
            raise ValueError("employment value must be non-negative")
        return value


class WorkplaceSizeRow(CanonicalProvenance):
    sector: NonEmptyString
    size_band: NonEmptyString
    count: StrictInt | None = None
    upper_bound: StrictInt | None = None
    censoring: Literal["exact", "positive_less_than"]
    unit: NonEmptyString

    @field_validator("count", "upper_bound")
    @classmethod
    def validate_nonnegative(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("workplace size counts must be non-negative")
        return value

    @field_validator("censoring")
    @classmethod
    def validate_censoring(cls, value: str) -> str:
        return value


class WorkplaceDestinationRow(CanonicalProvenance):
    measure: NonEmptyString
    category: NonEmptyString
    subcategory: StrictStr | None = None
    value: Number
    unit: NonEmptyString

    @field_validator("value")
    @classmethod
    def validate_percent_or_count(cls, value: int | float) -> int | float:
        if value < 0:
            raise ValueError("workplace destination value must be non-negative")
        if value > 100:
            raise ValueError("workplace destination percentage must be at most 100")
        return value


class CommuteModeRow(CanonicalProvenance):
    parish: NonEmptyString
    mode: NonEmptyString
    workers: StrictInt | None = None
    upper_bound: StrictInt | None = None
    censoring: Literal["exact", "positive_less_than"]

    @field_validator("workers", "upper_bound")
    @classmethod
    def validate_workers(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("commuting workers must be non-negative")
        return value


class SchoolStudentRow(CanonicalProvenance):
    year: StrictInt
    school_type: NonEmptyString
    students: StrictInt

    @field_validator("students")
    @classmethod
    def validate_students(cls, value: int) -> int:
        if value < 0:
            raise ValueError("student count must be non-negative")
        return value


class CommunalSettingRow(CanonicalProvenance):
    measure: NonEmptyString
    setting: NonEmptyString
    value: StrictInt
    unit: NonEmptyString

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: int) -> int:
        if value < 0:
            raise ValueError("communal setting value must be non-negative")
        return value


class PassengerArrivalRow(CanonicalProvenance):
    year: StrictInt
    mode: NonEmptyString
    passengers: StrictInt

    @field_validator("passengers")
    @classmethod
    def validate_passengers(cls, value: int) -> int:
        if value < 0:
            raise ValueError("passenger arrivals must be non-negative")
        return value


class DerivedControlRow(CanonicalProvenance):
    measure: NonEmptyString
    category: NonEmptyString
    value: Number
    unit: NonEmptyString
    reference: NonEmptyString
    source_table: NonEmptyString
    check_status: Literal["passed", "warning"]
