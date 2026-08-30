/**
 * Runs — the job list, plus an inline job monitor.
 *
 * Routing note: `src/app/routes.tsx` only declares `/runs` (adding a
 * `/runs/:jobId` child route would mean editing a file this agent does not
 * own), so the monitor is addressed with the search param `?job=<id>`.
 * Deep links, back/forward and refresh all work through the URL.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';
import { api, type JobState, type JobStatusResponse } from '../../api';
import { jobDisplayName, jobKindDetail } from '../../api/naming';
import { Btn, Card, KindChip, StateChip, useToast } from '../../components';
import { JobMonitor } from './JobMonitor';
import {
  durationLabel,
  interventionsLabel,
  isActive,
  populationLabel,
  resultsPath,
  stateNote,
} from './jobText';
import './runs.css';

const POLL_MS = 2_000;

type FilterId = 'all' | 'active' | 'succeeded' | 'failed';

const FILTERS: Array<{ id: FilterId; label: string }> = [
  { id: 'all', label: 'All' },
  { id: 'active', label: 'Active' },
  { id: 'succeeded', label: 'Succeeded' },
  { id: 'failed', label: 'Failed' },
];

/** The single-state filters map straight onto `listJobs({ state })`. */
const FILTER_STATE: Partial<Record<FilterId, JobState>> = {
  succeeded: 'SUCCEEDED',
  failed: 'FAILED',
};

export function RunsView() {
  const [params, setParams] = useSearchParams();
  const jobId = params.get('job');

  const closeMonitor = useCallback(() => {
    const next = new URLSearchParams(params);
    next.delete('job');
    setParams(next, { replace: false });
  }, [params, setParams]);

  return (
    <section className="view view-runs">
      {jobId ? (
        <JobMonitor jobId={jobId} onBack={closeMonitor} />
      ) : (
        <RunList
          onOpenMonitor={(id) => {
            const next = new URLSearchParams(params);
            next.set('job', id);
            setParams(next);
          }}
        />
      )}
    </section>
  );
}

