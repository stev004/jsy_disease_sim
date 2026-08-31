import json
import math
from datetime import date
from pathlib import Path

import numpy as np
import pytest

from jersey_outbreak.network_generator import generate_networks
from jersey_outbreak.network_schemas import NetworkGenerationConfig
from jersey_outbreak.outbreak_artifacts import write_outbreak_artifact
from jersey_outbreak.outbreak_runner import (
    default_run_config,
    load_parameter_set,
    run_outbreak,
)
from jersey_outbreak.outbreak_schemas import (
    ROUTE_IDS,
    DurationSpecification,
    OutbreakRunConfig,
)
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
from jersey_outbreak.respiratory import RespiratorySEIRS, sample_episode_duration

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def outbreak_network(tmp_path_factory: pytest.TempPathFactory):
    output = tmp_path_factory.mktemp("m5-inputs")
    population = generate_population(ROOT, PopulationGenerationConfig(mode="ci", seed=123))
    population_artifact = write_population_artifact(population, ROOT, output / "populations")
    m2_input = load_m2_population_artifact(ROOT, population_artifact.artifact_directory)
    structure = generate_structure(ROOT, StructureGenerationConfig(mode="ci", seed=123), m2_input)
    structure_artifact = write_structure_artifact(structure, ROOT, output / "structures", m2_input)
    m3_input = load_m3_structure_artifact(ROOT, structure_artifact.artifact_directory)
    return generate_networks(NetworkGenerationConfig(mode="ci", seed=123), m2_input, m3_input)


@pytest.fixture(scope="module")
def parameters():
    return load_parameter_set(ROOT)


def _config(**kwargs) -> OutbreakRunConfig:
    values = dict(mode="ci", seed=123, duration_days=8)
    values.update(kwargs)
    return OutbreakRunConfig(**values)


def _duration(mean_days: float, *, family: str = "constant", cv: float | None = None):
    return DurationSpecification(
        family=family,
        mean_days=mean_days,
        cv=cv,
        status="scenario_assumption",
        notes="Controlled M11-A test duration.",
    )


def test_beta_zero_and_no_seed_are_disease_free(outbreak_network, parameters) -> None:
    zero_beta = run_outbreak(
        outbreak_network,
        _config(beta=0.0, initial_seed_count=1),
        parameters,
    )
    assert zero_beta.diagnostics["attribution"]["local"] == 0
    assert zero_beta.diagnostics["attribution"]["imported"] == 0
    assert zero_beta.diagnostics["states"]["conserved"] is True

    disease_free = run_outbreak(
        outbreak_network,
        _config(beta=0.08, initial_seed_count=0),
        parameters,
    )
    assert disease_free.diagnostics["attribution"]["total_events"] == 0
    assert all(row["susceptible"] == 3000 for row in disease_free.daily_epidemic)


def test_parameter_bundle_keeps_demo_assumptions_and_deferred_families_explicit(parameters) -> None:
    assert parameters.module == "generic_respiratory_seirs"
    assert set(parameters.route_multipliers) == set(ROUTE_IDS)
    assert all(entry.status == "scenario_assumption" for entry in parameters.parameters.values())
    assert parameters.parameters["symptom_probability"].value == 0.6
    assert all(spec.family == "constant" for spec in parameters.durations.values())
    assert parameters.numeric("immunity_waning_enabled") == 0.0
    assert parameters.parameters["severe_progression"].value is None
    assert parameters.parameters["disease_death_probability"].value is None
    assert parameters.parameters["transmission_beta"].source_ids == []


def test_imports_and_route_attribution_conserve_events(outbreak_network, parameters) -> None:
    result = run_outbreak(
        outbreak_network,
        _config(
            beta=0.08,
            initial_seed_count=0,
            import_schedule={"2025-01-06": 2},
        ),
        parameters,
    )
    attribution = result.diagnostics["attribution"]
    assert attribution["imported"] == 2
    assert attribution["conserved"] is True
    assert attribution["all_local_events_have_route"] is True
    assert attribution["all_local_events_have_infector"] is True
    route_ids = {row["route_id"] for row in result.daily_route}
    assert set(ROUTE_IDS) <= route_ids
    assert {"exogenous_import", "seeded"} <= route_ids
    assert sum(row["new_imported_infections"] for row in result.daily_route) == 2
    import_rows = [row for row in result.daily_route if row["route_id"] == "exogenous_import"]
    assert import_rows[-1]["cumulative_infections"] == 2


