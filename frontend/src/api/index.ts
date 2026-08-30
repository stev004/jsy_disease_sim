/**
 * Client selection: real M9 API vs. the deterministic mock.
 *
 * Rules (decided once per browser session, then remembered):
 *   1. `VITE_JOS_MOCK === '1'`  -> always the mock.
 *   2. otherwise a `health()` probe against the real API decides;
 *      if it fails, the app silently falls back to the mock.
 *
 * `api` is a stable proxy: every call awaits the (memoized) resolution first,
 * so views can import it at module scope and never think about the switch.
 * `useApiMode()` exposes the decision to the UI.
 */

import { useSyncExternalStore } from 'react';
import { httpClient } from './client';
import { mockClient } from './mock';
import type {
  CancelResponse,
  CapabilitiesResponse,
  DatasetQuery,
  DatasetReadResponse,
  HealthResponse,
  JobArtifactsResponse,
  JobDatasetsResponse,
  JobEventsResponse,
  JobListParams,
  JobListResponse,
  JobRequest,
  JobStatusResponse,
  JobSubmissionResponse,
  JosClient,
  JsonObject,
  ScenarioValidationResponse,
} from './types';

export * from './types';
export { API_BASE } from './client';

const FORCE_MOCK = (import.meta.env.VITE_JOS_MOCK as string | undefined) === '1';

export interface ApiMode {
  /** null until the health probe resolves. */
  usingMock: boolean | null;
  /** True once the decision has been made for this session. */
  resolved: boolean;
  /** Why the mock is in use, when it is. */
  reason: 'forced' | 'unreachable' | null;
}

let mode: ApiMode = FORCE_MOCK
  ? { usingMock: true, resolved: true, reason: 'forced' }
  : { usingMock: null, resolved: false, reason: null };

const listeners = new Set<() => void>();

function setMode(next: ApiMode): void {
  mode = next;
  for (const l of listeners) l();
}

export function getApiMode(): ApiMode {
  return mode;
}

function subscribe(cb: () => void): () => void {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

/** React binding for the current real/mock decision. */
export function useApiMode(): ApiMode {
  return useSyncExternalStore(subscribe, getApiMode, getApiMode);
}

let resolution: Promise<JosClient> | null = null;

/** Resolves (once per session) which client backs the app. */
export function resolveClient(): Promise<JosClient> {
  if (resolution) return resolution;
  if (FORCE_MOCK) {
    resolution = Promise.resolve(mockClient as JosClient);
    return resolution;
  }
  resolution = httpClient
    .health()
    .then(() => {
      setMode({ usingMock: false, resolved: true, reason: null });
      return httpClient as JosClient;
    })
    .catch(() => {
      setMode({ usingMock: true, resolved: true, reason: 'unreachable' });
      return mockClient as JosClient;
    });
  return resolution;
}

/** Kick the probe off early (called from main.tsx). */
export function primeClient(): void {
  void resolveClient();
}

/** The client every view should use. */
export const api: JosClient = {
  get usingMock(): boolean {
    return mode.usingMock === true;
  },
  async health(): Promise<HealthResponse> {
    return (await resolveClient()).health();
  },
  async capabilities(): Promise<CapabilitiesResponse> {
    return (await resolveClient()).capabilities();
  },
  async validateScenario(scenario: JsonObject): Promise<ScenarioValidationResponse> {
    return (await resolveClient()).validateScenario(scenario);
  },
  async submitJob(req: JobRequest, idempotencyKey?: string): Promise<JobSubmissionResponse> {
    return (await resolveClient()).submitJob(req, idempotencyKey);
  },
  async listJobs(params?: JobListParams): Promise<JobListResponse> {
    return (await resolveClient()).listJobs(params);
  },
  async getJob(jobId: string): Promise<JobStatusResponse> {
    return (await resolveClient()).getJob(jobId);
  },
  async cancelJob(jobId: string): Promise<CancelResponse> {
    return (await resolveClient()).cancelJob(jobId);
  },
  async getJobEvents(jobId: string, limit?: number): Promise<JobEventsResponse> {
    return (await resolveClient()).getJobEvents(jobId, limit);
  },
  async getJobArtifacts(jobId: string): Promise<JobArtifactsResponse> {
    return (await resolveClient()).getJobArtifacts(jobId);
  },
  async getJobDatasets(jobId: string): Promise<JobDatasetsResponse> {
    return (await resolveClient()).getJobDatasets(jobId);
  },
  async readDataset(
    jobId: string,
    name: string,
    query?: DatasetQuery,
  ): Promise<DatasetReadResponse> {
    return (await resolveClient()).readDataset(jobId, name, query);
  },
};
