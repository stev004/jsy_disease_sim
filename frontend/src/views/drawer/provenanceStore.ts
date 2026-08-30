/**
 * Which job the "Assumptions & sources" drawer should describe.
 *
 * The drawer is mounted once, above the router, so a view announces its job
 * here instead of re-rendering the drawer. When nothing has been announced the
 * drawer falls back to the newest succeeded job.
 */

import { useSyncExternalStore } from 'react';

let jobId: string | null = null;
const listeners = new Set<() => void>();

export function setProvenanceJobId(id: string | null): void {
  if (jobId === id) return;
  jobId = id;
  for (const l of listeners) l();
}

export function getProvenanceJobId(): string | null {
  return jobId;
}

function subscribe(cb: () => void): () => void {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

export function useProvenanceJobId(): string | null {
  return useSyncExternalStore(subscribe, getProvenanceJobId, getProvenanceJobId);
}
