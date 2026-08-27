"""M7 route-shift and paired outcome summaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from .outbreak_runner import OutbreakRunResult


@dataclass(frozen=True)
class InterventionComparison:
    """Explicit health and route outcomes for one matched baseline/scenario pair."""

    comparison_id: str
    scenario_comparison: tuple[dict[str, Any], ...]
    route_shift: tuple[dict[str, Any], ...]
    paired_seed_comparison: tuple[dict[str, Any], ...]


def _epidemic_metric(result: OutbreakRunResult, key: str) -> float:
    return float(result.daily_epidemic[-1][key])


def _peak(result: OutbreakRunResult, key: str) -> tuple[float, str]:
    row = max(result.daily_epidemic, key=lambda item: (float(item[key]), item["date"]))
    return float(row[key]), str(row["date"])


def route_shift_rows(
    baseline: OutbreakRunResult, intervention: OutbreakRunResult
) -> tuple[dict[str, Any], ...]:
    """Report absolute route counts and route shares before and after intervention."""

    # The daily route table's cumulative column is the stable comparison unit;
    # use its final value rather than only the final day's incidence.
    base_counts = {
        row["route_id"]: int(row["cumulative_infections"])
        for row in baseline.daily_route
        if row["date"] == baseline.daily_epidemic[-1]["date"]
        and row["route_id"] not in {"seeded", "exogenous_import"}
    }
    int_counts = {
        row["route_id"]: int(row["cumulative_infections"])
        for row in intervention.daily_route
        if row["date"] == intervention.daily_epidemic[-1]["date"]
        and row["route_id"] not in {"seeded", "exogenous_import"}
    }
    route_ids = sorted(set(base_counts) | set(int_counts))
    base_total = sum(base_counts.values())
    int_total = sum(int_counts.values())
    return tuple(
        {
            "route_id": route_id,
            "baseline_absolute_infections": base_counts.get(route_id, 0),
            "intervention_absolute_infections": int_counts.get(route_id, 0),
            "absolute_difference": int_counts.get(route_id, 0) - base_counts.get(route_id, 0),
            "baseline_share": base_counts.get(route_id, 0) / base_total if base_total else 0.0,
            "intervention_share": int_counts.get(route_id, 0) / int_total if int_total else 0.0,
            "share_difference": (int_counts.get(route_id, 0) / int_total if int_total else 0.0)
            - (base_counts.get(route_id, 0) / base_total if base_total else 0.0),
            "interpretation": (
                "Shares are relative composition; a higher share is not an absolute increase."
            ),
        }
        for route_id in route_ids
    )


def _intervention_burden(result: OutbreakRunResult) -> dict[str, float]:
    rows = result.intervention_state
    return {
        "days_isolated": float(
            sum(
                row["active_agents"] for row in rows if row["intervention_type"] == "case_isolation"
            )
        ),
        "household_quarantine_burden": float(sum(row["active_households"] for row in rows)),
        "school_days_affected": float(
            sum(
                row["active_settings"]
                for row in rows
                if row["intervention_type"] == "school_closure"
            )
        ),
        "work_from_home_agent_days": float(
            sum(
                row["active_agents"]
                for row in rows
                if row["intervention_type"] == "workplace_reduction"
            )
        ),
        "effectively_protected_agent_days": float(
            sum(row["active_agents"] for row in rows if row["intervention_type"] == "vaccination")
        ),
        "vaccine_doses_administered": float(
            sum(event["action"] == "vaccine_administered" for event in result.intervention_events)
        ),
    }


def compare_intervention_runs(
    baseline: OutbreakRunResult,
    intervention: OutbreakRunResult,
    *,
    comparison_id: str,
) -> InterventionComparison:
    """Compare matched runs without collapsing health and social effects."""

    if baseline.config.seed != intervention.config.seed:
        raise ValueError("intervention comparison requires matched seeds")
    if (
        baseline.config.start_date != intervention.config.start_date
        or baseline.config.duration_days != intervention.config.duration_days
    ):
        raise ValueError("intervention comparison requires the same date horizon")
    if (
        baseline.generated.m2_input.manifest.logical_content_hash
        != intervention.generated.m2_input.manifest.logical_content_hash
    ):
        raise ValueError("intervention comparison requires the same M2 parent")
    if (
        baseline.generated.m3_input.manifest.logical_content_hash
        != intervention.generated.m3_input.manifest.logical_content_hash
    ):
        raise ValueError("intervention comparison requires the same M3 parent")
    if baseline.generated.logical_content_hash != intervention.generated.logical_content_hash:
        raise ValueError("intervention comparison requires the same M4 parent")
    base_cumulative = _epidemic_metric(baseline, "cumulative_total_infections")
    int_cumulative = _epidemic_metric(intervention, "cumulative_total_infections")
    base_peak, base_peak_date = _peak(baseline, "prevalence")
    int_peak, int_peak_date = _peak(intervention, "prevalence")
    comparison_rows = [
        {
            "comparison_id": comparison_id,
            "seed": baseline.config.seed,
            "metric": "cumulative_total_infections",
            "baseline_value": base_cumulative,
            "intervention_value": int_cumulative,
            "absolute_difference": int_cumulative - base_cumulative,
            "relative_difference": (
                (int_cumulative - base_cumulative) / base_cumulative if base_cumulative else None
            ),
        },
        {
            "comparison_id": comparison_id,
            "seed": baseline.config.seed,
            "metric": "peak_prevalence",
            "baseline_value": base_peak,
            "intervention_value": int_peak,
            "absolute_difference": int_peak - base_peak,
            "relative_difference": (int_peak - base_peak) / base_peak if base_peak else None,
        },
        {
            "comparison_id": comparison_id,
            "seed": baseline.config.seed,
            "metric": "peak_timing_days",
            "baseline_value": (
                date.fromisoformat(base_peak_date) - baseline.config.start_date
            ).days,
            "intervention_value": (
                date.fromisoformat(int_peak_date) - intervention.config.start_date
            ).days,
            "absolute_difference": (
                date.fromisoformat(int_peak_date) - intervention.config.start_date
            ).days
            - (date.fromisoformat(base_peak_date) - baseline.config.start_date).days,
            "relative_difference": None,
        },
    ]
    for metric, values in _intervention_burden(intervention).items():
        comparison_rows.append(
            {
                "comparison_id": comparison_id,
                "seed": intervention.config.seed,
                "metric": metric,
                "baseline_value": 0.0,
                "intervention_value": values,
                "absolute_difference": values,
                "relative_difference": None,
            }
        )
    paired_rows_list: list[dict[str, Any]] = []
    base_epidemic = {row["date"]: row for row in baseline.daily_epidemic}
    int_epidemic = {row["date"]: row for row in intervention.daily_epidemic}
    for when in sorted(set(base_epidemic) | set(int_epidemic)):
        for metric in ("cumulative_total_infections", "new_infections", "prevalence"):
            base_value = base_epidemic.get(when, {}).get(metric)
            int_value = int_epidemic.get(when, {}).get(metric)
            paired_rows_list.append(
                {
                    "comparison_id": comparison_id,
                    "seed": baseline.config.seed,
                    "scope": "epidemic",
                    "key": "all",
                    "metric": metric,
                    "date": when,
                    "baseline_value": base_value,
                    "intervention_value": int_value,
                    "difference": (
                        int_value - base_value
                        if base_value is not None and int_value is not None
                        else None
                    ),
                }
            )
    paired_rows = tuple(paired_rows_list)
    return InterventionComparison(
        comparison_id=comparison_id,
        scenario_comparison=tuple(comparison_rows),
        route_shift=route_shift_rows(baseline, intervention),
        paired_seed_comparison=paired_rows,
    )
