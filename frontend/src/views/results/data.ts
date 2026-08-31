/**
 * Results workspace data layer.
 *
 * This module is deliberately conservative: a missing scientific column is
 * represented as null and every derivation records its source in the
 * availability metadata. The UI must never turn an absent metric into zero.
 */

import { api, MAX_DATASET_ROWS } from '../../api';
import type { DatasetRow, JobStatusResponse, JsonObject } from '../../api';
import { PARISHES, parishIdFromName, type ParishId } from '../../map/geometry';

export const CORE_DATASETS = [
  'daily_epidemic',
  'daily_parish',
  'daily_route',
  'daily_age',
  'daily_travel',
] as const;

export const AUX_DATASETS = [
  'transmission_events',
  'detection_events',
  'observation_events',
  'daily_travel_route',
  'daily_travel_population',
] as const;

export const DATASETS = [...CORE_DATASETS, ...AUX_DATASETS] as const;
export type DatasetName = string;

/** A scientific value keeps absence distinct from a measured/derived zero. */
export interface ScientificValue<T> {
  value: T | null;
  available: boolean;
  source: string | null;
  reason: string | null;
}

export type MapMetric = 'new' | 'active' | 'cum' | 'detected' | 'attack' | 'visitor';

export interface MapMetricSpec {
  id: MapMetric;
  label: string;
  title: string;
}

export const MAP_METRICS: MapMetricSpec[] = [
  { id: 'new', label: 'New infections', title: 'New infections by parish' },
  { id: 'cum', label: 'Cumulative infected', title: 'Cumulative infected by parish' },
  { id: 'active', label: 'Active infectious', title: 'Active infectious by parish' },
  { id: 'detected', label: 'Detected cases', title: 'Detected cases by parish' },
  { id: 'attack', label: 'Ever infected', title: 'Ever-infected fraction by parish' },
  { id: 'visitor', label: 'Visitor-linked', title: 'Visitor-linked infections by parish' },
];

/* ============================== row helpers ============================== */

export function optionalNumber(row: DatasetRow | undefined, ...keys: string[]): number | null {
  if (!row) return null;
  for (const key of keys) {
    const value = row[key];
    if (typeof value === 'number' && Number.isFinite(value)) return value;
    if (typeof value === 'string' && value.trim() !== '' && Number.isFinite(Number(value))) {
      return Number(value);
    }
  }
  return null;
}

export function scientificNumber(
  row: DatasetRow | undefined,
  source: string,
  ...keys: string[]
): ScientificValue<number> {
  const value = optionalNumber(row, ...keys);
  return value == null
    ? { value: null, available: false, source: null, reason: `${source} did not publish ${keys.join(' / ')}` }
    : { value, available: true, source, reason: null };
}

function optionalString(row: DatasetRow | undefined, ...keys: string[]): string | null {
  if (!row) return null;
  for (const key of keys) {
    const value = row[key];
    if (typeof value === 'string' && value.trim()) return value;
  }
  return null;
}

function hasAny(rows: DatasetRow[], ...keys: string[]): boolean {
  return rows.some((row) => keys.some((key) => key in row));
}

function boolValue(row: DatasetRow, key: string): boolean {
  const value = row[key];
  if (typeof value === 'boolean') return value;
  if (typeof value === 'number') return value !== 0;
  return typeof value === 'string' && ['true', 'True', '1'].includes(value);
}

function sumPresent(row: DatasetRow, keys: string[]): number | null {
  const values = keys.map((key) => optionalNumber(row, key));
  return values.every((value) => value !== null) ? values.reduce((a, b) => a + (b as number), 0) : null;
}

function dateOf(row: DatasetRow): string | null {
  return optionalString(row, 'date', 'infection_date', 'detection_date');
}

function distinctDates(rowsets: DatasetRow[][]): string[] {
  const dates = new Set<string>();
  for (const rows of rowsets) {
    for (const row of rows) {
      const date = dateOf(row);
      if (date) dates.add(date);
    }
  }
  return [...dates].sort();
}

export async function readAllRows(
  jobId: string,
  name: string,
  columns?: string[],
): Promise<DatasetRow[]> {
  const rows: DatasetRow[] = [];
  let offset = 0;
  for (let page = 0; page < 200; page += 1) {
    const response = await api.readDataset(jobId, name, {
      limit: MAX_DATASET_ROWS,
      offset,
      ...(columns?.length ? { columns } : {}),
    });
    rows.push(...response.rows);
    if (!response.has_more || response.rows.length === 0) break;
    offset = response.next_offset ?? offset + response.rows.length;
  }
  return rows;
}

async function readProjected(jobId: string, name: string, columns: string[]): Promise<DatasetRow[]> {
  try {
    return await readAllRows(jobId, name, columns);
  } catch {
    return readAllRows(jobId, name);
  }
}

interface DatasetInfo {
  name: string;
  rowCount: number | null;
  columns: string[];
}

