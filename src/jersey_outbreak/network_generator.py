"""Starsim-independent deterministic route generation for Milestone 4.

This module owns only plain Python route metadata, memberships and canonical
undirected edge tables.  The Starsim dependency is deliberately confined to
``starsim_adapter.py``.
"""

from __future__ import annotations

import hashlib
import math
import resource
import time
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from .data_pipeline import DataBuildError
from .hashing import canonical_json_bytes, sha256_bytes
from .network_schemas import (
    Calendar,
    NetworkGenerationConfig,
    Persistence,
    RouteFamily,
    RouteKind,
    RouteSpec,
)
from .population_structure_artifacts import M2PopulationInput, M3StructureInput
from .staffing_generator import StaffingAllocation, build_staffing_allocation

PRIVATE_ROUTE_FAMILIES = {
    "household",
    "school",
    "work",
    "care",
    "transport",
    "indoor_community",
    "outdoor_community",
}

ROUTE_WEIGHT_MEANING = (
    "relative daily exposure/transmission opportunity weight in [0, 1]; not an observed "
    "contact count or a measured pathogen transmission probability"
)

AGE_BANDS = ("0-4", "5-17", "18-34", "35-64", "65+")
SCHOOL_CALENDAR_PROVENANCE = {
    "2025": {
        "source_id": "states_assembly_r119_2024_school_terms",
        "source_sha256": "7826d1877b40e10895cb784c3291546b5dd6133f3918f163df06f085c5219abd",
        "status": "official",
        "coverage": "common Jersey term and half-term dates; no institution-specific inset days",
    },
    "2026": {
        "source_id": "school_term_dates_govje_2026",
        "source_sha256": "307a9168a62cfef40e4912fe429b6d5aa2bbfad85636be3e44552e64bbd93c6e",
        "status": "official",
        "coverage": "common Jersey term and half-term dates; no institution-specific inset days",
    },
}
ROUTE_OVERLAP_POLICIES = {
    frozenset(("school_class", "school_cross_class")): "FORBIDDEN",
    frozenset(("workplace_team", "workplace_transient")): "FORBIDDEN",
}


@dataclass(frozen=True)
class RouteSnapshot:
    """One deterministic daily edge state for one route."""

    route_id: str
    snapshot_date: date
    edges: tuple[dict[str, Any], ...]


@dataclass
class GeneratedNetworks:
    """Validated M4 route state and diagnostics."""

    config: NetworkGenerationConfig
    m2_input: M2PopulationInput
    m3_input: M3StructureInput
    agent_ids: list[str]
    route_specs: dict[str, dict[str, Any]]
    structural_edges: dict[str, list[dict[str, Any]]]
    route_memberships: dict[str, list[dict[str, Any]]]
    school_staff_assignments: list[dict[str, Any]]
    care_staff_assignments: list[dict[str, Any]]
    staffing_diagnostics: dict[str, Any]
    staffing_provenance: dict[str, Any]
    diagnostics: dict[str, Any]
    logical_content_hash: str
    runtime_seconds: float
    peak_memory_bytes: int | None
    _dynamic_builders: dict[str, Callable[[date], list[dict[str, Any]]]] = field(
        repr=False, default_factory=dict
    )
    _snapshot_cache: dict[tuple[str, date], RouteSnapshot] = field(repr=False, default_factory=dict)

    def snapshot(self, snapshot_date: date) -> dict[str, RouteSnapshot]:
        """Return every configured route's edges for one calendar date."""

        return {
            route_id: self.route_snapshot(route_id, snapshot_date)
            for route_id in sorted(self.route_specs)
        }

    def route_snapshot(self, route_id: str, snapshot_date: date) -> RouteSnapshot:
        """Return one route's deterministic state for one day."""

        if route_id not in self.route_specs:
            raise KeyError(f"unknown route: {route_id}")
        key = (route_id, snapshot_date)
        if key in self._snapshot_cache:
            return self._snapshot_cache[key]
        spec = self.route_specs[route_id]
        if not _route_active(spec["active_calendar"], snapshot_date, self.config):
            edges: list[dict[str, Any]] = []
        elif route_id in self._dynamic_builders:
            edges = self._dynamic_builders[route_id](snapshot_date)
        else:
            edges = list(self.structural_edges.get(route_id, []))
        snapshot = RouteSnapshot(route_id, snapshot_date, tuple(edges))
        self._snapshot_cache[key] = snapshot
        return snapshot


