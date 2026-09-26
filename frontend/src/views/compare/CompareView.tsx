/** Compare two matched-seed arms from a `scenario_compare` job. */

import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../../api';
import type { JobStatusResponse } from '../../api/types';
import { Btn } from '../../components/Btn';
import { Card } from '../../components/Card';
import { Chip } from '../../components/Chip';
import { JerseyMap } from '../../components/JerseyMap';
import {
  getLineChartRenderedContent,
  lineSeriesColor,
  LineChart,
} from '../../components/LineChart';
import { useScenarioContextEffect } from '../../app/ScenarioContextProvider';
import { divColor, OSM_ATTRIBUTION, PARISHES, seqColor, type ParishId } from '../../map/geometry';
import { setProvenanceJobId } from '../drawer/provenanceStore';
import {
  fmt,
  formatDate,
  formatDay,
  loadCompare,
  metricDateLabel,
  peakIndex,
  percentDifference,
  signed,
  signedPct,
  type CompareModel,
} from './compareData';
import './compare.css';

const COMPARE_FOOTNOTE = 'These are simulated differences under the declared model assumptions — matched-seed runs of a synthetic population using the declared intervention mechanics. They are not predictions of real policy effectiveness in Jersey.';
const FOOTNOTE_LEAD = 'These are simulated differences under the declared model assumptions';

type ChangeTone = 'negative' | 'positive' | 'neutral';

function toneFor(value: number | null): ChangeTone {
  if (value == null || value === 0) return 'neutral';
  return value < 0 ? 'negative' : 'positive';
}

function ChangeCard({
  label,
  value,
  tone,
  detail,
}: {
  label: string;
  value: string;
  tone: ChangeTone;
  detail: string;
}) {
  return (
    <Card className="delta-card">
      <div className="delta-rule" />
      <div className="delta-label">{label}</div>
      <div className={'delta-value ' + tone}>{value}</div>
      <div className="delta-detail mono">{detail}</div>
    </Card>
  );
}

/* ============================ job resolution ============================ */

