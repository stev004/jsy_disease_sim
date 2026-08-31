"""Single versioned catalogue of scientific artifact families and datasets."""

from __future__ import annotations

SCIENTIFIC_DATASET_CATALOG: dict[str, frozenset[str]] = {
    "m5_outbreak": frozenset(
        {
            "daily_epidemic",
            "daily_parish",
            "daily_route",
            "daily_age",
            "transmission_events",
        }
    ),
    "m6_ensemble": frozenset({"ensemble_summary", "replicate_trajectories", "replicate_grid"}),
    "m6_comparison": frozenset({"matched_seed_comparison", "paired_difference_summary"}),
    "m7_intervention": frozenset(
        {
            "daily_epidemic",
            "daily_parish",
            "daily_route",
            "daily_age",
            "transmission_events",
            "daily_intervention_state",
            "intervention_events",
            "route_effects",
        }
    ),
    "m8_travel": frozenset(
        {
            "daily_travel_population",
            "travel_episodes",
            "visitor_population",
            "visitor_events",
            "daily_travel_route",
            "temporary_edges",
            "travel_transmission_events",
            "travel_intervention_events",
            "daily_travel_intervention_state",
            "seasonality_schedule",
            "high_risk_strata",
            "daily_high_risk",
            "daily_epidemic",
            "daily_parish",
            "daily_route",
            "daily_age",
            "transmission_events",
            "observation_events",
            "detection_events",
        }
    ),
}


ALL_SCIENTIFIC_DATASETS = tuple(sorted(set().union(*SCIENTIFIC_DATASET_CATALOG.values())))
