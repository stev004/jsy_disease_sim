/**
 * Deterministic mock implementation of the M9 API surface.
 *
 * It reproduces the M10 design mockup's fake data (60-day gaussian epidemic,
 * 12 parishes with lag/amplitude, 11 resident + 7 travel route mixes, four age
 * bands, a travel series) and serves it through the *real* dataset shapes, so
 * a feature view written against `HttpJosClient` behaves identically here.
 *
 * Column names match the scientific writers in
 * `src/jersey_outbreak/outbreak_runner.py` (daily_epidemic / daily_parish /
 * daily_route / daily_age).
 */

import { ISLAND_POP, PARISHES, type ParishId } from '../map/geometry';
import {
  ApiError,
  DEFAULT_DATASET_LIMIT,
  type CancelResponse,
  type CapabilitiesResponse,
  type DatasetQuery,
  type DatasetReadResponse,
  type DatasetRow,
  type HealthResponse,
  type JobArtifactsResponse,
  type JobDatasetsResponse,
  type JobEvent,
  type JobEventsResponse,
  type JobKind,
  type JobListParams,
  type JobListResponse,
  type JobPhase,
  type JobRequest,
  type JobStatusResponse,
  type JobSubmissionResponse,
  type JosClient,
  type JsonObject,
  type ScenarioValidationResponse,
} from './types';

/* ===================== deterministic epidemic curves ===================== */

export const MOCK_DAYS = 60;
export const MOCK_POP = ISLAND_POP;
export const MOCK_START_DATE = '2025-01-06';

// Authority: manifest_schema_version defaults in the backend schema/artifact modules.
const ARTIFACT_SCHEMA_VERSIONS = {
  m5: '1.2',
  m6_observation: '1.4',
  m6_ensemble: '1.4',
  m7: '2.1',
  m8: '2.2',
} as const;

const gauss = (d: number, peak: number, sigma: number, amp: number): number =>
  amp * Math.exp(-((d - peak) ** 2) / (2 * sigma * sigma));

/** Active infectious on day `d`. */
export function active(d: number): number {
  return gauss(d, 34, 10.5, 1884) + gauss(d, 20, 6, 260);
}

/** Cumulative infections up to and including day `d`. */
export function cum(d: number): number {
  let t = 0;
  for (let i = 0; i <= d; i++) t += active(i) / 5.0;
  return Math.min(t * 0.98 + 5, MOCK_POP * 0.12);
}

/** Detected cases (38% ascertainment, 3-day reporting lag). */
export function detected(d: number): number {
  return d < 3 ? 0 : 0.38 * cum(d - 3);
}

function isoDate(dayOffset: number): string {
  const dt = new Date(Date.UTC(2025, 0, 6));
  dt.setUTCDate(dt.getUTCDate() + dayOffset);
  return dt.toISOString().slice(0, 10);
}

/* ============================ parish mixing ============================ */

interface ParishSim {
  id: ParishId;
  name: string;
  pop: number;
  /** Days the parish trails St Helier by. */
  lag: number;
  /** Relative amplitude. */
  amp: number;
}

const PARISH_DYNAMICS: Record<ParishId, { lag: number; amp: number }> = {
  helier: { lag: 0, amp: 1.18 },
  saviour: { lag: 2, amp: 1.05 },
  brelade: { lag: 4, amp: 0.95 },
  clement: { lag: 3, amp: 1.0 },
  lawrence: { lag: 5, amp: 0.9 },
  grouville: { lag: 6, amp: 0.88 },
  peter: { lag: 7, amp: 0.85 },
  ouen: { lag: 11, amp: 0.72 },
  martin: { lag: 8, amp: 0.8 },
  trinity: { lag: 9, amp: 0.76 },
  john: { lag: 9, amp: 0.78 },
  mary: { lag: 12, amp: 0.68 },
};

export const MOCK_PARISHES: ParishSim[] = PARISHES.map((p) => ({
  ...p,
  ...PARISH_DYNAMICS[p.id],
}));

export type ParishMetric = 'active' | 'cum' | 'detected' | 'attack' | 'visitor';

