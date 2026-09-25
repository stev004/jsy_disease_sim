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
import { OSM_ATTRIBUTION, seqColor, type ParishId } from '../../map/geometry';
import { useScenarioContextEffect } from '../../app/ScenarioContextProvider';
import { setProvenanceJobId } from '../drawer/provenanceStore';
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

const PLAY_INTERVAL_MS = 500;

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
      setProvenanceJobId(job.job_id);
      const loaded = await loadResults(job);
      if (cancelled) return;
      setData(loaded);
      // Open on the peak day: the most informative frame of the run.
      let peak = 0;
      for (let d = 0; d < loaded.epi.length; d += 1) {
        if ((loaded.epi[d].active ?? -Infinity) > (loaded.epi[peak].active ?? -Infinity)) peak = d;
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
      setProvenanceJobId(null);
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

  const pulseParish = useMemo(() => {
    if (!data) return null;
    let highest: { id: ParishId; count: number } | null = null;
    for (const candidate of data.parishes) {
      const count = candidate.points[day]?.newInfections;
      if (count != null && count > 0 && (!highest || count > highest.count)) {
        highest = { id: candidate.id, count };
      }
    }
    return highest?.id ?? null;
  }, [data, day]);

  const topParishes = useMemo(() => {
    if (!data?.availability.parishAttack) return [];
    return data.parishes
      .flatMap((candidate) => {
        const share = candidate.points[day]?.attack;
        return share == null ? [] : [{ name: candidate.name, share }];
      })
      .sort((a, b) => b.share - a.share)
      .slice(0, 6);
  }, [data, day]);

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

  const range = (value: number | null, pct = false, banded = false): string | undefined => {
    if (!banded || data.seeds === 1 || value == null || epiToday.bandLow == null || epiToday.bandHigh == null) return undefined;
    if (pct && data.population != null) {
      return `${((100 * epiToday.bandLow) / data.population).toFixed(1)} – ${((100 * epiToday.bandHigh) / data.population).toFixed(1)}%`;
    }
    return pct ? undefined : `${fmt(epiToday.bandLow)} – ${fmt(epiToday.bandHigh)}`;
  };

  const legendScale = ((): string => {
    if (!parishAvailable) return '—';
    if (metric === 'attack') {
      const pct = vmax * 100;
      return `0 – ${pct < 5 ? pct.toFixed(1) : pct.toFixed(0)}% of parish`;
    }
    return `0 – ${fmt(vmax)} counts`;
  })();

  const parishCurve = selectedParish
    ? [{ pts: selectedParish.points.flatMap((point, d) => point.cum == null ? [] : [[d, point.cum] as [number, number]]) }]
    : [];
  const parishRelative = selectedParish && data.availability.parishAttack
    ? 'Parish ever-infected fraction is published for this run.'
    : selectedParish
      ? 'Parish route attribution and ever-infected denominator are not published for this run.'
      : '';
  const hasPublishedBand = data.seeds > 1 && data.epi.some((point) => point.bandLow != null && point.bandHigh != null);
  const ensembleNote = data.seeds > 1
    ? hasPublishedBand
      ? `Point values are ensemble medians of ${data.seeds} replicates; ranges are persisted lower–upper replicate quantiles, not confidence intervals.`
      : `This ensemble has ${data.seeds} persisted replicates, but no quantile band is available for this metric.`
    : 'Single-seed run: point values are one stochastic realisation, with no replicate range.';
  const tideSeries = [{
    pts: data.epi.flatMap((point) => point.active == null ? [] : [[point.day, point.active] as [number, number]]),
    band: hasPublishedBand
      ? {
          low: data.epi.flatMap((point) => point.bandLow == null ? [] : [[point.day, point.bandLow] as [number, number]]),
          high: data.epi.flatMap((point) => point.bandHigh == null ? [] : [[point.day, point.bandHigh] as [number, number]]),
        }
      : undefined,
  }];
  const hatchWindows = showIvMarkers
    ? interventions
        .filter((intervention) => !intervention.triggered)
        .map((intervention) => ({
          startDay: intervention.from,
          endDay: intervention.to,
          color: intervention.color,
        }))
    : [];

  return (
    <section className="view view-results active">
      <div className="rs-page">
        <header className="rs-page-head">
          <div className="rs-headline-block">
            <p className="rs-eyebrow">
              {jobDisplayName(data.job)} · {data.job.kind.replaceAll('_', ' ')} · {data.population == null ? 'Population not published' : `Population ${fmt(data.population)} residents`}
            </p>
            <h1 className="rs-day-headline" aria-label={`Day ${day}`}>
              <span>Day</span> <span className="rs-day-number">{String(day).padStart(2, '0')}</span>
            </h1>
            <p className="rs-head-date">{formatDate(data.dates[day] ?? '')}</p>
          </div>
          <div className="rs-metric-pills" role="group" aria-label="Map metric">
            {mapMetrics.length ? mapMetrics.map((mapMetric) => (
              <button
                key={mapMetric.id}
                type="button"
                className="rs-metric-pill"
                aria-pressed={metric === mapMetric.id}
                onClick={() => setMetric(mapMetric.id)}
              >
                {mapMetric.label}
              </button>
            )) : <p className="chart-note">{parishNote}</p>}
          </div>
        </header>

        <div className="rs-main-layout">
          <div className="rs-main-column">
            <section className="card rs-map-panel mapground" aria-label="Parish map panel">
              {fizzle && (
                <div className="card fizzle">
                  <div className="ft">The outbreak died out by day {fizzle.dieOutDay}.</div>
                  <p className="fb">
                    {fmt(fizzle.cumulative)} synthetic residents were infected before transmission
                    stopped{data.population != null
                      ? ` (${((100 * fizzle.cumulative) / data.population).toFixed(3)}% of the population)`
                      : ' (the run did not publish a denominator)'}. With this scenario&apos;s assumptions stochastic die-out is common.
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
              <div className="rs-map-head">
                <div>
                  <h2>{parishAvailable ? activeMetric.title : 'Jersey parishes'}</h2>
                  <p>{parishAvailable ? `${activeMetric.label} · ${metric === 'attack' ? 'share of parish population' : 'count'}` : 'Parish detail unavailable for this run'}</p>
                </div>
                <span className={`rs-play-state${playing ? ' is-playing' : ''}`} aria-live="polite">
                  <i aria-hidden="true" />{playing ? 'Playing' : 'Paused'}
                </span>
              </div>

              <div className="rs-map-controls">
                <span className="rs-layer-label">Layers</span>
                <label>
                  <input type="checkbox" checked={showLabels} onChange={(event) => setShowLabels(event.target.checked)} />
                  Parish names
                </label>
                <label>
                  <input type="checkbox" checked={showIvMarkers} onChange={(event) => setShowIvMarkers(event.target.checked)} />
                  Intervention markers
                </label>
                <label title="This run publishes no arrival-point geometry">
                  <input type="checkbox" disabled /> Arrival points
                </label>
              </div>

              <div className="map-svg-wrap rs-map-svg-wrap">
                <JerseyMap
                  labels={showLabels}
                  selected={parish}
                  pulse={pulseParish}
                  pulsePlaying={playing}
                  onSelect={(id) => setParish((current) => (current === id ? null : id))}
                  colorFor={(id) => {
                    if (!parishAvailable) return 'var(--panel-2)';
                    const currentParish = data.parishes.find((candidate) => candidate.id === id);
                    if (!currentParish) return 'var(--panel-2)';
                    const value = parishMetricPer1k(currentParish, day, metric);
                    return value == null ? 'var(--panel-2)' : seqColor(Math.min(0.999, vmax ? value / vmax : 0));
                  }}
                  ariaLabel={parishAvailable
                    ? `${activeMetric.title}, day ${day}`
                    : 'Jersey parishes — no parish breakdown was published by this run'}
                />
              </div>
              {!parishAvailable && (
                <p className="chart-note rs-map-note">
                  {parishNote} Parishes are drawn unshaded; the island-wide figures on the right are unaffected.
                </p>
              )}
              <div className="rs-map-footer">
                <div className="map-legend">
                  {parishAvailable ? (
                    <>
                      <span>Fewer</span>
                      <span className="bins">
                        {['--seq0', '--seq1', '--seq2', '--seq3', '--seq4', '--seq5'].map((token) => (
                          <span key={token} className="bin" style={{ background: `var(${token})` }} />
                        ))}
                      </span>
                      <span>More</span>
                      <span className="rs-legend-metric">{activeMetric.label} · {metric === 'attack' ? '% of parish' : 'count'}</span>
                    </>
                  ) : <span>No parish metric to scale</span>}
                  <span className="rs-legend-scale num">{legendScale}</span>
                </div>
                <span className="rs-map-attribution">{OSM_ATTRIBUTION}</span>
              </div>
            </section>

            <section className="card rs-tide-panel" ref={timeCardRef} aria-label="Epidemic curve playback">
              <div className="rs-gauge-head">
                <button
                  type="button"
                  className="rs-play-button"
                  aria-pressed={playing}
                  onClick={() => setPlaying((current) => !current)}
                  aria-label={playing ? 'Pause day playback' : 'Play day playback'}
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    {playing ? <path d="M7 5h4v14H7zM13 5h4v14h-4z" /> : <path d="M8 5l11 7-11 7z" />}
                  </svg>
                </button>
                <div className="rs-gauge-title">
                  <h2>Active infectious · tide gauge</h2>
                  <div className="rs-tide-legend">
                    <span><i className="rs-line-swatch" />{data.seeds > 1 ? 'Ensemble median' : 'Single replicate'}</span>
                    {hasPublishedBand && <span><i className="rs-band-swatch" />Replicate range</span>}
                    <span className="num">Day {day} · {formatDate(data.dates[day] ?? '')}</span>
                  </div>
                </div>
                <button
                  type="button"
                  className="rs-shortcuts-button"
                  title="Keyboard shortcuts"
                  onClick={() => window.dispatchEvent(new CustomEvent('jos:shortcuts'))}
                >
                  ⌨ Shortcuts
                </button>
              </div>
              <div className="rs-slider-line">
                <span className="rs-slider-day num">Day {day}</span>
                <div className="time-slider">
                  <input
                    ref={sliderRef}
                    type="range"
                    min={0}
                    max={lastDay}
                    value={day}
                    aria-label="Simulation day"
                    onChange={(event) => {
                      setPlaying(false);
                      goToDay(Number(event.target.value));
                    }}
                  />
                </div>
              </div>
              <div className="iv-strip" ref={stripRef} aria-label="Intervention windows">
                {showIvMarkers && interventions.map((intervention) => (
                  <span
                    key={intervention.id}
                    className={`ib${intervention.triggered ? ' dashed' : ''}`}
                    title={`${intervention.name} · ${intervention.detail}`}
                    style={{
                      left: `${(100 * intervention.from) / Math.max(1, lastDay)}%`,
                      width: `${(100 * Math.max(1, intervention.to - intervention.from)) / Math.max(1, lastDay)}%`,
                      background: intervention.color,
                    }}
                  />
                ))}
              </div>
              <LineChart
                series={tideSeries}
                marker={day}
                days={data.dayCount}
                height={104}
                formatDay={(index) => formatDate(data.dates[index] ?? '')}
                hatchWindows={hatchWindows}
                className="rs-tide-chart"
              />
              <div className="time-range" ref={rangeRef}>
                <span>{formatDateYear(data.dates[0] ?? '')}</span>
                <span>{formatDateYear(data.dates[lastDay] ?? '')}</span>
              </div>
            </section>
          </div>

          <aside className="rs-right-rail">
            <MetricTileGrid>
              <MetricTile
                k="Active infectious"
                v={epiToday.active == null ? null : fmt(epiToday.active)}
                u={range(epiToday.active, false, true)}
                availabilityNote="Active infectious data are not published for this day."
              />
              <MetricTile
                k={data.cumulativeLabel}
                v={epiToday.cum == null ? null : fmt(epiToday.cum)}
                availabilityNote="Cumulative infections are not published for this day."
              />
              <MetricTile
                k="Detected"
                v={data.availability.detected && epiToday.detected != null ? fmt(epiToday.detected) : null}
                u={data.availability.detected ? undefined : 'not published'}
                availabilityNote="Detected cases are not published by this run."
              />
              <MetricTile
                k="Ever infected"
                v={epiToday.attack == null ? null : `${(100 * epiToday.attack).toFixed(1)}%`}
                u={epiToday.attack == null ? 'not published' : undefined}
                availabilityNote="Ever-infected fraction is not published for this day."
              />
            </MetricTileGrid>
            <p className="rs-ensemble-note">{ensembleNote}</p>

            {selectedParish ? (
              <section className="card panel-block rs-side-panel">
                <h2>
                  <span>{selectedParish.name}</span>
                  <button type="button" className="close-x" onClick={() => setParish(null)} aria-label="Close parish detail">×</button>
                </h2>
                {!parishAvailable ? (
                  <p className="chart-note rs-side-copy">
                    {parishNote} There are no per-parish counts, ever-infected fractions or route splits to show for {selectedParish.name} in this run.
                  </p>
                ) : (
                  <>
                    <div className="metrics4 rs-parish-metrics">
                      <div className="m4">
                        <div className="k">Active infectious</div>
                        <div className="v num">{fmt(selectedParish.points[day]?.active ?? null)}</div>
                        {!data.availability.parishActive && <div className="s">not available for this run</div>}
                      </div>
                      <div className="m4">
                        <div className="k">New infections today</div>
                        <div className="v num">{fmt(selectedParish.points[day]?.newInfections ?? null)}</div>
                      </div>
                    </div>
                    <div className="parish-mini">
                      <LineChart
                        series={parishCurve}
                        marker={day}
                        days={data.dayCount}
                        height={110}
                        width={300}
                        formatDay={(index) => formatDate(data.dates[index] ?? '')}
                      />
                    </div>
                    <div className="vs-avg">{parishRelative}</div>
                  </>
                )}
              </section>
            ) : (
              <section className="card panel-block rs-side-panel">
                <h2>What&apos;s driving transmission <span className="x num">day {day}</span></h2>
                {drivers.length ? (
                  <HBar rows={drivers} />
                ) : data.availability.routes ? (
                  <p className="chart-note rs-side-copy">No infections were attributed to any route on day {day}.</p>
                ) : (
                  <p className="chart-note rs-side-copy">
                    This run published no route attribution (neither daily_route nor transmission_events carried rows).
                  </p>
                )}
                <div className="vs-avg rs-side-copy">
                  {data.availability.routeSource === 'transmission_events'
                    ? 'Attributed per day from transmission_events; seeded and imported infections are excluded.'
                    : data.seeds > 1
                      ? `Range shows the middle of ${data.seeds} ensemble replicates.`
                      : 'Counts are from a single replicate.'}
                </div>
              </section>
            )}

            <section className="card panel-block rs-side-panel rs-ranked-parishes">
              <h2>Parishes by ever-infected share <span className="x num">day {day}</span></h2>
              {data.availability.parishAttack ? topParishes.length ? (
                <div className="rs-rank-list">
                  {topParishes.map((row, index) => {
                    const maxShare = topParishes[0]?.share ?? 1;
                    return (
                      <div className="rs-rank-row" key={row.name}>
                        <span className="rs-rank-name">{row.name}</span>
                        <span className="rs-rank-track"><i className={index === 0 ? 'is-top' : undefined} style={{ width: `${maxShare > 0 ? 100 * row.share / maxShare : 0}%` }} /></span>
                        <span className="rs-rank-value num">{(100 * row.share).toFixed(1)}%</span>
                      </div>
                    );
                  })}
                </div>
              ) : <p className="chart-note rs-side-copy">Ever-infected parish values are not available for day {day}.</p> : (
                <p className="chart-note rs-side-copy">Ever-infected share by parish is not published by this run.</p>
              )}
            </section>
          </aside>
        </div>

        <TabsBand data={data} day={day} interventions={interventions} />
      </div>
    </section>
  );
}
