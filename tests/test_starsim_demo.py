from jersey_outbreak.starsim_compat import SUPPORTED_STARSIM_VERSION, run_official_sir_demo


def test_official_starsim_sir_demo_shape_and_conservation() -> None:
    result = run_official_sir_demo(seed=123)
    assert result.starsim_version == SUPPORTED_STARSIM_VERSION == "3.5.2"
    assert len(result.time_index) == 31
    assert len(result.n_susceptible) == len(result.n_infected) == len(result.n_recovered)
    assert result.n_susceptible[0] + result.n_infected[0] + result.n_recovered[0] == 100
    assert result.n_susceptible[-1] + result.n_infected[-1] + result.n_recovered[-1] == 100
    assert result.cumulative_infections[-1] >= result.cumulative_infections[0]


def test_same_seed_reproduces_declared_demo_outputs() -> None:
    first = run_official_sir_demo(seed=123)
    second = run_official_sir_demo(seed=123)
    assert first == second