function normalizeListing(listing: unknown): Map<string, DatasetInfo> {
  const out = new Map<string, DatasetInfo>();
  const entries = (listing as { datasets?: unknown } | null)?.datasets;
  if (!Array.isArray(entries)) return out;
  for (const raw of entries) {
    const entry = (raw ?? {}) as JsonObject;
    const name = typeof entry.name === 'string' ? entry.name : '';
    if (!name) continue;
    const metadata = (entry.metadata && typeof entry.metadata === 'object' ? entry.metadata : {}) as JsonObject;
    const rowCount =
      typeof metadata.row_count === 'number'
        ? metadata.row_count
        : typeof entry.rows === 'number'
          ? entry.rows
          : null;
    const rawColumns = Array.isArray(metadata.columns)
      ? metadata.columns
      : Array.isArray(entry.columns)
        ? entry.columns
        : [];
    const columns = rawColumns
      .map((column) => {
        if (typeof column === 'string') return column;
        const object = column as JsonObject | null;
        return object && typeof object.name === 'string' ? object.name : '';
      })
      .filter(Boolean);
    out.set(name, { name, rowCount, columns });
  }
  return out;
}

function seedCount(job: JobStatusResponse): number {
  const seeds = (job.request as JsonObject).replicate_seeds;
  return Array.isArray(seeds) ? seeds.filter((seed) => typeof seed === 'number').length : 1;
}

/* ============================== derived shapes ============================== */

export interface EpiPoint {
  day: number;
  date: string;
  active: number | null;
  exposed: number | null;
  cum: number | null;
  detected: number | null;
  attack: number | null;
  newInfections: number | null;
  bandLow: number | null;
  bandHigh: number | null;
}

export interface ParishPoint {
  newInfections: number | null;
  active: number | null;
  cum: number | null;
  detected: number | null;
  attack: number | null;
  visitor: number | null;
}

export interface ParishSeries {
  id: ParishId;
  name: string;
  pop: number | null;
  points: ParishPoint[];
}

export interface RouteSeries {
  id: string;
  name: string;
  family: 'resident' | 'travel';
  perDay: number[];
  cumulative: number[];
}

export interface AgeSeries {
  band: string;
  pop: number | null;
  cum: Array<number | null>;
  newInfections: Array<number | null>;
}

export interface TravelPoint {
  arrivals: number | null;
  activeVisitors: number | null;
  visitorInfections: number | null;
  residentInfections: number | null;
  visitorToResident: number | null;
  residentToVisitor: number | null;
  travelLocalInfections: number | null;
  returningAcquisitions: number | null;
}

export interface TravelSeries {
  points: TravelPoint[];
  hasArrivals: boolean;
  hasActiveVisitors: boolean;
  hasFlows: boolean;
  hasReturning: boolean;
  hasLegacyLinked: boolean;
  source: string;
}

export interface Availability {
  detected: boolean;
  detectedSource: string | null;
  activeState: boolean;
  exposedState: boolean;
  parish: boolean;
  parishNote: string | null;
  parishActive: boolean;
  parishAttack: boolean;
  parishRoutes: boolean;
  routes: boolean;
  routeSource: string | null;
  routeNote: string | null;
  ages: boolean;
  ageSource: string | null;
  ageNote: string | null;
  agePopulations: boolean;
}

export interface ResultsData {
  job: JobStatusResponse;
  dates: string[];
  dayCount: number;
  startDate: string;
  population: number | null;
  seeds: number;
  epi: EpiPoint[];
  parishes: ParishSeries[];
  routes: RouteSeries[];
  ages: AgeSeries[];
  travel: TravelSeries | null;
  availability: Availability;
  mapMetrics: MapMetricSpec[];
  populationSource: string | null;
  cumulativeSource: string | null;
  cumulativeLabel: string;
  datasetNames: string[];
  raw: Partial<Record<DatasetName, DatasetRow[]>>;
}

/* ============================== common builders ============================== */

function parishPoints(dayCount: number): ParishPoint[] {
  return Array.from({ length: dayCount }, () => ({
    newInfections: null,
    active: null,
    cum: null,
    detected: null,
    attack: null,
    visitor: null,
  }));
}

function emptyAvailability(): Availability {
  return {
    detected: false,
    detectedSource: null,
    activeState: false,
    exposedState: false,
    parish: false,
    parishNote: null,
    parishActive: false,
    parishAttack: false,
    parishRoutes: false,
    routes: false,
    routeSource: null,
    routeNote: null,
    ages: false,
    ageSource: null,
    ageNote: null,
    agePopulations: false,
  };
}

function summaryValue(row: DatasetRow | undefined, primary = 'median', fallback = 'value'): number | null {
  return optionalNumber(row, primary, fallback, 'value');
}

function summaryRowsBy(rows: DatasetRow[], scope: string, metric: string): DatasetRow[] {
  return rows.filter((row) => optionalString(row, 'scope') === scope && optionalString(row, 'metric') === metric);
}

function summaryKey(row: DatasetRow): string {
  return optionalString(row, 'key', 'parish', 'route_id', 'age_band') ?? '';
}