def test_recovery_and_configurable_waning(outbreak_network, parameters) -> None:
    result = run_outbreak(
        outbreak_network,
        _config(
            beta=0.0,
            initial_seed_count=1,
            duration_days=7,
            latent_duration=_duration(1.0),
            infectious_duration=_duration(2.0),
            immunity_duration=_duration(1.0),
            waning_enabled=True,
        ),
        parameters,
    )
    assert result.daily_epidemic[0]["exposed"] == 1
    assert result.daily_epidemic[1]["infectious"] == 1
    assert result.daily_epidemic[3]["recovered"] == 1
    assert result.daily_epidemic[4]["susceptible"] == 3000
    assert result.daily_epidemic[0]["cumulative_incidence_per_capita"] == pytest.approx(1 / 3000)
    assert result.daily_epidemic[0]["ever_infected_fraction"] == pytest.approx(1 / 3000)
    assert (
        result.daily_epidemic[0]["attack_rate"]
        == result.daily_epidemic[0]["cumulative_incidence_per_capita"]
    )
    assert result.diagnostics["output_semantics"]["attack_rate"].startswith("deprecated")

    disabled = run_outbreak(
        outbreak_network,
        _config(
            beta=0.0,
            initial_seed_count=1,
            duration_days=7,
            latent_duration=_duration(1.0),
            infectious_duration=_duration(1.0),
            immunity_duration=_duration(1.0),
            waning_enabled=False,
        ),
        parameters,
    )
    assert disabled.daily_epidemic[-1]["recovered"] == 1
    assert disabled.daily_epidemic[-1]["susceptible"] == 2999


def test_same_seed_reproduces_disease_and_outputs(outbreak_network, parameters) -> None:
    first = run_outbreak(outbreak_network, _config(), parameters)
    second = run_outbreak(outbreak_network, _config(), parameters)
    assert first.logical_content_hash == second.logical_content_hash
    assert first.transmission_events == second.transmission_events
    assert first.daily_epidemic == second.daily_epidemic
    assert first.diagnostics["network_immutability"]["passed"] is True


def test_gamma_duration_fixture_has_declared_moments_and_episode_identity() -> None:
    specification = _duration(4.0, family="gamma", cv=0.5)
    draws = np.asarray(
        [
            sample_episode_duration(
                specification,
                run_seed=20260830,
                stage="latent",
                agent_uid=uid,
                episode_index=0,
            )
            for uid in range(10_000)
        ]
    )
    assert abs(float(draws.mean()) / 4.0 - 1.0) < 0.02
    assert abs(float(draws.std(ddof=1) / draws.mean()) / 0.5 - 1.0) < 0.03
    first = sample_episode_duration(
        specification,
        run_seed=20260830,
        stage="latent",
        agent_uid=7,
        episode_index=0,
    )
    assert first == sample_episode_duration(
        specification,
        run_seed=20260830,
        stage="latent",
        agent_uid=7,
        episode_index=0,
    )
    assert first != sample_episode_duration(
        specification,
        run_seed=20260830,
        stage="latent",
        agent_uid=7,
        episode_index=1,
    )


def test_duration_schema_rejects_invalid_family_parameters() -> None:
    with pytest.raises(ValueError, match="gamma durations require"):
        _duration(4.0, family="gamma")
    with pytest.raises(ValueError, match="constant durations must not"):
        _duration(4.0, cv=0.5)


def test_constant_v1_comparator_has_exact_projection(outbreak_network) -> None:
    comparator = load_parameter_set(
        ROOT,
        ROOT / "configs" / "diseases" / "respiratory_seirs_v1_waning_comparator.yaml",
    )
    config = default_run_config("ci", 123, comparator, duration_days=8)
    result = run_outbreak(outbreak_network, config, comparator)
    assert result.diagnostics["compatibility"]["v1_projection_latent_outcome_hash"] == (
        "54a675a4546a636ac18a0b904d7fb935e36a5be8fd5a759bd71a789e84525733"
    )
    assert (
        result.latent_outcome_hash
        != result.diagnostics["compatibility"]["v1_projection_latent_outcome_hash"]
    )
    assert config.waning_enabled is True


