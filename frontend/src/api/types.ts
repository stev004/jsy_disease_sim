/**
 * TypeScript mirror of `src/jersey_outbreak/api_schemas.py` (M9 API, schema
 * `m9-1.0`, routes under `/api/v1`).  Field names, optionality and defaults
 * follow the pydantic models exactly.  Dates cross the wire as ISO
 * `YYYY-MM-DD` strings; timestamps as ISO datetime strings.
 */

export const API_VERSION = 'v1';
export const API_SCHEMA_VERSION = 'm9-1.0';
export const MAX_DATASET_ROWS = 10_000;
export const DEFAULT_DATASET_LIMIT = 1_000;

export type JobKind = 'scenario_run' | 'scenario_compare' | 'ensemble';

export type JobState =
  | 'QUEUED'
  | 'RUNNING'
  | 'SUCCEEDED'
  | 'FAILED'
  | 'CANCEL_REQUESTED'
  | 'CANCELLED'
  | 'INTERRUPTED';

export type JobPhase =
  | 'queued'
  | 'validating'
  | 'preparing'
  | 'running'
  | 'writing_artifacts'
  | 'verifying'
  | 'finalizing'
  | 'complete'
  | 'failed'
  | 'cancelled'
  | 'interrupted';

export const JOB_STATES: JobState[] = [
  'QUEUED',
  'RUNNING',
  'SUCCEEDED',
  'FAILED',
  'CANCEL_REQUESTED',
  'CANCELLED',
  'INTERRUPTED',
];

/** Ordered phases the job monitor renders as a checklist (M9 contract order). */
export const JOB_PHASES: JobPhase[] = [
  'queued',
  'validating',
  'preparing',
  'running',
  'writing_artifacts',
  'verifying',
  'finalizing',
];

/** Population presets; sizes come from `capabilities.population_presets`. */
export type PopulationMode = 'ci' | 'scaled' | 'full';

/** ISO `YYYY-MM-DD`. */
export type ISODate = string;
/** ISO 8601 datetime string. */
export type ISODateTime = string;

export type JsonObject = Record<string, unknown>;

/* ============================ requests ============================ */

export interface ScenarioRunRequest {
  kind: 'scenario_run';
  /** default "ci" */
  mode?: PopulationMode;
  /** default 123 */
  seed?: number;
  /** default "2025-01-06" */
  start_date?: ISODate;
  /** default 30, 1..366 */
  duration_days?: number;
  scenario?: JsonObject | null;
  parameters?: JsonObject | null;
  observation_config?: JsonObject | null;
  run_config?: JsonObject | null;
}

export interface ScenarioCompareRequest {
  kind: 'scenario_compare';
  /** default "ci" */
  mode?: PopulationMode;
  /** default [123]; unique, non-negative, explicitly ordered */
  replicate_seeds?: number[];
  /** default "2025-01-06" */
  start_date?: ISODate;
  /** default 30, 1..366 */
  duration_days?: number;
  baseline?: JsonObject | null;
  /** required */
  treated: JsonObject;
  /** default "m9-comparison" */
  comparison_id?: string;
  parameters?: JsonObject | null;
  observation_config?: JsonObject | null;
  /** default 1, 1..32 */
  workers?: number;
  /** default false */
  allow_unsafe_workers?: boolean;
}

export interface EnsembleJobRequest {
  kind: 'ensemble';
  /** default "ci" */
  mode?: PopulationMode;
  /** default [101, 102, 103]; unique, non-negative, explicitly ordered */
  replicate_seeds?: number[];
  /** default "2025-01-06" */
  start_date?: ISODate;
  /** default 30, 1..366 */
  duration_days?: number;
  /** default "m9-ensemble" */
  ensemble_id?: string;
  scenario?: JsonObject | null;
  parameters?: JsonObject | null;
  observation_config?: JsonObject | null;
  run_config?: JsonObject | null;
  /** default 1, 1..32 */
  workers?: number;
  /** default false */
  allow_unsafe_workers?: boolean;
}

export type JobRequest = ScenarioRunRequest | ScenarioCompareRequest | EnsembleJobRequest;

/** Defaults matching the pydantic models, for pre-filling the builder. */
export const SCENARIO_RUN_DEFAULTS = {
  mode: 'ci',
  seed: 123,
  start_date: '2025-01-06',
  duration_days: 30,
} as const;

export const SCENARIO_COMPARE_DEFAULTS = {
  mode: 'ci',
  replicate_seeds: [123],
  start_date: '2025-01-06',
  duration_days: 30,
  comparison_id: 'm9-comparison',
  workers: 1,
  allow_unsafe_workers: false,
} as const;

export const ENSEMBLE_DEFAULTS = {
  mode: 'ci',
  replicate_seeds: [101, 102, 103],
  start_date: '2025-01-06',
  duration_days: 30,
  ensemble_id: 'm9-ensemble',
  workers: 1,
  allow_unsafe_workers: false,
} as const;

export interface ScenarioValidationRequest {
  scenario: JsonObject;
}

/* ============================ responses ============================ */

export interface APIErrorBody {
  code: string;
  message: string;
  details?: JsonObject | null;
  request_id?: string | null;
}

export interface HealthResponse {
  status: 'ok' | 'degraded';
  api_version: 'v1';
  api_schema_version: 'm9-1.0';
  registry: 'ok' | 'error';
}

