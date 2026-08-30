/**
 * Compare — two matched-seed arms of a `scenario_compare` job.
 *
 * Layout follows the M10 design (§6): delta cards → paired epicurve + route
 * shifts on the left, comparison map + intervention burden on the right, and
 * the permanent claim-boundary footnote.
 */

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../../api';
import type { JobStatusResponse } from '../../api/types';
import { Btn } from '../../components/Btn';
import { Card } from '../../components/Card';
import { Chip } from '../../components/Chip';
import { JerseyMap } from '../../components/JerseyMap';
import { LineChart } from '../../components/LineChart';
import { Seg } from '../../components/Seg';
import { useScenarioContextEffect } from '../../app/ScenarioContextProvider';
import { divColor, seqColor, type ParishId } from '../../map/geometry';
import { setProvenanceJobId } from '../drawer/provenanceStore';
import {
  fmt,
  formatDay,
  loadCompare,
  peakIndex,
  signed,
  signedPct,
  type CompareModel,
} from './compareData';
import './compare.css';

type MapMode = 'a' | 'b' | 'diff';

const MAP_MODES: Array<{ value: MapMode; label: string }> = [
  { value: 'a', label: 'Baseline' },
  { value: 'b', label: 'Intervention' },
  { value: 'diff', label: 'Difference' },
];

