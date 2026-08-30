"""Milestone 8 explicit travel and visitor layer.

This module owns synthetic travel episodes, temporary route generation and
travel-aware run summaries.  It does not change the canonical M2 resident
tables or the M4 resident route artifact.
"""

from __future__ import annotations

import copy
import hashlib
import platform
import resource
import subprocess
import time
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import yaml  # type: ignore[import-untyped]

from .hashing import canonical_json_bytes, sha256_bytes
from .intervention_schemas import ScenarioConfig
from .interventions import InterventionManager
from .network_generator import (
    GeneratedNetworks,
    _complete_group,
    _deduplicate_edges,
    _ring_edges,
)
from .observation_scheduler import DetectionEvent, ObservationScheduler
from .observation_schemas import ObservationConfig
from .outbreak_schemas import OutbreakRunConfig, RespiratoryParameterSet
from .respiratory import RespiratorySEIRS
from .starsim_adapter import build_starsim_travel_sim
from .travel_schemas import (
    TRAVEL_ROUTE_IDS,
    AccommodationType,
    ArrivalDiseaseState,
    EntryMode,
    HighRiskConfig,
    LocalTransportType,
    RiskStratum,
    TravelConfig,
    TravelEpisode,
    TravellerType,
)

TRAVEL_GENERATOR_VERSION = "8.0.0"


def load_travel_config(root: Path, path: Path | None = None) -> TravelConfig:
    """Load and strictly validate a versioned M8 travel YAML file."""

    config_path = path or root / "configs" / "travel" / "m8_explicit_travel.yaml"
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("travel YAML must contain a mapping")
        return TravelConfig.model_validate(payload)
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        raise ValueError(f"invalid travel configuration {config_path}: {exc}") from exc


def _stable_int(seed: int, *parts: object) -> int:
    return int.from_bytes(
        hashlib.sha256("|".join(str(item) for item in (seed, *parts)).encode()).digest()[:8],
        "big",
    )


def _stable_uniform(seed: int, *parts: object) -> float:
    return _stable_int(seed, *parts) / 2**64


def _iso(when: date) -> str:
    return when.isoformat()


def _without_null_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _without_null_fields(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [_without_null_fields(item) for item in value]
    return value


def _dates(start_date: date, duration_days: int) -> tuple[date, ...]:
    return tuple(start_date + timedelta(days=index) for index in range(duration_days))


def _parish_for_household(households: list[dict[str, Any]]) -> dict[str, str]:
    return {str(row["household_id"]): str(row["home_parish"]) for row in households}


def _mode_key(when: date, mode: EntryMode) -> str:
    return f"{when.isoformat()}:{mode}"


@dataclass(frozen=True)
class TravelPlan:
    """Deterministic episode and stream outputs before disease execution."""

    episodes: tuple[TravelEpisode, ...]
    visitor_records: tuple[dict[str, Any], ...]
    daily_stream: tuple[dict[str, Any], ...]
    visitor_capacity: int
    visitor_slot_indices: tuple[tuple[str, int], ...]
    episode_hash: str
    visitor_hash: str
    reconciliation: dict[str, Any] = field(default_factory=dict)
    departure_reconciliation: dict[str, int] = field(default_factory=dict)

    @property
    def visitor_episodes(self) -> tuple[TravelEpisode, ...]:
        return tuple(item for item in self.episodes if item.visitor_uid is not None)

    @property
    def returning_resident_episodes(self) -> tuple[TravelEpisode, ...]:
        return tuple(item for item in self.episodes if item.resident_agent_id is not None)


@dataclass(frozen=True, order=True)
class ScheduledArrivalTest:
    """Episode-bound arrival-test result that cannot follow a reused slot."""

    result_time_index: int
    person_id: str
    detected: bool
    actor_type: str
    runtime_slot_uid: int
    trip_id: str
    travel_party_id: str
    episode_identity_hash: str
    administration_time_index: int


def _profile_counts(
    config: TravelConfig,
    when: date,
    mode: EntryMode,
    previous_expected: float,
) -> tuple[int, float]:
    direct = config.daily_arrivals.get(_mode_key(when, mode))
    if direct is None:
        direct = config.daily_arrivals.get(when.isoformat())
        if direct is not None:
            total = config.annual_air_arrivals + config.annual_ferry_arrivals
            share = (
                config.annual_air_arrivals / total
                if mode == "AIRPORT" and total
                else config.annual_ferry_arrivals / total
                if total
                else 0.0
            )
            direct = int(round(direct * share))
    if direct is None:
        if config.daily_arrivals:
            # A supplied schedule is authoritative for the requested horizon;
            # unspecified dates are explicit zeroes rather than silently
            # falling back to the annual stream.
            direct_float = 0.0
        else:
            annual = (
                config.annual_air_arrivals if mode == "AIRPORT" else config.annual_ferry_arrivals
            )
            direct_float = (
                annual
                * config.stream_scale
                * config.arrival_volume_multiplier
                * config.interventions.arrival_volume_multiplier
                / 365.0
                * config.visitor_seasonality.multiplier(when)
            )
    else:
        direct_float = (
            float(direct)
            * config.arrival_volume_multiplier
            * config.interventions.arrival_volume_multiplier
            * config.visitor_seasonality.multiplier(when)
        )
    cumulative = previous_expected + max(0.0, direct_float)
    count = int(cumulative)
    return count, cumulative - count


def _scaled_annual_target(config: TravelConfig, mode: EntryMode) -> int:
    """Return the declared integer simulated-movement target for one source stream."""

    source = config.annual_air_arrivals if mode == "AIRPORT" else config.annual_ferry_arrivals
    value = (
        source
        * config.stream_scale
        * config.arrival_volume_multiplier
        * config.interventions.arrival_volume_multiplier
    )
    # Half-up is explicit and stable; at stream_scale=1 with neutral volume
    # controls this is exactly the frozen source passenger-movement total.
    return int(np.floor(value + 0.5))


def _annual_apportionment(config: TravelConfig, year: int, mode: EntryMode) -> dict[date, int]:
    """Largest-remainder daily apportionment preserving the annual integer target."""

    start = date(year, 1, 1)
    n_days = (date(year + 1, 1, 1) - start).days
    days = [start + timedelta(days=index) for index in range(n_days)]
    target = _scaled_annual_target(config, mode)
    weights = [config.visitor_seasonality.multiplier(day) for day in days]
    total_weight = sum(weights)
    exact = [target * weight / total_weight for weight in weights]
    floors = [int(np.floor(value)) for value in exact]
    remainder = target - sum(floors)
    ranking = sorted(
        range(n_days),
        key=lambda index: (-(exact[index] - floors[index]), days[index].isoformat()),
    )
    for index in ranking[:remainder]:
        floors[index] += 1
    return dict(zip(days, floors, strict=True))


def _explicit_stream_count(
    schedule: dict[str, int], config: TravelConfig, when: date, mode: EntryMode
) -> int | None:
    """Resolve an optional date/mode keyed stream without annual fallback."""

    if not schedule:
        return None
    direct = schedule.get(_mode_key(when, mode))
    if direct is not None:
        return int(direct)
    total = schedule.get(when.isoformat())
    if total is None:
        return 0
    annual_total = config.annual_air_arrivals + config.annual_ferry_arrivals
    if not annual_total:
        return 0
    share = (
        config.annual_air_arrivals / annual_total
        if mode == "AIRPORT"
        else config.annual_ferry_arrivals / annual_total
    )
    return int(round(total * share))


def _choose_party_size(
    config: TravelConfig, seed: int, date_key: str, index: int, remaining: int
) -> int:
    draw = _stable_uniform(seed, "party-size", date_key, index)
    cumulative = 0.0
    chosen = config.party_sizes[-1]
    for size, probability in zip(config.party_sizes, config.party_probabilities, strict=True):
        cumulative += probability
        if draw < cumulative:
            chosen = size
            break
    return min(int(chosen), remaining)


def _arrival_state(config: TravelConfig, seed: int, visitor_uid: str) -> ArrivalDiseaseState:
    draw = _stable_uniform(seed, "arrival-state", visitor_uid)
    if draw < config.arrival_infectious_fraction:
        return "infectious"
    if draw < config.arrival_infectious_fraction + config.arrival_exposed_fraction:
        return "exposed"
    if draw < (
        config.arrival_infectious_fraction
        + config.arrival_exposed_fraction
        + config.arrival_recovered_fraction
    ):
        return "recovered"
    return "susceptible"


def _visitor_accommodation(
    config: TravelConfig,
    seed: int,
    visitor_uid: str,
    host_households: list[str],
    parish_by_household: dict[str, str],
) -> tuple[str, AccommodationType, str | None, str | None]:
    if _stable_uniform(seed, "day-visitor", visitor_uid) < config.day_visitor_fraction:
        parish = parish_by_household[host_households[0]] if host_households else "St Helier"
        return parish, "NONE", None, None
    if (
        host_households
        and _stable_uniform(seed, "host-choice", visitor_uid)
        < config.staying_with_resident_fraction
    ):
        household_id = host_households[
            _stable_int(seed, "host-household", visitor_uid) % len(host_households)
        ]
        return (
            parish_by_household[household_id],
            "HOST_HOUSEHOLD",
            f"host-{household_id}",
            household_id,
        )
    parish = (
        parish_by_household[
            host_households[_stable_int(seed, "hotel-parish", visitor_uid) % len(host_households)]
        ]
        if host_households
        else "St Helier"
    )
    guest_number = _stable_int(seed, "guest", visitor_uid) % 32
    accommodation_id = f"synthetic-guest-{parish.lower().replace(' ', '-')}-{guest_number:02d}"
    return parish, "HOTEL_GUEST", accommodation_id, None


def _transport(config: TravelConfig, seed: int, visitor_uid: str, host: bool) -> LocalTransportType:
    draw = _stable_uniform(seed, "transport", visitor_uid)
    cumulative = 0.0
    for mode in ("BUS", "PRIVATE_RENTAL_CAR", "TAXI_RIDE", "HOST_PICKUP", "WALKING_OTHER"):
        cumulative += config.local_transport_probabilities[mode]
        if draw < cumulative:
            return "WALKING_OTHER" if mode == "HOST_PICKUP" and not host else mode
    return "WALKING_OTHER"


def generate_travel_episodes(
    config: TravelConfig,
    *,
    seed: int,
    start_date: date,
    duration_days: int,
    residents: list[dict[str, Any]],
    households: list[dict[str, Any]],
) -> TravelPlan:
    """Generate deterministic person-level episodes from bounded streams."""

    if duration_days < 1:
        raise ValueError("travel duration_days must be positive")
    if config.mode not in {"explicit_travel", "both"}:
        return TravelPlan(
            (),
            (),
            tuple(
                {
                    "date": _iso(when),
                    "resident_present": len(residents),
                    "resident_away": 0,
                    "active_visitors": 0,
                    "arrivals": 0,
                    "departures": 0,
                    "present_population": len(residents),
                }
                for when in _dates(start_date, duration_days)
            ),
            0,
            (),
            sha256_bytes(canonical_json_bytes([])),
            sha256_bytes(canonical_json_bytes([])),
        )

    parish_by_household = _parish_for_household(households)
    host_households = sorted(parish_by_household)
    resident_ids = sorted(str(row["agent_id"]) for row in residents)
    entry_modes: tuple[EntryMode, ...] = ("AIRPORT", "FERRY")
    household_by_resident = {
        str(row["agent_id"]): str(row["household_id"])
        for row in residents
        if row.get("household_id") is not None
    }
    busy_until: dict[str, date] = {}
    episodes: list[TravelEpisode] = []
    visitor_records: list[dict[str, Any]] = []
    daily_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"AIRPORT": 0, "FERRY": 0})
    years = sorted({when.year for when in _dates(start_date, duration_days)})
    annual_counts = {
        (year, mode): _annual_apportionment(config, year, mode)
        for year in years
        for mode in entry_modes
    }
    if not config.daily_arrivals:
        horizon_movements = sum(
            annual_counts[(when.year, mode)][when]
            for when in _dates(start_date, duration_days)
            for mode in entry_modes
        )
        if horizon_movements > config.materialized_episode_limit:
            raise ValueError(
                "travel episode materialization limit exceeded; use "
                "benchmark_travel_generation for literal annual source-scale "
                "reconciliation/capacity and a declared scaled epidemic run"
            )
    visitor_counter = 0
    returning_expected = 0.0
    returning_assigned = 0
    for when in _dates(start_date, duration_days):
        for mode in entry_modes:
            explicit_count = _explicit_stream_count(config.daily_arrivals, config, when, mode)
            count = (
                annual_counts[(when.year, mode)][when]
                if explicit_count is None
                else int(
                    np.floor(
                        explicit_count
                        * config.arrival_volume_multiplier
                        * config.interventions.arrival_volume_multiplier
                        * config.visitor_seasonality.multiplier(when)
                        + 0.5
                    )
                )
            )
            daily_counts[_iso(when)][mode] = count
            # Traveller category is apportioned at PERSON-MOVEMENT level.
            # Homogeneous parties are constructed only after exact integer
            # category targets have been resolved, so grouping cannot change
            # the configured visitor/returning-resident split.
            returning_expected += count * config.returning_resident_fraction
            returning_count = int(np.floor(returning_expected + 0.5)) - returning_assigned
            returning_assigned += returning_count
            category_counts = (
                ("RETURNING_RESIDENT", returning_count),
                ("VISITOR", count - returning_count),
            )
            party_number = 0
            for category, category_count in category_counts:
                remaining = category_count
                while remaining:
                    party_size = _choose_party_size(
                        config,
                        seed,
                        f"{when.isoformat()}:{mode}:{category}",
                        party_number,
                        remaining,
                    )
                    party_number += 1
                    remaining -= party_size
                    trip_id = f"trip-{seed:010d}-{when:%Y%m%d}-{mode.lower()}-{party_number:04d}"
                    party_id = f"party-{trip_id}"
                    for person_number in range(party_size):
                        returning = category == "RETURNING_RESIDENT"
                        resident_id: str | None = None
                        if returning:
                            returning_candidates = [
                                agent_id
                                for agent_id in resident_ids
                                if busy_until.get(agent_id, start_date) <= when
                            ]
                            if not returning_candidates:
                                raise ValueError(
                                    "returning-resident person target exceeds available resident "
                                    "identity capacity"
                                )
                            resident_id = returning_candidates[
                                _stable_int(
                                    seed,
                                    "returning-resident",
                                    trip_id,
                                    person_number,
                                )
                                % len(returning_candidates)
                            ]
                            busy_until[resident_id] = when + timedelta(
                                days=max(2, config.stay_duration_days)
                            )
                        person_id = (
                            resident_id
                            if returning
                            else f"visitor-{seed:010d}-{visitor_counter:08d}"
                        )
                        assert person_id is not None
                        terminal = (
                            "JERSEY_AIRPORT" if mode == "AIRPORT" else "JERSEY_FERRY_TERMINAL"
                        )
                        if returning:
                            duration = max(2, config.stay_duration_days)
                            absence_start = when - timedelta(days=duration)
                            departure = when
                            episode = TravelEpisode(
                                trip_id=trip_id,
                                person_id=person_id,
                                visitor_uid=None,
                                resident_agent_id=resident_id,
                                traveller_type="RETURNING_RESIDENT",
                                arrival_date=when,
                                departure_date=departure,
                                entry_mode=mode,
                                entry_terminal=terminal,
                                origin_category="resident_outbound_return",
                                travel_party_id=party_id,
                                accommodation_type="NONE",
                                accommodation_id=None,
                                host_household_id=None,
                                local_transport_type="WALKING_OTHER",
                                active_start=when,
                                active_end=departure,
                                disease_state_on_arrival="susceptible",
                                provenance_config_hash=config.config_hash,
                                absence_start_date=absence_start,
                                return_date=when,
                                home_household_id=household_by_resident.get(str(resident_id)),
                            )
                            episodes.append(episode)
                        else:
                            visitor_uid = person_id
                            parish, accommodation_type, accommodation_id, host_household_id = (
                                _visitor_accommodation(
                                    config,
                                    seed,
                                    visitor_uid,
                                    host_households,
                                    parish_by_household,
                                )
                            )
                            if accommodation_type == "NONE":
                                departure = when
                                traveller_type: TravellerType = "DAY_VISITOR"
                            else:
                                jitter = (
                                    _stable_int(seed, "stay-jitter", visitor_uid)
                                    % (2 * config.stay_duration_jitter_days + 1)
                                    - config.stay_duration_jitter_days
                                )
                                departure = when + timedelta(
                                    days=max(1, config.stay_duration_days + int(jitter))
                                )
                                traveller_type = (
                                    "STAYING_WITH_RESIDENTS"
                                    if accommodation_type == "HOST_HOUSEHOLD"
                                    else "OVERNIGHT_ACCOMMODATION_VISITOR"
                                )
                            state = _arrival_state(config, seed, visitor_uid)
                            episode = TravelEpisode(
                                trip_id=trip_id,
                                person_id=person_id,
                                visitor_uid=visitor_uid,
                                resident_agent_id=None,
                                traveller_type=traveller_type,
                                arrival_date=when,
                                departure_date=departure,
                                entry_mode=mode,
                                entry_terminal=terminal,
                                origin_category="synthetic_temporary_visitor",
                                travel_party_id=party_id,
                                accommodation_type=accommodation_type,
                                accommodation_id=accommodation_id,
                                host_household_id=host_household_id,
                                local_transport_type=_transport(
                                    config, seed, visitor_uid, host_household_id is not None
                                ),
                                active_start=when,
                                active_end=departure,
                                disease_state_on_arrival=state,
                                provenance_config_hash=config.config_hash,
                            )
                            episodes.append(episode)
                            visitor_records.append(
                                {
                                    "visitor_uid": visitor_uid,
                                    "trip_id": trip_id,
                                    "travel_party_id": party_id,
                                    "age": 1 + (_stable_int(seed, "visitor-age", visitor_uid) % 90),
                                    "sex": "female"
                                    if _stable_int(seed, "visitor-sex", visitor_uid) % 2
                                    else "male",
                                    "home_parish": parish,
                                    "disease_state_on_arrival": state,
                                    "accommodation_type": accommodation_type,
                                    "accommodation_id": accommodation_id,
                                    "host_household_id": host_household_id,
                                    "local_transport_type": episode.local_transport_type,
                                    "entry_mode": mode,
                                    "entry_terminal": terminal,
                                    "arrival_date": when.isoformat(),
                                    "departure_date": departure.isoformat(),
                                    "traveller_type": traveller_type,
                                    "episode_identity_hash": episode.identity_hash,
                                }
                            )
                            visitor_counter += 1

    # When an explicit departure schedule is supplied, move a deterministic
    # subset of still-active episodes to those dates.  The schedule cannot
    # manufacture a departure without a prior arrival; any unmatchable excess
    # remains visible through the generated episode stream rather than being
    # silently dropped.
    requested_departures = 0
    matched_departures = 0
    horizon_end = start_date + timedelta(days=duration_days)
    requested_departures_outside_horizon = sum(
        count
        for key, count in config.daily_departures.items()
        if not start_date <= date.fromisoformat(key.split(":", 1)[0]) < horizon_end
    )
    if config.daily_departures:
        for when in _dates(start_date, duration_days):
            for mode in entry_modes:
                target = _explicit_stream_count(config.daily_departures, config, when, mode)
                if target is None or target <= 0:
                    continue
                requested_departures += target
                departure_candidates = [
                    episode
                    for episode in episodes
                    if episode.entry_mode == mode
                    and episode.arrival_date < when < episode.departure_date
                ]
                departure_candidates.sort(
                    key=lambda episode: (
                        _stable_int(
                            seed, "scheduled-departure", when.isoformat(), episode.person_id
                        ),
                        episode.person_id,
                    )
                )
                selected = {episode.person_id for episode in departure_candidates[:target]}
                matched_departures += len(selected)
                episodes = [
                    episode.model_copy(update={"departure_date": when, "active_end": when})
                    if episode.person_id in selected
                    else episode
                    for episode in episodes
                ]

    if requested_departures - matched_departures > config.departure_reconciliation_tolerance:
        raise ValueError(
            "explicit departure schedule reconciliation failed: "
            f"requested={requested_departures}, matched={matched_departures}, "
            f"tolerance={config.departure_reconciliation_tolerance}"
        )

    episode_payload = [
        row.model_dump(mode="json") | {"episode_identity_hash": row.identity_hash}
        for row in sorted(episodes, key=lambda row: (row.arrival_date, row.person_id))
    ]
    visitor_payload = sorted(visitor_records, key=lambda row: row["visitor_uid"])
    daily_stream: list[dict[str, Any]] = []
    for when in _dates(start_date, duration_days):
        date_key = _iso(when)
        active_visitors = sum(
            item.visitor_uid is not None
            and item.arrival_date <= when < item.departure_date
            or item.visitor_uid is not None
            and item.traveller_type == "DAY_VISITOR"
            and item.arrival_date == when
            for item in episodes
        )
        away = len(
            {
                item.resident_agent_id
                for item in episodes
                if item.resident_agent_id is not None
                and item.absence_start_date is not None
                and item.return_date is not None
                and item.absence_start_date <= when < item.return_date
            }
        )
        arrivals = sum(item.arrival_date == when for item in episodes)
        departures = sum(
            item.visitor_uid is not None and item.departure_date == when for item in episodes
        )
        daily_stream.append(
            {
                "date": date_key,
                "resident_present": len(residents) - away,
                "resident_away": away,
                "active_visitors": active_visitors,
                "arrivals": arrivals,
                "departures": departures,
                "present_population": len(residents) - away + active_visitors,
                "airport_arrivals": daily_counts[date_key]["AIRPORT"],
                "ferry_arrivals": daily_counts[date_key]["FERRY"],
            }
        )
    # Reuse temporary slots across non-overlapping episodes.  Capacity is
    # therefore driven by peak concurrency, not annual visitor volume.
    slot_release: list[date] = []
    slot_by_visitor: dict[str, int] = {}
    for episode in sorted(
        (item for item in episodes if item.visitor_uid is not None),
        key=lambda item: (item.arrival_date, item.person_id),
    ):
        assert episode.visitor_uid is not None
        reusable = next(
            (
                index
                for index, release in enumerate(slot_release)
                if release <= episode.arrival_date
            ),
            None,
        )
        release = (
            episode.departure_date
            if episode.traveller_type != "DAY_VISITOR"
            else episode.arrival_date + timedelta(days=1)
        )
        if reusable is None:
            reusable = len(slot_release)
            slot_release.append(release)
        else:
            slot_release[reusable] = release
        slot_by_visitor[episode.visitor_uid] = reusable
    peak = max((row["active_visitors"] for row in daily_stream), default=0)
    capacity = config.visitor_capacity
    if capacity is None:
        capacity = int(np.ceil(peak * (1.0 + config.visitor_capacity_headroom)))
    if peak > capacity:
        raise ValueError(
            "visitor slot capacity overflow: "
            f"peak active visitors {peak} exceeds configured capacity {capacity}"
        )
    simulated_by_mode = {
        "AIRPORT": sum(values["AIRPORT"] for values in daily_counts.values()),
        "FERRY": sum(values["FERRY"] for values in daily_counts.values()),
    }
    full_years = [
        year
        for year in years
        if start_date <= date(year, 1, 1)
        and start_date + timedelta(days=duration_days) >= date(year + 1, 1, 1)
    ]
    source_targets = {
        "AIRPORT": sum(_scaled_annual_target(config, "AIRPORT") for _year in full_years),
        "FERRY": sum(_scaled_annual_target(config, "FERRY") for _year in full_years),
    }
    realized_returning = len([row for row in episodes if row.resident_agent_id is not None])
    realized_total = len(episodes)
    return TravelPlan(
        episodes=tuple(sorted(episodes, key=lambda row: (row.arrival_date, row.person_id))),
        visitor_records=tuple(visitor_payload),
        daily_stream=tuple(daily_stream),
        visitor_capacity=capacity,
        visitor_slot_indices=tuple(sorted(slot_by_visitor.items())),
        episode_hash=sha256_bytes(canonical_json_bytes(episode_payload)),
        visitor_hash=sha256_bytes(canonical_json_bytes(visitor_payload)),
        reconciliation={
            "source_target_movements": {
                "AIRPORT": config.annual_air_arrivals,
                "FERRY": config.annual_ferry_arrivals,
                "TOTAL": config.annual_air_arrivals + config.annual_ferry_arrivals,
            },
            "simulated_movements": simulated_by_mode | {"TOTAL": sum(simulated_by_mode.values())},
            "full_year_scaled_targets": source_targets | {"TOTAL": sum(source_targets.values())},
            "stream_scale": config.stream_scale,
            "reconciliation_error": {
                mode: simulated_by_mode[mode] - source_targets[mode]
                for mode in entry_modes
                if full_years
            },
            "reconciliation_tolerance": 0,
            "rounding_contract": (
                "annual half-up integer target; largest-remainder daily apportionment"
            ),
            "returning_resident_person_fraction": (
                realized_returning / realized_total if realized_total else 0.0
            ),
            "returning_resident_fraction_tolerance": (
                0.5 / realized_total if realized_total else 0.0
            ),
        },
        departure_reconciliation={
            "requested_departures": requested_departures,
            "matched_departures": matched_departures,
            "unmatched_departures": requested_departures - matched_departures,
            "requested_departures_outside_horizon": requested_departures_outside_horizon,
            "departures_outside_horizon": sum(
                episode.visitor_uid is not None
                and episode.departure_date >= start_date + timedelta(days=duration_days)
                for episode in episodes
            ),
            "still_active_trips": sum(
                episode.visitor_uid is not None
                and episode.departure_date >= start_date + timedelta(days=duration_days)
                for episode in episodes
            ),
        },
    )


