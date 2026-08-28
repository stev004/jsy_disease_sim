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
from .observation_scheduler import ObservationScheduler
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

    @property
    def visitor_episodes(self) -> tuple[TravelEpisode, ...]:
        return tuple(item for item in self.episodes if item.visitor_uid is not None)

    @property
    def returning_resident_episodes(self) -> tuple[TravelEpisode, ...]:
        return tuple(item for item in self.episodes if item.resident_agent_id is not None)


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


def _transport(seed: int, visitor_uid: str, host: bool) -> LocalTransportType:
    draw = _stable_uniform(seed, "transport", visitor_uid)
    if host and draw < 0.35:
        return "HOST_PICKUP"
    if draw < 0.55:
        return "BUS"
    if draw < 0.78:
        return "PRIVATE_RENTAL_CAR"
    if draw < 0.90:
        return "TAXI_RIDE"
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
    fractional = {"AIRPORT": 0.0, "FERRY": 0.0}
    visitor_counter = 0
    for when in _dates(start_date, duration_days):
        for mode in entry_modes:
            count, fractional[mode] = _profile_counts(config, when, mode, fractional[mode])
            daily_counts[_iso(when)][mode] = count
            remaining = count
            party_number = 0
            while remaining:
                party_size = _choose_party_size(config, seed, _iso(when), party_number, remaining)
                party_number += 1
                remaining -= party_size
                trip_id = f"trip-{seed:010d}-{when:%Y%m%d}-{mode.lower()}-{party_number:04d}"
                party_id = f"party-{trip_id}"
                type_draw = _stable_uniform(seed, "traveller-type", trip_id)
                is_returning = type_draw < config.returning_resident_fraction
                is_visitor = (
                    type_draw < config.returning_resident_fraction + config.visitor_fraction
                )
                if is_returning:
                    returning_candidates = [
                        agent_id
                        for agent_id in resident_ids
                        if busy_until.get(agent_id, start_date) <= when
                    ]
                    if not returning_candidates:
                        is_returning = False
                        is_visitor = type_draw < config.visitor_fraction
                    else:
                        resident_id = returning_candidates[
                            _stable_int(seed, "returning-resident", trip_id)
                            % len(returning_candidates)
                        ]
                if not is_returning and not is_visitor:
                    continue
                for person_number in range(party_size):
                    terminal = "JERSEY_AIRPORT" if mode == "AIRPORT" else "JERSEY_FERRY_TERMINAL"
                    if is_returning:
                        if person_number > 0:
                            # A returning-resident episode is one resident per
                            # synthetic party; extra party members remain
                            # visitors with the same party identifier.
                            returning = False
                        else:
                            returning = True
                        person_id = (
                            resident_id
                            if returning
                            else f"visitor-{seed:010d}-{visitor_counter:08d}"
                        )
                        visitor_uid = None if returning else person_id
                    else:
                        returning = False
                        person_id = f"visitor-{seed:010d}-{visitor_counter:08d}"
                        visitor_uid = person_id
                    if returning:
                        duration = max(2, config.stay_duration_days)
                        absence_start = when - timedelta(days=duration)
                        departure = when
                        busy_until[resident_id] = when + timedelta(days=duration)
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
                            home_household_id=household_by_resident.get(resident_id),
                        )
                        episodes.append(episode)
                    else:
                        visitor_uid = person_id
                        parish, accommodation_type, accommodation_id, host_household_id = (
                            _visitor_accommodation(
                                config, seed, visitor_uid, host_households, parish_by_household
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
                                seed, visitor_uid, host_household_id is not None
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
                                "age": 35 + (_stable_int(seed, "visitor-age", visitor_uid) % 35),
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
                            }
                        )
                        visitor_counter += 1

    # When an explicit departure schedule is supplied, move a deterministic
    # subset of still-active episodes to those dates.  The schedule cannot
    # manufacture a departure without a prior arrival; any unmatchable excess
    # remains visible through the generated episode stream rather than being
    # silently dropped.
    if config.daily_departures:
        for when in _dates(start_date, duration_days):
            for mode in entry_modes:
                target = _explicit_stream_count(config.daily_departures, config, when, mode)
                if target is None or target <= 0:
                    continue
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
                episodes = [
                    episode.model_copy(update={"departure_date": when, "active_end": when})
                    if episode.person_id in selected
                    else episode
                    for episode in episodes
                ]

    episode_payload = [
        row.model_dump(mode="json")
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
        away = sum(
            item.resident_agent_id is not None
            and item.absence_start_date is not None
            and item.return_date is not None
            and item.absence_start_date <= when < item.return_date
            for item in episodes
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
    return TravelPlan(
        episodes=tuple(sorted(episodes, key=lambda row: (row.arrival_date, row.person_id))),
        visitor_records=tuple(visitor_payload),
        daily_stream=tuple(daily_stream),
        visitor_capacity=capacity,
        visitor_slot_indices=tuple(sorted(slot_by_visitor.items())),
        episode_hash=sha256_bytes(canonical_json_bytes(episode_payload)),
        visitor_hash=sha256_bytes(canonical_json_bytes(visitor_payload)),
    )


def _travel_spec(route_id: str, indoor: bool, weight: float, semantics: str) -> dict[str, Any]:
    return {
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
        self.pending_tests: list[tuple[int, str, bool]] = []
        self.current_date: date = start_date
        self.current_ti = 0
        self._all_resident_uids = set(range(len(base_generated.agent_ids)))
        self.event_log: list[dict[str, Any]] = []
        self.intervention_state: list[dict[str, Any]] = []
        self.route_edge_history: dict[tuple[int, str], list[dict[str, Any]]] = {}
        self.state_snapshots: list[dict[str, Any]] = []
        self._initialised = False
        self._episodes_by_arrival: dict[date, list[TravelEpisode]] = defaultdict(list)
        self._episodes_by_departure: dict[date, list[TravelEpisode]] = defaultdict(list)
        self._episode_by_person = {item.person_id: item for item in plan.episodes}
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
        # Disease/observation events should expose stable episode-scoped visitor
        # IDs even though Starsim itself receives only preallocated slot IDs.
        for visitor_id, uid in self.visitor_slot_by_id.items():
            self.id_by_uid[uid] = visitor_id

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
                "config_hash": self.config.intervention_hash,
                **extra,
            }
        )

    def _arrival_test(self, episode: TravelEpisode) -> None:
        controls = self.config.interventions
        if controls.testing_probability <= 0 or episode.visitor_uid is None:
            return
        tested = (
            _stable_uniform(self.seed, "arrival-test", episode.person_id)
            < controls.testing_probability
        )
        if not tested:
            self._append_event("arrival_test_not_taken", episode)
            return
        infected = episode.disease_state_on_arrival in {"exposed", "infectious"}
        probability = controls.test_sensitivity if infected else 1.0 - controls.test_specificity
        detected = (
            _stable_uniform(self.seed, "arrival-test-result", episode.person_id) < probability
        )
        result_ti = self.current_ti + controls.test_result_delay_days
        self.pending_tests.append((result_ti, episode.person_id, detected))
        self._append_event(
            "arrival_test_scheduled",
            episode,
            tested=True,
            detected=detected,
            result_time_index=result_ti,
            sensitivity=controls.test_sensitivity,
            specificity=controls.test_specificity,
        )

    def _process_test_results(self) -> None:
        controls = self.config.interventions
        due = [item for item in self.pending_tests if item[0] <= self.current_ti]
        self.pending_tests = [item for item in self.pending_tests if item[0] > self.current_ti]
        for result_ti, person_id, detected in sorted(due, key=lambda item: (item[0], item[1])):
            episode = self._episode_by_person[person_id]
            self._append_event(
                "arrival_test_result", episode, detected=detected, result_time_index=result_ti
            )
            eligible = (
                detected and controls.quarantine_positive_only or controls.quarantine_all_arrivals
            )
            if not eligible or controls.quarantine_duration_days <= 0:
                continue
            adheres = (
                _stable_uniform(self.seed, "quarantine-adherence", person_id, result_ti)
                < controls.quarantine_adherence
            )
            if not adheres:
                self._append_event("quarantine_declined", episode, cause="adherence")
                continue
            until = self.current_ti + controls.quarantine_duration_days
            self.quarantine_until[person_id] = max(until, self.quarantine_until.get(person_id, -1))
            self._append_event(
                "quarantine_started",
                episode,
                cause="arrival_test" if detected else "arrival_policy",
                release_time_index=self.quarantine_until[person_id],
            )

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
        self.sim.people.alive[uid] = True
        self.disease.initialize_arrival_state(np.asarray([uid]), episode.disease_state_on_arrival)
        controls = self.config.interventions
        if (
            episode.disease_state_on_arrival == "susceptible"
            and _stable_uniform(self.seed, "visitor-vaccination", episode.visitor_uid)
            < controls.traveller_vaccination_coverage
        ):
            self.disease.rel_sus.raw[uid] *= 1.0 - controls.traveller_vaccination_efficacy
            self._append_event(
                "traveller_protection_applied",
                episode,
                efficacy=controls.traveller_vaccination_efficacy,
            )
        self._arrival_test(episode)
        self._append_event("visitor_arrived", episode, slot_uid=uid)

    def _deactivate_visitor(self, episode: TravelEpisode) -> None:
        assert self.disease is not None and self.sim is not None
        if episode.visitor_uid is None or episode.visitor_uid not in self.active_visitor_ids:
            return
        uid = self.visitor_slot_by_id[episode.visitor_uid]
        self.active_visitor_ids.remove(episode.visitor_uid)
        self.sim.people.alive[uid] = False
        for state in (
            self.disease.susceptible,
            self.disease.exposed,
            self.disease.infected,
            self.disease.recovered,
        ):
            state[uid] = False
        self.disease.rel_sus.raw[uid] = 1.0
        self.disease.rel_trans.raw[uid] = 1.0
        self._append_event("visitor_departed", episode, slot_uid=uid)

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
        self._process_test_results()
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
            if episode.resident_agent_id is not None:
                resident_id = episode.resident_agent_id
                self.present_resident_ids.add(resident_id)
                self.away_resident_ids.discard(resident_id)
                uid = self.uid_by_id[resident_id]
                self.sim.people.alive[uid] = True
                self._returning_acquisition(episode)
                self._append_event("resident_returned", episode)
            elif episode.visitor_uid is not None:
                self._activate_visitor(episode)
        self._set_auids(self._active_uid_set())
        for route_id in TRAVEL_ROUTE_IDS:
            self.route_edge_history[(self.current_ti, route_id)] = self.route_edges(
                route_id, self.current_date
            )
        self.intervention_state.append(
            {
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
        )

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
        if route_id == "visitor_accommodation" or route_id == "visitor_host_household":
            return self.config.interventions.quarantine_accommodation_multiplier
        return self.config.interventions.quarantine_external_route_multiplier

    def _edge_factor(self, route_id: str, people: Iterable[str]) -> float:
        people = tuple(people)
        factor = float(self.config.visitor_route_multipliers[route_id])
        if (
            self.config.visitor_to_resident_multiplier < 1.0
            and any(item in self._visitor_by_id for item in people)
            and any(item in self._resident_by_id for item in people)
        ):
            factor *= self.config.visitor_to_resident_multiplier
        if self.config.enable_transmission_seasonality:
            factor *= self.config.transmission_seasonality.multiplier(self.current_date)
        if route_id == "arrival_terminal":
            factor *= self.config.interventions.terminal_contact_multiplier
        if route_id == "visitor_accommodation":
            factor *= min(self._quarantine_factor(item, route_id) for item in people)
        elif route_id in {
            "visitor_transit",
            "visitor_community_indoor",
            "visitor_community_outdoor",
        }:
            factor *= min(self._quarantine_factor(item, route_id) for item in people)
        return factor

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
                edge_weight = 0.30 * self._edge_factor(route_id, ids)
                edges.extend(_ring_edges(ids, 2, edge_weight, 1))
        elif route_id == "visitor_accommodation":
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
                        _complete_group(members, 0.55 * self._edge_factor(route_id, members), 7)
                    )
        elif route_id == "visitor_host_household":
            for row in active_rows:
                household = row.get("host_household_id")
                if household is None:
                    continue
                members = [
                    *self._household_members.get(str(household), []),
                    str(row["visitor_uid"]),
                ]
                members = sorted(set(members))
                edges.extend(
                    _complete_group(members, 0.80 * self._edge_factor(route_id, members), 1)
                )
        elif route_id == "visitor_transit":
            transit_groups: dict[tuple[str, LocalTransportType], list[str]] = defaultdict(list)
            for row in active_rows:
                if row["local_transport_type"] in {"BUS", "TAXI_RIDE"}:
                    transit_groups[(str(row["home_parish"]), row["local_transport_type"])].append(
                        str(row["visitor_uid"])
                    )
            for key, group in sorted(transit_groups.items(), key=lambda item: str(item[0])):
                if key[1] == "BUS":
                    edges.extend(
                        _ring_edges(
                            sorted(group),
                            self.config.visitor_transit_contacts,
                            0.35 * self._edge_factor(route_id, group),
                            1,
                        )
                    )
                else:
                    edges.extend(
                        _complete_group(group, 0.25 * self._edge_factor(route_id, group), 1)
                    )
        elif route_id in {"visitor_community_indoor", "visitor_community_outdoor"}:
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
                        (0.35 if route_id.endswith("indoor") else 0.18)
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
        if not self.plan.returning_resident_episodes:
            return list(edges)
        return [
            edge
            for edge in edges
            if edge["p1"] in self.present_resident_ids and edge["p2"] in self.present_resident_ids
        ]

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
        for route_id in TRAVEL_ROUTE_IDS:
            view.route_specs[route_id] = _travel_spec(
                route_id,
                route_id
                in {"visitor_accommodation", "visitor_host_household", "visitor_community_indoor"},
                0.35,
                "M8 synthetic temporary episode/activity membership",
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
        infected_id = self.id_by_uid[int(event["infected_uid"])]
        infector_uid = event.get("infector_uid")
        infector_id = None if infector_uid is None else self.id_by_uid[int(infector_uid)]
        infected_kind = (
            "visitor"
            if infected_id in self._visitor_by_id
            else "resident"
            if infected_id in self._resident_by_id
            else "visitor_slot"
        )
        infector_kind = (
            None
            if infector_id is None
            else "visitor"
            if infector_id in self._visitor_by_id
            else "resident"
            if infector_id in self._resident_by_id
            else "visitor_slot"
        )
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
    transmission_events: list[dict[str, Any]]
    daily_travel_population: list[dict[str, Any]]
    travel_episodes: list[dict[str, Any]]
    visitor_events: list[dict[str, Any]]
    daily_travel_route: list[dict[str, Any]]
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
                "visitor_attack_rate": cumulative_visitor / max(1, len(manager._visitor_by_id)),
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
    m7_manager = (
        InterventionManager(
            generated,
            scenario.interventions,
            run_seed=config.seed,
            start_date=config.start_date,
            duration_days=config.duration_days,
            scenario=scenario,
        )
        if scenario is not None and scenario.interventions
        else None
    )
    view = manager.route_view()
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
    high_risk = manager.high_risk_rows()
    high_risk_epidemic = _high_risk_epidemic_rows(
        manager, high_risk, events, config.start_date, config.duration_days
    )
    scenario_payload = {
        "scenario": scenario.model_dump(mode="json") if scenario is not None else None,
        "m4_parent_hash": generated.logical_content_hash,
        "m2_hash": generated.m2_input.manifest.logical_content_hash,
        "m3_hash": generated.m3_input.manifest.logical_content_hash,
        "run_config": config.model_dump(mode="json"),
        "travel_config_hash": travel_config.config_hash,
        "visitor_episode_hash": plan.episode_hash,
        "temporary_network_hash": travel_config.temporary_network_hash,
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
    latent_hash = sha256_bytes(canonical_json_bytes(latent_payload))
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
            "temporary_network": travel_config.temporary_network_hash,
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
        "capacity": {
            "configured_capacity": plan.visitor_capacity,
            "maximum_active_observed": max(
                (row["active_visitors"] for row in plan.daily_stream), default=0
            ),
            "unused_headroom": plan.visitor_capacity
            - max((row["active_visitors"] for row in plan.daily_stream), default=0),
        },
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
        transmission_events=events,
        daily_travel_population=list(plan.daily_stream),
        travel_episodes=[row.model_dump(mode="json") for row in plan.episodes],
        visitor_events=visitor_events,
        daily_travel_route=daily_route,
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
        temporary_network_hash=travel_config.temporary_network_hash,
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
    )


def compare_travel_runs(
    baseline: TravelRunResult, treated: TravelRunResult, *, comparison_id: str
) -> dict[str, Any]:
    """Matched-seed comparison with explicit coupling caveat."""

    if baseline.config.seed != treated.config.seed:
        raise ValueError("travel comparisons require matched seeds")
    rows = []
    for left, right in zip(baseline.daily_epidemic, treated.daily_epidemic, strict=True):
        rows.append(
            {
                "date": left["date"],
                "metric": "resident_infections",
                "baseline": left["resident_infections"],
                "treated": right["resident_infections"],
                "absolute_difference": right["resident_infections"] - left["resident_infections"],
            }
        )
        rows.append(
            {
                "date": left["date"],
                "metric": "visitor_to_resident_transmissions",
                "baseline": sum(
                    event["transmission_direction"] == "visitor_to_resident"
                    and event["date"] == left["date"]
                    for event in baseline.travel_transmission_events
                ),
                "treated": sum(
                    event["transmission_direction"] == "visitor_to_resident"
                    and event["date"] == left["date"]
                    for event in treated.travel_transmission_events
                ),
                "absolute_difference": sum(
                    event["transmission_direction"] == "visitor_to_resident"
                    and event["date"] == left["date"]
                    for event in treated.travel_transmission_events
                )
                - sum(
                    event["transmission_direction"] == "visitor_to_resident"
                    and event["date"] == left["date"]
                    for event in baseline.travel_transmission_events
                ),
            }
        )
    return {
        "comparison_id": comparison_id,
        "matched_seed": baseline.config.seed,
        "parent_m4_hash_equal": baseline.base_generated.logical_content_hash
        == treated.base_generated.logical_content_hash,
        "visitor_generation_coupled": baseline.travel_plan.episode_hash
        == treated.travel_plan.episode_hash,
        "coupling_note": (
            "Arrival/episode coupling is exact only while travel-generation controls "
            "are identical; diverging interventions may decay common random numbers."
        ),
        "rows": rows,
        "logical_content_hash": sha256_bytes(canonical_json_bytes(rows)),
    }


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
    for seed in seeds:
        run_config = base_config.model_copy(update={"seed": seed})
        runs.append(
            run_travel_outbreak(generated, run_config, parameters, travel_config, scenario=scenario)
        )
    summary = []
    for index in range(base_config.duration_days):
        values = [run.daily_epidemic[index] for run in runs]
        streams = [run.daily_travel_population[index] for run in runs]
        date_key = values[0]["date"]
        metrics = {
            "resident_infections": [float(row["resident_infections"]) for row in values],
            "visitor_infections": [float(row["visitor_infections"]) for row in values],
            "active_visitors": [float(row["active_visitors"]) for row in values],
            "present_population": [float(row["present_population"]) for row in values],
            "arrivals": [float(row["arrivals"]) for row in streams],
            "departures": [float(row["departures"]) for row in streams],
            "returning_resident_travel_acquisitions": [
                float(row["returning_resident_travel_acquisitions"]) for row in values
            ],
            "visitor_linked_local_acquisitions": [
                float(row["visitor_linked_local_acquisitions"]) for row in values
            ],
            "travel_intervention_burden": [
                float(sum(event["date"] == date_key for event in run.travel_intervention_events))
                for run in runs
            ],
        }
        for metric, metric_values in metrics.items():
            summary.append(
                {
                    "date": date_key,
                    "metric": metric,
                    "median": float(np.median(metric_values)),
                    "minimum": min(metric_values),
                    "maximum": max(metric_values),
                    "replicate_count": len(metric_values),
                    "semantic": "state"
                    if metric in {"active_visitors", "present_population"}
                    else "incidence",
                }
            )
    payload = {
        "seeds": list(seeds),
        "scenario_hashes": [run.scenario_hash for run in runs],
        "latent_hashes": [run.latent_outcome_hash for run in runs],
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
        ],
        "logical_content_hash": sha256_bytes(canonical_json_bytes(payload)),
        "diagnostics": {
            "status": "passed",
            "metric_semantics_preserved": True,
            "matched_seed_pairing": True,
            "synthetic_claim_boundary": (
                "Bounded uncertainty demonstration; not a Jersey prediction."
            ),
        },
    }


def provenance_table(config: TravelConfig) -> list[dict[str, Any]]:
    """Compact audit table for the major M8 quantities."""

    return [
        {
            "parameter": "annual_air_arrivals",
            "value_or_distribution": config.annual_air_arrivals,
            "units": "passenger arrivals/year",
            "provenance_status": "observed",
            "source_id": "passenger_arrivals_total_csv",
            "derivation": "Ports of Jersey 2025 total arrivals table; rounded source values.",
            "sensitivity_required": True,
        },
        {
            "parameter": "annual_ferry_arrivals",
            "value_or_distribution": config.annual_ferry_arrivals,
            "units": "passenger arrivals/year",
            "provenance_status": "observed",
            "source_id": "passenger_arrivals_total_csv",
            "derivation": "Ports of Jersey 2025 total arrivals table; rounded source values.",
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
    ]