const FOOTNOTE_LEAD = 'These are simulated differences under the declared model assumptions';

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
            setError(`Job ${jobId} is a ${j.kind}, not a comparison.`);
            setJob(null);
          } else if (j.state !== 'SUCCEEDED') {
            setError(`Comparison ${jobId} has not finished (state ${j.state}).`);
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
  const [mapMode, setMapMode] = useState<MapMode>('diff');

  useEffect(() => {
    if (!job) {
      setModel(null);
      return;
    }
    let cancelled = false;
    setDataError(null);
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
          kindDetail: model?.seeds.length ? `${model.seeds.length} matched seeds` : undefined,
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

  if (!job) {
    return <CompareEmpty reason={error} />;
  }

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

  return <CompareBody model={model} mapMode={mapMode} setMapMode={setMapMode} />;
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
          <p>
            Build a scenario, add the measures you want to test, and submit it as a comparison run.
          </p>
          <div className="cmp-empty-actions">
            <Btn to="/simulate" variant="primary">
              New scenario
            </Btn>
            <Btn to="/runs">Browse runs</Btn>
          </div>
        </Card>
      </div>
    </section>
  );
}

/* ================================ body ================================ */

function CompareBody({
  model,
  mapMode,
  setMapMode,
}: {
  model: CompareModel;
  mapMode: MapMode;
  setMapMode: (m: MapMode) => void;
}) {
  const last = model.days - 1;
  const banded = Boolean(model.baseline.activeBand && model.treated.activeBand);

  const cumBase = model.baseline.cumulative[last] ?? null;
  const cumTreated = model.treated.cumulative[last] ?? null;
  const cumDelta = cumBase != null && cumTreated != null ? cumTreated - cumBase : null;
  const cumPct = cumDelta != null && cumBase ? (100 * cumDelta) / cumBase : null;

  const peakBaseIdx = peakIndex(model.baseline.active);
  const peakTreatIdx = peakIndex(model.treated.active);
  const peakBase = peakBaseIdx >= 0 ? model.baseline.active[peakBaseIdx] : null;
  const peakTreat = peakTreatIdx >= 0 ? model.treated.active[peakTreatIdx] : null;
  const peakDelta = peakBase != null && peakTreat != null ? peakTreat - peakBase : null;
  const peakPct = peakDelta != null && peakBase ? (100 * peakDelta) / peakBase : null;
  const peakShift = peakBaseIdx >= 0 && peakTreatIdx >= 0 ? peakTreatIdx - peakBaseIdx : null;

  const arBase = model.baseline.attack[last] != null ? model.baseline.attack[last] * 100 : null;
  const arTreated = model.treated.attack[last] != null ? model.treated.attack[last] * 100 : null;
  const arDelta = arBase != null && arTreated != null ? arTreated - arBase : null;

  const chart = useMemo(
    () => [
      {
        pts: model.baseline.active.flatMap((v, d) => v == null ? [] : [[d, v] as [number, number]]),
        cls: 'base',
        band: model.baseline.activeBand
          ? {
              low: model.baseline.activeBand.low.flatMap((v, d) => v == null ? [] : [[d, v] as [number, number]]),
              high: model.baseline.activeBand.high.flatMap((v, d) => v == null ? [] : [[d, v] as [number, number]]),
            }
          : undefined,
      },
      {
        pts: model.treated.active.flatMap((v, d) => v == null ? [] : [[d, v] as [number, number]]),
        band: model.treated.activeBand
          ? {
              low: model.treated.activeBand.low.flatMap((v, d) => v == null ? [] : [[d, v] as [number, number]]),
              high: model.treated.activeBand.high.flatMap((v, d) => v == null ? [] : [[d, v] as [number, number]]),
            }
          : undefined,
      },
    ],
    [model, banded],
  );

  const topRoutes = model.routes.slice(0, 6);
  const routeMax = Math.max(...topRoutes.flatMap((r) => [r.base, r.treated]), 1);

  const parishById = useMemo(
    () => new Map(model.parishes.map((p) => [p.id, p])),
    [model.parishes],
  );
  const parishCeiling = Math.max(...model.parishes.map((p) => p.base), 1) * 1.05;

  const colorFor = (id: ParishId): string => {
    const p = parishById.get(id);
    if (!p) return 'var(--panel-2)';
    if (mapMode === 'a') return seqColor(Math.min(0.999, p.base / parishCeiling));
    if (mapMode === 'b') return seqColor(Math.min(0.999, p.treated / parishCeiling));
    if (!p.base) return 'var(--panel-2)';
    const rel = (p.treated - p.base) / p.base;
    return divColor(Math.min(0.999, Math.max(0, (rel + 0.3) / 0.6)));
  };

  const mapTitle =
    mapMode === 'diff'
      ? 'Difference in cumulative infections by parish'
      : mapMode === 'a'
        ? 'Baseline — cumulative infections by parish'
        : 'Intervention — cumulative infections by parish';

  return (
    <section className="view view-compare">
      <div className="wrap">
        <div className="cmp-head">
          <h1>Compare scenarios</h1>
          <div className="cmp-vs">
            <span className="pill">{model.baselineName}</span>
            <span style={{ color: 'var(--ink-3)' }}>vs</span>
            <span className="pill b">{model.treatedName}</span>
            <Chip className="kind">
              {model.seeds.length
                ? `Matched seeds ×${model.seeds.length}`
                : 'Matched-seed comparison'}
            </Chip>
          </div>
          <span style={{ flex: 1 }} />
          <Btn to="/runs">Change runs</Btn>
        </div>

        <div className="deltas">
          <Card className="delta-card">
            <div className="k">Cumulative infections</div>
              <div className={`v ${cumDelta != null && cumDelta < 0 ? 'down' : 'up'}`}>
              {cumDelta == null ? '—' : signed(cumDelta)} <span className="pct">{cumPct == null ? 'not available' : signedPct(cumPct)}</span>
            </div>
            <div className="s">
              {cumBase == null || cumTreated == null ? 'Cumulative values are not published for both arms.' : `${fmt(cumBase)} → ${fmt(cumTreated)} by day ${last}`}
            </div>
          </Card>

          <Card className="delta-card">
            <div className="k">Peak infectious</div>
            <div className={`v ${peakDelta != null && peakDelta < 0 ? 'down' : 'up'}`}>
              {peakPct == null ? '—' : signedPct(peakPct, 0)} <span className="pct">{peakDelta == null ? 'not available' : signed(peakDelta)}</span>
            </div>
            <div className="s">
              {peakBase == null || peakTreat == null ? 'Active infectious state is not published by both arms.' : `${fmt(peakBase)} → ${fmt(peakTreat)} residents`}
            </div>
          </Card>

          <Card className="delta-card">
            <div className="k">Peak date</div>
            <div className="v">
              {peakShift == null
                ? '—'
                : peakShift === 0
                ? 'unchanged'
                : `${peakShift > 0 ? '+' : '−'}${Math.abs(peakShift)} day${
                    Math.abs(peakShift) === 1 ? '' : 's'
                  }`}
            </div>
            <div className="s">
              {peakShift == null ? 'Peak date is not available for both arms.' : `${formatDay(model.startDate, peakBaseIdx)} → ${formatDay(model.startDate, peakTreatIdx)}`}
            </div>
          </Card>

          <Card className="delta-card">
            <div className="k">Attack rate</div>
            <div className={`v ${arDelta != null && arDelta < 0 ? 'down' : 'up'}`}>
              {arDelta == null ? '—' : `${arDelta < 0 ? '−' : '+'}${Math.abs(arDelta).toFixed(1)} pts`}
            </div>
            <div className="s">
              {arBase == null || arTreated == null ? 'Attack rate is not published for both arms.' : `${arBase.toFixed(1)}% → ${arTreated.toFixed(1)}% of residents`}
            </div>
          </Card>
        </div>

        <div className="cmp-grid">
          <div>
            <Card style={{ padding: '16px 18px' }}>
              <div className="chart-head">
                <h3>Active infectious — both scenarios</h3>
                <span className="legend">
                  <span>
                    <span className="sw" style={{ background: 'var(--ink-3)' }} />
                    Baseline
                  </span>
                  <span>
                    <span className="sw" style={{ background: 'var(--accent)' }} />
                    Intervention
                  </span>
                  {banded && (
                    <span>
                      <span className="swb" style={{ background: 'var(--band)' }} />
                      Replicate range
                    </span>
                  )}
                </span>
              </div>
              <LineChart series={chart} days={model.days} height={220} width={660} />
            </Card>

            <Card style={{ padding: '16px 18px', marginTop: 16 }}>
              <div className="chart-head">
                <h3>Route shifts — cumulative infections by route</h3>
                <span className="chart-note">
                  Absolute change; shares can rise while counts fall
                </span>
              </div>
              {topRoutes.length === 0 ? (
                <div className="cmp-note">This job serves no per-route table.</div>
              ) : (
                <div className="drv">
                  {topRoutes.map((r) => {
                    const d = r.treated - r.base;
                    const pct = r.base ? (100 * d) / r.base : null;
                    return (
                      <div className="drv-row cmp-route-row" key={r.routeId}>
                        <span className="nm" title={r.name}>
                          {r.name}
                          <small className="mono sci-only" style={{ color: 'var(--ink-3)', fontSize: 10 }}>
                            {' '}
                            {r.routeId}
                          </small>
                        </span>
                        <span
                          className="bar"
                          style={{ height: 12 }}
                          title={`Baseline ${fmt(r.base)} · intervention ${fmt(r.treated)}`}
                        >
                          {/* Longest bar first, so the shorter arm stays visible. */}
                          {[
                            {
                              key: 'base',
                              value: r.base,
                              style: { background: 'var(--ink-3)', opacity: 0.35 },
                            },
                            {
                              key: 'treated',
                              value: r.treated,
                              style: { background: 'var(--accent)' },
                            },
                          ]
                            .sort((a, b) => b.value - a.value)
                            .map((bar) => (
                              <i
                                key={bar.key}
                                style={{
                                  width: `${(100 * bar.value) / routeMax}%`,
                                  ...bar.style,
                                }}
                              />
                            ))}
                        </span>
                        <span className={`val ${d < 0 ? 'down' : 'up'}`}>
                          {signed(d)} <small>({pct == null ? 'not available' : `${pct.toFixed(0)}%`})</small>
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </Card>
          </div>

          <div>
            <div className="cmp-map-card mapground">
              <div className="cmp-map-head">
                <span style={{ fontWeight: 650, fontSize: 13 }}>{mapTitle}</span>
                  {model.parishes.length > 0 && (
                    <Seg
                      options={MAP_MODES}
                      value={mapMode}
                      onChange={setMapMode}
                      label="Map mode"
                      title="Which arm the choropleth shows"
                    />
                  )}
              </div>
              {model.parishes.length === 0 ? (
                <div className="cmp-note">This job serves no per-parish table.</div>
              ) : (
                <JerseyMap
                  colorFor={colorFor}
                  ariaLabel={mapTitle}
                  scalebar
                />
              )}
              <div
                className="map-legend"
                style={{ visibility: mapMode === 'diff' ? 'visible' : 'hidden' }}
              >
                <span>Fewer under intervention</span>
                <span className="bins">
                  {['--div-neg', '--div-neg-soft', '--div-mid', '--div-pos-soft', '--div-pos'].map(
                    (v) => (
                      <span className="bin" key={v} style={{ background: `var(${v})` }} />
                    ),
                  )}
                </span>
                <span>More</span>
              </div>
            </div>

            <Card style={{ padding: '16px 18px', marginTop: 16 }}>
              <h3 style={{ fontSize: 13.5, fontWeight: 650 }}>Intervention burden</h3>
              <div className="burden">
                {model.burden.map((b) => (
                  <div className="li" key={b.label}>
                    <span className="k">{b.label}</span>
                    <span
                      className="v"
                      style={b.placeholder ? { color: 'var(--ink-3)', fontWeight: 500 } : undefined}
                    >
                      {b.value}
                    </span>
                  </div>
                ))}
              </div>
              <p className="cmp-note" style={{ marginTop: 12 }}>
                Burden is reported separately from health outcomes. Agent-days, setting-days and
                doses need an intervention-burden dataset, which this job does not publish.
              </p>
            </Card>
          </div>
        </div>

        <p className="cmp-footnote">
          <b>{FOOTNOTE_LEAD}</b> — matched-seed runs of a synthetic population using the declared
          intervention mechanics. They are not predictions of real policy effectiveness in Jersey.
      </p>
      </div>
    </section>
  );
}