def benchmark_travel_generation(config: TravelConfig, *, year: int = 2025) -> dict[str, Any]:
    """Constant-memory annual movement/capacity benchmark without epidemic execution.

    This is the literal source-scale gate. It apportions the authoritative
    passenger-movement targets to dates, but deliberately does not claim that
    a scaled simulated person is a source-equivalent unique tourist.
    """

    started = time.perf_counter()
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    modes: tuple[EntryMode, ...] = ("AIRPORT", "FERRY")
    by_mode = {mode: _annual_apportionment(config, year, mode) for mode in modes}
    start = date(year, 1, 1)
    end = date(year + 1, 1, 1)
    daily = [
        by_mode["AIRPORT"][when] + by_mode["FERRY"][when]
        for when in _dates(start, (end - start).days)
    ]
    returning_expected = 0.0
    returning = 0
    visitor_daily: list[int] = []
    for count in daily:
        returning_expected += count * config.returning_resident_fraction
        assigned = int(np.floor(returning_expected + 0.5)) - returning
        returning += assigned
        visitor_daily.append(count - assigned)
    day_visitors = [
        int(np.floor(value * config.day_visitor_fraction + 0.5)) for value in visitor_daily
    ]
    overnight = [value - day for value, day in zip(visitor_daily, day_visitors, strict=True)]
    active: list[int] = []
    for index in range(len(daily)):
        value = day_visitors[index]
        for offset in range(max(1, config.stay_duration_days)):
            source_index = index - offset
            if source_index >= 0:
                value += overnight[source_index]
        active.append(value)
    peak = max(active, default=0)
    capacity = config.visitor_capacity
    if capacity is None:
        capacity = int(np.ceil(peak * (1.0 + config.visitor_capacity_headroom)))
    after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    simulated = sum(daily)
    source_total = config.annual_air_arrivals + config.annual_ferry_arrivals
    return {
        "year": year,
        "source_target_movements": {
            "AIRPORT": config.annual_air_arrivals,
            "FERRY": config.annual_ferry_arrivals,
            "TOTAL": source_total,
        },
        "simulated_movements": {
            "AIRPORT": sum(by_mode["AIRPORT"].values()),
            "FERRY": sum(by_mode["FERRY"].values()),
            "TOTAL": simulated,
        },
        "stream_scale": config.stream_scale,
        "reconciliation_error": simulated
        - _scaled_annual_target(config, "AIRPORT")
        - _scaled_annual_target(config, "FERRY"),
        "reconciliation_tolerance": 0,
        "average_daily_movements": simulated / len(daily),
        "peak_daily_movements": max(daily, default=0),
        "visitor_movements": sum(visitor_daily),
        "returning_resident_movements": returning,
        "realized_returning_fraction": returning / simulated if simulated else 0.0,
        "returning_fraction_tolerance": 0.5 / simulated if simulated else 0.0,
        "stay_distribution": {
            "day_visitors": sum(day_visitors),
            f"overnight_{config.stay_duration_days}_days": sum(overnight),
            "jitter_not_materialized_in_capacity_gate": config.stay_duration_jitter_days,
        },
        "peak_concurrent_visitors": peak,
        "required_slots": capacity,
        "seven_day_window": {
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=6)).isoformat(),
            "movements": sum(daily[:7]),
            "average_daily_movements": sum(daily[:7]) / 7,
            "peak_daily_movements": max(daily[:7], default=0),
            "peak_concurrent_visitors": max(active[:7], default=0),
            "required_slots": int(
                np.ceil(max(active[:7], default=0) * (1.0 + config.visitor_capacity_headroom))
            ),
        },
        "generation_runtime_seconds": time.perf_counter() - started,
        "generation_peak_memory_bytes": max(before, after),
        "generation_memory_delta_bytes": max(0, after - before),
        "execution_scope": "generation_and_capacity_only; no disease execution",
        "scaled_mode_contract": (
            "simulated movements are a computational sample; epidemic outcomes are not "
            "inflated to source scale"
            if config.stream_scale < 1
            else "literal source passenger-movement generation target"
        ),
    }


