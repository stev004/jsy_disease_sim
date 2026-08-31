"""Simulation-time observation scheduling shared by online and offline M6 paths."""

from __future__ import annotations

import hashlib
import heapq
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from types import MappingProxyType
from typing import Any, Protocol

import numpy as np

from .hashing import canonical_json_bytes, sha256_bytes
from .observation_schemas import ObservationConfig


def _stable_seed(seed: int, *parts: object) -> int:
    digest = hashlib.sha256("|".join(str(part) for part in (seed, *parts)).encode()).digest()
    return int.from_bytes(digest[:8], byteorder="little", signed=False)


def _age_band(age: int) -> str:
    if age <= 4:
        return "0-4"
    if age <= 17:
        return "5-17"
    if age <= 64:
        return "18-64"
    return "65+"


def _probability(config: ObservationConfig, name: str) -> float:
    value = config.numeric(name)
    if not 0 <= value <= 1:
        raise ValueError(f"observation probability {name!r} must be in [0, 1]")
    return value


def _delay(rng: np.random.Generator, distribution: Any) -> int:
    if distribution.kind == "fixed":
        return int(distribution.days[0])
    probabilities = np.asarray(distribution.probabilities, dtype=float)
    return int(rng.choice(np.asarray(distribution.days, dtype=np.int64), p=probabilities))


def observation_stream_seed(latent_seed: int, config: ObservationConfig) -> int:
    """Derive the replicate/configuration-specific observation stream namespace."""

    return _stable_seed(
        latent_seed,
        config.observation_seed,
        config.observation_config_id,
        "observation",
    )


def event_stream_seed(stream_seed: int, event: Mapping[str, Any]) -> int:
    """Derive an insertion-order-independent stream for one infection event."""

    return _stable_seed(
        stream_seed,
        "infection-event",
        event.get("infected_uid", event.get("infected_agent_id")),
        event.get("infected_agent_id", ""),
        event["date"],
        event.get("source_kind", ""),
        event.get("route_id", ""),
        event.get("infector_uid", ""),
        event.get("infected_episode_identity_hash", ""),
        event.get("infector_episode_identity_hash", ""),
    )


@dataclass(frozen=True)
class DetectionEvent:
    """Read-only detection notification delivered during the Starsim lifecycle."""

    agent_uid: int
    agent_id: str
    detection_date: str
    detection_time_index: int
    detection_reason: str
    symptomatic: bool
    observation_config_id: str
    provenance: Mapping[str, Any]
    infected_agent_id: str | None = None
    infected_actor_type: str | None = None
    infected_runtime_uid: int | None = None
    infected_trip_id: str | None = None
    infected_travel_party_id: str | None = None
    infected_episode_identity_hash: str | None = None
    infector_agent_id: str | None = None
    infector_actor_type: str | None = None
    infector_runtime_uid: int | None = None
    infector_trip_id: str | None = None
    infector_travel_party_id: str | None = None
    infector_episode_identity_hash: str | None = None


class DetectionConsumer(Protocol):
    """Narrow future-M7 hook; C4 supplies only test probe consumers."""

    def consume_detection(self, event: DetectionEvent) -> None:
        """Consume one due notification without access to scheduler mutation APIs."""


@dataclass(frozen=True)
class ObservationScheduleSnapshot:
    """Immutable view of all sampled schedules and runtime deliveries."""

    observation_events: tuple[dict[str, Any], ...]
    detection_events: tuple[DetectionEvent, ...]
    delivered_detection_events: tuple[DetectionEvent, ...]
    pending_detection_count: int
    stream_fingerprint: str


