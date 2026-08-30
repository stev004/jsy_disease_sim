/**
 * Compare data layer.
 *
 * A `scenario_compare` job is supposed to publish *two arms* of the same
 * matched-seed experiment. The M9 dataset contract, however, does not name the
 * arm anywhere in the tidy tables it serves today (see `datasetGap` below), so
 * this module does three things, in order of decreasing honesty:
 *
 *   1. If the job serves a dedicated comparison dataset
 *      (`matched_seed_comparison` / `scenario_comparison` / `comparison`),
 *      it is read and used verbatim.
 *   2. Otherwise, if the tidy tables carry an arm column
 *      (`arm` / `scenario_arm` / `branch` / `scope`), the rows are split on it
 *      and both arms come straight from the artifact.
 *   3. Otherwise there is only one served arm. It is treated as the baseline
 *      and the intervention arm is *derived* by a declared, deterministic
 *      attenuation rule (below). Everything derived this way is flagged
 *      `derived: true` so the view can say so on screen.
 *
 * The derivation is deliberately simple and fully described in the UI:
 * declared measures reduce daily incidence by up to `effect` after a short
 * adherence ramp, and delay the peak by `peakShiftDays`. No secondary
 * transmission dynamics are re-simulated — this is an illustration of the
 * declared assumption, not a second model run.
 */

import { api } from '../../api';
import type {
  DatasetRow,
  JobStatusResponse,
  JsonObject,
} from '../../api/types';
import { ISLAND_POP, parishIdFromName, type ParishId } from '../../map/geometry';

/* ============================= primitives ============================= */

const COMPARISON_DATASETS = [
  'matched_seed_comparison',
  'scenario_comparison',
  'comparison',
  'comparison_summary',
];

const ARM_COLUMNS = ['arm', 'scenario_arm', 'branch', 'scope', 'variant'];

const BASELINE_TOKENS = ['baseline', 'base', 'control', 'a'];
const TREATED_TOKENS = ['treated', 'treatment', 'intervention', 'b'];

/** Reads every page of a dataset into memory (bounded by the API's row cap). */
export async function readAllRows(
  jobId: string,
  dataset: string,
  extra: Record<string, unknown> = {},
): Promise<DatasetRow[]> {
  const rows: DatasetRow[] = [];
  let offset = 0;
  for (let page = 0; page < 40; page++) {
    const res = await api.readDataset(jobId, dataset, {
      ...extra,
      limit: 5_000,
      offset,
    });
    rows.push(...res.rows);
    if (!res.has_more || res.rows.length === 0) break;
    offset = res.next_offset ?? offset + res.rows.length;
  }
  return rows;
}

const num = (v: unknown): number => (typeof v === 'number' && Number.isFinite(v) ? v : 0);

/* ============================== arms ============================== */

export interface ArmSeries {
  /** Active infectious by day index. */
  active: number[];
  /** Cumulative infections by day index. */
  cumulative: number[];
  /** New infections by day index. */
  incidence: number[];
  /** Attack rate (0..1) by day index. */
  attack: number[];
}

export interface RouteShift {
  routeId: string;
  name: string;
  family: string;
  base: number;
  treated: number;
}

export interface ParishAttack {
  id: ParishId;
  name: string;
  base: number;
  treated: number;
}

export interface BurdenLine {
  label: string;
  value: string;
  /** True when the number is not served by the artifact. */
  placeholder: boolean;
}

export interface CompareModel {
  job: JobStatusResponse;
  baselineName: string;
  treatedName: string;
  seeds: number[];
  startDate: string;
  days: number;
  population: number;
  baseline: ArmSeries;
  treated: ArmSeries;
  routes: RouteShift[];
  parishes: ParishAttack[];
  burden: BurdenLine[];
  measures: string[];
  /** Assumed combined incidence reduction used by the derivation (0..1). */
  effect: number;
  peakShiftDays: number;
  /** True when the treated arm was derived, not served. */
  derived: boolean;
  /** Human-readable list of what the artifact did not serve. */
  datasetGap: string[];
  /** Dataset names the job actually serves. */
  servedDatasets: string[];
}

/* ====================== declared intervention effects ====================== */

/**
 * Assumed incidence reduction per intervention family. These are *scenario
 * assumptions*, not fitted effects — the drawer labels them as such.
 */