def _travel_spec(
    route_id: str,
    indoor: bool,
    weight: float,
    semantics: str,
    *,
    weight_components: dict[str, float] | None = None,
) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "route_id": route_id,
        "route_family": "transport"
        if route_id in {"arrival_terminal", "visitor_transit"}
        else "indoor_community"
        if indoor
        else "outdoor_community",
        "route_kind": route_id,
        "membership_source": semantics,
        "persistence": "daily_sampled",
        "active_calendar": "weekday_or_weekend",
        "indoor": indoor,
        "relative_weight": weight,
        "weight_meaning": (
            "relative temporary travel contact opportunity; not an observed "
            "contact count or measured beta"
        ),
        "assumptions": [
            "Synthetic temporary route; no named venue, passenger manifest or "
            "itinerary is represented."
        ],
    }
    if weight_components is not None:
        spec["relative_weight_components"] = weight_components
    return spec


def _configured_route_weights(config: TravelConfig) -> dict[str, float]:
    return {
        "arrival_terminal": config.arrival_terminal_edge_weight,
        "visitor_party": config.visitor_party_edge_weight,
        "visitor_accommodation": config.visitor_accommodation_edge_weight,
        "visitor_host_household": config.visitor_host_household_edge_weight,
        "visitor_transit": config.visitor_transit_bus_edge_weight,
        "visitor_community_indoor": config.visitor_community_indoor_edge_weight,
        "visitor_community_outdoor": config.visitor_community_outdoor_edge_weight,
    }


