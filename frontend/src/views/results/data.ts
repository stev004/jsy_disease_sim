/**
 * Results workspace data layer.
 *
 * On open the workspace pages every tidy dataset the job published through the
 * bounded `readDataset` endpoint into typed in-memory arrays, then derives the
 * per-day / per-parish / per-route series the whole view scrubs over. After
 * this module resolves, no further network calls happen — every interaction is
 * client-side and instant.
 */

import { api, MAX_DATASET_ROWS } from '../../api';
import type { DatasetRow, JobStatusResponse, JsonObject } from '../../api';
import { ISLAND_POP, PARISHES, parishIdFromName, type ParishId } from '../../map/geometry';

/**
 * The tidy per-day tables the workspace reads first. Older / simpler artifacts
 * (m5, m7) publish all of these; the travel-composed artifacts publish only
 * `daily_epidemic` with rows and leave the rest as empty schemas.
 */
export const CORE_DATASETS = [
  'daily_epidemic',
  'daily_parish',
  'daily_route',
  'daily_age',
  'daily_travel',
] as const;

/**
 * Event-level and travel tables the workspace falls back to when a per-day
 * table exists but carries no rows. These are only fetched when they are
 * actually needed, and always with a column projection.
 */
export const AUX_DATASETS = [
  'transmission_events',
  'detection_events',
  'observation_events',
  'daily_travel_route',
  'daily_travel_population',
] as const;

export const DATASETS = [...CORE_DATASETS, ...AUX_DATASETS] as const;

export type DatasetName = (typeof DATASETS)[number];

/** Map metric ids (left picker). */
export type MapMetric = 'active' | 'cum' | 'detected' | 'attack' | 'visitor';

export interface MapMetricSpec {
  id: MapMetric;
  label: string;
  title: string;
}

export const MAP_METRICS: MapMetricSpec[] = [
  { id: 'active', label: 'Active infectious', title: 'Active infectious per 1,000 residents' },
  { id: 'cum', label: 'Cumulative infected', title: 'Cumulative infected per 1,000' },
  { id: 'detected', label: 'Detected cases', title: 'Detected cases per 1,000' },
  { id: 'attack', label: 'Attack rate', title: 'Attack rate by parish' },
  { id: 'visitor', label: 'Visitor-linked', title: 'Visitor-linked infections' },
];

/* ============================== row helpers ============================== */

/** First numeric value among candidate column names (real + mock spellings). */
function num(row: DatasetRow, ...keys: string[]): number {
  for (const k of keys) {
    const v = row[k];
    if (typeof v === 'number' && Number.isFinite(v)) return v;
    if (typeof v === 'string' && v !== '' && Number.isFinite(Number(v))) return Number(v);
  }
  return 0;
}

function str(row: DatasetRow, ...keys: string[]): string {
  for (const k of keys) {
    const v = row[k];
    if (typeof v === 'string' && v) return v;
  }
  return '';
}

function has(row: DatasetRow | undefined, key: string): boolean {
  return Boolean(row) && key in (row as DatasetRow);
}

/** Truthy test that accepts the several ways a parquet bool reaches JSON. */
function flag(row: DatasetRow, key: string): boolean {
  const v = row[key];
  if (typeof v === 'boolean') return v;
  if (typeof v === 'number') return v !== 0;
  if (typeof v === 'string') return v === 'true' || v === 'True' || v === '1';
  return false;
}

/** Largest finite value of the first present column across every row. */
function maxNum(rows: DatasetRow[], ...keys: string[]): number {
  let m = 0;
  for (const r of rows) {
    const v = num(r, ...keys);
    if (v > m) m = v;
  }
  return m;
}

/** Pages a whole dataset through the bounded endpoint. */
export async function readAllRows(
  jobId: string,
  name: string,
  columns?: string[],
): Promise<DatasetRow[]> {
  const out: DatasetRow[] = [];
  let offset = 0;
  // Guard: 200 pages x 10k rows is far beyond any M9 artifact.
  for (let page = 0; page < 200; page += 1) {
    const res = await api.readDataset(jobId, name, {
      limit: MAX_DATASET_ROWS,
      offset,
      ...(columns && columns.length ? { columns } : {}),
    });
    out.push(...res.rows);
    if (!res.has_more || res.rows.length === 0) break;
    offset = res.next_offset ?? offset + res.rows.length;
  }
  return out;
}