export function parishMetric(p: ParishSim, d: number, metric: ParishMetric): number {
  const dd = Math.max(0, d - p.lag);
  const share = p.pop / MOCK_POP;
  switch (metric) {
    case 'active':
      return active(dd) * share * p.amp;
    case 'cum':
      return cum(dd) * share * p.amp;
    case 'detected':
      return detected(dd) * share * p.amp;
    case 'attack':
      return (cum(dd) * share * p.amp) / p.pop;
    case 'visitor':
      return cum(dd) * share * p.amp * 0.055 * (p.id === 'helier' ? 1.6 : 1);
    default:
      return 0;
  }
}

/* ============================== routes ============================== */

/** [route_id, display name, base share, [affected-by-closure, multiplier]] */
export const RES_ROUTES: Array<[string, string, number, [number, number]]> = [
  ['household', 'Household', 0.27, [0, 1]],
  ['community_indoor', 'Community indoor', 0.16, [0, 1]],
  ['school_class', 'School class', 0.13, [1, 0.25]],
  ['workplace_team', 'Workplace team', 0.11, [1, 0.55]],
  ['workplace_transient', 'Workplace transient', 0.06, [1, 0.55]],
  ['school_cross_class', 'School cross-class', 0.05, [1, 0.25]],
  ['community_outdoor', 'Community outdoor', 0.05, [0, 1]],
  ['bus', 'Bus', 0.035, [1, 0.7]],
  ['shared_vehicle', 'Shared vehicle', 0.03, [1, 0.7]],
  ['care_staff', 'Care staff', 0.022, [0, 1]],
  ['care_resident', 'Care resident', 0.018, [0, 1]],
];

export const TRV_ROUTES: Array<[string, string, number]> = [
  ['visitor_accommodation', 'Visitor accommodation', 0.014],
  ['visitor_community_indoor', 'Visitor community indoor', 0.012],
  ['arrival_terminal', 'Arrival terminal', 0.008],
  ['visitor_party', 'Visitor party', 0.007],
  ['visitor_host_household', 'Host household', 0.006],
  ['visitor_transit', 'Visitor transit', 0.004],
  ['visitor_community_outdoor', 'Visitor community outdoor', 0.003],
];

/** School closure days 6-20 and isolation from day 4 modulate the route mix. */
function routeWeight(key: string, base: number, mod: [number, number] | null, d: number): number {
  let w = base;
  const closure = d >= 6 && d <= 20;
  const iso = d >= 4;
  if (mod) {
    const [affected] = mod;
    if (affected && closure && key.startsWith('school')) w *= 0.18;
    if (
      affected &&
      closure &&
      (key.startsWith('workplace') || key === 'bus' || key === 'shared_vehicle')
    ) {
      w *= 0.8;
    }
  }
  if (key === 'household' && (closure || iso)) w *= 1.25;
  return w;
}

export interface RouteCount {
  name: string;
  key: string;
  kind: 'res' | 'trv';
  count: number;
  share: number;
}

export function routeCounts(day: number, win: 'cum' | 'day'): RouteCount[] {
  const total = win === 'cum' ? cum(day) : Math.max(0, cum(day) - cum(Math.max(0, day - 1)));
  const raw: Array<[string, number, 'res' | 'trv', string]> = [];
  let wsum = 0;
  for (const [key, name, base, mod] of RES_ROUTES) {
    const w = routeWeight(key, base, mod, day);
    raw.push([name, w, 'res', key]);
    wsum += w;
  }
  for (const [key, name, base] of TRV_ROUTES) {
    raw.push([name, base, 'trv', key]);
    wsum += base;
  }
  return raw.map(([name, w, kind, key]) => ({
    name,
    key,
    kind,
    count: (total * w) / wsum,
    share: w / wsum,
  }));
}

/* =============================== ages =============================== */

export const AGES = [
  { band: '0-4', pop: 5062, mult: 0.9 },
  { band: '5-17', pop: 14926, mult: 1.35 },
  { band: '18-64', pop: 65212, mult: 1.0 },
  { band: '65+', pop: 19340, mult: 0.72 },
];

/* ============================== travel ============================== */

export function arrivalsToday(d: number): number {
  return Math.round(210 + 60 * Math.sin(d / 2.2) + (d % 7 < 2 ? 90 : 0));
}

export function activeVisitors(d: number): number {
  return Math.round(680 + 140 * Math.sin(d / 9));
}

/* ============================ tidy datasets ============================ */

