import type { ReactNode } from 'react';
import type { JobKind, JobState } from '../api/types';

const STATE_CLASS: Record<JobState, string> = {
  QUEUED: 'state-queued',
  RUNNING: 'state-running',
  SUCCEEDED: 'state-succeeded',
  FAILED: 'state-failed',
  CANCEL_REQUESTED: 'state-cancel-requested',
  CANCELLED: 'state-cancelled',
  INTERRUPTED: 'state-interrupted',
};

const STATE_LABEL: Record<JobState, string> = {
  QUEUED: 'Queued',
  RUNNING: 'Running',
  SUCCEEDED: 'Succeeded',
  FAILED: 'Failed',
  CANCEL_REQUESTED: 'Cancelling…',
  CANCELLED: 'Cancelled',
  INTERRUPTED: 'Interrupted',
};

const KIND_LABEL: Record<JobKind, string> = {
  scenario_run: 'Scenario run',
  scenario_compare: 'Compare',
  ensemble: 'Ensemble',
};

export function jobStateLabel(state: JobState): string {
  return STATE_LABEL[state];
}

export function jobKindLabel(kind: JobKind): string {
  return KIND_LABEL[kind];
}

/** State chip: colored soft pill, always paired with the state word. */
export function StateChip({ state, label }: { state: JobState; label?: string }) {
  const running = state === 'RUNNING' || state === 'CANCEL_REQUESTED';
  return (
    <span className={`chip ${STATE_CLASS[state]}`}>
      {running ? (
        <span className="pulse" />
      ) : (
        <span className="dot" style={{ background: 'currentColor' }} />
      )}
      {label ?? STATE_LABEL[state]}
    </span>
  );
}

/** Neutral kind chip, e.g. "Ensemble · 5 seeds". */
export function KindChip({ kind, detail }: { kind: JobKind; detail?: string }) {
  return (
    <span className="chip kind">
      {KIND_LABEL[kind]}
      {detail ? ` · ${detail}` : ''}
    </span>
  );
}

/** Bare chip for free-form neutral text. */
export function Chip({ className, children }: { className?: string; children: ReactNode }) {
  return <span className={['chip', className].filter(Boolean).join(' ')}>{children}</span>;
}
