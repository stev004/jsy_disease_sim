from pathlib import Path

import pytest

from jersey_outbreak.network_generator import GeneratedNetworks, generate_networks
from jersey_outbreak.network_schemas import NetworkGenerationConfig
from jersey_outbreak.observation import load_observation_config
from jersey_outbreak.observation_schemas import ObservationConfig
from jersey_outbreak.outbreak_runner import default_run_config, load_parameter_set, run_outbreak
from jersey_outbreak.outbreak_schemas import OutbreakRunConfig, RespiratoryParameterSet
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

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def m6_network(tmp_path_factory: pytest.TempPathFactory) -> GeneratedNetworks:
    output = tmp_path_factory.mktemp("m6-inputs")
    population = generate_population(ROOT, PopulationGenerationConfig(mode="ci", seed=123))
    population_artifact = write_population_artifact(population, ROOT, output / "populations")
    m2_input = load_m2_population_artifact(ROOT, population_artifact.artifact_directory)
    structure = generate_structure(ROOT, StructureGenerationConfig(mode="ci", seed=123), m2_input)
    structure_artifact = write_structure_artifact(structure, ROOT, output / "structures", m2_input)
    m3_input = load_m3_structure_artifact(ROOT, structure_artifact.artifact_directory)
    return generate_networks(NetworkGenerationConfig(mode="ci", seed=123), m2_input, m3_input)


@pytest.fixture(scope="session")
def m6_parameters() -> RespiratoryParameterSet:
    return load_parameter_set(ROOT)


@pytest.fixture(scope="session")
def m6_base_config(
    m6_parameters: RespiratoryParameterSet,
) -> OutbreakRunConfig:
    return default_run_config("ci", 123, m6_parameters, duration_days=8)


@pytest.fixture(scope="session")
def m6_observation_config() -> ObservationConfig:
    return load_observation_config(ROOT)


@pytest.fixture(scope="session")
def m6_latent_run(
    m6_network: GeneratedNetworks,
    m6_base_config: OutbreakRunConfig,
    m6_parameters: RespiratoryParameterSet,
):
    return run_outbreak(m6_network, m6_base_config, m6_parameters)
