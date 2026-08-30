/**
 * Results workspace — the centerpiece view.
 *
 * One job's verified datasets are paged into memory once (see `data.ts`), then
 * a single `day` state drives every synchronized surface: the parish
 * choropleth, the headline metrics, the drivers/parish panel, the epicurve
 * marker, the intervention cursor and the travel stats. Nothing after the
 * initial load touches the network.
 */

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Btn,
  HBar,
  JerseyMap,
  LineChart,
  MetricTile,
  MetricTileGrid,
} from '../../components';
import type { HBarRow } from '../../components';
import { api } from '../../api';
import type { JobStatusResponse } from '../../api';
import { jobDisplayName, jobKindDetail } from '../../api/naming';
import { seqColor, type ParishId } from '../../map/geometry';
import { useScenarioContextEffect } from '../../app/ScenarioContextProvider';
import { TabsBand } from './TabsBand';
import { deriveInterventions, type InterventionBar } from './interventions';
import {
  MAP_METRICS,
  detectFizzle,
  fmt,
  formatDate,
  formatDateYear,
  loadResults,
  metricMax,
  parishMetricPer1k,
  routeCounts,
  type MapMetric,
  type ResultsData,
} from './data';
import './results.css';

const PLAY_INTERVAL_MS = 140;

/** Newest succeeded job, by finish time then creation time. */
function newestSucceeded(jobs: JobStatusResponse[]): JobStatusResponse | null {
  const done = jobs.filter((j) => j.state === 'SUCCEEDED');
  if (!done.length) return null;
  return [...done].sort((a, b) => {
    const at = Date.parse(a.finished_at ?? a.created_at);
    const bt = Date.parse(b.finished_at ?? b.created_at);
    return (Number.isNaN(bt) ? 0 : bt) - (Number.isNaN(at) ? 0 : at);
  })[0];
}

function isTyping(target: EventTarget | null): boolean {
  const el = target as HTMLElement | null;
  if (!el || !el.tagName) return false;
  return (
    el.tagName === 'INPUT' ||
    el.tagName === 'TEXTAREA' ||
    el.tagName === 'SELECT' ||
    el.isContentEditable
  );
}

