/**
 * Runs-view text helpers.
 *
 * Everything here derives display copy from the M9 `JobStatusResponse` only —
 * the API has no progress fraction, no queue position field and no worker-log
 * endpoint, so the wording below never claims more than the contract provides.
 */

import type { JobPhase, JobState, JobStatusResponse, JsonObject } from '../../api';
import { JOB_PHASES } from '../../api';
import { formatWhen, jobDurationDays, jobPopulationLabel } from '../../api/naming';

export const ACTIVE_STATES: JobState[] = ['QUEUED', 'RUNNING', 'CANCEL_REQUESTED'];

export function isActive(state: JobState): boolean {
  return ACTIVE_STATES.includes(state);
}

/** Plain-language checklist lines (docs/m10_ui_design.md §9). */
export const PHASE_LINES: Record<string, { nm: string; desc: string }> = {
  queued: {
    nm: 'Queued',
    desc: 'Waiting for the scheduler — one scientific job runs at a time',
  },
  validating: {
    nm: 'Validating scenario',
    desc: 'Typed scenario checks, no epidemic run',
  },
  preparing: {
    nm: 'Building Jersey population & contact networks',
    desc: 'Deterministic M2–M4 reconstruction — the long part',
  },
  running: {
    nm: 'Running outbreak',
    desc: 'Daily transmission across the synthetic population',
  },
  writing_artifacts: {
    nm: 'Writing results',
    desc: 'Tidy daily epidemic, parish, route, age & event tables',
  },
  verifying: {
    nm: 'Verifying results',
    desc: 'Independent content hashing of every artifact',
  },
  finalizing: {
    nm: 'Finalizing',
    desc: 'Strict reread — only verified results are published',
  },
};

/** Index into JOB_PHASES of the phase currently reached (or -1). */
export function phaseIndex(phase: JobPhase): number {
  return JOB_PHASES.indexOf(phase);
}

/**
 * Where the checklist cursor sits, and whether that row is a failure marker.
 * Terminal phases (`complete`/`failed`/`cancelled`/`interrupted`) are not in
 * JOB_PHASES, so they are mapped explicitly.
 */
export function checklistCursor(job: JobStatusResponse): { current: number; failed: boolean } {
  if (job.state === 'SUCCEEDED' || job.phase === 'complete') {
    return { current: JOB_PHASES.length, failed: false };
  }
  if (job.state === 'FAILED' || job.phase === 'failed') {
    return { current: failedPhaseIndex(job), failed: true };
  }
  const idx = phaseIndex(job.phase);
  if (idx >= 0) return { current: idx, failed: false };
  // cancelled / interrupted: fall back to the failure phase recorded in error
  // details when present, otherwise the start of the checklist.
  return { current: Math.max(0, failedPhaseIndex(job)), failed: false };
}

/** Phase the worker died in, from `error.details.phase` when the API supplies it. */
export function failedPhaseIndex(job: JobStatusResponse): number {
  const details = job.error?.details as JsonObject | null | undefined;
  const p = details?.phase;
  if (typeof p === 'string') {
    const i = JOB_PHASES.indexOf(p as JobPhase);
    if (i >= 0) return i;
  }
  const own = phaseIndex(job.phase);
  return own >= 0 ? own : JOB_PHASES.indexOf('running');
}

export function failedPhaseName(job: JobStatusResponse): string {
  return JOB_PHASES[failedPhaseIndex(job)] ?? 'running';
}

/** "06:18" / "1:04:22" — clock-style elapsed. */
export function formatElapsed(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const mm = String(m).padStart(2, '0');
  const ss = String(s).padStart(2, '0');
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

/** "9m 41s" / "1h 04m" — prose-style run duration. */
export function formatDuration(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  if (h > 0) return `${h}h ${String(m).padStart(2, '0')}m`;
  if (m > 0) return `${m}m ${String(s).padStart(2, '0')}s`;
  return `${s}s`;
}

function timeOfDay(iso: string | null | undefined): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
}

function millisBetween(a?: string | null, b?: string | null): number | null {
  if (!a || !b) return null;
  const ta = new Date(a).getTime();
  const tb = new Date(b).getTime();
  if (Number.isNaN(ta) || Number.isNaN(tb)) return null;
  return tb - ta;
}

