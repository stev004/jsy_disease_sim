"""Generic, pathogen-neutral respiratory SEIRS module for Milestone 5.

The class delegates edge-level transmission probability calculation to
Starsim's ``compute_transmission`` and ``Network.net_beta`` primitives. JOS
adds an order-invariant competing-candidate attribution layer and records the
resulting attributable events.
"""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict, deque
from datetime import date, timedelta
from typing import Any

import numpy as np

from .outbreak_schemas import DurationSpecification

SUCCESS_KEY_ISIN_THRESHOLD = 64
# Quick NumPy 2.x measurement on 100k edge keys: np.isin wins through 64
# successes; unique/searchsorted is faster from 65 onward.


def _load_starsim() -> Any:
    """Import the pinned engine lazily at the disease boundary."""

    import starsim as ss  # type: ignore[import-untyped]

    if ss.__version__ != "3.5.2":
        raise RuntimeError(f"M5 requires Starsim 3.5.2, found {ss.__version__}")
    return ss


def _stable_key(seed: int, *parts: object) -> bytes:
    return hashlib.sha256("|".join(str(part) for part in (seed, *parts)).encode()).digest()


def _match_success_hazards(
    src: np.ndarray,
    trg: np.ndarray,
    beta_per_dt: np.ndarray,
    rel_trans_raw: Any,
    rel_sus_raw: Any,
    target_uids: np.ndarray,
    source_uids: np.ndarray,
) -> list[tuple[tuple[int, int], float]]:
    """Match successful pairs to their earliest duplicate edge occurrences."""

    # Runtime UIDs are nonnegative and bounded below 2**32, so this
    # fixed-width packing is an exact pair encoding (including duplicate
    # occurrences); signed int64 preserves the unique 64-bit bit patterns.
    K = 2**32
    uid_arrays = (src, trg, source_uids, target_uids)
    max_uid = max(
        (int(np.max(values)) for values in uid_arrays if len(values)),
        default=-1,
    )
    assert max_uid < K
    edge_keys = np.asarray(src, dtype=np.int64) * K + np.asarray(trg, dtype=np.int64)
    success_keys = np.asarray(source_uids, dtype=np.int64) * K + np.asarray(
        target_uids, dtype=np.int64
    )
    if len(success_keys) <= SUCCESS_KEY_ISIN_THRESHOLD:
        hit_indices = np.flatnonzero(np.isin(edge_keys, success_keys))
    else:
        unique_success_keys = np.unique(success_keys)
        positions = np.searchsorted(unique_success_keys, edge_keys)
        in_range = positions < len(unique_success_keys)
        in_range[in_range] = unique_success_keys[positions[in_range]] == edge_keys[in_range]
        hit_indices = np.flatnonzero(in_range)
    indices_by_pair: dict[tuple[int, int], deque[int]] = defaultdict(deque)
    for hit_index in hit_indices:
        indices_by_pair[(int(src[hit_index]), int(trg[hit_index]))].append(int(hit_index))

    matches: list[tuple[tuple[int, int], float]] = []
    for target, source in zip(target_uids, source_uids, strict=True):
        pair = (int(source), int(target))
        edge_index = indices_by_pair[pair].popleft()
        probability = float(rel_trans_raw[pair[0]] * rel_sus_raw[pair[1]] * beta_per_dt[edge_index])
        matches.append((pair, max(0.0, min(1.0, probability))))
    return matches


def sample_episode_duration(
    specification: DurationSpecification,
    *,
    run_seed: int,
    stage: str,
    agent_uid: int,
    episode_index: int,
) -> float:
    """Draw one stage duration from an episode-scoped deterministic stream."""

    if specification.family == "constant":
        return float(specification.mean_days)
    if specification.cv is None:  # pragma: no cover - guarded by the strict schema
        raise ValueError("gamma durations require cv")
    shape = 1.0 / float(specification.cv) ** 2
    scale = float(specification.mean_days) / shape
    seed = int.from_bytes(
        _stable_key(
            run_seed,
            "natural-history-duration",
            specification.schema_version,
            stage,
            agent_uid,
            episode_index,
        )[:8],
        byteorder="little",
        signed=False,
    )
    return float(np.random.default_rng(seed).gamma(shape=shape, scale=scale))


