"""The Milestone 4 boundary between JOS route tables and Starsim 3.5.2."""

from __future__ import annotations

import contextlib
import io
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import numpy as np

from .network_generator import GeneratedNetworks

SUPPORTED_STARSIM_VERSION = "3.5.2"


class PlainMetadataBoundary:
    """Expose a plain mapping without making it part of Starsim discovery.

    sciris descends through an object's ``__dict__`` or ``__slots__``.  The
    mapping therefore lives in a closure, retained by the boundary's sole
    slot, and is returned only through this accessor.  sciris sees the
    callable slot but does not inspect Python closure cells.
    """

    __slots__ = ("_get_value",)

    def __init__(self, value: Any) -> None:
        self._get_value = lambda: value

    @property
    def value(self) -> Any:
        """Return the original mapping for its owning JOS consumer."""

        return self._get_value()


def _load_starsim() -> Any:
    """Import and verify the exact Starsim version used at the adapter boundary."""

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        import starsim as ss

    actual_version = getattr(ss, "__version__", None)
    if actual_version != SUPPORTED_STARSIM_VERSION:
        raise RuntimeError(
            f"Unsupported Starsim version {actual_version!r}; "
            f"Milestone 4 requires {SUPPORTED_STARSIM_VERSION}"
        )
    return ss


def agent_uid_mapping(generated: GeneratedNetworks) -> dict[str, int]:
    """Map stable JOS agent IDs to Starsim's zero-based UIDs exactly."""

    return {agent_id: index for index, agent_id in enumerate(generated.agent_ids)}


def _jos_demographics(generated: GeneratedNetworks) -> tuple[np.ndarray, np.ndarray]:
    """Return exact JOS age and female-state arrays in Starsim UID order."""

    m2_by_agent = {row["agent_id"]: row for row in generated.m2_input.residents}
    if set(m2_by_agent) != set(generated.agent_ids):
        raise ValueError("JOS demographic and agent ID universes do not match")
    ages = np.asarray(
        [m2_by_agent[agent_id]["age"] for agent_id in generated.agent_ids], dtype=float
    )
    female = np.asarray(
        [m2_by_agent[agent_id]["sex"] == "female" for agent_id in generated.agent_ids], dtype=bool
    )
    return ages, female


def _apply_jos_demographics(sim: Any, generated: GeneratedNetworks) -> None:
    """Replace Starsim's stochastic defaults with the exact synthetic JOS identities."""

    ages, female = _jos_demographics(generated)
    sim.people.age[:] = ages
    sim.people.female[:] = female
    if not np.array_equal(np.asarray(sim.people.age), ages):
        raise RuntimeError("Starsim ages do not match the JOS population")
    if not np.array_equal(np.asarray(sim.people.female), female):
        raise RuntimeError("Starsim sex state does not match the JOS population")


def _apply_demographics_arrays(sim: Any, ages: np.ndarray, female: np.ndarray) -> None:
    """Apply an explicit resident-plus-temporary demographic contract."""

    if len(ages) != len(sim.people) or len(female) != len(sim.people):
        raise ValueError("explicit demographic arrays must match the Starsim population size")
    sim.people.age[:] = ages
    sim.people.female[:] = female
    if not np.array_equal(np.asarray(sim.people.age), ages):
        raise RuntimeError("Starsim ages do not match the explicit JOS population")
    if not np.array_equal(np.asarray(sim.people.female), female):
        raise RuntimeError("Starsim sex state does not match the explicit JOS population")


def _edge_arrays(
    ss: Any,
    edges: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    uid_by_agent_id: dict[str, int],
) -> dict[str, np.ndarray]:
    try:
        p1 = np.asarray([uid_by_agent_id[edge["p1"]] for edge in edges], dtype=np.int64)
        p2 = np.asarray([uid_by_agent_id[edge["p2"]] for edge in edges], dtype=np.int64)
    except KeyError as exc:
        raise ValueError(f"route edge references unknown JOS agent: {exc.args[0]}") from exc
    beta = np.asarray([edge["weight"] for edge in edges], dtype=float)
    return {"p1": ss.uids(p1), "p2": ss.uids(p2), "beta": beta}