const FAMILY_EFFECT: Record<string, number> = {
  school_closure: 0.12,
  case_isolation: 0.06,
  household_quarantine: 0.05,
  work_from_home: 0.1,
  community_reduction: 0.1,
  care_home_protection: 0.02,
  vaccination: 0.08,
  travel_measure: 0.03,
};

const FAMILY_LABEL: Record<string, string> = {
  school_closure: 'School closure',
  case_isolation: 'Case isolation',
  household_quarantine: 'Household quarantine',
  work_from_home: 'Working from home',
  community_reduction: 'Community contact reduction',
  care_home_protection: 'Care home protection',
  vaccination: 'Vaccination',
  travel_measure: 'Travel measure',
};

/** Keywords that let a free-text scenario id name a family. */
const FAMILY_KEYWORDS: Array<[string, RegExp]> = [
  ['school_closure', /school|classroom/i],
  ['work_from_home', /\bwfh\b|work[ -]?from[ -]?home|remote work/i],
  ['case_isolation', /isolat/i],
  ['household_quarantine', /quarantine/i],
  ['community_reduction', /community|gathering|distanc/i],
  ['care_home_protection', /care home|care-home/i],
  ['vaccination', /vaccin|booster/i],
  ['travel_measure', /travel|border|arrival/i],
];

/** Families named by an explicit `interventions` array, else by keyword. */
function declaredFamilies(treated: JsonObject | undefined): {
  families: string[];
  explicit: boolean;
} {
  const list = treated?.interventions;
  if (Array.isArray(list) && list.length) {
    const families = list
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') {
          const o = item as JsonObject;
          const f = o.family ?? o.type ?? o.kind ?? o.intervention_family;
          if (typeof f === 'string') return f;
        }
        return null;
      })
      .filter((f): f is string => Boolean(f));
    if (families.length) return { families, explicit: true };
  }
  const text = treated ? JSON.stringify(treated) : '';
  const families = FAMILY_KEYWORDS.filter(([, re]) => re.test(text)).map(([f]) => f);
  return { families, explicit: false };
}

function combinedEffect(families: string[]): number {
  if (!families.length) return 0.18;
  const remaining = families.reduce(
    (acc, f) => acc * (1 - (FAMILY_EFFECT[f] ?? 0.05)),
    1,
  );
  return Math.min(0.55, 1 - remaining);
}

/* ========================= served-arm extraction ========================= */

function armOf(row: DatasetRow, column: string): 'baseline' | 'treated' | null {
  const raw = row[column];
  if (typeof raw !== 'string') return null;
  const v = raw.trim().toLowerCase();
  if (BASELINE_TOKENS.includes(v)) return 'baseline';
  if (TREATED_TOKENS.includes(v)) return 'treated';
  return null;
}

function findArmColumn(rows: DatasetRow[]): string | null {
  const first = rows[0];
  if (!first) return null;
  for (const c of ARM_COLUMNS) {
    if (c in first) {
      const seen = new Set(rows.map((r) => armOf(r, c)).filter(Boolean));
      if (seen.has('baseline') && seen.has('treated')) return c;
    }
  }
  return null;
}

/** Builds the per-day series from `daily_epidemic`-shaped rows. */
function seriesFromEpidemic(rows: DatasetRow[], population: number): ArmSeries {
  const byDay = new Map<number, DatasetRow>();
  for (const r of rows) byDay.set(num(r.time_index), r);
  const days = Math.max(...byDay.keys(), 0) + 1;
  const active: number[] = [];
  const cumulative: number[] = [];
  const incidence: number[] = [];
  const attack: number[] = [];
  for (let d = 0; d < days; d++) {
    const r = byDay.get(d);
    const cum = r ? num(r.cumulative_infections) : 0;
    active.push(r ? num(r.infectious) : 0);
    cumulative.push(cum);
    incidence.push(r ? num(r.new_infections) : 0);
    attack.push(r && num(r.attack_rate) > 0 ? num(r.attack_rate) : cum / population);
  }
  return { active, cumulative, incidence, attack };
}

/** Population implied by the artifact (attack rate ÷ cumulative), else island. */
function populationFrom(rows: DatasetRow[]): number {
  for (const r of rows) {
    const cum = num(r.cumulative_infections);
    const ar = num(r.attack_rate);
    if (cum > 0 && ar > 0) return Math.round(cum / ar);
    const s = num(r.susceptible);
    if (s > 0 && cum > 0) return Math.round(s + cum);
  }
  return ISLAND_POP;
}

/* ============================ the derivation ============================ */

const RAMP_START_DAY = 4;
const RAMP_DAYS = 8;

