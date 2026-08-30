/**
 * Comparison data adapter for the current M9 namespaced artifact contract.
 *
 * A comparison is displayable only when both arms are served by the job, or
 * when the persisted matched_seed_comparison artifact contains both values.
 * There is intentionally no synthetic treated arm and no route/parish
 * attenuation fallback here.
 */

import { api } from '../../api';
import type { DatasetRow, JobStatusResponse, JsonObject } from '../../api/types';
import { parishIdFromName, type ParishId } from '../../map/geometry';
import { isIntroductionRoute, optionalNumber, readAllRows } from '../results/data';

export interface BandSeries {
  low: Array<number | null>;
  high: Array<number | null>;
}

export interface ArmSeries {
  active: Array<number | null>;
  cumulative: Array<number | null>;
  incidence: Array<number | null>;
  attack: Array<number | null>;
  activeBand: BandSeries | null;
}

export interface RouteShift {
  routeId: string;
  name: string;
  family: string;
  base: number;
  treated: number;
}

/** Parish values are cumulative infection counts, not attack rates. */
export interface ParishAttack {
  id: ParishId;
  name: string;
  base: number;
  treated: number;
}

export interface BurdenLine {
  label: string;
  value: string;
  placeholder: boolean;
}

export interface CompareModel {
  job: JobStatusResponse;
  baselineName: string;
  treatedName: string;
  seeds: number[];
  startDate: string;
  days: number;
  population: number | null;
  baseline: ArmSeries;
  treated: ArmSeries;
  routes: RouteShift[];
  parishes: ParishAttack[];
  burden: BurdenLine[];
  measures: string[];
  derived: false;
  datasetGap: string[];
  servedDatasets: string[];
}

function text(row: DatasetRow | undefined, ...keys: string[]): string | null {
  if (!row) return null;
  for (const key of keys) {
    const value = row[key];
    if (typeof value === 'string' && value.trim()) return value;
  }
  return null;
}

function datesOf(rows: DatasetRow[]): string[] {
  return [...new Set(rows.map((row) => text(row, 'date')).filter((date): date is string => Boolean(date)))].sort();
}