class JOSDynamicNetworkMixin:
    """Shared daily replacement hook for calendar and sampled JOS routes."""

    sim: Any
    edges: Any
    _snapshot_provider: Callable[[date], list[dict[str, Any]]]
    _uid_by_agent_id: PlainMetadataBoundary

    def _replace_edges(self) -> None:
        raw_date = str(self.sim.t.now("str"))[:10].replace(".", "-")
        snapshot_date = date.fromisoformat(raw_date)
        edges = self._snapshot_provider(snapshot_date)
        arrays = _edge_arrays(_load_starsim(), edges, self._uid_by_agent_id.value)
        self.edges.p1 = arrays["p1"]
        self.edges.p2 = arrays["p2"]
        self.edges.beta = arrays["beta"]
        self.edges.dur = np.ones(len(edges), dtype=float)

    def add_pairs(self) -> None:
        self._replace_edges()

    def step(self) -> None:
        # Starsim's loop calls network.step() once per daily timestep.  Replacing
        # the complete daily snapshot keeps JOS persistence/calendar semantics
        # explicit while using the supported DynamicNetwork lifecycle hook.
        self._replace_edges()


def _make_dynamic_network(
    ss: Any,
    route_id: str,
    provider: Callable[[date], list[dict[str, Any]]],
    uid_by_agent_id: dict[str, int],
) -> Any:
    class JOSDynamicNetwork(JOSDynamicNetworkMixin, ss.DynamicNetwork):
        def __init__(self) -> None:
            super().__init__(name=route_id, label=route_id)
            self._snapshot_provider = provider
            self._uid_by_agent_id = PlainMetadataBoundary(uid_by_agent_id)

        def init_post(self, add_pairs: bool = True) -> None:
            super().init_post(add_pairs=False)
            self.add_pairs()

    return JOSDynamicNetwork()


def _make_static_network(
    ss: Any,
    route_id: str,
    arrays: dict[str, np.ndarray],
) -> Any:
    class JOSStaticNetwork(ss.Network):
        def step(self) -> None:
            return None

    return JOSStaticNetwork(name=route_id, **arrays, label=route_id)


def build_starsim_networks(generated: GeneratedNetworks) -> list[Any]:
    """Convert all configured JOS routes into exact Starsim network objects."""

    uid_by_agent_id = agent_uid_mapping(generated)
    return _build_starsim_networks_for_mapping(generated, uid_by_agent_id)


def _build_starsim_networks_for_mapping(
    generated: GeneratedNetworks, uid_by_agent_id: dict[str, int]
) -> list[Any]:
    """Build networks using a caller-owned total identity mapping."""

    ss = _load_starsim()
    networks: list[Any] = []
    initial_date = generated.config.start_date
    for route_id, spec in sorted(generated.route_specs.items()):
        needs_daily_update = (
            route_id in generated._dynamic_builders or spec["active_calendar"] != "always"
        )
        if needs_daily_update:

            def provider(snapshot_date: date, route_id: str = route_id) -> list[dict[str, Any]]:
                return list(generated.route_snapshot(route_id, snapshot_date).edges)

            networks.append(_make_dynamic_network(ss, route_id, provider, uid_by_agent_id))
        else:
            edges = generated.route_snapshot(route_id, initial_date).edges
            arrays = _edge_arrays(ss, edges, uid_by_agent_id)
            networks.append(_make_static_network(ss, route_id, arrays))
    return networks