/**
 * Reads an event table with a column projection, retrying unprojected if the
 * server rejects the projection (older API builds, or a renamed column).
 */
async function readProjected(
  jobId: string,
  name: string,
  columns: string[],
): Promise<DatasetRow[]> {
  try {
    return await readAllRows(jobId, name, columns);
  } catch {
    return readAllRows(jobId, name);
  }
}

/* ============================== derived shapes ============================== */

export interface EpiPoint {
  day: number;
  date: string;
  active: number;
  cum: number;
  detected: number;
  attack: number;
  newInfections: number;
  /** Replicate-range columns when the artifact carries them. */
  bandLow: number | null;
  bandHigh: number | null;
}

export interface ParishPoint {
  active: number;
  cum: number;
  detected: number;
  attack: number;
  visitor: number;
}

export interface ParishSeries {
  id: ParishId;
  name: string;
  pop: number;
  points: ParishPoint[];
}

export interface RouteSeries {
  id: string;
  name: string;
  family: 'resident' | 'travel';
  /** New infection events attributed to this route on each day. */
  perDay: number[];
  /** Cumulative infection events up to and including each day. */
  cumulative: number[];
}

export interface AgeSeries {
  band: string;
  pop: number;
  cum: number[];
  newInfections: number[];
}

export interface TravelPoint {
  arrivals: number;
  activeVisitors: number;
  /** Legacy per-day columns (`visitor_infections` / `resident_infections`). */
  visitorInfections: number;
  residentInfections: number;
  /** Real travel-artifact flows, summed across travel routes for the day. */
  visitorToResident: number;
  residentToVisitor: number;
  travelLocalInfections: number;
  /** Residents who acquired infection abroad and returned that day. */
  returningAcquisitions: number;
}

export interface TravelSeries {
  points: TravelPoint[];
  hasArrivals: boolean;
  hasActiveVisitors: boolean;
  /** `visitor_to_resident` / `resident_to_visitor` came from daily_travel_route. */
  hasFlows: boolean;
  hasReturning: boolean;
  /** Legacy mock-shaped visitor/resident infection split. */
  hasLegacyLinked: boolean;
  source: string;
}

/**
 * Which derived surfaces this run can honestly show, and where each came from.
 * Every consumer must check these before rendering a number — a metric the run
 * did not publish is shown as "not published", never as zero.
 */
export interface Availability {
  detected: boolean;
  detectedSource: string | null;
  parish: boolean;
  parishNote: string | null;
  routes: boolean;
  routeSource: string | null;
  routeNote: string | null;
  ages: boolean;
  ageSource: string | null;
  ageNote: string | null;
  /** Age bands carry their own denominators (so "% of band" is meaningful). */
  agePopulations: boolean;
}

export interface ResultsData {
  job: JobStatusResponse;
  /** ISO dates, one per simulated day, in order. */
  dates: string[];
  dayCount: number;
  startDate: string;
  population: number;
  seeds: number;
  epi: EpiPoint[];
  parishes: ParishSeries[];
  routes: RouteSeries[];
  ages: AgeSeries[];
  travel: TravelSeries | null;
  availability: Availability;
  /** Map metrics this run can actually colour (empty when no parish table). */
  mapMetrics: MapMetricSpec[];
  /** Where the resident denominator came from, for the honesty strip. */
  populationSource: string;
  /** Datasets actually available on this job (for the provenance strip). */
  datasetNames: string[];
  /** Raw rows, kept for honest CSV export of exactly what was loaded. */
  raw: Partial<Record<DatasetName, DatasetRow[]>>;
}

/* ============================== loading ============================== */

function distinctDates(rowsets: DatasetRow[][]): string[] {
  const seen = new Set<string>();
  for (const rows of rowsets) {
    for (const r of rows) {
      const d = str(r, 'date');
      if (d) seen.add(d);
    }
  }
  return [...seen].sort();
}

function seedCount(job: JobStatusResponse): number {
  const seeds = (job.request as JsonObject).replicate_seeds;
  if (Array.isArray(seeds)) return seeds.length;
  return 1;
}

function emptyParishPoints(n: number): ParishPoint[] {
  return Array.from({ length: n }, () => ({
    active: 0,
    cum: 0,
    detected: 0,
    attack: 0,
    visitor: 0,
  }));
}

/* ---------------------------- dataset listing ---------------------------- */

interface DatasetInfo {
  name: string;
  /** null when the listing reports no row count at all. */
  rowCount: number | null;
  columns: string[];
}

