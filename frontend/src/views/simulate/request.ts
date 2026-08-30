/**
 * Form state → M9 request contract.
 *
 * The builder holds human concepts; this module is the single place that
 * translates them into a `ScenarioConfig` (M7/M8) and the job request the API
 * accepts. Anything the contract has no field for stays in the UI only — the
 * request never invents fields.
 */

import type { EnsembleJobRequest, JobRequest, JsonObject, PopulationMode, ScenarioRunRequest } from '../../api';
import { IV_PRESETS, addDays, type IvKey, type TravelMode } from './templates';

/** The five explicit, ordered replicate seeds an ensemble run uses. */
export const ENSEMBLE_SEEDS = [123, 124, 125, 126, 127] as const;

/** Single runs (and the first ensemble replicate) use this seed. */
export const BASE_SEED = ENSEMBLE_SEEDS[0];

export type Uncertainty = 'single' | 'ensemble';

export interface BuilderState {
  name: string;
  population: PopulationMode;
  seeded: number;
  startDate: string;
  duration: number;
  ivs: IvKey[];
  travel: TravelMode;
  uncertainty: Uncertainty;
}

/** `scenario_id` must be a non-empty slug; the API has no free-text name field. */
export function scenarioId(name: string): string {
  const slug = name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return slug || 'untitled-scenario';
}

function travelConfig(mode: TravelMode): JsonObject {
  if (mode === 'off') return { mode: 'disabled' };
  if (mode === 'custom') {
    return { travel_config_id: 'm10-custom-travel-v1', mode: 'explicit_travel' };
  }
  return { mode: 'explicit_travel' };
}

/** The inline `ScenarioConfig` sent to validation and to the job request. */
export function buildScenario(state: BuilderState): JsonObject {
  const interventions = state.ivs
    .map((key) => {
      const preset = IV_PRESETS[key];
      if (!preset.toConfig) return null;
      const start =
        preset.offsetDays === null ? state.startDate : addDays(state.startDate, preset.offsetDays);
      return preset.toConfig(start);
    })
    .filter((item): item is JsonObject => item !== null);

  return {
    schema_version: '8.0',
    scenario_id: scenarioId(state.name),
    scenario_version: '7.0.0',
    interventions,
    seed: BASE_SEED,
    start_date: state.startDate,
    duration_days: state.duration,
    travel: travelConfig(state.travel),
  };
}

/**
 * `initial_seed_count` lives on `OutbreakRunConfig`, not on `ScenarioConfig`,
 * so the seeded-infection count travels in `run_config`. The adapter requires
 * mode/seed/date/duration there to match the request exactly.
 */
function runConfig(state: BuilderState, seed: number): JsonObject {
  return {
    mode: state.population,
    seed,
    start_date: state.startDate,
    duration_days: state.duration,
    initial_seed_count: state.seeded,
  };
}

export function buildRequest(state: BuilderState): JobRequest {
  const scenario = buildScenario(state);
  if (state.uncertainty === 'ensemble') {
    const req: EnsembleJobRequest = {
      kind: 'ensemble',
      mode: state.population,
      replicate_seeds: [...ENSEMBLE_SEEDS],
      start_date: state.startDate,
      duration_days: state.duration,
      ensemble_id: scenarioId(state.name),
      scenario,
      run_config: runConfig(state, ENSEMBLE_SEEDS[0]),
    };
    return req;
  }
  const req: ScenarioRunRequest = {
    kind: 'scenario_run',
    mode: state.population,
    seed: BASE_SEED,
    start_date: state.startDate,
    duration_days: state.duration,
    scenario,
    run_config: runConfig(state, BASE_SEED),
  };
  return req;
}

/** First human-readable message out of a validation error payload. */
export function firstErrorMessage(errors: JsonObject[]): string {
  for (const err of errors) {
    const msg = err.message ?? err.msg ?? err.detail;
    if (typeof msg === 'string' && msg.trim()) {
      const loc = err.loc ?? err.path ?? err.field;
      const where = Array.isArray(loc) ? loc.join('.') : typeof loc === 'string' ? loc : '';
      return where ? `${where}: ${msg}` : msg;
    }
  }
  return 'Scenario is not valid.';
}

/** "a3f2c9…e41b" — first 6 and last 4 characters of the config hash. */
export function shortHash(hash: string): string {
  return hash.length > 12 ? `${hash.slice(0, 6)}…${hash.slice(-4)}` : hash;
}