function buildSummaryIndex(rows: DatasetRow[]): Map<string, DatasetRow> {
  const out = new Map<string, DatasetRow>();
  for (const row of rows) {
    const scope = optionalString(row, 'scope') ?? '';
    const key = summaryKey(row);
    const metric = optionalString(row, 'metric') ?? '';
    const date = optionalString(row, 'date') ?? '';
    out.set(`${scope}|${key}|${metric}|${date}`, row);
  }
  return out;
}

function buildResultsFromSummary(job: JobStatusResponse, rows: DatasetRow[], datasetNames: string[]): ResultsData {
  const dates = distinctDates([rows]);
  if (!dates.length) throw new Error('This ensemble published no ensemble_summary rows.');
  const index = buildSummaryIndex(rows);
  const lookup = (scope: string, key: string, metric: string, date: string): DatasetRow | undefined =>
    index.get(`${scope}|${key}|${metric}|${date}`);

  let population: number | null = null;
  for (const date of dates) {
    const cumulative = summaryValue(lookup('epidemic', 'all', 'latent_cumulative_infections', date));
    const attack = summaryValue(lookup('epidemic', 'all', 'latent_cumulative_incidence_per_capita', date));
    if (cumulative != null && attack != null && attack > 0) {
      const candidate = cumulative / attack;
      if (Number.isFinite(candidate) && candidate > 0) population = candidate;
    }
  }

  const epi: EpiPoint[] = dates.map((date, day) => {
    const prevalenceRow = lookup('epidemic', 'all', 'latent_prevalence', date);
    const cumulativeRow = lookup('epidemic', 'all', 'latent_cumulative_infections', date);
    const incidenceRow = lookup('epidemic', 'all', 'latent_new_infections', date);
    const attackRow = lookup('epidemic', 'all', 'latent_ever_infected_fraction', date);
    const prevalence = summaryValue(prevalenceRow);
    const active = prevalence != null && population != null ? prevalence * population : null;
    return {
      day,
      date,
      active,
      exposed: null,
      cum: summaryValue(cumulativeRow),
      detected: null,
      attack: summaryValue(attackRow),
      newInfections: summaryValue(incidenceRow),
      bandLow: (() => {
        const value = optionalNumber(prevalenceRow, 'lower_value');
        return value != null && population != null ? value * population : null;
      })(),
      bandHigh: (() => {
        const value = optionalNumber(prevalenceRow, 'upper_value');
        return value != null && population != null ? value * population : null;
      })(),
    };
  });

  const parishes: ParishSeries[] = PARISHES.map((parish) => ({ id: parish.id, name: parish.name, pop: null, points: parishPoints(dates.length) }));
  const parishById = new Map(parishes.map((parish) => [parish.id, parish]));
  const parishRows = summaryRowsBy(rows, 'parish', 'latent_new_infections');
  for (const row of parishRows) {
    const id = parishIdFromName(summaryKey(row));
    const day = dates.indexOf(optionalString(row, 'date') ?? '');
    if (!id || day < 0) continue;
    const series = parishById.get(id);
    if (!series) continue;
    const value = summaryValue(row);
    series.points[day].newInfections = value;
  }
  for (const series of parishes) {
    let running: number | null = null;
    for (const point of series.points) {
      if (point.newInfections != null) {
        running = (running ?? 0) + point.newInfections;
        point.cum = running;
      }
    }
  }

  const routeMap = new Map<string, RouteSeries>();
  for (const row of summaryRowsBy(rows, 'route', 'latent_local_infections')) {
    const id = summaryKey(row);
    const day = dates.indexOf(optionalString(row, 'date') ?? '');
    const value = summaryValue(row);
    if (!id || isIntroductionRoute(id) || day < 0 || value == null) continue;
    const current = routeMap.get(id) ?? {
      id,
      name: prettyRouteName(id),
      family: id.startsWith('visitor_') ? 'travel' : 'resident',
      perDay: new Array<number>(dates.length).fill(0),
      cumulative: new Array<number>(dates.length).fill(0),
    };
    current.perDay[day] = value;
    routeMap.set(id, current);
  }
  const routes = [...routeMap.values()];
  for (const route of routes) {
    let running = 0;
    route.perDay.forEach((value, day) => {
      running += value;
      route.cumulative[day] = running;
    });
  }

  const ageMap = new Map<string, AgeSeries>();
  for (const row of summaryRowsBy(rows, 'age', 'latent_new_infections')) {
    const band = summaryKey(row);
    const day = dates.indexOf(optionalString(row, 'date') ?? '');
    const value = summaryValue(row);
    if (!band || day < 0 || value == null) continue;
    const series = ageMap.get(band) ?? {
      band,
      pop: null,
      cum: new Array<number | null>(dates.length).fill(null),
      newInfections: new Array<number | null>(dates.length).fill(null),
    };
    series.newInfections[day] = value;
    ageMap.set(band, series);
  }
  const ages = [...ageMap.values()].sort((a, b) => a.band.localeCompare(b.band, 'en'));
  for (const age of ages) {
    let running = 0;
    age.newInfections.forEach((value, day) => {
      if (value != null) {
        running += value;
        age.cum[day] = running;
      }
    });
  }

  const availability = emptyAvailability();
  availability.activeState = epi.some((point) => point.active != null);
  availability.parish = parishRows.length > 0;
  availability.parishNote = availability.parish
    ? 'This ensemble publishes parish incidence; parish active, ever-infected fraction and route tables are unavailable.'
    : 'Parish breakdown was not published by this ensemble.';
  availability.routes = routes.length > 0;
  availability.routeSource = availability.routes ? 'ensemble_summary.latent_local_infections' : null;
  availability.routeNote = availability.routes
    ? 'Local infections attributed to resident routes; seeded and imported infections are excluded.'
    : null;
  availability.ages = ages.length > 0;
  availability.ageSource = availability.ages ? 'ensemble_summary.latent_new_infections' : null;
  availability.ageNote = availability.ages ? 'Age populations are not published by this ensemble.' : 'This ensemble published no age breakdown.';
  const mapMetrics = availability.parish ? MAP_METRICS.filter((metric) => metric.id === 'new' || metric.id === 'cum') : [];
  return {
    job,
    dates,
    dayCount: dates.length,
    startDate: dates[0],
    population,
    seeds: seedCount(job),
    epi,
    parishes,
    routes,
    ages,
    travel: null,
    availability,
    mapMetrics,
    populationSource: population != null ? 'ensemble_summary latent_cumulative_incidence_per_capita + latent_cumulative_infections' : null,
    cumulativeSource: 'ensemble_summary.latent_cumulative_infections',
    cumulativeLabel: 'Cumulative infected',
    datasetNames,
    raw: { ensemble_summary: rows },
  };
}

