"""Strict Milestone 7 intervention and scenario contracts.

The intervention layer is deliberately generic.  Values in the demonstration
configs are scenario assumptions, not estimates of Jersey policy effects,
adherence, vaccine performance, or venue-specific contacts.
"""

from __future__ import annotations

from datetime import date, timedelta
from math import isfinite
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from .contracts import NonEmptyString, StrictModel
from .hashing import canonical_json_bytes, sha256_bytes
from .outbreak_schemas import ROUTE_IDS

InterventionType = Literal[
    "case_isolation",
    "household_quarantine",
    "school_closure",
    "workplace_reduction",
    "community_reduction",
    "care_home_protection",
    "vaccination",
    "masking",
    "gathering_reduction",
]
ActivationRule = Literal["calendar", "detection_triggered"]
ReleaseRule = Literal["date", "duration", "simulation_end"]
CareTarget = Literal["nursing", "non_nursing", "both"]
CareRole = Literal["any", "care_resident", "care_staff"]
AgeBand = Literal["0-4", "5-17", "18-64", "65+"]

INTERVENTION_SENSITIVITY_AXES: tuple[str, ...] = (
    "timing",
    "duration",
    "adherence",
    "coverage",
    "rollout",
    "protection_delay",
    "susceptibility_efficacy",
    "infectiousness_efficacy",
    "waning",
    "target_population",
    "route_contact_multiplier",
)


def _tuple(value: object) -> object:
    return tuple(value) if isinstance(value, list) else value


