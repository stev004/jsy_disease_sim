import { describe, expect, it } from 'vitest';
import { buildRequest, buildScenario, type BuilderState } from './views/simulate/request';
import { TEMPLATES, type IvKey } from './views/simulate/templates';
import { loadResults, routeCounts } from './views/results/data';
import type { JobStatusResponse } from './api';
import { loadCompare } from './views/compare/compareData';

const base: BuilderState = {
  name: 'M10.1 live contract check',
  population: 'ci',
  seeded: 1,
  startDate: '2025-01-06',
  duration: 14,
  ivs: [],
  travel: 'off',
  uncertainty: 'single',
};

const liveApi = import.meta.env.VITE_M10_API as string | undefined;
const json = async (path: string, init?: RequestInit): Promise<Record<string, unknown>> => {
  const response = await fetch(`${liveApi}${path}`, init);
  const body = (await response.json()) as Record<string, unknown>;
  expect(response.ok, `${path}: ${JSON.stringify(body)}`).toBe(true);
  return body;
};

async function submitAndWait(request: Record<string, unknown>, key: string): Promise<{ jobId: string; status: Record<string, unknown> }> {
  const response = await json('/api/v1/jobs', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'Idempotency-Key': key },
    body: JSON.stringify(request),
  });
  const jobId = String(response.job_id);
  expect(typeof response.job_id).toBe('string');
  let status: Record<string, unknown> = {};
  for (let attempt = 0; attempt < 180; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    status = await json(`/api/v1/jobs/${jobId}`);
    if (['SUCCEEDED', 'FAILED', 'CANCELLED', 'INTERRUPTED'].includes(String(status.state))) break;
  }
  expect(status.state, `${key}: ${JSON.stringify(status)}`).toBe('SUCCEEDED');
  return { jobId, status };
}