export function buildResultsFromEnsembleSummary(job: JobStatusResponse, rows: DatasetRow[], datasetNames = ['ensemble_summary']): ResultsData {
  return buildResultsFromSummary(job, rows, datasetNames);
}

/* ============================== single-run loading ============================== */

const TRAVEL_ROUTE_IDS = new Set([
  'arrival_terminal',
  'visitor_accommodation',
  'visitor_community_indoor',
  'visitor_community_outdoor',
  'visitor_host_household',
  'visitor_party',
  'visitor_transit',
]);

export function isIntroductionRoute(id: string): boolean {
  return id === 'seeded' || id === 'imported' || id === 'exogenous_import';
}

function prettyRouteName(id: string): string {
  const text = id.replace(/[_-]+/g, ' ').trim();
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : id;
}

function isTravelRoute(id: string, family: string): boolean {
  return family === 'travel' || TRAVEL_ROUTE_IDS.has(id) || id.startsWith('visitor_');
}

function populationFromEpi(rows: DatasetRow[]): { value: number | null; source: string | null } {
  let maxState = 0;
  for (const row of rows) {
    const state = sumPresent(row, ['susceptible', 'exposed', 'infectious', 'recovered', 'dead']);
    if (state != null && state > maxState) maxState = state;
  }
  if (maxState > 0) return { value: maxState, source: 'daily_epidemic state compartments' };
  for (const row of rows) {
    const resident = optionalNumber(row, 'resident_present', 'present_population');
    if (resident != null && resident > 0) return { value: resident, source: 'daily_epidemic published denominator' };
  }
  for (const row of rows) {
    const total = optionalNumber(row, 'cumulative_total_infections');
    const attack = optionalNumber(
      row,
      'cumulative_incidence_per_capita',
      'resident_cumulative_incidence_per_capita',
    );
    if (total != null && attack != null && attack > 0) {
      const value = total / attack;
      if (Number.isFinite(value) && value > 0) return { value, source: 'daily_epidemic cumulative_total_infections ÷ cumulative_incidence_per_capita' };
    }
  }
  return { value: null, source: null };
}

function buildSingleEpi(
  rows: DatasetRow[],
  dates: string[],
  detectionByDay: Array<number | null>,
  detectedColumn: string | null,
): { epi: EpiPoint[]; cumulativeSource: string | null; cumulativeLabel: string } {
  const byDate = new Map(rows.map((row) => [optionalString(row, 'date'), row]));
  const hasTotal = hasAny(rows, 'cumulative_total_infections');
  const hasExcluding = hasAny(rows, 'cumulative_infections');
  const hasComponents = hasAny(rows, 'new_infections', 'new_local_infections') && hasAny(rows, 'new_seeded_infections', 'seeded_infections');
  const cumulativeSource = hasTotal
    ? 'daily_epidemic.cumulative_total_infections'
    : hasComponents
      ? 'derived: daily_epidemic new_infections + new_seeded_infections'
      : hasExcluding
        ? 'daily_epidemic.cumulative_infections (excluding seeded infections)'
        : null;
  const cumulativeLabel = hasTotal || hasComponents ? 'Cumulative infected' : 'Locally acquired infections';
  let running: number | null = 0;
  const epi = dates.map((date, day) => {
    const row = byDate.get(date);
    if (!row) return { day, date, active: null, exposed: null, cum: null, detected: null, attack: null, newInfections: null, bandLow: null, bandHigh: null };
    const localOrImported = optionalNumber(row, 'new_infections', 'new_local_infections');
    const seeded = optionalNumber(row, 'new_seeded_infections', 'seeded_infections');
    const newTotal = localOrImported != null && seeded != null ? localOrImported + seeded : localOrImported;
    let cum: number | null;
    if (hasTotal) cum = optionalNumber(row, 'cumulative_total_infections');
    else if (hasComponents) {
      running = running == null || newTotal == null ? null : running + newTotal;
      cum = running;
    } else if (hasExcluding) cum = optionalNumber(row, 'cumulative_infections');
    else cum = null;
    const attackPublished = optionalNumber(
      row,
      'ever_infected_fraction',
      'resident_ever_infected_fraction',
    );
    const attack = attackPublished;
    return {
      day,
      date,
      active: optionalNumber(row, 'present_infectious', 'infectious', 'active_infectious', 'n_infectious'),
      exposed: optionalNumber(row, 'present_exposed', 'exposed', 'n_exposed'),
      cum,
      detected: detectedColumn ? optionalNumber(row, detectedColumn) : detectionByDay[day] ?? null,
      attack,
      newInfections: newTotal,
      bandLow: optionalNumber(row, 'band_low'),
      bandHigh: optionalNumber(row, 'band_high'),
    };
  });
  return { epi, cumulativeSource, cumulativeLabel };
}

