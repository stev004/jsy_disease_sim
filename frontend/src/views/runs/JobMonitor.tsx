/**
 * Job monitor — one job, rendered as the mockup's `.job-card`.
 *
 * Polls `GET /jobs/{id}` every 2 s while the job is active and stops at a
 * terminal state. No percentage is shown anywhere: M9's `progress_fraction`
 * is always null, and the honesty footer says so.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { api, JOB_PHASES, type JobStatusResponse } from '../../api';
import { jobDisplayName, jobKindDetail } from '../../api/naming';
import { Btn, Card, KindChip, StateChip, useToast } from '../../components';
import { useScenarioContextEffect } from '../../app/ScenarioContextProvider';
import {
  PHASE_LINES,
  checklistCursor,
  failedPhaseName,
  formatElapsed,
  durationLabel,
  interventionsLabel,
  isActive,
  populationLabel,
  resultsPath,
  runtimeMs,
  shortHash,
} from './jobText';

const POLL_MS = 2_000;

export function JobMonitor({ jobId, onBack }: { jobId: string; onBack: () => void }) {
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [cancelling, setCancelling] = useState(false);
  const { showToast } = useToast();
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  const load = useCallback(async () => {
    try {
      const next = await api.getJob(jobId);
      if (!alive.current) return;
      setJob(next);
      setError(null);
    } catch (e) {
      if (!alive.current) return;
      setError(e instanceof Error ? e.message : 'Could not read this job from the API.');
    }
  }, [jobId]);

  useEffect(() => {
    setJob(null);
    void load();
  }, [load]);

  const active = job ? isActive(job.state) : false;

  // Poll only while the job can still change.
  useEffect(() => {
    if (!active) return undefined;
    const id = window.setInterval(() => void load(), POLL_MS);
    return () => window.clearInterval(id);
  }, [active, load]);

  // Elapsed ticks once a second while running.
  useEffect(() => {
    if (!active) return undefined;
    const id = window.setInterval(() => setNow(Date.now()), 1_000);
    return () => window.clearInterval(id);
  }, [active]);

  useScenarioContextEffect(
    job
      ? {
          name: jobDisplayName(job),
          kind: job.kind,
          kindDetail: jobKindDetail(job),
          state: job.state,
          jobId: job.job_id,
        }
      : null,
  );

  const cancel = useCallback(async () => {
    if (!job) return;
    setCancelling(true);
    try {
      await api.cancelJob(job.job_id);
      showToast({
        title: 'Cancellation requested',
        body: 'The worker stops at its next checkpoint. No partial results are published.',
        tone: 'neutral',
      });
      await load();
    } catch (e) {
      showToast({
        title: 'Could not cancel this run',
        body: e instanceof Error ? e.message : 'The API rejected the cancel request.',
        tone: 'bad',
      });
    } finally {
      if (alive.current) setCancelling(false);
    }
  }, [job, load, showToast]);

  if (!job) {
    return (
      <div className="wrap">
        <BackLink onBack={onBack} />
        <Card className="job-card">
          <div className="job-sub">{error ?? 'Loading run…'}</div>
        </Card>
      </div>
    );
  }

  const { current, failed } = checklistCursor(job);
  const elapsed = runtimeMs(job, now);
  const cancellable = job.state === 'QUEUED' || job.state === 'RUNNING';
  const succeeded = job.state === 'SUCCEEDED';
  const isFailed = job.state === 'FAILED';

  const sciBits = [
    job.request_hash ? `request ${shortHash(job.request_hash)}` : null,
    job.worker_pid ? `worker pid ${job.worker_pid}` : null,
    job.engine_git_commit
      ? `engine ${job.engine_git_commit}${job.dirty_worktree_flag ? ' (dirty)' : ' (clean)'}`
      : null,
  ].filter(Boolean);

  return (
    <div className="wrap runs-monitor">
      <BackLink onBack={onBack} />
      <Card className="job-card">
        <div className="top">
          <h1>{jobDisplayName(job)}</h1>
          <StateChip state={job.state} />
        </div>
        <div className="job-sub">
          <KindChip kind={job.kind} detail={jobKindDetail(job)} />{' '}
          {populationLabel(job)} · {durationLabel(job)} · {interventionsLabel(job)}
          {elapsed !== null && (
            <>
              {' '}
              ·{' '}
              <span className="mono num">{formatElapsed(elapsed)}</span>{' '}
              {job.finished_at ? 'total' : 'elapsed'}
            </>
          )}
        </div>
        {sciBits.length > 0 && (
          <div className="sci-only sci-note" style={{ marginTop: 6 }}>
            {sciBits.join(' · ')}
          </div>
        )}

        <div className="phases">
          {JOB_PHASES.map((phase, i) => {
            const line = PHASE_LINES[phase];
            const isDone = i < current;
            const isNow = i === current && !failed;
            const isBad = failed && i === current;
            const cls = isDone ? 'done' : isNow ? 'now' : 'todo';
            return (
              <div className={`phase ${cls}`} key={phase}>
                <span
                  className="ico"
                  style={isBad ? { background: 'var(--bad-soft)', color: 'var(--bad)' } : undefined}
                >
                  {isBad ? '✕' : isDone ? '✓' : isNow ? <span className="pulse" /> : ''}
                </span>
                <span>
                  <span className="nm">{line.nm}</span>
                  <br />
                  <span className="t">{line.desc}</span>
                </span>
                <span className="t num">{isDone ? 'done' : ''}</span>
              </div>
            );
          })}
        </div>

        {isFailed && (
          <div className="job-err" style={{ display: 'block' }}>
            <b>
              {failedPhaseName(job) ? (
                <>The run failed during <span className="mono">{failedPhaseName(job)}</span>.</>
              ) : (
                'Run failed.'
              )}
            </b>
            <span className="mono">
              {job.error?.message ?? 'The API reported a failure without a message.'}
            </span>
            <div style={{ marginTop: 10, display: 'flex', gap: 8 }}>
              <Btn
                style={{ fontSize: 12 }}
                disabled
                title="Log retrieval needs API support"
              >
                View worker log
              </Btn>
              <Btn to="/simulate" style={{ fontSize: 12 }}>
                New scenario
              </Btn>
            </div>
          </div>
        )}

        {job.state === 'INTERRUPTED' && (
          <div className="runs-note">
            The server stopped mid-run; it is never silently re-run. Re-submit the scenario when
            you want it again.
          </div>
        )}
        {job.state === 'CANCELLED' && (
          <div className="runs-note">Cancelled by you. No results were written.</div>
        )}
        {error && <div className="runs-note bad">{error}</div>}

        <div className="job-foot">
          <span className="job-honesty">
            Phases are real checkpoints from the engine — it does not report a percentage, so none
            is shown.
          </span>
          <span style={{ display: 'flex', gap: 8 }}>
            {cancellable && (
              <Btn variant="danger" onClick={() => void cancel()} disabled={cancelling}>
                Cancel run
              </Btn>
            )}
            {succeeded && (
              <Btn variant="primary" to={resultsPath(job)}>
                {job.kind === 'scenario_compare' ? 'Open comparison' : 'Open results'}
              </Btn>
            )}
            {(job.state === 'CANCELLED' || job.state === 'INTERRUPTED') && (
              <Btn to="/simulate">Re-run scenario</Btn>
            )}
          </span>
        </div>
      </Card>
    </div>
  );
}

function BackLink({ onBack }: { onBack: () => void }) {
  return (
    <button type="button" className="runs-back" onClick={onBack}>
      ← All runs
    </button>
  );
}
