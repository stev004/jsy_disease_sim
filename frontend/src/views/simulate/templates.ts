/**
 * Scenario templates and intervention presets.
 *
 * Ported from the M10 design mockup (`TEMPLATES` / `IV_PRESETS`). The face of
 * every card is a human concept; `sci` is the scientific-mode line and
 * `toConfig` is the (deliberately minimal) `InterventionConfig` the request
 * carries — richer UI concepts such as "Strength: Full closure" stay visual
 * because the M7 contract has no field for them.
 */

import type { JsonObject } from '../../api';
import type { Provenance } from '../../components';

export type IvKey =
  | 'school'
  | 'isolation'
  | 'quarantine'
  | 'wfh'
  | 'community'
  | 'care'
  | 'vacc'
  | 'travel';

export interface IvMetaItem {
  k: string;
  v: string;
  badge?: Provenance;
}

export interface IvPreset {
  key: IvKey;
  /** `--iv-<color>` token used for the card's left border. */
  color: string;
  name: string;
  /** Days after the scenario start date, for calendar-activated families. */
  offsetDays: number | null;
  meta: (startLabel: string) => IvMetaItem[];
  sci: string;
  /**
   * The minimal, well-formed `InterventionConfig` for this preset, or null
   * when the M7 contract has no matching `InterventionType` (arrival testing
   * is an M8 travel measure, not an intervention family).
   */
  toConfig: ((startDate: string) => JsonObject) | null;
}

/** `YYYY-MM-DD` + n days, still `YYYY-MM-DD`. */
export function addDays(iso: string, days: number): string {
  const base = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(base.getTime())) return iso;
  base.setUTCDate(base.getUTCDate() + days);
  return base.toISOString().slice(0, 10);
}

/** "12 Jan" */
export function dayMonth(iso: string): string {
  const d = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' });
}

/** "6 Jan 2025" */
export function dayMonthYear(iso: string): string {
  const d = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  });
}

export const IV_PRESETS: Record<IvKey, IvPreset> = {
  school: {
    key: 'school',
    color: 'school',
    name: 'School closure',
    offsetDays: 6,
    meta: (start) => [
      { k: 'Start', v: start },
      { k: 'Duration', v: '14 days' },
      { k: 'Strength', v: 'Full closure' },
      { k: 'Scope', v: 'All schools' },
    ],
    sci:
      'school_closure · calendar · release_rule=duration · school_class ×0.00 · ' +
      'school_cross_class ×0.00 · staff memberships included (M4.1)',
    toConfig: (startDate) => ({
      intervention_id: 'school-closure',
      type: 'school_closure',
      activation_rule: 'calendar',
      start_date: startDate,
      duration_days: 14,
      release_rule: 'duration',
      adherence: 1.0,
    }),
  },
  isolation: {
    key: 'isolation',
    color: 'isolation',
    name: 'Case isolation',
    offsetDays: null,
    meta: () => [
      { k: 'Trigger', v: 'On detection' },
      { k: 'Duration', v: '7 days' },
      { k: 'Adherence', v: '80%', badge: 'assumption' },
    ],
    sci:
      'case_isolation · detection_triggered · start_delay_days=1 · household ×0.50, ' +
      'all other routes ×0.10 · adherence=0.80 (scenario assumption)',
    toConfig: () => ({
      intervention_id: 'case-isolation',
      type: 'case_isolation',
      activation_rule: 'detection_triggered',
      duration_days: 7,
      release_rule: 'duration',
      start_delay_days: 1,
      adherence: 0.8,
    }),
  },
  quarantine: {
    key: 'quarantine',
    color: 'quarantine',
    name: 'Household quarantine',
    offsetDays: null,
    meta: () => [
      { k: 'Trigger', v: 'Case detected' },
      { k: 'Duration', v: '10 days' },
      { k: 'Adherence', v: '70%', badge: 'assumption' },
    ],
    sci:
      'household_quarantine · detection_triggered · household members only · ' +
      'non-household routes ×0.15 · adherence=0.70 (scenario assumption)',
    toConfig: () => ({
      intervention_id: 'household-quarantine',
      type: 'household_quarantine',
      activation_rule: 'detection_triggered',
      duration_days: 10,
      release_rule: 'duration',
      adherence: 0.7,
    }),
  },
  wfh: {
    key: 'wfh',
    color: 'wfh',
    name: 'Working from home',
    offsetDays: 10,
    meta: (start) => [
      { k: 'Start', v: start },
      { k: 'Duration', v: '28 days' },
      { k: 'Uptake', v: '45% of workers', badge: 'assumption' },
    ],
    sci:
      'work_from_home · calendar · workplace_team ×0.55 · workplace_transient ×0.55 · ' +
      'bus ×0.70 · shared_vehicle ×0.70 · household ×1.10',
    toConfig: (startDate) => ({
      intervention_id: 'working-from-home',
      type: 'workplace_reduction',
      activation_rule: 'calendar',
      start_date: startDate,
      duration_days: 28,
      release_rule: 'duration',
      adherence: 0.45,
    }),
  },
  community: {
    key: 'community',
    color: 'community',
    name: 'Community reduction',
    offsetDays: 8,
    meta: (start) => [
      { k: 'Start', v: start },
      { k: 'Duration', v: '21 days' },
      { k: 'Strength', v: 'Indoor mixing −40%' },
    ],
    sci:
      'community_reduction · calendar · community_indoor ×0.60 · community_outdoor ×0.90 · ' +
      'visitor_community_indoor ×0.60',
    toConfig: (startDate) => ({
      intervention_id: 'community-reduction',
      type: 'community_reduction',
      activation_rule: 'calendar',
      start_date: startDate,
      duration_days: 21,
      release_rule: 'duration',
      adherence: 1.0,
    }),
  },
  care: {
    key: 'care',
    color: 'care',
    name: 'Care-home protection',
    offsetDays: 4,
    meta: (start) => [
      { k: 'Start', v: start },
      { k: 'Duration', v: 'Rest of run' },
      { k: 'Scope', v: 'Residents & staff' },
    ],
    sci:
      'care_home_protection · calendar · care_resident ×0.35 · care_staff ×0.45 · ' +
      'staff testing cadence 2/week (scenario assumption)',
    toConfig: (startDate) => ({
      intervention_id: 'care-home-protection',
      type: 'care_home_protection',
      activation_rule: 'calendar',
      start_date: startDate,
      release_rule: 'simulation_end',
      adherence: 1.0,
    }),
  },
  vacc: {
    key: 'vacc',
    color: 'vacc',
    name: 'Vaccination campaign',
    offsetDays: 7,
    meta: (start) => [
      { k: 'Start', v: start },
      { k: 'Rate', v: '1,200 doses/day' },
      { k: 'Protection after', v: '14 days', badge: 'assumption' },
    ],
    sci:
      'vaccination · rolling · daily_doses=1200 · onset_delay_days=14 · efficacy=0.62 · ' +
      'oldest-first targeting · waning applies (M5)',
    toConfig: (startDate) => ({
      intervention_id: 'vaccination-campaign',
      type: 'vaccination',
      activation_rule: 'calendar',
      start_date: startDate,
      release_rule: 'simulation_end',
      adherence: 1.0,
      protection_delay_days: 14,
    }),
  },
  travel: {
    key: 'travel',
    color: 'travel',
    name: 'Arrival testing',
    offsetDays: 0,
    meta: () => [
      { k: 'Start', v: 'Day 0' },
      { k: 'Coverage', v: '60% of arrivals' },
      { k: 'Positive arrivals', v: 'Isolated 7 days' },
    ],
    sci:
      'travel_measure · arrival_testing · coverage=0.60 · sensitivity=0.75 · ' +
      'arrival_terminal ×0.70 · positives diverted to isolation (M8)',
    // No M7 InterventionType covers arrival testing; it is an M8 travel
    // measure, so the request carries it as a custom travel configuration.
    toConfig: null,
  },
};