/** Wall-clock runtime, or elapsed-so-far for a running job. */
export function runtimeMs(job: JobStatusResponse, now: number): number | null {
  if (!job.started_at) return null;
  const start = new Date(job.started_at).getTime();
  if (Number.isNaN(start)) return null;
  if (job.finished_at) return millisBetween(job.started_at, job.finished_at);
  return now - start;
}

function interventionsOf(request: JsonObject): unknown[] | null {
  for (const key of ['scenario', 'treated'] as const) {
    const block = request[key];
    if (block && typeof block === 'object') {
      const iv = (block as JsonObject).interventions;
      if (Array.isArray(iv)) return iv;
    }
  }
  return null;
}

/** "3 interventions" / "vs baseline · matched ×5" for comparisons. */
export function interventionsLabel(job: JobStatusResponse): string {
  const req = job.request as JsonObject;
  if (job.kind === 'scenario_compare') {
    const seeds = req.replicate_seeds;
    const n = Array.isArray(seeds) ? seeds.length : 1;
    return `vs baseline · matched ×${n}`;
  }
  const iv = interventionsOf(req);
  if (iv === null) return 'interventions not listed';
  return `${iv.length} intervention${iv.length === 1 ? '' : 's'}`;
}

export function durationLabel(job: JobStatusResponse): string {
  const d = jobDurationDays(job);
  return d ? `${d} days` : 'duration not stated';
}

export function populationLabel(job: JobStatusResponse): string {
  return jobPopulationLabel(job);
}

/**
 * The honest, state-specific trailing note of a run row.
 * `queuePosition` is derived locally by ordering the QUEUED jobs — M9 exposes
 * no queue-position field.
 */
export function stateNote(
  job: JobStatusResponse,
  now: number,
  queuePosition?: number,
): string {
  const created = formatWhen(job.created_at);
  switch (job.state) {
    case 'QUEUED': {
      const pos = queuePosition ?? 1;
      return `position ${pos} in queue — one job runs at a time`;
    }
    case 'RUNNING': {
      const ms = runtimeMs(job, now);
      const started = timeOfDay(job.started_at);
      const bits = [
        started ? `started ${started}` : `submitted ${created}`,
        ms === null ? null : `${formatElapsed(ms)} elapsed`,
        `phase: ${job.phase}`,
      ].filter(Boolean);
      return bits.join(' · ');
    }
    case 'CANCEL_REQUESTED': {
      const ms = runtimeMs(job, now);
      return [
        'cancel requested — waiting for the worker to stop',
        ms === null ? null : `${formatElapsed(ms)} elapsed`,
      ]
        .filter(Boolean)
        .join(' · ');
    }
    case 'SUCCEEDED': {
      const ms = runtimeMs(job, now);
      const bits = [
        formatWhen(job.finished_at ?? job.created_at),
        ms === null ? null : `ran ${formatDuration(ms)}`,
        job.verification_status === 'passed' ? 'verified ✓' : null,
      ].filter(Boolean);
      return bits.join(' · ');
    }
    case 'FAILED':
      return [
        formatWhen(job.finished_at ?? job.created_at),
        `failed during ${failedPhaseName(job)}`,
      ].join(' · ');
    case 'CANCELLED': {
      const ms = runtimeMs(job, now);
      const at = ms === null ? null : `cancelled by you at ${formatElapsed(ms)}`;
      return [formatWhen(job.finished_at ?? job.created_at), at ?? 'cancelled by you']
        .filter(Boolean)
        .join(' · ');
    }
    case 'INTERRUPTED':
      return [
        formatWhen(job.finished_at ?? job.started_at ?? job.created_at),
        'the server stopped mid-run; it is never silently re-run',
      ]
        .filter(Boolean)
        .join(' · ');
    default:
      return created;
  }
}

/** Where a succeeded job's results live. */
export function resultsPath(job: JobStatusResponse): string {
  return job.kind === 'scenario_compare' ? `/compare/${job.job_id}` : `/results/${job.job_id}`;
}

export function shortHash(hash: string | null | undefined): string {
  if (!hash) return '';
  const h = hash.replace(/^mock-/, '');
  return h.length > 14 ? `${h.slice(0, 6)}…${h.slice(-4)}` : h;
}