export function ResultsView() {
  const { jobId } = useParams<{ jobId?: string }>();
  const navigate = useNavigate();

  const [data, setData] = useState<ResultsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [day, setDay] = useState(0);
  const [metric, setMetric] = useState<MapMetric>('active');
  const [parish, setParish] = useState<ParishId | null>(null);
  const [playing, setPlaying] = useState(false);
  const [showLabels, setShowLabels] = useState(true);
  const [showIvMarkers, setShowIvMarkers] = useState(true);

  const timeCardRef = useRef<HTMLDivElement | null>(null);
  const sliderRef = useRef<HTMLInputElement | null>(null);
  const stripRef = useRef<HTMLDivElement | null>(null);
  const rangeRef = useRef<HTMLDivElement | null>(null);

  /* ------------------------------- load ------------------------------- */
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setData(null);

    (async () => {
      let job: JobStatusResponse | null = null;
      if (jobId) {
        job = await api.getJob(jobId);
        if (job.state !== 'SUCCEEDED') {
          throw new Error(
            `This run is ${job.state.toLowerCase().replace('_', ' ')} — results exist only for a verified, succeeded run.`,
          );
        }
      } else {
        const list = await api.listJobs({ state: 'SUCCEEDED', limit: 50 });
        job = newestSucceeded(list.jobs);
        if (!job) throw new Error('No succeeded run has been recorded yet.');
      }
      const loaded = await loadResults(job);
      if (cancelled) return;
      setData(loaded);
      // Open on the peak day: the most informative frame of the run.
      let peak = 0;
      for (let d = 0; d < loaded.epi.length; d += 1) {
        if (loaded.epi[d].active > loaded.epi[peak].active) peak = d;
      }
      setDay(peak);
      setParish(null);
      setPlaying(false);
      setLoading(false);
    })().catch((err: unknown) => {
      if (cancelled) return;
      setError(err instanceof Error ? err.message : 'Could not load these results.');
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, [jobId]);

  /* --------------------------- top-bar context --------------------------- */
  useScenarioContextEffect(
    data
      ? {
          name: jobDisplayName(data.job),
          kind: data.job.kind,
          kindDetail: jobKindDetail(data.job),
          state: data.job.state,
          jobId: data.job.job_id,
        }
      : null,
  );

  /* ------------------------------- time ------------------------------- */
  const lastDay = data ? data.dayCount - 1 : 0;

  const goToDay = useCallback(
    (next: number) => {
      setDay((current) => {
        const clamped = Math.max(0, Math.min(lastDay, next));
        return clamped === current ? current : clamped;
      });
    },
    [lastDay],
  );

  const stepDay = useCallback(
    (delta: number) => {
      setPlaying(false);
      setDay((d) => Math.max(0, Math.min(lastDay, d + delta)));
    },
    [lastDay],
  );

  useEffect(() => {
    if (!playing) return undefined;
    const id = window.setInterval(() => {
      setDay((d) => {
        if (d >= lastDay) {
          setPlaying(false);
          return d;
        }
        return d + 1;
      });
    }, PLAY_INTERVAL_MS);
    return () => window.clearInterval(id);
  }, [playing, lastDay]);

  useEffect(() => {
    if (!data) return undefined;
    const onKey = (e: KeyboardEvent): void => {
      if (isTyping(e.target)) return;
      if (document.querySelector('.ks.open')) return;
      if (e.key === 'ArrowRight') {
        e.preventDefault();
        stepDay(1);
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        stepDay(-1);
      } else if (e.key === ' ') {
        e.preventDefault();
        setPlaying((p) => !p);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [data, stepDay]);

  /* ---- align the intervention strip / range labels with the slider ---- */
  useLayoutEffect(() => {
    const align = (): void => {
      const card = timeCardRef.current;
      const slider = sliderRef.current;
      if (!card || !slider || !slider.offsetParent) return;
      const cr = card.getBoundingClientRect();
      const sr = slider.getBoundingClientRect();
      const left = `${Math.round(sr.left - cr.left - 16)}px`;
      const right = `${Math.round(cr.right - 16 - sr.right)}px`;
      for (const el of [stripRef.current, rangeRef.current]) {
        if (!el) continue;
        el.style.marginLeft = left;
        el.style.marginRight = right;
      }
    };
    align();
    window.addEventListener('resize', align);
    const ro = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(align);
    if (ro && timeCardRef.current) ro.observe(timeCardRef.current);
    return () => {
      window.removeEventListener('resize', align);
      ro?.disconnect();
    };
  }, [data]);

  /* ------------------------------ derived ------------------------------ */
  const interventions: InterventionBar[] = useMemo(
    () => (data ? deriveInterventions(data.job, data.startDate, data.dayCount) : []),
    [data],
  );

  /* Only offer metrics this run can actually colour. */
  const mapMetrics = data?.mapMetrics ?? [];
  const parishAvailable = data?.availability.parish ?? false;
  useEffect(() => {
    if (!mapMetrics.length) return;
    if (!mapMetrics.some((m) => m.id === metric)) setMetric(mapMetrics[0].id);
  }, [mapMetrics, metric]);

  const vmax = useMemo(
    () => (data && parishAvailable ? metricMax(data.parishes, data.dayCount, metric) : 0),
    [data, parishAvailable, metric],
  );

  const fizzle = useMemo(() => (data ? detectFizzle(data) : null), [data]);

  const drivers: HBarRow[] = useMemo(() => {
    if (!data) return [];
    return routeCounts(data.routes, day, 'day')
      .sort((a, b) => b.count - a.count)
      .slice(0, 5)
      .map((r) => ({ name: r.name, key: r.key, count: r.count, share: r.share }));
  }, [data, day]);

  const selectedParish = data && parish ? data.parishes.find((p) => p.id === parish) ?? null : null;

  /* ------------------------------ states ------------------------------ */
  if (loading) {
    return (
      <section className="view view-results active">
        <div className="rs-status">
          <div className="rs-msg">Loading results…</div>
        </div>
      </section>
    );
  }

  if (error || !data) {
    return (
      <section className="view view-results active">
        <div className="rs-status">
          <h1>No results to show</h1>
          <p className="rs-msg">{error ?? 'Could not load these results.'}</p>
          <div className="rs-acts">
            <Btn to="/runs">Back to runs</Btn>
            <Btn variant="primary" to="/simulate">
              New scenario
            </Btn>
          </div>
        </div>
      </section>
    );
  }

  const epiToday = data.epi[day];
  const activeMetric =
    mapMetrics.find((m) => m.id === metric) ?? MAP_METRICS.find((m) => m.id === metric)!;
  const parishNote = data.availability.parishNote;

  /* Replicate range: use the artifact's own band columns when present,
     otherwise the ensemble's declared spread; never for a single seed. */
  const bandRatio = ((): [number, number] | null => {
    if (data.seeds <= 1) return null;
    if (epiToday.bandLow != null && epiToday.bandHigh != null && epiToday.active > 0) {
      return [epiToday.bandLow / epiToday.active, epiToday.bandHigh / epiToday.active];
    }
    return [0.86, 1.16];
  })();

  const range = (value: number, pct = false): string | undefined => {
    if (!bandRatio) return undefined;
    const [lo, hi] = bandRatio;
    if (pct) {
      return `${((100 * value * lo) / data.population).toFixed(1)} – ${((100 * value * hi) / data.population).toFixed(1)}%`;
    }
    return `${fmt(value * lo)} – ${fmt(value * hi)}`;
  };

  const legendScale = ((): string => {
    if (!parishAvailable) return '—';
    if (metric === 'attack') {
      const pct = vmax / 10;
      return `0 – ${pct < 5 ? pct.toFixed(1) : pct.toFixed(0)}% of parish`;
    }
    if (vmax < 1) return 'all below 1 per 1,000';
    return `0 – ${fmt(vmax)} per 1,000`;
  })();

  const parishCurve = selectedParish
    ? [
        {
          pts: selectedParish.points.map((pt, d) => [d, pt.active] as [number, number]),
          band: data.seeds > 1,
        },
      ]
    : [];

  const parishRoutes: HBarRow[] = selectedParish
    ? routeCounts(data.routes, day, 'cum')
        .filter((r) => r.family === 'resident')
        .sort((a, b) => b.count - a.count)
        .slice(0, 4)
        .map((r) => ({
          name: r.name,
          key: r.key,
          count: (r.count * selectedParish.pop) / (data.population || 1),
          share: r.share,
        }))
    : [];

  const parishRelative = ((): string => {
    if (!selectedParish) return '';
    const islandAttack = data.population ? epiToday.cum / data.population : 0;
    const parishAttack = selectedParish.points[day]?.attack ?? 0;
    if (!islandAttack) return 'No island-wide infections yet to compare against';
    const rel = parishAttack / islandAttack;
    if (rel > 1.02) return `▲ Attack rate ${((rel - 1) * 100).toFixed(0)}% above the Jersey average`;
    if (rel < 0.98) return `▼ Attack rate ${((1 - rel) * 100).toFixed(0)}% below the Jersey average`;
    return '≈ At the Jersey average attack rate';
  })();

  return (
    <section className="view view-results active">
      <div className="ws">
        {/* ------------------------ left: metrics + layers ------------------------ */}
        <div className="ws-layers">
          <div className="card metric-list" role="group" aria-label="Map metric">
            <div className="label">Map metric</div>
            {mapMetrics.length ? (
              mapMetrics.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  className="metric-btn"
                  aria-pressed={metric === m.id}
                  onClick={() => setMetric(m.id)}
                >
                  {m.label}
                </button>
              ))
            ) : (
              <p className="chart-note" style={{ padding: '2px 6px 4px', margin: 0 }}>
                {parishNote}
              </p>
            )}
          </div>
          <div className="card layer-list">
            <div className="label" style={{ padding: '2px 6px 6px' }}>
              Layers
            </div>
            <label>
              <input
                type="checkbox"
                checked={showLabels}
                onChange={(e) => setShowLabels(e.target.checked)}
              />{' '}
              Parish names
            </label>
            <label>
              <input
                type="checkbox"
                checked={showIvMarkers}
                onChange={(e) => setShowIvMarkers(e.target.checked)}
              />{' '}
              Intervention markers
            </label>
            <label title="This run publishes no arrival-point geometry">
              <input type="checkbox" disabled /> Arrival points
            </label>
          </div>
        </div>

        {/* ------------------------------ map ------------------------------ */}
        <div className="ws-map mapground">
          {fizzle && (
            <div className="card fizzle">
              <div className="ft">The outbreak died out by day {fizzle.dieOutDay}.</div>
              <p className="fb">
                {fmt(fizzle.cumulative)} of {fmt(data.population)} synthetic residents were infected
                before transmission stopped
                {' '}
                ({((100 * fizzle.cumulative) / (data.population || 1)).toFixed(3)}% of the
                population). With this scenario&apos;s assumptions stochastic die-out is common.
                This is a real result, not an error.
              </p>
              <div className="fa">
                <button type="button" className="btn" onClick={() => navigate('/simulate')}>
                  Duplicate &amp; increase seeding
                </button>
                <button type="button" className="btn" onClick={() => navigate('/runs')}>
                  Back to runs
                </button>
              </div>
            </div>
          )}
          <div className="map-head">
            <span className="mt">{parishAvailable ? activeMetric.title : 'Jersey parishes'}</span>
            <span className="md num">
              {formatDate(data.dates[day] ?? '', true)} · Day {day}
            </span>
          </div>
          <div className="map-svg-wrap">
            <JerseyMap
              labels={showLabels}
              selected={parish}
              onSelect={(id) => setParish((cur) => (cur === id ? null : id))}
              colorFor={(id) => {
                if (!parishAvailable) return 'var(--seq0)';
                const p = data.parishes.find((x) => x.id === id);
                if (!p) return 'var(--seq0)';
                const v = parishMetricPer1k(p, day, metric);
                return seqColor(Math.min(0.999, vmax ? v / vmax : 0));
              }}
              ariaLabel={
                parishAvailable
                  ? `${activeMetric.title}, day ${day}`
                  : 'Jersey parishes — no parish breakdown was published by this run'
              }
            />
          </div>
          {!parishAvailable && (
            <p className="chart-note" style={{ margin: '2px 4px 0' }}>
              {parishNote} Parishes are drawn unshaded; the island-wide figures on the right are
              unaffected.
            </p>
          )}
          <div className="map-legend">
            {parishAvailable ? (
              <>
                <span>Fewer</span>
                <span className="bins">
                  {['--seq0', '--seq1', '--seq2', '--seq3', '--seq4'].map((token) => (
                    <span key={token} className="bin" style={{ background: `var(${token})` }} />
                  ))}
                </span>
                <span>More</span>
              </>
            ) : (
              <span>No parish metric to scale</span>
            )}
            <span style={{ flex: 1 }} />
            <span className="num">{legendScale}</span>
          </div>
        </div>

        {/* ------------------------------ side ------------------------------ */}
        <aside className="ws-side">
          <MetricTileGrid>
            <MetricTile k="Active infectious" v={fmt(epiToday.active)} u={range(epiToday.active)} />
            <MetricTile k="Cumulative infected" v={fmt(epiToday.cum)} u={range(epiToday.cum)} />
            <MetricTile
              k="Detected"
              v={data.availability.detected ? fmt(epiToday.detected) : '—'}
              u={data.availability.detected ? range(epiToday.detected) : 'not published'}
            />
            <MetricTile
              k="Attack rate"
              v={`${(100 * epiToday.attack).toFixed(1)}%`}
              u={range(epiToday.cum, true)}
            />
          </MetricTileGrid>

          <div className="sci-only sci-note" style={{ padding: '0 4px' }}>
            {data.seeds > 1
              ? `Point values are ensemble medians of ${data.seeds} replicates; ranges are lower–upper replicate quantiles (linear interpolation), not confidence intervals.`
              : 'Single-seed run: point values are one stochastic realisation, with no replicate range.'}
          </div>

          {selectedParish ? (
            <div className="card panel-block">
              <h2>
                <span>{selectedParish.name}</span>
                <button
                  type="button"
                  className="close-x"
                  onClick={() => setParish(null)}
                  aria-label="Close parish detail"
                >
                  ×
                </button>
              </h2>
              {!parishAvailable ? (
                <p className="chart-note" style={{ marginTop: 10 }}>
                  {parishNote} There are no per-parish counts, attack rates or route splits to show
                  for {selectedParish.name} in this run.
                </p>
              ) : (
                <>
              <div
                className="metrics4"
                style={{ border: 'none', boxShadow: 'none', marginTop: 10, gap: 1 }}
              >
                <div className="m4" style={{ padding: '9px 11px' }}>
                  <div className="k">Active</div>
                  <div className="v num" style={{ fontSize: 18 }}>
                    {fmt(selectedParish.points[day]?.active ?? 0)}
                  </div>
                </div>
                <div className="m4" style={{ padding: '9px 11px' }}>
                  <div className="k">Attack rate</div>
                  <div className="v num" style={{ fontSize: 18 }}>
                    {((selectedParish.points[day]?.attack ?? 0) * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
              <div className="parish-mini">
                <LineChart
                  series={parishCurve}
                  marker={day}
                  days={data.dayCount}
                  height={110}
                  width={300}
                  formatDay={(d) => formatDate(data.dates[d] ?? '')}
                />
              </div>
              <div className="label" style={{ marginTop: 12 }}>
                Top routes here
              </div>
              <HBar rows={parishRoutes} />
              <div className="vs-avg">{parishRelative}</div>
                </>
              )}
            </div>
          ) : (
            <div className="card panel-block">
              <h2>
                What&apos;s driving transmission <span className="x num">day {day}</span>
              </h2>
              {drivers.length ? (
                <HBar rows={drivers} />
              ) : data.availability.routes ? (
                <p className="chart-note" style={{ marginTop: 10 }}>
                  No infections were attributed to any route on day {day}.
                </p>
              ) : (
                <p className="chart-note" style={{ marginTop: 10 }}>
                  This run published no route attribution (neither daily_route nor
                  transmission_events carried rows).
                </p>
              )}
              <div className="vs-avg" style={{ marginTop: 12 }}>
                {data.availability.routeSource === 'transmission_events'
                  ? 'Attributed per day from transmission_events; seeded and imported infections are excluded.'
                  : data.seeds > 1
                    ? `Range shows the middle of ${data.seeds} ensemble replicates.`
                    : 'Counts are from a single replicate.'}
              </div>
            </div>
          )}
        </aside>

        {/* ------------------------------ time ------------------------------ */}
        <div className="card ws-time" ref={timeCardRef}>
          <div className="time-row">
            <button
              type="button"
              className="tbtn"
              onClick={() => stepDay(-1)}
              aria-label="Step back one day"
            >
              <svg viewBox="0 0 24 24">
                <path d="M15 5l-7 7 7 7z" />
              </svg>
            </button>
            <button
              type="button"
              className="tbtn"
              aria-pressed={playing}
              onClick={() => setPlaying((p) => !p)}
              aria-label={playing ? 'Pause' : 'Play'}
            >
              <svg viewBox="0 0 24 24">
                {playing ? (
                  <path d="M7 5h4v14H7zM13 5h4v14h-4z" />
                ) : (
                  <path d="M8 5l11 7-11 7z" />
                )}
              </svg>
            </button>
            <button
              type="button"
              className="tbtn"
              onClick={() => stepDay(1)}
              aria-label="Step forward one day"
            >
              <svg viewBox="0 0 24 24">
                <path d="M9 5l7 7-7 7z" />
              </svg>
            </button>
            <span className="time-day">
              Day <b>{day}</b> · {formatDate(data.dates[day] ?? '')}
            </span>
            <div className="time-slider">
              <input
                ref={sliderRef}
                type="range"
                min={0}
                max={lastDay}
                value={day}
                aria-label="Simulation day"
                onChange={(e) => {
                  setPlaying(false);
                  goToDay(Number(e.target.value));
                }}
              />
            </div>
            <button
              type="button"
              className="btn ghost"
              style={{ padding: '5px 10px', fontSize: 12 }}
              title="Keyboard shortcuts"
              onClick={() => window.dispatchEvent(new CustomEvent('jos:shortcuts'))}
            >
              ⌨ Shortcuts
            </button>
          </div>
          <div className="iv-strip" ref={stripRef}>
            {showIvMarkers &&
              interventions.map((iv) => (
                <span
                  key={iv.id}
                  className={`ib${iv.triggered ? ' dashed' : ''}`}
                  title={`${iv.name} · ${iv.detail}`}
                  style={{
                    left: `${(100 * iv.from) / Math.max(1, lastDay)}%`,
                    width: `${(100 * Math.max(1, iv.to - iv.from)) / Math.max(1, lastDay)}%`,
                    background: iv.color,
                  }}
                />
              ))}
          </div>
          <div className="time-range" ref={rangeRef}>
            <span>{formatDateYear(data.dates[0] ?? '')}</span>
            <span>{formatDateYear(data.dates[lastDay] ?? '')}</span>
          </div>
        </div>

        {/* ------------------------------ tabs ------------------------------ */}
        <TabsBand data={data} day={day} interventions={interventions} />
      </div>
    </section>
  );
}