function median(values: number[]): number | null {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function summaryRows(rows: DatasetRow[], scope: string, metric: string): DatasetRow[] {
  return rows.filter((row) => text(row, 'scope') === scope && text(row, 'metric') === metric);
}

function keyOf(row: DatasetRow): string {
  return text(row, 'key', 'route_id', 'parish') ?? '';
}

function summaryMetric(row: DatasetRow | undefined, field = 'median'): number | null {
  return optionalNumber(row, field, 'value', 'median');
}

function populationFromSummary(rows: DatasetRow[]): number | null {
  const values: number[] = [];
  for (const row of summaryRows(rows, 'epidemic', 'latent_attack_rate')) {
    const attack = summaryMetric(row);
    if (attack == null || attack <= 0) continue;
    const date = text(row, 'date');
    const cumulative = summaryRows(rows, 'epidemic', 'latent_cumulative_infections').find((candidate) => text(candidate, 'date') === date);
    const total = summaryMetric(cumulative);
    if (total != null && total > 0) values.push(total / attack);
  }
  return values.length ? median(values) : null;
}

function rowFor(rows: DatasetRow[], metric: string, date: string): DatasetRow | undefined {
  return summaryRows(rows, 'epidemic', metric).find((row) => text(row, 'date') === date);
}

export function armFromSummary(rows: DatasetRow[], dates: string[], population: number | null): ArmSeries {
  const active: Array<number | null> = [];
  const cumulative: Array<number | null> = [];
  const incidence: Array<number | null> = [];
  const attack: Array<number | null> = [];
  const low: Array<number | null> = [];
  const high: Array<number | null> = [];
  for (const date of dates) {
    const prevalence = summaryMetric(rowFor(rows, 'latent_prevalence', date));
    const cum = summaryMetric(rowFor(rows, 'latent_cumulative_infections', date));
    const inc = summaryMetric(rowFor(rows, 'latent_new_infections', date));
    const ar = summaryMetric(rowFor(rows, 'latent_attack_rate', date));
    active.push(prevalence != null && population != null ? prevalence * population : null);
    cumulative.push(cum);
    incidence.push(inc);
    attack.push(ar);
    const prevalenceRow = rowFor(rows, 'latent_prevalence', date);
    const lower = optionalNumber(prevalenceRow, 'lower_value', 'lower_quantile');
    const upper = optionalNumber(prevalenceRow, 'upper_value', 'upper_quantile');
    low.push(lower != null && population != null ? lower * population : null);
    high.push(upper != null && population != null ? upper * population : null);
  }
  const hasBand = low.some((value) => value != null) && high.some((value) => value != null);
  return { active, cumulative, incidence, attack, activeBand: hasBand ? { low, high } : null };
}

function armFromComparison(rows: DatasetRow[], dates: string[], side: 'a' | 'b', population: number | null): ArmSeries {
  const byDateMetric = (metric: string, date: string): number | null => {
    const values = rows
      .filter((row) => text(row, 'scope') === 'epidemic' && text(row, 'metric') === metric && text(row, 'date') === date)
      .map((row) => optionalNumber(row, side === 'a' ? 'value_a' : 'value_b'))
      .filter((value): value is number => value != null);
    return median(values);
  };
  const cumulative = dates.map((date) => byDateMetric('latent_cumulative_infections', date));
  const attack = dates.map((date) => byDateMetric('latent_attack_rate', date));
  const incidence = dates.map((date) => byDateMetric('latent_new_infections', date));
  const active = dates.map((date) => {
    const prevalence = byDateMetric('latent_prevalence', date);
    return prevalence != null && population != null ? prevalence * population : null;
  });
  return { active, cumulative, incidence, attack, activeBand: null };
}

function populationFromComparison(rows: DatasetRow[]): number | null {
  const values: number[] = [];
  for (const row of rows.filter((candidate) => text(candidate, 'scope') === 'epidemic' && text(candidate, 'metric') === 'latent_attack_rate')) {
    const attack = optionalNumber(row, 'value_a');
    const date = text(row, 'date');
    const cumulative = rows.find((candidate) => text(candidate, 'scope') === 'epidemic' && text(candidate, 'metric') === 'latent_cumulative_infections' && text(candidate, 'date') === date);
    const total = optionalNumber(cumulative, 'value_a');
    if (attack != null && attack > 0 && total != null && total > 0) values.push(total / attack);
  }
  return values.length ? median(values) : null;
}

function shiftsFromComparison(rows: DatasetRow[]): { routes: RouteShift[]; parishes: ParishAttack[] } {
  const collect = (scope: string, metric: string, side: 'a' | 'b'): Map<string, number> => {
    const output = new Map<string, number>();
    for (const row of rows.filter((candidate) => text(candidate, 'scope') === scope && text(candidate, 'metric') === metric)) {
      const key = keyOf(row);
      const value = optionalNumber(row, side === 'a' ? 'value_a' : 'value_b');
      if (key && !isIntroductionRoute(key) && value != null) output.set(key, (output.get(key) ?? 0) + value);
    }
    return output;
  };
  const baseRoutes = collect('route', 'latent_local_infections', 'a');
  const treatedRoutes = collect('route', 'latent_local_infections', 'b');
  const routes = [...new Set([...baseRoutes.keys(), ...treatedRoutes.keys()])]
    .filter((routeId) => baseRoutes.has(routeId) && treatedRoutes.has(routeId))
    .map((routeId) => ({ routeId, name: routeId.replace(/[_-]+/g, ' '), family: routeId.startsWith('visitor_') ? 'travel' : 'resident', base: baseRoutes.get(routeId) as number, treated: treatedRoutes.get(routeId) as number }))
    .sort((a, b) => b.base - a.base);
  const baseParishes = collect('parish', 'latent_new_infections', 'a');
  const treatedParishes = collect('parish', 'latent_new_infections', 'b');
  const parishes = [...baseParishes.entries()]
    .filter(([id]) => treatedParishes.has(id))
    .map(([id, base]) => ({ id: parishIdFromName(id) as ParishId, name: id, base, treated: treatedParishes.get(id) ?? 0 }))
    .filter((parish): parish is ParishAttack => Boolean(parish.id));
  return { routes, parishes };
}

function routesFromSummary(baseRows: DatasetRow[], treatedRows: DatasetRow[]): RouteShift[] {
  const collect = (rows: DatasetRow[]): Map<string, number> => {
    const output = new Map<string, number>();
    for (const row of summaryRows(rows, 'route', 'latent_local_infections')) {
      const id = keyOf(row);
      const value = summaryMetric(row);
      if (!id || isIntroductionRoute(id) || value == null) continue;
      output.set(id, (output.get(id) ?? 0) + value);
    }
    return output;
  };
  const base = collect(baseRows);
  const treated = collect(treatedRows);
  return [...new Set([...base.keys(), ...treated.keys()])]
    .filter((routeId) => base.has(routeId) && treated.has(routeId))
    .map((routeId) => ({ routeId, name: routeId.replace(/[_-]+/g, ' '), family: routeId.startsWith('visitor_') ? 'travel' : 'resident', base: base.get(routeId) as number, treated: treated.get(routeId) as number }))
    .sort((a, b) => b.base - a.base);
}

function parishesFromSummary(baseRows: DatasetRow[], treatedRows: DatasetRow[]): ParishAttack[] {
  const collect = (rows: DatasetRow[]): Map<ParishId, { name: string; value: number }> => {
    const output = new Map<ParishId, { name: string; value: number }>();
    for (const row of summaryRows(rows, 'parish', 'latent_new_infections')) {
      const id = parishIdFromName(keyOf(row));
      const value = summaryMetric(row);
      if (!id || value == null) continue;
      const current = output.get(id) ?? { name: keyOf(row), value: 0 };
      current.value += value;
      output.set(id, current);
    }
    return output;
  };
  const base = collect(baseRows);
  const treated = collect(treatedRows);
  return [...base.entries()]
    .filter(([id]) => treated.has(id))
    .map(([id, value]) => ({ id, name: value.name, base: value.value, treated: treated.get(id)?.value ?? 0 }));
}

function scenarioName(value: unknown, fallback: string): string {
  if (value && typeof value === 'object') {
    const record = value as JsonObject;
    const name = record.scenario_id ?? record.name;
    if (typeof name === 'string' && name.trim()) return name.trim();
  }
  return fallback;
}

function declaredMeasures(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => {
    if (typeof item === 'string') return item;
    if (item && typeof item === 'object') {
      const record = item as JsonObject;
      return String(record.type ?? record.family ?? record.kind ?? 'measure');
    }
    return 'measure';
  });
}