class ObservationScheduler:
    """Sample infection observations immediately and causally deliver due detections.

    The scheduler is called by ``RespiratorySEIRS._record_events()`` as each
    infection is created. Starsim then invokes ``deliver_due()`` after that
    day's disease transmission. The consumer cannot affect transmission that
    has already happened; a future intervention may first affect the next
    timestep's contacts or agent intervention state.
    """

    def __init__(
        self,
        *,
        latent_seed: int,
        start_date: date,
        config: ObservationConfig,
        agent_id_by_uid: Mapping[int, str],
        resident_by_agent_id: Mapping[str, Mapping[str, Any]],
        consumer: DetectionConsumer | None = None,
    ) -> None:
        self.latent_seed = latent_seed
        self.start_date = start_date
        self.config = config
        self.agent_id_by_uid = dict(agent_id_by_uid)
        self.resident_by_agent_id = resident_by_agent_id
        self.consumer = consumer
        self.stream_seed = observation_stream_seed(latent_seed, config)
        self._observation_events: list[dict[str, Any]] = []
        self._detection_events: list[DetectionEvent] = []
        self._delivered: list[DetectionEvent] = []
        self._queue: list[tuple[int, str, int, str, str, DetectionEvent]] = []
        self._scheduled_keys: set[tuple[int, str, str, str]] = set()

    @property
    def stream_fingerprint(self) -> str:
        return hashlib.sha256(str(self.stream_seed).encode()).hexdigest()

    def schedule_infection(self, event: Mapping[str, Any]) -> dict[str, Any]:
        """Sample and queue one infection's complete observation schedule."""

        uid = int(event["infected_uid"])
        agent_id = str(event.get("infected_agent_id") or self.agent_id_by_uid[uid])
        episode_hash = str(event.get("infected_episode_identity_hash") or "")
        event_key = (uid, str(event["date"]), str(event.get("source_kind", "")), episode_hash)
        if event_key in self._scheduled_keys:
            raise ValueError(f"infection event was scheduled twice: {event_key}")
        self._scheduled_keys.add(event_key)
        resident = self.resident_by_agent_id[agent_id]
        actor_type = str(
            event.get("infected_actor_type")
            or event.get("infected_population")
            or resident.get("population_kind")
            or "resident"
        )
        infected_runtime_uid = int(
            event.get(
                "infected_runtime_uid",
                event.get("infected_runtime_slot_uid", event.get("infected_slot_uid", uid)),
            )
        )
        raw_infector_uid = event.get("infector_uid")
        infector_uid = int(raw_infector_uid) if raw_infector_uid is not None else None
        infector_agent_id = event.get("infector_agent_id")
        if infector_agent_id is None and infector_uid is not None:
            infector_agent_id = self.agent_id_by_uid[infector_uid]
        infector_metadata = (
            self.resident_by_agent_id.get(str(infector_agent_id), {})
            if infector_agent_id is not None
            else {}
        )
        infector_actor_type = (
            event.get("infector_actor_type")
            or event.get("infector_population")
            or infector_metadata.get("population_kind")
            or ("resident" if infector_agent_id is not None else None)
        )
        identity = {
            "infected_agent_id": agent_id,
            "infected_actor_type": actor_type,
            "infected_runtime_uid": infected_runtime_uid,
            "infected_trip_id": event.get("infected_trip_id"),
            "infected_travel_party_id": event.get("infected_travel_party_id"),
            "infected_episode_identity_hash": event.get("infected_episode_identity_hash"),
            "infector_agent_id": infector_agent_id,
            "infector_actor_type": infector_actor_type,
            "infector_runtime_uid": event.get(
                "infector_runtime_uid",
                event.get(
                    "infector_runtime_slot_uid",
                    event.get("infector_slot_uid", infector_uid),
                ),
            ),
            "infector_trip_id": event.get("infector_trip_id"),
            "infector_travel_party_id": event.get("infector_travel_party_id"),
            "infector_episode_identity_hash": event.get("infector_episode_identity_hash"),
        }
        required_natural_history = {
            "symptomatic",
            "infectious_start_date",
            "symptom_onset_date",
            "recovery_date",
        }
        missing_natural_history = required_natural_history - set(event)
        if missing_natural_history:
            raise ValueError(
                "infection event is missing natural-history fields: "
                f"{sorted(missing_natural_history)}"
            )
        infection_date = date.fromisoformat(str(event.get("infection_date", event["date"])))
        infectious_start_date = date.fromisoformat(str(event["infectious_start_date"]))
        recovery_date = date.fromisoformat(str(event["recovery_date"]))
        symptomatic = bool(event["symptomatic"])
        symptom_date = (
            date.fromisoformat(str(event["symptom_onset_date"]))
            if event["symptom_onset_date"] is not None
            else None
        )
        if not infection_date < infectious_start_date <= recovery_date:
            raise ValueError(
                "natural-history chronology must satisfy infection < infectious <= recovery"
            )
        if symptomatic and symptom_date != infectious_start_date:
            raise ValueError("generic symptomatic onset must equal infectious start")
        if not symptomatic and symptom_date is not None:
            raise ValueError("asymptomatic infection must not define symptom onset")
        seeded_event = {**dict(event), "infected_agent_id": agent_id}
        rng = np.random.default_rng(event_stream_seed(self.stream_seed, seeded_event))
        symptom_delay = (symptom_date - infection_date).days if symptom_date is not None else None
        detection_anchor = symptom_date or infection_date
        detection_probability = (
            _probability(
                self.config,
                "symptomatic_detection_probability"
                if symptomatic
                else "asymptomatic_detection_probability",
            )
            * self.config.day_of_week_effect[detection_anchor.weekday()]
        )
        tested = bool(rng.random() < detection_probability)
        detection_delay = _delay(rng, self.config.detection_delay) if tested else None
        detection_date = (
            detection_anchor + timedelta(days=detection_delay)
            if detection_delay is not None
            else None
        )
        reporting_delay = _delay(rng, self.config.reporting_delay) if tested else None
        report_date = (
            detection_date + timedelta(days=reporting_delay)
            if detection_date is not None and reporting_delay is not None
            else None
        )
        reason = (
            "symptomatic_test"
            if tested and symptomatic
            else "asymptomatic_test"
            if tested
            else "not_detected"
        )
        row = {
            **identity,
            "infected_uid": uid,
            "infection_date": infection_date.isoformat(),
            "infectious_start_date": infectious_start_date.isoformat(),
            "symptom_onset_date": symptom_date.isoformat() if symptom_date else None,
            "recovery_date": recovery_date.isoformat(),
            "detection_date": detection_date.isoformat() if detection_date else None,
            "report_date": report_date.isoformat() if report_date else None,
            "symptom_onset_delay_days": symptom_delay,
            "detection_delay_days": detection_delay,
            "reporting_delay_days": reporting_delay,
            "symptomatic": symptomatic,
            "tested": tested,
            "detected": tested,
            "detection_reason": reason,
            "source_kind": str(event["source_kind"]),
            "route_id": str(event["route_id"]),
            "home_parish": str(resident["home_parish"]),
            "age_band": _age_band(int(resident["age"])),
        }
        self._observation_events.append(row)
        if tested and detection_date is not None:
            config_hash = sha256_bytes(canonical_json_bytes(self.config.model_dump(mode="json")))
            notification = DetectionEvent(
                agent_uid=uid,
                agent_id=agent_id,
                detection_date=detection_date.isoformat(),
                detection_time_index=(detection_date - self.start_date).days,
                detection_reason=reason,
                symptomatic=symptomatic,
                observation_config_id=self.config.observation_config_id,
                provenance=MappingProxyType(
                    {
                        "observation_config_id": self.config.observation_config_id,
                        "observation_config_hash": config_hash,
                        "observation_seed": self.config.observation_seed,
                        "parameter_statuses": {
                            key: parameter.status
                            for key, parameter in sorted(self.config.parameters.items())
                        },
                        "lifecycle_delivery_point": "after_disease_transmission",
                    }
                ),
                **identity,
            )
            self._detection_events.append(notification)
            heapq.heappush(
                self._queue,
                (
                    notification.detection_time_index,
                    notification.detection_date,
                    notification.agent_uid,
                    notification.agent_id,
                    notification.infected_episode_identity_hash or "",
                    notification,
                ),
            )
        return row

    def deliver_due(self, time_index: int) -> tuple[DetectionEvent, ...]:
        """Deliver notifications due now or earlier, never future notifications."""

        delivered_now: list[DetectionEvent] = []
        while self._queue and self._queue[0][0] <= time_index:
            _ti, _date, _uid, _agent_id, _episode_hash, event = heapq.heappop(self._queue)
            if event.detection_time_index > time_index:
                raise RuntimeError("future detection notification became visible early")
            delivered_now.append(event)
            self._delivered.append(event)
            if self.consumer is not None:
                self.consumer.consume_detection(event)
        return tuple(delivered_now)

    def snapshot(self) -> ObservationScheduleSnapshot:
        """Return normalized schedule and delivery views without mutation methods."""

        observations = tuple(
            sorted(
                (dict(row) for row in self._observation_events),
                key=lambda row: (row["infection_date"], row["infected_agent_id"]),
            )
        )
        detections = tuple(
            sorted(
                self._detection_events,
                key=lambda event: (
                    event.detection_time_index,
                    event.detection_date,
                    event.agent_uid,
                    event.agent_id,
                ),
            )
        )
        return ObservationScheduleSnapshot(
            observation_events=observations,
            detection_events=detections,
            delivered_detection_events=tuple(self._delivered),
            pending_detection_count=len(self._queue),
            stream_fingerprint=self.stream_fingerprint,
        )


def build_offline_schedule(
    events: list[dict[str, Any]],
    *,
    latent_seed: int,
    start_date: date,
    config: ObservationConfig,
    agent_id_by_uid: Mapping[int, str],
    resident_by_agent_id: Mapping[str, Mapping[str, Any]],
) -> ObservationScheduleSnapshot:
    """Apply the same scheduler semantics without runtime notification delivery."""

    scheduler = ObservationScheduler(
        latent_seed=latent_seed,
        start_date=start_date,
        config=config,
        agent_id_by_uid=agent_id_by_uid,
        resident_by_agent_id=resident_by_agent_id,
    )
    for event in sorted(events, key=lambda row: (row["date"], row["infected_agent_id"])):
        scheduler.schedule_infection(event)
    return scheduler.snapshot()