function RunList({ onOpenMonitor }: { onOpenMonitor: (jobId: string) => void }) {
  const [filter, setFilter] = useState<FilterId>('all');
  const [jobs, setJobs] = useState<JobStatusResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [now, setNow] = useState(() => Date.now());
  const { showToast } = useToast();
  const navigate = useNavigate();
  const alive = useRef(true);
  /** Last seen state per job, for terminal-transition toasts. */
  const seen = useRef<Map<string, JobState>>(new Map());
  const primed = useRef(false);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  const announce = useCallback(
    (list: JobStatusResponse[]) => {
      const prev = seen.current;
      if (primed.current) {
        for (const job of list) {
          const before = prev.get(job.job_id);
          if (!before || !isActive(before) || isActive(job.state)) continue;
          if (job.state === 'SUCCEEDED') {
            showToast({
              title: `Run finished — ${jobDisplayName(job)}`,
              body:
                job.verification_status === 'passed'
                  ? 'Succeeded · all artifacts verified'
                  : 'Succeeded',
              tone: 'good',
              action: { label: 'Open results', fn: () => navigate(resultsPath(job)) },
            });
          } else if (job.state === 'FAILED') {
            showToast({
              title: `Run failed — ${jobDisplayName(job)}`,
              body: job.error?.message ?? 'The worker stopped before results were written.',
              tone: 'bad',
              action: { label: 'View error', fn: () => onOpenMonitor(job.job_id) },
            });
          }
        }
      }
      const next = new Map<string, JobState>();
      for (const job of list) next.set(job.job_id, job.state);
      seen.current = next;
      primed.current = true;
    },
    [navigate, onOpenMonitor, showToast],
  );

  const load = useCallback(async () => {
    try {
      const state = FILTER_STATE[filter];
      // "Active" spans three states and `listJobs` takes only one, so it is
      // filtered client-side from the unfiltered listing.
      const res = await api.listJobs({ limit: 100, ...(state ? { state } : {}) });
      if (!alive.current) return;
      setJobs(res.jobs);
      setError(null);
      announce(res.jobs);
    } catch (e) {
      if (!alive.current) return;
      setError(e instanceof Error ? e.message : 'Could not reach the job API.');
    } finally {
      if (alive.current) setLoaded(true);
    }
  }, [announce, filter]);

  useEffect(() => {
    void load();
  }, [load]);

  const visible = useMemo(
    () => (filter === 'active' ? jobs.filter((j) => isActive(j.state)) : jobs),
    [filter, jobs],
  );

  const anyActive = useMemo(() => jobs.some((j) => isActive(j.state)), [jobs]);

  // Poll only while something can still change.
  useEffect(() => {
    if (!anyActive) return undefined;
    const poll = window.setInterval(() => void load(), POLL_MS);
    const tick = window.setInterval(() => setNow(Date.now()), 1_000);
    return () => {
      window.clearInterval(poll);
      window.clearInterval(tick);
    };
  }, [anyActive, load]);

  // Queue positions are derived here: M9 exposes no queue-position field.
  const queuePosition = useMemo(() => {
    const map = new Map<string, number>();
    jobs
      .filter((j) => j.state === 'QUEUED')
      .slice()
      .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
      .forEach((j, i) => map.set(j.job_id, i + 1));
    return map;
  }, [jobs]);

  const cancel = useCallback(
    async (job: JobStatusResponse) => {
      try {
        await api.cancelJob(job.job_id);
        showToast({
          title: `Cancellation requested — ${jobDisplayName(job)}`,
          body: 'The worker stops at its next checkpoint. No partial results are published.',
          tone: 'neutral',
        });
      } catch (e) {
        showToast({
          title: 'Could not cancel this run',
          body: e instanceof Error ? e.message : 'The API rejected the cancel request.',
          tone: 'bad',
        });
      }
      await load();
    },
    [load, showToast],
  );

  return (
    <div className="wrap">
      <h1>Runs</h1>
      <div className="sub">
        Jobs run locally and survive restarts. Results stay verified against their scenario.
      </div>
      <div className="filterbar" role="group" aria-label="Filter runs">
        {FILTERS.map((f) => (
          <button
            key={f.id}
            type="button"
            className="fchip"
            aria-pressed={filter === f.id}
            onClick={() => setFilter(f.id)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && <div className="runs-note bad">{error}</div>}

      <Card>
        {visible.length === 0 ? (
          <div className="runs-empty">
            {!loaded
              ? 'Loading runs…'
              : filter === 'all'
                ? 'No runs yet. Build a scenario and submit it — it will appear here.'
                : 'No runs match this filter.'}
          </div>
        ) : (
          visible.map((job) => (
            <RunRow
              key={job.job_id}
              job={job}
              now={now}
              queuePosition={queuePosition.get(job.job_id)}
              onOpenMonitor={onOpenMonitor}
              onCancel={cancel}
            />
          ))
        )}
      </Card>
    </div>
  );
}

function RunRow({
  job,
  now,
  queuePosition,
  onOpenMonitor,
  onCancel,
}: {
  job: JobStatusResponse;
  now: number;
  queuePosition?: number;
  onOpenMonitor: (jobId: string) => void;
  onCancel: (job: JobStatusResponse) => void | Promise<void>;
}) {
  const active = isActive(job.state);
  return (
    <div className="run-row">
      <div className="t">
        <StateChip state={job.state} />
        <span className="nm">{jobDisplayName(job)}</span>
        <KindChip kind={job.kind} detail={jobKindDetail(job)} />
      </div>
      <div className="acts">
        {job.state === 'SUCCEEDED' && (
          <Btn variant="primary" to={resultsPath(job)}>
            {job.kind === 'scenario_compare' ? 'Open comparison' : 'Open results'}
          </Btn>
        )}
        {active && (
          <Btn onClick={() => onOpenMonitor(job.job_id)}>View status</Btn>
        )}
        {job.state === 'FAILED' && (
          <Btn onClick={() => onOpenMonitor(job.job_id)}>View error</Btn>
        )}
        {(job.state === 'QUEUED' || job.state === 'RUNNING') && (
          <Btn variant="danger" onClick={() => void onCancel(job)}>
            Cancel
          </Btn>
        )}
        {job.state === 'CANCEL_REQUESTED' && (
          <Btn disabled title="Cancellation already requested">
            Cancelling…
          </Btn>
        )}
        {job.state === 'INTERRUPTED' ? (
          <Btn to="/simulate">Re-run scenario</Btn>
        ) : job.state === 'FAILED' ? (
          <Btn to="/simulate">Duplicate &amp; edit</Btn>
        ) : !active ? (
          <Btn to="/simulate">Duplicate</Btn>
        ) : null}
      </div>
      <div className="meta">
        <span>{populationLabel(job)}</span>
        <span>{durationLabel(job)}</span>
        <span>{interventionsLabel(job)}</span>
        <span>{stateNote(job, now, queuePosition)}</span>
      </div>
    </div>
  );
}
