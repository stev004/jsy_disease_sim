import { describe, expect, it, vi } from 'vitest';
import { api, type JobStatusResponse } from './api';
import { buildResultsFromEnsembleSummary, detectFizzle, isIntroductionRoute, loadResults, optionalNumber, parishMetricPer1k, scientificNumber, type ResultsData } from './views/results/data';
import { deriveInterventions } from './views/results/interventions';
import { failedPhaseName, stateNote } from './views/runs/jobText';
import { buildCompareFromSummary } from './views/compare/compareData';
import { buildScenario, travelConfig, type BuilderState } from './views/simulate/request';
import { isSupportedStartDate } from './views/simulate/SimulateView';

const job = (kind: JobStatusResponse['kind'] = 'ensemble'): JobStatusResponse => ({
  job_id: `test-${kind}`,
  kind,
  state: 'SUCCEEDED',
  phase: 'complete',
  created_at: '2025-01-01T00:00:00Z',
  started_at: '2025-01-01T00:00:00Z',
  finished_at: '2025-01-01T00:00:01Z',
  progress_fraction: null,
  request_hash: 'request',
  request: {
    kind,
    start_date: '2025-01-06',
    duration_days: 2,
    replicate_seeds: [101, 102, 103],
    baseline: { scenario_id: 'baseline' },
    treated: { scenario_id: 'treated', interventions: [{ type: 'school_closure' }] },
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
  status_url: '/jobs/test',
});

const row = (scope: string, key: string, metric: string, date: string, median: number, extra = {}) => ({
  scope,
  key,
  metric,
  date,
  median,
  ...extra,
});

const state: BuilderState = {
  name: 'M10.1 payloads',
  population: 'ci',
  seeded: 2,
  startDate: '2025-01-06',
  duration: 30,
  ivs: ['school', 'isolation', 'quarantine', 'wfh', 'community', 'care', 'vacc'],
  travel: 'custom',
  uncertainty: 'single',
};

describe('M10.1 scientific truth regressions', () => {
  it('serializes advertised intervention controls into supported M7 fields', () => {
    const interventions = buildScenario(state).interventions as Array<Record<string, unknown>>;
    const byType = new Map(interventions.map((item) => [item.type, item]));
    expect(byType.get('school_closure')).toMatchObject({ class_multiplier: 0, cross_class_multiplier: 0 });
    expect(byType.get('case_isolation')).toMatchObject({ adherence: 0.8, route_effects: { household: 0.5, community_indoor: 0.1 } });
    expect(byType.get('household_quarantine')).toMatchObject({ route_effects: { household: 1, workplace_team: 0.15 } });
    expect(byType.get('workplace_reduction')).toMatchObject({ workplace_multiplier: 0.5, commute_multiplier: 0, additional_wfh_fraction: 0.5 });
    expect(byType.get('community_reduction')).toMatchObject({ indoor_multiplier: 0.5, outdoor_multiplier: 1, community_scope: 'everyone_present' });
    expect(byType.get('care_home_protection')).toMatchObject({ care_target: 'both', care_contact_multiplier: 0.5, care_external_staff_multiplier: 0.75 });
    expect(byType.get('vaccination')).toMatchObject({ rollout_rate: 0.1, coverage_target: 0.7, uptake_probability: 0.8, efficacy_susceptibility: 0.6, efficacy_infectiousness: 0, waning_days: 365 });
  });

  it('serializes arrival testing as the current M8 travel intervention config', () => {
    expect(travelConfig('custom')).toMatchObject({
      mode: 'explicit_travel',
      interventions: {
        testing_probability: 1,
        test_sensitivity: 1,
        test_result_delay_days: 0,
        quarantine_positive_only: true,
        quarantine_duration_days: 7,
      },
    });
  });

  it('blocks dates outside the current 2025 engine calendar', () => {
    expect(isSupportedStartDate('2025-12-31')).toBe(true);
    expect(isSupportedStartDate('2026-01-06')).toBe(false);
  });

  it('keeps absent scientific values absent', () => {
    expect(optionalNumber({}, 'cumulative_total_infections')).toBeNull();
    expect(scientificNumber({}, 'daily_epidemic', 'cumulative_total_infections')).toEqual({
      value: null,
      available: false,
      source: null,
      reason: 'daily_epidemic did not publish cumulative_total_infections',
    });
    const parish = { id: 'helier', name: 'St Helier', pop: null, points: [{ newInfections: 2, active: null, cum: 2, detected: null, attack: null, visitor: null }] } as ResultsData['parishes'][number];
    expect(parishMetricPer1k(parish, 0, 'active')).toBeNull();
  });

  it('prefers published cumulative totals that include seeded infections', async () => {
    vi.spyOn(api, 'getJobDatasets').mockResolvedValue({
      job_id: 'test-scenario_run',
      available: true,
      datasets: [{ name: 'daily_epidemic', rows: 2, columns: [], artifact_id: 'daily' }],
    });
    vi.spyOn(api, 'readDataset').mockResolvedValue({
      job_id: 'test-scenario_run',
      dataset: 'daily_epidemic',
      artifact_id: 'daily',
      metadata: {},
      rows: [
        { date: '2025-01-06', susceptible: 990, exposed: 5, infectious: 5, recovered: 0, dead: 0, new_infections: 10, new_seeded_infections: 5, cumulative_infections: 10, cumulative_total_infections: 15, attack_rate: 0.015 },
        { date: '2025-01-07', susceptible: 985, exposed: 5, infectious: 5, recovered: 5, dead: 0, new_infections: 0, new_seeded_infections: 0, cumulative_infections: 10, cumulative_total_infections: 15, attack_rate: 0.015 },
      ],
      total: 2,
      has_more: false,
      limit: 10_000,
      offset: 0,
      next_offset: null,
    });
    try {
      const results = await loadResults(job('scenario_run'));
      expect(results.epi[0].cum).toBe(15);
      expect(results.cumulativeLabel).toBe('Cumulative infected');
      expect(results.epi[0].attack).toBe(0.015);
      expect(results.epi[0].bandLow).toBeNull();
      expect(results.epi[0].bandHigh).toBeNull();
    } finally {
      vi.restoreAllMocks();
    }
  });

  it('accepts current M6 ensemble_summary semantics and persisted quantile fields', () => {
    const rows = [
      row('epidemic', 'all', 'latent_prevalence', '2025-01-06', 0.01, { lower_value: 0.008, upper_value: 0.012 }),
      row('epidemic', 'all', 'latent_cumulative_infections', '2025-01-06', 100),
      row('epidemic', 'all', 'latent_attack_rate', '2025-01-06', 0.1),
      row('epidemic', 'all', 'latent_new_infections', '2025-01-06', 10),
      row('epidemic', 'all', 'latent_prevalence', '2025-01-07', 0.012, { lower_value: 0.01, upper_value: 0.014 }),
      row('epidemic', 'all', 'latent_cumulative_infections', '2025-01-07', 120),
      row('epidemic', 'all', 'latent_attack_rate', '2025-01-07', 0.12),
      row('epidemic', 'all', 'latent_new_infections', '2025-01-07', 20),
      row('parish', 'St Helier', 'latent_new_infections', '2025-01-06', 3),
      row('parish', 'St Helier', 'latent_new_infections', '2025-01-07', 4),
      row('route', 'household', 'latent_local_infections', '2025-01-06', 2),
      row('route', 'household', 'latent_local_infections', '2025-01-07', 3),
      row('route', 'seeded', 'latent_local_infections', '2025-01-06', 0),
      row('route', 'exogenous_import', 'latent_local_infections', '2025-01-06', 0),
    ];
    const results = buildResultsFromEnsembleSummary(job(), rows);
    expect(results.population).toBe(1000);
    expect(results.epi[0].active).toBe(10);
    expect(results.epi[0].bandLow).toBe(8);
    expect(results.epi[0].bandHigh).toBe(12);
    expect(results.parishes.find((p) => p.id === 'helier')?.points[1].cum).toBe(7);
    expect(results.routes[0].cumulative[1]).toBe(5);
    expect(results.routes.some((route) => isIntroductionRoute(route.id))).toBe(false);
    expect(results.availability.parishRoutes).toBe(false);
    expect(results.mapMetrics.map((metric) => metric.id)).toEqual(['new', 'cum']);
  });

  it('only calls fizzle when endpoint exposed and infectious states are both zero', () => {
    const base = {
      epi: [{ day: 0, date: '2025-01-06', active: 0, exposed: 0, cum: 2, detected: null, attack: null, newInfections: 2, bandLow: null, bandHigh: null }],
      availability: { activeState: true, exposedState: true },
    } as ResultsData;
    expect(detectFizzle(base)).toEqual({ cumulative: 2, dieOutDay: 0 });
    expect(detectFizzle({ ...base, epi: [{ ...base.epi[0], exposed: 1 }] })).toBeNull();
    expect(detectFizzle({ ...base, epi: [{ ...base.epi[0], active: 1 }] })).toBeNull();
    expect(detectFizzle({ ...base, availability: { ...base.availability, exposedState: false } })).toBeNull();
    expect(detectFizzle({ ...base, epi: [{ ...base.epi[0], cum: null }] })).toBeNull();
  });

  it('does not assign a calendar bar to detection-triggered interventions and uses inclusive duration', () => {
    const bars = deriveInterventions({ ...job('scenario_run'), request: { scenario: { interventions: [
      { type: 'case_isolation', activation_rule: 'detection_triggered', start_delay_days: 1, duration_days: 7 },
      { type: 'school_closure', activation_rule: 'calendar', start_date: '2025-01-06', duration_days: 14 },
    ] } } } as JobStatusResponse, '2025-01-06', 30);
    expect(bars[0]).toMatchObject({ triggered: true, from: 0, to: 0 });
    expect(bars[1]).toMatchObject({ triggered: false, from: 0, to: 13 });
  });

  it('uses genuine baseline and treated summary values without deriving an arm', () => {
    const base = [
      row('epidemic', 'all', 'latent_prevalence', '2025-01-06', 0.01),
      row('epidemic', 'all', 'latent_cumulative_infections', '2025-01-06', 100),
      row('epidemic', 'all', 'latent_attack_rate', '2025-01-06', 0.1),
      row('epidemic', 'all', 'latent_new_infections', '2025-01-06', 10),
      row('route', 'household', 'latent_local_infections', '2025-01-06', 6),
      row('parish', 'St Helier', 'latent_new_infections', '2025-01-06', 5),
    ];
    const treated = [
      row('epidemic', 'all', 'latent_prevalence', '2025-01-06', 0.005),
      row('epidemic', 'all', 'latent_cumulative_infections', '2025-01-06', 50),
      row('epidemic', 'all', 'latent_attack_rate', '2025-01-06', 0.05),
      row('epidemic', 'all', 'latent_new_infections', '2025-01-06', 5),
      row('route', 'household', 'latent_local_infections', '2025-01-06', 2),
      row('parish', 'St Helier', 'latent_new_infections', '2025-01-06', 2),
    ];
    const model = buildCompareFromSummary(job('scenario_compare'), base, treated, ['baseline:ensemble_summary', 'treated:ensemble_summary', 'comparison:matched_seed_comparison']);
    expect(model.derived).toBe(false);
    expect(model.baseline.cumulative[0]).toBe(100);
    expect(model.treated.cumulative[0]).toBe(50);
    expect(model.routes[0].treated).toBe(2);
    expect(model.parishes[0].treated).toBe(2);
  });

  it('keeps introduction sources out of local transmission-route attribution', () => {
    expect(isIntroductionRoute('seeded')).toBe(true);
    expect(isIntroductionRoute('exogenous_import')).toBe(true);
    expect(isIntroductionRoute('household')).toBe(false);
  });

  it('does not infer a running failure phase when M9 reports only failed', () => {
    const failed = {
      ...job('scenario_run'),
      state: 'FAILED' as const,
      phase: 'failed' as const,
      error: { code: 'worker_execution_failed', message: 'failed', details: null },
    };
    expect(failedPhaseName(failed)).toBeNull();
    expect(stateNote(failed, Date.now())).toContain('Run failed');
    expect(stateNote(failed, Date.now())).not.toContain('failed during running');
  });
});