function useCompareJob(jobId: string | undefined) {
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    (async () => {
      try {
        if (jobId) {
          const j = await api.getJob(jobId);
          if (cancelled) return;
          if (j.kind !== 'scenario_compare') {
            setError('Job ' + jobId + ' is a ' + j.kind + ', not a comparison.');
            setJob(null);
          } else if (j.state !== 'SUCCEEDED') {
            setError('Comparison ' + jobId + ' has not finished (state ' + j.state + ').');
            setJob(null);
          } else {
            setJob(j);
          }
          return;
        }
        const res = await api.listJobs({ kind: 'scenario_compare', state: 'SUCCEEDED', limit: 50 });
        if (cancelled) return;
        const newest = [...res.jobs].sort((a, b) =>
          (b.finished_at ?? b.created_at).localeCompare(a.finished_at ?? a.created_at),
        )[0];
        setJob(newest ?? null);
        if (!newest) setError('empty');
      } catch (e) {
        if (!cancelled) {
          setJob(null);
          setError(e instanceof Error ? e.message : 'Could not load the comparison.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
      setProvenanceJobId(null);
    };
  }, [jobId]);

  return { job, error, loading };
}

/* ============================== the view ============================== */

export function CompareView() {
  const { jobId } = useParams<{ jobId?: string }>();
  const { job, error, loading } = useCompareJob(jobId);
  const [model, setModel] = useState<CompareModel | null>(null);
  const [dataError, setDataError] = useState<string | null>(null);

  useEffect(() => {
    if (!job) {
      setModel(null);
      return;
    }
    let cancelled = false;
    setDataError(null);
    setModel(null);
    setProvenanceJobId(job.job_id);
    loadCompare(job)
      .then((m) => {
        if (!cancelled) setModel(m);
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setModel(null);
          setDataError(e instanceof Error ? e.message : 'Could not read the comparison datasets.');
        }
      });
    return () => {
      cancelled = true;
    };
  }, [job]);

  useScenarioContextEffect(
    job
      ? {
          name: model?.treatedName ?? 'Comparison',
          kind: 'scenario_compare',
          kindDetail: model?.seeds.length ? model.seeds.length + ' matched seeds' : undefined,
          state: job.state,
          jobId: job.job_id,
        }
      : null,
  );

  if (loading) {
    return (
      <section className="view view-compare">
        <div className="wrap">
          <div className="cmp-loading">Loading comparison…</div>
        </div>
      </section>
    );
  }

  if (!job) return <CompareEmpty reason={error} />;

  if (dataError) {
    return (
      <section className="view view-compare">
        <div className="wrap">
          <Card className="cmp-empty">
            <h1>Comparison datasets unavailable</h1>
            <p>{dataError}</p>
            <Btn to="/runs">Open runs</Btn>
          </Card>
        </div>
      </section>
    );
  }

  if (!model) {
    return (
      <section className="view view-compare">
        <div className="wrap">
          <div className="cmp-loading">Reading comparison datasets…</div>
        </div>
      </section>
    );
  }

  return <CompareBody model={model} />;
}

/* ============================== empty state ============================== */

function CompareEmpty({ reason }: { reason: string | null }) {
  const specific = reason && reason !== 'empty' ? reason : null;
  return (
    <section className="view view-compare">
      <div className="wrap">
        <Card className="cmp-empty">
          <h1>Nothing to compare yet</h1>
          <p>
            {specific ??
              'Comparison is its own job kind: both arms are re-run against the same seeds so the ' +
                'difference is attributable to the intervention, not to sampling noise.'}
          </p>
          <p>Build a scenario, add the measures you want to test, and submit it as a comparison run.</p>
          <div className="cmp-empty-actions">
            <Btn to="/simulate" variant="primary">New scenario</Btn>
            <Btn to="/runs">Browse runs</Btn>
          </div>
        </Card>
      </div>
    </section>
  );
}

/* ================================ body ================================ */

function CompareBody({ model }: { model: CompareModel }) {
  const [day, setDay] = useState(Math.max(0, model.days - 1));
  const lastDay = Math.max(0, model.days - 1);
  const selectedDay = Math.min(day, lastDay);

  const cumulative = model.comparisonMetrics.cumulative;
  const cumBase = cumulative.baseline;
  const cumTreated = cumulative.treated;
  const cumDelta = cumulative.delta;
  const cumPct = percentDifference(cumBase, cumTreated);

  const peakBaseIdx = peakIndex(model.baseline.active);
  const peakTreatIdx = peakIndex(model.treated.active);
  const peakBase = peakBaseIdx >= 0 ? model.baseline.active[peakBaseIdx] : null;
  const peakTreat = peakTreatIdx >= 0 ? model.treated.active[peakTreatIdx] : null;
  const peakDelta = peakBase != null && peakTreat != null ? peakTreat - peakBase : null;
  const peakPct = peakDelta != null && peakBase ? (100 * peakDelta) / peakBase : null;
  const peakShift = peakBaseIdx >= 0 && peakTreatIdx >= 0 ? peakTreatIdx - peakBaseIdx : null;

  const attack = model.comparisonMetrics.attack;
  const arBase = attack.baseline != null ? attack.baseline * 100 : null;
  const arTreated = attack.treated != null ? attack.treated * 100 : null;
  const arDelta = attack.delta != null ? attack.delta * 100 : null;

  const chart = useMemo(
    () => [
      {
        label: 'Baseline',
        pts: model.baseline.active.flatMap((value, index) =>
          value == null ? [] : [[index, value] as [number, number]],
        ),
        role: 'baseline' as const,
        cls: 'base',
        band: model.baseline.activeBand
          ? {
              low: model.baseline.activeBand.low.flatMap((value, index) =>
                value == null ? [] : [[index, value] as [number, number]],
              ),
              high: model.baseline.activeBand.high.flatMap((value, index) =>
                value == null ? [] : [[index, value] as [number, number]],
              ),
            }
          : undefined,
      },
      {
        label: 'Intervention',
        pts: model.treated.active.flatMap((value, index) =>
          value == null ? [] : [[index, value] as [number, number]],
        ),
        role: 'intervention' as const,
        cls: 'treated',
        band: model.treated.activeBand
          ? {
              low: model.treated.activeBand.low.flatMap((value, index) =>
                value == null ? [] : [[index, value] as [number, number]],
              ),
              high: model.treated.activeBand.high.flatMap((value, index) =>
                value == null ? [] : [[index, value] as [number, number]],
              ),
            }
          : undefined,
      },
    ],
    [model],
  );
  const chartContent = getLineChartRenderedContent(chart, true);

  const routes = model.routes.slice(0, 6);
  const maxShift = Math.max(...routes.map((route) => Math.abs(route.treated - route.base)), 1);
  const parishById = useMemo(
    () => new Map(model.parishes.map((parish) => [parish.id, parish])),
    [model.parishes],
  );
  const parishCeiling = Math.max(...model.parishes.flatMap((parish) => [parish.base, parish.treated]), 1);
  const seedText = model.seeds.length
    ? 'matched seeds ×' + model.seeds.length
    : 'matched-seed comparison';
  const populationText = model.population == null
    ? 'population not published'
    : fmt(model.population) + ' residents';
  const chartKey = model.job.job_id + ':' + model.days + ':' + model.latestDate + ':' + JSON.stringify([
    model.baseline.active,
    model.treated.active,
  ]);

  const armColor = (arm: 'base' | 'treated', id: ParishId): string => {
    const parish = parishById.get(id);
    if (!parish) return 'var(--panel-2)';
    return seqColor(Math.min(0.999, parish[arm] / parishCeiling));
  };
  const differenceColor = (id: ParishId): string => {
    const parish = parishById.get(id);
    if (!parish) return 'var(--panel-2)';
    if (parish.base === 0) return divColor(parish.treated === 0 ? 0.5 : 1);
    const relative = (parish.treated - parish.base) / parish.base;
    return divColor((Math.min(0.3, Math.max(-0.3, relative)) + 0.3) / 0.6);
  };

  const parishDifference = (parish: CompareModel['parishes'][number]): string =>
    signed(parish.treated - parish.base);
  const parishDifferenceTooltip = (id: ParishId): string => {
    const name = PARISHES.find((parish) => parish.id === id)?.name ?? id;
    const parish = parishById.get(id);
    if (!parish || !Number.isFinite(parish.base) || !Number.isFinite(parish.treated)) {
      return `${name}: infection count difference unavailable (intervention − baseline)`;
    }
    const difference = parish.treated - parish.base;
    const magnitude = Number.isInteger(difference)
      ? Math.abs(difference).toLocaleString('en-GB')
      : Math.abs(difference).toLocaleString('en-GB', { maximumSignificantDigits: 21 });
    const count = `${difference < 0 ? '−' : '+'}${magnitude}`;
    const countText = `${name}: ${count} ${Math.abs(difference) === 1 ? 'infection' : 'infections'} (intervention − baseline)`;
    const population = PARISHES.find((candidate) => candidate.id === id)?.pop;
    if (population == null || population <= 0) return countText;

    const perThousand = (difference * 1000) / population;
    const rateMagnitude = difference === 0
      ? '0'
      : Math.abs(perThousand).toLocaleString('en-GB', { maximumSignificantDigits: 2 });
    const rate = `${perThousand < 0 ? '−' : '+'}${rateMagnitude}`;
    return `${countText} · ${rate} per 1,000 (parish population)`;
  };

  return (
    <section className="view view-compare">
      <div className="wrap">
        <header className="cmp-header">
          <div className="cmp-eyebrow">Scenario comparison · {seedText} · {populationText}</div>
          <div className="cmp-header-main">
            <div className="cmp-title-group">
              <h1>What changes with {model.treatedName}?</h1>
              <div className="cmp-arm-pills" aria-label="Compared scenarios">
                <span className="cmp-arm-pill baseline" title={'Baseline: ' + model.baselineName}>
                  <span>Baseline</span>{model.baselineName}
                </span>
                <span className="cmp-arm-pill intervention" title={'Intervention: ' + model.treatedName}>
                  <span>Intervention</span>{model.treatedName}
                </span>
              </div>
            </div>
            <div className="cmp-header-actions">
              <Chip className="kind">{model.seeds.length ? 'Matched seeds ×' + model.seeds.length : 'Matched-seed comparison'}</Chip>
              <span className="cmp-date-note">Latest comparison date: {formatDate(model.latestDate)}</span>
              <Btn to="/runs">Change runs</Btn>
            </div>
          </div>
        </header>

        <div className="deltas">
          <ChangeCard
            label="Cumulative infections"
            value={cumDelta == null ? '—' : cumDelta === 0 ? '0' : signed(cumDelta)}
            tone={toneFor(cumDelta)}
            detail={cumBase == null || cumTreated == null
              ? 'Unavailable · ' + metricDateLabel(cumulative)
              : fmt(cumBase) + ' → ' + fmt(cumTreated) + ' · ' + (cumPct == null ? 'percent unavailable' : signedPct(cumPct))}
          />
          <ChangeCard
            label="Peak active infectious"
            value={peakDelta == null ? '—' : peakDelta === 0 ? '0' : signed(peakDelta)}
            tone={toneFor(peakDelta)}
            detail={peakBase == null || peakTreat == null
              ? 'Active infectious state is not published by both arms.'
              : fmt(peakBase) + ' → ' + fmt(peakTreat) + ' residents' + (peakPct == null ? '' : ' · ' + signedPct(peakPct, 0))}
          />
          <ChangeCard
            label="Peak date shift"
            value={peakShift == null
              ? '—'
              : peakShift === 0
                ? 'unchanged'
                : (peakShift < 0 ? '−' : '+') + Math.abs(peakShift) + ' day' + (Math.abs(peakShift) === 1 ? '' : 's')}
            tone={toneFor(peakShift)}
            detail={peakShift == null
              ? 'Peak date is not available for both arms.'
              : 'Baseline ' + formatDay(model.startDate, peakBaseIdx) + ' · intervention ' + formatDay(model.startDate, peakTreatIdx)}
          />
          <ChangeCard
            label="Ever infected"
            value={arDelta == null
              ? '—'
              : arDelta === 0
                ? '0.0 pp'
                : (arDelta < 0 ? '−' : '+') + Math.abs(arDelta).toFixed(1) + ' pp'}
            tone={toneFor(arDelta)}
            detail={arBase == null || arTreated == null
              ? 'Unavailable · ' + metricDateLabel(attack)
              : arBase.toFixed(1) + '% → ' + arTreated.toFixed(1) + '% · ' + metricDateLabel(attack)}
          />
        </div>

        <div className="cmp-grid">
          <div className="cmp-left-column">
            <Card className="cmp-chart-panel">
              <div className="cmp-panel-head">
                <div>
                  <div className="cmp-section-kicker">Tide gauge</div>
                  <h2>Active infectious over time</h2>
                </div>
                <div className="cmp-chart-legend" aria-label="Chart legend">
                  {chartContent.series.map((item) => (
                    <span key={item.label}><i className={`cmp-line-swatch ${item.role}`} style={{ background: lineSeriesColor(item) }} />{item.label}</span>
                  ))}
                </div>
              </div>
              <div className="cmp-area-legend">
                {chartContent.comparisonAreas.some((area) => !area.positive) && (
                  <span><i className="cmp-area-swatch fewer" />infections averted (simulated)</span>
                )}
                {chartContent.comparisonAreas.some((area) => area.positive) && (
                  <span><i className="cmp-area-swatch more" />added (simulated)</span>
                )}
                {chartContent.bands.length > 0 && (
                  <span><i className="cmp-band-swatch" />Replicate range</span>
                )}
              </div>
              <div className="cmp-day-control">
                <label htmlFor="cmp-day-slider">
                  <span className="cmp-selected-day">Day {selectedDay}</span>
                  <span>{formatDay(model.startDate, selectedDay)}</span>
                </label>
                <input
                  id="cmp-day-slider"
                  type="range"
                  min={0}
                  max={lastDay}
                  value={selectedDay}
                  aria-label="Comparison day"
                  onChange={(event) => setDay(Number(event.target.value))}
                />
                <div className="cmp-date-range mono">
                  <span>{formatDate(model.startDate)}</span>
                  <span>{formatDate(model.latestDate)}</span>
                </div>
              </div>
              <LineChart
                key={chartKey}
                series={chart}
                marker={selectedDay}
                days={model.days}
                height={188}
                width={560}
                comparisonAreas
                formatDay={(index) => formatDay(model.startDate, index)}
                className="cmp-tide-chart"
              />
            </Card>

            <Card className="cmp-route-panel">
              <div className="cmp-panel-head cmp-route-head">
                <div>
                  <div className="cmp-section-kicker">Transmission routes</div>
                  <h2>Route shifts</h2>
                </div>
                <span className="cmp-panel-note">Intervention − baseline infections</span>
              </div>
              {routes.length === 0 ? (
                <div className="cmp-note">This job serves no per-route table.</div>
              ) : (
                <div className="cmp-routes">
                  {routes.map((route) => {
                    const change = route.treated - route.base;
                    const width = (50 * Math.abs(change)) / maxShift;
                    const tone = toneFor(change);
                    return (
                      <div className="cmp-route-row" key={route.routeId}>
                        <span className="cmp-route-name" title={route.name}>{route.name}
                          <small className="mono sci-only">{route.routeId}</small>
                        </span>
                        <span className="cmp-div-track" title={'Baseline ' + fmt(route.base) + ' · intervention ' + fmt(route.treated)}>
                          <i className="cmp-div-center" />
                          {change < 0 && <i className="cmp-div-bar negative" style={{ right: '50%', width: width + '%' }} />}
                          {change > 0 && <i className="cmp-div-bar positive" style={{ left: '50%', width: width + '%' }} />}
                        </span>
                        <span className={'cmp-route-value ' + tone}>
                          {change === 0 ? '0' : signed(change)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
              <p className="cmp-route-note">Absolute change; route shares can rise while counts fall.</p>
            </Card>
          </div>

          <div className="cmp-right-column">
            <div className="cmp-map-grid">
              <MapPanel title="Baseline" subtitle="Cumulative infections by parish">
                <JerseyMap
                  colorFor={(id) => armColor('base', id)}
                  ariaLabel="Baseline cumulative infections by parish"
                  scalebar={false}
                />
              </MapPanel>
              <MapPanel title="Intervention" subtitle="Cumulative infections by parish">
                <JerseyMap
                  colorFor={(id) => armColor('treated', id)}
                  ariaLabel="Intervention cumulative infections by parish"
                  scalebar={false}
                />
              </MapPanel>
              <MapPanel title="Difference" subtitle="Intervention − baseline">
                <JerseyMap
                  colorFor={differenceColor}
                  tooltipFor={parishDifferenceTooltip}
                  ariaLabel="Difference map: fewer, same, or more cumulative infections under intervention"
                  scalebar={false}
                />
              </MapPanel>
              <Card className="cmp-map-explanation">
                <div className="cmp-section-kicker">Difference scale</div>
                {model.parishes.length > 0 ? (
                  <>
                    <div className="cmp-sequential-label">Cumulative infections · episodes</div>
                    <div className="cmp-sequential-legend" aria-label="Fewer to more cumulative infections">
                      <span>Fewer</span>
                      <span className="cmp-sequential-bins">
                        {['--seq0', '--seq1', '--seq2', '--seq3', '--seq4', '--seq5'].map((token) => (
                          <i key={token} style={{ background: 'var(' + token + ')' }} />
                        ))}
                      </span>
                      <span>More</span>
                    </div>
                    <div className="cmp-scale-divider" />
                    <div className="cmp-difference-legend" aria-label="Fewer, same, more diverging scale">
                      <span>Fewer</span>
                      <span className="cmp-difference-bins">
                        {['--div-neg', '--div-neg-soft', '--div-mid', '--div-pos-soft', '--div-pos'].map((token) => (
                          <i key={token} style={{ background: 'var(' + token + ')' }} />
                        ))}
                      </span>
                      <span>More</span>
                    </div>
                    <div className="cmp-same-label">Same</div>
                    <p>Relative change in cumulative infections, capped at ±30%. Blue means fewer under intervention; orange means more.</p>
                    <div className="cmp-parish-differences" aria-label="Signed cumulative infection differences by parish">
                      {model.parishes.map((parish) => (
                        <span key={parish.id} title={parish.name + ': ' + parishDifference(parish) + ' infections under intervention'}>
                          {parish.name} <b className={toneFor(parish.treated - parish.base)}>{parishDifference(parish)}</b>
                        </span>
                      ))}
                    </div>
                  </>
                ) : (
                  <p className="cmp-no-parish-values">This job serves no per-parish table; infection differences are unavailable.</p>
                )}
                <div className="cmp-map-attribution">{OSM_ATTRIBUTION}</div>
              </Card>
            </div>

            <Card className="cmp-burden sci-only">
              <div className="cmp-section-kicker">Scientific mode</div>
              <h2>Intervention burden</h2>
              <div className="burden">
                {model.burden.map((item) => (
                  <div className="li" key={item.label}>
                    <span className="k">{item.label}</span>
                    <span className="v" style={item.placeholder ? { color: 'var(--ink-3)', fontWeight: 500 } : undefined}>
                      {item.value}
                    </span>
                  </div>
                ))}
              </div>
              <p className="cmp-note">Burden is reported separately from health outcomes. Agent-days, setting-days and doses need an intervention-burden dataset, which this job does not publish.</p>
            </Card>
          </div>
        </div>

        <p className="cmp-footnote">
          <b>{FOOTNOTE_LEAD}</b>{COMPARE_FOOTNOTE.slice(FOOTNOTE_LEAD.length)}
        </p>
      </div>
    </section>
  );
}

function MapPanel({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <Card className="cmp-map-card mapground">
      <div className="cmp-map-head">
        <h2>{title}</h2>
        <span>{subtitle}</span>
      </div>
      {children}
    </Card>
  );
}