function dailyEpidemicRows(): DatasetRow[] {
  const rows: DatasetRow[] = [];
  for (let d = 0; d < MOCK_DAYS; d++) {
    const infectious = Math.round(active(d));
    const totalCumulative = Math.round(cum(d));
    const nonSeededCumulative = Math.max(0, totalCumulative - 5);
    const prevNonSeeded = d === 0 ? 0 : Math.max(0, Math.round(cum(d - 1)) - 5);
    rows.push({
      date: isoDate(d),
      time_index: d,
      susceptible: MOCK_POP - totalCumulative,
      exposed: Math.round(active(d) * 0.42),
      infectious,
      recovered: Math.max(0, totalCumulative - infectious),
      severe: 0,
      dead: 0,
      new_infections: Math.max(0, nonSeededCumulative - prevNonSeeded),
      new_local_infections: Math.max(0, nonSeededCumulative - prevNonSeeded),
      new_imported_infections: 0,
      new_seeded_infections: d === 0 ? 5 : 0,
      cumulative_infections: nonSeededCumulative,
      cumulative_total_infections: totalCumulative,
      prevalence: infectious / MOCK_POP,
      cumulative_incidence_per_capita: totalCumulative / MOCK_POP,
      ever_infected_fraction: totalCumulative / MOCK_POP,
      attack_rate: totalCumulative / MOCK_POP,
      detected_cases: Math.round(detected(d)),
    });
  }
  return rows;
}

function dailyParishRows(): DatasetRow[] {
  const rows: DatasetRow[] = [];
  for (let d = 0; d < MOCK_DAYS; d++) {
    for (const p of MOCK_PARISHES) {
      const cumToday = parishMetric(p, d, 'cum');
      const cumYesterday = d === 0 ? 0 : parishMetric(p, d - 1, 'cum');
      const newInfections = Math.max(0, Math.round(cumToday - cumYesterday));
      rows.push({
        date: isoDate(d),
        time_index: d,
        parish: p.name,
        new_seeded_infections: d === 0 && p.id === 'helier' ? 5 : 0,
        new_imported_infections: 0,
        new_local_infections: newInfections,
        new_infections: newInfections,
        // Convenience columns the workspace's map metrics read directly.
        active_infectious: Math.round(parishMetric(p, d, 'active')),
        cumulative_infections: Math.round(cumToday),
        detected_cases: Math.round(parishMetric(p, d, 'detected')),
        ever_infected_fraction: parishMetric(p, d, 'attack'),
        attack_rate: parishMetric(p, d, 'attack'),
        visitor_linked_infections: Math.round(parishMetric(p, d, 'visitor')),
        population: p.pop,
      });
    }
  }
  return rows;
}

function dailyRouteRows(): DatasetRow[] {
  const rows: DatasetRow[] = [];
  const cumulative = new Map<string, number>();
  for (let d = 0; d < MOCK_DAYS; d++) {
    const dayRows = routeCounts(d, 'day');
    for (const r of dayRows) {
      const newEvents = Math.round(r.count);
      cumulative.set(r.key, (cumulative.get(r.key) ?? 0) + newEvents);
      rows.push({
        date: isoDate(d),
        time_index: d,
        route_id: r.key,
        route_name: r.name,
        route_family: r.kind === 'res' ? 'resident' : 'travel',
        new_events: newEvents,
        new_local_infections: newEvents,
        new_imported_infections: 0,
        new_seeded_infections: 0,
        cumulative_infections: cumulative.get(r.key) ?? 0,
      });
    }
  }
  return rows;
}

function dailyAgeRows(): DatasetRow[] {
  const rows: DatasetRow[] = [];
  const weightSum = AGES.reduce((s, a) => s + a.pop * a.mult, 0);
  for (let d = 0; d < MOCK_DAYS; d++) {
    const dayTotal = Math.max(0, cum(d) - cum(Math.max(0, d - 1)));
    const cumTotal = cum(d);
    for (const a of AGES) {
      const w = (a.pop * a.mult) / weightSum;
      const newInfections = Math.round(dayTotal * w);
      rows.push({
        date: isoDate(d),
        time_index: d,
        age_band: a.band,
        new_seeded_infections: 0,
        new_imported_infections: 0,
        new_local_infections: newInfections,
        new_infections: newInfections,
        cumulative_infections: Math.round(cumTotal * w),
        population: a.pop,
        attack_rate: (cumTotal * w) / a.pop,
      });
    }
  }
  return rows;
}