class TravelManager:
    """Lifecycle, sparse temporary routes and travel interventions."""

    def __init__(
        self,
        base_generated: GeneratedNetworks,
        plan: TravelPlan,
        config: TravelConfig,
        *,
        seed: int,
        start_date: date,
        duration_days: int,
    ) -> None:
        self.base_generated = base_generated
        self.plan = plan
        self.config = config
        self.seed = seed
        self.start_date = start_date
        self.duration_days = duration_days
        self.sim: Any | None = None
        self.disease: RespiratorySEIRS | None = None
        self.uid_by_id: dict[str, int] = {}
        self.id_by_uid: dict[int, str] = {}
        self.visitor_slot_by_id: dict[str, int] = {}
        self._planned_slot_by_visitor = {
            visitor_id: slot_index for visitor_id, slot_index in plan.visitor_slot_indices
        }
        self.active_visitor_ids: set[str] = set()
        self.present_resident_ids: set[str] = set(base_generated.agent_ids)
        self.away_resident_ids: set[str] = set()
        self.quarantine_until: dict[str, int] = {}
        self._quarantine_episode_by_person: dict[str, tuple[str, str]] = {}
        self.pending_tests: list[ScheduledArrivalTest] = []
        self.pending_quarantines: list[tuple[int, str, str, str]] = []
        self.current_date: date = start_date
        self.current_ti = 0
        self._all_resident_uids = set(range(len(base_generated.agent_ids)))
        self.event_log: list[dict[str, Any]] = []
        self.intervention_state: list[dict[str, Any]] = []
        self.route_edge_history: dict[tuple[int, str], list[dict[str, Any]]] = {}
        self.temporary_edge_history: list[dict[str, Any]] = []
        self._active_episode_by_uid: dict[int, TravelEpisode] = {}
        self._identity_by_uid_ti: dict[tuple[int, int], dict[str, Any]] = {}
        self._traveller_vaccine_effective_from: dict[str, int] = {}
        self._traveller_vaccine_until: dict[str, int | None] = {}
        self._processed_arrival_episodes: set[tuple[str, str]] = set()
        self.state_snapshots: list[dict[str, Any]] = []
        self._initialised = False
        self._episodes_by_arrival: dict[date, list[TravelEpisode]] = defaultdict(list)
        self._episodes_by_departure: dict[date, list[TravelEpisode]] = defaultdict(list)
        self._episode_by_trip_person = {
            (item.trip_id, item.person_id): item for item in plan.episodes
        }
        self._episode_by_person = {
            item.person_id: item for item in plan.episodes if item.visitor_uid is not None
        }
        for episode in plan.episodes:
            self._episodes_by_arrival[episode.arrival_date].append(episode)
            self._episodes_by_departure[episode.departure_date].append(episode)
        self._resident_by_id = {
            str(row["agent_id"]): row for row in base_generated.m2_input.residents
        }
        self._m3_by_id = {
            str(row["agent_id"]): row for row in base_generated.m3_input.resident_structure
        }
        self._household_members: dict[str, list[str]] = defaultdict(list)
        self._residents_by_parish: dict[str, list[str]] = defaultdict(list)
        for row in base_generated.m2_input.residents:
            self._residents_by_parish[str(row["home_parish"])].append(str(row["agent_id"]))
            if row.get("household_id") is not None:
                self._household_members[str(row["household_id"])].append(str(row["agent_id"]))
        self._visitor_by_id = {row["visitor_uid"]: row for row in plan.visitor_records}
        initial_away = {
            agent_id
            for agent_id in self.base_generated.agent_ids
            if not self._resident_present_on(agent_id, self.start_date)
        }
        self.present_resident_ids.difference_update(initial_away)
        self.away_resident_ids.update(initial_away)

    @property
    def visitor_slot_ids(self) -> list[str]:
        return [f"visitor-slot-{index:06d}" for index in range(self.plan.visitor_capacity)]

    @property
    def total_agent_ids(self) -> list[str]:
        return [*self.base_generated.agent_ids, *self.visitor_slot_ids]

    @property
    def person_metadata(self) -> dict[str, dict[str, Any]]:
        metadata = {
            agent_id: {
                **self._resident_by_id[agent_id],
                **self._m3_by_id.get(agent_id, {}),
                "population_kind": "resident",
                "is_resident": True,
            }
            for agent_id in self.base_generated.agent_ids
        }
        for visitor_id, row in self._visitor_by_id.items():
            metadata[visitor_id] = {**row, "population_kind": "visitor", "is_resident": False}
        metadata.update(
            {
                slot: {
                    "age": 35,
                    "sex": "male",
                    "home_parish": "St Helier",
                    "population_kind": "visitor_slot",
                    "is_resident": False,
                }
                for slot in self.visitor_slot_ids
            }
        )
        return metadata

    def attach(self, sim: Any, disease: RespiratorySEIRS) -> None:
        self.sim = sim
        self.disease = disease
        self.uid_by_id = {agent_id: index for index, agent_id in enumerate(self.total_agent_ids)}
        self.id_by_uid = {uid: agent_id for agent_id, uid in self.uid_by_id.items()}
        self.visitor_slot_by_id = {
            visitor_id: self.uid_by_id[self.visitor_slot_ids[slot_index]]
            for visitor_id, slot_index in self.plan.visitor_slot_indices
        }
        # Slot UIDs deliberately retain their runtime slot name here. Historical
        # visitor identity is resolved only through the event-time interval map.
        self.disease._event_identity_resolver = self.event_identity
        self.disease._directional_modifier_resolver = self.directional_edge_factor

    def _episode_identity(self, episode: TravelEpisode, uid: int) -> dict[str, Any]:
        return {
            "runtime_slot_uid": uid,
            "slot_uid": uid,
            "actor_type": "visitor" if episode.visitor_uid is not None else "resident",
            "resident_or_visitor_id": episode.visitor_uid or episode.resident_agent_id,
            "visitor_id": episode.visitor_uid,
            "resident_agent_id": episode.resident_agent_id,
            "trip_id": episode.trip_id,
            "travel_party_id": episode.travel_party_id,
            "traveller_type": episode.traveller_type,
            "arrival_date": episode.arrival_date.isoformat(),
            "arrival_time_index": (episode.arrival_date - self.start_date).days,
            "departure_date": episode.departure_date.isoformat(),
            "departure_time_index": (episode.departure_date - self.start_date).days,
            "resident_or_visitor_status": (
                "visitor" if episode.visitor_uid is not None else "resident"
            ),
            "episode_identity_hash": episode.identity_hash,
        }

    def event_identity(self, uid: int, ti: int, prefix: str) -> dict[str, Any]:
        """Resolve an actor at event time; never consult the slot's later occupant."""

        identity = self._identity_by_uid_ti.get((uid, ti))
        if identity is None and uid < len(self.base_generated.agent_ids):
            agent_id = self.base_generated.agent_ids[uid]
            identity = {
                "runtime_slot_uid": uid,
                "slot_uid": uid,
                "actor_type": "resident",
                "resident_or_visitor_id": agent_id,
                "visitor_id": None,
                "resident_agent_id": agent_id,
                "trip_id": None,
                "travel_party_id": None,
                "traveller_type": None,
                "arrival_date": None,
                "arrival_time_index": None,
                "departure_date": None,
                "departure_time_index": None,
                "resident_or_visitor_status": "resident",
                "episode_identity_hash": None,
            }
        if identity is None:
            raise RuntimeError(f"inactive visitor slot {uid} has no identity at timestep {ti}")
        resolved = {f"{prefix}_{key}": value for key, value in identity.items()}
        resolved[f"{prefix}_agent_id"] = identity["resident_or_visitor_id"]
        resolved[f"{prefix}_population"] = identity["actor_type"]
        return resolved

    def _set_auids(self, uids: Iterable[int]) -> None:
        assert self.sim is not None
        values = set(uids)
        ordered = (
            np.arange(len(self.base_generated.agent_ids), dtype=np.int64)
            if values == self._all_resident_uids
            else np.asarray(sorted(values), dtype=np.int64)
        )
        self.sim.people.auids = self.sim.people.uid[ordered]

    def _active_uid_set(self) -> set[int]:
        return {self.uid_by_id[item] for item in self.present_resident_ids} | {
            self.visitor_slot_by_id[item] for item in self.active_visitor_ids
        }

    def _visitor_active(self, episode: TravelEpisode, when: date) -> bool:
        return (
            episode.arrival_date == when
            if episode.traveller_type == "DAY_VISITOR"
            else episode.arrival_date <= when < episode.departure_date
        )

    def _resident_present_on(self, agent_id: str, when: date) -> bool:
        return not any(
            item.resident_agent_id == agent_id
            and item.absence_start_date is not None
            and item.return_date is not None
            and item.absence_start_date <= when < item.return_date
            for item in self.plan.returning_resident_episodes
        )

    def _append_event(self, action: str, episode: TravelEpisode, **extra: Any) -> None:
        uid = (
            self.visitor_slot_by_id.get(episode.visitor_uid)
            if episode.visitor_uid is not None
            else self.uid_by_id.get(str(episode.resident_agent_id))
        )
        self.event_log.append(
            {
                "date": _iso(self.current_date),
                "time_index": self.current_ti,
                "action": action,
                "trip_id": episode.trip_id,
                "person_id": episode.person_id,
                "visitor_uid": episode.visitor_uid,
                "resident_agent_id": episode.resident_agent_id,
                "traveller_type": episode.traveller_type,
                "travel_party_id": episode.travel_party_id,
                "runtime_slot_uid": uid,
                "arrival_date": episode.arrival_date.isoformat(),
                "arrival_time_index": (episode.arrival_date - self.start_date).days,
                "departure_date": episode.departure_date.isoformat(),
                "departure_time_index": (episode.departure_date - self.start_date).days,
                "resident_or_visitor_status": (
                    "visitor" if episode.visitor_uid is not None else "resident"
                ),
                "episode_identity_hash": episode.identity_hash,
                "config_hash": self.config.intervention_hash,
                **extra,
            }
        )

    def _arrival_test(self, episode: TravelEpisode) -> None:
        controls = self.config.interventions
        if controls.testing_probability <= 0:
            return
        tested = (
            _stable_uniform(self.seed, "arrival-test", episode.trip_id, episode.person_id)
            < controls.testing_probability
        )
        if not tested:
            self._append_event("arrival_test_not_taken", episode)
            return
        infected = episode.disease_state_on_arrival in {"exposed", "infectious"}
        if episode.resident_agent_id is not None and self.disease is not None:
            uid = self.uid_by_id[episode.resident_agent_id]
            infected = bool(self.disease.exposed.raw[uid] or self.disease.infected.raw[uid])
        probability = controls.test_sensitivity if infected else 1.0 - controls.test_specificity
        detected = (
            _stable_uniform(self.seed, "arrival-test-result", episode.trip_id, episode.person_id)
            < probability
        )
        result_ti = self.current_ti + controls.test_result_delay_days
        runtime_slot_uid = (
            self.visitor_slot_by_id[episode.visitor_uid]
            if episode.visitor_uid is not None
            else self.uid_by_id[str(episode.resident_agent_id)]
        )
        self.pending_tests.append(
            ScheduledArrivalTest(
                result_time_index=result_ti,
                person_id=episode.person_id,
                detected=detected,
                actor_type="visitor" if episode.visitor_uid is not None else "resident",
                runtime_slot_uid=runtime_slot_uid,
                trip_id=episode.trip_id,
                travel_party_id=episode.travel_party_id,
                episode_identity_hash=episode.identity_hash,
                administration_time_index=self.current_ti,
            )
        )
        self._append_event(
            "arrival_test_administered",
            episode,
            tested=True,
            sensitivity=controls.test_sensitivity,
            specificity=controls.test_specificity,
            administration_time_index=self.current_ti,
            result_time_index=result_ti,
        )
        self._append_event(
            "arrival_test_result_scheduled",
            episode,
            administration_time_index=self.current_ti,
            result_time_index=result_ti,
        )

    def _schedule_quarantine(self, episode: TravelEpisode, cause: str, anchor_ti: int) -> None:
        controls = self.config.interventions
        if controls.quarantine_duration_days <= 0:
            return
        adheres = (
            _stable_uniform(self.seed, "quarantine-adherence", episode.person_id, cause, anchor_ti)
            < controls.quarantine_adherence
        )
        if not adheres:
            self._append_event("quarantine_declined", episode, cause="adherence")
            return
        activation_ti = anchor_ti + controls.quarantine_start_delay_days
        self.pending_quarantines.append((activation_ti, episode.trip_id, episode.person_id, cause))
        self._append_event(
            "quarantine_scheduled",
            episode,
            cause=cause,
            activation_time_index=activation_ti,
        )

    def _process_quarantines(self) -> None:
        due = [item for item in self.pending_quarantines if item[0] <= self.current_ti]
        self.pending_quarantines = [
            item for item in self.pending_quarantines if item[0] > self.current_ti
        ]
        for activation_ti, trip_id, person_id, cause in sorted(due):
            episode = self._episode_by_trip_person[(trip_id, person_id)]
            if episode.visitor_uid is not None:
                uid = self.visitor_slot_by_id[episode.visitor_uid]
                active_episode = self._active_episode_by_uid.get(uid)
                if (
                    episode.visitor_uid not in self.active_visitor_ids
                    or active_episode is None
                    or active_episode.identity_hash != episode.identity_hash
                    or not self._visitor_active(episode, self.current_date)
                ):
                    self._append_event(
                        "quarantine_not_activated_after_departure",
                        episode,
                        cause=cause,
                        activation_time_index=activation_ti,
                        actionable=False,
                    )
                    continue
            until = activation_ti + self.config.interventions.quarantine_duration_days
            self.quarantine_until[person_id] = max(until, self.quarantine_until.get(person_id, -1))
            self._quarantine_episode_by_person[person_id] = (
                episode.trip_id,
                episode.person_id,
            )
            self._append_event(
                "quarantine_activated",
                episode,
                cause=cause,
                release_time_index=self.quarantine_until[person_id],
            )

    def _release_quarantines(self) -> None:
        for person_id, until in sorted(tuple(self.quarantine_until.items())):
            if until != self.current_ti:
                continue
            self._append_event(
                "quarantine_released",
                self._episode_by_trip_person[self._quarantine_episode_by_person[person_id]],
                release_time_index=until,
            )

    def _process_test_results(self) -> None:
        controls = self.config.interventions
        due = [item for item in self.pending_tests if item.result_time_index <= self.current_ti]
        self.pending_tests = [
            item for item in self.pending_tests if item.result_time_index > self.current_ti
        ]
        for scheduled in sorted(due):
            episode = self._episode_by_trip_person[(scheduled.trip_id, scheduled.person_id)]
            if (
                scheduled.trip_id != episode.trip_id
                or scheduled.travel_party_id != episode.travel_party_id
                or scheduled.episode_identity_hash != episode.identity_hash
            ):
                raise RuntimeError("scheduled arrival-test episode identity changed")
            if episode.visitor_uid is not None:
                active_episode = self._active_episode_by_uid.get(scheduled.runtime_slot_uid)
                episode_active = bool(
                    episode.visitor_uid in self.active_visitor_ids
                    and active_episode is not None
                    and active_episode.identity_hash == scheduled.episode_identity_hash
                    and self._visitor_active(episode, self.current_date)
                )
            else:
                resident_id = str(episode.resident_agent_id)
                episode_active = bool(
                    scheduled.actor_type == "resident"
                    and scheduled.runtime_slot_uid == self.uid_by_id[resident_id]
                    and resident_id in self.present_resident_ids
                )
            result_fields = {
                "detected": scheduled.detected,
                "administration_time_index": scheduled.administration_time_index,
                "result_time_index": scheduled.result_time_index,
                "result_runtime_slot_uid": scheduled.runtime_slot_uid,
                "result_episode_identity_hash": scheduled.episode_identity_hash,
                "episode_active": episode_active,
                "actionable": episode_active,
            }
            if episode.visitor_uid is not None and not episode_active:
                self._append_event(
                    "test_result_available_after_departure",
                    episode,
                    **result_fields,
                )
                continue
            self._append_event(
                "arrival_test_result",
                episode,
                **result_fields,
            )
            if scheduled.detected and controls.quarantine_positive_only:
                self._schedule_quarantine(episode, "positive_test", scheduled.result_time_index)

    def initialize(
        self,
        *,
        initial_seed_count: int = 0,
        initial_prevalence: float | None = None,
    ) -> None:
        """Initialize the preallocated slots and resident-only seed state."""

        if self.sim is None or self.disease is None:
            raise RuntimeError("travel manager must be attached before initialize")
        people = self.sim.people
        people.alive[:] = False
        people.alive[np.asarray([self.uid_by_id[item] for item in self.present_resident_ids])] = (
            True
        )
        self.disease.susceptible[:] = False
        self.disease.exposed[:] = False
        self.disease.infected[:] = False
        self.disease.recovered[:] = False
        visitor_uids = np.asarray(
            [self.uid_by_id[slot] for slot in self.visitor_slot_ids], dtype=np.int64
        )
        if len(visitor_uids):
            self.disease.reset_person_state(visitor_uids)
            people.age[visitor_uids] = 0.0
            people.female[visitor_uids] = False
        resident_uids = np.asarray(
            [self.uid_by_id[item] for item in self.base_generated.agent_ids], dtype=np.int64
        )
        self.disease.susceptible[resident_uids] = True
        active_resident_uids = np.asarray(
            [self.uid_by_id[item] for item in self.present_resident_ids], dtype=np.int64
        )
        self._set_auids(active_resident_uids)
        self._initialised = True
        self.apply(self.sim)
        count = int(initial_seed_count)
        if initial_prevalence is not None:
            count = round(len(active_resident_uids) * float(initial_prevalence))
        if count > len(active_resident_uids):
            raise ValueError("initial infections cannot exceed resident population")
        if count:
            ordered = self.disease._ordered_uids(active_resident_uids, "seed")
            seeds = ordered[:count]
            sources = np.full(count, -1, dtype=np.int64)
            self.disease.set_prognoses(seeds, sources=sources)
            self.disease._record_events(
                seeds, sources, np.full(count, -1, dtype=np.int64), kind="seeded"
            )
            self.disease._seed_uids = [int(uid) for uid in seeds]

    def _activate_visitor(self, episode: TravelEpisode) -> None:
        assert self.disease is not None and self.sim is not None
        if episode.visitor_uid is None or episode.visitor_uid in self.active_visitor_ids:
            return
        uid = self.visitor_slot_by_id[episode.visitor_uid]
        self.active_visitor_ids.add(episode.visitor_uid)
        identity = self._episode_identity(episode, uid)
        self._active_episode_by_uid[uid] = episode
        self._identity_by_uid_ti[(uid, self.current_ti)] = identity
        self.sim.people.alive[uid] = True
        visitor = self._visitor_by_id[episode.visitor_uid]
        self.sim.people.age[uid] = float(visitor["age"])
        self.sim.people.female[uid] = visitor["sex"] == "female"
        self.disease.initialize_arrival_state(
            np.asarray([uid]),
            episode.disease_state_on_arrival,
            recovered_days_since=self.config.recovered_arrival_days_since_recovery,
        )
        controls = self.config.interventions
        if (
            _stable_uniform(self.seed, "visitor-vaccination-acceptance", episode.visitor_uid)
            < controls.traveller_vaccination_coverage
        ):
            effective_from = self.current_ti + controls.traveller_vaccination_protection_delay_days
            self._traveller_vaccine_effective_from[episode.visitor_uid] = effective_from
            self._traveller_vaccine_until[episode.visitor_uid] = (
                None
                if controls.traveller_vaccination_waning_days is None
                else effective_from + controls.traveller_vaccination_waning_days
            )
            self._append_event(
                "traveller_vaccine_administered",
                episode,
                effective_time_index=effective_from,
            )
        self._arrival_test(episode)
        if controls.quarantine_all_arrivals:
            self._schedule_quarantine(episode, "all_arrivals", self.current_ti)
        self._append_event(
            "visitor_arrived",
            episode,
            slot_uid=uid,
            active_age=float(self.sim.people.age[uid]),
            active_sex="female" if bool(self.sim.people.female[uid]) else "male",
            arrival_disease_state=episode.disease_state_on_arrival,
        )

    def _deactivate_visitor(self, episode: TravelEpisode) -> None:
        assert self.disease is not None and self.sim is not None
        if episode.visitor_uid is None or episode.visitor_uid not in self.active_visitor_ids:
            return
        uid = self.visitor_slot_by_id[episode.visitor_uid]
        self.active_visitor_ids.remove(episode.visitor_uid)
        self.sim.people.alive[uid] = False
        self._append_event("visitor_departed", episode, slot_uid=uid)
        self.disease.reset_person_state(np.asarray([uid]))
        self.sim.people.age[uid] = 0.0
        self.sim.people.female[uid] = False
        self._active_episode_by_uid.pop(uid, None)
        self.quarantine_until.pop(episode.person_id, None)
        self._quarantine_episode_by_person.pop(episode.person_id, None)
        self._traveller_vaccine_effective_from.pop(episode.person_id, None)
        self._traveller_vaccine_until.pop(episode.person_id, None)
        self._append_event(
            "visitor_slot_reset",
            episode,
            slot_uid=uid,
            alive=bool(self.sim.people.alive[uid]),
            susceptible=bool(self.disease.susceptible.raw[uid]),
            exposed=bool(self.disease.exposed.raw[uid]),
            infectious=bool(self.disease.infected.raw[uid]),
            recovered=bool(self.disease.recovered.raw[uid]),
            age=float(self.sim.people.age[uid]),
            rel_sus=float(self.disease.rel_sus.raw[uid]),
            rel_trans=float(self.disease.rel_trans.raw[uid]),
        )

    def _sync_traveller_modifiers(self) -> None:
        assert self.disease is not None and self.sim is not None
        n_agents = len(self.disease.rel_sus.raw)
        sus = np.ones(n_agents, dtype=float)
        trans = np.ones(n_agents, dtype=float)
        controls = self.config.interventions
        for visitor_id in self.active_visitor_ids:
            effective = self._traveller_vaccine_effective_from.get(visitor_id)
            until = self._traveller_vaccine_until.get(visitor_id)
            if effective is None or self.current_ti < effective:
                continue
            if until is not None and self.current_ti >= until:
                continue
            uid = self.visitor_slot_by_id[visitor_id]
            sus[uid] *= 1.0 - controls.traveller_vaccination_efficacy
            trans[uid] *= 1.0 - controls.traveller_vaccination_infectiousness_efficacy
        self.disease.set_modifier_component("m8_traveller_vaccination", sus, trans)

    def _returning_acquisition(self, episode: TravelEpisode) -> None:
        assert self.disease is not None
        resident_id = episode.resident_agent_id
        if resident_id is None:
            return
        uid = self.uid_by_id[resident_id]
        pressure = (
            self.config.returning_resident_external_acquisition_probability
            * self.config.interventions.travel_acquisition_multiplier
        )
        if not self.disease.susceptible.raw[uid] or pressure <= 0:
            return
        if (
            _stable_uniform(
                self.seed, "returning-resident-acquisition", resident_id, self.current_ti
            )
            >= pressure
        ):
            return
        self.disease.set_prognoses(np.asarray([uid]), sources=np.asarray([-1], dtype=np.int64))
        self.disease._record_events(
            np.asarray([uid]),
            np.asarray([-1], dtype=np.int64),
            np.asarray([-1], dtype=np.int64),
            kind="travel_imported",
        )
        self._append_event("returning_resident_acquisition", episode, route_id="travel_external")

    def apply(self, _sim: Any) -> None:
        """Apply arrivals/departures before disease state and network phases."""

        if not self._initialised and self.sim is None:
            raise RuntimeError("travel manager is not attached")
        if self.sim is None or self.disease is None:
            return
        raw_date = str(self.sim.t.now("str"))[:10].replace(".", "-")
        self.current_date = date.fromisoformat(raw_date)
        self.current_ti = int(self.disease.ti)
        planned_away_ids = {
            str(episode.resident_agent_id)
            for episode in self.plan.returning_resident_episodes
            if episode.resident_agent_id is not None
            and episode.absence_start_date is not None
            and episode.return_date is not None
            and episode.absence_start_date <= self.current_date < episode.return_date
        }
        travel_resident_ids = {
            str(episode.resident_agent_id)
            for episode in self.plan.returning_resident_episodes
            if episode.resident_agent_id is not None
        }
        self.present_resident_ids.difference_update(travel_resident_ids)
        self.present_resident_ids.update(travel_resident_ids - planned_away_ids)
        self.away_resident_ids = planned_away_ids
        for resident_id in travel_resident_ids:
            self.sim.people.alive[self.uid_by_id[resident_id]] = (
                resident_id in self.present_resident_ids
            )
        self._release_quarantines()
        self._process_test_results()
        self._process_quarantines()
        # Day visitors have an inclusive one-day active window, so they are
        # retired on the next dated callback.  The same guard also makes slot
        # lifecycle robust if a departure is reached after a callback gap.
        for visitor_id in sorted(self.active_visitor_ids):
            episode = self._episode_by_person[visitor_id]
            if not self._visitor_active(episode, self.current_date):
                self._deactivate_visitor(episode)
        for episode in self._episodes_by_departure.get(self.current_date, []):
            # RETURNING_RESIDENT episodes are return events.  Their absence
            # interval is applied at initialization and their arrival callback;
            # the equal departure/arrival date must not create a false outbound
            # transition in the same timestep.
            if (
                episode.resident_agent_id is not None
                and episode.traveller_type != "RETURNING_RESIDENT"
            ):
                raise RuntimeError(
                    "resident departure episodes are unsupported in the M8 return-event contract"
                )
        for episode in self._episodes_by_arrival.get(self.current_date, []):
            episode_key = (episode.trip_id, episode.person_id)
            if episode_key in self._processed_arrival_episodes:
                continue
            self._processed_arrival_episodes.add(episode_key)
            if episode.resident_agent_id is not None:
                resident_id = episode.resident_agent_id
                uid = self.uid_by_id[resident_id]
                resident_is_present = resident_id not in planned_away_ids
                if resident_is_present:
                    self.present_resident_ids.add(resident_id)
                    self.away_resident_ids.discard(resident_id)
                self.sim.people.alive[uid] = resident_is_present
                self._returning_acquisition(episode)
                self._arrival_test(episode)
                if self.config.interventions.quarantine_all_arrivals:
                    self._schedule_quarantine(episode, "all_arrivals", self.current_ti)
                self._append_event("resident_returned", episode)
            elif episode.visitor_uid is not None:
                self._activate_visitor(episode)
        # Delay-zero results and delay-zero all-arrival quarantine activate at
        # this declared pre-network/pre-transmission arrival phase.
        self._process_test_results()
        self._process_quarantines()
        for visitor_id in self.active_visitor_ids:
            uid = self.visitor_slot_by_id[visitor_id]
            self._identity_by_uid_ti[(uid, self.current_ti)] = self._episode_identity(
                self._episode_by_person[visitor_id], uid
            )
        self._sync_traveller_modifiers()
        planned_away = int(self.plan.daily_stream[self.current_ti]["resident_away"])
        if len(self.away_resident_ids) != planned_away:
            raise RuntimeError(
                "planned and runtime resident-away counts differ: "
                f"date={self.current_date.isoformat()}, planned={planned_away}, "
                f"runtime={len(self.away_resident_ids)}"
            )
        self._set_auids(self._active_uid_set())
        for route_id in TRAVEL_ROUTE_IDS:
            self.route_edge_history[(self.current_ti, route_id)] = self.route_edges(
                route_id, self.current_date
            )
        state = {
            "date": _iso(self.current_date),
            "time_index": self.current_ti,
            "active_visitors": len(self.active_visitor_ids),
            "resident_present": len(self.present_resident_ids),
            "resident_away": len(self.away_resident_ids),
            "quarantined_travellers": sum(
                value > self.current_ti for value in self.quarantine_until.values()
            ),
            "testing_pending": len(self.pending_tests),
            "config_hash": self.config.intervention_hash,
        }
        if self.intervention_state and self.intervention_state[-1]["time_index"] == self.current_ti:
            self.intervention_state[-1] = state
        else:
            self.intervention_state.append(state)

    def capture(self, _sim: Any) -> None:
        """Capture post-transmission active-state counts for dated outputs."""

        if self.sim is None or self.disease is None:
            return
        active = np.fromiter(self._active_uid_set(), dtype=np.int64)
        resident = np.fromiter(
            (self.uid_by_id[item] for item in self.present_resident_ids), dtype=np.int64
        )
        visitors = np.fromiter(
            (self.visitor_slot_by_id[item] for item in self.active_visitor_ids),
            dtype=np.int64,
        )
        self.state_snapshots.append(
            {
                "susceptible": int(np.count_nonzero(self.disease.susceptible.raw[active])),
                "exposed": int(np.count_nonzero(self.disease.exposed.raw[active])),
                "infectious": int(np.count_nonzero(self.disease.infected.raw[active])),
                "recovered": int(np.count_nonzero(self.disease.recovered.raw[active])),
                "resident_infectious": int(np.count_nonzero(self.disease.infected.raw[resident])),
                "visitor_infectious": int(np.count_nonzero(self.disease.infected.raw[visitors])),
            }
        )

    def _quarantine_factor(self, person_id: str, route_id: str) -> float:
        if self.quarantine_until.get(person_id, -1) <= self.current_ti:
            return 1.0
        if route_id in {"household", "visitor_accommodation", "visitor_host_household"}:
            return self.config.interventions.quarantine_accommodation_multiplier
        return self.config.interventions.quarantine_external_route_multiplier

    def _edge_factor(self, route_id: str, people: Iterable[str]) -> float:
        factor = float(self.config.visitor_route_multipliers[route_id])
        if self.config.enable_transmission_seasonality:
            factor *= self.config.transmission_seasonality.multiplier(self.current_date)
        if route_id == "arrival_terminal":
            factor *= self.config.interventions.terminal_contact_multiplier
        return factor

    def directional_edge_factor(
        self, route_id: str, source_uid: int, target_uid: int, ti: int
    ) -> float:
        """Return exact endpoint/direction-specific M8 effects at transmission time."""

        if route_id not in TRAVEL_ROUTE_IDS:
            return 1.0
        source = self.event_identity(source_uid, ti, "source")
        target = self.event_identity(target_uid, ti, "target")
        source_kind = source["source_actor_type"]
        target_kind = target["target_actor_type"]
        factor = 1.0
        if source_kind == "visitor" and target_kind == "resident":
            factor *= self.config.visitor_to_resident_multiplier
        for identity in (source, target):
            person_id = str(
                identity[f"{'source' if identity is source else 'target'}_resident_or_visitor_id"]
            )
            factor *= self._quarantine_factor(person_id, route_id)
        return max(0.0, min(1.0, factor))

    def _visitor_rows_active(self, when: date) -> list[dict[str, Any]]:
        return [
            row
            for row in self.plan.visitor_records
            if self._visitor_active(self._episode_by_person[row["visitor_uid"]], when)
        ]

    def _resident_pool(self, parish: str, token: object, limit: int) -> list[str]:
        candidates = self._residents_by_parish.get(parish, [])
        if not candidates or limit <= 0:
            return []
        if len(self.present_resident_ids) == len(self.base_generated.agent_ids):
            start = _stable_int(self.seed, "resident-pool", token) % len(candidates)
            return [
                candidates[(start + offset) % len(candidates)]
                for offset in range(min(limit, len(candidates)))
            ]
        present = [item for item in candidates if item in self.present_resident_ids]
        if len(present) <= limit:
            return present
        start = _stable_int(self.seed, "resident-pool", token) % len(present)
        return [present[(start + offset) % len(present)] for offset in range(limit)]

    def _groups_by(self, rows: list[dict[str, Any]], key: str) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = defaultdict(list)
        for row in rows:
            groups[str(row.get(key) or "unknown")].append(str(row["visitor_uid"]))
        return groups

    def route_edges(self, route_id: str, when: date) -> list[dict[str, Any]]:
        active_rows = self._visitor_rows_active(when)
        edges: list[dict[str, Any]] = []
        if route_id == "arrival_terminal":
            if self.config.terminal_mixing_contacts == 0:
                return []
            arrivals = [
                row
                for row in self.plan.visitor_records
                if self._episode_by_person[row["visitor_uid"]].arrival_date == when
            ]
            for terminal, group in self._groups_by(arrivals, "entry_terminal").items():
                resident_pool = self._resident_pool(
                    "St Helier", terminal, self.config.terminal_mixing_contacts
                )
                ids = [*group, *resident_pool]
                edge_weight = self.config.arrival_terminal_edge_weight * self._edge_factor(
                    route_id, ids
                )
                edges.extend(_ring_edges(ids, self.config.terminal_mixing_contacts, edge_weight, 1))
        elif route_id == "visitor_party":
            if self.config.visitor_party_contacts == 0:
                return []
            for _party_id, group in sorted(self._groups_by(active_rows, "travel_party_id").items()):
                ordered = sorted(group)
                edges.extend(
                    _ring_edges(
                        ordered,
                        min(self.config.visitor_party_contacts, len(ordered) - 1),
                        self.config.visitor_party_edge_weight
                        * self._edge_factor(route_id, ordered),
                        1,
                    )
                )
        elif route_id == "visitor_accommodation":
            if self.config.visitor_accommodation_contacts == 0:
                return []
            groups: dict[str, list[str]] = defaultdict(list)
            for row in active_rows:
                if row["accommodation_id"] is not None:
                    groups[str(row["accommodation_id"])].append(str(row["visitor_uid"]))
            for accommodation, group in sorted(groups.items()):
                ordered = sorted(
                    group,
                    key=lambda item: (
                        _stable_int(self.seed, "accommodation", accommodation, item),
                        item,
                    ),
                )
                for start in range(0, len(ordered), self.config.accommodation_group_capacity):
                    members = ordered[start : start + self.config.accommodation_group_capacity]
                    edges.extend(
                        _ring_edges(
                            members,
                            min(self.config.visitor_accommodation_contacts, len(members) - 1),
                            self.config.visitor_accommodation_edge_weight
                            * self._edge_factor(route_id, members),
                            7,
                        )
                    )
        elif route_id == "visitor_host_household":
            for row in active_rows:
                household = row.get("host_household_id")
                if household is None:
                    continue
                visitor_id = str(row["visitor_uid"])
                for resident_id in sorted(self._household_members.get(str(household), [])):
                    edges.append(
                        {
                            "p1": visitor_id,
                            "p2": resident_id,
                            "weight": self.config.visitor_host_household_edge_weight
                            * self._edge_factor(route_id, (visitor_id, resident_id)),
                            "duration_days": 1,
                        }
                    )
        elif route_id == "visitor_transit":
            if self.config.visitor_transit_contacts == 0:
                return []
            transit_groups: dict[tuple[str, LocalTransportType], list[dict[str, Any]]] = (
                defaultdict(list)
            )
            for row in active_rows:
                if row["local_transport_type"] != "WALKING_OTHER":
                    transit_groups[(str(row["home_parish"]), row["local_transport_type"])].append(
                        row
                    )
            for key, rows in sorted(transit_groups.items(), key=lambda item: str(item[0])):
                group = [str(row["visitor_uid"]) for row in rows]
                if key[1] == "BUS":
                    edges.extend(
                        _ring_edges(
                            sorted(group),
                            self.config.visitor_transit_contacts,
                            self.config.visitor_transit_bus_edge_weight
                            * self._edge_factor(route_id, group),
                            1,
                        )
                    )
                elif key[1] == "TAXI_RIDE":
                    ordered = sorted(
                        group,
                        key=lambda item: (_stable_int(self.seed, "taxi-unit", when, item), item),
                    )
                    for start in range(0, len(ordered), self.config.taxi_capacity):
                        unit = ordered[start : start + self.config.taxi_capacity]
                        unit_id = (
                            f"taxi-{when:%Y%m%d}-{key[0]}-{start // self.config.taxi_capacity:04d}"
                        )
                        edges.extend(
                            {**edge, "transport_unit_id": unit_id}
                            for edge in _complete_group(
                                unit,
                                self.config.visitor_transit_vehicle_edge_weight
                                * self._edge_factor(route_id, unit),
                                1,
                            )
                        )
                elif key[1] == "PRIVATE_RENTAL_CAR":
                    for _party, unit in sorted(self._groups_by(rows, "travel_party_id").items()):
                        ordered = sorted(unit)
                        for start in range(0, len(ordered), self.config.private_vehicle_capacity):
                            vehicle = ordered[start : start + self.config.private_vehicle_capacity]
                            edges.extend(
                                _complete_group(
                                    vehicle,
                                    self.config.visitor_transit_vehicle_edge_weight
                                    * self._edge_factor(route_id, vehicle),
                                    1,
                                )
                            )
                elif key[1] == "HOST_PICKUP":
                    for row in rows:
                        visitor_id = str(row["visitor_uid"])
                        household = row.get("host_household_id")
                        hosts = self._household_members.get(str(household), [])
                        if hosts:
                            host_id = sorted(hosts)[
                                _stable_int(self.seed, "host-pickup", when, visitor_id) % len(hosts)
                            ]
                            edges.append(
                                {
                                    "p1": visitor_id,
                                    "p2": host_id,
                                    "weight": self.config.visitor_transit_vehicle_edge_weight
                                    * self._edge_factor(route_id, (visitor_id, host_id)),
                                    "duration_days": 1,
                                }
                            )
        elif route_id in {"visitor_community_indoor", "visitor_community_outdoor"}:
            if self.config.visitor_community_contacts == 0:
                return []
            probability = (
                self.config.visitor_community_indoor_probability
                if route_id.endswith("indoor")
                else self.config.visitor_community_outdoor_probability
            )
            community_groups: dict[str, list[str]] = defaultdict(list)
            for row in active_rows:
                visitor_id = str(row["visitor_uid"])
                if _stable_uniform(self.seed, route_id, when.isoformat(), visitor_id) < probability:
                    community_groups[str(row["home_parish"])].append(visitor_id)
            for parish, group in sorted(community_groups.items()):
                resident_pool = self._resident_pool(
                    parish, (route_id, when.isoformat()), self.config.visitor_community_contacts
                )
                ids = [*group, *resident_pool]
                edges.extend(
                    _ring_edges(
                        sorted(ids),
                        self.config.visitor_community_contacts,
                        (
                            self.config.visitor_community_indoor_edge_weight
                            if route_id.endswith("indoor")
                            else self.config.visitor_community_outdoor_edge_weight
                        )
                        * self._edge_factor(route_id, ids),
                        1,
                    )
                )
        # Route construction uses stable episode IDs for grouping and policy
        # factors, then translates temporary people to the preallocated slot
        # namespace required by the Starsim adapter.
        translated = [
            {
                **edge,
                "p1": self._route_endpoint(edge["p1"]),
                "p2": self._route_endpoint(edge["p2"]),
            }
            for edge in edges
        ]
        return _deduplicate_edges(translated)

    def _route_endpoint(self, person_id: str) -> str:
        slot_index = self._planned_slot_by_visitor.get(person_id)
        if slot_index is None:
            return person_id
        return self.visitor_slot_ids[slot_index]

    def filtered_base_edges(self, route_id: str, when: date) -> list[dict[str, Any]]:
        edges = self.base_generated.route_snapshot(route_id, when).edges
        if not self.plan.returning_resident_episodes and not self.quarantine_until:
            return list(edges)
        effective: list[dict[str, Any]] = []
        for edge in edges:
            p1, p2 = str(edge["p1"]), str(edge["p2"])
            if p1 not in self.present_resident_ids or p2 not in self.present_resident_ids:
                continue
            factor = self._quarantine_factor(p1, route_id) * self._quarantine_factor(p2, route_id)
            if factor > 0:
                effective.append({**edge, "weight": float(edge["weight"]) * factor})
        return effective

    def temporary_edge_rows(self) -> list[dict[str, Any]]:
        """Canonical exact sparse representation of every executed temporary edge."""

        rows: list[dict[str, Any]] = []
        for (ti, route_id), edges in sorted(self.route_edge_history.items()):
            when = self.start_date + timedelta(days=ti)
            for edge in edges:
                p1_uid = self.uid_by_id[str(edge["p1"])]
                p2_uid = self.uid_by_id[str(edge["p2"])]
                p1 = self.event_identity(p1_uid, ti, "p1")
                p2 = self.event_identity(p2_uid, ti, "p2")
                visitor_ids = [
                    item
                    for item in (p1.get("p1_visitor_id"), p2.get("p2_visitor_id"))
                    if item is not None
                ]
                visitor = self._visitor_by_id.get(str(visitor_ids[0])) if visitor_ids else None
                rows.append(
                    {
                        "date": when.isoformat(),
                        "time_index": ti,
                        "route_id": route_id,
                        **p1,
                        **p2,
                        "edge_weight": float(edge["weight"]),
                        "duration_days": int(edge.get("persistence_days", 1)),
                        "travel_party_id": visitor.get("travel_party_id") if visitor else None,
                        "accommodation_id": visitor.get("accommodation_id") if visitor else None,
                        "transport_type": (
                            visitor.get("local_transport_type") if visitor else None
                        ),
                        "transport_unit_id": edge.get("transport_unit_id"),
                    }
                )
        return sorted(
            rows,
            key=lambda row: (
                row["time_index"],
                row["route_id"],
                row["p1_runtime_slot_uid"],
                row["p2_runtime_slot_uid"],
            ),
        )

    def route_view(self) -> GeneratedNetworks:
        """Create a shallow route view while retaining the immutable M4 hash."""

        view = copy.copy(self.base_generated)
        view.agent_ids = self.total_agent_ids
        view.route_specs = dict(self.base_generated.route_specs)
        view.structural_edges = {
            key: list(value) for key, value in self.base_generated.structural_edges.items()
        }
        view.route_memberships = {
            key: list(value) for key, value in self.base_generated.route_memberships.items()
        }
        view._dynamic_builders = dict(self.base_generated._dynamic_builders)
        view._snapshot_cache = {}
        route_weights = _configured_route_weights(self.config)
        for route_id in TRAVEL_ROUTE_IDS:
            view.route_specs[route_id] = _travel_spec(
                route_id,
                route_id
                in {"visitor_accommodation", "visitor_host_household", "visitor_community_indoor"},
                route_weights[route_id],
                "M8 synthetic temporary episode/activity membership",
                weight_components=(
                    {
                        "bus": self.config.visitor_transit_bus_edge_weight,
                        "vehicle": self.config.visitor_transit_vehicle_edge_weight,
                    }
                    if route_id == "visitor_transit"
                    else None
                ),
            )
            view.structural_edges[route_id] = []
            view.route_memberships[route_id] = []

            def travel_builder(when: date, route_id: str = route_id) -> list[dict[str, Any]]:
                return self.route_edges(route_id, when)

            view._dynamic_builders[route_id] = travel_builder
        if self.plan.returning_resident_episodes:
            for route_id in self.base_generated.route_specs:

                def resident_builder(when: date, route_id: str = route_id) -> list[dict[str, Any]]:
                    return self.filtered_base_edges(route_id, when)

                view._dynamic_builders[route_id] = resident_builder
        # The logical parent identity intentionally remains the M4 hash.  The
        # temporary network has its own hash in the M8 result/manifest.
        view.logical_content_hash = self.base_generated.logical_content_hash
        return view

    def classify_event(self, event: dict[str, Any]) -> dict[str, Any]:
        infected_id = event.get("infected_agent_id")
        infected_kind = event.get("infected_actor_type") or event.get("infected_population")
        infector_id = event.get("infector_agent_id")
        infector_kind = event.get("infector_actor_type") or event.get("infector_population")
        direction = (
            f"{infector_kind}_to_{infected_kind}"
            if infector_kind
            else f"external_to_{infected_kind}"
        )
        return {
            **event,
            "infected_agent_id": infected_id,
            "infector_agent_id": infector_id,
            "infected_population": infected_kind,
            "infector_population": infector_kind,
            "transmission_direction": direction,
            "travel_linked": bool(
                event.get("source_kind") == "local"
                and (infected_kind == "visitor" or infector_kind == "visitor")
            ),
        }

    def seasonality_rows(self) -> list[dict[str, Any]]:
        rows = []
        for when in _dates(self.start_date, self.duration_days):
            rows.append(
                {
                    "date": _iso(when),
                    "visitor_intensity_multiplier": self.config.visitor_seasonality.multiplier(
                        when
                    ),
                    "transmission_seasonality_multiplier": (
                        self.config.transmission_seasonality.multiplier(when)
                    )
                    if self.config.enable_transmission_seasonality
                    else 1.0,
                    "community_seasonal_multiplier": (
                        self.config.transmission_seasonality.multiplier(when)
                    )
                    if self.config.enable_transmission_seasonality
                    else 1.0,
                    "visitor_profile_id": self.config.visitor_seasonality.profile_id,
                    "transmission_profile_id": self.config.transmission_seasonality.profile_id,
                    "source_status": self.config.visitor_seasonality.status,
                    "config_hash": self.config.seasonality_hash,
                }
            )
        return rows

    def high_risk_rows(self) -> list[dict[str, Any]]:
        config: HighRiskConfig = self.config.high_risk
        rows: list[dict[str, Any]] = []
        care_staff_ids = {row["agent_id"] for row in self.base_generated.care_staff_assignments}
        for agent_id in self.base_generated.agent_ids:
            m2 = self._resident_by_id[agent_id]
            m3 = self._m3_by_id.get(agent_id, {})
            if int(m2["age"]) >= config.older_age_threshold:
                stratum: RiskStratum = "older_resident"
            elif m2.get("care_setting_id") is not None and config.include_care_residents:
                stratum = "care_resident"
            elif agent_id in care_staff_ids and config.include_care_staff:
                stratum = "care_staff"
            elif (
                config.include_occupational_exposure
                and str(m3.get("employment_sector")) in config.occupational_sectors
            ):
                stratum = "occupational_exposure"
            else:
                stratum = "general_resident"
            rows.append(
                {
                    "agent_id": agent_id,
                    "population_kind": "resident",
                    "risk_stratum": stratum,
                    "targeting_only": True,
                    "biological_risk_multiplier": config.biological_risk_multiplier,
                    "severity_model_implemented": False,
                    "config_hash": config.config_hash,
                }
            )
        for visitor_id in sorted(self._visitor_by_id):
            rows.append(
                {
                    "agent_id": visitor_id,
                    "population_kind": "visitor",
                    "risk_stratum": "visitor_travel_exposure"
                    if config.include_visitor_travel_exposure
                    else "general_resident",
                    "targeting_only": True,
                    "biological_risk_multiplier": config.biological_risk_multiplier,
                    "severity_model_implemented": False,
                    "config_hash": config.config_hash,
                }
            )
        return rows