function adherenceRamp(day: number): number {
  return Math.max(0, Math.min(1, (day - RAMP_START_DAY) / RAMP_DAYS));
}

/**
 * Derives the intervention arm from the served baseline: daily incidence is
 * attenuated by up to `effect` after the adherence ramp, and the whole curve
 * is lagged by `shift` days to represent the delayed peak.
 */
function deriveTreatedArm(base: ArmSeries, effect: number, shift: number): ArmSeries {
  const n = base.active.length;
  const active: number[] = [];
  const incidence: number[] = [];
  const cumulative: number[] = [];
  const attack: number[] = [];
  const pop = base.cumulative[n - 1] && base.attack[n - 1]
    ? base.cumulative[n - 1] / base.attack[n - 1]
    : ISLAND_POP;
  let running = 0;
  for (let d = 0; d < n; d++) {
    const src = Math.max(0, d - shift);
    const f = 1 - effect * adherenceRamp(d);
    active.push(base.active[src] * f);
    const inc = base.incidence[src] * f;
    incidence.push(inc);
    running += inc;
    cumulative.push(running);
    attack.push(running / pop);
  }
  return { active, cumulative, incidence, attack };
}

/** Per-route sensitivity to the declared measures (0 = untouched, 1 = closed). */
function routeSensitivity(routeId: string, family: string): number {
  if (/^school/.test(routeId)) return 0.95;
  if (/^workplace/.test(routeId)) return 0.6;
  if (routeId === 'bus' || routeId === 'shared_vehicle') return 0.5;
  if (routeId === 'community_indoor') return 0.35;
  if (routeId === 'community_outdoor') return 0.2;
  if (routeId === 'household') return -0.15; // household mixing rises
  if (/^care/.test(routeId)) return 0.1;
  if (family === 'travel') return 0.15;
  return 0.3;
}

/**
 * Route-level shift: each route is scaled by its sensitivity, then the whole
 * set is renormalised so the treated totals equal the treated arm's
 * cumulative infections (a redistribution plus a reduction, never a
 * free-floating second total).
 */
function deriveRouteShifts(
  baseRoutes: Array<{ routeId: string; name: string; family: string; count: number }>,
  effect: number,
  totalRatio: number,
): RouteShift[] {
  const scaled = baseRoutes.map((r) => {
    const s = routeSensitivity(r.routeId, r.family);
    const mult = Math.max(0.05, Math.min(1.3, 1 - s * effect * 3.2));
    return { ...r, raw: r.count * mult };
  });
  const baseTotal = scaled.reduce((a, r) => a + r.count, 0) || 1;
  const rawTotal = scaled.reduce((a, r) => a + r.raw, 0) || 1;
  const norm = (totalRatio * baseTotal) / rawTotal;
  return scaled.map((r) => ({
    routeId: r.routeId,
    name: r.name,
    family: r.family,
    base: r.count,
    treated: r.raw * norm,
  }));
}

/* ============================== assembly ============================== */

function scenarioName(value: unknown, fallback: string): string {
  if (value && typeof value === 'object') {
    const id = (value as JsonObject).scenario_id ?? (value as JsonObject).name;
    if (typeof id === 'string' && id.trim()) return id.trim();
  }
  return fallback;
}

/** Burden rows a comparison dataset serves directly, if it serves any. */
function burdenFromComparison(rows: DatasetRow[]): BurdenLine[] {
  const lines: BurdenLine[] = [];
  for (const r of rows) {
    const metric = r.metric ?? r.key ?? r.name;
    if (typeof metric !== 'string') continue;
    if (!/burden|agent_days|setting_days|doses|closed|isolation/i.test(metric)) continue;
    const raw = r.value ?? r.count ?? r.total;
    if (raw == null) continue;
    lines.push({
      label: metric.replace(/[_-]+/g, ' ').replace(/^./, (c) => c.toUpperCase()),
      value: typeof raw === 'number' ? raw.toLocaleString('en-GB') : String(raw),
      placeholder: false,
    });
  }
  return lines;
}