def build_starsim_sim(
    generated: GeneratedNetworks,
    *,
    start_date: date | None = None,
    duration_days: int = 2,
    seed: int | None = None,
) -> Any:
    """Build an initialized network-only Starsim Sim for compatibility checks."""

    if duration_days <= 0:
        raise ValueError("duration_days must be positive")
    ss = _load_starsim()
    start = start_date or generated.config.start_date
    # ``duration_days`` is the number of dated output points, including the
    # start date.  Starsim's stop date is inclusive, so the final point is
    # start + duration_days - 1 (C5 canonical horizon contract).
    stop = start + timedelta(days=duration_days - 1)
    sim = ss.Sim(
        people=ss.People(len(generated.agent_ids)),
        start=start.isoformat(),
        stop=stop.isoformat(),
        dt=ss.days(1),
        rand_seed=generated.config.seed if seed is None else seed,
        networks=build_starsim_networks(generated),
        verbose=0,
        copy_inputs=False,
    )
    sim.init()
    _apply_jos_demographics(sim, generated)
    return sim


def build_starsim_disease_sim(
    generated: GeneratedNetworks,
    disease: Any,
    *,
    start_date: date | None = None,
    duration_days: int = 2,
    seed: int | None = None,
    interventions: list[Any] | tuple[Any, ...] | None = None,
) -> Any:
    """Build an initialized Starsim simulation using the existing JOS routes."""

    if duration_days <= 0:
        raise ValueError("duration_days must be positive")
    ss = _load_starsim()
    start = start_date or generated.config.start_date
    # Starsim executes both start and stop.  Keep the public JOS control as a
    # count of dated output points rather than elapsed intervals.
    stop = start + timedelta(days=duration_days - 1)
    sim = ss.Sim(
        people=ss.People(len(generated.agent_ids)),
        start=start.isoformat(),
        stop=stop.isoformat(),
        dt=ss.days(1),
        rand_seed=generated.config.seed if seed is None else seed,
        networks=build_starsim_networks(generated),
        diseases=disease,
        interventions=list(interventions or []),
        verbose=0,
        copy_inputs=False,
    )
    sim.init()
    _apply_jos_demographics(sim, generated)
    return sim


def build_starsim_travel_sim(
    generated: GeneratedNetworks,
    disease: Any,
    *,
    agent_ids: list[str],
    ages: np.ndarray,
    female: np.ndarray,
    start_date: date | None = None,
    duration_days: int = 2,
    seed: int | None = None,
    interventions: list[Any] | tuple[Any, ...] | None = None,
) -> Any:
    """Build Starsim with a preallocated resident-plus-visitor slot pool.

    M4 remains the immutable parent artifact.  The supplied ``generated``
    view adds only temporary route snapshots and uses an explicit identity
    mapping for the larger Starsim population.
    """

    if duration_days <= 0:
        raise ValueError("duration_days must be positive")
    if len(agent_ids) != len(ages) or len(agent_ids) != len(female):
        raise ValueError("travel identities and demographics must have equal lengths")
    ss = _load_starsim()
    start = start_date or generated.config.start_date
    stop = start + timedelta(days=duration_days - 1)
    uid_by_agent_id = {agent_id: index for index, agent_id in enumerate(agent_ids)}
    sim = ss.Sim(
        people=ss.People(len(agent_ids)),
        start=start.isoformat(),
        stop=stop.isoformat(),
        dt=ss.days(1),
        rand_seed=generated.config.seed if seed is None else seed,
        networks=_build_starsim_networks_for_mapping(generated, uid_by_agent_id),
        diseases=disease,
        interventions=list(interventions or []),
        verbose=0,
        copy_inputs=False,
    )
    sim.init()
    _apply_demographics_arrays(sim, ages, female)
    return sim


def run_starsim_network_compatibility(
    generated: GeneratedNetworks, *, duration_days: int = 2
) -> dict[str, Any]:
    """Initialize and execute the route stack without adding disease biology."""

    ss = _load_starsim()
    sim = build_starsim_sim(generated, duration_days=duration_days)
    initial_counts = {name: len(network) for name, network in sim.networks.items()}
    sim.run(verbose=0)
    final_counts = {name: len(network) for name, network in sim.networks.items()}
    return {
        "starsim_version": ss.__version__,
        "n_agents": len(generated.agent_ids),
        "duration_days": duration_days,
        "network_count": len(sim.networks),
        "initial_edge_counts": initial_counts,
        "final_edge_counts": final_counts,
        "executed_without_disease": True,
    }