function dailyTravelRows(): DatasetRow[] {
  const rows: DatasetRow[] = [];
  for (let d = 0; d < MOCK_DAYS; d++) {
    rows.push({
      date: isoDate(d),
      time_index: d,
      arrivals: arrivalsToday(d),
      active_visitors: activeVisitors(d),
      visitor_infections: Math.round(active(d) * 0.055),
      resident_infections: Math.round(active(d) * 0.945),
    });
  }
  return rows;
}

/** Demo-only M6-shaped summary rows used to exercise the real ensemble loader. */
function ensembleSummaryRows(): DatasetRow[] {
  const rows: DatasetRow[] = [];
  const add = (scope: string, key: string, metric: string, date: string, value: number) => {
    rows.push({
      scope,
      key,
      metric,
      metric_semantic: metric.includes('prevalence')
        ? 'state'
        : metric.includes('cumulative') || metric.includes('ever_infected') || metric.includes('attack')
          ? 'cumulative'
          : 'incidence',
      date,
      cell_semantic: 'median',
      median: value,
      replicate_count: 5,
    });
  };
  const epi = dailyEpidemicRows();
  for (const row of epi) {
    const date = String(row.date);
    add('epidemic', 'all', 'latent_new_infections', date, Number(row.new_infections));
    add('epidemic', 'all', 'latent_prevalence', date, Number(row.prevalence));
    add('epidemic', 'all', 'latent_cumulative_infections', date, Number(row.cumulative_total_infections));
    add('epidemic', 'all', 'latent_cumulative_incidence_per_capita', date, Number(row.cumulative_incidence_per_capita));
    add('epidemic', 'all', 'latent_ever_infected_fraction', date, Number(row.ever_infected_fraction));
    add('epidemic', 'all', 'latent_attack_rate', date, Number(row.attack_rate));
  }
  for (const row of dailyParishRows()) add('parish', String(row.parish), 'latent_new_infections', String(row.date), Number(row.new_infections));
  for (const row of dailyRouteRows()) add('route', String(row.route_id), 'latent_local_infections', String(row.date), Number(row.new_local_infections));
  for (const row of dailyAgeRows()) add('age', String(row.age_band), 'latent_new_infections', String(row.date), Number(row.new_infections));
  return rows;
}

const DATASETS: Record<string, () => DatasetRow[]> = {
  daily_epidemic: dailyEpidemicRows,
  daily_parish: dailyParishRows,
  daily_route: dailyRouteRows,
  daily_age: dailyAgeRows,
  daily_travel: dailyTravelRows,
  ensemble_summary: ensembleSummaryRows,
  matched_seed_comparison: () => [],
};

const datasetCache = new Map<string, DatasetRow[]>();

function datasetRows(name: string): DatasetRow[] {
  const baseName = name.includes(':') ? name.slice(name.indexOf(':') + 1) : name;
  const cached = datasetCache.get(name);
  if (cached) return cached;
  const build = DATASETS[baseName];
  if (!build) throw new ApiError(404, `Unknown dataset "${name}"`, {
    code: 'dataset_not_found',
    message: `Unknown dataset "${name}"`,
  });
  const rows = build();
  datasetCache.set(name, rows);
  return rows;
}

/* ============================== jobs ============================== */

const REQUEST_HASH = 'demo-session';

function ts(offsetMinutes: number): string {
  return new Date(Date.now() - offsetMinutes * 60_000).toISOString();
}

function makeJob(partial: Partial<JobStatusResponse> & Pick<JobStatusResponse, 'job_id' | 'kind' | 'state' | 'phase'>): JobStatusResponse {
  return {
    created_at: ts(120),
    started_at: ts(119),
    finished_at: ts(108),
    progress_fraction: null,
    request_hash: REQUEST_HASH,
    request: {},
    scenario_hash: null,
    latent_hash: null,
    bundle_hash: null,
    error: null,
    artifact_count: 0,
    verification_status: null,
    worker_pid: null,
    last_heartbeat: null,
    exit_status: 0,
    result_manifest_path: null,
    result_manifest_hash: null,
    engine_git_commit: null,
    dirty_worktree_flag: false,
    status_url: `/api/v1/jobs/${partial.job_id}`,
    ...partial,
  };
}