export interface CapabilitiesResponse {
  api_version: 'v1';
  api_schema_version: 'm9-1.0';
  package_version: string;
  artifact_schema_version_semantics: string;
  engine: JsonObject;
  artifact_schema_versions: Record<string, string>;
  population_presets: Record<string, number>;
  job_kinds: JobKind[];
  resident_route_ids: string[];
  travel_route_ids: string[];
  route_families: string[];
  intervention_families: string[];
  travel_modes: string[];
  parishes: string[];
  dataset_names: string[];
  scheduler: JsonObject;
  limits: Record<string, number>;
  state_directory: string;
  scientific_claim_boundary: string;
}

export interface ScenarioValidationResponse {
  valid: boolean;
  errors: JsonObject[];
  warnings: string[];
  normalized?: JsonObject | null;
  scenario_config_hash?: string | null;
}

export interface JobSubmissionResponse {
  job_id: string;
  kind: JobKind;
  state: 'QUEUED';
  request_hash: string;
  status_url: string;
  events_url: string;
  already_exists: boolean;
}

export interface JobStatusResponse {
  job_id: string;
  kind: JobKind;
  state: JobState;
  phase: JobPhase;
  created_at: ISODateTime;
  started_at?: string | null;
  finished_at?: string | null;
  /** Always null in M9 — Starsim exposes no truthful run fraction. */
  progress_fraction?: number | null;
  request_hash: string;
  request: JsonObject;
  scenario_hash?: string | null;
  latent_hash?: string | null;
  bundle_hash?: string | null;
  error?: APIErrorBody | null;
  artifact_count: number;
  verification_status?: string | null;
  worker_pid?: number | null;
  last_heartbeat?: string | null;
  exit_status?: number | null;
  result_manifest_path?: string | null;
  result_manifest_hash?: string | null;
  engine_git_commit?: string | null;
  dirty_worktree_flag?: boolean | null;
  status_url: string;
}

export interface JobListResponse {
  jobs: JobStatusResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface JobListParams {
  state?: JobState;
  kind?: JobKind;
  /** default 50, 1..100 */
  limit?: number;
  /** default 0 */
  offset?: number;
}

export interface CancelResponse {
  job_id: string;
  state: JobState;
  action: string;
  idempotent: boolean;
}

export interface JobEvent {
  event_id: string;
  job_id: string;
  timestamp: ISODateTime;
  type: string;
  message: string;
  metadata: JsonObject;
}

export interface JobEventsResponse {
  job_id: string;
  events: JobEvent[];
}

export interface APIArtifact {
  role: string;
  artifact_type: string;
  artifact_id: string;
  manifest_path: string;
  scenario_hash?: string | null;
  latent_hash?: string | null;
  bundle_hash?: string | null;
  logical_content_hash?: string | null;
  verification_status: 'passed' | 'failed';
  size_bytes: number;
  datasets: string[];
}

export interface JobArtifactsResponse {
  job_id: string;
  artifacts: APIArtifact[];
}

export interface JobDatasetsResponse {
  job_id: string;
  datasets: JsonObject[];
  available: boolean;
}

/** Bounded, non-SQL dataset query controls (`DatasetQuery`). */
export interface DatasetQuery {
  start_date?: ISODate;
  end_date?: ISODate;
  /** default 1000, 1..10000 */
  limit?: number;
  /** default 0, 0..100000 */
  offset?: number;
  parish?: string;
  route_id?: string;
  age_band?: string;
  intervention_id?: string;
  scope?: string;
  metric?: string;
  key?: string;
  seed?: number;
  /** Repeated `columns` query params; must be non-empty and unique. */
  columns?: string[];
}

export type DatasetRow = Record<string, string | number | boolean | null>;

export interface DatasetReadResponse {
  job_id: string;
  dataset: string;
  artifact_id: string;
  metadata: JsonObject;
  rows: DatasetRow[];
  /** null when the read was filtered (no second whole-dataset count scan). */
  total?: number | null;
  has_more: boolean;
  limit: number;
  offset: number;
  next_offset?: number | null;
}

/** Tidy dataset names the results workspace reads. */
export const DATASET_DAILY_EPIDEMIC = 'daily_epidemic';
export const DATASET_DAILY_PARISH = 'daily_parish';
export const DATASET_DAILY_ROUTE = 'daily_route';
export const DATASET_DAILY_AGE = 'daily_age';

/** Error thrown by the client for non-2xx responses. */
export class ApiError extends Error {
  readonly status: number;
  readonly body: APIErrorBody | null;

  constructor(status: number, message: string, body: APIErrorBody | null = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

/** The surface every client (real or mock) implements. */
export interface JosClient {
  readonly usingMock: boolean;
  health(): Promise<HealthResponse>;
  capabilities(): Promise<CapabilitiesResponse>;
  validateScenario(scenario: JsonObject): Promise<ScenarioValidationResponse>;
  submitJob(req: JobRequest, idempotencyKey?: string): Promise<JobSubmissionResponse>;
  listJobs(params?: JobListParams): Promise<JobListResponse>;
  getJob(jobId: string): Promise<JobStatusResponse>;
  cancelJob(jobId: string): Promise<CancelResponse>;
  getJobEvents(jobId: string, limit?: number): Promise<JobEventsResponse>;
  getJobArtifacts(jobId: string): Promise<JobArtifactsResponse>;
  getJobDatasets(jobId: string): Promise<JobDatasetsResponse>;
  readDataset(jobId: string, name: string, query?: DatasetQuery): Promise<DatasetReadResponse>;
}