/** Normalises the real API listing and the mock listing into one shape. */
function normalizeListing(listing: unknown): Map<string, DatasetInfo> {
  const out = new Map<string, DatasetInfo>();
  const entries = (listing as { datasets?: unknown } | null)?.datasets;
  if (!Array.isArray(entries)) return out;
  for (const entry of entries) {
    const e = (entry ?? {}) as JsonObject;
    const name = typeof e.name === 'string' ? e.name : '';
    if (!name) continue;
    const meta = (typeof e.metadata === 'object' && e.metadata ? e.metadata : {}) as JsonObject;
    const rowCount =
      typeof meta.row_count === 'number'
        ? meta.row_count
        : typeof e.rows === 'number'
          ? e.rows
          : null;
    const rawCols = Array.isArray(meta.columns) ? meta.columns : Array.isArray(e.columns) ? e.columns : [];
    const columns = rawCols
      .map((c) => {
        if (typeof c === 'string') return c;
        const o = c as JsonObject | null;
        return o && typeof o.name === 'string' ? o.name : '';
      })
      .filter(Boolean);
    out.set(name, { name, rowCount, columns });
  }
  return out;
}

/**
 * Travel-family route ids. The composed travel artifacts name them explicitly
 * in `daily_travel_route`; this set is the fallback for artifacts that do not
 * publish that table.
 */
const TRAVEL_ROUTE_IDS = new Set([
  'arrival_terminal',
  'visitor_accommodation',
  'visitor_community_indoor',
  'visitor_community_outdoor',
  'visitor_host_household',
  'visitor_party',
  'visitor_transit',
]);

