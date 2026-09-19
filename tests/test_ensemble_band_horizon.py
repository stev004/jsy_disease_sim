"""Regression tests for M6 metric-specific horizon semantics."""

from __future__ import annotations

from jersey_outbreak.ensemble import _completed_grid_rows, _summary_rows


def test_ci_incidence_band_does_not_fabricate_tail_zeroes() -> None:
    """A shorter replicate horizon is null/non-contributing, not a zero."""

    trajectories = {
        101: (
            {
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_new_infections",
                "date": "2025-01-01",
                "value": 2,
            },
            # Date 2025-01-02 is a genuine quiet day inside this replicate's
            # horizon and must be completed as a structural zero.
            {
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_new_infections",
                "date": "2025-01-03",
                "value": 1,
            },
        ),
        102: (
            {
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_new_infections",
                "date": "2025-01-01",
                "value": 4,
            },
            {
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_new_infections",
                "date": "2025-01-02",
                "value": 6,
            },
            {
                "scope": "epidemic",
                "key": "all",
                "metric": "latent_new_infections",
                "date": "2025-01-03",
                "value": 8,
            },
        ),
    }
    duration = ("2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04")

    grid = _completed_grid_rows(
        trajectories,
        successful_seeds=(101, 102),
        failed_seeds=(),
        horizon=duration,
    )
    short_tail = next(row for row in grid if row["seed"] == 101 and row["date"] == "2025-01-04")
    quiet_day = next(row for row in grid if row["seed"] == 101 and row["date"] == "2025-01-02")
    assert quiet_day["value"] == 0.0
    assert quiet_day["cell_semantic"] == "structural_zero"
    assert quiet_day["contributes"] is True
    assert short_tail["value"] is None
    assert short_tail["cell_semantic"] == "outside_metric_horizon"
    assert short_tail["contributes"] is False

    summary = _summary_rows(
        trajectories,
        0.25,
        0.75,
        requested_replicates=2,
        horizon=duration,
    )
    by_date = {row["date"]: row for row in summary}
    assert by_date["2025-01-02"]["median"] == 3.0
    assert by_date["2025-01-04"]["median"] is None
    assert by_date["2025-01-04"]["lower_value"] is None
    assert by_date["2025-01-04"]["upper_value"] is None
    assert by_date["2025-01-04"]["cell_semantic"] == "outside_metric_horizon"
    assert by_date["2025-01-04"]["contributing_replicates"] == 0
    assert by_date["2025-01-04"]["outside_metric_horizon_replicates"] == 2