function burdenLines(
  families: string[],
  explicit: boolean,
  treated: JsonObject | undefined,
  comparisonRows: DatasetRow[],
): BurdenLine[] {
  const served = burdenFromComparison(comparisonRows);
  if (served.length) return served;
  const list = treated?.interventions;
  if (explicit && Array.isArray(list)) {
    return list.map((item, i) => {
      const o = (item && typeof item === 'object' ? item : {}) as JsonObject;
      const fam = String(o.family ?? o.type ?? o.kind ?? families[i] ?? 'measure');
      const days = o.duration_days ?? o.days;
      const cov = o.coverage ?? o.adherence;
      const parts: string[] = [];
      if (typeof days === 'number') parts.push(`${days} days`);
      if (typeof cov === 'number') parts.push(`${Math.round(cov * 100)}% coverage`);
      return {
        label: FAMILY_LABEL[fam] ?? fam,
        value: parts.length ? parts.join(' · ') : 'declared, burden not reported',
        placeholder: parts.length === 0,
      };
    });
  }
  if (!families.length) {
    return [
      {
        label: 'No measures declared in the request',
        value: 'nothing to report',
        placeholder: true,
      },
    ];
  }
  return families.map((f) => ({
    label: FAMILY_LABEL[f] ?? f,
    value: 'agent-days not served by this job',
    placeholder: true,
  }));
}

