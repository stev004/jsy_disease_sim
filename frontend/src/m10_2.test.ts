import { describe, expect, it } from 'vitest';
import type { DatasetRow, JobStatusResponse } from './api';
import {
  buildCompareFromMatchedComparison,
  buildCompareFromSummary,
  formatDate,
  latestAvailableMetricPoint,
  metricDateLabel,
  metricPointAtOrBefore,
  percentDifference,
  type ComparisonMetricPoint,
} from './views/compare/compareData';

const job = (): JobStatusResponse => ({
  job_id: 'm10-2-test-comparison',
  kind: 'scenario_compare',
  state: 'SUCCEEDED',
  phase: 'complete',
  created_at: '2025-01-01T00:00:00Z',
  started_at: '2025-01-01T00:00:00Z',
  finished_at: '2025-01-01T00:00:01Z',
  progress_fraction: null,
  request_hash: 'request',
  request: {
    kind: 'scenario_compare',
    start_date: '2025-01-06',
    duration_days: 8,
    replicate_seeds: [123],
    baseline: { scenario_id: 'baseline' },
    treated: { scenario_id: 'treated' },
  },
  scenario_hash: 'scenario',
  latent_hash: 'latent',
  bundle_hash: 'bundle',
  error: null,
  artifact_count: 1,
  verification_status: 'passed',
  worker_pid: null,
  last_heartbeat: null,
  exit_status: 0,
  result_manifest_path: null,
  result_manifest_hash: null,
  engine_git_commit: 'engine',
  dirty_worktree_flag: false,
  status_url: '/jobs/m10-2-test-comparison',
});

const point = (date: string, baseline: number, treated: number): ComparisonMetricPoint => ({
  date,
  baseline,
  treated,
  delta: treated - baseline,
});

const row = (
  metric: string,
  date: string,
  median: number,
  extra: Record<string, string | number | boolean | null> = {},
): DatasetRow => ({
  scope: 'epidemic',
  key: 'all',
  metric,
  date,
  median,
  ...extra,
});

const matchedRow = (
  metric: string,
  date: string,
  valueA: number,
  valueB: number,
): DatasetRow => ({
  seed: 123,
  scope: 'epidemic',
  key: 'all',
  metric,
  date,
  status: 'paired',
  value_a: valueA,
  value_b: valueB,
  difference: -999,
});

describe('M10.2 comparison metric horizons', () => {
  it('resolves independent horizons without discarding or extending a metric', () => {
    const metricA = [point('2025-01-01', 1, 2), point('2025-01-08', 8, 6)];
    const metricB = [
      ...metricA,
      point('2025-01-09', 9, 7),
      point('2025-01-10', 10, 8),
    ];

    expect(latestAvailableMetricPoint(metricA)?.date).toBe('2025-01-08');
    expect(metricPointAtOrBefore(metricA, '2025-01-10')).toEqual(metricA[1]);
    expect(latestAvailableMetricPoint(metricB)?.date).toBe('2025-01-10');
    expect(metricPointAtOrBefore(metricB, '2025-01-10')?.treated).toBe(8);
  });

  it('keeps cumulative and attack values available at their own persisted horizons', () => {
    const cumulative = 'latent_cumulative_infections';
    const attack = 'latent_ever_infected_fraction';
    const base = [
      row(cumulative, '2025-01-01', 10),
      row(cumulative, '2025-01-08', 85),
      row(attack, '2025-01-01', 0.01),
      row(attack, '2025-01-10', 0.1),
    ];
    const treated = [
      row(cumulative, '2025-01-01', 8),
      row(cumulative, '2025-01-08', 63),
      row(attack, '2025-01-01', 0.008),
      row(attack, '2025-01-10', 0.08),
    ];
    const model = buildCompareFromSummary(job(), base, treated, [
      'baseline:ensemble_summary',
      'treated:ensemble_summary',
    ]);

    expect(model.latestDate).toBe('2025-01-10');
    expect(model.comparisonMetrics.cumulative).toMatchObject({
      actualDate: '2025-01-08',
      horizonStart: '2025-01-01',
      horizonEnd: '2025-01-08',
      baseline: 85,
      treated: 63,
      delta: -22,
      status: 'as_of',
    });
    expect(model.comparisonMetrics.attack).toMatchObject({
      actualDate: '2025-01-10',
      horizonEnd: '2025-01-10',
      baseline: 0.1,
      treated: 0.08,
      delta: -0.020000000000000004,
      status: 'exact',
    });
    expect(model.baseline.cumulative[model.baseline.cumulative.length - 1]).toBeNull();
    expect(model.treated.cumulative[model.treated.cumulative.length - 1]).toBeNull();
    expect(metricDateLabel(model.comparisonMetrics.cumulative)).toBe(
      'As of 8 Jan (selected 10 Jan)',
    );
    expect(formatDate('2025-01-10')).toBe('10 Jan');
  });

  it('recomputes matched comparison deltas from same-date persisted values', () => {
    const rows = [
      matchedRow('latent_cumulative_infections', '2025-01-13', 85, 63),
      matchedRow('latent_ever_infected_fraction', '2025-01-13', 0.028333333333333332, 0.021),
      matchedRow('observed_reported_cases', '2025-01-14', 3, 2),
      matchedRow('observed_reported_cases', '2025-01-15', 4, 3),
    ];
    const model = buildCompareFromMatchedComparison(job(), rows, [
      'comparison:matched_seed_comparison',
    ]);

    expect(model.latestDate).toBe('2025-01-15');
    expect(model.comparisonMetrics.cumulative).toMatchObject({
      actualDate: '2025-01-13',
      horizonEnd: '2025-01-13',
      baseline: 85,
      treated: 63,
      delta: -22,
      status: 'as_of',
    });
    expect(model.comparisonMetrics.attack).toMatchObject({
      actualDate: '2025-01-13',
      horizonEnd: '2025-01-13',
      baseline: 0.028333333333333332,
      treated: 0.021,
      delta: -0.007333333333333331,
      status: 'as_of',
    });
    expect(model.baseline.cumulative.slice(-2)).toEqual([null, null]);
    expect(model.treated.cumulative.slice(-2)).toEqual([null, null]);
    expect(metricDateLabel(model.comparisonMetrics.attack)).toBe(
      'As of 13 Jan (selected 15 Jan)',
    );
    expect(percentDifference(0, 1)).toBeNull();
    expect(percentDifference(85, 63)).toBe(-25.88235294117647);
  });

  it('never pairs a later baseline point with an earlier treated point', () => {
    const base = [
      row('latent_cumulative_infections', '2025-01-09', 100),
      row('latent_cumulative_infections', '2025-01-10', 999),
    ];
    const treated = [row('latent_cumulative_infections', '2025-01-09', 90)];
    const model = buildCompareFromSummary(job(), base, treated, []);

    expect(model.comparisonMetrics.cumulative).toMatchObject({
      selectedDate: '2025-01-10',
      actualDate: '2025-01-09',
      baseline: 100,
      treated: 90,
      delta: -10,
      status: 'as_of',
    });
  });
});