const SEED_JOBS: JobStatusResponse[] = [
  makeJob({
    job_id: 'mock-ensemble-baseline',
    kind: 'ensemble',
    state: 'SUCCEEDED',
    phase: 'complete',
    created_at: ts(180),
    started_at: ts(179),
    finished_at: ts(168),
    request: {
      kind: 'ensemble',
      mode: 'full',
      replicate_seeds: [101, 102, 103, 104, 105],
      start_date: MOCK_START_DATE,
      duration_days: MOCK_DAYS,
      ensemble_id: 'winter-respiratory-baseline',
      scenario: { scenario_id: 'Winter respiratory baseline', interventions: [] },
    },
  }),
  makeJob({
    job_id: 'mock-compare-school-wfh',
    kind: 'scenario_compare',
    state: 'SUCCEEDED',
    phase: 'complete',
    created_at: ts(85),
    started_at: ts(84),
    finished_at: ts(62),
    artifact_count: 9,
    request: {
      kind: 'scenario_compare',
      mode: 'full',
      replicate_seeds: [101, 102, 103, 104, 105],
      start_date: MOCK_START_DATE,
      duration_days: MOCK_DAYS,
      comparison_id: 'school-closure-wfh',
      baseline: { scenario_id: 'Winter respiratory baseline' },
      treated: { scenario_id: 'School closure + WFH' },
    },
  }),
  makeJob({
    job_id: 'mock-run-vaccination',
    kind: 'scenario_run',
    state: 'FAILED',
    phase: 'failed',
    created_at: ts(1_200),
    started_at: ts(1_199),
    finished_at: ts(1_194),
    artifact_count: 0,
    verification_status: null,
    scenario_hash: null,
    latent_hash: null,
    bundle_hash: null,
    exit_status: 1,
    error: {
      code: 'worker_failed',
      message: 'Worker exited during running: vaccination schedule exceeded run duration',
      details: { phase: 'running', exit_status: 1 },
    },
    request: {
      kind: 'scenario_run',
      mode: 'full',
      seed: 123,
      start_date: MOCK_START_DATE,
      duration_days: 120,
      scenario: { scenario_id: 'Vaccination rollout, fast waning' },
    },
  }),
];

/** Phase walk for a freshly submitted mock job (ms per phase). */
const PHASE_WALK: Array<[JobPhase, number]> = [
  ['queued', 1_500],
  ['validating', 2_000],
  ['preparing', 5_000],
  ['running', 5_000],
  ['writing_artifacts', 2_500],
  ['verifying', 2_000],
  ['finalizing', 1_500],
];

/* ============================ mock client ============================ */

export class MockJosClient implements JosClient {
  readonly usingMock = true;

  private jobs: JobStatusResponse[] = SEED_JOBS.map((j) => ({ ...j }));
  private events = new Map<string, JobEvent[]>();
  private counter = 0;

  async health(): Promise<HealthResponse> {
    return {
      status: 'ok',
      api_version: 'v1',
      api_schema_version: 'm9-1.0',
      registry: 'ok',
    };
  }

  async capabilities(): Promise<CapabilitiesResponse> {
    return {
      api_version: 'v1',
      api_schema_version: 'm9-1.0',
      package_version: '0.9.2+mock',
      artifact_schema_version_semantics:
        'current write versions; read-accepted versions are not represented',
      engine: { name: 'Demo engine', version: 'demo', git_commit: null, dirty_worktree_flag: null },
      artifact_schema_versions: ARTIFACT_SCHEMA_VERSIONS,
      population_presets: { ci: 3_000, scaled: 15_000, full: MOCK_POP },
      job_kinds: ['scenario_run', 'scenario_compare', 'ensemble'],
      resident_route_ids: RES_ROUTES.map(([key]) => key),
      travel_route_ids: TRV_ROUTES.map(([key]) => key),
      route_families: ['resident', 'travel'],
      intervention_families: [
        'school_closure',
        'case_isolation',
        'household_quarantine',
        'work_from_home',
        'community_reduction',
        'care_home_protection',
        'vaccination',
        'travel_measure',
      ],
      travel_modes: ['air', 'ferry'],
      parishes: MOCK_PARISHES.map((p) => p.name),
      dataset_names: ['daily_epidemic', 'daily_parish', 'daily_route', 'daily_age', 'daily_travel', 'ensemble_summary'],
      scheduler: { max_concurrent_jobs: 1, queue_policy: 'fifo' },
      limits: { max_dataset_rows: 10_000, default_dataset_limit: DEFAULT_DATASET_LIMIT },
      state_directory: '(mock — no local state directory)',
      scientific_claim_boundary:
        'Synthetic research simulation of a generated Jersey population. Not a forecast, ' +
        'surveillance product, or policy recommendation. No real people are represented.',
    };
  }

