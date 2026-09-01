from __future__ import annotations

from types import SimpleNamespace

import jersey_outbreak.travel as travel_module
from jersey_outbreak.travel import run_travel_ensemble


def _fake_run(seed: int) -> SimpleNamespace:
    return SimpleNamespace(
        config=SimpleNamespace(seed=seed),
        scenario_hash=f"scenario-{seed}",
        latent_outcome_hash=f"latent-{seed}",
        travel_config_hash="travel-config",
        visitor_episode_hash=f"visitor-episode-{seed}",
        daily_epidemic=[
            {
                "date": "2025-01-06",
                "resident_infections": 0,
                "visitor_infections": 0,
            }
        ],
        daily_travel_population=[
            {
                "active_visitors": 0,
                "present_population": 1,
                "arrivals": 0,
                "departures": 0,
            }
        ],
        transmission_events=[],
        travel_intervention_events=[],
    )


def test_invalid_summary_semantics_fail_the_ensemble_diagnostic() -> None:
    ensemble_result = {
        "runs": [_fake_run(101)],
        "failures": [],
        "seeds": (101,),
        "summary": [
            {
                "replicate_count": 1,
                "semantic": "unsupported",
                "missing_behavior": "structural_zero",
                "outside_horizon_behavior": "excluded",
            }
        ],
    }

    diagnostics = travel_module._travel_ensemble_diagnostics(**ensemble_result)

    assert diagnostics["status"] == "failed"
    assert diagnostics["invariant_predicates"]["metric_semantics_preserved"] is False


def test_normal_small_ensemble_passes_all_invariant_predicates(monkeypatch, m6_base_config) -> None:
    def fake_run(_generated, run_config, _parameters, _travel_config, *, scenario=None):
        return _fake_run(run_config.seed)

    monkeypatch.setattr(travel_module, "run_travel_outbreak", fake_run)
    result = run_travel_ensemble(
        object(),
        object(),
        m6_base_config.model_copy(update={"duration_days": 1}),
        object(),
        (101, 102),
    )

    diagnostics = result["diagnostics"]
    assert diagnostics["status"] == "passed"
    assert diagnostics["invariant_predicates"]
    assert all(diagnostics["invariant_predicates"].values())
    assert all(
        diagnostics[key] is diagnostics["invariant_predicates"][key]
        for key in (
            "metric_semantics_preserved",
            "matched_seed_pairing",
            "failed_replicates_excluded",
        )
    )
