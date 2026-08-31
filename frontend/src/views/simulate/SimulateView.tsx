/**
 * Simulate — the scenario builder.
 *
 * Tier 0 decisions are on the face of the cards, tier 1 lives in opt-in cards
 * (interventions, travel, uncertainty) and tier 2 in each card's `Advanced`
 * disclosure, which opens itself in scientific mode. Every edit debounces into
 * `POST /api/v1/scenarios/validate`; the rail shows the verdict and the
 * returned `scenario_config_hash`, and Run is disabled until the scenario is
 * valid.
 */

import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, type CapabilitiesResponse, type JsonObject, type PopulationMode } from '../../api';
import { Badge, Btn, Card, Label, Seg, useToast, type SegOption } from '../../components';
import { useDetail } from '../../app/DetailProvider';
import { useScenarioContextEffect } from '../../app/ScenarioContextProvider';
import {
  IV_PICKER,
  IV_PRESETS,
  TEMPLATES,
  TRAVEL_LABEL,
  addDays,
  dayMonth,
  dayMonthYear,
  type IvKey,
  type TravelMode,
} from './templates';
import {
  BASE_SEED,
  ENSEMBLE_SEEDS,
  buildRequest,
  buildScenario,
  firstErrorMessage,
  shortHash,
  type BuilderState,
  type Uncertainty,
} from './request';
import './simulate.css';

const FALLBACK_PRESETS: Record<PopulationMode, number> = {
  full: 104_540,
  scaled: 15_000,
  ci: 3_000,
};

const POPULATION_NAME: Record<PopulationMode, string> = {
  full: 'Full Jersey',
  scaled: 'Scaled',
  ci: 'Quick test',
};

const DEFAULT_STATE: BuilderState = {
  name: 'Quick respiratory baseline',
  population: 'ci',
  seeded: 1,
  startDate: '2025-01-06', // engine calendar (school terms, seasonality) is anchored to 2025
  duration: 30,
  ivs: [],
  travel: 'off',
  uncertainty: 'single',
};

export const SUPPORTED_START_DATE_MIN = '2025-01-01';
export const SUPPORTED_START_DATE_MAX = '2025-12-31';

export function isSupportedStartDate(value: string): boolean {
  return value >= SUPPORTED_START_DATE_MIN && value <= SUPPORTED_START_DATE_MAX;
}

const TRAVEL_OPTIONS: SegOption<TravelMode>[] = [
  { value: 'default', label: 'Default' },
  { value: 'off', label: 'Off' },
  { value: 'custom', label: 'Custom' },
];

const UNCERTAINTY_OPTIONS: SegOption<Uncertainty>[] = [
  { value: 'single', label: 'Single run' },
  { value: 'ensemble', label: `Ensemble · ${ENSEMBLE_SEEDS.length} seeds` },
];

const nf = new Intl.NumberFormat('en-GB');

interface ValidationState {
  status: 'idle' | 'checking' | 'valid' | 'invalid' | 'error';
  hash: string | null;
  message: string | null;
}

/** `details.adv` that opens itself whenever scientific mode is on. */
function Adv({ summary, children }: { summary: string; children: ReactNode }) {
  const { sci } = useDetail();
  const [open, setOpen] = useState(sci);
  useEffect(() => setOpen(sci), [sci]);
  return (
    <details
      className="adv"
      open={open}
      onToggle={(e) => setOpen((e.currentTarget as HTMLDetailsElement).open)}
    >
      <summary>{summary}</summary>
      {children}
    </details>
  );
}

function AdvItem({
  name,
  value,
  badge,
  mono = true,
}: {
  name: string;
  value: string;
  badge?: ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="adv-item">
      <span className="nm">{name}</span>
      <span>
        <b className={mono ? 'num' : undefined}>{value}</b> {badge}
      </span>
    </div>
  );
}

