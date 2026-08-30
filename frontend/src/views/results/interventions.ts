/**
 * Intervention timeline derived from the *job's own request*.
 *
 * The M9 contract carries no intervention artifact table, so the strip and the
 * Gantt read the scenario the run was submitted with. Calendar interventions
 * have their dates converted to day offsets against the run start; detection-
 * triggered ones cannot have a real start day (it depends on the stochastic
 * detection time), so they are drawn hatched from day 0 plus their declared
 * start delay and labelled as triggered.
 */

import type { JobStatusResponse, JsonObject } from '../../api';
import { isoPlusDays } from './data';

export interface InterventionBar {
  id: string;
  name: string;
  family: string;
  color: string;
  from: number;
  to: number;
  /** Detection-triggered: hatched texture, not a calendar window. */
  triggered: boolean;
  /** Tooltip / Gantt caption. */
  detail: string;
}

const FAMILY_TOKEN: Record<string, string> = {
  school_closure: 'school',
  case_isolation: 'isolation',
  household_quarantine: 'quarantine',
  work_from_home: 'wfh',
  community_reduction: 'community',
  care_home_protection: 'care',
  vaccination: 'vacc',
  travel_measure: 'travel',
};

const FAMILY_LABEL: Record<string, string> = {
  school_closure: 'School closure',
  case_isolation: 'Case isolation',
  household_quarantine: 'Household quarantine',
  work_from_home: 'Working from home',
  community_reduction: 'Community reduction',
  care_home_protection: 'Care-home protection',
  vaccination: 'Vaccination rollout',
  travel_measure: 'Travel measure',
};

const FALLBACK_COLORS = [
  'var(--iv-school)',
  'var(--iv-isolation)',
  'var(--iv-wfh)',
  'var(--iv-vacc)',
  'var(--iv-community)',
  'var(--iv-care)',
  'var(--iv-quarantine)',
  'var(--iv-travel)',
];

function titleize(raw: string): string {
  const s = raw.replace(/[_-]+/g, ' ').trim();
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}

function asRecord(value: unknown): JsonObject | null {
  return value && typeof value === 'object' && !Array.isArray(value) ? (value as JsonObject) : null;
}

function pickNumber(obj: JsonObject, ...keys: string[]): number | null {
  for (const k of keys) {
    const v = obj[k];
    if (typeof v === 'number' && Number.isFinite(v)) return v;
    if (typeof v === 'string' && v !== '' && Number.isFinite(Number(v))) return Number(v);
  }
  return null;
}

function pickString(obj: JsonObject, ...keys: string[]): string | null {
  for (const k of keys) {
    const v = obj[k];
    if (typeof v === 'string' && v) return v;
  }
  return null;
}

function scenarioOf(job: JobStatusResponse): JsonObject | null {
  const req = job.request as JsonObject;
  return asRecord(req.scenario) ?? asRecord(req.treated) ?? asRecord(req.baseline);
}

/** Day offset of an ISO date from the run start (clamped into the run). */
function dayOffset(startDate: string, iso: string, dayCount: number): number | null {
  if (!startDate || !iso) return null;
  const start = Date.parse(`${startDate}T00:00:00Z`);
  const at = Date.parse(`${iso}T00:00:00Z`);
  if (Number.isNaN(start) || Number.isNaN(at)) return null;
  const off = Math.round((at - start) / 86_400_000);
  return Math.max(0, Math.min(dayCount - 1, off));
}

/**
 * Reads `scenario.interventions` (list, or a mapping of id → config) and turns
 * each entry into a bar. Unknown shapes degrade to a whole-run bar rather than
 * inventing dates.
 */
export function deriveInterventions(
  job: JobStatusResponse,
  startDate: string,
  dayCount: number,
): InterventionBar[] {
  const scenario = scenarioOf(job);
  if (!scenario) return [];
  const rawList = scenario.interventions;
  let entries: JsonObject[] = [];
  if (Array.isArray(rawList)) {
    entries = rawList.map(asRecord).filter((x): x is JsonObject => x !== null);
  } else {
    const asMap = asRecord(rawList);
    if (asMap) {
      entries = Object.entries(asMap)
        .map(([k, v]) => {
          const rec = asRecord(v);
          return rec ? ({ id: k, ...rec } as JsonObject) : null;
        })
        .filter((x): x is JsonObject => x !== null);
    }
  }
  if (!entries.length) return [];

  const last = dayCount - 1;
  return entries.map((entry, i) => {
    const family = pickString(entry, 'family', 'type', 'kind', 'intervention_family') ?? '';
    const id = pickString(entry, 'id', 'intervention_id', 'name') ?? `intervention_${i + 1}`;
    const name =
      pickString(entry, 'label', 'display_name') ??
      FAMILY_LABEL[family] ??
      titleize(id);
    const token = FAMILY_TOKEN[family];
    const color = token ? `var(--iv-${token})` : FALLBACK_COLORS[i % FALLBACK_COLORS.length];

    const trigger = (pickString(entry, 'trigger', 'activation', 'release_rule') ?? '').toLowerCase();
    const triggeredFlag = entry.detection_triggered === true || trigger.includes('detect');
    const startDelay = pickNumber(entry, 'start_delay_days', 'delay_days') ?? 0;

    const startIso = pickString(entry, 'start_date', 'start');
    const endIso = pickString(entry, 'end_date', 'end');
    const startDay = pickNumber(entry, 'start_day', 'day');
    const duration = pickNumber(entry, 'duration_days', 'duration');

    let from: number;
    let to: number;
    if (triggeredFlag) {
      from = Math.max(0, Math.min(last, Math.round(startDelay)));
      to = last;
    } else {
      const resolvedStart =
        (startIso ? dayOffset(startDate, startIso, dayCount) : null) ??
        (startDay != null ? Math.max(0, Math.min(last, Math.round(startDay))) : 0);
      const resolvedEnd =
        (endIso ? dayOffset(startDate, endIso, dayCount) : null) ??
        (duration != null ? Math.min(last, resolvedStart + Math.round(duration)) : last);
      from = resolvedStart;
      to = Math.max(from, resolvedEnd);
    }

    const detailParts: string[] = [];
    if (triggeredFlag) {
      detailParts.push(
        startDelay
          ? `detection-triggered · ${startDelay}-day start delay`
          : 'detection-triggered',
      );
    } else {
      detailParts.push(
        `${formatDayLabel(startDate, from)} → ${formatDayLabel(startDate, to)}`,
      );
    }
    if (family) detailParts.push(family);

    return {
      id: `${id}-${i}`,
      name: triggeredFlag ? `${name} (triggered)` : name,
      family: family || 'intervention',
      color,
      from,
      to,
      triggered: triggeredFlag,
      detail: detailParts.join(' · '),
    };
  });
}

function formatDayLabel(startDate: string, day: number): string {
  const iso = isoPlusDays(startDate, day);
  return `day ${day} (${iso})`;
}