describe('M10.1 live M9 contract checks', () => {
  it.skipIf(!liveApi)('validates every frontend scenario payload against the running API', async () => {
    for (const template of TEMPLATES) {
      const ivs = template.ivs as IvKey[];
      const state = { ...base, name: template.name, ivs, travel: template.travel };
      const body = await json('/api/v1/scenarios/validate', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ scenario: buildScenario(state) }),
      });
      expect(body.valid).toBe(true);
      const normalized = body.normalized as Record<string, unknown>;
      const sent = buildScenario(state);
      const normalizedInterventions = normalized.interventions as Array<Record<string, unknown>>;
      for (const item of sent.interventions as Array<Record<string, unknown>>) {
        const normalizedItem = normalizedInterventions.find((candidate) => candidate.type === item.type);
        expect(normalizedItem).toBeDefined();
        for (const [key, value] of Object.entries(item)) expect(normalizedItem?.[key]).toEqual(value);
      }
      const sentTravel = sent.travel as Record<string, unknown>;
      if (sentTravel.interventions) {
        expect((normalized.travel as Record<string, unknown>).interventions).toMatchObject(sentTravel.interventions as Record<string, unknown>);
      }
    }
  });

  it.skipIf(!liveApi)('submits a builder-generated quick run and reads its succeeded datasets', async () => {
    const { jobId, status } = await submitAndWait(buildRequest(base) as unknown as Record<string, unknown>, 'm10-1-live-contract-check');
    const datasets = await json(`/api/v1/jobs/${jobId}/datasets`);
    const names = (datasets.datasets as Array<Record<string, unknown>>).map((dataset) => dataset.name);
    expect(names).toContain('daily_epidemic');
    const epiRows = (await json(`/api/v1/jobs/${jobId}/datasets/daily_epidemic?limit=10000`)).rows as Array<Record<string, unknown>>;
    expect(epiRows.length).toBeGreaterThan(0);
    const routeRows = (await json(`/api/v1/jobs/${jobId}/datasets/daily_route?limit=10000`)).rows as Array<Record<string, unknown>>;
    const loaded = await loadResults((status as unknown) as JobStatusResponse);
    expect(loaded.population).toBeGreaterThan(0);
    expect(loaded.dates).toHaveLength(14);
    expect(loaded.cumulativeSource).toContain('cumulative_total_infections');
    const lastApi = epiRows[epiRows.length - 1];
    const lastUi = loaded.epi[loaded.epi.length - 1];
    expect(lastUi.active).toBe(lastApi.infectious);
    expect(lastUi.cum).toBe(lastApi.cumulative_total_infections);
    expect(lastUi.attack).toBe(lastApi.attack_rate);
    const household = routeRows
      .filter((row) => row.route_id === 'household')
      .reduce((sum, row) => sum + Number(row.new_local_infections), 0);
    const routeTotal = routeRows.reduce((sum, row) => sum + Number(row.new_local_infections), 0);
    const counts = routeCounts(loaded.routes, loaded.dayCount - 1, 'cum');
    const householdCount = counts.find((route) => route.key === 'household');
    expect(householdCount?.count).toBe(household);
    expect(householdCount?.share).toBe(routeTotal > 0 ? household / routeTotal : 0);
  }, 240_000);

  it.skipIf(!liveApi)('executes a corrected school-closure scenario through validation, job, and artifact loading', async () => {
    const state = { ...base, name: 'M10.1 live school closure', ivs: ['school'] as BuilderState['ivs'] };
    const validation = await json('/api/v1/scenarios/validate', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ scenario: buildScenario(state) }),
    });
    expect(validation.valid).toBe(true);
    const { status } = await submitAndWait(buildRequest(state) as unknown as Record<string, unknown>, 'm10-1-live-school-execution');
    const persistedScenario = (status.request as Record<string, unknown>).scenario as Record<string, unknown>;
    const intervention = (persistedScenario.interventions as Array<Record<string, unknown>>)[0];
    expect(intervention).toMatchObject({ type: 'school_closure', class_multiplier: 0, cross_class_multiplier: 0 });
    const loaded = await loadResults((status as unknown) as JobStatusResponse);
    expect(loaded.epi.length).toBeGreaterThan(0);
  }, 240_000);

  it.skipIf(!liveApi)('opens a real M6 ensemble artifact with persisted summary quantiles', async () => {
    const state = { ...base, name: 'M10.1 live ensemble', duration: 3, uncertainty: 'ensemble' as const };
    const { jobId, status } = await submitAndWait(buildRequest(state) as unknown as Record<string, unknown>, 'm10-1-live-ensemble-execution');
    const datasets = await json(`/api/v1/jobs/${jobId}/datasets`);
    const names = (datasets.datasets as Array<Record<string, unknown>>).map((dataset) => dataset.name);
    expect(names).toEqual(expect.arrayContaining(['ensemble_summary', 'replicate_grid', 'replicate_trajectories']));
    const summaryRows = (await json(`/api/v1/jobs/${jobId}/datasets/ensemble_summary?limit=10000`)).rows as Array<Record<string, unknown>>;
    expect(summaryRows.some((row) => row.metric === 'latent_prevalence' && row.lower_value != null && row.upper_value != null)).toBe(true);
    const loaded = await loadResults((status as unknown) as JobStatusResponse);
    expect(loaded.epi.some((point) => point.bandLow != null && point.bandHigh != null)).toBe(true);
    expect(loaded.cumulativeSource).toContain('latent_cumulative_infections');
  }, 240_000);

  it.skipIf(!liveApi)('opens a current M8 travel artifact without false parish or age zeros', async () => {
    const state = { ...base, name: 'M10.1 live travel', duration: 3, travel: 'custom' as const };
    const { status } = await submitAndWait(buildRequest(state) as unknown as Record<string, unknown>, 'm10-1-live-travel-execution-v2');
    const scenario = (status.request as Record<string, unknown>).scenario as Record<string, unknown>;
    expect((scenario.travel as Record<string, unknown>).interventions).toMatchObject({ testing_probability: 1, test_sensitivity: 1, quarantine_duration_days: 7, quarantine_adherence: 1 });
    const loaded = await loadResults((status as unknown) as JobStatusResponse);
    expect(loaded.travel).not.toBeNull();
    expect(loaded.availability.parishActive).toBe(false);
    expect(loaded.availability.parishAttack).toBe(false);
    if (loaded.availability.ages) expect(loaded.ages.length).toBeGreaterThan(0);
    else expect(loaded.ages).toEqual([]);
  }, 240_000);

  it.skipIf(!liveApi)('loads a real namespaced M9 comparison without synthesizing the treated arm', async () => {
    const status = await json('/api/v1/jobs/cd966cd2-5a3e-41a4-a6c8-c27259537e6f');
    expect(status.state).toBe('SUCCEEDED');
    const model = await loadCompare((status as unknown) as JobStatusResponse);
    expect(model.derived).toBe(false);
    expect(model.servedDatasets).toContain('baseline:ensemble_summary');
    expect(model.servedDatasets).toContain('treated:ensemble_summary');
    expect(model.servedDatasets).toContain('comparison:matched_seed_comparison');
    expect(model.baseline.cumulative.length).toBeGreaterThan(0);
    expect(model.treated.cumulative.length).toBe(model.baseline.cumulative.length);
  });
});