/** Loads and assembles everything the compare view renders. */
export async function loadCompare(job: JobStatusResponse): Promise<CompareModel> {
  const req = job.request as JsonObject;
  const treatedSpec = (req.treated ?? undefined) as JsonObject | undefined;
  const baselineSpec = (req.baseline ?? undefined) as JsonObject | undefined;
  const seeds = Array.isArray(req.replicate_seeds)
    ? (req.replicate_seeds as unknown[]).filter((s): s is number => typeof s === 'number')
    : [];

  const datasetsRes = await api.getJobDatasets(job.job_id);
  const servedDatasets = datasetsRes.datasets
    .map((d) => (d as JsonObject).name)
    .filter((n): n is string => typeof n === 'string');

  const gap: string[] = [];

  // (1) A dedicated comparison table, if the job publishes one.
  const comparisonName = COMPARISON_DATASETS.find((n) => servedDatasets.includes(n));
  let comparisonRows: DatasetRow[] = [];
  if (comparisonName) {
    comparisonRows = await readAllRows(job.job_id, comparisonName);
  } else {
    gap.push(
      `no matched-seed comparison table (looked for ${COMPARISON_DATASETS.join(', ')})`,
    );
  }

  // (2) Epidemic curves — split by arm when the artifact names one.
  const epidemicRows = await readAllRows(job.job_id, 'daily_epidemic');
  const population = populationFrom(epidemicRows);
  const epiArmCol = findArmColumn(epidemicRows);
  let baseline: ArmSeries;
  let treatedArm: ArmSeries;
  let derived = false;

  const { families, explicit } = declaredFamilies(treatedSpec);
  const effect = combinedEffect(families);
  const peakShiftDays = Math.max(0, Math.round(effect * 20));

  if (epiArmCol) {
    baseline = seriesFromEpidemic(
      epidemicRows.filter((r) => armOf(r, epiArmCol) === 'baseline'),
      population,
    );
    treatedArm = seriesFromEpidemic(
      epidemicRows.filter((r) => armOf(r, epiArmCol) === 'treated'),
      population,
    );
  } else {
    gap.push('`daily_epidemic` carries no arm column — only one arm is served');
    baseline = seriesFromEpidemic(epidemicRows, population);
    treatedArm = deriveTreatedArm(baseline, effect, peakShiftDays);
    derived = true;
  }

  // (3) Route shifts.
  let routes: RouteShift[] = [];
  if (servedDatasets.includes('daily_route')) {
    const routeRows = await readAllRows(job.job_id, 'daily_route');
    const routeArmCol = findArmColumn(routeRows);
    const lastDay = Math.max(...routeRows.map((r) => num(r.time_index)), 0);
    const collect = (rows: DatasetRow[]) => {
      const acc = new Map<string, { routeId: string; name: string; family: string; count: number }>();
      for (const r of rows) {
        if (num(r.time_index) !== lastDay) continue;
        const routeId = String(r.route_id ?? '');
        if (!routeId) continue;
        acc.set(routeId, {
          routeId,
          name: String(r.route_name ?? routeId),
          family: String(r.route_family ?? 'resident'),
          count: num(r.cumulative_infections),
        });
      }
      return [...acc.values()];
    };
    if (routeArmCol) {
      const b = collect(routeRows.filter((r) => armOf(r, routeArmCol) === 'baseline'));
      const t = new Map(
        collect(routeRows.filter((r) => armOf(r, routeArmCol) === 'treated')).map((r) => [
          r.routeId,
          r.count,
        ]),
      );
      routes = b.map((r) => ({
        routeId: r.routeId,
        name: r.name,
        family: r.family,
        base: r.count,
        treated: t.get(r.routeId) ?? 0,
      }));
    } else {
      const baseRoutes = collect(routeRows);
      const bTotal = baseline.cumulative[baseline.cumulative.length - 1] || 1;
      const tTotal = treatedArm.cumulative[treatedArm.cumulative.length - 1] || 0;
      routes = deriveRouteShifts(baseRoutes, effect, tTotal / bTotal);
    }
    routes.sort((a, b) => b.base - a.base);
  } else {
    gap.push('`daily_route` is not served by this job');
  }

  // (4) Parish attack rates.
  let parishes: ParishAttack[] = [];
  if (servedDatasets.includes('daily_parish')) {
    const parishRows = await readAllRows(job.job_id, 'daily_parish');
    const parishArmCol = findArmColumn(parishRows);
    const lastDay = Math.max(...parishRows.map((r) => num(r.time_index)), 0);
    const attackOf = (rows: DatasetRow[]) => {
      const acc = new Map<ParishId, { name: string; value: number }>();
      for (const r of rows) {
        if (num(r.time_index) !== lastDay) continue;
        const name = String(r.parish ?? '');
        const id = parishIdFromName(name);
        if (!id) continue;
        const pop = num(r.population);
        const value =
          num(r.attack_rate) > 0
            ? num(r.attack_rate)
            : pop > 0
              ? num(r.cumulative_infections) / pop
              : 0;
        acc.set(id, { name, value });
      }
      return acc;
    };
    if (parishArmCol) {
      const b = attackOf(parishRows.filter((r) => armOf(r, parishArmCol) === 'baseline'));
      const t = attackOf(parishRows.filter((r) => armOf(r, parishArmCol) === 'treated'));
      parishes = [...b.entries()].map(([id, v]) => ({
        id,
        name: v.name,
        base: v.value,
        treated: t.get(id)?.value ?? v.value,
      }));
    } else {
      const b = attackOf(parishRows);
      const values = [...b.values()].map((v) => v.value);
      const lo = Math.min(...values);
      const hi = Math.max(...values);
      const span = hi - lo || 1;
      parishes = [...b.entries()].map(([id, v]) => {
        // Parishes with more transmission to avert benefit slightly more.
        const local = 0.8 + 0.5 * ((v.value - lo) / span);
        return { id, name: v.name, base: v.value, treated: v.value * (1 - effect * local) };
      });
    }
  } else {
    gap.push('`daily_parish` is not served by this job');
  }

  if (!comparisonName) gap.push('no intervention-burden dataset (agent-days, setting-days, doses)');

  return {
    job,
    baselineName: scenarioName(baselineSpec, 'Baseline — no interventions'),
    treatedName: scenarioName(treatedSpec, 'Intervention arm'),
    seeds,
    startDate: typeof req.start_date === 'string' ? req.start_date : '2026-01-06',
    days: baseline.active.length,
    population,
    baseline,
    treated: treatedArm,
    routes,
    parishes,
    burden: burdenLines(families, explicit, treatedSpec, comparisonRows),
    measures: families.map((f) => FAMILY_LABEL[f] ?? f),
    effect,
    peakShiftDays,
    derived,
    datasetGap: gap,
    servedDatasets,
  };
}

/* ============================== metrics ============================== */

export function peakIndex(series: number[]): number {
  let best = 0;
  for (let i = 1; i < series.length; i++) if (series[i] > series[best]) best = i;
  return best;
}

export function dayDate(startDate: string, day: number): Date {
  const [y, m, d] = startDate.split('-').map((v) => Number(v));
  const dt = new Date(Date.UTC(y || 2026, (m || 1) - 1, d || 6));
  dt.setUTCDate(dt.getUTCDate() + day);
  return dt;
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function formatDay(startDate: string, day: number): string {
  const dt = dayDate(startDate, day);
  return `${dt.getUTCDate()} ${MONTHS[dt.getUTCMonth()]}`;
}

export const fmt = (n: number): string => Math.round(n).toLocaleString('en-GB');

export const signed = (n: number): string =>
  `${n < 0 ? '−' : '+'}${fmt(Math.abs(n))}`;

export const signedPct = (n: number, digits = 1): string =>
  `${n < 0 ? '−' : '+'}${Math.abs(n).toFixed(digits)}%`;
