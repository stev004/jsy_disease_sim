"""The sole Starsim API boundary for the Milestone 0 compatibility spike."""

from __future__ import annotations

import contextlib
import io
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUPPORTED_STARSIM_VERSION = "3.5.2"


@dataclass(frozen=True)
class StarsimDemoResult:
    """Plain-Python results extracted from the supported Starsim run."""

    starsim_version: str
    n_agents: int
    duration: int
    n_contacts: int
    time_index: list[int]
    n_susceptible: list[int]
    n_infected: list[int]
    n_recovered: list[int]
    cumulative_infections: list[int]


def _load_starsim() -> Any:
    """Import and verify the exact API version at the integration boundary."""

    cache_directory = Path(tempfile.gettempdir()) / "jos-matplotlib"
    cache_directory.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache_directory))
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        import starsim as ss

    actual_version = getattr(ss, "__version__", None)
    if actual_version != SUPPORTED_STARSIM_VERSION:
        raise RuntimeError(
            f"Unsupported Starsim version {actual_version!r}; "
            f"Milestone 0 requires {SUPPORTED_STARSIM_VERSION}"
        )
    return ss


def _count_series(results: Any, key: str) -> list[int]:
    """Convert Starsim's numeric result arrays into stable integer counts."""

    return [int(round(float(value))) for value in results[key]]


def run_official_sir_demo(
    *, seed: int, n_agents: int = 100, duration: int = 30, n_contacts: int = 10
) -> StarsimDemoResult:
    """Run Starsim's official SIR example with its built-in ``RandomNet``.

    The values are deliberately demo assumptions. They are not Jersey data or
    parameters for a named pathogen.
    """

    if seed < 0:
        raise ValueError("seed must be non-negative")
    if n_agents <= 0 or duration <= 0 or n_contacts <= 0:
        raise ValueError("n_agents, duration and n_contacts must be positive")

    ss = _load_starsim()
    previous_verbose = ss.options.verbose
    ss.options.verbose = 0
    try:
        sim = ss.Sim(
            pars=dict(
                n_agents=n_agents,
                dur=duration,
                rand_seed=seed,
                networks=ss.RandomNet(n_contacts=n_contacts),
                diseases=ss.SIR(
                    beta=ss.peryear(0.8),
                    init_prev=ss.bernoulli(p=0.1),
                    dur_inf=ss.years(0.1),
                    p_death=ss.bernoulli(p=0.0),
                ),
            )
        )
        sim.run()
        disease_results = sim.diseases.sir.results
        n_susceptible = _count_series(disease_results, "n_susceptible")
        n_infected = _count_series(disease_results, "n_infected")
        n_recovered = _count_series(disease_results, "n_recovered")
        cumulative_infections = _count_series(disease_results, "cum_infections")
        return StarsimDemoResult(
            starsim_version=ss.__version__,
            n_agents=n_agents,
            duration=duration,
            n_contacts=n_contacts,
            time_index=list(range(len(n_susceptible))),
            n_susceptible=n_susceptible,
            n_infected=n_infected,
            n_recovered=n_recovered,
            cumulative_infections=cumulative_infections,
        )
    finally:
        ss.options.verbose = previous_verbose