  async validateScenario(scenario: JsonObject): Promise<ScenarioValidationResponse> {
    return {
      valid: true,
      errors: [],
      warnings: [],
      normalized: scenario,
      scenario_config_hash: 'a3f2c9e41b',
    };
  }

  async submitJob(req: JobRequest, _idempotencyKey?: string): Promise<JobSubmissionResponse> {
    void _idempotencyKey;
    this.counter += 1;
    const jobId = `mock-job-${this.counter}`;
    const kind: JobKind = req.kind;
    const job = makeJob({
      job_id: jobId,
      kind,
      state: 'QUEUED',
      phase: 'queued',
      created_at: new Date().toISOString(),
      started_at: null,
      finished_at: null,
      artifact_count: 0,
      verification_status: null,
      scenario_hash: null,
      latent_hash: null,
      bundle_hash: null,
      exit_status: null,
      request: req as unknown as JsonObject,
    });
    this.jobs = [job, ...this.jobs];
    this.pushEvent(jobId, 'job_submitted', 'Job accepted and queued');
    this.walkPhases(jobId);
    return {
      job_id: jobId,
      kind,
      state: 'QUEUED',
      request_hash: REQUEST_HASH,
      status_url: `/api/v1/jobs/${jobId}`,
      events_url: `/api/v1/jobs/${jobId}/events`,
      already_exists: false,
    };
  }

  private pushEvent(jobId: string, type: string, message: string, metadata: JsonObject = {}): void {
    const list = this.events.get(jobId) ?? [];
    list.push({
      event_id: `${jobId}-ev-${list.length + 1}`,
      job_id: jobId,
      timestamp: new Date().toISOString(),
      type,
      message,
      metadata,
    });
    this.events.set(jobId, list);
  }

  private patch(jobId: string, patch: Partial<JobStatusResponse>): void {
    this.jobs = this.jobs.map((j) => (j.job_id === jobId ? { ...j, ...patch } : j));
  }

  /** Walks a submitted job through the real phase sequence on a timer. */
  private walkPhases(jobId: string, index = 0): void {
    const entry = PHASE_WALK[index];
    if (!entry) {
      this.patch(jobId, {
        state: 'SUCCEEDED',
        phase: 'complete',
        finished_at: new Date().toISOString(),
        artifact_count: 0,
        verification_status: null,
        scenario_hash: null,
        latent_hash: null,
        bundle_hash: null,
        exit_status: 0,
      });
      this.pushEvent(jobId, 'job_completed', 'Demo job completed in memory');
      return;
    }
    const [phase, delay] = entry;
    window.setTimeout(() => {
      const job = this.jobs.find((j) => j.job_id === jobId);
      if (!job) return;
      // A cancelled/failed job stops walking.
      if (job.state === 'CANCELLED' || job.state === 'CANCEL_REQUESTED') {
        this.patch(jobId, {
          state: 'CANCELLED',
          phase: 'cancelled',
          finished_at: new Date().toISOString(),
        });
        this.pushEvent(jobId, 'job_cancelled', 'Cancelled before completion');
        return;
      }
      this.patch(jobId, {
        state: phase === 'queued' ? 'QUEUED' : 'RUNNING',
        phase,
        started_at: job.started_at ?? new Date().toISOString(),
      });
      this.pushEvent(jobId, 'phase_changed', `Phase: ${phase}`, { phase });
      this.walkPhases(jobId, index + 1);
    }, delay);
  }

  async listJobs(params: JobListParams = {}): Promise<JobListResponse> {
    const limit = params.limit ?? 50;
    const offset = params.offset ?? 0;
    let jobs = this.jobs;
    if (params.state) jobs = jobs.filter((j) => j.state === params.state);
    if (params.kind) jobs = jobs.filter((j) => j.kind === params.kind);
    const total = jobs.length;
    return { jobs: jobs.slice(offset, offset + limit).map((j) => ({ ...j })), total, limit, offset };
  }

