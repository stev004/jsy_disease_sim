/**
 * Presentation helpers for jobs.
 *
 * The M9 API has no "scenario name" field, so a display name is derived from
 * the canonical request (`ensemble_id` / `comparison_id`) and falls back to the
 * job kind plus a short id.
 */

import type { JobStatusResponse, JsonObject } from './types';

const KIND_NOUN: Record<JobStatusResponse['kind'], string> = {
  scenario_run: 'Scenario run',
  scenario_compare: 'Comparison',
  ensemble: 'Ensemble',
};

function titleize(raw: string): string {
  const s = raw.replace(/[-_]+/g, ' ').trim();
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}

function scenarioId(value: unknown): string | undefined {
  if (value && typeof value === 'object') {
    const id = (value as JsonObject).scenario_id;
    if (typeof id === 'string' && id.trim()) return id;
  }
  return undefined;
}

/**
 * Best available name, in order: the scenario's own `scenario_id`, then the
 * ensemble/comparison id, then the job kind plus a short id. The M9 contract
 * has no free-text scenario name field.
 */
export function jobDisplayName(job: JobStatusResponse): string {
  const req = job.request as JsonObject;
  const fromScenario = scenarioId(req.scenario) ?? scenarioId(req.treated);
  if (fromScenario) return titleize(fromScenario);
  const id = req.ensemble_id ?? req.comparison_id;
  if (typeof id === 'string' && id.trim()) return titleize(id);
  return `${KIND_NOUN[job.kind]} ${job.job_id.slice(0, 8)}`;
}

/** e.g. "5 seeds" for the kind chip. */
export function jobKindDetail(job: JobStatusResponse): string | undefined {
  const seeds = (job.request as JsonObject).replicate_seeds;
  if (Array.isArray(seeds)) return `${seeds.length} seed${seeds.length === 1 ? '' : 's'}`;
  return undefined;
}

export function jobDurationDays(job: JobStatusResponse): number | undefined {
  const d = (job.request as JsonObject).duration_days;
  return typeof d === 'number' ? d : undefined;
}

export function jobPopulationLabel(job: JobStatusResponse): string {
  const mode = (job.request as JsonObject).mode;
  if (mode === 'full') return 'Full Jersey';
  if (mode === 'scaled') return 'Scaled';
  if (mode === 'ci') return 'Quick test';
  return typeof mode === 'string' ? titleize(mode) : 'Jersey';
}

/** "today 09:12" / "yesterday 16:20" / "Tue 22:31" / "12 Feb 09:12". */
export function formatWhen(iso: string | null | undefined): string {
  if (!iso) return '';
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) return '';
  const time = dt.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
  const today = new Date();
  const dayDiff = Math.floor(
    (new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime() -
      new Date(dt.getFullYear(), dt.getMonth(), dt.getDate()).getTime()) /
      86_400_000,
  );
  if (dayDiff === 0) return `today ${time}`;
  if (dayDiff === 1) return `yesterday ${time}`;
  if (dayDiff > 1 && dayDiff < 7) {
    return `${dt.toLocaleDateString('en-GB', { weekday: 'short' })} ${time}`;
  }
  return `${dt.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })} ${time}`;
}

/** Compact meta line: "Full Jersey · 60 days · Ensemble ×5 · today 09:12". */
export function jobMetaLine(job: JobStatusResponse): string {
  const parts: string[] = [jobPopulationLabel(job)];
  const days = jobDurationDays(job);
  if (days) parts.push(`${days} days`);
  const seeds = (job.request as JsonObject).replicate_seeds;
  if (Array.isArray(seeds)) parts.push(`${KIND_NOUN[job.kind].toLowerCase()} ×${seeds.length}`);
  else parts.push(KIND_NOUN[job.kind].toLowerCase());
  const when = formatWhen(job.finished_at ?? job.created_at);
  if (when) parts.push(when);
  return parts.join(' · ');
}