/** Loads and derives everything the workspace needs for one job. */
export async function loadResults(job: JobStatusResponse): Promise<ResultsData> {
  const jobId = job.job_id;

  let listing = new Map<string, DatasetInfo>();
  try {
    listing = normalizeListing(await api.getJobDatasets(jobId));
  } catch {
    /* fall back to attempting the canonical per-day tables */
  }

  const known = (name: string): DatasetInfo | undefined => listing.get(name);
  /** Listed with at least one row (unknown counts are treated as "maybe"). */
  const hasRows = (name: string): boolean => {
    const info = known(name);
    if (!info) return false;
    return info.rowCount === null || info.rowCount > 0;
  };
  const hasColumn = (name: string, column: string): boolean =>
    (known(name)?.columns ?? []).includes(column);

  // Empty listing => older/mock server: just try the canonical per-day tables.
  const coreWanted = CORE_DATASETS.filter((n) => (listing.size === 0 ? true : hasRows(n)));

  const raw: Partial<Record<DatasetName, DatasetRow[]>> = {};
  await Promise.all(
    coreWanted.map(async (name) => {
      try {
        raw[name] = await readAllRows(jobId, name);
      } catch {
        // A missing optional table (e.g. daily_travel) must not fail the view.
        if (name === 'daily_epidemic') throw new Error(`Could not read ${name}`);
      }
    }),
  );

  const epiRows = raw.daily_epidemic ?? [];
  if (epiRows.length === 0) {
    throw new Error('This run published no daily_epidemic rows, so there is nothing to show.');
  }

  /* ---- decide which event tables we still need, then fetch only those ---- */
  const epiCols = new Set(Object.keys(epiRows[0]));
  const detectedCol = ['detected_cases', 'cumulative_detected', 'detected', 'reported_cases'].find(
    (c) => epiCols.has(c),
  );

  const needRoutes = (raw.daily_route?.length ?? 0) === 0 && hasRows('transmission_events');
  const needDetected = !detectedCol && hasRows('detection_events');
  const needAges =
    (raw.daily_age?.length ?? 0) === 0 &&
    hasRows('observation_events') &&
    hasColumn('observation_events', 'age_band');
  const needTravelRoute = !raw.daily_travel?.length && hasRows('daily_travel_route');
  const needTravelPop = !raw.daily_travel?.length && hasRows('daily_travel_population');

  await Promise.all([
    needRoutes
      ? readProjected(jobId, 'transmission_events', [
          'date',
          'attributed_route_id',
          'route_id',
          'seeded',
          'imported',
          'travel_linked',
          'source_kind',
        ])
          .then((rows) => {
            raw.transmission_events = rows;
          })
          .catch(() => undefined)
      : null,
    needDetected
      ? readProjected(jobId, 'detection_events', ['detection_date', 'detection_time_index'])
          .then((rows) => {
            raw.detection_events = rows;
          })
          .catch(() => undefined)
      : null,
    needAges
      ? readProjected(jobId, 'observation_events', ['infection_date', 'age_band'])
          .then((rows) => {
            raw.observation_events = rows;
          })
          .catch(() => undefined)
      : null,
    needTravelRoute
      ? readAllRows(jobId, 'daily_travel_route')
          .then((rows) => {
            raw.daily_travel_route = rows;
          })
          .catch(() => undefined)
      : null,
    needTravelPop
      ? readAllRows(jobId, 'daily_travel_population')
          .then((rows) => {
            raw.daily_travel_population = rows;
          })
          .catch(() => undefined)
      : null,
  ]);

  const dates = distinctDates([epiRows, raw.daily_parish ?? []]);
  const dayOf = new Map(dates.map((d, i) => [d, i]));
  const dayCount = dates.length;

  /* ---- population ------------------------------------------------------
     Never assume the island's real headcount: a run simulates whatever
     synthetic population it was given. Prefer the run's own denominator. */
  const parishRows = raw.daily_parish ?? [];
  let population = 0;
  let populationSource = '';
  const residentPresent = maxNum(epiRows, 'resident_present');
  const presentPop = maxNum(epiRows, 'present_population');
  if (residentPresent > 0) {
    population = residentPresent;
    populationSource = 'daily_epidemic.resident_present';
  } else if (presentPop > 0) {
    population = presentPop;
    populationSource = 'daily_epidemic.present_population';
  }
  if (!population && parishRows.length && has(parishRows[0], 'population')) {
    const perParish = new Map<string, number>();
    for (const r of parishRows) {
      const name = str(r, 'parish', 'parish_name');
      if (name && !perParish.has(name)) perParish.set(name, num(r, 'population'));
    }
    population = [...perParish.values()].reduce((a, b) => a + b, 0);
    if (population) populationSource = 'daily_parish.population';
  }
  if (!population) {
    const first = epiRows[0];
    population =
      num(first, 'susceptible') + num(first, 'cumulative_infections', 'cumulative_total_infections');
    if (population) populationSource = 'daily_epidemic day 0 susceptible + cumulative';
  }
  if (!population) {
    population = ISLAND_POP;
    populationSource = 'Jersey resident population (no denominator published)';
  }

  /* ---- detected: a cumulative count of detection events by date ---- */
  const detectionRows = raw.detection_events ?? [];
  const detectedByDay = new Array<number>(dayCount).fill(0);
  let detectedAvailable = Boolean(detectedCol);
  let detectedSource: string | null = detectedCol ? `daily_epidemic.${detectedCol}` : null;
  if (!detectedCol && detectionRows.length) {
    for (const r of detectionRows) {
      const day = dayOf.get(str(r, 'detection_date', 'date'));
      if (day == null) continue;
      detectedByDay[day] += 1;
    }
    let running = 0;
    for (let d = 0; d < dayCount; d += 1) {
      running += detectedByDay[d];
      detectedByDay[d] = running;
    }
    detectedAvailable = true;
    detectedSource = 'detection_events';
  }

  /* ---- epidemic ---- */
  const hasBand = has(epiRows[0], 'band_low') && has(epiRows[0], 'band_high');
  const hasCumColumn = epiCols.has('cumulative_infections') || epiCols.has('cumulative_total_infections');
  const seededCol = ['seeded_infections', 'new_seeded_infections'].find((c) => epiCols.has(c));
  const attackCol = ['resident_attack_rate', 'attack_rate'].find((c) => epiCols.has(c));
  const epiByDate = new Map<string, DatasetRow>();
  for (const r of epiRows) {
    const d = str(r, 'date');
    if (d) epiByDate.set(d, r);
  }

  let runningCumulative = 0;
  const epi: EpiPoint[] = dates.map((date, day) => {
    const r = epiByDate.get(date);
    if (!r) {
      return {
        day,
        date,
        active: 0,
        cum: runningCumulative,
        detected: detectedAvailable && !detectedCol ? detectedByDay[day] : 0,
        attack: population ? runningCumulative / population : 0,
        newInfections: 0,
        bandLow: null,
        bandHigh: null,
      };
    }
    const newInfections = num(r, 'new_infections', 'new_local_infections');
    // Seeded infections are reported in their own column and are NOT included
    // in `new_infections`, so a derived cumulative must add them back.
    const seeded = seededCol ? num(r, seededCol) : 0;
    runningCumulative = hasCumColumn
      ? num(r, 'cumulative_infections', 'cumulative_total_infections')
      : runningCumulative + newInfections + seeded;
    const cum = runningCumulative;
    return {
      day,
      date,
      active: num(r, 'infectious', 'active_infectious', 'n_infectious'),
      cum,
      detected: detectedCol ? num(r, detectedCol) : detectedAvailable ? detectedByDay[day] : 0,
      // `resident_attack_rate` / `attack_rate` are already fractions of the
      // run's own resident denominator — use them verbatim.
      attack: attackCol ? num(r, attackCol) : population ? cum / population : 0,
      newInfections,
      bandLow: hasBand ? num(r, 'band_low') : null,
      bandHigh: hasBand ? num(r, 'band_high') : null,
    };
  });

  /* ---- parishes ----
     When the run published no parish rows we still build the (zeroed) series so
     geometry code keeps working, but flag it so nothing renders those zeros as
     if they were measurements. */
  const parishAvailable = parishRows.length > 0;
  const parishMap = new Map<ParishId, ParishSeries>();
  for (const p of PARISHES) {
    parishMap.set(p.id, { id: p.id, name: p.name, pop: p.pop, points: emptyParishPoints(dayCount) });
  }
  const parishHasActive = parishRows.length > 0 && has(parishRows[0], 'active_infectious');
  const parishHasDetected = parishRows.length > 0 && has(parishRows[0], 'detected_cases');
  const runningCum = new Map<ParishId, number>();
  for (const r of parishRows) {
    const day = dayOf.get(str(r, 'date'));
    const name = str(r, 'parish', 'parish_name');
    const id = parishIdFromName(name);
    if (day == null || !id) continue;
    const series = parishMap.get(id);
    if (!series) continue;
    const pop = num(r, 'population') || series.pop;
    series.pop = pop;
    let cum = num(r, 'cumulative_infections', 'cumulative_total_infections');
    if (!cum) {
      // Some artifacts only carry daily increments — accumulate them.
      cum = (runningCum.get(id) ?? 0) + num(r, 'new_infections', 'new_local_infections');
      runningCum.set(id, cum);
    }
    const attack = num(r, 'attack_rate') || (pop ? cum / pop : 0);
    series.points[day] = {
      active: parishHasActive
        ? num(r, 'active_infectious', 'infectious')
        : num(r, 'new_infections', 'new_local_infections'),
      cum,
      detected: num(r, 'detected_cases'),
      attack,
      visitor: num(r, 'visitor_linked_infections', 'travel_linked_infections'),
    };
  }
  const parishes = PARISHES.map((p) => parishMap.get(p.id)!).filter(Boolean);

  /* ---- routes ----
     Preferred source is the tidy `daily_route` table. Travel-composed
     artifacts publish that table with zero rows, so the event-level
     `transmission_events` table is attributed per day instead. */
  const travelRouteIds = new Set(TRAVEL_ROUTE_IDS);
  for (const r of raw.daily_travel_route ?? []) {
    const id = str(r, 'route_id');
    if (id) travelRouteIds.add(id);
  }
  const isTravelRoute = (id: string, familyCol: string): boolean =>
    familyCol === 'travel' || travelRouteIds.has(id) || id.startsWith('visitor_');

  const routeMap = new Map<string, RouteSeries>();
  const ensureRoute = (id: string, name: string, familyCol: string): RouteSeries => {
    let series = routeMap.get(id);
    if (!series) {
      series = {
        id,
        name: name || prettyRouteName(id),
        family: isTravelRoute(id, familyCol) ? 'travel' : 'resident',
        perDay: new Array<number>(dayCount).fill(0),
        cumulative: new Array<number>(dayCount).fill(0),
      };
      routeMap.set(id, series);
    }
    return series;
  };

  const dailyRouteRows = raw.daily_route ?? [];
  const eventRouteRows = dailyRouteRows.length ? [] : (raw.transmission_events ?? []);
  let routeSource: string | null = null;
  let routeNote: string | null = null;
  let seededExcluded = 0;

  for (const r of dailyRouteRows) {
    const day = dayOf.get(str(r, 'date'));
    const id = str(r, 'route_id', 'route');
    if (day == null || !id) continue;
    const series = ensureRoute(id, str(r, 'route_name'), str(r, 'route_family'));
    series.perDay[day] = num(r, 'new_events', 'new_infections', 'new_local_infections');
    series.cumulative[day] = num(r, 'cumulative_infections', 'cumulative_events');
  }
  if (dailyRouteRows.length) {
    routeSource = 'daily_route';
    routeNote =
      'Counts are simulated infection events attributed to the route where transmission occurred.';
  }

  for (const r of eventRouteRows) {
    const day = dayOf.get(str(r, 'date'));
    if (day == null) continue;
    const kind = str(r, 'source_kind');
    const id = str(r, 'attributed_route_id', 'route_id');
    const isSeed =
      flag(r, 'seeded') ||
      flag(r, 'imported') ||
      kind === 'seeded' ||
      kind === 'imported' ||
      id === 'seeded' ||
      id === 'imported';
    if (isSeed) {
      seededExcluded += 1;
      continue;
    }
    if (!id) continue;
    ensureRoute(id, '', flag(r, 'travel_linked') ? 'travel' : '').perDay[day] += 1;
  }
  if (eventRouteRows.length) {
    routeSource = 'transmission_events';
    routeNote =
      `This run published no daily_route rows, so routes are attributed per day from the ` +
      `${fmt(eventRouteRows.length)} rows of transmission_events (attributed_route_id, falling ` +
      `back to route_id).` +
      (seededExcluded
        ? ` ${fmt(seededExcluded)} seeded or imported ${seededExcluded === 1 ? 'infection is' : 'infections are'} excluded from the ranking — they had no within-island route.`
        : '');
  }

  const routes = [...routeMap.values()];
  for (const s of routes) {
    // Backfill cumulative when the artifact only reports daily counts.
    let running = 0;
    const anyCum = s.cumulative.some((v) => v > 0);
    for (let d = 0; d < dayCount; d += 1) {
      running += s.perDay[d];
      if (!anyCum) s.cumulative[d] = running;
      else if (s.cumulative[d] === 0 && d > 0) s.cumulative[d] = s.cumulative[d - 1];
    }
  }

  /* ---- ages ---- */
  const ageMap = new Map<string, AgeSeries>();
  for (const r of raw.daily_age ?? []) {
    const day = dayOf.get(str(r, 'date'));
    const band = str(r, 'age_band', 'band');
    if (day == null || !band) continue;
    let series = ageMap.get(band);
    if (!series) {
      series = {
        band,
        pop: num(r, 'population'),
        cum: new Array<number>(dayCount).fill(0),
        newInfections: new Array<number>(dayCount).fill(0),
      };
      ageMap.set(band, series);
    }
    if (!series.pop) series.pop = num(r, 'population');
    series.cum[day] = num(r, 'cumulative_infections', 'cumulative_total_infections');
    series.newInfections[day] = num(r, 'new_infections', 'new_local_infections');
  }
  let ageSource: string | null = ageMap.size ? 'daily_age' : null;
  let ageNote: string | null = null;

  // Fallback: the per-infection line list carries an age band per case.
  const ageEventRows = ageMap.size ? [] : (raw.observation_events ?? []);
  for (const r of ageEventRows) {
    const day = dayOf.get(str(r, 'infection_date', 'date'));
    const band = str(r, 'age_band', 'band');
    if (day == null || !band) continue;
    let series = ageMap.get(band);
    if (!series) {
      series = {
        band,
        pop: 0,
        cum: new Array<number>(dayCount).fill(0),
        newInfections: new Array<number>(dayCount).fill(0),
      };
      ageMap.set(band, series);
    }
    series.newInfections[day] += 1;
  }
  if (ageEventRows.length) {
    ageSource = 'observation_events';
    ageNote =
      'This run published no daily_age table. Bands are counted from the per-infection ' +
      'observation_events line list; it carries no per-band denominators, so these are ' +
      'infection counts and shares of all infections, not attack rates.';
  }

  // Bands sort by their lower bound ("0-4" < "5-17" < "18-64" < "65+").
  const bandLowerBound = (band: string): number => {
    const m = /-?\d+/.exec(band);
    return m ? Number(m[0]) : Number.MAX_SAFE_INTEGER;
  };
  const ages = [...ageMap.values()].sort(
    (a, b) => bandLowerBound(a.band) - bandLowerBound(b.band) || a.band.localeCompare(b.band, 'en'),
  );
  for (const a of ages) {
    const noCumulativeColumn = a.cum.reduce((s, v) => s + v, 0) === 0;
    if (noCumulativeColumn) {
      let running = 0;
      for (let d = 0; d < dayCount; d += 1) {
        running += a.newInfections[d];
        a.cum[d] = running;
      }
    }
  }
  const agePopulations = ages.length > 0 && ages.every((a) => a.pop > 0);
  if (!ages.length) {
    ageNote = 'This run published no age breakdown (daily_age has no rows).';
  }

  /* ---- travel ----
     Legacy shape is one `daily_travel` table. Real travel artifacts spread the
     same facts across daily_epidemic, daily_travel_population and
     daily_travel_route; prefer those real columns when they exist. */
  const legacyTravelRows = raw.daily_travel ?? [];
  const travelPopRows = raw.daily_travel_population ?? [];
  const travelRouteRows = raw.daily_travel_route ?? [];
  const epiHasVisitors = epiCols.has('active_visitors');
  const epiHasReturning = epiCols.has('returning_resident_travel_acquisitions');

  let travel: TravelSeries | null = null;
  if (legacyTravelRows.length || travelPopRows.length || travelRouteRows.length || epiHasVisitors) {
    const points: TravelPoint[] = Array.from({ length: dayCount }, () => ({
      arrivals: 0,
      activeVisitors: 0,
      visitorInfections: 0,
      residentInfections: 0,
      visitorToResident: 0,
      residentToVisitor: 0,
      travelLocalInfections: 0,
      returningAcquisitions: 0,
    }));
    let hasArrivals = false;
    let hasLegacyLinked = false;

    for (const r of legacyTravelRows) {
      const day = dayOf.get(str(r, 'date'));
      if (day == null) continue;
      const pt = points[day];
      pt.arrivals = num(r, 'arrivals', 'daily_arrivals');
      pt.activeVisitors = num(r, 'active_visitors', 'visitors_on_island');
      pt.visitorInfections = num(r, 'visitor_infections', 'visitor_linked_infections');
      pt.residentInfections = num(r, 'resident_infections');
      if (has(r, 'arrivals') || has(r, 'daily_arrivals')) hasArrivals = true;
      if (has(r, 'visitor_infections') || has(r, 'visitor_linked_infections')) hasLegacyLinked = true;
    }
    for (const r of travelPopRows) {
      const day = dayOf.get(str(r, 'date'));
      if (day == null) continue;
      points[day].arrivals = num(r, 'arrivals', 'daily_arrivals');
      points[day].activeVisitors = num(r, 'active_visitors', 'visitors_on_island');
      hasArrivals = true;
    }
    for (const r of travelRouteRows) {
      const day = dayOf.get(str(r, 'date'));
      if (day == null) continue;
      points[day].visitorToResident += num(r, 'visitor_to_resident');
      points[day].residentToVisitor += num(r, 'resident_to_visitor');
      points[day].travelLocalInfections += num(r, 'new_local_infections');
    }
    if (epiHasVisitors || epiHasReturning) {
      for (const r of epiRows) {
        const day = dayOf.get(str(r, 'date'));
        if (day == null) continue;
        if (epiHasVisitors) points[day].activeVisitors = num(r, 'active_visitors');
        if (epiHasReturning) {
          points[day].returningAcquisitions = num(r, 'returning_resident_travel_acquisitions');
        }
      }
    }

    const sources = [
      legacyTravelRows.length ? 'daily_travel' : '',
      travelPopRows.length ? 'daily_travel_population' : '',
      travelRouteRows.length ? 'daily_travel_route' : '',
      epiHasVisitors || epiHasReturning ? 'daily_epidemic' : '',
    ].filter(Boolean);

    travel = {
      points,
      hasArrivals,
      hasActiveVisitors: epiHasVisitors || travelPopRows.length > 0 || legacyTravelRows.length > 0,
      hasFlows: travelRouteRows.length > 0,
      hasReturning: epiHasReturning,
      hasLegacyLinked,
      source: sources.join(' · '),
    };
  }

  const availability: Availability = {
    detected: detectedAvailable,
    detectedSource,
    parish: parishAvailable,
    parishNote: parishAvailable ? null : 'Parish breakdown was not published by this run.',
    routes: routes.length > 0,
    routeSource,
    routeNote,
    ages: ages.length > 0,
    ageSource,
    ageNote,
    agePopulations,
  };

  const mapMetrics = parishAvailable
    ? MAP_METRICS.filter((m) => (m.id === 'detected' ? parishHasDetected : true))
    : [];

  const loadedNames = DATASETS.filter((n) => (raw[n]?.length ?? 0) > 0);

  return {
    job,
    dates,
    dayCount,
    startDate: dates[0] ?? '',
    population,
    seeds: seedCount(job),
    epi,
    parishes,
    routes,
    ages,
    travel,
    availability,
    mapMetrics,
    populationSource,
    datasetNames: loadedNames,
    raw,
  };
}