@dataclass(frozen=True)
class TravelRunResult:
    """Visualization-ready M8 run outputs and reconstructibility hashes."""

    config: OutbreakRunConfig
    parameters: RespiratoryParameterSet
    travel_config: TravelConfig
    base_generated: GeneratedNetworks
    travel_plan: TravelPlan
    daily_epidemic: list[dict[str, Any]]
    daily_parish: list[dict[str, Any]]
    daily_route: list[dict[str, Any]]
    daily_age: list[dict[str, Any]]
    transmission_events: list[dict[str, Any]]
    daily_travel_population: list[dict[str, Any]]
    travel_episodes: list[dict[str, Any]]
    visitor_events: list[dict[str, Any]]
    daily_travel_route: list[dict[str, Any]]
    temporary_edges: list[dict[str, Any]]
    travel_transmission_events: list[dict[str, Any]]
    travel_intervention_events: list[dict[str, Any]]
    daily_travel_intervention_state: list[dict[str, Any]]
    seasonality_schedule: list[dict[str, Any]]
    high_risk_strata: list[dict[str, Any]]
    high_risk_epidemic: list[dict[str, Any]]
    diagnostics: dict[str, Any]
    scenario_hash: str
    travel_config_hash: str
    visitor_episode_hash: str
    temporary_network_hash: str
    seasonality_hash: str
    latent_outcome_hash: str
    artifact_bundle_hash: str
    runtime_seconds: float
    peak_memory_bytes: int | None
    m7_intervention_state: list[dict[str, Any]] = field(default_factory=list)
    m7_intervention_events: list[dict[str, Any]] = field(default_factory=list)
    m7_intervention_route_effects: list[dict[str, Any]] = field(default_factory=list)
    m7_intervention_diagnostics: dict[str, Any] = field(default_factory=dict)
    observation_config: ObservationConfig | None = None
    scenario_config: ScenarioConfig | None = None
    observation_events: list[dict[str, Any]] = field(default_factory=list)
    detection_events: tuple[DetectionEvent, ...] = ()
    delivered_detection_events: tuple[DetectionEvent, ...] = ()


