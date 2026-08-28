"""Strict Milestone 8 travel, visitor, seasonality and risk contracts.

The travel layer is intentionally separate from the permanent resident tables.
All visitor quantities that are not directly observed are explicit scenario
controls and carry provenance metadata.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date
from math import isfinite
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from .contracts import NonEmptyString, StrictModel
from .hashing import canonical_json_bytes, sha256_bytes

TravelMode = Literal["disabled", "generic_import_only", "explicit_travel", "both"]
TravellerType = Literal[
    "OVERNIGHT_ACCOMMODATION_VISITOR",
    "STAYING_WITH_RESIDENTS",
    "DAY_VISITOR",
    "RETURNING_RESIDENT",
]
EntryMode = Literal["AIRPORT", "FERRY"]
AccommodationType = Literal["HOTEL_GUEST", "HOST_HOUSEHOLD", "OTHER_VISITOR_ACCOMMODATION", "NONE"]
LocalTransportType = Literal[
    "BUS", "PRIVATE_RENTAL_CAR", "TAXI_RIDE", "HOST_PICKUP", "WALKING_OTHER"
]
ArrivalDiseaseState = Literal["susceptible", "exposed", "infectious", "recovered"]
RiskStratum = Literal[
    "general_resident",
    "older_resident",
    "care_resident",
    "care_staff",
    "occupational_exposure",
    "visitor_travel_exposure",
]

TRAVEL_ROUTE_IDS: tuple[str, ...] = (
    "arrival_terminal",
    "visitor_party",
    "visitor_accommodation",
    "visitor_host_household",
    "visitor_transit",
    "visitor_community_indoor",
    "visitor_community_outdoor",
)

PARAMETER_STATUSES = Literal[
    "observed",
    "derived",
    "literature_prior",
    "calibrated",
    "scenario_assumption",
]


def _default_transport_probabilities() -> dict[LocalTransportType, float]:
    return {
        "BUS": 0.45,
        "PRIVATE_RENTAL_CAR": 0.23,
        "TAXI_RIDE": 0.12,
        "HOST_PICKUP": 0.10,
        "WALKING_OTHER": 0.10,
    }


class TravelParameter(StrictModel):
    """One M8 control and its auditable provenance."""

    value: float | int | bool | str | None = None
    distribution: NonEmptyString = "fixed"
    units: NonEmptyString
    status: PARAMETER_STATUSES = "scenario_assumption"
    source_ids: list[NonEmptyString] = Field(default_factory=list)
    derivation: NonEmptyString | None = None
    sensitivity_required: bool = True
    notes: NonEmptyString


class SeasonalityProfile(StrictModel):
    """A bounded, deterministic monthly multiplier profile."""

    profile_id: NonEmptyString
    monthly_multipliers: tuple[float, ...] = (1.0,) * 12
    normalization: Literal["day_weighted_annual_mean_one", "mean_one"] = (
        "day_weighted_annual_mean_one"
    )
    minimum: float = Field(default=0.0, ge=0.0)
    maximum: float = Field(default=2.0, gt=0.0)
    status: PARAMETER_STATUSES = "scenario_assumption"
    source_ids: list[NonEmptyString] = Field(default_factory=list)
    notes: NonEmptyString = "Synthetic bounded monthly scenario profile; not a forecast."

    @field_validator("monthly_multipliers", mode="before")
    @classmethod
    def normalize_values(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_profile(self) -> SeasonalityProfile:
        if len(self.monthly_multipliers) != 12:
            raise ValueError("seasonality profile must contain exactly 12 monthly multipliers")
        if any(not isfinite(float(value)) for value in self.monthly_multipliers):
            raise ValueError("seasonality multipliers must be finite")
        if any(value < self.minimum or value > self.maximum for value in self.monthly_multipliers):
            raise ValueError("seasonality multiplier falls outside its declared bounds")
        if sum(self.monthly_multipliers) <= 0:
            raise ValueError("seasonality profile must have positive total intensity")
        return self

    @property
    def config_hash(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.model_dump(mode="json")))

    def multiplier(self, when: date) -> float:
        value = float(self.monthly_multipliers[when.month - 1])
        # ``mean_one`` is retained as an input alias for M8 configuration
        # compatibility, but M8.1 gives it the corrected day-weighted meaning.
        days = [monthrange(when.year, month)[1] for month in range(1, 13)]
        weighted_mean = sum(
            multiplier * days[index] for index, multiplier in enumerate(self.monthly_multipliers)
        ) / sum(days)
        value /= weighted_mean
        return value


class TravelInterventionConfig(StrictModel):
    """Prospective travel intervention controls."""

    arrival_volume_multiplier: float = Field(default=1.0, ge=0.0, le=1.0)
    testing_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    test_sensitivity: float = Field(default=1.0, ge=0.0, le=1.0)
    test_specificity: float = Field(default=1.0, ge=0.0, le=1.0)
    test_result_delay_days: int = Field(default=0, ge=0, le=30)
    quarantine_positive_only: bool = True
    quarantine_all_arrivals: bool = False
    quarantine_duration_days: int = Field(default=0, ge=0, le=366)
    quarantine_start_delay_days: int = Field(default=0, ge=0, le=30)
    quarantine_adherence: float = Field(default=0.0, ge=0.0, le=1.0)
    quarantine_external_route_multiplier: float = Field(default=0.0, ge=0.0, le=1.0)
    quarantine_accommodation_multiplier: float = Field(default=1.0, ge=0.0, le=1.0)
    terminal_contact_multiplier: float = Field(default=1.0, ge=0.0, le=1.0)
    travel_acquisition_multiplier: float = Field(default=1.0, ge=0.0, le=1.0)
    traveller_vaccination_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    traveller_vaccination_efficacy: float = Field(default=0.0, ge=0.0, le=1.0)
    traveller_vaccination_infectiousness_efficacy: float = Field(default=0.0, ge=0.0, le=1.0)
    traveller_vaccination_protection_delay_days: int = Field(default=0, ge=0, le=366)
    traveller_vaccination_waning_days: int | None = Field(default=None, ge=1, le=3650)

    @model_validator(mode="after")
    def validate_quarantine(self) -> TravelInterventionConfig:
        if self.quarantine_positive_only and self.quarantine_all_arrivals:
            raise ValueError(
                "quarantine_positive_only and quarantine_all_arrivals are mutually exclusive"
            )
        if (
            self.traveller_vaccination_waning_days is not None
            and self.traveller_vaccination_protection_delay_days
            >= self.traveller_vaccination_waning_days
        ):
            raise ValueError("traveller vaccination waning must follow its protection delay")
        # Adherence=0 is intentionally valid: it is the exact neutral case for
        # a configured quarantine policy.
        return self

    @property
    def config_hash(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.model_dump(mode="json")))


class HighRiskConfig(StrictModel):
    """Conservative targeting metadata; no severity model is implied."""

    older_age_threshold: int = Field(default=65, ge=50, le=95)
    include_care_residents: bool = True
    include_care_staff: bool = True
    include_occupational_exposure: bool = True
    include_visitor_travel_exposure: bool = True
    occupational_sectors: tuple[NonEmptyString, ...] = ()
    biological_risk_multiplier: float = Field(default=1.0, ge=0.0, le=1.0)
    status: PARAMETER_STATUSES = "scenario_assumption"
    source_ids: list[NonEmptyString] = Field(default_factory=list)
    notes: NonEmptyString = (
        "Targeting and stratification metadata only; M5 has no validated severity pathway."
    )

    @field_validator("occupational_sectors", mode="before")
    @classmethod
    def normalize_sectors(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @property
    def config_hash(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.model_dump(mode="json")))


class TravelConfig(StrictModel):
    """Complete explicit-travel contract, independent of M2 resident data."""

    schema_version: Literal["1.0"] = "1.0"
    travel_config_id: NonEmptyString = "m8-explicit-travel-v1"
    mode: TravelMode = "disabled"
    daily_arrivals: dict[str, int] = Field(default_factory=dict)
    daily_departures: dict[str, int] = Field(default_factory=dict)
    departure_reconciliation_tolerance: int = Field(default=0, ge=0)
    annual_air_arrivals: int = Field(default=720_842, ge=0)
    annual_ferry_arrivals: int = Field(default=196_623, ge=0)
    stream_scale: float = Field(default=0.001, ge=0.0, le=1.0)
    arrival_volume_multiplier: float = Field(default=1.0, ge=0.0, le=10.0)
    visitor_fraction: float = Field(default=0.9, ge=0.0, le=1.0)
    returning_resident_fraction: float = Field(default=0.1, ge=0.0, le=1.0)
    day_visitor_fraction: float = Field(default=0.1, ge=0.0, le=1.0)
    staying_with_resident_fraction: float = Field(default=0.2, ge=0.0, le=1.0)
    stay_duration_days: int = Field(default=3, ge=1, le=60)
    stay_duration_jitter_days: int = Field(default=1, ge=0, le=14)
    party_sizes: tuple[int, ...] = (1, 2, 4, 6)
    party_probabilities: tuple[float, ...] = (0.45, 0.30, 0.20, 0.05)
    accommodation_group_capacity: int = Field(default=8, ge=2, le=40)
    visitor_accommodation_contacts: int = Field(default=3, ge=0, le=20)
    terminal_mixing_contacts: int = Field(default=4, ge=0, le=30)
    visitor_community_contacts: int = Field(default=3, ge=0, le=20)
    visitor_transit_contacts: int = Field(default=2, ge=0, le=20)
    visitor_party_contacts: int = Field(default=3, ge=0, le=11)
    taxi_capacity: int = Field(default=4, ge=1, le=8)
    private_vehicle_capacity: int = Field(default=7, ge=1, le=12)
    local_transport_probabilities: dict[LocalTransportType, float] = Field(
        default_factory=_default_transport_probabilities
    )
    visitor_community_indoor_probability: float = Field(default=0.65, ge=0.0, le=1.0)
    visitor_community_outdoor_probability: float = Field(default=0.45, ge=0.0, le=1.0)
    visitor_to_resident_multiplier: float = Field(default=1.0, ge=0.0, le=1.0)
    visitor_route_multipliers: dict[str, float] = Field(
        default_factory=lambda: {route: 1.0 for route in TRAVEL_ROUTE_IDS}
    )
    arrival_infectious_fraction: float = Field(default=0.0, ge=0.0, le=1.0)
    arrival_exposed_fraction: float = Field(default=0.0, ge=0.0, le=1.0)
    arrival_recovered_fraction: float = Field(default=0.0, ge=0.0, le=1.0)
    recovered_arrival_days_since_recovery: int = Field(default=0, ge=0, le=3650)
    returning_resident_external_acquisition_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    visitor_capacity: int | None = Field(default=None, ge=0)
    visitor_capacity_headroom: float = Field(default=0.10, ge=0.0, le=2.0)
    materialized_episode_limit: int = Field(default=200_000, ge=1)
    visitor_seasonality: SeasonalityProfile = Field(
        default_factory=lambda: SeasonalityProfile(profile_id="neutral-visitor-seasonality")
    )
    transmission_seasonality: SeasonalityProfile = Field(
        default_factory=lambda: SeasonalityProfile(profile_id="neutral-transmission-seasonality")
    )
    enable_transmission_seasonality: bool = False
    interventions: TravelInterventionConfig = Field(default_factory=TravelInterventionConfig)
    high_risk: HighRiskConfig = Field(default_factory=HighRiskConfig)
    parameter_provenance: dict[NonEmptyString, TravelParameter] = Field(default_factory=dict)
    assumptions: tuple[NonEmptyString, ...] = (
        "Annual air/sea values are Ports of Jersey passenger arrivals, not unique visitors.",
        "Daily stream values are derived or scenario-defined and do not represent manifests.",
        "All unobserved visitor composition and contact values are synthetic assumptions.",
    )

    @field_validator("daily_arrivals", "daily_departures")
    @classmethod
    def validate_daily_stream(cls, value: dict[str, int]) -> dict[str, int]:
        for key, count in value.items():
            try:
                date.fromisoformat(key.split(":", 1)[0])
            except ValueError as exc:
                raise ValueError(f"travel stream date is not ISO formatted: {key}") from exc
            if ":" in key and key.rsplit(":", 1)[1] not in {"AIRPORT", "FERRY"}:
                raise ValueError(f"travel stream mode is not AIRPORT or FERRY: {key}")
            if count < 0:
                raise ValueError("travel stream counts must be non-negative")
        return value

    @field_validator("party_sizes", "party_probabilities", mode="before")
    @classmethod
    def normalize_parties(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("assumptions", mode="before")
    @classmethod
    def normalize_assumptions(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("visitor_route_multipliers")
    @classmethod
    def validate_route_multipliers(cls, value: dict[str, float]) -> dict[str, float]:
        if set(value) != set(TRAVEL_ROUTE_IDS):
            raise ValueError("visitor_route_multipliers must cover exactly the M8 route IDs")
        if any(not isfinite(float(item)) or item < 0 or item > 1 for item in value.values()):
            raise ValueError("visitor route multipliers must be finite and in [0, 1]")
        return value

    @field_validator("local_transport_probabilities")
    @classmethod
    def validate_transport_probabilities(
        cls, value: dict[LocalTransportType, float]
    ) -> dict[LocalTransportType, float]:
        expected = {"BUS", "PRIVATE_RENTAL_CAR", "TAXI_RIDE", "HOST_PICKUP", "WALKING_OTHER"}
        if set(value) != expected:
            raise ValueError("local transport probabilities must cover every declared mode")
        if any(not isfinite(item) or item < 0 for item in value.values()):
            raise ValueError("local transport probabilities must be finite and non-negative")
        if abs(sum(value.values()) - 1.0) > 1e-9:
            raise ValueError("local transport probabilities must sum to 1")
        return value

    @model_validator(mode="after")
    def validate_distributions(self) -> TravelConfig:
        if len(self.party_sizes) != len(self.party_probabilities) or not self.party_sizes:
            raise ValueError("party_sizes and party_probabilities must have equal non-zero length")
        if any(size < 1 or size > 12 for size in self.party_sizes):
            raise ValueError("travel party sizes must be between 1 and 12")
        if any(probability < 0 for probability in self.party_probabilities):
            raise ValueError("travel party probabilities must be non-negative")
        if abs(sum(self.party_probabilities) - 1.0) > 1e-6:
            raise ValueError("travel party probabilities must sum to 1")
        if abs(self.visitor_fraction + self.returning_resident_fraction - 1.0) > 1e-9:
            raise ValueError(
                "visitor_fraction plus returning_resident_fraction must equal 1 because "
                "they partition person movements"
            )
        if (
            self.arrival_infectious_fraction
            + self.arrival_exposed_fraction
            + self.arrival_recovered_fraction
            > 1.0 + 1e-9
        ):
            raise ValueError("arrival disease-state fractions must sum to at most 1")
        return self

    @property
    def config_hash(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.model_dump(mode="json")))

    @property
    def seasonality_hash(self) -> str:
        return sha256_bytes(
            canonical_json_bytes(
                {
                    "visitor": self.visitor_seasonality.model_dump(mode="json"),
                    "transmission": self.transmission_seasonality.model_dump(mode="json"),
                    "enabled": self.enable_transmission_seasonality,
                }
            )
        )

    @property
    def intervention_hash(self) -> str:
        return self.interventions.config_hash

    def resolved_parameter_provenance(self) -> dict[str, dict[str, Any]]:
        """Return explicit provenance for every scalar control used by M8."""

        result = {
            key: value.model_dump(mode="json")
            for key, value in sorted(self.parameter_provenance.items())
        }
        payload = self.model_dump(mode="json", exclude={"parameter_provenance"})
        for key, value in sorted(payload.items()):
            if isinstance(value, (bool, int, float, str)) or value is None:
                result.setdefault(
                    key,
                    {
                        "value": value,
                        "distribution": "fixed",
                        "units": "scenario-control",
                        "status": "scenario_assumption",
                        "source_ids": [],
                        "derivation": None,
                        "sensitivity_required": True,
                        "notes": "Synthetic M8 control; not a Jersey estimate.",
                    },
                )
        for key in ("annual_air_arrivals", "annual_ferry_arrivals"):
            result[key] = {
                "value": payload[key],
                "distribution": "fixed",
                "units": "passenger movements/year",
                "status": "observed",
                "source_ids": ["passenger_arrivals_total_csv"],
                "derivation": "Frozen Ports of Jersey 2025 passenger-arrival total.",
                "sensitivity_required": True,
                "notes": "Passenger movements, not unique tourists.",
            }
        return result


class TravelEpisode(StrictModel):
    """One person-level temporary episode; never a permanent resident row."""

    trip_id: NonEmptyString
    person_id: NonEmptyString
    visitor_uid: NonEmptyString | None = None
    resident_agent_id: NonEmptyString | None = None
    traveller_type: TravellerType
    arrival_date: date
    departure_date: date
    entry_mode: EntryMode
    entry_terminal: NonEmptyString
    origin_category: NonEmptyString
    travel_party_id: NonEmptyString
    accommodation_type: AccommodationType
    accommodation_id: NonEmptyString | None = None
    host_household_id: NonEmptyString | None = None
    local_transport_type: LocalTransportType
    active_start: date
    active_end: date
    disease_state_on_arrival: ArrivalDiseaseState
    provenance_config_hash: NonEmptyString
    absence_start_date: date | None = None
    return_date: date | None = None
    home_household_id: NonEmptyString | None = None

    @property
    def identity_hash(self) -> str:
        """Immutable identity of this person-level trip episode."""

        return sha256_bytes(canonical_json_bytes(self.model_dump(mode="json")))

    @model_validator(mode="after")
    def validate_episode(self) -> TravelEpisode:
        if (
            self.traveller_type not in {"DAY_VISITOR", "RETURNING_RESIDENT"}
            and self.departure_date <= self.arrival_date
        ):
            raise ValueError("travel departure_date must be after arrival_date")
        if self.active_start != self.arrival_date or self.active_end != self.departure_date:
            raise ValueError("active episode dates must equal arrival and departure dates")
        if self.traveller_type == "RETURNING_RESIDENT":
            if self.resident_agent_id is None or self.visitor_uid is not None:
                raise ValueError("returning residents require resident_agent_id and no visitor_uid")
            if self.accommodation_type != "NONE":
                raise ValueError("returning residents do not receive visitor accommodation")
            if self.return_date != self.arrival_date or self.absence_start_date is None:
                raise ValueError(
                    "returning residents require an absence interval ending at return_date"
                )
            if self.absence_start_date >= self.return_date:
                raise ValueError("returning resident absence must precede return_date")
            if self.departure_date != self.arrival_date:
                raise ValueError(
                    "returning resident episodes use return_date as their active event date"
                )
        else:
            if self.visitor_uid is None or self.resident_agent_id is not None:
                raise ValueError("temporary visitors require visitor_uid and no resident_agent_id")
        if self.traveller_type == "STAYING_WITH_RESIDENTS":
            if self.accommodation_type != "HOST_HOUSEHOLD" or self.host_household_id is None:
                raise ValueError("host-household visitors require host household assignment")
        if self.traveller_type == "DAY_VISITOR" and self.departure_date != self.arrival_date:
            raise ValueError("day visitors must depart on their arrival date")
        return self
