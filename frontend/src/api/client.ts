/**
 * Thin typed fetch client for the M9 local API.
 *
 * The server runs at http://127.0.0.1:8000 and allows http://localhost:5173 as
 * a CORS origin, so the browser talks to it directly (no dev proxy).
 */

import {
  ApiError,
  type APIErrorBody,
  type CancelResponse,
  type CapabilitiesResponse,
  type DatasetQuery,
  type DatasetReadResponse,
  type HealthResponse,
  type JobArtifactsResponse,
  type JobDatasetsResponse,
  type JobEventsResponse,
  type JobListParams,
  type JobListResponse,
  type JobRequest,
  type JobStatusResponse,
  type JobSubmissionResponse,
  type JosClient,
  type JsonObject,
  type ScenarioValidationResponse,
} from './types';

export const API_BASE: string =
  (import.meta.env.VITE_JOS_API as string | undefined) ?? 'http://127.0.0.1:8000';

const V1 = '/api/v1';

function buildQuery(params: Record<string, unknown>): string {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      // Repeated params (e.g. `columns`).
      for (const item of value) {
        if (item === undefined || item === null) continue;
        qs.append(key, String(item));
      }
    } else {
      qs.append(key, String(value));
    }
  }
  const s = qs.toString();
  return s ? `?${s}` : '';
}

/** Serialize a DatasetQuery into the API's query-string shape. */
export function datasetQueryString(query: DatasetQuery = {}): string {
  return buildQuery({
    start_date: query.start_date,
    end_date: query.end_date,
    limit: query.limit,
    offset: query.offset,
    parish: query.parish,
    route_id: query.route_id,
    age_band: query.age_band,
    intervention_id: query.intervention_id,
    scope: query.scope,
    metric: query.metric,
    key: query.key,
    seed: query.seed,
    columns: query.columns,
  });
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
        ...(init?.headers ?? {}),
      },
    });
  } catch (cause) {
    throw new ApiError(0, `Cannot reach the JOS API at ${API_BASE}`, {
      code: 'network_error',
      message: cause instanceof Error ? cause.message : String(cause),
    });
  }

  if (!res.ok) {
    let body: APIErrorBody | null = null;
    let message = `${res.status} ${res.statusText}`;
    try {
      const parsed = (await res.json()) as { detail?: APIErrorBody } & Partial<APIErrorBody>;
      body = parsed.detail ?? (parsed.code ? (parsed as APIErrorBody) : null);
      if (body?.message) message = body.message;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, message, body);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export class HttpJosClient implements JosClient {
  readonly usingMock = false;

  health(): Promise<HealthResponse> {
    return request<HealthResponse>('/health');
  }

  capabilities(): Promise<CapabilitiesResponse> {
    return request<CapabilitiesResponse>(`${V1}/capabilities`);
  }

  validateScenario(scenario: JsonObject): Promise<ScenarioValidationResponse> {
    return request<ScenarioValidationResponse>(`${V1}/scenarios/validate`, {
      method: 'POST',
      body: JSON.stringify({ scenario }),
    });
  }

  submitJob(req: JobRequest, idempotencyKey?: string): Promise<JobSubmissionResponse> {
    return request<JobSubmissionResponse>(`${V1}/jobs`, {
      method: 'POST',
      body: JSON.stringify(req),
      headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : undefined,
    });
  }

  listJobs(params: JobListParams = {}): Promise<JobListResponse> {
    return request<JobListResponse>(
      `${V1}/jobs${buildQuery({
        state: params.state,
        kind: params.kind,
        limit: params.limit,
        offset: params.offset,
      })}`,
    );
  }

  getJob(jobId: string): Promise<JobStatusResponse> {
    return request<JobStatusResponse>(`${V1}/jobs/${encodeURIComponent(jobId)}`);
  }

  cancelJob(jobId: string): Promise<CancelResponse> {
    return request<CancelResponse>(`${V1}/jobs/${encodeURIComponent(jobId)}/cancel`, {
      method: 'POST',
    });
  }

  getJobEvents(jobId: string, limit?: number): Promise<JobEventsResponse> {
    return request<JobEventsResponse>(
      `${V1}/jobs/${encodeURIComponent(jobId)}/events${buildQuery({ limit })}`,
    );
  }

  getJobArtifacts(jobId: string): Promise<JobArtifactsResponse> {
    return request<JobArtifactsResponse>(`${V1}/jobs/${encodeURIComponent(jobId)}/artifacts`);
  }

  getJobDatasets(jobId: string): Promise<JobDatasetsResponse> {
    return request<JobDatasetsResponse>(`${V1}/jobs/${encodeURIComponent(jobId)}/datasets`);
  }

  readDataset(jobId: string, name: string, query: DatasetQuery = {}): Promise<DatasetReadResponse> {
    return request<DatasetReadResponse>(
      `${V1}/jobs/${encodeURIComponent(jobId)}/datasets/${encodeURIComponent(name)}` +
        datasetQueryString(query),
    );
  }
}

export const httpClient = new HttpJosClient();
