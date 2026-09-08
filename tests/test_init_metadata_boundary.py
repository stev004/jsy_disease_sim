"""PERF-1: keep plain JOS metadata outside Starsim recursive discovery."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import sciris as sc
import starsim as ss

from jersey_outbreak.network_generator import generate_networks
from jersey_outbreak.network_schemas import NetworkGenerationConfig
from jersey_outbreak.observation import load_observation_config
from jersey_outbreak.observation_scheduler import ObservationScheduler
from jersey_outbreak.outbreak_runner import default_run_config, load_parameter_set
from jersey_outbreak.population_artifacts import write_population_artifact
from jersey_outbreak.population_generator import generate_population
from jersey_outbreak.population_schemas import PopulationGenerationConfig
from jersey_outbreak.population_structure_artifacts import (
    load_m2_population_artifact,
    load_m3_structure_artifact,
    write_structure_artifact,
)
from jersey_outbreak.population_structure_generator import generate_structure
from jersey_outbreak.population_structure_schemas import StructureGenerationConfig
from jersey_outbreak.respiratory import RespiratorySEIRS
from jersey_outbreak.starsim_adapter import (
    PlainMetadataBoundary,
    _edge_arrays,
    build_starsim_disease_sim,
)

ROOT = Path(__file__).resolve().parents[1]

# Recorded from origin/main a3caccf2d37d2462880e6ae349f042d4d9893501 with the
# same CI/123/7-day builder in /tmp/jos_perf1_inspect.py before this change.
BASE_DISTRIBUTIONS = (
    (
        "pars_diseases_respiratoryseirs_import_count",
        511688290,
        "pars_diseases_respiratoryseirs_import_count",
    ),
    (
        "diseases_respiratoryseirs_trans_rng_dists_0",
        531984607,
        "diseases_respiratoryseirs_trans_rng_dists_0",
    ),
    (
        "diseases_respiratoryseirs_trans_rng_dists_1",
        897350529,
        "diseases_respiratoryseirs_trans_rng_dists_1",
    ),
    ("people_states_age_default", 671341605, "people_states_age_default"),
    ("people_states_female_default", 670325783, "people_states_female_default"),
)
BASE_RATE_PATHS = {
    "bus": (),
    "care_resident": (),
    "care_staff": (),
    "community_indoor": (),
    "community_outdoor": (),
    "household": (),
    "school_class": (),
    "school_cross_class": (),
    "shared_vehicle": (),
    "workplace_team": (),
    "workplace_transient": (),
    "respiratoryseirs": (),
}


def _build_initialized_sim(tmp_path):
    population = generate_population(ROOT, PopulationGenerationConfig(mode="ci", seed=123))
    population_artifact = write_population_artifact(population, ROOT, tmp_path / "m2")
    m2_input = load_m2_population_artifact(ROOT, population_artifact.artifact_directory)
    structure = generate_structure(ROOT, StructureGenerationConfig(mode="ci", seed=123), m2_input)
    structure_artifact = write_structure_artifact(structure, ROOT, tmp_path / "m3", m2_input)
    m3_input = load_m3_structure_artifact(ROOT, structure_artifact.artifact_directory)
    generated = generate_networks(NetworkGenerationConfig(mode="ci", seed=123), m2_input, m3_input)
    parameters = load_parameter_set(ROOT)
    config = default_run_config("ci", 123, parameters, duration_days=7)
    route_betas = {
        route_id: config.beta * float(config.route_multipliers[route_id])
        for route_id in generated.route_specs
    }
    agent_id_by_uid = {uid: agent_id for uid, agent_id in enumerate(generated.agent_ids)}
    resident_by_agent_id = {row["agent_id"]: row for row in generated.m3_input.resident_structure}
    scheduler = ObservationScheduler(
        latent_seed=config.seed,
        start_date=config.start_date,
        config=load_observation_config(ROOT),
        agent_id_by_uid=agent_id_by_uid,
        resident_by_agent_id=resident_by_agent_id,
    )
    disease = RespiratorySEIRS(
        route_betas=route_betas,
        initial_seed_count=config.initial_seed_count,
        initial_prevalence=config.initial_prevalence,
        import_schedule=config.import_schedule,
        import_rate_per_day=config.import_rate_per_day,
        latent_duration=config.latent_duration,
        infectious_duration=config.infectious_duration,
        immunity_duration=config.immunity_duration,
        symptomatic_probability=config.symptomatic_probability,
        waning_enabled=config.waning_enabled,
        observation_scheduler=scheduler,
    )
    sim = build_starsim_disease_sim(
        generated,
        disease,
        start_date=config.start_date,
        duration_days=config.duration_days,
        seed=config.seed,
    )
    return sim, generated, config, scheduler, agent_id_by_uid, resident_by_agent_id


def test_metadata_boundary_preserves_discovery_and_consumers(tmp_path) -> None:
    sim, generated, config, scheduler, agent_id_by_uid, resident_by_agent_id = (
        _build_initialized_sim(tmp_path)
    )
    uid_by_agent_id = {agent_id: uid for uid, agent_id in agent_id_by_uid.items()}

    distributions = tuple(
        (str(key), int(dist.seed), str(dist.trace)) for key, dist in sim.dists.dists.items()
    )
    assert distributions == BASE_DISTRIBUTIONS
    assert int(sim.pars.rand_seed) == 123

    rate_paths = {}
    for name, module in [*sim.networks.items(), *sim.diseases.items()]:
        found = sc.search(module, type=ss.Rate, skip=dict(keys=["sim", "module"]))
        rate_paths[str(name)] = tuple(str(key) for key in found)
    assert rate_paths == BASE_RATE_PATHS

    # This uses 104,540 entries, the full-mode resident metadata cardinality.
    probe_dist = ss.random()
    full_size_boundary = PlainMetadataBoundary(
        {f"agent-{index}": probe_dist for index in range(104_540)}
    )
    started = time.perf_counter()
    assert not sc.search(full_size_boundary, type=ss.Dist)
    elapsed = time.perf_counter() - started
    assert elapsed < 0.010
    assert not hasattr(full_size_boundary, "__dict__")

    for route_id, network in sim.networks.items():
        if not hasattr(network, "_replace_edges"):
            continue
        assert isinstance(network._uid_by_agent_id, PlainMetadataBoundary)
        network._replace_edges()
        expected = _edge_arrays(
            ss,
            generated.route_snapshot(route_id, config.start_date).edges,
            uid_by_agent_id,
        )
        for name, expected_array in expected.items():
            actual = np.asarray(getattr(network.edges, name))
            assert actual.dtype == expected_array.dtype
            assert np.array_equal(actual, expected_array)

    sampled_uid = next(iter(agent_id_by_uid))
    sampled_agent_id = scheduler.agent_id_by_uid[sampled_uid]
    assert sampled_agent_id == agent_id_by_uid[sampled_uid]
    assert (
        scheduler.resident_by_agent_id[sampled_agent_id] is resident_by_agent_id[sampled_agent_id]
    )