class RespiratorySEIRS(_load_starsim().Infection):  # type: ignore[misc]
    """A generic daily SEIRS infection with optional immunity waning.

    Presymptomatic, symptomatic and asymptomatic substates, severity and
    disease deaths are intentionally deferred.  The active state machine is
    ``S -> E -> I -> R`` and, when enabled, ``R -> S``.
    """

    disease_module_version = "11.1.0"

    def __init__(
        self,
        *,
        route_betas: dict[str, float],
        initial_seed_count: int = 1,
        initial_prevalence: float | None = None,
        import_schedule: dict[str, int] | None = None,
        import_rate_per_day: float = 0.0,
        latent_duration: DurationSpecification | None = None,
        infectious_duration: DurationSpecification | None = None,
        immunity_duration: DurationSpecification | None = None,
        symptomatic_probability: float = 0.6,
        waning_enabled: bool = False,
        observation_scheduler: Any | None = None,
    ) -> None:
        ss = _load_starsim()
        super().__init__()
        if set(route_betas) == set():
            raise ValueError("at least one Starsim route beta is required")
        if any(beta < 0 or beta > 1 for beta in route_betas.values()):
            raise ValueError("route beta values must be in [0, 1]")
        if initial_seed_count < 0:
            raise ValueError("initial_seed_count must be non-negative")
        if initial_prevalence is not None and initial_seed_count != 0:
            raise ValueError("set either initial_seed_count or initial_prevalence, not both")
        if initial_prevalence is not None and not 0 <= initial_prevalence <= 1:
            raise ValueError("initial_prevalence must be in [0, 1]")
        if import_rate_per_day < 0:
            raise ValueError("import_rate_per_day must be non-negative")
        if not 0 <= symptomatic_probability <= 1:
            raise ValueError("symptomatic_probability must be in [0, 1]")

        self._duration_specs = {
            "latent": latent_duration
            or DurationSpecification(
                family="constant",
                mean_days=2.0,
                status="scenario_assumption",
                notes="Pathogen-neutral constructor default.",
            ),
            "infectious": infectious_duration
            or DurationSpecification(
                family="constant",
                mean_days=5.0,
                status="scenario_assumption",
                notes="Pathogen-neutral constructor default.",
            ),
            "immunity": immunity_duration
            or DurationSpecification(
                family="constant",
                mean_days=30.0,
                status="scenario_assumption",
                notes="Explicit waning comparator constructor default.",
            ),
        }

        self.define_pars(
            beta=dict(route_betas),
            init_prev=None,
            initial_seed_count=initial_seed_count,
            initial_prevalence=initial_prevalence,
            import_schedule=dict(import_schedule or {}),
            import_count=ss.poisson(lam=import_rate_per_day),
            symptomatic_probability=symptomatic_probability,
            waning_enabled=waning_enabled,
        )
        self.define_states(
            ss.BoolState("susceptible", default=True, label="Susceptible"),
            ss.BoolState("exposed", label="Exposed"),
            ss.BoolState("infected", label="Infectious"),
            ss.BoolState("recovered", label="Recovered"),
            ss.FloatArr("rel_sus", default=1.0, label="Relative susceptibility"),
            ss.FloatArr("rel_trans", default=1.0, label="Relative transmission"),
            ss.FloatArr("ti_exposed", label="Time exposed"),
            ss.FloatArr("ti_infected", label="Time infectious"),
            ss.FloatArr("ti_recovered", label="Time recovered"),
            ss.FloatArr("ti_susceptible", label="Time immunity wanes"),
            reset=True,
        )
        self._events_by_ti: dict[int, list[dict[str, Any]]] = defaultdict(list)
        self._all_events: list[dict[str, Any]] = []
        self._seed_uids: list[int] = []
        self._import_counter = 0
        self._import_attempts_by_ti: dict[int, dict[str, int]] = {}
        self._last_attribution_evidence: dict[int, dict[str, Any]] = {}
        self._observation_scheduler = observation_scheduler
        self._event_identity_resolver: Any | None = None
        self._directional_modifier_resolver: Any | None = None
        self._modifier_components: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        self._episode_counts: dict[int, int] = defaultdict(int)
        self._active_episode_by_uid: dict[int, int] = {}
        self._natural_history_by_episode: dict[tuple[int, int], dict[str, Any]] = {}
        return

    def _duration(self, stage: str, uid: int, episode_index: int) -> float:
        return sample_episode_duration(
            self._duration_specs[stage],
            run_seed=int(self.sim.pars.rand_seed),
            stage=stage,
            agent_uid=uid,
            episode_index=episode_index,
        )

    def _transition_index(self, scheduled_time: float) -> int:
        """Return the first verified daily timestep at or after a continuous time."""

        return int(math.ceil(scheduled_time))

    def _date_for_ti(self, time_index: int) -> str:
        return (
            date.fromisoformat(self._current_date()) + timedelta(days=time_index - int(self.ti))
        ).isoformat()

    def _episode_natural_history(self, uid: int) -> dict[str, Any]:
        episode_index = self._active_episode_by_uid.get(uid)
        if episode_index is None:
            raise RuntimeError("infection event has no authoritative natural-history prognosis")
        return self._natural_history_by_episode[(uid, episode_index)]

    def set_modifier_component(
        self, name: str, relative_susceptibility: np.ndarray, relative_transmission: np.ndarray
    ) -> None:
        """Compose independent biological modifiers without one owner erasing another."""

        sus = np.asarray(relative_susceptibility, dtype=float)
        trans = np.asarray(relative_transmission, dtype=float)
        n_people = len(self.rel_sus.raw)
        if len(sus) != n_people or len(trans) != n_people:
            raise ValueError("biological modifier components must cover the Starsim population")
        self._modifier_components[name] = (sus.copy(), trans.copy())
        self.recompose_modifiers()

    def recompose_modifiers(self) -> None:
        self.rel_sus.raw[:] = 1.0
        self.rel_trans.raw[:] = 1.0
        for name in sorted(self._modifier_components):
            sus, trans = self._modifier_components[name]
            self.rel_sus.raw[:] *= sus
            self.rel_trans.raw[:] *= trans

    @property
    def infectious(self) -> Any:
        """Only the infectious state transmits in the core M5 model."""

        return self.infected

    def _ordered_uids(self, uids: np.ndarray, *parts: object) -> np.ndarray:
        seed = int(self.sim.pars.rand_seed)
        ordered = sorted(
            (int(uid) for uid in uids),
            key=lambda uid: (_stable_key(seed, *parts, uid), uid),
        )
        return np.asarray(ordered, dtype=np.int64)

    def _current_date(self) -> str:
        raw = str(self.sim.t.now("str"))[:10].replace(".", "-")
        return date.fromisoformat(raw).isoformat()

    def _record_events(
        self,
        uids: np.ndarray,
        sources: np.ndarray,
        networks: np.ndarray,
        *,
        kind: str,
    ) -> None:
        route_ids = list(self.sim.networks.keys())
        ti = int(self.ti)
        event_date = self._current_date()
        for uid, source, network_index in zip(uids, sources, networks, strict=True):
            target_uid = int(uid)
            source_uid = int(source)
            route = {"seeded": "seeded", "imported": "exogenous_import"}.get(kind, kind)
            if kind == "local":
                index = int(network_index)
                if index < 0 or index >= len(route_ids):
                    raise RuntimeError("Starsim returned an invalid transmission route index")
                route = str(route_ids[index])
            event = {
                "time_index": ti,
                "date": event_date,
                "infected_uid": target_uid,
                "infector_uid": None if source_uid < 0 else source_uid,
                "route_id": route,
                "source_kind": kind,
                "imported": kind == "imported",
                "seeded": kind == "seeded",
                "state": "exposed",
            }
            event.update(self._episode_natural_history(target_uid))
            if self._event_identity_resolver is not None:
                event.update(self._event_identity_resolver(target_uid, ti, "infected"))
                if source_uid >= 0:
                    event.update(self._event_identity_resolver(source_uid, ti, "infector"))
            if kind == "travel_imported":
                event.update(
                    {
                        "travel_acquisition": True,
                        "imported": False,
                        "travel_origin": "external_resident_travel",
                    }
                )
            evidence = self._last_attribution_evidence.get(target_uid)
            if evidence is not None:
                event.update(evidence)
            self._events_by_ti[ti].append(event)
            self._all_events.append(event)
            if self._observation_scheduler is not None:
                self._observation_scheduler.schedule_infection(event)

    def _order_invariant_infect(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Run Starsim's network transmission kernel with order-invariant attribution.

        Starsim evaluates each route independently and then retains the first successful
        candidate for a target.  Candidate occurrence is therefore the union of all successful
        directed edges, while first-route attribution is an insertion-order artefact.  This
        method retains Starsim's ``compute_transmission`` calls and route beta calculation,
        then selects one successful candidate per target with a stable draw proportional to its
        successful edge probability.  The draw is keyed by seed, timestep and target, so route
        insertion order cannot change it.
        """

        ss = _load_starsim()
        betamap = self.validate_beta()
        rel_trans = self.rel_trans.asnew(self.infectious.raw * self.rel_trans.raw, copy=False)
        rel_sus = self.rel_sus.asnew(self.susceptible.raw * self.rel_sus.raw, copy=False)
        route_items = sorted(self.sim.networks.items(), key=lambda item: str(item[0]))
        route_index = {
            str(key): index for index, (key, _route) in enumerate(self.sim.networks.items())
        }
        candidates_by_target: dict[int, list[dict[str, Any]]] = defaultdict(list)

        for nkey, route in route_items:
            route_id = str(nkey)
            nk = ss.standardize_netkey(nkey)
            if isinstance(route, ss.Network):
                if not len(route):
                    continue
                edges = route.edges
                directions = (
                    (edges.p1, edges.p2, betamap[nk][0]),
                    (edges.p2, edges.p1, betamap[nk][1]),
                )
                for src, trg, beta in directions:
                    if not beta:
                        continue
                    disease_beta = (
                        beta.to_prob(self.sim.t.dt) if isinstance(beta, ss.Rate) else beta
                    )
                    beta_per_dt = route.net_beta(disease_beta=disease_beta, disease=self)
                    if np.ndim(beta_per_dt) == 0:
                        beta_per_dt = np.full(len(src), beta_per_dt, dtype=float)
                    if self._directional_modifier_resolver is not None:
                        beta_per_dt = np.asarray(beta_per_dt, dtype=float) * np.asarray(
                            [
                                self._directional_modifier_resolver(
                                    route_id, int(source), int(target), int(self.ti)
                                )
                                for source, target in zip(src, trg, strict=True)
                            ],
                            dtype=float,
                        )
                    randvals = self.trans_rng.rvs(src, trg)
                    target_uids, source_uids = self.compute_transmission(
                        src, trg, rel_trans, rel_sus, beta_per_dt, randvals
                    )
                    for pair, hazard in _match_success_hazards(
                        src,
                        trg,
                        beta_per_dt,
                        rel_trans.raw,
                        rel_sus.raw,
                        target_uids,
                        source_uids,
                    ):
                        candidates_by_target[pair[1]].append(
                            {
                                "route_id": route_id,
                                "network_index": route_index[route_id],
                                "source": pair[0],
                                "hazard": hazard,
                            }
                        )
            elif isinstance(route, ss.Route):
                disease_beta = (
                    betamap[nk][0].to_prob(self.sim.t.dt)
                    if isinstance(betamap[nk][0], ss.Rate)
                    else betamap[nk][0]
                )
                target_uids = route.compute_transmission(
                    rel_sus, rel_trans, disease_beta, disease=self
                )
                for target in target_uids:
                    candidates_by_target[int(target)].append(
                        {
                            "route_id": route_id,
                            "network_index": route_index[route_id],
                            "source": -1,
                            "hazard": max(0.0, min(1.0, float(disease_beta))),
                        }
                    )
            else:
                raise TypeError(
                    f"Cannot compute transmission via route {type(route)}; expected a "
                    "Starsim network or route"
                )

        selected: list[dict[str, Any]] = []
        self._last_attribution_evidence = {}
        seed = int(self.sim.pars.rand_seed)
        for target in sorted(candidates_by_target):
            candidates = sorted(
                candidates_by_target[target],
                key=lambda candidate: (
                    candidate["route_id"],
                    candidate["source"],
                    candidate["network_index"],
                ),
            )
            candidate_route_types = sorted({candidate["route_id"] for candidate in candidates})
            total_hazard = sum(float(candidate["hazard"]) for candidate in candidates)
            draw = (
                int.from_bytes(_stable_key(seed, "attribution", int(self.ti), target)[:8], "big")
                / 2**64
                * total_hazard
            )
            cumulative = 0.0
            chosen = candidates[-1]
            for candidate in candidates:
                cumulative += float(candidate["hazard"])
                if draw < cumulative:
                    chosen = candidate
                    break
            selected.append(chosen | {"target": target})
            self._last_attribution_evidence[target] = {
                "successful_candidate_route_count": len(candidate_route_types),
                "successful_candidate_routes": candidate_route_types,
                "successful_candidate_edge_count": len(candidates),
                "successful_candidate_edge_routes": [
                    candidate["route_id"] for candidate in candidates
                ],
                "successful_candidate_hazards": [
                    float(candidate["hazard"]) for candidate in candidates
                ],
                "attributed_route_id": chosen["route_id"],
            }

        if not selected:
            return (
                np.empty(0, dtype=np.int64),
                np.empty(0, dtype=np.int64),
                np.empty(0, dtype=np.int64),
            )
        return (
            np.asarray([candidate["target"] for candidate in selected], dtype=np.int64),
            np.asarray([candidate["source"] for candidate in selected], dtype=np.int64),
            np.asarray([candidate["network_index"] for candidate in selected], dtype=np.int64),
        )

    def init_post(self) -> np.ndarray:
        """Initialize deterministic seeds after Starsim state arrays exist."""

        super().init_post()
        count = int(self.pars.initial_seed_count)
        if self.pars.initial_prevalence is not None:
            count = round(len(self.sim.people) * float(self.pars.initial_prevalence))
        if count > len(self.sim.people):
            raise ValueError("initial infections cannot exceed the population")
        if count:
            candidates = self._ordered_uids(
                np.asarray(self.sim.people.auids, dtype=np.int64), "seed"
            )
            seeds = candidates[:count]
            sources = np.full(count, -1, dtype=np.int64)
            networks = np.full(count, -1, dtype=np.int64)
            self.set_prognoses(seeds, sources=sources)
            self._record_events(seeds, sources, networks, kind="seeded")
            self._seed_uids = [int(uid) for uid in seeds]
        return np.asarray(self._seed_uids, dtype=np.int64)

    def step_state(self) -> None:
        """Progress exposed, infectious and waning-immunity states."""

        exposed_to_infectious = (self.exposed & (self.ti_infected <= self.ti)).uids
        self.exposed[exposed_to_infectious] = False
        self.infected[exposed_to_infectious] = True

        infectious_to_recovered = (self.infected & (self.ti_recovered <= self.ti)).uids
        self.infected[infectious_to_recovered] = False
        self.recovered[infectious_to_recovered] = True

        if self.pars.waning_enabled:
            recovered_to_susceptible = (self.recovered & (self.ti_susceptible <= self.ti)).uids
            self.recovered[recovered_to_susceptible] = False
            self.susceptible[recovered_to_susceptible] = True

    def _scheduled_imports(self) -> int:
        date_key = self._current_date()
        scheduled = int(self.pars.import_schedule.get(date_key, 0))
        # Keep one Starsim-owned draw per step, including when its rate is zero.
        stochastic = int(self.pars.import_count.rvs(1)[0])
        self._import_counter += 1
        return scheduled + stochastic

    def _select_imports(self, count: int, excluded: np.ndarray) -> np.ndarray:
        if count <= 0:
            self._import_attempts_by_ti[int(self.ti)] = {
                "exposure_attempts": 0,
                "successful_acquisitions": 0,
            }
            return np.empty(0, dtype=np.int64)
        all_uids = np.asarray(self.sim.people.auids, dtype=np.int64)
        available = all_uids[np.asarray(self.susceptible.raw[all_uids], dtype=bool)]
        if len(excluded):
            available = available[~np.isin(available, excluded)]
        ordered = self._ordered_uids(
            available, "import", self._import_counter, self._current_date()
        )
        # The configured pressure is a number of exposure attempts, not a
        # guaranteed number of imported acquisitions.  Draw the attempted
        # people first, independently of vaccine state, then apply relative
        # susceptibility to each attempt.  This prevents partial protection
        # from merely changing identities while back-filling the requested
        # count from the rest of the susceptible population.
        attempts = ordered[: min(count, len(ordered))]
        accepted = [
            int(uid)
            for uid in attempts
            if int.from_bytes(
                _stable_key(
                    int(self.sim.pars.rand_seed),
                    "import-acquisition",
                    self._import_counter,
                    self._current_date(),
                    int(uid),
                )[:8],
                "big",
            )
            / 2**64
            < max(0.0, min(1.0, float(self.rel_sus.raw[int(uid)])))
        ]
        self._import_attempts_by_ti[int(self.ti)] = {
            "exposure_attempts": len(attempts),
            "successful_acquisitions": len(accepted),
        }
        return np.asarray(accepted, dtype=np.int64)

    def step(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Run Starsim network transmission and generic exogenous imports."""

        local_cases, local_sources, local_networks = self._order_invariant_infect()
        local_cases = np.asarray(local_cases, dtype=np.int64)
        local_sources = np.asarray(local_sources, dtype=np.int64)
        local_networks = np.asarray(local_networks, dtype=np.int64)
        imported = self._select_imports(self._scheduled_imports(), local_cases)

        if len(local_cases) or len(imported):
            all_cases = np.concatenate((local_cases, imported)).astype(np.int64, copy=False)
            all_sources = np.concatenate(
                (local_sources, np.full(len(imported), -1, dtype=np.int64))
            )
            self.set_outcomes(all_cases, all_sources)
        if len(local_cases):
            self._record_events(local_cases, local_sources, local_networks, kind="local")
        if len(imported):
            import_sources = np.full(len(imported), -1, dtype=np.int64)
            import_networks = np.full(len(imported), -1, dtype=np.int64)
            self._record_events(imported, import_sources, import_networks, kind="imported")
        return local_cases, local_sources, local_networks

    def set_outcomes(self, uids: np.ndarray, sources: np.ndarray | None = None) -> None:
        """Apply the generic prognosis to every age, including age-zero residents."""

        self.set_prognoses(uids, sources)

    def set_prognoses(self, uids: np.ndarray, sources: np.ndarray | None = None) -> None:
        """Assign the exposed state and Starsim-compatible transition times."""

        super().set_prognoses(uids, sources)
        if not len(uids):
            return
        self.susceptible[uids] = False
        self.exposed[uids] = True
        self.infected[uids] = False
        self.recovered[uids] = False
        for raw_uid in np.asarray(uids, dtype=np.int64):
            uid = int(raw_uid)
            episode_index = self._episode_counts[uid]
            self._episode_counts[uid] += 1
            self._active_episode_by_uid[uid] = episode_index
            latent_draw = self._duration("latent", uid, episode_index)
            infectious_draw = self._duration("infectious", uid, episode_index)
            exposed_ti = int(self.ti)
            infectious_ti = self._transition_index(exposed_ti + latent_draw)
            recovered_ti = self._transition_index(infectious_ti + infectious_draw)
            self.ti_exposed[uid] = exposed_ti
            self.ti_infected[uid] = infectious_ti
            self.ti_recovered[uid] = recovered_ti
            immunity_draw: float | None = None
            susceptible_ti: int | None = None
            if self.pars.waning_enabled:
                immunity_draw = self._duration("immunity", uid, episode_index)
                susceptible_ti = self._transition_index(recovered_ti + immunity_draw)
                self.ti_susceptible[uid] = susceptible_ti
            else:
                self.ti_susceptible[uid] = np.nan
            symptomatic_draw = (
                int.from_bytes(
                    _stable_key(
                        int(self.sim.pars.rand_seed),
                        "natural-history-symptomatic",
                        "1.1",
                        uid,
                        episode_index,
                    )[:8],
                    byteorder="big",
                    signed=False,
                )
                / 2**64
            )
            symptomatic = symptomatic_draw < float(self.pars.symptomatic_probability)
            self._natural_history_by_episode[(uid, episode_index)] = {
                "natural_history_episode_index": episode_index,
                "infection_date": self._date_for_ti(exposed_ti),
                "infectious_start_date": self._date_for_ti(infectious_ti),
                "symptomatic": symptomatic,
                "symptom_onset_date": (self._date_for_ti(infectious_ti) if symptomatic else None),
                "recovery_date": self._date_for_ti(recovered_ti),
                "susceptibility_return_date": (
                    self._date_for_ti(susceptible_ti) if susceptible_ti is not None else None
                ),
                "latent_duration_draw_days": latent_draw,
                "infectious_duration_draw_days": infectious_draw,
                "immunity_duration_draw_days": immunity_draw,
            }

    def reset_person_state(self, uids: np.ndarray) -> None:
        """Reset reusable temporary slots to a known non-participating baseline."""

        uids = np.asarray(uids, dtype=np.int64)
        for uid in uids:
            self._active_episode_by_uid.pop(int(uid), None)
        for state in (self.susceptible, self.exposed, self.infected, self.recovered):
            state[uids] = False
        for timer in (
            self.ti_exposed,
            self.ti_infected,
            self.ti_recovered,
            self.ti_susceptible,
        ):
            timer[uids] = np.nan
        for name, (sus, trans) in self._modifier_components.items():
            sus[uids] = 1.0
            trans[uids] = 1.0
            self._modifier_components[name] = (sus, trans)
        self.recompose_modifiers()

    def initialize_arrival_state(
        self, uids: np.ndarray, state: str, *, recovered_days_since: int = 0
    ) -> None:
        """Initialize a temporary traveller without changing resident identity.

        This is deliberately a small generic state initializer.  Visitor
        prevalence is a scenario control, not a clinical diagnosis model.
        """

        if state not in {"susceptible", "exposed", "infectious", "recovered"}:
            raise ValueError(f"unknown arrival disease state: {state}")
        uids = np.asarray(uids, dtype=np.int64)
        if not len(uids):
            return
        self.reset_person_state(uids)
        if state == "susceptible":
            self.susceptible[uids] = True
            self.exposed[uids] = False
            self.infected[uids] = False
            self.recovered[uids] = False
            return
        if state == "recovered":
            self.susceptible[uids] = False
            self.exposed[uids] = False
            self.infected[uids] = False
            self.recovered[uids] = True
            self.ti_recovered[uids] = self.ti - recovered_days_since
            if self.pars.waning_enabled:
                episode_indices = {int(uid): self._episode_counts[int(uid)] for uid in uids}
                remaining = np.asarray(
                    [
                        max(
                            0.0,
                            self._duration("immunity", int(uid), episode_indices[int(uid)])
                            - recovered_days_since,
                        )
                        for uid in uids
                    ],
                    dtype=float,
                )
                for uid in uids:
                    self._episode_counts[int(uid)] += 1
                self.ti_susceptible[uids] = self.ti + remaining
            else:
                self.ti_susceptible[uids] = np.nan
            return
        self.set_prognoses(uids, sources=np.full(len(uids), -1, dtype=np.int64))
        if state == "infectious":
            self.exposed[uids] = False
            self.infected[uids] = True
            self.ti_infected[uids] = self.ti
            for raw_uid in uids:
                uid = int(raw_uid)
                episode_index = self._active_episode_by_uid[uid]
                recovered_ti = self._transition_index(
                    int(self.ti) + self._duration("infectious", uid, episode_index)
                )
                self.ti_recovered[uid] = recovered_ti
                history = self._natural_history_by_episode[(uid, episode_index)]
                history["infectious_start_date"] = self._date_for_ti(int(self.ti))
                history["symptom_onset_date"] = (
                    self._date_for_ti(int(self.ti)) if history["symptomatic"] else None
                )
                history["recovery_date"] = self._date_for_ti(recovered_ti)
            if self.pars.waning_enabled:
                for raw_uid in uids:
                    uid = int(raw_uid)
                    episode_index = self._active_episode_by_uid[uid]
                    susceptible_ti = self._transition_index(
                        float(self.ti_recovered[uid])
                        + self._duration("immunity", uid, episode_index)
                    )
                    self.ti_susceptible[uid] = susceptible_ti
                    self._natural_history_by_episode[(uid, episode_index)][
                        "susceptibility_return_date"
                    ] = self._date_for_ti(susceptible_ti)

    def init_results(self) -> None:
        """Add explicit seed/import/local and total-infection result series."""

        ss = _load_starsim()
        super().init_results()
        self.define_results(
            ss.Result("new_seeded", dtype=int, scale=True, label="New seeded infections"),
            ss.Result("new_imported", dtype=int, scale=True, label="New imported infections"),
            ss.Result("new_local", dtype=int, scale=True, label="New local infections"),
            ss.Result("cum_total_infections", dtype=int, scale=True, label="Cumulative infections"),
            ss.Result("attack_rate", dtype=float, scale=False, label="Cumulative attack rate"),
        )

    def update_results(self) -> None:
        """Write state counts and event-conserving daily infection totals."""

        super().update_results()
        ti = int(self.ti)
        events = self._events_by_ti.get(ti, [])
        seeded = sum(bool(event["seeded"]) for event in events)
        imported = sum(bool(event["imported"]) for event in events)
        local = sum(event["source_kind"] == "local" for event in events)
        non_seeded = imported + local
        previous_total = int(round(float(self.results.cum_total_infections[ti - 1]))) if ti else 0
        previous_non_seeded = int(round(float(self.results.cum_infections[ti - 1]))) if ti else 0
        self.results.new_seeded[ti] = seeded
        self.results.new_imported[ti] = imported
        self.results.new_local[ti] = local
        self.results.new_infections[ti] = non_seeded
        self.results.cum_infections[ti] = previous_non_seeded + non_seeded
        self.results.cum_total_infections[ti] = previous_total + seeded + non_seeded
        self.results.attack_rate[ti] = float(self.results.cum_total_infections[ti]) / len(
            self.sim.people
        )

    def finalize_results(self) -> None:
        """Scale results without the base infection class recomputing cumulative totals."""

        ss = _load_starsim()
        ss.Module.finalize_results(self)

    def step_die(self, uids: np.ndarray) -> None:
        """No disease deaths are implemented in the bounded M5 core."""

        for state in ("susceptible", "exposed", "infected", "recovered"):
            self.state_dict[state][uids] = False