def _git_metadata(root: Path) -> tuple[str | None, bool]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=False, capture_output=True, text=True
        )
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=root, check=False, capture_output=True, text=True
        )
        return commit.stdout.strip() or None, bool(status.stdout.strip())
    except OSError:
        return None, True


def _daily_metrics(
    disease: RespiratorySEIRS,
    manager: TravelManager,
    config: OutbreakRunConfig,
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    dates = _dates(config.start_date, config.duration_days)
    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        by_date[str(event["date"])].append(event)
    daily: list[dict[str, Any]] = []
    cumulative_resident = 0
    cumulative_visitor = 0
    acquisition_kinds = {"local", "imported", "travel_imported"}
    for index, when in enumerate(dates):
        stream = manager.plan.daily_stream[index]
        state = (
            manager.state_snapshots[index]
            if index < len(manager.state_snapshots)
            else {
                "susceptible": 0,
                "exposed": 0,
                "infectious": 0,
                "recovered": 0,
                "resident_infectious": 0,
                "visitor_infectious": 0,
            }
        )
        day_events = by_date[_iso(when)]
        resident_infections = sum(
            event["infected_population"] == "resident" and event["source_kind"] in acquisition_kinds
            for event in day_events
        )
        visitor_infections = sum(
            event["infected_population"] == "visitor" and event["source_kind"] in acquisition_kinds
            for event in day_events
        )
        seeded_infections = sum(event["source_kind"] == "seeded" for event in day_events)
        travel_acquisitions = sum(event["source_kind"] == "travel_imported" for event in day_events)
        visitor_linked = sum(event.get("travel_linked", False) for event in day_events)
        cumulative_resident += resident_infections
        cumulative_visitor += visitor_infections
        daily.append(
            {
                "date": _iso(when),
                "time_index": index,
                "resident_present": stream["resident_present"],
                "resident_away": stream["resident_away"],
                "active_visitors": stream["active_visitors"],
                "present_population": stream["present_population"],
                "susceptible": state["susceptible"],
                "exposed": state["exposed"],
                "infectious": state["infectious"],
                "recovered": state["recovered"],
                "new_infections": resident_infections + visitor_infections,
                "resident_infections": resident_infections,
                "visitor_infections": visitor_infections,
                "seeded_infections": seeded_infections,
                "returning_resident_travel_acquisitions": travel_acquisitions,
                "visitor_linked_local_acquisitions": visitor_linked,
                "resident_attack_rate": cumulative_resident
                / max(1, len(manager.base_generated.agent_ids)),
                "visitor_arrived_denominator": sum(
                    episode.visitor_uid is not None and episode.arrival_date <= when
                    for episode in manager.plan.episodes
                ),
                "visitor_attack_rate": cumulative_visitor
                / max(
                    1,
                    sum(
                        episode.visitor_uid is not None and episode.arrival_date <= when
                        for episode in manager.plan.episodes
                    ),
                ),
                "present_prevalence": state["infectious"] / max(1, stream["present_population"]),
                "resident_infectious": state["resident_infectious"],
                "visitor_infectious": state["visitor_infectious"],
            }
        )
    return daily


def _high_risk_epidemic_rows(
    manager: TravelManager,
    strata: list[dict[str, Any]],
    events: list[dict[str, Any]],
    start_date: date,
    duration_days: int,
) -> list[dict[str, Any]]:
    """Export targeting strata without implying severity biology."""

    stratum_by_id = {str(row["agent_id"]): str(row["risk_stratum"]) for row in strata}
    rows: list[dict[str, Any]] = []
    for when in _dates(start_date, duration_days):
        date_key = _iso(when)
        day_events = [event for event in events if event["date"] == date_key]
        detection_events = [
            event
            for event in manager.event_log
            if event["date"] == date_key
            and event["action"] == "arrival_test_result"
            and event.get("detected")
        ]
        for stratum in sorted(set(stratum_by_id.values())):
            selected = [
                event
                for event in day_events
                if stratum_by_id.get(str(event["infected_agent_id"])) == stratum
            ]
            rows.append(
                {
                    "date": date_key,
                    "time_index": (when - start_date).days,
                    "risk_stratum": stratum,
                    "new_infections": len(selected),
                    "new_local_infections": sum(
                        event["source_kind"] == "local" for event in selected
                    ),
                    "new_travel_acquisitions": sum(
                        event["source_kind"] == "travel_imported" for event in selected
                    ),
                    "detections": sum(
                        stratum_by_id.get(str(event.get("visitor_uid"))) == stratum
                        for event in detection_events
                    ),
                    "targeting_only": True,
                    "severity_model_implemented": False,
                }
            )
    return rows


def run_travel_outbreak(
    generated: GeneratedNetworks,
    config: OutbreakRunConfig,
    parameters: RespiratoryParameterSet,
    travel_config: TravelConfig,
    *,
    observation_config: ObservationConfig | None = None,
    scenario: ScenarioConfig | None = None,
) -> TravelRunResult:
    """Run a travel-aware synthetic epidemic through the preallocated slots."""

    if generated.config.mode != config.mode:
        raise ValueError("M8 run mode must match the M4 route artifact")
    if config.parameter_set_id != parameters.parameter_set_id:
        raise ValueError("run parameter_set_id does not match parameters")
    if config.dt_days != 1.0:
        raise ValueError("M8 supports only the verified daily timestep")
    if travel_config.mode == "disabled":
        raise ValueError("run_travel_outbreak requires an explicit or generic travel mode")
    if scenario is not None:
        if scenario.travel is not None and scenario.travel.config_hash != travel_config.config_hash:
            raise ValueError("scenario travel config does not match the supplied travel config")
        if scenario.seed is not None and scenario.seed != config.seed:
            raise ValueError("scenario seed must match the travel run seed")
        if scenario.start_date is not None and scenario.start_date != config.start_date:
            raise ValueError("scenario start_date must match the travel run start_date")
        if scenario.duration_days is not None and scenario.duration_days != config.duration_days:
            raise ValueError("scenario duration_days must match the travel run duration_days")
        if (
            any(
                item.type in {"case_isolation", "household_quarantine"}
                for item in scenario.interventions
            )
            and observation_config is None
        ):
            raise ValueError("detection-triggered interventions require an observation_config")
    started = time.perf_counter()
    before_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    plan = generate_travel_episodes(
        travel_config,
        seed=config.seed,
        start_date=config.start_date,
        duration_days=config.duration_days,
        residents=generated.m2_input.residents,
        households=generated.m2_input.households,
    )
    manager = TravelManager(
        generated,
        plan,
        travel_config,
        seed=config.seed,
        start_date=config.start_date,
        duration_days=config.duration_days,
    )
    view = manager.route_view()
    m7_manager = (
        InterventionManager(
            view,
            scenario.interventions,
            run_seed=config.seed,
            start_date=config.start_date,
            duration_days=config.duration_days,
            scenario=scenario,
        )
        if scenario is not None and scenario.interventions
        else None
    )
    route_betas: dict[str, float] = {}
    for route_id in view.route_specs:
        if route_id in config.route_multipliers:
            route_betas[route_id] = config.beta * float(config.route_multipliers[route_id])
        else:
            # The M8 multiplier is part of the sparse temporary edge weight so
            # quarantine and mixed-route controls can vary by active person;
            # applying it again at disease beta would double-count it.
            route_betas[route_id] = config.beta
    if travel_config.enable_transmission_seasonality:
        maximum = travel_config.transmission_seasonality.maximum
        if any(beta * maximum > 1.0 for beta in route_betas.values()):
            raise ValueError("travel transmission seasonality can push beta above 1")
    generic_enabled = travel_config.mode in {"generic_import_only", "both"}
    disease = RespiratorySEIRS(
        route_betas=route_betas,
        initial_seed_count=config.initial_seed_count,
        initial_prevalence=config.initial_prevalence,
        import_schedule=config.import_schedule if generic_enabled else {},
        import_rate_per_day=config.import_rate_per_day if generic_enabled else 0.0,
        latent_period_days=config.latent_period_days,
        infectious_period_days=config.infectious_period_days,
        immunity_duration_days=config.immunity_duration_days,
        waning_enabled=config.waning_enabled,
        observation_scheduler=None,
    )
    # Initial resident seeds are selected by TravelManager after sim.init so
    # inactive temporary slots can never enter the seed denominator.
    disease.pars.initial_seed_count = 0
    disease.pars.initial_prevalence = None
    people_ids = manager.total_agent_ids
    metadata = manager.person_metadata
    ages = np.asarray([metadata[agent_id]["age"] for agent_id in people_ids], dtype=float)
    female = np.asarray(
        [metadata[agent_id]["sex"] == "female" for agent_id in people_ids], dtype=bool
    )
    sim = build_starsim_travel_sim(
        view,
        disease,
        agent_ids=people_ids,
        ages=ages,
        female=female,
        start_date=config.start_date,
        duration_days=config.duration_days,
        seed=config.seed,
        interventions=[m7_manager] if m7_manager is not None else None,
    )
    manager.attach(sim, disease)
    scheduler: ObservationScheduler | None = None
    if observation_config is not None:
        scheduler = ObservationScheduler(
            latent_seed=config.seed,
            start_date=config.start_date,
            config=observation_config,
            agent_id_by_uid=manager.id_by_uid,
            resident_by_agent_id=metadata,
            consumer=m7_manager,
        )
        disease._observation_scheduler = scheduler

        def deliver_detection_notifications(_sim: Any) -> None:
            scheduler.deliver_due(int(disease.ti))

        sim.loop.insert(deliver_detection_notifications, label=f"{disease.name}.step")
    manager.initialize(
        initial_seed_count=config.initial_seed_count,
        initial_prevalence=config.initial_prevalence,
    )
    sim.loop.insert(manager.apply, label=f"{disease.name}.step_state", before=True)
    sim.loop.insert(manager.capture, label=f"{disease.name}.step")
    sim.run(verbose=0)
    observation_schedule = scheduler.snapshot() if scheduler is not None else None
    events = [manager.classify_event(event) for event in disease._all_events]
    # The event list has to be classified after the run, but the runner also
    # records terminal/accommodation lifecycle separately in visitor_events.
    daily_epidemic = _daily_metrics(disease, manager, config, events)
    event_by_route: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        event_by_route[(str(event["date"]), str(event["route_id"]))].append(event)
    daily_route: list[dict[str, Any]] = []
    local_events_by_date = Counter(
        event["date"] for event in events if event["source_kind"] == "local"
    )
    for index, when in enumerate(_dates(config.start_date, config.duration_days)):
        for route_id in TRAVEL_ROUTE_IDS:
            edges = manager.route_edge_history.get(
                (index, route_id), manager.route_edges(route_id, when)
            )
            route_events = event_by_route[(_iso(when), route_id)]
            direction_counts = Counter(event["transmission_direction"] for event in route_events)
            daily_route.append(
                {
                    "date": _iso(when),
                    "time_index": index,
                    "route_id": route_id,
                    "active_edges": len(edges),
                    "active_contacts": len(
                        {endpoint for edge in edges for endpoint in (edge["p1"], edge["p2"])}
                    ),
                    "new_local_infections": sum(
                        event["source_kind"] == "local" for event in route_events
                    ),
                    "share_of_local_transmission": sum(
                        event["source_kind"] == "local" for event in route_events
                    )
                    / max(1, local_events_by_date[_iso(when)]),
                    "resident_to_visitor": direction_counts["resident_to_visitor"],
                    "visitor_to_resident": direction_counts["visitor_to_resident"],
                    "visitor_to_visitor": direction_counts["visitor_to_visitor"],
                    "resident_to_resident": direction_counts["resident_to_resident"],
                    "effective_multiplier": travel_config.visitor_route_multipliers[route_id],
                }
            )
    travel_events = [
        event
        for event in events
        if event["route_id"] in TRAVEL_ROUTE_IDS
        or event.get("travel_linked")
        or event["source_kind"] == "travel_imported"
    ]
    visitor_events = list(manager.event_log)
    m7_events = [] if m7_manager is None else list(m7_manager.event_log)
    m7_state = [] if m7_manager is None else list(m7_manager.daily_state)
    m7_route_effects = [] if m7_manager is None else list(m7_manager.route_effects)
    m7_diagnostics = {} if m7_manager is None else m7_manager.diagnostics()
    seasonality = manager.seasonality_rows()
    temporary_edges = manager.temporary_edge_rows()
    temporary_network_hash = sha256_bytes(canonical_json_bytes(temporary_edges))
    high_risk = manager.high_risk_rows()
    high_risk_epidemic = _high_risk_epidemic_rows(
        manager, high_risk, events, config.start_date, config.duration_days
    )
    canonical_daily_parish: list[dict[str, Any]] = []
    canonical_daily_route: list[dict[str, Any]] = []
    canonical_daily_age: list[dict[str, Any]] = []
    canonical_zero_latent_hash: str | None = None
    if not plan.episodes:
        # An explicit empty travel manager is a mathematical no-op. Reuse the
        # canonical C5 projection and identity verbatim; empty temporary tables
        # remain separate M8 artifacts and cannot perturb the C5 latent hash.
        from .outbreak_runner import run_outbreak

        canonical_scenario = (
            scenario.model_copy(update={"travel": None}) if scenario is not None else None
        )
        canonical_config = (
            config
            if generic_enabled
            else config.model_copy(update={"import_schedule": {}, "import_rate_per_day": 0.0})
        )
        canonical = run_outbreak(
            generated,
            canonical_config,
            parameters,
            observation_config=observation_config,
            scenario=canonical_scenario,
        )
        daily_epidemic = canonical.daily_epidemic
        events = canonical.transmission_events
        canonical_daily_parish = canonical.daily_parish
        canonical_daily_route = canonical.daily_route
        canonical_daily_age = canonical.daily_age
        canonical_zero_latent_hash = canonical.latent_outcome_hash
    scenario_payload = {
        "scenario": scenario.model_dump(mode="json") if scenario is not None else None,
        "m4_parent_hash": generated.logical_content_hash,
        "m2_hash": generated.m2_input.manifest.logical_content_hash,
        "m3_hash": generated.m3_input.manifest.logical_content_hash,
        "run_config": config.model_dump(mode="json"),
        "travel_config_hash": travel_config.config_hash,
        "visitor_episode_hash": plan.episode_hash,
        "temporary_network_hash": temporary_network_hash,
        "seasonality_hash": travel_config.seasonality_hash,
        "starsim_version": "3.5.2",
        "scenario_config": scenario.model_dump(mode="json") if scenario is not None else None,
        "m7_scenario_hash": scenario.config_hash if scenario is not None else None,
        "observation_config_hash": (
            sha256_bytes(canonical_json_bytes(observation_config.model_dump(mode="json")))
            if observation_config is not None
            else None
        ),
    }
    resolved_scenario_hash = sha256_bytes(canonical_json_bytes(scenario_payload))
    latent_payload = {
        "daily_epidemic": daily_epidemic,
        "transmission_events": events,
        "daily_travel_population": list(plan.daily_stream),
        "daily_travel_route": daily_route,
        "travel_intervention_events": visitor_events + m7_events,
        "seasonality_schedule": seasonality,
    }
    latent_hash = canonical_zero_latent_hash or sha256_bytes(
        canonical_json_bytes(_without_null_fields(latent_payload))
    )
    artifact_hash = sha256_bytes(
        canonical_json_bytes(
            {
                "scenario_hash": resolved_scenario_hash,
                "latent_hash": latent_hash,
                "episode_hash": plan.episode_hash,
            }
        )
    )
    peak_memory = max(before_memory, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    visitor_slot_uids = [manager.uid_by_id[slot] for slot in manager.visitor_slot_ids]
    inactive_slot_uids = [
        uid for uid in visitor_slot_uids if uid not in manager._active_episode_by_uid
    ]
    inactive_slot_audit = {
        "count": len(inactive_slot_uids),
        "alive_false": all(not bool(sim.people.alive[uid]) for uid in inactive_slot_uids),
        "disease_states_false": all(
            not any(
                bool(state.raw[uid])
                for state in (
                    disease.susceptible,
                    disease.exposed,
                    disease.infected,
                    disease.recovered,
                )
            )
            for uid in inactive_slot_uids
        ),
        "timers_nan": all(
            all(
                bool(np.isnan(timer.raw[uid]))
                for timer in (
                    disease.ti_exposed,
                    disease.ti_infected,
                    disease.ti_recovered,
                    disease.ti_susceptible,
                )
            )
            for uid in inactive_slot_uids
        ),
        "modifiers_neutral": all(
            disease.rel_sus.raw[uid] == 1.0 and disease.rel_trans.raw[uid] == 1.0
            for uid in inactive_slot_uids
        ),
        "excluded_from_auids": all(
            uid not in {int(item) for item in sim.people.auids} for uid in inactive_slot_uids
        ),
    }
    diagnostics = {
        "status": "passed",
        "framework_version": TRAVEL_GENERATOR_VERSION,
        "temporary_agent_strategy": (
            "preallocated Starsim visitor slots; active UID and alive-state lifecycle"
        ),
        "temporary_agent_rationale": (
            "Starsim 3.5.2 People.grow is append-only; preallocation avoids unsafe "
            "mid-run array growth and keeps visitor IDs episode-scoped."
        ),
        "parent_hashes": {
            "m2": generated.m2_input.manifest.logical_content_hash,
            "m3": generated.m3_input.manifest.logical_content_hash,
            "m4": generated.logical_content_hash,
        },
        "hashes": {
            "travel_config": travel_config.config_hash,
            "visitor_episode": plan.episode_hash,
            "visitor_population": plan.visitor_hash,
            "temporary_network": temporary_network_hash,
            "seasonality": travel_config.seasonality_hash,
            "scenario": resolved_scenario_hash,
            "latent_outcome": latent_hash,
            "artifact_bundle": artifact_hash,
        },
        "identity": {
            "resident_count": len(generated.agent_ids),
            "visitor_count": len(plan.visitor_records),
            "visitor_capacity": plan.visitor_capacity,
            "temporary_slot_ids": manager.visitor_slot_ids,
            "resident_ids_unchanged": generated.agent_ids == sorted(generated.agent_ids),
            "visitor_namespace": "visitor-<seed>-<counter>",
            "slot_reuse_count": len(plan.visitor_records)
            - len({slot for _visitor, slot in plan.visitor_slot_indices}),
            "event_time_identity_rows": len(manager._identity_by_uid_ti),
            "final_uid_to_visitor_mapping_forbidden": True,
            "inactive_slot_audit": inactive_slot_audit,
        },
        "streams": {
            "generic_imports_enabled": generic_enabled,
            "explicit_travel_enabled": travel_config.mode in {"explicit_travel", "both"},
            "double_counting_contract": (
                "generic imports and explicit travel are separate; both is explicit"
            ),
            "annual_air_arrivals_source_id": "passenger_arrivals_total_csv",
            "annual_ferry_arrivals_source_id": "passenger_arrivals_total_csv",
            "annual_values_are_passenger_arrivals": True,
        },
        "denominators": {
            "resident_attack_rate_denominator": len(generated.agent_ids),
            "visitor_attack_rate_denominator": len(plan.visitor_records),
            "present_population_is_date_specific": True,
            "inactive_slots_excluded": True,
        },
        "interventions": {
            "events": len(visitor_events) + len(m7_events),
            "prospective": True,
            "neutral_adherence_zero": travel_config.interventions.quarantine_adherence == 0,
            "config_hash": travel_config.intervention_hash,
            "m7_composed": m7_manager is not None,
        },
        "seasonality": {
            "visitor_profile": travel_config.visitor_seasonality.model_dump(mode="json"),
            "transmission_enabled": travel_config.enable_transmission_seasonality,
            "applied_once": True,
            "schedule_persisted": True,
        },
        "high_risk": {
            "targeting_only": True,
            "severity_model_implemented": False,
            "config_hash": travel_config.high_risk.config_hash,
        },
        "observation_config": (
            observation_config.model_dump(mode="json") if observation_config is not None else None
        ),
        "observation_config_hash": scenario_payload["observation_config_hash"],
        "m7_scenario_hash": scenario_payload["m7_scenario_hash"],
        "scenario_config": scenario_payload["scenario_config"],
        "capacity": {
            "configured_capacity": plan.visitor_capacity,
            "maximum_active_observed": max(
                (row["active_visitors"] for row in plan.daily_stream), default=0
            ),
            "unused_headroom": plan.visitor_capacity
            - max((row["active_visitors"] for row in plan.daily_stream), default=0),
        },
        "movement_reconciliation": plan.reconciliation,
        "departure_reconciliation": plan.departure_reconciliation,
        "performance": {
            "runtime_seconds": time.perf_counter() - started,
            "peak_memory_bytes": peak_memory,
            "python_version": platform.python_version(),
            "temporary_edge_count": sum(row["active_edges"] for row in daily_route),
        },
        "source_parameter_provenance": travel_config.resolved_parameter_provenance(),
        "synthetic_claim_boundary": (
            "Synthetic travel scenario only; not a real prevalence, itinerary, "
            "terminal rate, policy or forecast claim."
        ),
    }
    return TravelRunResult(
        config=config,
        parameters=parameters,
        travel_config=travel_config,
        base_generated=generated,
        travel_plan=plan,
        daily_epidemic=daily_epidemic,
        daily_parish=canonical_daily_parish,
        daily_route=canonical_daily_route,
        daily_age=canonical_daily_age,
        transmission_events=events,
        daily_travel_population=list(plan.daily_stream),
        travel_episodes=[
            row.model_dump(mode="json") | {"episode_identity_hash": row.identity_hash}
            for row in plan.episodes
        ],
        visitor_events=visitor_events,
        daily_travel_route=daily_route,
        temporary_edges=temporary_edges,
        travel_transmission_events=travel_events,
        travel_intervention_events=visitor_events + m7_events,
        daily_travel_intervention_state=manager.intervention_state,
        seasonality_schedule=seasonality,
        high_risk_strata=high_risk,
        high_risk_epidemic=high_risk_epidemic,
        diagnostics=diagnostics,
        scenario_hash=resolved_scenario_hash,
        travel_config_hash=travel_config.config_hash,
        visitor_episode_hash=plan.episode_hash,
        temporary_network_hash=temporary_network_hash,
        seasonality_hash=travel_config.seasonality_hash,
        latent_outcome_hash=latent_hash,
        artifact_bundle_hash=artifact_hash,
        runtime_seconds=time.perf_counter() - started,
        peak_memory_bytes=peak_memory,
        m7_intervention_state=m7_state,
        m7_intervention_events=m7_events,
        m7_intervention_route_effects=m7_route_effects,
        m7_intervention_diagnostics=m7_diagnostics,
        observation_config=observation_config,
        scenario_config=scenario,
        observation_events=(
            list(observation_schedule.observation_events)
            if observation_schedule is not None
            else []
        ),
        detection_events=(
            observation_schedule.detection_events if observation_schedule is not None else ()
        ),
        delivered_detection_events=(
            observation_schedule.delivered_detection_events
            if observation_schedule is not None
            else ()
        ),
    )


def compare_travel_runs(
    baseline: TravelRunResult, treated: TravelRunResult, *, comparison_id: str
) -> dict[str, Any]:
    """Matched-seed comparison with explicit coupling caveat."""

    if baseline.config.seed != treated.config.seed:
        raise ValueError("travel comparisons require matched seeds")
    rows = []
    for left, right in zip(baseline.daily_epidemic, treated.daily_epidemic, strict=True):
        date_key = left["date"]
        left_stream = next(
            row for row in baseline.daily_travel_population if row["date"] == date_key
        )
        right_stream = next(
            row for row in treated.daily_travel_population if row["date"] == date_key
        )
        metric_values = {
            "resident_infections": (
                left.get("resident_infections", 0),
                right.get("resident_infections", 0),
            ),
            "visitor_infections": (
                left.get("visitor_infections", 0),
                right.get("visitor_infections", 0),
            ),
            "travel_imported_acquisitions": (
                left.get("returning_resident_travel_acquisitions", 0),
                right.get("returning_resident_travel_acquisitions", 0),
            ),
            "arrivals": (left_stream["arrivals"], right_stream["arrivals"]),
            "active_visitors": (left_stream["active_visitors"], right_stream["active_visitors"]),
            "quarantined_travellers": (
                sum(
                    event["date"] == date_key and event["action"] == "quarantine_activated"
                    for event in baseline.travel_intervention_events
                ),
                sum(
                    event["date"] == date_key and event["action"] == "quarantine_activated"
                    for event in treated.travel_intervention_events
                ),
            ),
            "positive_tests": (
                sum(
                    event["date"] == date_key
                    and event["action"] == "arrival_test_result"
                    and bool(event.get("detected"))
                    for event in baseline.travel_intervention_events
                ),
                sum(
                    event["date"] == date_key
                    and event["action"] == "arrival_test_result"
                    and bool(event.get("detected"))
                    for event in treated.travel_intervention_events
                ),
            ),
        }
        for direction in (
            "resident_to_resident",
            "resident_to_visitor",
            "visitor_to_resident",
            "visitor_to_visitor",
        ):
            metric_values[direction] = (
                sum(
                    event.get("transmission_direction") == direction and event["date"] == date_key
                    for event in baseline.transmission_events
                ),
                sum(
                    event.get("transmission_direction") == direction and event["date"] == date_key
                    for event in treated.transmission_events
                ),
            )
        for metric, (left_value, right_value) in metric_values.items():
            rows.append(
                {
                    "date": date_key,
                    "metric": metric,
                    "baseline": left_value,
                    "treated": right_value,
                    "absolute_difference": right_value - left_value,
                }
            )
    payload = {
        "comparison_id": comparison_id,
        "seed": baseline.config.seed,
        "status": "completed",
        "baseline_scenario_hash": baseline.scenario_hash,
        "intervention_scenario_hash": treated.scenario_hash,
        "baseline_latent_hash": baseline.latent_outcome_hash,
        "intervention_latent_hash": treated.latent_outcome_hash,
        "baseline_travel_config_hash": baseline.travel_config_hash,
        "intervention_travel_config_hash": treated.travel_config_hash,
        "parent_m4_hash_equal": baseline.base_generated.logical_content_hash
        == treated.base_generated.logical_content_hash,
        "visitor_generation_coupled": baseline.travel_plan.episode_hash
        == treated.travel_plan.episode_hash,
        "temporary_network_coupled": baseline.temporary_network_hash
        == treated.temporary_network_hash,
        "coupling_note": (
            "Arrival/episode coupling is exact only while travel-generation controls "
            "are identical; diverging interventions may decay common random numbers."
        ),
        "rows": rows,
    }
    return payload | {"logical_content_hash": sha256_bytes(canonical_json_bytes(payload))}


def run_travel_ensemble(
    generated: GeneratedNetworks,
    parameters: RespiratoryParameterSet,
    base_config: OutbreakRunConfig,
    travel_config: TravelConfig,
    seeds: tuple[int, ...],
    *,
    scenario: ScenarioConfig | None = None,
) -> dict[str, Any]:
    """Small sequential M8 ensemble retaining per-seed hashes and summaries."""

    if not seeds:
        raise ValueError("travel ensemble requires at least one seed")
    runs: list[TravelRunResult] = []
    failures: list[dict[str, Any]] = []
    for seed in seeds:
        run_config = base_config.model_copy(update={"seed": seed})
        run_scenario = (
            scenario.model_copy(update={"seed": seed})
            if scenario is not None and scenario.seed is not None
            else scenario
        )
        try:
            runs.append(
                run_travel_outbreak(
                    generated, run_config, parameters, travel_config, scenario=run_scenario
                )
            )
        except Exception as exc:  # failed replicates are visible and excluded
            failures.append({"seed": seed, "status": "failed", "error": str(exc)})
    if not runs:
        raise ValueError(f"all travel ensemble replicates failed: {failures}")
    summary = []
    for index in range(base_config.duration_days):
        values = [run.daily_epidemic[index] for run in runs]
        streams = [run.daily_travel_population[index] for run in runs]
        date_key = values[0]["date"]
        metrics = {
            "resident_infections": [
                float(row.get("resident_infections", row.get("new_infections", 0)))
                for row in values
            ],
            "visitor_infections": [float(row.get("visitor_infections", 0)) for row in values],
            "active_visitors": [float(row["active_visitors"]) for row in streams],
            "present_population": [float(row["present_population"]) for row in streams],
            "arrivals": [float(row["arrivals"]) for row in streams],
            "departures": [float(row["departures"]) for row in streams],
            "returning_resident_travel_acquisitions": [
                float(row.get("returning_resident_travel_acquisitions", 0)) for row in values
            ],
            "visitor_linked_local_acquisitions": [
                float(row.get("visitor_linked_local_acquisitions", 0)) for row in values
            ],
            "travel_intervention_burden": [
                float(
                    sum(
                        event["date"] == date_key
                        and event["action"]
                        in {
                            "arrival_test_administered",
                            "arrival_test_result",
                            "quarantine_scheduled",
                            "quarantine_activated",
                            "quarantine_released",
                            "traveller_vaccine_administered",
                        }
                        for event in run.travel_intervention_events
                    )
                )
                for run in runs
            ],
        }
        for direction in (
            "resident_to_resident",
            "resident_to_visitor",
            "visitor_to_resident",
            "visitor_to_visitor",
        ):
            metrics[direction] = [
                float(
                    sum(
                        event["date"] == date_key
                        and event.get("transmission_direction") == direction
                        for event in run.transmission_events
                    )
                )
                for run in runs
            ]
        for metric, metric_values in metrics.items():
            summary.append(
                {
                    "date": date_key,
                    "metric": metric,
                    "median": float(np.median(metric_values)),
                    "minimum": min(metric_values),
                    "maximum": max(metric_values),
                    "replicate_count": len(metric_values),
                    "semantic": (
                        "state"
                        if metric == "active_visitors"
                        else "population_denominator"
                        if metric == "present_population"
                        else "incidence_event"
                    ),
                    "outside_horizon_behavior": "excluded",
                    "missing_behavior": (
                        "carry_forward" if metric == "active_visitors" else "structural_zero"
                    ),
                }
            )
    payload = {
        "seeds": list(seeds),
        "scenario_hashes": [run.scenario_hash for run in runs],
        "latent_hashes": [run.latent_outcome_hash for run in runs],
        "failures": failures,
        "summary": summary,
    }
    return {
        "summary": summary,
        "replicates": [
            {
                "seed": run.config.seed,
                "scenario_hash": run.scenario_hash,
                "latent_outcome_hash": run.latent_outcome_hash,
                "travel_config_hash": run.travel_config_hash,
                "visitor_episode_hash": run.visitor_episode_hash,
            }
            for run in runs
        ]
        + failures,
        "logical_content_hash": sha256_bytes(canonical_json_bytes(payload)),
        "diagnostics": {
            "status": "passed",
            "metric_semantics_preserved": True,
            "matched_seed_pairing": True,
            "failed_replicates_excluded": True,
            "failure_count": len(failures),
            "synthetic_claim_boundary": (
                "Bounded uncertainty demonstration; not a Jersey prediction."
            ),
        },
    }


def run_travel_sensitivity(
    generated: GeneratedNetworks,
    parameters: RespiratoryParameterSet,
    run_config: OutbreakRunConfig,
    base_travel_config: TravelConfig,
    sensitivity: dict[str, Any],
) -> dict[str, Any]:
    """Execute named low/baseline/high M8 variants in a valid schema domain."""

    sensitivity_id = str(sensitivity["sensitivity_id"])
    axis = str(sensitivity["axis"])
    if axis not in {
        "visitor_community_contacts",
        "terminal_mixing_contacts",
        "arrival_infectious_fraction",
    }:
        raise ValueError(f"unsupported M8 sensitivity axis: {axis}")
    variants: list[dict[str, Any]] = []
    for variant in sensitivity["variants"]:
        value = variant[axis]
        travel = base_travel_config.model_copy(update={axis: value})
        result = run_travel_outbreak(generated, run_config, parameters, travel)
        variants.append(
            {
                "sensitivity_id": variant["sensitivity_id"],
                "axis": axis,
                "value": value,
                "config": travel.model_dump(mode="json"),
                "parent_hashes": result.diagnostics["parent_hashes"],
                "scenario_hash": result.scenario_hash,
                "travel_config_hash": result.travel_config_hash,
                "visitor_episode_hash": result.visitor_episode_hash,
                "temporary_network_hash": result.temporary_network_hash,
                "latent_outcome_hash": result.latent_outcome_hash,
                "outcome_summary": {
                    "resident_infections": sum(
                        row.get("resident_infections", 0) for row in result.daily_epidemic
                    ),
                    "visitor_infections": sum(
                        row.get("visitor_infections", 0) for row in result.daily_epidemic
                    ),
                    "temporary_edges": len(result.temporary_edges),
                },
            }
        )
    payload = {"sensitivity_id": sensitivity_id, "axis": axis, "variants": variants}
    return payload | {"logical_content_hash": sha256_bytes(canonical_json_bytes(payload))}


def provenance_table(config: TravelConfig) -> list[dict[str, Any]]:
    """Compact audit table for the major M8 quantities."""

    return [
        {
            "parameter": "annual_air_arrivals",
            "value_or_distribution": config.annual_air_arrivals,
            "units": "passenger arrivals/year",
            "provenance_status": "observed",
            "source_id": "passenger_arrivals_total_csv",
            "derivation": "Ports of Jersey 2025 total passenger-arrival movements.",
            "sensitivity_required": True,
        },
        {
            "parameter": "annual_ferry_arrivals",
            "value_or_distribution": config.annual_ferry_arrivals,
            "units": "passenger arrivals/year",
            "provenance_status": "observed",
            "source_id": "passenger_arrivals_total_csv",
            "derivation": "Ports of Jersey 2025 total passenger-arrival movements.",
            "sensitivity_required": True,
        },
        {
            "parameter": "daily_stream",
            "value_or_distribution": "annual / 365 × stream_scale × seasonal multiplier",
            "units": "synthetic passenger episodes/day",
            "provenance_status": "derived",
            "source_id": "passenger_arrivals_total_csv",
            "derivation": (
                "Transparent annual-to-daily derivation with deterministic cumulative rounding."
            ),
            "sensitivity_required": True,
        },
        {
            "parameter": "visitor_composition_and_stay",
            "value_or_distribution": {
                "visitor_fraction": config.visitor_fraction,
                "returning_resident_fraction": config.returning_resident_fraction,
                "stay_duration_days": config.stay_duration_days,
            },
            "units": "fractions and days",
            "provenance_status": "scenario_assumption",
            "source_id": None,
            "derivation": "No canonical unique-visitor/average-stay table is frozen in M1.",
            "sensitivity_required": True,
        },
        {
            "parameter": "visitor_seasonality",
            "value_or_distribution": list(config.visitor_seasonality.monthly_multipliers),
            "units": "normalized monthly multiplier",
            "provenance_status": config.visitor_seasonality.status,
            "source_id": ",".join(config.visitor_seasonality.source_ids) or None,
            "derivation": (
                "Declared monthly profile; neutral by default because no official "
                "monthly visitor snapshot is frozen."
            ),
            "sensitivity_required": True,
        },
        {
            "parameter": "visitor_contact_intensity",
            "value_or_distribution": {
                "terminal": config.terminal_mixing_contacts,
                "transit": config.visitor_transit_contacts,
                "community": config.visitor_community_contacts,
            },
            "units": "bounded synthetic contacts/participant/day",
            "provenance_status": "scenario_assumption",
            "source_id": None,
            "derivation": "Sparse route construction; no manifests or venue histories are used.",
            "sensitivity_required": True,
        },
        *[
            {
                "parameter": name,
                "value_or_distribution": value,
                "units": "relative contact-opportunity weight",
                "provenance_status": "scenario_assumption",
                "source_id": None,
                "derivation": (
                    "V1 numeric value promoted unchanged from the temporary-route constructor; "
                    "not an observed contact rate or measured transmission coefficient."
                ),
                "sensitivity_required": True,
            }
            for name, value in (
                ("arrival_terminal_edge_weight", config.arrival_terminal_edge_weight),
                ("visitor_party_edge_weight", config.visitor_party_edge_weight),
                (
                    "visitor_accommodation_edge_weight",
                    config.visitor_accommodation_edge_weight,
                ),
                (
                    "visitor_host_household_edge_weight",
                    config.visitor_host_household_edge_weight,
                ),
                ("visitor_transit_bus_edge_weight", config.visitor_transit_bus_edge_weight),
                (
                    "visitor_transit_vehicle_edge_weight",
                    config.visitor_transit_vehicle_edge_weight,
                ),
                (
                    "visitor_community_indoor_edge_weight",
                    config.visitor_community_indoor_edge_weight,
                ),
                (
                    "visitor_community_outdoor_edge_weight",
                    config.visitor_community_outdoor_edge_weight,
                ),
            )
        ],
        *[
            {
                "parameter": name,
                "value_or_distribution": value,
                "units": units,
                "provenance_status": "scenario_assumption",
                "source_id": None,
                "derivation": "Synthetic configurable M8.1 structural assumption; not observed.",
                "sensitivity_required": True,
            }
            for name, value, units in (
                ("stream_scale", config.stream_scale, "computational sample fraction"),
                (
                    "visitor_returning_split",
                    {
                        "visitor": config.visitor_fraction,
                        "returning_resident": config.returning_resident_fraction,
                    },
                    "person-movement fractions",
                ),
                (
                    "party_distribution",
                    dict(zip(config.party_sizes, config.party_probabilities, strict=True)),
                    "party-size probability",
                ),
                (
                    "stay_duration",
                    {
                        "central_days": config.stay_duration_days,
                        "jitter_days": config.stay_duration_jitter_days,
                    },
                    "days",
                ),
                (
                    "accommodation_mix",
                    {
                        "day_visitor_fraction": config.day_visitor_fraction,
                        "staying_with_resident_fraction": config.staying_with_resident_fraction,
                    },
                    "fractions",
                ),
                (
                    "transport_mix",
                    config.local_transport_probabilities,
                    "categorical probabilities",
                ),
                ("terminal_contacts", config.terminal_mixing_contacts, "contacts/day"),
                (
                    "arrival_disease_prevalence",
                    {
                        "infectious": config.arrival_infectious_fraction,
                        "exposed": config.arrival_exposed_fraction,
                        "recovered": config.arrival_recovered_fraction,
                    },
                    "arrival fractions",
                ),
                (
                    "travel_acquisition_pressure",
                    config.returning_resident_external_acquisition_probability,
                    "probability/return",
                ),
                (
                    "testing",
                    config.interventions.testing_probability,
                    "probability/arrival",
                ),
                (
                    "quarantine",
                    {
                        "all_arrivals": config.interventions.quarantine_all_arrivals,
                        "positive_only": config.interventions.quarantine_positive_only,
                        "duration_days": config.interventions.quarantine_duration_days,
                    },
                    "policy scenario controls",
                ),
                (
                    "traveller_vaccination",
                    {
                        "coverage": config.interventions.traveller_vaccination_coverage,
                        "susceptibility_efficacy": (
                            config.interventions.traveller_vaccination_efficacy
                        ),
                        "infectiousness_efficacy": (
                            config.interventions.traveller_vaccination_infectiousness_efficacy
                        ),
                    },
                    "fractions",
                ),
            )
        ],
    ]