class InterventionParameter(StrictModel):
    """One intervention value with its provenance metadata."""

    value: float | int | bool | str | None = None
    units: NonEmptyString
    status: Literal[
        "observed",
        "derived",
        "literature_prior",
        "calibrated",
        "scenario_assumption",
    ] = "scenario_assumption"
    source_ids: list[NonEmptyString] = Field(default_factory=list)
    valid_range: tuple[float, float] | None = None
    notes: NonEmptyString

    @field_validator("valid_range", mode="before")
    @classmethod
    def normalize_range(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_parameter(self) -> InterventionParameter:
        if self.valid_range is not None:
            low, high = self.valid_range
            if low > high:
                raise ValueError("intervention parameter valid_range is reversed")
            if isinstance(self.value, (float, int)) and not isinstance(self.value, bool):
                if not low <= float(self.value) <= high:
                    raise ValueError("intervention parameter value is outside valid_range")
        return self


class TargetPopulation(StrictModel):
    """Declarative structural targeting over the existing M2/M3 metadata."""

    agent_ids: tuple[NonEmptyString, ...] = ()
    age_min: int | None = Field(default=None, ge=0, le=95)
    age_max: int | None = Field(default=None, ge=0, le=95)
    age_bands: tuple[AgeBand, ...] = ()
    home_parishes: tuple[NonEmptyString, ...] = ()
    employment_sectors: tuple[NonEmptyString, ...] = ()
    school_types: tuple[NonEmptyString, ...] = ()
    school_ids: tuple[NonEmptyString, ...] = ()
    workplace_ids: tuple[NonEmptyString, ...] = ()
    care_setting_types: tuple[NonEmptyString, ...] = ()
    care_role: CareRole = "any"
    worker_only: bool = False
    include_institutional_staff: bool = False

    @field_validator(
        "agent_ids",
        "age_bands",
        "home_parishes",
        "employment_sectors",
        "school_types",
        "school_ids",
        "workplace_ids",
        "care_setting_types",
        mode="before",
    )
    @classmethod
    def normalize_sequences(cls, value: object) -> object:
        return _tuple(value)

    @model_validator(mode="after")
    def validate_target(self) -> TargetPopulation:
        if self.age_min is not None and self.age_max is not None and self.age_min > self.age_max:
            raise ValueError("target age_min must not exceed age_max")
        if len(set(self.agent_ids)) != len(self.agent_ids):
            raise ValueError("target agent_ids must be unique")
        return self


class InterventionConfig(StrictModel):
    """One composable intervention specification."""

    schema_version: Literal["1.0"] = "1.0"
    intervention_id: NonEmptyString
    version: NonEmptyString = "7.0.0"
    type: InterventionType
    enabled: bool = True
    activation_rule: ActivationRule = "calendar"
    start_date: date | None = None
    end_date: date | None = None
    target: TargetPopulation = Field(default_factory=TargetPopulation)
    route_effects: dict[str, float] = Field(default_factory=dict)
    adherence: float = Field(default=1.0, ge=0.0, le=1.0)
    start_delay_days: int = Field(default=0, ge=0, le=366)
    duration_days: int | None = Field(default=None, ge=1, le=3660)
    release_rule: ReleaseRule = "date"

    # Family-specific contact controls.  They are kept in one typed contract
    # so scenarios can compose without creating separate runner classes.
    class_multiplier: float = Field(default=1.0, ge=0.0, le=1.0)
    cross_class_multiplier: float = Field(default=1.0, ge=0.0, le=1.0)
    workplace_multiplier: float = Field(default=1.0, ge=0.0, le=1.0)
    commute_multiplier: float = Field(default=1.0, ge=0.0, le=1.0)
    additional_wfh_fraction: float = Field(default=0.0, ge=0.0, le=1.0)
    wfh_days_per_week: int | None = Field(default=None, ge=0, le=5)
    indoor_multiplier: float = Field(default=1.0, ge=0.0, le=1.0)
    outdoor_multiplier: float = Field(default=1.0, ge=0.0, le=1.0)
    care_target: CareTarget = "both"
    care_contact_multiplier: float = Field(default=1.0, ge=0.0, le=1.0)
    care_external_resident_multiplier: float = Field(default=1.0, ge=0.0, le=1.0)
    care_external_staff_multiplier: float = Field(default=1.0, ge=0.0, le=1.0)

    # Generic vaccination controls.  These apply to susceptibility and,
    # optionally, infectiousness only; there is no severity pathway in M5.
    rollout_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    coverage_target: float = Field(default=1.0, ge=0.0, le=1.0)
    uptake_probability: float = Field(default=1.0, ge=0.0, le=1.0)
    protection_delay_days: int = Field(default=0, ge=0, le=366)
    efficacy_susceptibility: float = Field(default=0.0, ge=0.0, le=1.0)
    efficacy_infectiousness: float = Field(default=0.0, ge=0.0, le=1.0)
    waning_days: int | None = Field(default=None, ge=1, le=3650)

    parameter_provenance: dict[NonEmptyString, InterventionParameter] = Field(default_factory=dict)
    assumptions: tuple[NonEmptyString, ...] = ()

    @field_validator("assumptions", mode="before")
    @classmethod
    def normalize_assumptions(cls, value: object) -> object:
        return _tuple(value)

    @field_validator("route_effects")
    @classmethod
    def validate_route_effects(cls, value: dict[str, float]) -> dict[str, float]:
        unknown = sorted(set(value) - set(ROUTE_IDS))
        if unknown:
            raise ValueError(f"route_effects contain unknown M4 routes: {unknown}")
        if any(not isfinite(float(multiplier)) for multiplier in value.values()):
            raise ValueError("route_effects must be finite")
        if any(float(multiplier) < 0 or float(multiplier) > 1 for multiplier in value.values()):
            raise ValueError("route_effects must be in [0, 1]")
        return {str(route): float(multiplier) for route, multiplier in value.items()}

    @model_validator(mode="after")
    def validate_lifecycle(self) -> InterventionConfig:
        detection_types = {"case_isolation", "household_quarantine"}
        if self.type in detection_types:
            if self.activation_rule == "calendar":
                self.activation_rule = "detection_triggered"
            if self.duration_days is None:
                raise ValueError(f"{self.type} requires duration_days")
            if self.start_date is not None or self.end_date is not None:
                raise ValueError("detection-triggered interventions do not use calendar dates")
        elif self.activation_rule == "detection_triggered":
            raise ValueError("only case isolation and household quarantine are detection-triggered")

        if self.start_date is None and self.type not in detection_types:
            raise ValueError(f"{self.type} requires start_date")
        if (
            self.end_date is not None
            and self.start_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("intervention end_date must not precede start_date")
        if self.release_rule == "duration" and self.duration_days is None:
            raise ValueError("release_rule=duration requires duration_days")
        if self.type == "vaccination" and self.start_date is None:
            raise ValueError("vaccination requires a rollout start_date")
        if self.wfh_days_per_week is not None and self.additional_wfh_fraction > 0:
            raise ValueError("set either wfh_days_per_week or additional_wfh_fraction")
        if self.waning_days is not None and self.protection_delay_days >= self.waning_days:
            raise ValueError("vaccine waning_days must exceed protection_delay_days")
        return self

    def active_date_window(self, when: date, simulation_end: date | None = None) -> bool:
        """Return whether a calendar intervention is active on an inclusive date."""

        if not self.enabled or self.activation_rule != "calendar" or self.start_date is None:
            return False
        if when < self.start_date:
            return False
        end = self.end_date
        if end is None and self.release_rule == "duration" and self.duration_days is not None:
            end = self.start_date + timedelta(days=self.duration_days - 1)
        if end is None and self.release_rule == "date":
            end = simulation_end
        return end is None or when <= end

    @property
    def config_hash(self) -> str:
        """Return the independent content hash for this intervention."""

        return intervention_config_hash(self)

    def resolved_parameter_provenance(self) -> dict[str, dict[str, Any]]:
        """Resolve scalar controls into auditable parameter metadata."""

        values = self.model_dump(mode="json", exclude={"parameter_provenance"})
        result: dict[str, dict[str, Any]] = {
            key: value.model_dump(mode="json")
            for key, value in sorted(self.parameter_provenance.items())
        }
        for key, value in sorted(values.items()):
            if key in {
                "schema_version",
                "intervention_id",
                "version",
                "type",
                "enabled",
                "target",
                "assumptions",
            }:
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                result.setdefault(
                    key,
                    {
                        "value": value,
                        "units": "scenario-control",
                        "status": "scenario_assumption",
                        "source_ids": [],
                        "notes": (
                            "Synthetic Milestone 7 scenario assumption; not a Jersey estimate."
                        ),
                    },
                )
        for route_id, multiplier in sorted(self.route_effects.items()):
            result.setdefault(
                f"route_effect:{route_id}",
                {
                    "value": multiplier,
                    "units": "relative route multiplier",
                    "status": "scenario_assumption",
                    "source_ids": [],
                    "notes": "Prospective effective-beta/contact assumption.",
                },
            )
        return result


# A descriptive alias is useful to callers that prefer "spec" terminology.
InterventionSpec = InterventionConfig


class ScenarioConfig(StrictModel):
    """A deterministic, composable M7 scenario definition."""

    schema_version: Literal["7.0"] = "7.0"
    scenario_id: NonEmptyString
    scenario_version: NonEmptyString = "7.0.0"
    interventions: tuple[InterventionConfig, ...] = ()
    seed: int | None = Field(default=None, ge=0)
    start_date: date | None = None
    duration_days: int | None = Field(default=None, ge=1, le=3660)
    disease_config_id: NonEmptyString | None = None
    observation_config_id: NonEmptyString | None = None
    sensitivity_config_ids: tuple[NonEmptyString, ...] = ()
    notes: NonEmptyString = (
        "Synthetic scenario experiment; not a Jersey policy recommendation or forecast."
    )

    @field_validator("interventions", "sensitivity_config_ids", mode="before")
    @classmethod
    def normalize_sequences(cls, value: object) -> object:
        return _tuple(value)

    @model_validator(mode="after")
    def validate_interventions(self) -> ScenarioConfig:
        ids = [item.intervention_id for item in self.interventions]
        if len(set(ids)) != len(ids):
            raise ValueError("scenario intervention_id values must be unique")
        if len(set(self.sensitivity_config_ids)) != len(self.sensitivity_config_ids):
            raise ValueError("sensitivity_config_ids must be unique")
        # Scenario tuple order is not a scientific control.  Canonicalizing it
        # also makes multiplier composition and scenario identity invariant to
        # YAML/list ordering.
        object.__setattr__(
            self,
            "interventions",
            tuple(
                sorted(self.interventions, key=lambda item: (item.intervention_id, item.version))
            ),
        )
        object.__setattr__(
            self, "sensitivity_config_ids", tuple(sorted(self.sensitivity_config_ids))
        )
        return self

    @property
    def enabled_interventions(self) -> tuple[InterventionConfig, ...]:
        return tuple(item for item in self.interventions if item.enabled)

    @property
    def config_hash(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.model_dump(mode="json")))

    def run_hash(
        self,
        *,
        disease_config_hash: str,
        network_hash: str,
        observation_config_hash: str | None,
        seed: int,
        start_date: date,
        duration_days: int,
        run_config_hash: str | None = None,
        m2_hash: str | None = None,
        m3_hash: str | None = None,
        starsim_version: str = "3.5.2",
        jos_model_versions: dict[str, str] | None = None,
    ) -> str:
        """Hash the canonical scientific parent/config contract for one run.

        ``run_config_hash`` is the hash of the complete ``OutbreakRunConfig``.
        The explicit legacy fields remain in the payload as independently
        inspectable controls and for compatibility with callers constructing
        scenario hashes outside the runner.
        """

        return sha256_bytes(
            canonical_json_bytes(
                {
                    "scenario_config_hash": self.config_hash,
                    "run_config_hash": run_config_hash,
                    "m2_hash": m2_hash,
                    "m3_hash": m3_hash,
                    "disease_config_hash": disease_config_hash,
                    "network_hash": network_hash,
                    "observation_config_hash": observation_config_hash,
                    "seed": seed,
                    "start_date": start_date.isoformat(),
                    "duration_days": duration_days,
                    "starsim_version": starsim_version,
                    "jos_model_versions": dict(sorted((jos_model_versions or {}).items())),
                }
            )
        )


def intervention_config_hash(config: InterventionConfig) -> str:
    """Return an independent content hash for one intervention."""

    return sha256_bytes(canonical_json_bytes(config.model_dump(mode="json")))


def scenario_hash(
    scenario: ScenarioConfig,
    *,
    disease_config_hash: str | None = None,
    network_hash: str | None = None,
    observation_config_hash: str | None = None,
    seed: int | None = None,
    start_date: date | None = None,
    duration_days: int | None = None,
    run_config_hash: str | None = None,
    m2_hash: str | None = None,
    m3_hash: str | None = None,
    starsim_version: str = "3.5.2",
    jos_model_versions: dict[str, str] | None = None,
) -> str:
    """Hash a scenario alone or with its complete run-parent contract."""

    if (
        disease_config_hash is None
        or network_hash is None
        or seed is None
        or start_date is None
        or duration_days is None
    ):
        return scenario.config_hash
    return scenario.run_hash(
        disease_config_hash=disease_config_hash,
        network_hash=network_hash,
        observation_config_hash=observation_config_hash,
        seed=seed,
        start_date=start_date,
        duration_days=duration_days,
        run_config_hash=run_config_hash,
        m2_hash=m2_hash,
        m3_hash=m3_hash,
        starsim_version=starsim_version,
        jos_model_versions=jos_model_versions,
    )
