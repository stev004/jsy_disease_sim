"""Shared canonical scientific identity functions used by writers and verifiers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .hashing import canonical_json_bytes, sha256_bytes

_OPTIONAL_ATTRIBUTION_FIELDS = {
    "successful_candidate_route_count",
    "successful_candidate_routes",
    "successful_candidate_edge_count",
    "successful_candidate_edge_routes",
    "successful_candidate_hazards",
    "attributed_route_id",
}


def canonical_m5_events(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove only schema-added null attribution columns absent in runtime events."""

    return [
        {
            key: value
            for key, value in row.items()
            if value is not None or key not in _OPTIONAL_ATTRIBUTION_FIELDS
        }
        for row in rows
    ]


def m5_latent_outcome_hash(
    *,
    daily_epidemic: list[dict[str, Any]],
    daily_parish: list[dict[str, Any]],
    daily_route: list[dict[str, Any]],
    daily_age: list[dict[str, Any]],
    transmission_events: list[dict[str, Any]],
) -> str:
    payload = {
        "daily_epidemic": daily_epidemic,
        "daily_parish": daily_parish,
        "daily_route": daily_route,
        "daily_age": daily_age,
        "transmission_events": canonical_m5_events(transmission_events),
    }
    return sha256_bytes(canonical_json_bytes(payload))


def m5_logical_content_hash(
    *, config: dict[str, Any], parameters: dict[str, Any], latent_hash: str, network_hash: str
) -> str:
    return sha256_bytes(
        canonical_json_bytes(
            {
                "config": config,
                "parameters": parameters,
                "latent_outcome_hash": latent_hash,
                "network_logical_content_hash": network_hash,
            }
        )
    )


def m5_artifact_bundle_hash(
    *,
    logical_hash: str,
    latent_hash: str,
    scenario_hash: str | None,
    daily_intervention_state: list[dict[str, Any]],
    intervention_events: list[dict[str, Any]],
    route_effects: list[dict[str, Any]],
) -> str:
    return sha256_bytes(
        canonical_json_bytes(
            {
                "latent_logical_content_hash": logical_hash,
                "latent_outcome_hash": latent_hash,
                "scenario_hash": scenario_hash,
                "daily_intervention_state": daily_intervention_state,
                "intervention_events": intervention_events,
                "route_effects": route_effects,
            }
        )
    )


def m6_ensemble_logical_hash(
    *,
    config: dict[str, Any],
    replicate_records: list[dict[str, Any]],
    summary: list[dict[str, Any]],
    trajectories: Mapping[int, Sequence[dict[str, Any]]],
    replicate_grid: list[dict[str, Any]],
) -> str:
    canonical_trajectories: dict[int, list[dict[str, Any]]] = {}
    for seed, rows in trajectories.items():
        normalized_rows: list[dict[str, Any]] = []
        for row in rows:
            normalized = dict(row)
            value = normalized.get("value")
            metric = normalized.get("metric")
            if value is not None:
                if metric in {"latent_prevalence", "latent_attack_rate"}:
                    normalized["value"] = float(value)
                elif metric == "intervention_route_active":
                    normalized["value"] = bool(value)
                else:
                    normalized["value"] = int(value)
            normalized_rows.append(normalized)
        canonical_trajectories[seed] = normalized_rows
    return sha256_bytes(
        canonical_json_bytes(
            {
                "config": config,
                "replicates": [
                    {key: value for key, value in record.items() if key != "runtime_seconds"}
                    for record in replicate_records
                ],
                "summary": summary,
                "trajectories": canonical_trajectories,
                "replicate_grid": replicate_grid,
            }
        )
    )


def m6_comparison_logical_hash(
    *, comparison_id: str, config_a_hash: str, config_b_hash: str, rows: list[dict[str, Any]]
) -> str:
    canonical_rows: list[dict[str, Any]] = []
    for row in rows:
        normalized = dict(row)
        metric = normalized.get("metric")
        for key in ("value_a", "value_b"):
            value = normalized.get(key)
            if value is None:
                continue
            if metric in {"latent_prevalence", "latent_attack_rate"}:
                normalized[key] = float(value)
            elif metric == "intervention_route_active":
                normalized[key] = bool(value)
            else:
                normalized[key] = int(value)
        difference = normalized.get("difference")
        if difference is not None:
            normalized["difference"] = (
                float(difference)
                if metric in {"latent_prevalence", "latent_attack_rate"}
                else int(difference)
            )
        canonical_rows.append(normalized)
    return sha256_bytes(
        canonical_json_bytes(
            {
                "comparison_id": comparison_id,
                "config_a_hash": config_a_hash,
                "config_b_hash": config_b_hash,
                "rows": canonical_rows,
            }
        )
    )