  async getJob(jobId: string): Promise<JobStatusResponse> {
    const job = this.jobs.find((j) => j.job_id === jobId);
    if (!job) {
      throw new ApiError(404, `Unknown job ${jobId}`, {
        code: 'job_not_found',
        message: `Unknown job ${jobId}`,
      });
    }
    return { ...job };
  }

  async cancelJob(jobId: string): Promise<CancelResponse> {
    const job = await this.getJob(jobId);
    const terminal = ['SUCCEEDED', 'FAILED', 'CANCELLED', 'INTERRUPTED'];
    if (terminal.includes(job.state)) {
      return { job_id: jobId, state: job.state, action: 'noop', idempotent: true };
    }
    this.patch(jobId, { state: 'CANCEL_REQUESTED', phase: job.phase });
    this.pushEvent(jobId, 'cancel_requested', 'Cancellation requested');
    return { job_id: jobId, state: 'CANCEL_REQUESTED', action: 'cancel_requested', idempotent: false };
  }

  async getJobEvents(jobId: string, limit = 200): Promise<JobEventsResponse> {
    await this.getJob(jobId);
    const events = (this.events.get(jobId) ?? []).slice(-limit);
    return { job_id: jobId, events };
  }

  async getJobArtifacts(jobId: string): Promise<JobArtifactsResponse> {
    await this.getJob(jobId);
    return { job_id: jobId, artifacts: [] };
  }

  async getJobDatasets(jobId: string): Promise<JobDatasetsResponse> {
    const job = await this.getJob(jobId);
    if (job.state !== 'SUCCEEDED') return { job_id: jobId, datasets: [], available: false };
    return {
      job_id: jobId,
      available: true,
      datasets: (job.kind === 'ensemble'
        ? ['ensemble_summary']
        : job.kind === 'scenario_compare'
          ? ['baseline:ensemble_summary', 'treated:ensemble_summary', 'comparison:matched_seed_comparison']
          : Object.keys(DATASETS).filter((name) => name !== 'ensemble_summary')).map((name) => {
        const rows = datasetRows(name);
        return {
          name,
          rows: rows.length,
          columns: Object.keys(rows[0] ?? {}),
          artifact_id: `${jobId}-${name}`,
        };
      }),
    };
  }

  async readDataset(
    jobId: string,
    name: string,
    query: DatasetQuery = {},
  ): Promise<DatasetReadResponse> {
    const job = await this.getJob(jobId);
    if (job.state !== 'SUCCEEDED') {
      throw new ApiError(409, 'Datasets are available only after verified success', {
        code: 'dataset_unavailable',
        message: 'Datasets are available only after verified success',
      });
    }
    const all = datasetRows(name);
    const filtered = all.filter((row) => {
      if (query.start_date && String(row.date) < query.start_date) return false;
      if (query.end_date && String(row.date) > query.end_date) return false;
      if (query.parish && row.parish !== query.parish) return false;
      if (query.route_id && row.route_id !== query.route_id) return false;
      if (query.age_band && row.age_band !== query.age_band) return false;
      if (query.intervention_id && row.intervention_id !== query.intervention_id) return false;
      if (query.scope && row.scope !== query.scope) return false;
      if (query.metric && row.metric !== query.metric) return false;
      if (query.key && row.key !== query.key) return false;
      if (query.seed != null && row.seed !== query.seed) return false;
      return true;
    });

    const isFiltered = filtered.length !== all.length;
    const limit = query.limit ?? DEFAULT_DATASET_LIMIT;
    const offset = query.offset ?? 0;
    const page = filtered.slice(offset, offset + limit);
    const projected = query.columns
      ? page.map((row) =>
          Object.fromEntries(
            query.columns!.filter((c) => c in row).map((c) => [c, row[c]]),
          ) as DatasetRow,
        )
      : page;
    const hasMore = offset + page.length < filtered.length;

    return {
      job_id: jobId,
      dataset: name,
      artifact_id: `${jobId}-${name}`,
      metadata: {
        schema_version: '1.0',
        columns: Object.keys(all[0] ?? {}),
        start_date: MOCK_START_DATE,
        duration_days: MOCK_DAYS,
        mock: true,
      },
      rows: projected,
      // Mirrors the real API: filtered reads report a null total.
      total: isFiltered ? null : all.length,
      has_more: hasMore,
      limit,
      offset,
      next_offset: hasMore ? offset + page.length : null,
    };
  }
}

export const mockClient = new MockJosClient();