def _stable_int(seed: int, *parts: object) -> int:
    payload = "|".join(str(part) for part in (seed, *parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def _ordered_ids(ids: Iterable[str], seed: int, *parts: object) -> list[str]:
    return sorted(ids, key=lambda agent_id: (_stable_int(seed, *parts, agent_id), agent_id))


def _canonical_edge(
    p1: str, p2: str, weight: float, persistence_days: int = 1
) -> dict[str, Any] | None:
    if p1 == p2:
        return None
    left, right = sorted((p1, p2))
    return {
        "p1": left,
        "p2": right,
        "weight": float(weight),
        "persistence_days": int(persistence_days),
    }


def _deduplicate_edges(edges: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for edge in edges:
        key = (edge["p1"], edge["p2"])
        existing = unique.get(key)
        if existing is None or edge["weight"] > existing["weight"]:
            unique[key] = edge
    return [unique[key] for key in sorted(unique)]


def _complete_group(
    ids: Iterable[str], weight: float, persistence_days: int = 30
) -> list[dict[str, Any]]:
    ordered = sorted(set(ids))
    edges: list[dict[str, Any]] = []
    for left_index, left in enumerate(ordered):
        for right in ordered[left_index + 1 :]:
            edge = _canonical_edge(left, right, weight, persistence_days)
            if edge is not None:
                edges.append(edge)
    return edges


def _ring_edges(
    ids: Iterable[str],
    contacts_per_participant: int,
    weight: float,
    persistence_days: int,
    excluded_pairs: set[tuple[str, str]] | None = None,
) -> list[dict[str, Any]]:
    ordered = list(ids)
    if len(ordered) < 2 or contacts_per_participant <= 0:
        return []
    edges: list[dict[str, Any]] = []
    n = len(ordered)
    for index, left in enumerate(ordered):
        for offset in range(1, min(contacts_per_participant, n - 1) + 1):
            right = ordered[(index + offset) % n]
            pair = tuple(sorted((left, right)))
            if excluded_pairs is not None and pair in excluded_pairs:
                continue
            edge = _canonical_edge(left, right, weight, persistence_days)
            if edge is not None:
                edges.append(edge)
    return _deduplicate_edges(edges)


def _grouped_ring_edges(
    groups: Iterable[Iterable[str]],
    seed: int,
    route_id: str,
    snapshot_date: date,
    contacts_per_participant: int,
    weight: float,
    persistence_days: int,
    excluded_pairs: set[tuple[str, str]] | None = None,
) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for group_index, group in enumerate(groups):
        ordered = _ordered_ids(group, seed, route_id, snapshot_date.isoformat(), group_index)
        edges.extend(
            _ring_edges(
                ordered,
                contacts_per_participant,
                weight,
                persistence_days,
                excluded_pairs,
            )
        )
    return _deduplicate_edges(edges)


def _school_staff_cross_edges(
    school_year_groups: dict[tuple[str, str], list[str]],
    school_staff_by_school_year: dict[tuple[str, str], list[str]],
    seed: int,
    snapshot_date: date,
    contacts_per_staff: int,
    weight: float,
    persistence_days: int,
    excluded_pairs: set[tuple[str, str]] | None = None,
) -> list[dict[str, Any]]:
    """Add bounded staff/year contacts without changing pupil-only ring edges."""

    edges: list[dict[str, Any]] = []
    for school_year, pupil_group in sorted(school_year_groups.items()):
        pupils = _ordered_ids(
            pupil_group,
            seed,
            "school_cross_class-pupils",
            snapshot_date.isoformat(),
            school_year,
        )
        staff_ids = sorted(set(school_staff_by_school_year.get(school_year, [])))
        if not pupils or not staff_ids or contacts_per_staff <= 0:
            continue
        contact_count = min(contacts_per_staff, len(pupils))
        for staff_id in staff_ids:
            start = _stable_int(
                seed,
                "school_cross_class-staff",
                snapshot_date.isoformat(),
                school_year,
                staff_id,
            ) % len(pupils)
            for offset in range(contact_count):
                edge = _canonical_edge(
                    staff_id,
                    pupils[(start + offset) % len(pupils)],
                    weight,
                    persistence_days,
                )
                if edge is not None and (
                    excluded_pairs is None or (edge["p1"], edge["p2"]) not in excluded_pairs
                ):
                    edges.append(edge)
    return _deduplicate_edges(edges)


def _age_band(age: int) -> str:
    if age <= 4:
        return "0-4"
    if age <= 17:
        return "5-17"
    if age <= 34:
        return "18-34"
    if age <= 64:
        return "35-64"
    return "65+"


def _is_school_term(snapshot_date: date, config: NetworkGenerationConfig) -> bool:
    if snapshot_date.year != config.school_calendar_year:
        raise ValueError(
            "school route date is outside the configured authoritative reference calendar year"
        )
    if not any(start <= snapshot_date <= end for start, end in config.school_term_periods):
        return False
    return not any(start <= snapshot_date <= end for start, end in config.school_holiday_periods)


def _route_active(calendar: str, snapshot_date: date, config: NetworkGenerationConfig) -> bool:
    weekday = snapshot_date.weekday() < 5
    if calendar == "always":
        return True
    if calendar == "weekday":
        return weekday
    if calendar == "weekend":
        return not weekday
    if calendar == "weekday_term":
        return weekday and _is_school_term(snapshot_date, config)
    if calendar == "weekday_or_weekend":
        return True
    raise ValueError(f"unknown route calendar: {calendar}")


def _job_is_physical_on_date(
    job: dict[str, Any], agent_id: str, snapshot_date: date, seed: int
) -> bool:
    if snapshot_date.weekday() >= 5:
        return False
    days_per_week = int(job["days_per_week"])
    remote_days = int(job["remote_days_per_week"])
    if days_per_week <= 0:
        return False
    selected = sorted(
        range(5), key=lambda day: _stable_int(seed, "workday", job["job_id"], agent_id, day)
    )[:days_per_week]
    remote = set(
        sorted(
            selected,
            key=lambda day: _stable_int(seed, "remote", job["job_id"], agent_id, day),
        )[:remote_days]
    )
    return snapshot_date.weekday() in set(selected) - remote


def _participation(
    agent_id: str,
    age: int,
    snapshot_date: date,
    seed: int,
    route_id: str,
    weekend_probability: int,
    weekday_probability: int,
) -> bool:
    probability = weekend_probability if snapshot_date.weekday() >= 5 else weekday_probability
    return _stable_int(seed, route_id, snapshot_date.isoformat(), agent_id) % 100 < probability


def _route_spec(
    route_id: str,
    route_family: RouteFamily,
    route_kind: RouteKind,
    membership_source: str,
    persistence: Persistence,
    active_calendar: Calendar,
    indoor: bool,
    relative_weight: float,
    assumptions: tuple[str, ...] = (),
) -> dict[str, Any]:
    spec = RouteSpec(
        route_id=route_id,
        route_family=route_family,
        route_kind=route_kind,
        membership_source=membership_source,
        persistence=persistence,
        active_calendar=active_calendar,
        indoor=indoor,
        relative_weight=relative_weight,
        weight_meaning=ROUTE_WEIGHT_MEANING,
        assumptions=assumptions,
    )
    return spec.model_dump(mode="json")


def _build_route_specs(config: NetworkGenerationConfig) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    if config.route_family_enabled("household"):
        specs["household"] = _route_spec(
            "household",
            "household",
            "household",
            "M2 private household_id membership",
            "fixed",
            "always",
            True,
            1.0,
            ("Complete within-private-household mixing is a structural approximation.",),
        )
    if config.route_family_enabled("school"):
        specs["school_class"] = _route_spec(
            "school_class",
            "school",
            "school_class",
            "M3 class_id pupil membership",
            "fixed",
            "weekday_term",
            True,
            0.85,
            (
                (
                    "M3 has pupil memberships but no observed teacher rosters; synthetic "
                    "teacher/TA class membership is a structural overlay."
                ),
            ),
        )
        specs["school_cross_class"] = _route_spec(
            "school_cross_class",
            "school",
            "school_cross_class",
            "M3 school_id and school_year membership after class/core exclusion",
            "periodically_refreshed",
            "weekday_term",
            True,
            0.5,
            (
                (
                    "Cross-class contacts are bounded daily samples within school/year, "
                    "not real venue histories; pairs already in school_class are excluded."
                ),
            ),
        )
    if config.route_family_enabled("work"):
        specs["workplace_team"] = _route_spec(
            "workplace_team",
            "work",
            "workplace_team",
            "M3 effective job team_id membership",
            "fixed",
            "weekday",
            True,
            0.7,
            (
                "For synthetic school/care staff, the M3 primary job is institutionally "
                "reinterpreted and only an explicitly represented secondary job remains "
                "in this ordinary-workplace route; M3 job accounting is unchanged.",
            ),
        )
        specs["workplace_transient"] = _route_spec(
            "workplace_transient",
            "work",
            "workplace_transient",
            "M3 effective workplace_id job membership",
            "periodically_refreshed",
            "weekday",
            True,
            0.3,
            (
                (
                    "Large workplaces use bounded workplace-level sampling; they are not "
                    "complete cliques. Institutional school/care staff retain only "
                    "explicitly represented secondary workplace participation."
                ),
            ),
        )
    if config.route_family_enabled("care"):
        specs["care_resident"] = _route_spec(
            "care_resident",
            "care",
            "care_resident",
            "M2 care_setting_id membership for care establishments",
            "fixed",
            "always",
            True,
            0.9,
            (
                (
                    "Care residents are clustered into bounded synthetic cohorts rather "
                    "than one facility clique."
                ),
            ),
        )
        specs["care_staff"] = _route_spec(
            "care_staff",
            "care",
            "care_staff",
            "No M3 staff roster available",
            "fixed",
            "always",
            True,
            0.65,
            (
                (
                    "Staff endpoints are existing synthetic workers assigned by regulatory "
                    "minimum structure; no real care-home roster is claimed."
                ),
            ),
        )
    if config.route_family_enabled("transport"):
        if config.shared_vehicle_enabled:
            specs["shared_vehicle"] = _route_spec(
                "shared_vehicle",
                "transport",
                "shared_vehicle",
                "M3 constrained household car-commuter groups; car-alone commuters excluded",
                "periodically_refreshed",
                "weekday",
                True,
                0.7,
                (
                    (
                        "Only same-household car commuters with a common synthetic work parish "
                        "are matched; driver/passenger roles are structural, not observed."
                    ),
                ),
            )
        specs["bus"] = _route_spec(
            "bus",
            "transport",
            "bus",
            "M3 bus commuters grouped by broad geography/time band",
            "periodically_refreshed",
            "weekday",
            True,
            0.45,
            (
                "Synthetic transit cohorts use no route, stop or departure history.",
                "Weekly boardings are not treated as unique riders.",
            ),
        )
    if config.route_family_enabled("indoor_community"):
        specs["community_indoor"] = _route_spec(
            "community_indoor",
            "indoor_community",
            "community_indoor",
            "M2 age/parish attributes with seeded activity propensity and configured age mixing",
            "periodically_refreshed",
            "weekday_or_weekend",
            True,
            config.indoor_weight,
            (
                (
                    "Indoor participation and the age-mixing matrix are structural assumptions; "
                    "regular contacts persist while a daily component refreshes."
                ),
            ),
        )
    if config.route_family_enabled("outdoor_community"):
        specs["community_outdoor"] = _route_spec(
            "community_outdoor",
            "outdoor_community",
            "community_outdoor",
            "M2 age/parish attributes with seeded activity propensity and configured age mixing",
            "periodically_refreshed",
            "weekday_or_weekend",
            False,
            config.outdoor_weight,
            (
                (
                    "Outdoor participation and the age-mixing matrix are structural assumptions; "
                    "regular contacts persist while a daily component refreshes."
                ),
            ),
        )
    return {
        route_id: spec
        for route_id, spec in specs.items()
        if route_id not in config.disabled_route_ids
    }


def _build_group_memberships(
    groups: dict[str, list[str]], membership_name: str
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group_id in sorted(groups):
        for agent_id in sorted(set(groups[group_id])):
            rows.append({"membership": membership_name, "group_id": group_id, "agent_id": agent_id})
    return rows


def _analyse_edges(
    edges: list[dict[str, Any]],
    eligible_agents: set[str],
    agent_info: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    duplicate_count = len(edges) - len({(edge["p1"], edge["p2"]) for edge in edges})
    self_edge_count = sum(edge["p1"] == edge["p2"] for edge in edges)
    endpoint_ids = {endpoint for edge in edges for endpoint in (edge["p1"], edge["p2"])}
    degrees: dict[str, int] = defaultdict(int)
    adjacency: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        p1, p2 = edge["p1"], edge["p2"]
        degrees[p1] += 1
        degrees[p2] += 1
        adjacency[p1].add(p2)
        adjacency[p2].add(p1)
    all_degrees = [degrees.get(agent_id, 0) for agent_id in sorted(eligible_agents)]
    if all_degrees:
        ordered_degrees = sorted(all_degrees)
        percentiles = {
            str(percentile): float(_quantile(ordered_degrees, percentile / 100))
            for percentile in (50, 90, 95, 99, 100)
        }
        mean_degree = sum(all_degrees) / len(all_degrees)
        median_degree = percentiles["50"]
        max_degree = max(all_degrees)
    else:
        percentiles = {str(percentile): 0.0 for percentile in (50, 90, 95, 99, 100)}
        mean_degree = 0.0
        median_degree = 0.0
        max_degree = 0

    parent = {agent_id: agent_id for agent_id in eligible_agents}

    def find(agent_id: str) -> str:
        while parent[agent_id] != agent_id:
            parent[agent_id] = parent[parent[agent_id]]
            agent_id = parent[agent_id]
        return agent_id

    for edge in edges:
        left, right = edge["p1"], edge["p2"]
        if left not in parent or right not in parent:
            continue
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root
    components = len({find(agent_id) for agent_id in eligible_agents}) if eligible_agents else 0

    sample_ids = sorted(endpoint_ids)[: min(2000, len(endpoint_ids))]
    local_coefficients: list[float] = []
    for agent_id in sample_ids:
        neighbors = sorted(adjacency[agent_id])
        possible = len(neighbors) * (len(neighbors) - 1) / 2
        if possible == 0:
            local_coefficients.append(0.0)
            continue
        triangles = sum(
            neighbor_right in adjacency[neighbor_left]
            for index, neighbor_left in enumerate(neighbors)
            for neighbor_right in neighbors[index + 1 :]
        )
        local_coefficients.append(triangles / possible)
    clustering = sum(local_coefficients) / len(local_coefficients) if local_coefficients else 0.0

    age_pairs = []
    parish_pairs = []
    for edge in edges:
        left = agent_info.get(edge["p1"])
        right = agent_info.get(edge["p2"])
        if left is None or right is None:
            continue
        age_pairs.append(abs(int(left["age"]) - int(right["age"])))
        parish_pairs.append(left["home_parish"] == right["home_parish"])
    weights = [float(edge["weight"]) for edge in edges]
    return {
        "eligible_agents": len(eligible_agents),
        "participating_agents": len(endpoint_ids),
        "edge_count": len(edges),
        "mean_degree": mean_degree,
        "median_degree": median_degree,
        "degree_percentiles": percentiles,
        "max_degree": max_degree,
        "connected_components": components,
        "clustering_coefficient_sample": clustering,
        "clustering_sample_size": len(sample_ids),
        "mean_absolute_age_difference": sum(age_pairs) / len(age_pairs) if age_pairs else 0.0,
        "same_home_parish_edge_share": (
            sum(parish_pairs) / len(parish_pairs) if parish_pairs else 0.0
        ),
        "edge_weight": {
            "min": min(weights) if weights else 0.0,
            "median": _quantile(sorted(weights), 0.5) if weights else 0.0,
            "mean": sum(weights) / len(weights) if weights else 0.0,
            "max": max(weights) if weights else 0.0,
        },
        "self_edge_count": self_edge_count,
        "duplicate_edge_count": duplicate_count,
    }


def _edge_keys(edges: Iterable[dict[str, Any]]) -> set[tuple[str, str]]:
    return {(edge["p1"], edge["p2"]) for edge in edges}


def _age_mixing_matrix(
    edges: Iterable[dict[str, Any]], agent_info: dict[str, dict[str, Any]]
) -> dict[str, dict[str, int]]:
    matrix = {left: {right: 0 for right in AGE_BANDS} for left in AGE_BANDS}
    for edge in edges:
        left = agent_info.get(edge["p1"])
        right = agent_info.get(edge["p2"])
        if left is None or right is None:
            continue
        left_band = _age_band(int(left["age"]))
        right_band = _age_band(int(right["age"]))
        matrix[left_band][right_band] += 1
        if left_band != right_band:
            matrix[right_band][left_band] += 1
    return matrix


def _route_overlap_matrix(
    generated: GeneratedNetworks,
    baseline_date: date,
) -> list[dict[str, Any]]:
    route_ids = sorted(generated.route_specs)
    edge_sets = {
        route_id: _edge_keys(generated.route_snapshot(route_id, baseline_date).edges)
        for route_id in route_ids
    }
    rows: list[dict[str, Any]] = []
    for left_index, left in enumerate(route_ids):
        for right in route_ids[left_index + 1 :]:
            overlap = len(edge_sets[left] & edge_sets[right])
            policy = ROUTE_OVERLAP_POLICIES.get(
                frozenset((left, right)),
                "ALLOWED_DISTINCT_SETTING"
                if generated.route_specs[left]["route_family"]
                != generated.route_specs[right]["route_family"]
                else "DIAGNOSTIC_ONLY",
            )
            status = "passed"
            if policy == "FORBIDDEN":
                status = "passed" if overlap == 0 else "failed"
            elif policy == "DIAGNOSTIC_ONLY" and overlap:
                status = "warning"
            smaller = min(len(edge_sets[left]), len(edge_sets[right]))
            rows.append(
                {
                    "route_a": left,
                    "route_b": right,
                    "overlapping_agent_pairs": overlap,
                    "percentage_of_smaller_route": overlap / max(1, smaller),
                    "policy": policy,
                    "status": status,
                    "interpretation": (
                        "Distinct physical settings may create multiple exposure opportunities; "
                        "this is not duplicate storage of one encounter."
                        if policy == "ALLOWED_DISTINCT_SETTING"
                        else "Nested same-setting route layers must not repeat the same pair."
                        if policy == "FORBIDDEN"
                        else (
                            "Overlap is retained as a diagnostic because route semantics "
                            "need review."
                        )
                    ),
                }
            )
    return rows


def _quantile(values: list[float] | list[int], q: float) -> float:
    if not values:
        return 0.0
    if q <= 0:
        return float(values[0])
    if q >= 1:
        return float(values[-1])
    position = (len(values) - 1) * q
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return float(values[low])
    fraction = position - low
    return float(values[low] + fraction * (values[high] - values[low]))


def _route_diagnostics(
    generated: GeneratedNetworks,
    baseline_date: date,
) -> dict[str, Any]:
    agent_info = {row["agent_id"]: row for row in generated.m3_input.resident_structure}
    agent_info.update(
        {
            row["agent_id"]: {
                **agent_info.get(row["agent_id"], {}),
                "household_id": row.get("household_id"),
                "care_setting_id": row.get("care_setting_id"),
            }
            for row in generated.m2_input.residents
        }
    )
    output: dict[str, Any] = {}
    for route_id, spec in sorted(generated.route_specs.items()):
        snapshot = generated.route_snapshot(route_id, baseline_date)
        eligible = {row["agent_id"] for row in generated.route_memberships.get(route_id, [])}
        route = _analyse_edges(list(snapshot.edges), eligible, agent_info)
        route["route_id"] = route_id
        route["route_family"] = spec["route_family"]
        route["persistence"] = spec["persistence"]
        route["active_calendar"] = spec["active_calendar"]
        route["indoor"] = spec["indoor"]
        route["baseline_date"] = baseline_date.isoformat()
        route["age_mixing_matrix"] = _age_mixing_matrix(snapshot.edges, agent_info)
        diagnostic_dates = generated.config.snapshot_dates
        snapshots = [generated.route_snapshot(route_id, when) for when in diagnostic_dates]
        edge_sets = [
            {(edge["p1"], edge["p2"]) for edge in snapshot.edges} for snapshot in snapshots
        ]
        if len(edge_sets) > 1:
            previous = edge_sets[0]
            overlaps = []
            new_edge_rates = []
            for current in edge_sets[1:]:
                overlaps.append(len(previous & current) / max(1, len(previous | current)))
                new_edge_rates.append(len(current - previous) / max(1, len(current)))
                previous = current
            route["repeated_edge_rate"] = sum(overlaps) / len(overlaps)
            route["cross_day_jaccard"] = overlaps
            route["new_edge_rate"] = new_edge_rates
        else:
            route["repeated_edge_rate"] = 0.0
            route["cross_day_jaccard"] = []
            route["new_edge_rate"] = []
        route["diagnostic_snapshot_dates"] = [when.isoformat() for when in diagnostic_dates]
        route["persistence_diagnostic_kind"] = "measurement"
        output[route_id] = route
    return output


def _is_care_setting(setting_type: str) -> bool:
    lowered = setting_type.lower()
    return "care" in lowered or "medical" in lowered


def _school_edge_breakdown(
    edges: tuple[dict[str, Any], ...], pupil_ids: set[str], staff_ids: set[str]
) -> dict[str, int]:
    counts = {"pupil_pupil": 0, "pupil_staff": 0, "staff_staff": 0, "other": 0}
    for edge in edges:
        left, right = edge["p1"], edge["p2"]
        left_staff, right_staff = left in staff_ids, right in staff_ids
        left_pupil, right_pupil = left in pupil_ids, right in pupil_ids
        if left_staff and right_staff:
            counts["staff_staff"] += 1
        elif (left_staff and right_pupil) or (right_staff and left_pupil):
            counts["pupil_staff"] += 1
        elif left_pupil and right_pupil:
            counts["pupil_pupil"] += 1
        else:
            counts["other"] += 1
    return counts


def _occupational_staffing_audit(
    staff_ids: set[str],
    jobs_by_agent: dict[str, list[dict[str, Any]]],
    effective_work_jobs_by_agent: dict[str, list[dict[str, Any]]],
    ordinary_workplace_participants: set[str],
) -> dict[str, Any]:
    primary_membership = {
        agent_id
        for agent_id in staff_ids
        if any(job["job_role"] == "primary" for job in jobs_by_agent.get(agent_id, []))
    }
    secondary_membership = {
        agent_id
        for agent_id in staff_ids
        if any(job["job_role"] == "secondary" for job in jobs_by_agent.get(agent_id, []))
    }
    effective_ordinary_membership = {
        agent_id for agent_id in staff_ids if effective_work_jobs_by_agent.get(agent_id)
    }
    unmapped_primary = {
        agent_id
        for agent_id in primary_membership
        if any(
            job["job_role"] == "primary" for job in effective_work_jobs_by_agent.get(agent_id, [])
        )
    }
    unexpected_route_participants = (
        staff_ids & ordinary_workplace_participants
    ) - secondary_membership
    return {
        "endpoints": len(staff_ids),
        "m3_primary_job_membership": len(primary_membership),
        "primary_job_reinterpreted_to_institution": len(primary_membership) - len(unmapped_primary),
        "m3_secondary_job_workers": len(secondary_membership),
        "effective_ordinary_workplace_job_membership": len(effective_ordinary_membership),
        "ordinary_workplace_route_participants_any_snapshot": len(
            staff_ids & ordinary_workplace_participants
        ),
        "unintended_occupational_double_counting": len(unexpected_route_participants),
        "double_counting_diagnostic_kind": "measurement",
        "mapping_rule": (
            "institutional school/care staff keep M3 identity and job rows, but their "
            "primary job is reinterpreted as the institutional role for ordinary workplace "
            "routes; explicitly represented secondary jobs remain."
        ),
    }


def _institutional_staff_commute_metadata(
    m3_input: M3StructureInput, staffing: StaffingAllocation
) -> dict[str, dict[str, Any]]:
    """Build the effective institutional destination overlay for transport routes.

    M3 job rows remain unchanged.  At the M4 route boundary, an institutional
    assignment supplies the physical school/care destination; a full M3
    work-from-home assignment is replaced by ``other`` because a staff endpoint
    must be physically present for its institutional contact route.
    """

    m3_by_agent = {row["agent_id"]: row for row in m3_input.resident_structure}
    metadata: dict[str, dict[str, Any]] = {}
    for assignment in [*staffing.school_assignments, *staffing.care_assignments]:
        agent_id = assignment["agent_id"]
        if agent_id in metadata:
            raise DataBuildError("institutional staff has more than one effective assignment")
        source = m3_by_agent[agent_id]
        source_mode = source.get("commute_mode")
        metadata[agent_id] = {
            "institution_type": "school" if "school_id" in assignment else "care",
            "institution_id": assignment.get("school_id", assignment.get("setting_id")),
            "institution_parish": assignment["institution_parish"],
            "source_work_parish": source.get("work_parish"),
            "source_commute_mode": source_mode,
            "effective_work_parish": assignment["institution_parish"],
            "effective_commute_mode": "other" if source_mode == "work_from_home" else source_mode,
            "work_from_home_days_per_week": 0
            if source_mode == "work_from_home"
            else source.get("work_from_home_days_per_week", 0),
            "status": "synthetic_institutional_overlay",
        }
    return metadata


def generate_networks(
    config: NetworkGenerationConfig,
    m2_input: M2PopulationInput,
    m3_input: M3StructureInput,
    root: Path | None = None,
) -> GeneratedNetworks:
    """Generate reproducible M4 route structure from validated M2/M3 artifacts."""

    started = time.perf_counter()
    before_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if m2_input.manifest.mode != config.mode or m3_input.manifest.mode != config.mode:
        raise DataBuildError("M4 mode must match both M2 and M3 artifacts")
    if m2_input.manifest.actual_population != m3_input.manifest.actual_population:
        raise DataBuildError("M2 and M3 population counts do not match")

    m2_by_agent = {row["agent_id"]: row for row in m2_input.residents}
    m3_by_agent = {row["agent_id"]: row for row in m3_input.resident_structure}
    if set(m2_by_agent) != set(m3_by_agent):
        raise DataBuildError("M2 and M3 agent ID universes do not match")
    agent_ids = sorted(m2_by_agent)
    route_specs = _build_route_specs(config)
    staffing: StaffingAllocation = build_staffing_allocation(
        root or Path(__file__).resolve().parents[2],
        m2_input,
        m3_input,
        seed=config.seed,
        fte_per_endpoint=config.school_fte_per_synthetic_endpoint,
        care_coverage_multiplier=config.care_shift_coverage_multiplier,
        include_leadership=config.include_school_leadership,
    )
    structural_edges: dict[str, list[dict[str, Any]]] = {}
    route_memberships: dict[str, list[dict[str, Any]]] = {}
    dynamic_builders: dict[str, Callable[[date], list[dict[str, Any]]]] = {}

    households: dict[str, list[str]] = defaultdict(list)
    private_agents: set[str] = set()
    for row in m2_input.residents:
        household_id = row.get("household_id")
        if household_id is not None:
            households[household_id].append(row["agent_id"])
            private_agents.add(row["agent_id"])
    if "household" in route_specs:
        structural_edges["household"] = _deduplicate_edges(
            edge for group in households.values() for edge in _complete_group(group, 1.0, 3650)
        )
        route_memberships["household"] = _build_group_memberships(households, "household_id")

    class_groups: dict[str, list[str]] = defaultdict(list)
    school_year_groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in m3_input.school_assignments:
        class_groups[row["class_id"]].append(row["agent_id"])
        school_year_groups[(row["school_id"], row["school_year"])].append(row["agent_id"])
    school_year_route_groups = {
        key: list(group) + staffing.school_staff_by_school_year.get(key, [])
        for key, group in school_year_groups.items()
    }
    school_core_pairs = {
        (edge["p1"], edge["p2"])
        for class_id, group in class_groups.items()
        for edge in _complete_group(
            group + staffing.school_staff_by_class.get(class_id, []), 0.85, 180
        )
    }
    if "school_class" in route_specs:
        structural_edges["school_class"] = _deduplicate_edges(
            edge
            for class_id, group in class_groups.items()
            for edge in _complete_group(
                group + staffing.school_staff_by_class.get(class_id, []), 0.85, 180
            )
        )
        route_memberships["school_class"] = _build_group_memberships(class_groups, "class_id")
        route_memberships["school_class"].extend(
            {
                "membership": "school_staff_class",
                "group_id": class_id,
                "agent_id": agent_id,
            }
            for class_id, staff_ids in staffing.school_staff_by_class.items()
            for agent_id in sorted(staff_ids)
        )
    if "school_cross_class" in route_specs:
        route_memberships["school_cross_class"] = [
            {
                "membership": "school_year",
                "group_id": f"{school_id}|{school_year}",
                "agent_id": agent_id,
            }
            for (school_id, school_year), group in sorted(school_year_route_groups.items())
            for agent_id in sorted(set(group))
        ]

        def build_school_cross(snapshot_date: date) -> list[dict[str, Any]]:
            pupil_edges = _grouped_ring_edges(
                school_year_groups.values(),
                config.seed,
                "school_cross_class",
                snapshot_date,
                config.school_cross_class_contacts,
                0.5,
                14,
                school_core_pairs,
            )
            staff_edges = _school_staff_cross_edges(
                school_year_groups,
                staffing.school_staff_by_school_year,
                config.seed,
                snapshot_date,
                config.school_cross_class_contacts,
                0.5,
                14,
                school_core_pairs,
            )
            return _deduplicate_edges([*pupil_edges, *staff_edges])

        dynamic_builders["school_cross_class"] = build_school_cross

    jobs_by_agent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    jobs_by_workplace: dict[str, list[dict[str, Any]]] = defaultdict(list)
    jobs_by_team: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for job in m3_input.job_assignments:
        jobs_by_agent[job["agent_id"]].append(job)
        jobs_by_workplace[job["workplace_id"]].append(job)
        if job.get("team_id") is not None:
            jobs_by_team[job["team_id"]].append(job)
    institutional_staff_ids = {
        row["agent_id"] for row in staffing.school_assignments + staffing.care_assignments
    }
    work_route_jobs_by_agent: dict[str, list[dict[str, Any]]] = {
        agent_id: [
            job
            for job in jobs
            if not (agent_id in institutional_staff_ids and job["job_role"] == "primary")
        ]
        for agent_id, jobs in jobs_by_agent.items()
    }
    work_route_jobs_by_workplace: dict[str, list[dict[str, Any]]] = defaultdict(list)
    work_route_jobs_by_team: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for jobs in work_route_jobs_by_agent.values():
        for job in jobs:
            work_route_jobs_by_workplace[job["workplace_id"]].append(job)
            if job.get("team_id") is not None:
                work_route_jobs_by_team[job["team_id"]].append(job)
    workplace_team_pairs = {
        (edge["p1"], edge["p2"])
        for team_jobs in work_route_jobs_by_team.values()
        for edge in _complete_group([job["agent_id"] for job in team_jobs], 0.7, 365)
    }

    institutional_staff_commute = _institutional_staff_commute_metadata(m3_input, staffing)
    if "workplace_team" in route_specs:
        structural_edges["workplace_team"] = _deduplicate_edges(
            edge
            for team_jobs in work_route_jobs_by_team.values()
            for edge in _complete_group([job["agent_id"] for job in team_jobs], 0.7, 365)
        )
        route_memberships["workplace_team"] = _build_group_memberships(
            {
                team_id: [job["agent_id"] for job in jobs]
                for team_id, jobs in work_route_jobs_by_team.items()
            },
            "team_id",
        )

    if "workplace_transient" in route_specs:
        route_memberships["workplace_transient"] = _build_group_memberships(
            {
                workplace_id: [job["agent_id"] for job in jobs]
                for workplace_id, jobs in work_route_jobs_by_workplace.items()
            },
            "workplace_id",
        )

        def build_workplace_transient(snapshot_date: date) -> list[dict[str, Any]]:
            groups: list[list[str]] = []
            for workplace_id, jobs in sorted(work_route_jobs_by_workplace.items()):
                active = [
                    job["agent_id"]
                    for job in jobs
                    if _job_is_physical_on_date(job, job["agent_id"], snapshot_date, config.seed)
                ]
                groups.append(
                    _ordered_ids(
                        active,
                        config.seed,
                        "workplace",
                        workplace_id,
                        snapshot_date.isocalendar().week,
                    )
                )
            return _grouped_ring_edges(
                groups,
                config.seed,
                "workplace_transient",
                snapshot_date,
                config.workplace_transient_contacts,
                0.3,
                7,
                workplace_team_pairs,
            )

        dynamic_builders["workplace_transient"] = build_workplace_transient

    if "workplace_team" in route_specs:

        def build_workplace_team(snapshot_date: date) -> list[dict[str, Any]]:
            if snapshot_date.weekday() >= 5:
                return []
            active_agents_by_team = {
                team_id: [
                    job["agent_id"]
                    for job in jobs
                    if _job_is_physical_on_date(job, job["agent_id"], snapshot_date, config.seed)
                ]
                for team_id, jobs in work_route_jobs_by_team.items()
            }
            return _deduplicate_edges(
                edge
                for group in active_agents_by_team.values()
                for edge in _complete_group(group, 0.7, 1)
            )

        dynamic_builders["workplace_team"] = build_workplace_team

    care_groups: dict[str, list[str]] = defaultdict(list)
    care_setting_ids = {
        row["setting_id"]
        for row in m2_input.communal_settings
        if _is_care_setting(row["setting_type"])
    }
    for row in m2_input.residents:
        setting_id = row.get("care_setting_id")
        if isinstance(setting_id, str) and setting_id in care_setting_ids:
            care_groups[setting_id].append(row["agent_id"])
    if "care_resident" in route_specs:
        care_edges: list[dict[str, Any]] = []
        for setting_id, group in sorted(care_groups.items()):
            ordered = _ordered_ids(group, config.seed, "care", setting_id)
            cohorts = [
                ordered[index : index + config.care_cohort_capacity]
                for index in range(0, len(ordered), config.care_cohort_capacity)
            ]
            for cohort in cohorts:
                care_edges.extend(_complete_group(cohort, 0.9, 365))
            for left, right in zip(cohorts, cohorts[1:], strict=False):
                if left and right:
                    edge = _canonical_edge(left[0], right[0], 0.75, 365)
                    if edge is not None:
                        care_edges.append(edge)
        structural_edges["care_resident"] = _deduplicate_edges(care_edges)
        route_memberships["care_resident"] = _build_group_memberships(
            care_groups, "care_setting_id"
        )
    if "care_staff" in route_specs:
        care_staff_edges: list[dict[str, Any]] = []
        for setting_id, staff_ids in sorted(staffing.care_staff_by_setting.items()):
            residents = _ordered_ids(
                care_groups.get(setting_id, []), config.seed, "care-staff", setting_id
            )
            cohorts = [
                residents[index : index + config.care_cohort_capacity]
                for index in range(0, len(residents), config.care_cohort_capacity)
            ]
            if not cohorts:
                continue
            for staff_index, staff_id in enumerate(sorted(staff_ids)):
                cohort = cohorts[staff_index % len(cohorts)]
                care_staff_edges.extend(
                    edge
                    for resident_id in cohort
                    if (
                        edge := _canonical_edge(
                            staff_id,
                            resident_id,
                            0.65,
                            1,
                        )
                    )
                    is not None
                )
        structural_edges["care_staff"] = _deduplicate_edges(care_staff_edges)
        route_memberships["care_staff"] = [
            {
                "membership": "care_staff_setting",
                "group_id": setting_id,
                "agent_id": agent_id,
            }
            for setting_id, staff_ids in sorted(staffing.care_staff_by_setting.items())
            for agent_id in sorted(staff_ids)
        ]

    worker_jobs = {
        agent_id: jobs
        for agent_id, jobs in jobs_by_agent.items()
        if agent_id in m3_by_agent and m3_by_agent[agent_id]["economic_status"] == "employed"
    }
    car_commuters_by_household_destination: dict[tuple[str, str], list[str]] = defaultdict(list)
    bus_groups: dict[tuple[str, str, int], list[str]] = defaultdict(list)
    car_commuter_ids: set[str] = set()
    for agent_id, jobs in worker_jobs.items():
        primary = next((job for job in jobs if job["job_role"] == "primary"), None)
        if primary is None:
            continue
        resident = m3_by_agent[agent_id]
        institutional = institutional_staff_commute.get(agent_id)
        mode = (
            institutional["effective_commute_mode"]
            if institutional
            else resident.get("commute_mode")
        )
        if mode not in {"car", "bus"}:
            continue
        home = resident["home_parish"]
        work_parish = (
            institutional["effective_work_parish"] if institutional else primary["work_parish"]
        )
        time_band = _stable_int(config.seed, "time-band", agent_id) % 3
        if mode == "car":
            household_id = m2_by_agent[agent_id].get("household_id")
            if household_id is not None:
                car_commuters_by_household_destination[(household_id, work_parish)].append(agent_id)
            car_commuter_ids.add(agent_id)
        else:
            bus_groups[(home, work_parish, int(time_band))].append(agent_id)
    shared_vehicle_groups: dict[str, list[str]] = {}
    for (household_id, work_parish), group in sorted(
        car_commuters_by_household_destination.items()
    ):
        ordered = _ordered_ids(
            group,
            config.seed,
            "carpool-household",
            household_id,
            work_parish,
        )
        for vehicle_number, start in enumerate(
            range(0, len(ordered), config.shared_vehicle_capacity), start=1
        ):
            vehicle = ordered[start : start + config.shared_vehicle_capacity]
            if len(vehicle) >= 2:
                shared_vehicle_groups[f"{household_id}|{work_parish}|{vehicle_number:02d}"] = (
                    vehicle
                )
    shared_vehicle_participants = (
        set().union(*shared_vehicle_groups.values()) if shared_vehicle_groups else set()
    )
    shared_vehicle_diagnostics = {
        "car_alone_commuters": len(car_commuter_ids - shared_vehicle_participants),
        "drivers_with_passengers": len(shared_vehicle_groups),
        "passengers": sum(max(0, len(group) - 1) for group in shared_vehicle_groups.values()),
        "shared_vehicle_participants": len(shared_vehicle_participants),
        "synthetic_vehicles": len(shared_vehicle_groups),
        "occupancy_distribution": dict(
            sorted(Counter(len(group) for group in shared_vehicle_groups.values()).items())
        ),
        "household_only_shared_rides": len(shared_vehicle_groups),
        "non_household_shared_rides": 0,
        "unmatched_car_commuters": len(car_commuter_ids - shared_vehicle_participants),
        "eligibility_assumption": (
            "Only same-household car commuters with the same synthetic work parish are matched; "
            "the canonical commute table has no driver/passenger split, so unmatched car "
            "commuters remain outside the shared-vehicle route."
        ),
    }
    if "shared_vehicle" in route_specs:
        route_memberships["shared_vehicle"] = [
            {
                "membership": "synthetic_vehicle_cohort",
                "group_id": key,
                "agent_id": agent_id,
            }
            for key, group in sorted(shared_vehicle_groups.items())
            for agent_id in sorted(group)
        ]

        def build_shared_vehicle(snapshot_date: date) -> list[dict[str, Any]]:
            if snapshot_date.weekday() >= 5:
                return []
            edges: list[dict[str, Any]] = []
            for key, group in sorted(shared_vehicle_groups.items()):
                active = [
                    agent_id
                    for agent_id in group
                    if _job_is_physical_on_date(
                        next(job for job in worker_jobs[agent_id] if job["job_role"] == "primary"),
                        agent_id,
                        snapshot_date,
                        config.seed,
                    )
                ]
                ordered = _ordered_ids(
                    active,
                    config.seed,
                    "vehicle",
                    key,
                    snapshot_date.isocalendar().week // 4,
                )
                for index in range(0, len(ordered), config.shared_vehicle_capacity):
                    edges.extend(
                        _complete_group(
                            ordered[index : index + config.shared_vehicle_capacity],
                            0.7,
                            28,
                        )
                    )
            return _deduplicate_edges(edges)

        dynamic_builders["shared_vehicle"] = build_shared_vehicle
    if "bus" in route_specs:
        route_memberships["bus"] = [
            {
                "membership": "synthetic_transit_cohort",
                "group_id": "|".join(map(str, key)),
                "agent_id": agent_id,
            }
            for key, group in sorted(bus_groups.items())
            for agent_id in sorted(group)
        ]

        def build_bus(snapshot_date: date) -> list[dict[str, Any]]:
            if snapshot_date.weekday() >= 5:
                return []
            edges: list[dict[str, Any]] = []
            for key, group in sorted(bus_groups.items()):
                active = [
                    agent_id
                    for agent_id in group
                    if _job_is_physical_on_date(
                        next(job for job in worker_jobs[agent_id] if job["job_role"] == "primary"),
                        agent_id,
                        snapshot_date,
                        config.seed,
                    )
                ]
                ordered = _ordered_ids(
                    active,
                    config.seed,
                    "bus",
                    *key,
                    snapshot_date.isocalendar().week,
                )
                for index in range(0, len(ordered), config.bus_cohort_capacity):
                    edges.extend(
                        _complete_group(
                            ordered[index : index + config.bus_cohort_capacity],
                            0.45,
                            7,
                        )
                    )
            return _deduplicate_edges(edges)

        dynamic_builders["bus"] = build_bus

    def community_builder(
        route_id: str, contacts: int, weight: float
    ) -> Callable[[date], list[dict[str, Any]]]:
        regular_contacts = round(contacts * float(config.community_regular_edge_fraction))
        daily_contacts = max(0, contacts - regular_contacts)

        def mixed_edges(
            participants: dict[str, list[str]],
            token: object,
            contact_count: int,
            persistence_days: int,
        ) -> list[dict[str, Any]]:
            by_band = {
                parish: {
                    band: sorted(
                        agent_id
                        for agent_id in ids
                        if _age_band(m3_by_agent[agent_id]["age"]) == band
                    )
                    for band in AGE_BANDS
                }
                for parish, ids in participants.items()
            }
            edges: list[dict[str, Any]] = []
            for _parish, band_groups in sorted(by_band.items()):
                for source_band_index, source_band in enumerate(AGE_BANDS):
                    sources = band_groups[source_band]
                    for source in sources:
                        probabilities = config.community_age_mixing[source_band_index]
                        for contact_index in range(contact_count):
                            draw = (
                                _stable_int(
                                    config.seed,
                                    "community-age-target",
                                    route_id,
                                    token,
                                    source,
                                    contact_index,
                                )
                                % 1_000_000
                                / 1_000_000
                            )
                            cumulative = 0.0
                            target_band = AGE_BANDS[-1]
                            for candidate_band, probability in zip(
                                AGE_BANDS, probabilities, strict=True
                            ):
                                cumulative += float(probability)
                                if draw < cumulative:
                                    target_band = candidate_band
                                    break
                            candidates = [
                                agent_id
                                for agent_id in band_groups[target_band]
                                if agent_id != source
                            ]
                            if not candidates:
                                continue
                            target = candidates[
                                _stable_int(
                                    config.seed,
                                    "community-age-choice",
                                    route_id,
                                    token,
                                    source,
                                    contact_index,
                                )
                                % len(candidates)
                            ]
                            edge = _canonical_edge(source, target, weight, persistence_days)
                            if edge is not None:
                                edges.append(edge)
            return _deduplicate_edges(edges)

        regular_groups: dict[str, list[str]] = defaultdict(list)
        regular_probability = 65 if route_id == "community_indoor" else 45
        for agent_id in agent_ids:
            if (
                _stable_int(config.seed, "community-regular", route_id, agent_id) % 100
                < regular_probability
            ):
                regular_groups[m3_by_agent[agent_id]["home_parish"]].append(agent_id)
        regular_edges = mixed_edges(
            regular_groups,
            "regular",
            regular_contacts,
            int(max(7, config.community_regular_edge_fraction * 30)),
        )

        def build(snapshot_date: date) -> list[dict[str, Any]]:
            groups: dict[str, list[str]] = defaultdict(list)
            for agent_id in agent_ids:
                info = m3_by_agent[agent_id]
                if route_id == "community_indoor":
                    weekday_probability = 58 if info["age"] >= 18 else 35
                    weekend_probability = 70 if info["age"] >= 18 else 55
                else:
                    weekday_probability = 28 if info["age"] >= 18 else 20
                    weekend_probability = 55 if info["age"] >= 18 else 45
                if _participation(
                    agent_id,
                    info["age"],
                    snapshot_date,
                    config.seed,
                    route_id,
                    weekend_probability,
                    weekday_probability,
                ):
                    groups[info["home_parish"]].append(agent_id)
            daily_edges = mixed_edges(groups, snapshot_date.isoformat(), daily_contacts, 1)
            return _deduplicate_edges(
                [
                    *regular_edges,
                    *daily_edges,
                ]
            )

        return build

    if "community_indoor" in route_specs:
        route_memberships["community_indoor"] = [
            {"membership": "community_participant_pool", "group_id": "all", "agent_id": agent_id}
            for agent_id in agent_ids
        ]
        dynamic_builders["community_indoor"] = community_builder(
            "community_indoor", config.community_indoor_contacts, config.indoor_weight
        )
    if "community_outdoor" in route_specs:
        route_memberships["community_outdoor"] = [
            {"membership": "community_participant_pool", "group_id": "all", "agent_id": agent_id}
            for agent_id in agent_ids
        ]
        dynamic_builders["community_outdoor"] = community_builder(
            "community_outdoor", config.community_outdoor_contacts, config.outdoor_weight
        )

    for route_id in route_specs:
        structural_edges.setdefault(route_id, [])
        route_memberships.setdefault(route_id, [])
    generated = GeneratedNetworks(
        config=config,
        m2_input=m2_input,
        m3_input=m3_input,
        agent_ids=agent_ids,
        route_specs=route_specs,
        structural_edges={
            route_id: _deduplicate_edges(edges) for route_id, edges in structural_edges.items()
        },
        route_memberships=route_memberships,
        school_staff_assignments=staffing.school_assignments,
        care_staff_assignments=staffing.care_assignments,
        staffing_diagnostics=staffing.diagnostics,
        staffing_provenance=staffing.provenance,
        diagnostics={},
        logical_content_hash="",
        runtime_seconds=0.0,
        peak_memory_bytes=None,
        _dynamic_builders=dynamic_builders,
    )
    baseline_date = config.snapshot_dates[0]
    route_diagnostics = _route_diagnostics(generated, baseline_date)
    baseline_snapshot = generated.snapshot(baseline_date)
    route_overlap_matrix = _route_overlap_matrix(generated, baseline_date)
    ordinary_workplace_participants = {
        endpoint
        for snapshot_date in config.snapshot_dates
        for route_id in ("workplace_team", "workplace_transient")
        if route_id in generated.route_specs
        for edge in generated.route_snapshot(route_id, snapshot_date).edges
        for endpoint in (edge["p1"], edge["p2"])
    }
    route_participation: dict[str, set[str]] = {
        route_id: {endpoint for edge in snapshot.edges for endpoint in (edge["p1"], edge["p2"])}
        for route_id, snapshot in baseline_snapshot.items()
    }
    non_household_route_ids = [
        route_id for route_id, spec in route_specs.items() if spec["route_family"] != "household"
    ]
    non_household_participants = (
        set().union(*(route_participation[route_id] for route_id in non_household_route_ids))
        if non_household_route_ids
        else set()
    )
    route_type_count: dict[int, int] = defaultdict(int)
    for agent_id in agent_ids:
        route_type_count[
            sum(agent_id in participants for participants in route_participation.values())
        ] += 1
    secondary_job_agents = {
        agent_id
        for agent_id, jobs in jobs_by_agent.items()
        if any(job["job_role"] == "secondary" for job in jobs)
    }
    bridge_agents = {
        agent_id
        for agent_id, jobs in jobs_by_agent.items()
        if len({job["workplace_id"] for job in jobs}) > 1
    }
    school_agents = {row["agent_id"] for row in m3_input.school_assignments}
    school_staff_ids = {row["agent_id"] for row in staffing.school_assignments}
    care_staff_ids = {row["agent_id"] for row in staffing.care_assignments}
    community_members = {
        agent_id
        for route_id in ("community_indoor", "community_outdoor")
        for membership in route_memberships.get(route_id, [])
        for agent_id in (membership["agent_id"],)
    }
    worker_agents = set(worker_jobs)
    household_school_connectivity = sum(
        bool(set(group) & school_agents) for group in households.values()
    )
    household_work_connectivity = sum(
        bool(set(group) & worker_agents) for group in households.values()
    )
    school_occupational_audit = _occupational_staffing_audit(
        school_staff_ids,
        jobs_by_agent,
        work_route_jobs_by_agent,
        ordinary_workplace_participants,
    )
    care_occupational_audit = _occupational_staffing_audit(
        care_staff_ids,
        jobs_by_agent,
        work_route_jobs_by_agent,
        ordinary_workplace_participants,
    )
    staffing_diagnostics = {
        **staffing.diagnostics,
        "school": {
            **staffing.diagnostics["school"],
            "route_edge_breakdown": {
                route_id: _school_edge_breakdown(
                    baseline_snapshot[route_id].edges,
                    school_agents,
                    school_staff_ids,
                )
                for route_id in ("school_class", "school_cross_class")
                if route_id in baseline_snapshot
            },
            "staff_with_community_bridge_membership": len(school_staff_ids & community_members),
        },
        "care": {
            **staffing.diagnostics["care"],
            "resident_staff_edge_count": len(
                baseline_snapshot.get(
                    "care_staff", RouteSnapshot("care_staff", baseline_date, ())
                ).edges
            ),
            "staff_with_community_bridge_membership": len(care_staff_ids & community_members),
        },
        "occupational_staff_mapping": {
            "school": school_occupational_audit,
            "care": care_occupational_audit,
            "household_community_transport_preserved": True,
            "unintended_occupational_double_counting": (
                school_occupational_audit["unintended_occupational_double_counting"]
                + care_occupational_audit["unintended_occupational_double_counting"]
            ),
            "double_counting_diagnostic_kind": "measurement",
            "institutional_staff_commute_metadata": institutional_staff_commute,
        },
    }
    generated.staffing_diagnostics = staffing_diagnostics
    diagnostics = {
        "schema_version": "1.0",
        "status": (
            "failed" if any(row["status"] == "failed" for row in route_overlap_matrix) else "passed"
        ),
        "mode": config.mode,
        "generated_population": len(agent_ids),
        "route_count": len(route_specs),
        "routes": route_diagnostics,
        "cross_route": {
            "zero_non_household_contacts": len(set(agent_ids) - non_household_participants),
            "agents_by_route_type_count": {
                str(count): number for count, number in sorted(route_type_count.items())
            },
            "multi_job_workers": len(secondary_job_agents),
            "multi_job_workplace_bridges": len(bridge_agents),
            "households_with_school_connectivity": household_school_connectivity,
            "households_with_work_connectivity": household_work_connectivity,
            "care_staff_community_bridges": len(care_staff_ids & community_members),
            "route_overlap_matrix": route_overlap_matrix,
            "shared_vehicle": shared_vehicle_diagnostics,
        },
        "calendars": {
            "school_calendar_year": config.school_calendar_year,
            "school_calendar_provenance": SCHOOL_CALENDAR_PROVENANCE.get(
                str(config.school_calendar_year),
                {
                    "source_id": None,
                    "source_sha256": None,
                    "status": "configuration_only",
                    "coverage": "caller-supplied reference calendar",
                },
            ),
            "school_term_periods": [
                [start.isoformat(), end.isoformat()] for start, end in config.school_term_periods
            ],
            "school_holiday_periods": [
                [start.isoformat(), end.isoformat()] for start, end in config.school_holiday_periods
            ],
            "school_term_rule": (
                "weekdays inside the frozen common Jersey reference-year term periods, "
                "excluding official half-term holiday periods; institution-specific inset "
                "days are not modelled"
            ),
            "work_rule": "synthetic deterministic weekday schedules from M3 days/remote days",
            "community_rule": (
                "structural broad-age mixing matrix with a configured regular-contact pool "
                "plus a daily refreshed component"
            ),
            "community_regular_edge_fraction": config.community_regular_edge_fraction,
            "community_age_bands": list(AGE_BANDS),
            "community_age_mixing": [list(row) for row in config.community_age_mixing],
            "time_step": "daily; no hourly event simulation",
        },
        "staffing": staffing_diagnostics,
        "provenance": {
            "m2_artifact_id": m2_input.manifest.artifact_id,
            "m2_logical_content_hash": m2_input.manifest.logical_content_hash,
            "m3_artifact_id": m3_input.manifest.artifact_id,
            "m3_logical_content_hash": m3_input.manifest.logical_content_hash,
            "staffing": staffing.provenance,
            "assumptions": [
                (
                    "School staff endpoints are synthetic allocations from the existing "
                    "M3 education-health worker pool; no real school roster is claimed."
                ),
                (
                    "Care staff endpoints apply Care Commission regulatory minima with a "
                    "configurable shift-coverage multiplier; no actual roster is claimed."
                ),
                (
                    "Cross-class, cross-team, bus, carpool and community contacts are "
                    "structural scenario assumptions, not observations."
                ),
                (
                    "Relative edge weights encode contact opportunity only and are not "
                    "disease-specific transmission probabilities."
                ),
            ],
        },
    }
    generated.diagnostics = diagnostics
    generated.logical_content_hash = sha256_bytes(
        canonical_json_bytes(
            {
                "agent_ids": agent_ids,
                "route_specs": generated.route_specs,
                "structural_edges": generated.structural_edges,
                "memberships": generated.route_memberships,
                "school_staff_assignments": generated.school_staff_assignments,
                "care_staff_assignments": generated.care_staff_assignments,
                "staffing_provenance": generated.staffing_provenance,
                "snapshots": {
                    route_id: [
                        {
                            "date": when.isoformat(),
                            "edges": list(generated.route_snapshot(route_id, when).edges),
                        }
                        for when in config.snapshot_dates
                    ]
                    for route_id in sorted(route_specs)
                },
            }
        )
    )
    generated.runtime_seconds = time.perf_counter() - started
    generated.peak_memory_bytes = max(
        before_memory, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    )
    generated.diagnostics["benchmark"] = {
        "construction_runtime_seconds": generated.runtime_seconds,
        "peak_memory_bytes": generated.peak_memory_bytes,
        "total_structural_edges": sum(len(edges) for edges in generated.structural_edges.values()),
        "total_baseline_edges": sum(len(snapshot.edges) for snapshot in baseline_snapshot.values()),
        "agent_count": len(agent_ids),
        "snapshot_dates": [when.isoformat() for when in config.snapshot_dates],
    }
    return generated