function placeholderBurden(measures: string[]): BurdenLine[] {
  return measures.length
    ? measures.map((measure) => ({ label: measure.replace(/[_-]+/g, ' '), value: 'not reported by this job', placeholder: true }))
    : [{ label: 'Intervention burden', value: 'not reported by this job', placeholder: true }];
}

/** Builds a comparison from the real namespaced M9 summary artifacts. */
export function buildCompareFromSummary(
  job: JobStatusResponse,
  baselineRows: DatasetRow[],
  treatedRows: DatasetRow[],
  servedDatasets: string[],
): CompareModel {
  const dates = [...new Set([...datesOf(baselineRows), ...datesOf(treatedRows)])].sort();
  if (!dates.length) throw new Error('The comparison arms contain no dated ensemble_summary rows.');
  const population = populationFromSummary(baselineRows);
  const baseline = armFromSummary(baselineRows, dates, population);
  const treated = armFromSummary(treatedRows, dates, population);
  const request = job.request as JsonObject;
  const treatedSpec = request.treated as JsonObject | undefined;
  const measures = declaredMeasures(treatedSpec?.interventions);
  return {
    job,
    baselineName: scenarioName(request.baseline, 'Baseline'),
    treatedName: scenarioName(request.treated, 'Intervention'),
    seeds: Array.isArray(request.replicate_seeds) ? request.replicate_seeds.filter((seed): seed is number => typeof seed === 'number') : [],
    startDate: typeof request.start_date === 'string' ? request.start_date : dates[0],
    days: dates.length,
    population,
    baseline,
    treated,
    routes: routesFromSummary(baselineRows, treatedRows),
    parishes: parishesFromSummary(baselineRows, treatedRows),
    burden: placeholderBurden(measures),
    measures,
    derived: false,
    datasetGap: ['Intervention-burden values are not published by the current M9 artifacts.'],
    servedDatasets,
  };
}

