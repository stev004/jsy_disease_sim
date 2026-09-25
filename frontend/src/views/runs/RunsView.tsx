/**
 * Runs & evidence — live job phases, recent jobs and the provenance published
 * for the selected job. Selection is kept in `?job=<id>` for deep links.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { API_SCHEMA_VERSION, API_VERSION, api, JOB_PHASES, type APIArtifact, type JobState, type JobStatusResponse } from '../../api';
import { jobDisplayName, jobKindDetail } from '../../api/naming';
import { Btn, Card, KindChip, Seg, StateChip, useToast } from '../../components';
import { ProvenanceChain } from '../../components/ProvenanceChain';
import { validation } from '../../content/validation';
import { useScenarioContextEffect } from '../../app/ScenarioContextProvider';
import {
  checklistCursor,
  durationLabel,
  failedPhaseName,
  formatElapsed,
  interventionsLabel,
  isActive,
  PHASE_LINES,
  populationLabel,
  resultsPath,
  runtimeMs,
  stateNote,
} from './jobText';
import './runs.css';

const POLL_MS = 2_000;

type FilterId = 'all' | 'active' | 'succeeded' | 'failed';

const FILTERS: Array<{ value: FilterId; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'active', label: 'Active' },
  { value: 'succeeded', label: 'Succeeded' },
  { value: 'failed', label: 'Failed' },
];

const PHASE_HONESTY_NOTE =
  'Phases are real checkpoints from the engine — it does not report a percentage, so none is shown.';

export function RunsView() {
  const [params, setParams] = useSearchParams();
  const selectedId = params.get('job');
  const [filter, setFilter] = useState<FilterId>('all');
  const [jobs, setJobs] = useState<JobStatusResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectionError, setSelectionError] = useState<string | null>(null);
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

  const selectJob = useCallback(
    (id: string) => {
      const next = new URLSearchParams(params);
      next.set('job', id);
      setParams(next);
    },
    [params, setParams],
  );

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
              action: { label: 'View error', fn: () => selectJob(job.job_id) },
            });
          }
        }
      }
      const next = new Map<string, JobState>();
      for (const job of list) next.set(job.job_id, job.state);
      seen.current = next;
      primed.current = true;
    },
    [navigate, selectJob, showToast],
  );

  const load = useCallback(async () => {
    try {
      const res = await api.listJobs({ limit: 100 });
      let list = res.jobs;
      if (selectedId && !list.some((job) => job.job_id === selectedId)) {
        try {
          const selected = await api.getJob(selectedId);
          list = [...list, selected];
          if (alive.current) setSelectionError(null);
        } catch (e) {
          if (alive.current) {
            setSelectionError(e instanceof Error ? e.message : 'Could not read the selected run.');
          }
        }
      } else if (alive.current) {
        setSelectionError(null);
      }
      if (!alive.current) return;
      setJobs(list);
      setError(null);
      announce(list);
    } catch (e) {
      if (!alive.current) return;
      setError(e instanceof Error ? e.message : 'Could not reach the job API.');
    } finally {
      if (alive.current) setLoaded(true);
    }
  }, [announce, selectedId]);

  useEffect(() => {
    void load();
  }, [load]);

  const newestFirst = useMemo(
    () =>
      jobs
        .slice()
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()),
    [jobs],
  );
  const visible = useMemo(() => {
    if (filter === 'active') return newestFirst.filter((job) => isActive(job.state));
    if (filter === 'succeeded' || filter === 'failed') {
      const state = filter === 'succeeded' ? 'SUCCEEDED' : 'FAILED';
      return newestFirst.filter((job) => job.state === state);
    }
    return newestFirst;
  }, [filter, newestFirst]);
  const activeJobs = useMemo(() => newestFirst.filter((job) => isActive(job.state)), [newestFirst]);
  const anyActive = activeJobs.length > 0;
  const selectedJob = selectedId
    ? newestFirst.find((job) => job.job_id === selectedId) ?? null
    : activeJobs[0] ?? newestFirst[0] ?? null;

  useScenarioContextEffect(
    selectedJob
      ? {
          name: jobDisplayName(selectedJob),
          kind: selectedJob.kind,
          kindDetail: jobKindDetail(selectedJob),
          state: selectedJob.state,
          jobId: selectedJob.job_id,
        }
      : null,
  );

  // Poll every two seconds while any listed job can still change.
  useEffect(() => {
    if (!anyActive) return undefined;
    const poll = window.setInterval(() => void load(), POLL_MS);
    const tick = window.setInterval(() => setNow(Date.now()), 1_000);
    return () => {
      window.clearInterval(poll);
      window.clearInterval(tick);
    };
  }, [anyActive, load]);

  const queuePosition = useMemo(() => {
    const map = new Map<string, number>();
    newestFirst
      .filter((job) => job.state === 'QUEUED')
      .slice()
      .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
      .forEach((job, i) => map.set(job.job_id, i + 1));
    return map;
  }, [newestFirst]);

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

  const closeSelection = useCallback(() => {
    const next = new URLSearchParams(params);
    next.delete('job');
    setParams(next, { replace: false });
  }, [params, setParams]);

  return (
    <section className="view view-runs">
      <div className="runs-page">
        <header className="runs-heading">
          <span className="runs-eyebrow">RUNS · PROVENANCE · VALIDATION</span>
          <h1>Runs &amp; evidence</h1>
          <p>Job checkpoints, published provenance and hand-maintained model validation.</p>
        </header>

        <div className="runs-left-column">
          <LiveJobPanel
            job={selectedJob}
            now={now}
            queuePosition={selectedJob ? queuePosition.get(selectedJob.job_id) : undefined}
            error={selectedId ? selectionError : error}
            onCancel={cancel}
            onClear={selectedId ? closeSelection : undefined}
          />
          <section className="runs-recent" aria-labelledby="recent-runs-title">
            <div className="runs-section-head">
              <div>
                <span className="runs-eyebrow">HISTORY</span>
                <h2 id="recent-runs-title">Recent runs</h2>
              </div>
              <span className="runs-count mono">{visible.length}</span>
            </div>
            <Seg
              options={FILTERS}
              value={filter}
              onChange={setFilter}
              label="Filter runs"
              className="runs-filter"
            />
            {error && !selectedId && <div className="runs-note bad">{error}</div>}
            <Card className="runs-list-card">
              {visible.length === 0 ? (
                <div className="runs-empty">
                  {error
                    ? 'Runs could not be loaded.'
                    : !loaded
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
                    selected={selectedJob?.job_id === job.job_id}
                    onSelect={selectJob}
                    onCancel={cancel}
                  />
                ))
              )}
            </Card>
          </section>
        </div>

        <div className="runs-right-column">
          <ProvenancePanel job={selectedJob} />
          <ValidationPanel />
        </div>
      </div>
    </section>
  );
}

function LiveJobPanel({
  job,
  now,
  queuePosition,
  error,
  onCancel,
  onClear,
}: {
  job: JobStatusResponse | null;
  now: number;
  queuePosition?: number;
  error: string | null;
  onCancel: (job: JobStatusResponse) => void | Promise<void>;
  onClear?: () => void;
}) {
  const [cancelling, setCancelling] = useState(false);
  if (!job) {
    return (
      <Card className="runs-live-card">
        <div className="runs-section-head">
          <div>
            <span className="runs-eyebrow">LIVE JOB</span>
            <h2>Job phases</h2>
          </div>
        </div>
        <p className="runs-empty">{error ?? 'No runs are available yet.'}</p>
        <p className="job-honesty">{PHASE_HONESTY_NOTE}</p>
      </Card>
    );
  }

  const { current, failed } = checklistCursor(job);
  const active = isActive(job.state);
  const failedState = job.state === 'FAILED';
  const cancellable = job.state === 'QUEUED' || job.state === 'RUNNING';
  const elapsed = runtimeMs(job, now);
  const requestCancel = async () => {
    setCancelling(true);
    try {
      await onCancel(job);
    } finally {
      setCancelling(false);
    }
  };

  return (
    <Card className="runs-live-card">
      <div className="runs-section-head runs-live-head">
        <div>
          <span className="runs-eyebrow">{active ? 'LIVE JOB' : 'SELECTED RUN'}</span>
          <h2>Job phases</h2>
        </div>
        <StateChip state={job.state} />
      </div>
      <h3 className="runs-job-name">{jobDisplayName(job)}</h3>
      <div className="runs-job-meta">
        <KindChip kind={job.kind} detail={jobKindDetail(job)} />
        <span>{populationLabel(job)}</span>
        <span>{durationLabel(job)}</span>
        {elapsed !== null && (
          <span className="mono">{formatElapsed(elapsed)} {job.finished_at ? 'total' : 'elapsed'}</span>
        )}
      </div>
      <p className="runs-state-note">{stateNote(job, now, queuePosition)}</p>

      <div className="runs-pipeline" aria-label={`Job phase pipeline for ${jobDisplayName(job)}`}>
        {JOB_PHASES.map((phase, index) => {
          const line = PHASE_LINES[phase];
          const isDone = index < current || job.state === 'SUCCEEDED';
          const isFailure = failed && index === current;
          const isCurrent = !isDone && !isFailure && index === current;
          const phaseClass = isDone ? 'done' : isFailure ? 'failed' : isCurrent ? (active ? 'now' : 'stopped') : 'todo';
          return (
            <div className={`phase ${phaseClass}`} key={phase}>
              <span className="ico" aria-hidden="true">
                {isFailure ? '×' : isDone ? '✓' : isCurrent && active ? <span className="pulse" /> : ''}
              </span>
              <span className="phase-copy">
                <span className="nm">{line.nm}</span>
                <span className="phase-desc">{line.desc}</span>
              </span>
              <span className="phase-code mono">{phase}</span>
            </div>
          );
        })}
      </div>

      {failedState && (
        <div className="job-err runs-job-error" role="alert">
          <b>
            {failedPhaseName(job) ? (
              <>The run failed during <span className="mono">{failedPhaseName(job)}</span>.</>
            ) : 'Run failed.'}
          </b>
          <span className="mono">{job.error?.message ?? 'The API reported a failure without a message.'}</span>
        </div>
      )}
      {error && <div className="runs-note bad">{error}</div>}
      <p className="job-honesty">{PHASE_HONESTY_NOTE}</p>
      <div className="runs-live-actions">
        {onClear && <Btn variant="ghost" onClick={onClear}>Clear selection</Btn>}
        {cancellable && (
          <Btn variant="danger" onClick={() => void requestCancel()} disabled={cancelling}>
            Cancel run
          </Btn>
        )}
        {job.state === 'SUCCEEDED' && (
          <Btn variant="primary" to={resultsPath(job)}>
            {job.kind === 'scenario_compare' ? 'Open comparison' : 'Open results'}
          </Btn>
        )}
        {(job.state === 'CANCELLED' || job.state === 'INTERRUPTED') && (
          <Btn to="/simulate">Re-run scenario</Btn>
        )}
        {job.state === 'FAILED' && <Btn to="/simulate">New scenario</Btn>}
      </div>
      {!active && job.error?.message && !failedState && (
        <p className="runs-note">{job.error.message}</p>
      )}
    </Card>
  );
}

function RunRow({
  job,
  now,
  queuePosition,
  selected,
  onSelect,
  onCancel,
}: {
  job: JobStatusResponse;
  now: number;
  queuePosition?: number;
  selected: boolean;
  onSelect: (jobId: string) => void;
  onCancel: (job: JobStatusResponse) => void | Promise<void>;
}) {
  const active = isActive(job.state);
  return (
    <article className={`run-row${selected ? ' selected' : ''}`}>
      <div className="run-row-top">
        <StateChip state={job.state} />
        <button
          type="button"
          className="run-row-name"
          aria-label={`Select ${jobDisplayName(job)} for evidence`}
          aria-pressed={selected}
          onClick={() => onSelect(job.job_id)}
        >
          {jobDisplayName(job)}
        </button>
        <KindChip kind={job.kind} detail={jobKindDetail(job)} />
      </div>
      <div className="run-row-meta">
        <span>{populationLabel(job)}</span>
        <span>{durationLabel(job)}</span>
        <span>{interventionsLabel(job)}</span>
        <span>{stateNote(job, now, queuePosition)}</span>
      </div>
      <div className="run-row-actions">
        {job.state === 'SUCCEEDED' && (
          <Btn variant="primary" to={resultsPath(job)}>
            {job.kind === 'scenario_compare' ? 'Open comparison' : 'Open results'}
          </Btn>
        )}
        {(active || job.state === 'FAILED' || job.state === 'SUCCEEDED') && (
          <Btn onClick={() => onSelect(job.job_id)}>
            {job.state === 'FAILED' ? 'View error' : 'View status'}
          </Btn>
        )}
        {(job.state === 'QUEUED' || job.state === 'RUNNING') && (
          <Btn variant="danger" onClick={() => void onCancel(job)}>Cancel</Btn>
        )}
        {job.state === 'CANCEL_REQUESTED' && (
          <Btn disabled title="Cancellation already requested">Cancelling…</Btn>
        )}
        {job.state === 'INTERRUPTED' ? (
          <Btn to="/simulate">Re-run scenario</Btn>
        ) : job.state === 'FAILED' ? (
          <Btn to="/simulate">New scenario</Btn>
        ) : !active ? (
          <Btn to="/simulate">New scenario</Btn>
        ) : null}
      </div>
    </article>
  );
}

interface ArtifactState {
  jobId: string;
  rows: APIArtifact[];
  loading: boolean;
  error: string | null;
}

function ProvenancePanel({ job }: { job: JobStatusResponse | null }) {
  const [artifacts, setArtifacts] = useState<ArtifactState | null>(null);

  useEffect(() => {
    if (!job) {
      setArtifacts(null);
      return undefined;
    }
    let cancelled = false;
    setArtifacts({ jobId: job.job_id, rows: [], loading: true, error: null });
    api
      .getJobArtifacts(job.job_id)
      .then((response) => {
        if (!cancelled) setArtifacts({ jobId: job.job_id, rows: response.artifacts, loading: false, error: null });
      })
      .catch((e) => {
        if (!cancelled) {
          setArtifacts({
            jobId: job.job_id,
            rows: [],
            loading: false,
            error: e instanceof Error ? e.message : 'Could not load artifact details.',
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [job?.job_id, job?.state, job?.phase, job?.artifact_count]);

  const currentArtifacts = artifacts?.jobId === job?.job_id ? artifacts : null;
  return (
    <Card className="runs-provenance-card">
      <div className="runs-section-head">
        <div>
          <span className="runs-eyebrow">JOB EVIDENCE</span>
          <h2>Provenance</h2>
        </div>
        {job && <StateChip state={job.state} />}
      </div>
      {!job ? (
        <p className="runs-empty">Select a run to inspect its hashes and artifacts.</p>
      ) : (
        <>
          <p className="runs-provenance-name">{jobDisplayName(job)} <span className="mono">{job.job_id}</span></p>
          <ProvenanceChain job={job} running={job.state === 'RUNNING'} />

          <div className="runs-contract" aria-label="Engine and API contract">
            <div className="runs-contract-line">
              <span>Engine Git commit</span>
              <span className="mono">{job.engine_git_commit ?? 'not published'}</span>
            </div>
            <div className="runs-contract-line">
              <span>Engine worktree</span>
              <span className="mono">
                {job.dirty_worktree_flag === true ? 'dirty' : job.dirty_worktree_flag === false ? 'clean' : 'not published'}
              </span>
            </div>
            <div className="runs-contract-line">
              <span>API contract</span>
              <span className="mono">{API_VERSION} · {API_SCHEMA_VERSION}</span>
            </div>
          </div>

          <div className="runs-artifacts">
            <div className="runs-artifacts-heading">
              <h3>Artifacts</h3>
              <span className="mono">{job.artifact_count} reported</span>
            </div>
            {currentArtifacts?.loading && <p className="runs-muted">Loading artifact records…</p>}
            {currentArtifacts?.error && (
              <p className="runs-muted">Artifact records could not be loaded. The job reports {job.artifact_count} artifact(s).</p>
            )}
            {!currentArtifacts?.loading && !currentArtifacts?.error && currentArtifacts?.rows.length === 0 && (
              <p className="runs-muted">
                {job.artifact_count === 0
                  ? 'No artifacts are published for this run.'
                  : 'No artifact records were returned; the job reports the count above.'}
              </p>
            )}
            {(currentArtifacts?.rows ?? []).length > 0 && (
              <ul className="runs-artifact-list">
                {currentArtifacts?.rows.map((artifact) => <ArtifactRow key={artifact.artifact_id} artifact={artifact} />)}
              </ul>
            )}
          </div>
        </>
      )}
    </Card>
  );
}

function ArtifactRow({ artifact }: { artifact: APIArtifact }) {
  const verification = artifact.verification_status;
  const verificationClass = verification === 'passed' ? 'good' : 'bad';
  return (
    <li className="runs-artifact-row">
      <div className="runs-artifact-top">
        <strong>{artifact.role}</strong>
        <span className={`runs-verify-chip ${verificationClass}`}>{verification}</span>
      </div>
      <div className="runs-artifact-detail">
        <span>{artifact.artifact_type}</span>
        <span className="mono">{artifact.artifact_id}</span>
        <span className="mono">{formatBytes(artifact.size_bytes)}</span>
      </div>
    </li>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1_000) return `${bytes} B`;
  if (bytes < 1_000_000) return `${(bytes / 1_000).toFixed(1)} kB`;
  return `${(bytes / 1_000_000).toFixed(1)} MB`;
}

function ValidationPanel() {
  return (
    <section className="runs-validation" aria-labelledby="validation-title">
      <div className="runs-section-head">
        <div>
          <span className="runs-eyebrow">STATIC · HAND-MAINTAINED</span>
          <h2 id="validation-title">Model validation</h2>
        </div>
        <span className="runs-as-of mono">as of {validation.asOf}</span>
      </div>
      <div className="runs-gate-list">
        {validation.gates.map((gate) => (
          <Card className="runs-gate-card" key={gate.id}>
            <div className="runs-gate-head">
              <div>
                <h3>{gate.title}</h3>
                <span className="runs-gate-date mono">{gate.date ?? 'No execution date'}</span>
              </div>
              <span className={`runs-gate-verdict ${gate.verdict.toLowerCase().replace(' ', '-')}`}>
                {gate.verdict}
              </span>
            </div>
            <p className="runs-gate-summary">{gate.summary}</p>
            {gate.arms && gate.arms.length > 0 && (
              <div className="runs-gate-arms">
                {gate.arms.map((arm) => (
                  <div className="runs-gate-arm" key={arm.id}>
                    <strong>{arm.name}</strong>
                    <span>{arm.summary}</span>
                  </div>
                ))}
              </div>
            )}
            <div className="runs-citations">
              <span className="runs-citations-label">Citations</span>
              {gate.citations.map((citation) => (
                <span className="runs-citation mono" key={citation}>{citation}</span>
              ))}
            </div>
          </Card>
        ))}
      </div>
      <p className="runs-validation-note">{validation.note}</p>
    </section>
  );
}