function prettyRouteName(id: string): string {
  const s = id.replace(/[_-]+/g, ' ').trim();
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : id;
}

/* ============================== derivations ============================== */

/** Per-1,000-resident value for the map, for one parish on one day. */
export function parishMetricPer1k(p: ParishSeries, day: number, metric: MapMetric): number {
  const pt = p.points[day];
  if (!pt) return 0;
  if (metric === 'attack') return pt.attack * 1000;
  const raw = metric === 'active' ? pt.active : metric === 'cum' ? pt.cum : metric === 'detected' ? pt.detected : pt.visitor;
  return p.pop ? (raw / p.pop) * 1000 : 0;
}

/** Run-wide maximum of a metric, so the bins never flicker during playback. */
export function metricMax(parishes: ParishSeries[], dayCount: number, metric: MapMetric): number {
  let m = 0;
  for (const p of parishes) {
    for (let d = 0; d < dayCount; d += 1) {
      const v = parishMetricPer1k(p, d, metric);
      if (v > m) m = v;
    }
  }
  return m;
}

export interface RouteCount {
  key: string;
  name: string;
  family: 'resident' | 'travel';
  count: number;
  share: number;
}

/** Route counts for the selected day, either cumulative or that day only. */
export function routeCounts(
  routes: RouteSeries[],
  day: number,
  win: 'cum' | 'day',
): RouteCount[] {
  const values = routes.map((r) => (win === 'cum' ? r.cumulative[day] ?? 0 : r.perDay[day] ?? 0));
  const total = values.reduce((a, b) => a + b, 0);
  return routes.map((r, i) => ({
    key: r.id,
    name: r.name,
    family: r.family,
    count: values[i],
    share: total ? values[i] / total : 0,
  }));
}

