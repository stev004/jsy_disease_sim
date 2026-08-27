"""Prospective Milestone 7 intervention runtime.

The manager is one Starsim intervention module.  It owns only intervention
state and effective daily route views; M2/M3/M4 artifacts remain immutable.
The C4 scheduler calls :meth:`consume_detection` after disease transmission,
so a detection on timestep *t* can first change contacts on *t + 1*.
"""

from __future__ import annotations

import hashlib
import weakref
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

import numpy as np
import starsim as ss

from .hashing import canonical_json_bytes, sha256_bytes
from .intervention_schemas import (
    INTERVENTION_SENSITIVITY_AXES,
    InterventionConfig,
    ScenarioConfig,
    intervention_config_hash,
)
from .starsim_adapter import _edge_arrays, _load_starsim

INTERVENTION_FRAMEWORK_VERSION = "7.0.0"
WORKPLACE_ROUTES = {"workplace_team", "workplace_transient"}
TRANSPORT_ROUTES = {"shared_vehicle", "bus"}
SCHOOL_ROUTES = {"school_class", "school_cross_class"}
COMMUNITY_ROUTES = {"community_indoor", "community_outdoor"}
CARE_ROUTES = {"care_resident", "care_staff"}
EXTERNAL_ROUTES = (
    WORKPLACE_ROUTES | TRANSPORT_ROUTES | SCHOOL_ROUTES | COMMUNITY_ROUTES | CARE_ROUTES
)