export function SimulateView() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const { sci } = useDetail();

  const [state, setState] = useState<BuilderState>(DEFAULT_STATE);
  const [tpl, setTpl] = useState<number | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [caps, setCaps] = useState<CapabilitiesResponse | null>(null);
  const [validation, setValidation] = useState<ValidationState>({
    status: 'idle',
    hash: null,
    message: null,
  });
  const [submitting, setSubmitting] = useState(false);

  useScenarioContextEffect({
    name: state.name.trim() || 'New scenario',
    kind: state.uncertainty === 'ensemble' ? 'ensemble' : 'scenario_run',
    kindDetail: 'Draft',
  });

  useEffect(() => {
    let alive = true;
    void api
      .capabilities()
      .then((c) => {
        if (alive) setCaps(c);
      })
      .catch(() => {
        /* the rail falls back to documented preset sizes */
      });
    return () => {
      alive = false;
    };
  }, []);

  const presets = useMemo<Record<PopulationMode, number>>(() => {
    const p = caps?.population_presets;
    if (!p) return FALLBACK_PRESETS;
    return {
      full: typeof p.full === 'number' ? p.full : FALLBACK_PRESETS.full,
      scaled: typeof p.scaled === 'number' ? p.scaled : FALLBACK_PRESETS.scaled,
      ci: typeof p.ci === 'number' ? p.ci : FALLBACK_PRESETS.ci,
    };
  }, [caps]);

  const populationOptions = useMemo<SegOption<PopulationMode>[]>(
    () =>
      (['full', 'scaled', 'ci'] as PopulationMode[]).map((mode) => ({
        value: mode,
        label: `${POPULATION_NAME[mode]} · ${nf.format(presets[mode])}`,
      })),
    [presets],
  );

  const engineLine = useMemo(() => {
    const engine = (caps?.engine ?? {}) as JsonObject;
    const commit = typeof engine.git_commit === 'string' ? engine.git_commit : 'unknown';
    const dirty = engine.dirty_worktree_flag === true ? 'dirty' : 'clean';
    const starsim = typeof engine.version === 'string' ? engine.version : 'unknown';
    return `${commit} ${dirty} · starsim ${starsim}`;
  }, [caps]);

  const scenario = useMemo(() => buildScenario(state), [state]);
  const scenarioKey = useMemo(() => JSON.stringify(scenario), [scenario]);

  /* Continuous validation: 500ms after the last edit. */
  const requestSeq = useRef(0);
  useEffect(() => {
    const seq = ++requestSeq.current;
    if (!isSupportedStartDate(state.startDate)) {
      setValidation({
        status: 'invalid',
        hash: null,
        message: 'The current M9 engine supports start dates in 2025 only.',
      });
      return undefined;
    }
    setValidation((v) => ({ ...v, status: 'checking' }));
    const timer = window.setTimeout(() => {
      void api
        .validateScenario(JSON.parse(scenarioKey) as JsonObject)
        .then((res) => {
          if (seq !== requestSeq.current) return;
          setValidation({
            status: res.valid ? 'valid' : 'invalid',
            hash: res.scenario_config_hash ?? null,
            message: res.valid ? null : firstErrorMessage(res.errors),
          });
        })
        .catch((cause: unknown) => {
          if (seq !== requestSeq.current) return;
          setValidation({
            status: 'error',
            hash: null,
            message: cause instanceof Error ? cause.message : 'Validation is unavailable.',
          });
        });
    }, 500);
    return () => window.clearTimeout(timer);
  }, [scenarioKey, state.startDate]);

  const applyTemplate = useCallback((index: number) => {
    const t = TEMPLATES[index];
    setTpl(index);
    setState((s) => ({ ...s, name: t.name, ivs: [...t.ivs], travel: t.travel }));
    setPickerOpen(false);
  }, []);

  const addIntervention = useCallback((key: IvKey) => {
    setState((s) => (s.ivs.includes(key) ? s : { ...s, ivs: [...s.ivs, key] }));
    setPickerOpen(false);
  }, []);

  const removeIntervention = useCallback((key: IvKey) => {
    setState((s) => ({ ...s, ivs: s.ivs.filter((k) => k !== key) }));
  }, []);

  const dateSupported = isSupportedStartDate(state.startDate);
  const canRun = validation.status === 'valid' && dateSupported && !submitting;

  const run = useCallback(async () => {
    if (!canRun) return;
    setSubmitting(true);
    const name = state.name.trim() || 'Untitled scenario';
    try {
      await api.submitJob(buildRequest(state), crypto.randomUUID());
      showToast({ title: `Run submitted — ${name}`, tone: 'good' });
      navigate('/runs');
    } catch (cause: unknown) {
      showToast({
        title: 'Could not submit the run',
        body: cause instanceof Error ? cause.message : String(cause),
        tone: 'bad',
      });
      setSubmitting(false);
    }
  }, [canRun, navigate, showToast, state]);

  const template = tpl === null ? null : TEMPLATES[tpl];
  const ivNames = state.ivs.map((k) => IV_PRESETS[k].name);

  return (
    <section className="view view-simulate">
      <div className="wrap">
        <div className="b-head">
          <h1>New scenario</h1>
          <span className="sub">
            Defaults are a cheap single-seed baseline. Open a section only if you want to change it.
          </span>
        </div>

        <div>
          {/* ---------------- templates ---------------- */}
          <Card className="b-card">
            <div className="tpl-row">
              <span className="label" style={{ flex: 'none', paddingTop: 5 }}>
                Start from
              </span>
              <div className="tpl-chips" role="group" aria-label="Scenario templates">
                {TEMPLATES.map((t, i) => (
                  <button
                    key={t.name}
                    type="button"
                    className="tchip"
                    aria-pressed={tpl === i}
                    title={t.desc}
                    onClick={() => applyTemplate(i)}
                  >
                    {t.name}
                  </button>
                ))}
              </div>
            </div>
            <p className="tpl-desc" role="status">
              {template ? (
                <>
                  {template.desc}.{tpl !== null && tpl > 0 ? ' Applied — everything below stays editable.' : ''}
                  {template.file && sci ? <span className="mono"> {template.file}</span> : null}
                </>
              ) : (
                'A blank scenario with sensible defaults — you choose everything. All templates are synthetic demo assumptions and stay fully editable.'
              )}
            </p>
          </Card>

          {/* ---------------- name ---------------- */}
          <Card className="b-card">
            <Label htmlFor="scnName">Scenario name</Label>
            <div className="b-row" style={{ marginTop: 8 }}>
              <input
                id="scnName"
                type="text"
                value={state.name}
                onChange={(e) => setState((s) => ({ ...s, name: e.target.value }))}
                style={{ flex: 1, fontSize: 14, fontWeight: 600 }}
              />
            </div>
          </Card>

          {/* ---------------- population ---------------- */}
          <Card className="b-card">
            <div className="head">
              <h2>Population</h2>
            </div>
            <div className="b-row">
              <Seg
                options={populationOptions}
                value={state.population}
                onChange={(population) => setState((s) => ({ ...s, population }))}
                label="Population preset"
              />
            </div>
            <p className="desc" style={{ marginTop: 10 }}>
              Full Jersey is one synthetic agent per resident with households, schools, workplaces,
              care settings and commuting. Quick test is for fast iteration, not results.
            </p>
          </Card>

          {/* ---------------- disease ---------------- */}
          <Card className="b-card">
            <div className="head">
              <h2>Disease</h2>
              <Badge kind="assumption">Scenario assumption</Badge>
            </div>
            <div className="b-row">
              <span className="chip kind" style={{ fontSize: 12.5, padding: '6px 12px' }}>
                Generic respiratory (SEIRS)
              </span>
              <span className="desc">
                A pathogen-neutral respiratory infection. Severity and deaths are not modelled.
              </span>
            </div>
            <Adv summary="Disease parameters">
              <div className="adv-grid">
                <AdvItem name="Transmissibility (β)" value="0.08" badge={<Badge kind="assumption" />} />
                <AdvItem name="Latent duration" value="2.0 d" badge={<Badge kind="assumption" />} />
                <AdvItem name="Infectious duration" value="5.0 d" badge={<Badge kind="assumption" />} />
                <AdvItem name="Immunity waning" value="Disabled" badge={<Badge kind="assumption" />} />
              </div>
              <div className="sci-only sci-note" style={{ marginTop: 10 }}>
                beta = 0.08 · fixed · valid [0, 1] · per-contact daily transmission probability
                <br />
                latent_duration = constant(mean_days=2.0) · E→I
                <br />
                infectious_duration = constant(mean_days=5.0) · I→R
                <br />
                waning_enabled = false · 30-day full reset available only as the V1 comparator
                <br />
                route_multipliers: all 11 M4 routes ×1.0 (neutral) · parameter_set
                respiratory-demo-v1.1
              </div>
            </Adv>
          </Card>

          {/* ---------------- outbreak & duration ---------------- */}
          <Card className="b-card">
            <div className="head">
              <h2>Initial outbreak &amp; duration</h2>
            </div>
            <div className="b-row">
              <span>Start with</span>
              <input
                className="inline-num num"
                type="number"
                min={0}
                max={1000}
                value={state.seeded}
                aria-label="Initial infections"
                onChange={(e) =>
                  setState((s) => ({
                    ...s,
                    seeded: Math.max(0, Number(e.target.value) || 0),
                  }))
                }
              />
              <span>infections on</span>
              <input
                type="date"
                value={state.startDate}
                min={SUPPORTED_START_DATE_MIN}
                max={SUPPORTED_START_DATE_MAX}
                style={{ width: 150 }}
                aria-label="Start date"
                onChange={(e) =>
                  setState((s) => ({ ...s, startDate: e.target.value || s.startDate }))
                }
              />
            </div>
            <p className="desc" style={{ marginTop: 8 }}>
              M9 engine support: 1 Jan–31 Dec 2025. Dates outside 2025 cannot be submitted.
            </p>
            <div className="slider-row">
              <input
                type="range"
                min={14}
                max={180}
                value={state.duration}
                aria-label="Duration in days"
                onChange={(e) => setState((s) => ({ ...s, duration: Number(e.target.value) }))}
              />
              <b className="num">{state.duration} days</b>
            </div>
            <Adv summary="Imports &amp; seeding detail">
              <div className="adv-grid">
                <AdvItem
                  name="Background import rate"
                  value="0 / day"
                  badge={<Badge kind="assumption" />}
                />
                <AdvItem name="Seeding method" value="Count (not prevalence)" mono={false} />
              </div>
            </Adv>
          </Card>

          {/* ---------------- interventions ---------------- */}
          <Card className="b-card">
            <div className="head">
              <h2>Interventions</h2>
              <span className="desc" style={{ margin: 0 }}>
                Optional — a baseline runs with none
              </span>
            </div>
            <div>
              {state.ivs.length === 0 ? (
                <div className="iv-empty">No interventions — this is a baseline.</div>
              ) : (
                state.ivs.map((key) => {
                  const preset = IV_PRESETS[key];
                  const startLabel =
                    preset.offsetDays === null
                      ? ''
                      : dayMonth(addDays(state.startDate, preset.offsetDays));
                  return (
                    <div
                      key={key}
                      className="iv-card"
                      style={{ borderLeftColor: `var(--iv-${preset.color})` }}
                    >
                      <div className="top">
                        <span className="nm">{preset.name}</span>
                        <span>
                          <button
                            type="button"
                            className="close-x"
                            title="Remove"
                            aria-label={`Remove ${preset.name}`}
                            onClick={() => removeIntervention(key)}
                          >
                            ×
                          </button>
                        </span>
                      </div>
                      <div className="meta">
                        {preset.meta(startLabel).map((m) => (
                          <span key={m.k}>
                            {m.k} <b>{m.v}</b> {m.badge ? <Badge kind={m.badge} /> : null}
                          </span>
                        ))}
                      </div>
                      <div className="sci-only sci-note">{preset.sci}</div>
                    </div>
                  );
                })
              )}
            </div>
            <button
              type="button"
              className="iv-add"
              aria-expanded={pickerOpen}
              onClick={() => setPickerOpen((v) => !v)}
            >
              + Add intervention
            </button>
            <div
              className={`iv-picker${pickerOpen ? ' open' : ''}`}
              role="group"
              aria-label="Intervention families"
            >
              {IV_PICKER.map((opt) => (
                <button
                  key={opt.key}
                  type="button"
                  className="iv-opt"
                  onClick={() => addIntervention(opt.key)}
                >
                  <span className="nm">
                    <i style={{ background: `var(--iv-${IV_PRESETS[opt.key].color})` }} />
                    {opt.label}
                  </span>
                  <span className="d">{opt.desc}</span>
                </button>
              ))}
            </div>
          </Card>

          {/* ---------------- travel ---------------- */}
          <Card className="b-card">
            <div className="head">
              <h2>Travel &amp; visitors</h2>
            </div>
            <div className="b-row">
              <Seg
                options={TRAVEL_OPTIONS}
                value={state.travel}
                onChange={(travel) => setState((s) => ({ ...s, travel }))}
                label="Travel mode"
              />
              <span className="desc">
                Airport &amp; ferry arrivals, visitors and returning residents at observed 2025
                annual volumes with seasonal profile.
              </span>
            </div>
            <Adv summary="Travel detail">
              <div className="adv-grid">
                <AdvItem
                  name="Annual air arrivals"
                  value={nf.format(720_842)}
                  badge={<Badge kind="observed" />}
                />
                <AdvItem
                  name="Annual ferry arrivals"
                  value={nf.format(196_623)}
                  badge={<Badge kind="observed" />}
                />
                <AdvItem
                  name="Monthly seasonality"
                  value="Summer-peaked"
                  mono={false}
                  badge={<Badge kind="assumption" />}
                />
                <AdvItem
                  name="Visitor composition"
                  value="Default mix"
                  mono={false}
                  badge={<Badge kind="assumption" />}
                />
              </div>
            </Adv>
          </Card>

          {/* ---------------- uncertainty ---------------- */}
          <Card className="b-card">
            <div className="head">
              <h2>Uncertainty</h2>
            </div>
            <div className="b-row">
              <Seg
                options={UNCERTAINTY_OPTIONS}
                value={state.uncertainty}
                onChange={(uncertainty) => setState((s) => ({ ...s, uncertainty }))}
                label="Run type"
              />
              <span className="desc">
                An ensemble shows the spread across stochastic replicates instead of one path.
              </span>
            </div>
          </Card>

          <Adv summary="Advanced — route multipliers, observation model, seeds">
            <p className="desc" style={{ marginTop: 8 }}>
              Per-route contact multipliers (11 resident + 7 travel routes), detection &amp;
              reporting assumptions, and explicit replicate seeds. All values carry provenance
              labels.
            </p>
          </Adv>
        </div>

        {/* ---------------- summary rail ---------------- */}
        <aside className="b-side">
          <Card className="b-summary">
            <h2>This scenario</h2>
            <div className="li">
              <span className="k">Population</span>
              <span className="v">
                {POPULATION_NAME[state.population]} · {nf.format(presets[state.population])}
              </span>
            </div>
            <div className="li">
              <span className="k">Disease</span>
              <span className="v">Generic respiratory</span>
            </div>
            <div className="li">
              <span className="k">Starts</span>
              <span className="v">
                {dayMonthYear(state.startDate)} · {state.seeded} seeded
              </span>
            </div>
            <div className="li">
              <span className="k">Duration</span>
              <span className="v num">{state.duration} days</span>
            </div>
            <div className="li">
              <span className="k">Interventions</span>
              <span className="v">{ivNames.length ? ivNames.join(', ') : 'None'}</span>
            </div>
            <div className="li">
              <span className="k">Travel</span>
              <span className="v">{TRAVEL_LABEL[state.travel]}</span>
            </div>
            <div className="li">
              <span className="k">Uncertainty</span>
              <span className="v">
                {state.uncertainty === 'ensemble'
                  ? `Ensemble · ${ENSEMBLE_SEEDS.length} seeds`
                  : 'Single run'}
              </span>
            </div>
            <hr className="divider" style={{ margin: '10px 0' }} />
            <div className="li sci-only f">
              <span className="k">Mode / seeds</span>
              <span className="v mono" style={{ fontSize: 11 }}>
                {state.population} ·{' '}
                {state.uncertainty === 'ensemble' ? ENSEMBLE_SEEDS.join(',') : String(BASE_SEED)}
              </span>
            </div>
            <div className="li sci-only f">
              <span className="k">Engine</span>
              <span className="v mono" style={{ fontSize: 11 }}>
                {engineLine}
              </span>
            </div>

            <div
              className={`valid-note${
                validation.status === 'valid'
                  ? ''
                  : validation.status === 'checking' || validation.status === 'idle'
                    ? ' checking'
                    : ' bad'
              }`}
              role="status"
            >
              {validation.status === 'valid' ? (
                <>✓&nbsp; Scenario valid — checked as you edit</>
              ) : validation.status === 'checking' || validation.status === 'idle' ? (
                <>·&nbsp; Checking scenario…</>
              ) : (
                <>!&nbsp; {validation.message}</>
              )}
            </div>
            {validation.hash && (
              <div className="hash-line mono">scenario {shortHash(validation.hash)}</div>
            )}
            <Btn
              variant="primary"
              big
              style={{ marginTop: 14 }}
              disabled={!canRun}
              aria-disabled={!canRun}
              onClick={() => void run()}
            >
              {submitting ? 'Submitting…' : 'Run simulation'}
            </Btn>
            <p className="runtime-note">
              Runs in the background on this machine. Full Jersey and ensembles take longer than
              this quick baseline — you can keep working and will find it under <b>Runs</b>.
            </p>
          </Card>
        </aside>
      </div>
    </section>
  );
}