function buildParishes(rows: DatasetRow[], dates: string[]): { parishes: ParishSeries[]; available: boolean; active: boolean; attack: boolean } {
  const parishes: ParishSeries[] = PARISHES.map((parish) => ({ id: parish.id, name: parish.name, pop: null, points: parishPoints(dates.length) }));
  const byId = new Map(parishes.map((parish) => [parish.id, parish]));
  const running = new Map<ParishId, number>();
  let validRows = 0;
  let hasActive = false;
  let hasAttack = false;
  for (const row of rows) {
    const id = parishIdFromName(optionalString(row, 'parish', 'parish_name') ?? '');
    const day = dates.indexOf(optionalString(row, 'date') ?? '');
    if (!id || day < 0) continue;
    const series = byId.get(id);
    if (!series) continue;
    const newValue = optionalNumber(row, 'new_infections') ?? sumPresent(row, ['new_local_infections', 'new_imported_infections', 'new_seeded_infections']);
    const publishedCum = optionalNumber(row, 'cumulative_total_infections', 'cumulative_infections');
    const cum = publishedCum ?? (newValue == null ? null : (running.get(id) ?? 0) + newValue);
    if (cum != null) running.set(id, cum);
    const pop = optionalNumber(row, 'population');
    if (pop != null) series.pop = pop;
    const active = optionalNumber(row, 'active_infectious', 'infectious');
    const attack = optionalNumber(row, 'ever_infected_fraction');
    hasActive ||= active != null;
    hasAttack ||= attack != null;
    if (newValue != null || cum != null) validRows += 1;
    series.points[day] = { newInfections: newValue, active, cum, detected: optionalNumber(row, 'detected_cases', 'detected'), attack, visitor: optionalNumber(row, 'visitor_linked_infections', 'travel_linked_infections') };
  }
  return { parishes, available: validRows > 0, active: hasActive, attack: hasAttack };
}

function buildRoutes(dailyRows: DatasetRow[], eventRows: DatasetRow[], dates: string[]): { routes: RouteSeries[]; source: string | null; note: string | null } {
  const map = new Map<string, RouteSeries>();
  const ensure = (id: string, name: string, family: string): RouteSeries => {
    const existing = map.get(id);
    if (existing) return existing;
    const created: RouteSeries = { id, name: name || prettyRouteName(id), family: isTravelRoute(id, family) ? 'travel' : 'resident', perDay: new Array<number>(dates.length).fill(0), cumulative: new Array<number>(dates.length).fill(0) };
    map.set(id, created);
    return created;
  };
  let source: string | null = null;
  let note: string | null = null;
  if (dailyRows.length && hasAny(dailyRows, 'new_local_infections')) {
    for (const row of dailyRows) {
      const id = optionalString(row, 'route_id', 'route');
      const day = dates.indexOf(optionalString(row, 'date') ?? '');
      const local = optionalNumber(row, 'new_local_infections');
      if (!id || isIntroductionRoute(id) || day < 0 || local == null) continue;
      ensure(id, optionalString(row, 'route_name') ?? '', optionalString(row, 'route_family') ?? '').perDay[day] = local;
    }
    source = 'daily_route.new_local_infections';
    note = 'Local infections attributed to resident routes; seeded and imported infections are excluded.';
  } else if (eventRows.length) {
    let excluded = 0;
    for (const row of eventRows) {
      const kind = optionalString(row, 'source_kind')?.toLowerCase();
      const day = dates.indexOf(optionalString(row, 'date') ?? '');
      const id = optionalString(row, 'attributed_route_id', 'route_id');
      if (day < 0 || !id) continue;
      if (kind !== 'local' || boolValue(row, 'seeded') || boolValue(row, 'imported')) {
        excluded += 1;
        continue;
      }
      ensure(id, '', boolValue(row, 'travel_linked') ? 'travel' : '').perDay[day] += 1;
    }
    if (map.size) {
      source = 'transmission_events.source_kind=local';
      note = `Local attributed transmission events only; ${excluded.toLocaleString('en-GB')} seeded, imported or non-local rows excluded.`;
    }
  }
  const routes = [...map.values()];
  for (const route of routes) {
    let running = 0;
    route.perDay.forEach((value, day) => { running += value; route.cumulative[day] = running; });
  }
  return { routes, source, note };
}