export function buildCompareFromMatchedComparison(job: JobStatusResponse, rows: DatasetRow[], servedDatasets: string[]): CompareModel {
  const dates = datesOf(rows);
  if (!dates.length) throw new Error('The matched_seed_comparison artifact contains no dated rows.');
  const request = job.request as JsonObject;
  const population = populationFromComparison(rows);
  const treatedSpec = request.treated as JsonObject | undefined;
  const shifts = shiftsFromComparison(rows);
  return {
    job,
    baselineName: scenarioName(request.baseline, 'Baseline'),
    treatedName: scenarioName(request.treated, 'Intervention'),
    seeds: Array.isArray(request.replicate_seeds) ? request.replicate_seeds.filter((seed): seed is number => typeof seed === 'number') : [],
    startDate: typeof request.start_date === 'string' ? request.start_date : dates[0],
    days: dates.length,
    population,
    baseline: armFromComparison(rows, dates, 'a', population),
    treated: armFromComparison(rows, dates, 'b', population),
    routes: shifts.routes,
    parishes: shifts.parishes,
    burden: placeholderBurden(declaredMeasures(treatedSpec?.interventions)),
    measures: declaredMeasures(treatedSpec?.interventions),
    derived: false,
    datasetGap: ['Persisted comparison values do not include intervention-burden fields.'],
    servedDatasets,
  };
}

export async function loadCompare(job: JobStatusResponse): Promise<CompareModel> {
  const listing = await api.getJobDatasets(job.job_id);
  const servedDatasets = listing.datasets
    .map((dataset) => (dataset as JsonObject).name)
    .filter((name): name is string => typeof name === 'string');
  const comparisonName = servedDatasets.includes('comparison:matched_seed_comparison') ? 'comparison:matched_seed_comparison' : null;
  if (comparisonName) {
    const comparisonRows = await readAllRows(job.job_id, comparisonName);
    if (comparisonRows.some((row) => text(row, 'scope') === 'epidemic' && text(row, 'metric') === 'latent_cumulative_infections')) {
      return buildCompareFromMatchedComparison(job, comparisonRows, servedDatasets);
    }
  }
  const baselineSummary = servedDatasets.includes('baseline:ensemble_summary') ? 'baseline:ensemble_summary' : null;
  const treatedSummary = servedDatasets.includes('treated:ensemble_summary') ? 'treated:ensemble_summary' : null;
  if (baselineSummary && treatedSummary) {
    const [baselineRows, treatedRows] = await Promise.all([
      readAllRows(job.job_id, baselineSummary),
      readAllRows(job.job_id, treatedSummary),
    ]);
    return buildCompareFromSummary(job, baselineRows, treatedRows, servedDatasets);
  }

  if (comparisonName) {
    const rows = await readAllRows(job.job_id, comparisonName);
    return buildCompareFromMatchedComparison(job, rows, servedDatasets);
  }
  throw new Error('This comparison job does not publish both namespaced arms or a matched_seed_comparison artifact.');
}

export function peakIndex(series: Array<number | null>): number {
  let best = -1;
  for (let index = 0; index < series.length; index += 1) {
    const value = series[index];
    if (value != null && (best < 0 || value > (series[best] ?? -Infinity))) best = index;
  }
  return best;
}

export function dayDate(startDate: string, day: number): Date {
  const [year, month, date] = startDate.split('-').map((value) => Number(value));
  const result = new Date(Date.UTC(year || 2025, (month || 1) - 1, date || 1));
  result.setUTCDate(result.getUTCDate() + day);
  return result;
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function formatDay(startDate: string, day: number): string {
  const date = dayDate(startDate, day);
  return `${date.getUTCDate()} ${MONTHS[date.getUTCMonth()]}`;
}

export const fmt = (value: number | null | undefined): string => value == null || !Number.isFinite(value) ? '—' : Math.round(value).toLocaleString('en-GB');

export const signed = (value: number): string => `${value < 0 ? '−' : '+'}${fmt(Math.abs(value))}`;

export const signedPct = (value: number, digits = 1): string => `${value < 0 ? '−' : '+'}${Math.abs(value).toFixed(digits)}%`;