def _stable_int(seed: int, *parts: object) -> int:
    payload = "|".join(str(part) for part in (seed, *parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def _stable_uniform(seed: int, *parts: object) -> float:
    return _stable_int(seed, *parts) / 2**64


def _age_band(age: int) -> str:
    if age <= 4:
        return "0-4"
    if age <= 17:
        return "5-17"
    if age <= 64:
        return "18-64"
    return "65+"


class InterventionManager(ss.Intervention):
    """Shared typed runtime for all core M7 intervention families."""

    framework_version = INTERVENTION_FRAMEWORK_VERSION

    def __init__(
        self,
        generated: Any,
        interventions: tuple[InterventionConfig, ...] | list[InterventionConfig],
        *,
        run_seed: int,
        start_date: date,
        duration_days: int,
        scenario: ScenarioConfig | None = None,
    ) -> None:
        super().__init__(name="jos_interventions", label="JOS interventions")
        # Keep the large M4 object out of this Starsim module's object graph.
        # Starsim/sciris scans module attributes while initializing all
        # distributions; a weak reference preserves access during the run
        # without recursively walking the full route artifact.
        self._generated_ref = weakref.ref(generated)
        self.intervention_configs = tuple(interventions)
        self.run_seed = run_seed
        self.start_date = start_date
        self.duration_days = duration_days
        self.simulation_end = start_date + timedelta(days=duration_days - 1)
        self.scenario = scenario
        self.config_hashes = {
            config.intervention_id: intervention_config_hash(config)
            for config in self.intervention_configs
        }
        self.event_log: list[dict[str, Any]] = []
        self.daily_state: list[dict[str, Any]] = []
        self.route_effects: list[dict[str, Any]] = []
        self._pending_detection_actions: list[tuple[int, str, Any]] = []
        self._calendar_was_active: dict[str, bool] = defaultdict(bool)
        self._isolation_until: dict[str, np.ndarray] = {}
        self._quarantine_until: dict[str, dict[str, int]] = {}
        self._wfh_current: dict[str, set[str]] = defaultdict(set)
        self._wfh_previous: dict[str, set[str]] = defaultdict(set)
        self._vaccinated_by_intervention: dict[str, set[int]] = defaultdict(set)
        self._effective_by_intervention: dict[str, set[int]] = defaultdict(set)
        self._vaccine_effective_from: dict[str, dict[int, int]] = defaultdict(dict)
        self._vaccine_expired: dict[str, set[int]] = defaultdict(set)
        self._vaccination_denominator: dict[str, int] = {}
        self._day_activations: dict[str, int] = defaultdict(int)
        self._day_releases: dict[str, int] = defaultdict(int)
        self._m2_by_agent: dict[str, dict[str, Any]] = {}
        self._m3_by_agent: dict[str, dict[str, Any]] = {}
        self._households: dict[str, set[str]] = defaultdict(set)
        self._school_by_agent: dict[str, set[str]] = defaultdict(set)
        self._school_type_by_id: dict[str, str] = {}
        self._workplaces_by_agent: dict[str, set[str]] = defaultdict(set)
        self._sectors_by_agent: dict[str, set[str]] = defaultdict(set)
        self._care_setting_by_agent: dict[str, str] = {}
        self._care_type_by_setting: dict[str, str] = {}
        self._care_resident_ids: set[str] = set()
        self._care_staff_ids: set[str] = set()
        self._institutional_staff_ids: set[str] = set()
        self._uid_by_agent_id = {
            agent_id: index for index, agent_id in enumerate(generated.agent_ids)
        }
        self._agent_id_by_uid = {
            index: agent_id for agent_id, index in self._uid_by_agent_id.items()
        }
        self._prepare_metadata()

    @property
    def generated(self) -> Any:
        generated = self._generated_ref()
        if generated is None:
            raise RuntimeError("M4 route object was released before intervention execution")
        return generated

    def _prepare_metadata(self) -> None:
        self._m2_by_agent = {row["agent_id"]: row for row in self.generated.m2_input.residents}
        self._m3_by_agent = {
            row["agent_id"]: row for row in self.generated.m3_input.resident_structure
        }
        for agent_id, row in self._m2_by_agent.items():
            household_id = row.get("household_id")
            if household_id is not None:
                self._households[str(household_id)].add(agent_id)
            setting_id = row.get("care_setting_id")
            if setting_id is not None:
                self._care_setting_by_agent[agent_id] = str(setting_id)
                self._care_resident_ids.add(agent_id)
        for setting in self.generated.m2_input.communal_settings:
            setting_id = str(setting["setting_id"])
            self._care_type_by_setting[setting_id] = str(setting["setting_type"])
        for row in self.generated.m3_input.school_assignments:
            agent_id = str(row["agent_id"])
            self._school_by_agent[agent_id].add(str(row["school_id"]))
            self._school_type_by_id[str(row["school_id"])] = str(row["school_type"])
        for row in self.generated.m3_input.job_assignments:
            agent_id = str(row["agent_id"])
            self._workplaces_by_agent[agent_id].add(str(row["workplace_id"]))
            self._sectors_by_agent[agent_id].add(str(row["sector"]))
        for row in self.generated.school_staff_assignments:
            agent_id = str(row["agent_id"])
            self._school_by_agent[agent_id].add(str(row["school_id"]))
            self._school_type_by_id[str(row["school_id"])] = str(row["school_type"])
            self._institutional_staff_ids.add(agent_id)
        for row in self.generated.care_staff_assignments:
            agent_id = str(row["agent_id"])
            self._care_staff_ids.add(agent_id)
            self._institutional_staff_ids.add(agent_id)
            self._care_setting_by_agent[agent_id] = str(row["setting_id"])

    @ss.required("disable")
    def init_pre(self, sim: Any) -> None:
        # This manager owns only deterministic Python state and no Starsim
        # distributions/results.  The base Module initializer recursively
        # searches every attribute for rates; traversing the full M2/M3
        # metadata at island scale is both unnecessary and pathological.
        # Link the simulation timeline directly and leave the empty module
        # containers untouched.
        self.setattribute("sim", sim)
        self.setattribute("t", sim.t)
        self.pre_initialized = True
        n_agents = len(sim.people)
        for config in self.intervention_configs:
            if config.type == "case_isolation":
                self._isolation_until[config.intervention_id] = np.full(
                    n_agents, -1, dtype=np.int64
                )
            elif config.type == "household_quarantine":
                self._quarantine_until[config.intervention_id] = {}
        return

    @ss.required("disable")
    def finish_step(self) -> None:
        """Do not advance the shared simulation timeline a second time."""

        return

    @ss.required("disable")
    def link_rates(self, force: bool = False) -> None:
        """M7 has no Starsim rate parameters to link."""

        return

    @ss.required("disable")
    def init_results(self) -> None:
        """M7 state is exported by JOS, not as a Starsim result series."""

        return

    def _disease(self) -> Any:
        diseases = list(self.sim.diseases())
        if not diseases:
            raise RuntimeError("M7 interventions require one respiratory disease module")
        return diseases[0]

    def _current_date(self) -> date:
        raw = str(self.sim.t.now("str"))[:10].replace(".", "-")
        return date.fromisoformat(raw)

    def _target_matches(self, config: InterventionConfig, agent_id: str) -> bool:
        target = config.target
        m2 = self._m2_by_agent[agent_id]
        m3 = self._m3_by_agent[agent_id]
        age = int(m2["age"])
        care_setting = self._care_setting_by_agent.get(agent_id)
        care_role = (
            "care_staff"
            if agent_id in self._care_staff_ids
            else "care_resident"
            if agent_id in self._care_resident_ids
            else None
        )
        if target.agent_ids and agent_id not in target.agent_ids:
            return False
        if target.age_min is not None and age < target.age_min:
            return False
        if target.age_max is not None and age > target.age_max:
            return False
        if target.age_bands and _age_band(age) not in target.age_bands:
            return False
        if target.home_parishes and m2["home_parish"] not in target.home_parishes:
            return False
        sectors = self._sectors_by_agent.get(agent_id, set())
        if target.employment_sectors and not sectors.intersection(target.employment_sectors):
            return False
        schools = self._school_by_agent.get(agent_id, set())
        if target.school_ids and not schools.intersection(target.school_ids):
            return False
        if target.school_types and not any(
            self._school_type_by_id.get(school_id) in target.school_types for school_id in schools
        ):
            return False
        workplaces = self._workplaces_by_agent.get(agent_id, set())
        if target.workplace_ids and not workplaces.intersection(target.workplace_ids):
            return False
        if target.worker_only and m3.get("economic_status") != "employed":
            return False
        if target.care_role != "any" and care_role != target.care_role:
            return False
        if target.care_setting_types:
            if (
                care_setting is None
                or self._care_type_by_setting.get(care_setting) not in target.care_setting_types
            ):
                return False
        if (
            agent_id in self._institutional_staff_ids
            and not target.include_institutional_staff
            and config.type == "workplace_reduction"
        ):
            return False
        return True

    def _target_adheres(self, config: InterventionConfig, agent_id: str, route_id: str) -> bool:
        """Return the stable per-agent adherence draw for route effects."""

        return (
            self._target_matches(config, agent_id)
            and _stable_uniform(
                self.run_seed, "route-adherence", config.intervention_id, route_id, agent_id
            )
            < config.adherence
        )

    def _event_reference(self, event: Any) -> str:
        return f"detection:{event.agent_id}:{event.detection_date}:{event.detection_reason}"

    def _append_event(
        self,
        config: InterventionConfig,
        *,
        action: str,
        cause: str,
        agent_id: str | None = None,
        household_id: str | None = None,
        setting_id: str | None = None,
        detection_reference: str | None = None,
        previous_state: Any = None,
        new_state: Any = None,
        date_value: date | None = None,
        time_index: int | None = None,
    ) -> None:
        when = date_value or self._current_date()
        ti = int(self.ti) if time_index is None else time_index
        row: dict[str, Any] = {
            "date": when.isoformat(),
            "time_index": ti,
            "intervention_id": config.intervention_id,
            "intervention_type": config.type,
            "action": action,
            "cause": cause,
            "detection_event_reference": detection_reference,
            "agent_uid": self._uid_by_agent_id.get(agent_id) if agent_id is not None else None,
            "agent_id": agent_id,
            "household_id": household_id,
            "setting_id": setting_id,
            "previous_state": previous_state,
            "new_state": new_state,
            "config_hash": self.config_hashes[config.intervention_id],
            "provenance_hash": sha256_bytes(
                canonical_json_bytes(config.resolved_parameter_provenance())
            ),
        }
        self.event_log.append(row)
        if action in {
            "intervention_activated",
            "agent_entered_isolation",
            "household_entered_quarantine",
            "wfh_schedule_changed",
            "vaccine_administered",
            "protection_became_effective",
            "care_protection_activated",
            "school_route_suppressed",
        }:
            self._day_activations[config.intervention_id] += 1
        if action in {
            "intervention_released",
            "agent_left_isolation",
            "household_released",
            "protection_expired",
        }:
            self._day_releases[config.intervention_id] += 1

    def consume_detection(self, event: Any) -> None:
        """Queue detection-triggered state; delivery occurs after current transmission."""

        for config in self.intervention_configs:
            if not config.enabled or config.type not in {"case_isolation", "household_quarantine"}:
                continue
            if not self._target_matches(config, event.agent_id):
                continue
            accepted = (
                _stable_uniform(
                    self.run_seed,
                    "adherence",
                    config.intervention_id,
                    event.agent_id,
                    event.detection_date,
                )
                < config.adherence
            )
            if not accepted:
                self._append_event(
                    config,
                    action="intervention_declined",
                    cause="adherence",
                    agent_id=event.agent_id,
                    detection_reference=self._event_reference(event),
                    previous_state=False,
                    new_state=False,
                    time_index=event.detection_time_index,
                    date_value=date.fromisoformat(event.detection_date),
                )
                continue
            effective_ti = event.detection_time_index + 1 + config.start_delay_days
            self._pending_detection_actions.append((effective_ti, config.intervention_id, event))

    def _apply_detection_actions(self, ti: int) -> None:
        due = [item for item in self._pending_detection_actions if item[0] <= ti]
        self._pending_detection_actions = [
            item for item in self._pending_detection_actions if item[0] > ti
        ]
        for effective_ti, intervention_id, event in sorted(
            due, key=lambda item: (item[0], item[1], item[2].agent_uid)
        ):
            config = next(
                item
                for item in self.intervention_configs
                if item.intervention_id == intervention_id
            )
            detection_reference = self._event_reference(event)
            if config.type == "case_isolation":
                uid = int(event.agent_uid)
                until = effective_ti + int(config.duration_days or self.duration_days)
                states = self._isolation_until[intervention_id]
                previous = int(states[uid])
                states[uid] = max(previous, until)
                action = (
                    "agent_entered_isolation" if previous <= effective_ti else "isolation_extended"
                )
                self._append_event(
                    config,
                    action=action,
                    cause="detection",
                    agent_id=event.agent_id,
                    detection_reference=detection_reference,
                    previous_state=previous if previous >= 0 else None,
                    new_state=int(states[uid]),
                    time_index=ti,
                )
            else:
                household_id = self._m2_by_agent[event.agent_id].get("household_id")
                if household_id is None:
                    self._append_event(
                        config,
                        action="quarantine_skipped_communal_resident",
                        cause="detection",
                        agent_id=event.agent_id,
                        detection_reference=detection_reference,
                        time_index=ti,
                    )
                    continue
                household_key = str(household_id)
                until = effective_ti + int(config.duration_days or self.duration_days)
                quarantine_states = self._quarantine_until[intervention_id]
                previous = quarantine_states.get(household_key, -1)
                quarantine_states[household_key] = max(previous, until)
                action = (
                    "household_entered_quarantine"
                    if previous <= effective_ti
                    else "quarantine_extended"
                )
                self._append_event(
                    config,
                    action=action,
                    cause="detection",
                    agent_id=event.agent_id,
                    household_id=household_key,
                    detection_reference=detection_reference,
                    previous_state=previous if previous >= 0 else None,
                    new_state=quarantine_states[household_key],
                    time_index=ti,
                )

    def _release_detection_states(self, ti: int) -> None:
        for config in self.intervention_configs:
            if config.type == "case_isolation":
                states = self._isolation_until[config.intervention_id]
                due_uids = np.flatnonzero(states == ti)
                for uid in due_uids:
                    agent_id = self._agent_id_by_uid[int(uid)]
                    self._append_event(
                        config,
                        action="agent_left_isolation",
                        cause="duration_elapsed",
                        agent_id=agent_id,
                        previous_state=int(ti),
                        new_state=None,
                    )
                    states[uid] = -1
            elif config.type == "household_quarantine":
                quarantine_states = self._quarantine_until[config.intervention_id]
                due_households = sorted(
                    household_id for household_id, until in quarantine_states.items() if until == ti
                )
                for household_id in due_households:
                    self._append_event(
                        config,
                        action="household_released",
                        cause="duration_elapsed",
                        household_id=household_id,
                        previous_state=ti,
                        new_state=None,
                    )
                    del quarantine_states[household_id]

    def _active_isolation(self, config_id: str, uid: int, ti: int) -> bool:
        states = self._isolation_until.get(config_id)
        return states is not None and int(states[uid]) > ti

    def _active_quarantine(self, config_id: str, agent_id: str, ti: int) -> bool:
        household_id = self._m2_by_agent[agent_id].get("household_id")
        if household_id is None:
            return False
        until = self._quarantine_until.get(config_id, {}).get(str(household_id), -1)
        return until > ti

    def _calendar_active(self, config: InterventionConfig, when: date) -> bool:
        return config.active_date_window(when, self.simulation_end)

    def _update_calendar_transitions(self, when: date) -> None:
        for config in self.intervention_configs:
            if config.activation_rule != "calendar":
                continue
            active = self._calendar_active(config, when)
            previous = self._calendar_was_active[config.intervention_id]
            if active and not previous:
                self._append_event(config, action="intervention_activated", cause="calendar")
                if config.type == "school_closure":
                    self._append_event(
                        config,
                        action="school_route_suppressed",
                        cause="calendar",
                        new_state={
                            "class_multiplier": config.class_multiplier,
                            "cross_class_multiplier": config.cross_class_multiplier,
                        },
                    )
                if config.type == "care_home_protection":
                    self._append_event(config, action="care_protection_activated", cause="calendar")
            if previous and not active:
                self._append_event(config, action="intervention_released", cause="calendar")
            self._calendar_was_active[config.intervention_id] = active

    def _refresh_wfh(self, when: date, ti: int) -> None:
        for config in self.intervention_configs:
            if config.type != "workplace_reduction":
                continue
            active = self._calendar_active(config, when)
            current: set[str] = set()
            if active and config.adherence > 0:
                for agent_id in self.generated.agent_ids:
                    if not self._target_matches(config, agent_id):
                        continue
                    if (
                        _stable_uniform(
                            self.run_seed, "wfh-adherence", config.intervention_id, agent_id
                        )
                        >= config.adherence
                    ):
                        continue
                    if config.wfh_days_per_week is not None:
                        weekdays = sorted(
                            range(5),
                            key=lambda weekday: _stable_int(
                                self.run_seed,
                                "wfh-week",
                                config.intervention_id,
                                agent_id,
                                when.isocalendar().year,
                                when.isocalendar().week,
                                weekday,
                            ),
                        )[: config.wfh_days_per_week]
                        scheduled = when.weekday() in weekdays
                    else:
                        scheduled = (
                            when.weekday() < 5
                            and _stable_uniform(
                                self.run_seed,
                                "wfh-day",
                                config.intervention_id,
                                agent_id,
                                when.isoformat(),
                            )
                            < config.additional_wfh_fraction
                        )
                    if scheduled:
                        current.add(agent_id)
            previous = self._wfh_previous[config.intervention_id]
            for agent_id in sorted(current ^ previous):
                self._append_event(
                    config,
                    action="wfh_schedule_changed",
                    cause="calendar_schedule",
                    agent_id=agent_id,
                    previous_state=agent_id in previous,
                    new_state=agent_id in current,
                    time_index=ti,
                    date_value=when,
                )
            self._wfh_current[config.intervention_id] = current
            self._wfh_previous[config.intervention_id] = current

    def _refresh_vaccination(self, when: date, ti: int) -> None:
        disease = self._disease()
        for config in self.intervention_configs:
            if config.type != "vaccination" or not self._calendar_active(config, when):
                continue
            intervention_id = config.intervention_id
            if intervention_id not in self._vaccination_denominator:
                self._vaccination_denominator[intervention_id] = sum(
                    self._target_matches(config, agent_id) for agent_id in self.generated.agent_ids
                )
            denominator = self._vaccination_denominator[intervention_id]
            target_doses = int(np.ceil(denominator * config.coverage_target))
            already = self._vaccinated_by_intervention[intervention_id]
            remaining = max(0, target_doses - len(already))
            if not remaining or config.rollout_rate <= 0:
                continue
            vaccinated_agent_ids = {self._agent_id_by_uid[uid] for uid in already}
            candidates = [
                agent_id
                for agent_id in self.generated.agent_ids
                if agent_id not in vaccinated_agent_ids
                and self._target_matches(config, agent_id)
                and bool(disease.susceptible.raw[self._uid_by_agent_id[agent_id]])
            ]
            candidates.sort(
                key=lambda agent_id: (
                    _stable_int(self.run_seed, "vaccine-rollout", intervention_id, agent_id),
                    agent_id,
                )
            )
            count = min(
                remaining,
                len(candidates),
                max(1, int(np.ceil(len(candidates) * config.rollout_rate))),
            )
            for agent_id in candidates[:count]:
                if (
                    _stable_uniform(
                        self.run_seed, "vaccine-uptake", intervention_id, agent_id, when.isoformat()
                    )
                    >= config.uptake_probability
                ):
                    continue
                uid = self._uid_by_agent_id[agent_id]
                already.add(uid)
                effective_ti = ti + config.protection_delay_days
                self._vaccine_effective_from[intervention_id][uid] = effective_ti
                self._append_event(
                    config,
                    action="vaccine_administered",
                    cause="rollout",
                    agent_id=agent_id,
                    previous_state=False,
                    new_state={
                        "effective_time_index": effective_ti,
                        "efficacy_susceptibility": config.efficacy_susceptibility,
                        "efficacy_infectiousness": config.efficacy_infectiousness,
                    },
                    date_value=when,
                    time_index=ti,
                )

    def _sync_vaccine_modifiers(self, ti: int) -> None:
        vaccine_configs = [item for item in self.intervention_configs if item.type == "vaccination"]
        if not vaccine_configs:
            return
        disease = self._disease()
        n_agents = len(self.generated.agent_ids)
        relative_sus = np.ones(n_agents, dtype=float)
        relative_trans = np.ones(n_agents, dtype=float)
        for config in vaccine_configs:
            intervention_id = config.intervention_id
            administered = self._vaccinated_by_intervention[intervention_id]
            effective_from = self._vaccine_effective_from[intervention_id]
            for uid in sorted(administered):
                effective_ti = effective_from[uid]
                waned = config.waning_days is not None and ti >= effective_ti + config.waning_days
                if ti >= effective_ti and not waned:
                    if uid not in self._effective_by_intervention[intervention_id]:
                        self._effective_by_intervention[intervention_id].add(uid)
                        self._append_event(
                            config,
                            action="protection_became_effective",
                            cause="protection_delay_elapsed",
                            agent_id=self._agent_id_by_uid[uid],
                            previous_state=False,
                            new_state=True,
                            time_index=ti,
                        )
                    relative_sus[uid] *= 1.0 - config.efficacy_susceptibility
                    relative_trans[uid] *= 1.0 - config.efficacy_infectiousness
                elif waned and uid not in self._vaccine_expired[intervention_id]:
                    self._effective_by_intervention[intervention_id].discard(uid)
                    self._vaccine_expired[intervention_id].add(uid)
                    self._append_event(
                        config,
                        action="protection_expired",
                        cause="waning",
                        agent_id=self._agent_id_by_uid[uid],
                        previous_state=True,
                        new_state=False,
                        time_index=ti,
                    )
        disease.rel_sus.raw[:] = relative_sus
        disease.rel_trans.raw[:] = relative_trans

    def _school_edge_matches(self, config: InterventionConfig, p1: str, p2: str) -> bool:
        if not any(self._target_matches(config, agent_id) for agent_id in (p1, p2)):
            return False
        edge_schools = self._school_by_agent.get(p1, set()) | self._school_by_agent.get(p2, set())
        if not edge_schools:
            return False
        if config.target.school_ids and not edge_schools.intersection(config.target.school_ids):
            return False
        if config.target.school_types and not any(
            self._school_type_by_id.get(school_id) in config.target.school_types
            for school_id in edge_schools
        ):
            return False
        if not config.target.school_ids and not config.target.school_types:
            return True
        return True

    def _care_edge_matches(self, config: InterventionConfig, p1: str, p2: str) -> bool:
        settings = {
            self._care_setting_by_agent[agent_id]
            for agent_id in (p1, p2)
            if agent_id in self._care_setting_by_agent
        }
        return any(self._care_target_matches_setting(config, setting_id) for setting_id in settings)

    def _care_target_matches_setting(self, config: InterventionConfig, setting_id: str) -> bool:
        setting_type = self._care_type_by_setting.get(setting_id, "")
        if (
            config.target.care_setting_types
            and setting_type not in config.target.care_setting_types
        ):
            return False
        if config.care_target == "both":
            return True
        nursing = "with nursing" in setting_type.lower()
        return nursing if config.care_target == "nursing" else not nursing

    def _edge_multiplier(
        self, config: InterventionConfig, route_id: str, p1: str, p2: str, when: date, ti: int
    ) -> float:
        endpoints = (p1, p2)
        if not config.enabled:
            return 1.0
        if config.activation_rule == "calendar" and not self._calendar_active(config, when):
            return 1.0
        if config.type in {"case_isolation", "household_quarantine"}:
            factor = 1.0
            for agent_id in endpoints:
                active = (
                    self._active_isolation(
                        config.intervention_id, self._uid_by_agent_id[agent_id], ti
                    )
                    if config.type == "case_isolation"
                    else self._active_quarantine(config.intervention_id, agent_id, ti)
                )
                if active:
                    factor *= config.route_effects.get(
                        route_id, 1.0 if route_id == "household" else 0.0
                    )
            return factor
        explicit = config.route_effects.get(route_id)
        if config.type in {"masking", "gathering_reduction"}:
            if not any(self._target_adheres(config, agent_id, route_id) for agent_id in endpoints):
                return 1.0
            return 1.0 if explicit is None else explicit
        if config.type == "school_closure":
            if (
                route_id not in SCHOOL_ROUTES
                or not self._school_edge_matches(config, p1, p2)
                or not any(
                    self._target_adheres(config, agent_id, route_id) for agent_id in endpoints
                )
            ):
                return 1.0
            if explicit is not None:
                return explicit
            return (
                config.class_multiplier
                if route_id == "school_class"
                else config.cross_class_multiplier
            )
        if config.type == "workplace_reduction":
            target_edge = any(
                self._target_adheres(config, agent_id, route_id) for agent_id in endpoints
            )
            if route_id in WORKPLACE_ROUTES | TRANSPORT_ROUTES and any(
                agent_id in self._wfh_current[config.intervention_id] for agent_id in endpoints
            ):
                return 0.0
            if route_id in WORKPLACE_ROUTES and target_edge:
                return config.workplace_multiplier if explicit is None else explicit
            if route_id in TRANSPORT_ROUTES and target_edge:
                return config.commute_multiplier if explicit is None else explicit
            return 1.0
        if config.type == "community_reduction":
            if route_id not in COMMUNITY_ROUTES:
                return 1.0
            if not any(self._target_adheres(config, agent_id, route_id) for agent_id in endpoints):
                return 1.0
            if explicit is not None:
                return explicit
            return (
                config.indoor_multiplier
                if route_id == "community_indoor"
                else config.outdoor_multiplier
            )
        if config.type == "care_home_protection":
            care_target = self._care_edge_matches(config, p1, p2) and any(
                self._target_adheres(config, agent_id, route_id)
                for agent_id in endpoints
                if agent_id in self._care_setting_by_agent
            )
            if route_id in CARE_ROUTES and care_target:
                return config.care_contact_multiplier if explicit is None else explicit
            if route_id not in {"household", *CARE_ROUTES}:
                resident_target = any(
                    agent_id in self._care_resident_ids
                    and self._care_target_matches_setting(
                        config, self._care_setting_by_agent[agent_id]
                    )
                    and self._target_adheres(config, agent_id, route_id)
                    for agent_id in endpoints
                )
                staff_target = any(
                    agent_id in self._care_staff_ids
                    and self._care_target_matches_setting(
                        config, self._care_setting_by_agent[agent_id]
                    )
                    and self._target_adheres(config, agent_id, route_id)
                    for agent_id in endpoints
                )
                if resident_target:
                    return config.care_external_resident_multiplier
                if staff_target:
                    return config.care_external_staff_multiplier
            return 1.0 if explicit is None else explicit
        return 1.0 if explicit is None else explicit

    def _apply_effective_routes(self, when: date, ti: int) -> None:
        ss_module = _load_starsim()
        route_map = {str(key): route for key, route in self.sim.networks.items()}
        for route_id in sorted(self.generated.route_specs):
            route = route_map.get(route_id)
            if route is None:
                continue
            base_edges = list(self.generated.route_snapshot(route_id, when).edges)
            effective_edges: list[dict[str, Any]] = []
            multipliers: list[float] = []
            for edge in base_edges:
                factor = 1.0
                for config in self.intervention_configs:
                    factor *= self._edge_multiplier(
                        config, route_id, str(edge["p1"]), str(edge["p2"]), when, ti
                    )
                factor = max(0.0, min(1.0, factor))
                multipliers.append(factor)
                # Care roster edges remain represented with beta=0 when a care
                # intervention suppresses them.  This preserves staffing and
                # setting topology while eliminating transmission opportunity.
                keep_zero = route_id in CARE_ROUTES
                if factor > 0 or keep_zero:
                    effective_edges.append({**edge, "weight": float(edge["weight"]) * factor})
            arrays = _edge_arrays(ss_module, effective_edges, self._uid_by_agent_id)
            route.edges.p1 = arrays["p1"]
            route.edges.p2 = arrays["p2"]
            route.edges.beta = arrays["beta"]
            route.edges.dur = np.ones(len(effective_edges), dtype=float)
            self.route_effects.append(
                {
                    "date": when.isoformat(),
                    "time_index": ti,
                    "route_id": route_id,
                    "base_edge_count": len(base_edges),
                    "effective_edge_count": len(effective_edges),
                    "suppressed_edge_count": len(base_edges) - len(effective_edges),
                    "mean_multiplier": float(np.mean(multipliers)) if multipliers else 1.0,
                    "minimum_multiplier": min(multipliers) if multipliers else 1.0,
                    "maximum_multiplier": max(multipliers) if multipliers else 1.0,
                }
            )

    def _active_agents(self, config: InterventionConfig, ti: int) -> int:
        if config.type == "case_isolation":
            return int(np.count_nonzero(self._isolation_until[config.intervention_id] > ti))
        if config.type == "household_quarantine":
            return sum(
                len(self._households[household_id])
                for household_id, until in self._quarantine_until[config.intervention_id].items()
                if until > ti
            )
        if config.type == "workplace_reduction":
            return len(self._wfh_current[config.intervention_id])
        if config.type == "vaccination":
            return len(self._effective_by_intervention[config.intervention_id])
        if config.type in {
            "school_closure",
            "community_reduction",
            "care_home_protection",
            "masking",
            "gathering_reduction",
        }:
            return sum(
                self._target_matches(config, agent_id) for agent_id in self.generated.agent_ids
            )
        return 0

    def _active_households(self, config: InterventionConfig, ti: int) -> int:
        if config.type != "household_quarantine":
            return 0
        return sum(until > ti for until in self._quarantine_until[config.intervention_id].values())

    def _active_settings(self, config: InterventionConfig, when: date) -> int:
        if config.type == "school_closure" and self._calendar_active(config, when):
            schools = set(self._school_type_by_id)
            if config.target.school_ids:
                schools &= set(config.target.school_ids)
            if config.target.school_types:
                schools = {
                    school
                    for school in schools
                    if self._school_type_by_id[school] in config.target.school_types
                }
            return len(schools)
        if config.type == "care_home_protection" and self._calendar_active(config, when):
            return sum(
                self._care_target_matches_setting(config, setting_id)
                for setting_id in self._care_type_by_setting
            )
        if config.type == "workplace_reduction" and self._calendar_active(config, when):
            return len(
                {
                    workplace
                    for agent_id in self._wfh_current[config.intervention_id]
                    for workplace in self._workplaces_by_agent.get(agent_id, set())
                }
            )
        return 0

    def _record_daily_state(self, when: date, ti: int) -> None:
        for config in self.intervention_configs:
            self.daily_state.append(
                {
                    "date": when.isoformat(),
                    "time_index": ti,
                    "intervention_id": config.intervention_id,
                    "intervention_type": config.type,
                    "active_agents": self._active_agents(config, ti),
                    "active_households": self._active_households(config, ti),
                    "active_settings": self._active_settings(config, when),
                    "new_activations": self._day_activations[config.intervention_id],
                    "new_releases": self._day_releases[config.intervention_id],
                    "config_hash": self.config_hashes[config.intervention_id],
                }
            )

    def step(self) -> None:
        ti = int(self.ti)
        when = self._current_date()
        self._day_activations.clear()
        self._day_releases.clear()
        self._release_detection_states(ti)
        self._apply_detection_actions(ti)
        self._update_calendar_transitions(when)
        self._refresh_wfh(when, ti)
        self._refresh_vaccination(when, ti)
        self._sync_vaccine_modifiers(ti)
        self._apply_effective_routes(when, ti)
        self._record_daily_state(when, ti)

    @property
    def state_snapshot(self) -> dict[str, Any]:
        """Return minimal final runtime state for diagnostics and tests."""

        return {
            "isolation_until": {
                key: values.tolist() for key, values in sorted(self._isolation_until.items())
            },
            "quarantine_until": {
                key: dict(sorted(values.items()))
                for key, values in sorted(self._quarantine_until.items())
            },
            "vaccinated": {
                key: sorted(values)
                for key, values in sorted(self._vaccinated_by_intervention.items())
            },
            "vaccine_effective_from": {
                key: dict(sorted(values.items()))
                for key, values in sorted(self._vaccine_effective_from.items())
            },
            "wfh_active_agents": {
                key: sorted(values) for key, values in sorted(self._wfh_current.items())
            },
        }

    def diagnostics(self) -> dict[str, Any]:
        """Return framework, lifecycle, composition and provenance diagnostics."""

        return {
            "framework_version": self.framework_version,
            "scenario_id": self.scenario.scenario_id if self.scenario is not None else None,
            "scenario_config_hash": (
                self.scenario.config_hash if self.scenario is not None else None
            ),
            "intervention_ids": [config.intervention_id for config in self.intervention_configs],
            "intervention_config_hashes": dict(sorted(self.config_hashes.items())),
            "sensitivity_axes": list(INTERVENTION_SENSITIVITY_AXES),
            "sensitivity_config_ids": (
                list(self.scenario.sensitivity_config_ids) if self.scenario is not None else []
            ),
            "lifecycle_order": [
                "disease_state_progression",
                "network_refresh",
                "intervention_phase",
                "disease_transmission_and_imports",
                "detection_delivery",
                "next_timestep_consumer_effect",
            ],
            "detection_trigger_contract": (
                "detection on t schedules state; effective from t+1 plus declared delay"
            ),
            "no_retroactive_effect": True,
            "network_strategy": (
                "immutable M4 snapshots plus prospective effective route edge/beta views"
            ),
            "composition": {
                "rule": "product of active route multipliers, clipped to [0, 1]",
                "ordering": (
                    "stable intervention_id order for diagnostics; multiplication is commutative"
                ),
                "canonical_network_mutated": False,
            },
            "event_count": len(self.event_log),
            "daily_state_rows": len(self.daily_state),
            "route_effect_rows": len(self.route_effects),
            "state": self.state_snapshot,
        }