function buildAges(rows: DatasetRow[], eventRows: DatasetRow[], dates: string[]): { ages: AgeSeries[]; source: string | null; note: string | null; populations: boolean } {
  const map = new Map<string, AgeSeries>();
  const add = (band: string, day: number, value: number | null, pop: number | null) => {
    if (!band || day < 0 || value == null) return;
    const series = map.get(band) ?? { band, pop: null, cum: new Array<number | null>(dates.length).fill(null), newInfections: new Array<number | null>(dates.length).fill(null) };
    if (pop != null) series.pop = pop;
    series.newInfections[day] = value;
    map.set(band, series);
  };
  for (const row of rows) add(optionalString(row, 'age_band', 'band') ?? '', dates.indexOf(optionalString(row, 'date') ?? ''), optionalNumber(row, 'new_infections', 'new_local_infections') ?? sumPresent(row, ['new_local_infections', 'new_imported_infections', 'new_seeded_infections']), optionalNumber(row, 'population'));
  let source = map.size ? 'daily_age' : null;
  let note: string | null = null;
  if (!map.size) {
    for (const row of eventRows) add(optionalString(row, 'age_band', 'band') ?? '', dates.indexOf(optionalString(row, 'infection_date', 'date') ?? ''), 1, null);
    if (map.size) {
      source = 'observation_events';
      note = 'Age bands counted from observation_events; no per-band population denominator is published.';
    }
  }
  const ages = [...map.values()].sort((a, b) => a.band.localeCompare(b.band, 'en'));
  for (const age of ages) {
    let running = 0;
    age.newInfections.forEach((value, day) => { if (value != null) { running += value; age.cum[day] = running; } });
  }
  if (!ages.length) note = 'This run published no age breakdown.';
  return { ages, source, note, populations: ages.length > 0 && ages.every((age) => age.pop != null && age.pop > 0) };
}

function buildTravel(legacyRows: DatasetRow[], populationRows: DatasetRow[], routeRows: DatasetRow[], epiRows: DatasetRow[], dates: string[]): TravelSeries | null {
  const hasEpiVisitors = hasAny(epiRows, 'active_visitors');
  const hasEpiReturning = hasAny(epiRows, 'returning_resident_travel_acquisitions');
  if (!legacyRows.length && !populationRows.length && !routeRows.length && !hasEpiVisitors && !hasEpiReturning) return null;
  const points: TravelPoint[] = Array.from({ length: dates.length }, () => ({ arrivals: null, activeVisitors: null, visitorInfections: null, residentInfections: null, visitorToResident: null, residentToVisitor: null, travelLocalInfections: null, returningAcquisitions: null }));
  let hasArrivals = false;
  let hasLegacyLinked = false;
  for (const row of legacyRows) {
    const day = dates.indexOf(optionalString(row, 'date') ?? '');
    if (day < 0) continue;
    const point = points[day];
    point.arrivals = optionalNumber(row, 'arrivals', 'daily_arrivals');
    point.activeVisitors = optionalNumber(row, 'active_visitors', 'visitors_on_island');
    point.visitorInfections = optionalNumber(row, 'visitor_infections', 'visitor_linked_infections');
    point.residentInfections = optionalNumber(row, 'resident_infections');
    hasArrivals ||= point.arrivals != null;
    hasLegacyLinked ||= point.visitorInfections != null || point.residentInfections != null;
  }
  for (const row of populationRows) {
    const day = dates.indexOf(optionalString(row, 'date') ?? '');
    if (day < 0) continue;
    points[day].arrivals = optionalNumber(row, 'arrivals', 'daily_arrivals');
    points[day].activeVisitors = optionalNumber(row, 'active_visitors', 'visitors_on_island');
    hasArrivals ||= points[day].arrivals != null;
  }
  for (const row of routeRows) {
    const day = dates.indexOf(optionalString(row, 'date') ?? '');
    if (day < 0) continue;
    const visitorToResident = optionalNumber(row, 'visitor_to_resident');
    const residentToVisitor = optionalNumber(row, 'resident_to_visitor');
    const local = optionalNumber(row, 'new_local_infections');
    if (visitorToResident != null) points[day].visitorToResident = (points[day].visitorToResident ?? 0) + visitorToResident;
    if (residentToVisitor != null) points[day].residentToVisitor = (points[day].residentToVisitor ?? 0) + residentToVisitor;
    if (local != null) points[day].travelLocalInfections = (points[day].travelLocalInfections ?? 0) + local;
  }
  for (const row of epiRows) {
    const day = dates.indexOf(optionalString(row, 'date') ?? '');
    if (day < 0) continue;
    if (hasEpiVisitors) points[day].activeVisitors = optionalNumber(row, 'active_visitors');
    if (hasEpiReturning) points[day].returningAcquisitions = optionalNumber(row, 'returning_resident_travel_acquisitions');
  }
  return {
    points,
    hasArrivals,
    hasActiveVisitors: points.some((point) => point.activeVisitors != null),
    hasFlows: routeRows.length > 0,
    hasReturning: points.some((point) => point.returningAcquisitions != null),
    hasLegacyLinked,
    source: [legacyRows.length ? 'daily_travel' : '', populationRows.length ? 'daily_travel_population' : '', routeRows.length ? 'daily_travel_route' : '', hasEpiVisitors || hasEpiReturning ? 'daily_epidemic' : ''].filter(Boolean).join(' · '),
  };
}