def test_gamma_transition_advances_on_first_daily_timestep_after_draw(
    outbreak_network, parameters
) -> None:
    result = run_outbreak(
        outbreak_network,
        _config(
            beta=0.0,
            initial_seed_count=1,
            duration_days=15,
            latent_duration=_duration(4.0, family="gamma", cv=0.5),
            infectious_duration=_duration(4.0, family="gamma", cv=0.5),
        ),
        parameters,
    )
    event = result.transmission_events[0]
    infection = date.fromisoformat(event["infection_date"])
    infectious_start = date.fromisoformat(event["infectious_start_date"])
    recovery = date.fromisoformat(event["recovery_date"])
    assert (infectious_start - infection).days == math.ceil(event["latent_duration_draw_days"])
    assert (recovery - infectious_start).days == math.ceil(event["infectious_duration_draw_days"])


def test_route_removal_does_not_create_staff_route(outbreak_network, parameters) -> None:
    reduced = generate_networks(
        NetworkGenerationConfig(
            mode="ci",
            seed=123,
            enabled_route_families=(
                "household",
                "school",
                "work",
                "transport",
                "indoor_community",
                "outdoor_community",
            ),
        ),
        outbreak_network.m2_input,
        outbreak_network.m3_input,
    )
    result = run_outbreak(reduced, _config(beta=0.0), parameters)
    assert "care_staff" not in reduced.route_specs
    assert all(
        row["new_events"] == 0 for row in result.daily_route if row["route_id"] == "care_staff"
    )


def test_starsim_single_route_attribution() -> None:
    import starsim as ss

    class FixedNetwork(ss.Network):
        def step(self):
            return None

    network = FixedNetwork(
        name="single_route",
        p1=ss.uids(np.array([0], dtype=np.int64)),
        p2=ss.uids(np.array([1], dtype=np.int64)),
        beta=np.ones(1),
        label="single_route",
    )
    disease = RespiratorySEIRS(
        route_betas={"single_route": 1.0},
        initial_seed_count=1,
        latent_duration=_duration(1.0),
        infectious_duration=_duration(5.0),
        waning_enabled=False,
    )
    sim = ss.Sim(
        n_agents=2,
        start=date(2025, 1, 6).isoformat(),
        stop=date(2025, 1, 8).isoformat(),
        dt=ss.days(1),
        rand_seed=123,
        networks=network,
        diseases=disease,
        verbose=0,
        copy_inputs=False,
    )
    sim.init()
    sim.people.age[:] = 0
    sim.run(verbose=0)
    local = [event for event in disease._all_events if event["source_kind"] == "local"]
    assert len(local) == 1
    assert local[0]["route_id"] == "single_route"
    assert local[0]["infector_uid"] in {0, 1}
    assert local[0]["infected_uid"] in {0, 1}
    infected_uid = int(local[0]["infected_uid"])
    assert float(sim.people.age[infected_uid]) <= 0
    assert not bool(disease.susceptible.raw[infected_uid])
    assert local[0]["infection_date"] < local[0]["infectious_start_date"]
    assert local[0]["recovery_date"] >= local[0]["infectious_start_date"]


def test_outbreak_artifact_contains_tidy_outputs(
    outbreak_network, parameters, tmp_path: Path
) -> None:
    result = run_outbreak(outbreak_network, _config(duration_days=3), parameters)
    artifact = write_outbreak_artifact(result, ROOT, tmp_path)
    manifest = json.loads((artifact.artifact_directory / "manifest.json").read_text())
    assert manifest["diagnostics_status"] == "passed"
    assert manifest["starsim_version"] == "3.5.2"
    assert manifest["m4_logical_content_hash"] == outbreak_network.logical_content_hash
    for filename in (
        "daily_epidemic.parquet",
        "daily_parish.parquet",
        "daily_route.parquet",
        "daily_age.parquet",
        "transmission_events.parquet",
        "parameters.json",
        "diagnostics.json",
    ):
        assert (artifact.artifact_directory / filename).exists()