/** Cumulative < 0.1% of population at the end of the run. */
export interface Fizzle {
  cumulative: number;
  dieOutDay: number;
}

export function detectFizzle(data: ResultsData): Fizzle | null {
  if (!data.epi.length) return null;
  const last = data.epi[data.epi.length - 1];
  if (last.cum >= data.population * 0.001) return null;
  let dieOut = 0;
  for (let d = 0; d < data.epi.length; d += 1) {
    if (data.epi[d].active > 0) dieOut = d;
  }
  return { cumulative: Math.round(last.cum), dieOutDay: dieOut };
}

/* ============================== formatting ============================== */

export const fmt = (n: number): string => Math.round(n).toLocaleString('en-GB');

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function parseISO(iso: string): Date | null {
  if (!iso) return null;
  const dt = new Date(`${iso}T00:00:00Z`);
  return Number.isNaN(dt.getTime()) ? null : dt;
}

/** "9 Feb" / "Mon 9 Feb 2026". */
export function formatDate(iso: string, long = false): string {
  const dt = parseISO(iso);
  if (!dt) return iso;
  const day = dt.getUTCDate();
  const mo = MONTHS[dt.getUTCMonth()];
  if (!long) return `${day} ${mo}`;
  return `${WEEKDAYS[dt.getUTCDay()]} ${day} ${mo} ${dt.getUTCFullYear()}`;
}

/** "6 Jan 2026". */
export function formatDateYear(iso: string): string {
  const dt = parseISO(iso);
  if (!dt) return iso;
  return `${dt.getUTCDate()} ${MONTHS[dt.getUTCMonth()]} ${dt.getUTCFullYear()}`;
}

export function isoPlusDays(iso: string, days: number): string {
  const dt = parseISO(iso);
  if (!dt) return iso;
  dt.setUTCDate(dt.getUTCDate() + days);
  return dt.toISOString().slice(0, 10);
}

/** Short hash pair for the provenance strip: "a3f2c9…e41b". */
export function shortHash(hash: string | null | undefined): string {
  if (!hash) return '—';
  if (hash.length <= 12) return hash;
  return `${hash.slice(0, 6)}…${hash.slice(-4)}`;
}