export async function loadResults(job: JobStatusResponse): Promise<ResultsData> {
  const listing = normalizeListing(await api.getJobDatasets(job.job_id).catch(() => ({ datasets: [] })));
  const names = [...listing.keys()];
  if (job.kind === 'ensemble' || names.includes('ensemble_summary')) {
    const summaryRows = await readAllRows(job.job_id, 'ensemble_summary');
    return buildResultsFromSummary(job, summaryRows, names.length ? names : ['ensemble_summary']);
  }

  const hasRows = (name: string): boolean => {
    const info = listing.get(name);
    return !listing.size || Boolean(info && (info.rowCount == null || info.rowCount > 0));
  };
  const raw: Partial<Record<DatasetName, DatasetRow[]>> = {};
  await Promise.all(CORE_DATASETS.filter((name) => hasRows(name)).map(async (name) => {
    try {
      raw[name] = await readAllRows(job.job_id, name);
    } catch {
      if (name === 'daily_epidemic') throw new Error(`Could not read ${name}`);
    }
  }));
  const epiRows = raw.daily_epidemic ?? [];
  if (!epiRows.length) throw new Error('This run published no daily_epidemic rows, so there is nothing to show.');

  const needRoutes = !raw.daily_route?.length && hasRows('transmission_events');
  const needDetected = !hasAny(epiRows, 'detected_cases', 'cumulative_detected', 'detected', 'reported_cases') && hasRows('detection_events');
  const needAges = !raw.daily_age?.length && hasRows('observation_events');
  const needTravelRoute = !raw.daily_travel?.length && hasRows('daily_travel_route');
  const needTravelPop = !raw.daily_travel?.length && hasRows('daily_travel_population');
  await Promise.all([
    needRoutes ? readProjected(job.job_id, 'transmission_events', ['date', 'attributed_route_id', 'route_id', 'seeded', 'imported', 'travel_linked', 'source_kind']).then((rows) => { raw.transmission_events = rows; }).catch(() => undefined) : null,
    needDetected ? readProjected(job.job_id, 'detection_events', ['detection_date', 'detection_time_index']).then((rows) => { raw.detection_events = rows; }).catch(() => undefined) : null,
    needAges ? readProjected(job.job_id, 'observation_events', ['infection_date', 'age_band']).then((rows) => { raw.observation_events = rows; }).catch(() => undefined) : null,
    needTravelRoute ? readAllRows(job.job_id, 'daily_travel_route').then((rows) => { raw.daily_travel_route = rows; }).catch(() => undefined) : null,
    needTravelPop ? readAllRows(job.job_id, 'daily_travel_population').then((rows) => { raw.daily_travel_population = rows; }).catch(() => undefined) : null,
  ]);

  const parishRows = raw.daily_parish ?? [];
  const dates = distinctDates([epiRows, parishRows, raw.daily_route ?? [], raw.daily_travel ?? []]);
  const dayOf = new Map(dates.map((date, day) => [date, day]));
  const detectedColumn = ['detected_cases', 'cumulative_detected', 'detected', 'reported_cases'].find((column) => hasAny(epiRows, column)) ?? null;
  const detectionRows = raw.detection_events ?? [];
  const detectionByDay: Array<number | null> = new Array(dates.length).fill(null);
  if (!detectedColumn && detectionRows.length) {
    const counts = new Array<number>(dates.length).fill(0);
    for (const row of detectionRows) {
      const day = dayOf.get(optionalString(row, 'detection_date', 'date') ?? '');
      if (day != null) counts[day] += 1;
    }
    let running = 0;
    counts.forEach((value, day) => { running += value; detectionByDay[day] = running; });
  }
  const { value: population, source: populationSource } = populationFromEpi(epiRows);
  const { epi, cumulativeSource, cumulativeLabel } = buildSingleEpi(epiRows, dates, detectionByDay, detectedColumn);
  const parish = buildParishes(parishRows, dates);
  const route = buildRoutes(raw.daily_route ?? [], raw.transmission_events ?? [], dates);
  const age = buildAges(raw.daily_age ?? [], raw.observation_events ?? [], dates);
  const travel = buildTravel(raw.daily_travel ?? [], raw.daily_travel_population ?? [], raw.daily_travel_route ?? [], epiRows, dates);

  const availability = emptyAvailability();
  availability.detected = Boolean(detectedColumn || detectionRows.length);
  availability.detectedSource = detectedColumn ? `daily_epidemic.${detectedColumn}` : detectionRows.length ? 'detection_events' : null;
  availability.activeState = hasAny(epiRows, 'infectious', 'active_infectious', 'n_infectious');
  availability.exposedState = hasAny(epiRows, 'exposed', 'n_exposed');
  availability.parish = parish.available;
  availability.parishNote = parish.available
    ? 'This run publishes parish incidence. Parish active, ever-infected fraction or route data are shown only when their own fields are present.'
    : 'Parish breakdown was not published by this run.';
  availability.parishActive = parish.active;
  availability.parishAttack = parish.attack;
  availability.parishRoutes = false;
  availability.routes = route.routes.length > 0;
  availability.routeSource = route.source;
  availability.routeNote = route.note;
  availability.ages = age.ages.length > 0;
  availability.ageSource = age.source;
  availability.ageNote = age.note;
  availability.agePopulations = age.populations;
  const hasParishMetric = (metric: MapMetric): boolean => parish.parishes.some((series) => series.points.some((point) => parishMetricValue(point, metric) != null));
  const mapMetrics = parish.available ? MAP_METRICS.filter((metric) => hasParishMetric(metric.id)) : [];
  return {
    job,
    dates,
    dayCount: dates.length,
    startDate: dates[0] ?? '',
    population,
    seeds: seedCount(job),
    epi,
    parishes: parish.parishes,
    routes: route.routes,
    ages: age.ages,
    travel,
    availability,
    mapMetrics,
    populationSource,
    cumulativeSource,
    cumulativeLabel,
    datasetNames: names.length ? names : Object.keys(raw),
    raw,
  };
}