export type TravelMode = 'default' | 'off' | 'custom';

export const TRAVEL_LABEL: Record<TravelMode, string> = {
  default: 'Default (on)',
  off: 'Off',
  custom: 'Custom',
};

export interface ScenarioTemplate {
  name: string;
  desc: string;
  file: string | null;
  ivs: IvKey[];
  travel: TravelMode;
}

export const TEMPLATES: ScenarioTemplate[] = [
  {
    name: 'Blank scenario',
    desc: 'Defaults only — you choose everything',
    file: null,
    ivs: [],
    travel: 'default',
  },
  {
    name: 'Winter baseline',
    desc: 'Uncontrolled winter respiratory outbreak',
    file: 'configs/scenarios/m7_baseline.yaml',
    ivs: [],
    travel: 'default',
  },
  {
    name: 'School closure',
    desc: 'Close all schools for two weeks mid-outbreak',
    file: 'configs/scenarios/m7_school_closure.yaml',
    ivs: ['school'],
    travel: 'default',
  },
  {
    name: 'Isolation + quarantine',
    desc: 'Detected cases isolate; their households quarantine',
    file: 'configs/scenarios/m7_case_isolation_quarantine.yaml',
    ivs: ['isolation', 'quarantine'],
    travel: 'default',
  },
  {
    name: 'Working from home',
    desc: 'Shift workplaces and commuting to home',
    file: 'configs/scenarios/m7_wfh.yaml',
    ivs: ['wfh'],
    travel: 'default',
  },
  {
    name: 'Community reduction',
    desc: 'Damp indoor community mixing',
    file: 'configs/scenarios/m7_community_indoor.yaml',
    ivs: ['community'],
    travel: 'default',
  },
  {
    name: 'Care-home protection',
    desc: 'Shield care residents and staff',
    file: 'configs/scenarios/m7_care_home.yaml',
    ivs: ['care'],
    travel: 'default',
  },
  {
    name: 'Vaccination campaign',
    desc: 'Rolling vaccination with delayed protection',
    file: 'configs/scenarios/m7_vaccination.yaml',
    ivs: ['vacc'],
    travel: 'default',
  },
  {
    name: 'High-season travel',
    desc: 'Summer visitor pressure with arrival testing',
    file: 'configs/travel/m8_arrival_testing.yaml',
    ivs: ['travel'],
    travel: 'custom',
  },
];

/** The "+ Add intervention" picker, in mockup order. */
export const IV_PICKER: Array<{ key: IvKey; label: string; desc: string }> = [
  { key: 'quarantine', label: 'Household quarantine', desc: "Quarantine a detected case's household" },
  { key: 'wfh', label: 'Working from home', desc: 'Reduce workplace & commute contact' },
  { key: 'community', label: 'Community reduction', desc: 'Indoor / outdoor mixing controls' },
  { key: 'care', label: 'Care-home protection', desc: 'Protect residents & care staff' },
  { key: 'vacc', label: 'Vaccination', desc: 'Rollout with delay, efficacy, waning' },
  { key: 'travel', label: 'Travel measures', desc: 'Arrival reduction, testing, quarantine' },
];