function parishMetricValue(point: ParishPoint, metric: MapMetric): number | null {
  if (metric === 'new') return point.newInfections;
  if (metric === 'active') return point.active;
  if (metric === 'cum') return point.cum;
  if (metric === 'detected') return point.detected;
  if (metric === 'attack') return point.attack;
  return point.visitor;
}

export function parishMetricPer1k(p: ParishSeries, day: number, metric: MapMetric): number | null {
  return parishMetricValue(p.points[day] ?? { newInfections: null, active: null, cum: null, detected: null, attack: null, visitor: null }, metric);
}

export function metricMax(parishes: ParishSeries[], dayCount: number, metric: MapMetric): number {
  let max = 0;
  for (const parish of parishes) {
    for (let day = 0; day < dayCount; day += 1) {
      const value = parishMetricPer1k(parish, day, metric);
      if (value != null && value > max) max = value;
    }
  }
  return max;
}

export interface RouteCount {
  key: string;
  name: string;
  family: 'resident' | 'travel';
  count: number;
  share: number;
}

export function routeCounts(routes: RouteSeries[], day: number, win: 'cum' | 'day'): RouteCount[] {
  const values = routes.map((route) => win === 'cum' ? route.cumulative[day] ?? 0 : route.perDay[day] ?? 0);
  const total = values.reduce((a, b) => a + b, 0);
  return routes.map((route, index) => ({ key: route.id, name: route.name, family: route.family, count: values[index], share: total > 0 ? values[index] / total : 0 }));
}

export interface Fizzle {
  cumulative: number;
  dieOutDay: number;
}

export function detectFizzle(data: ResultsData): Fizzle | null {
  if (!data.epi.length || !data.availability.activeState || !data.availability.exposedState) return null;
  const last = data.epi[data.epi.length - 1];
  if (last.exposed !== 0 || last.active !== 0 || last.cum == null || last.cum <= 0) return null;
  let dieOutDay = 0;
  for (let day = 0; day < data.epi.length; day += 1) {
    if ((data.epi[day].exposed ?? 0) > 0 || (data.epi[day].active ?? 0) > 0) dieOutDay = day;
  }
  return { cumulative: Math.round(last.cum), dieOutDay };
}

/* ============================== formatting ============================== */

export const fmt = (value: number | null | undefined): string => value == null || !Number.isFinite(value) ? '—' : Math.round(value).toLocaleString('en-GB');

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function parseISO(iso: string): Date | null {
  if (!iso) return null;
  const date = new Date(`${iso}T00:00:00Z`);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatDate(iso: string, long = false): string {
  const date = parseISO(iso);
  if (!date) return iso;
  const day = date.getUTCDate();
  const month = MONTHS[date.getUTCMonth()];
  return long ? `${WEEKDAYS[date.getUTCDay()]} ${day} ${month} ${date.getUTCFullYear()}` : `${day} ${month}`;
}

export function formatDateYear(iso: string): string {
  const date = parseISO(iso);
  if (!date) return iso;
  return `${date.getUTCDate()} ${MONTHS[date.getUTCMonth()]} ${date.getUTCFullYear()}`;
}

export function isoPlusDays(iso: string, days: number): string {
  const date = parseISO(iso);
  if (!date) return iso;
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

export function shortHash(hash: string | null | undefined): string {
  if (!hash) return '—';
  return hash.length <= 12 ? hash : `${hash.slice(0, 6)}…${hash.slice(-4)}`;
}
