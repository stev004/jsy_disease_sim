import { useMemo, useRef, useState } from 'react';
import { HBar, LineChart, Seg, useToast } from '../../components';
import type { HBarRow } from '../../components';
import type { DatasetRow } from '../../api';
import { ExportMenu } from './ExportMenu';
import {
  buildBarsSvg,
  dayWindowSuffix,
  exportRowsAsCsv,
  exportSvgAsPng,
  type BarSpec,
} from './exporters';
import {
  fmt,
  formatDate,
  routeCounts,
  shortHash,
  type ResultsData,
} from './data';
import type { InterventionBar } from './interventions';

type TabId = 'epi' | 'routes' | 'ages' | 'travel' | 'iv';
type EpiMetric = 'active' | 'cum' | 'detected';
type RouteWin = 'cum' | 'day';

const TABS: Array<{ id: TabId; label: string }> = [
  { id: 'epi', label: 'Epidemic curve' },
  { id: 'routes', label: 'Transmission routes' },
  { id: 'ages', label: 'Ages' },
  { id: 'travel', label: 'Travel & visitors' },
  { id: 'iv', label: 'Interventions' },
];

const EPI_TITLE: Record<EpiMetric, string> = {
  active: 'Active infectious residents',
  cum: 'Cumulative infected residents',
  detected: 'Detected / reported cases',
};

export interface TabsBandProps {
  data: ResultsData;
  day: number;
  interventions: InterventionBar[];
}

export function TabsBand({ data, day, interventions }: TabsBandProps) {
  const [tab, setTab] = useState<TabId>('epi');
  const [epiMetric, setEpiMetric] = useState<EpiMetric>('active');
  const [routeWin, setRouteWin] = useState<RouteWin>('cum');
  const epiRef = useRef<HTMLDivElement | null>(null);
  const { showToast } = useToast();

  const lastDay = data.dayCount - 1;
  const multiSeed = data.seeds > 1;
  const formatDay = (d: number): string => formatDate(data.dates[d] ?? '');

  /* ------------------------------- epi ------------------------------- */
  const epiSeries = useMemo(() => {
    const pts = data.epi.map(
      (p) => [p.day, epiMetric === 'active' ? p.active : epiMetric === 'cum' ? p.cum : p.detected] as [number, number],
    );
    return [{ pts, band: multiSeed }];
  }, [data.epi, epiMetric, multiSeed]);

  /* ------------------------------ routes ------------------------------ */
  const routeRows = useMemo(
    () => routeCounts(data.routes, day, routeWin),
    [data.routes, day, routeWin],
  );
  const residentRows: HBarRow[] = routeRows
    .filter((r) => r.family === 'resident')
    .sort((a, b) => b.count - a.count)
    .map((r) => ({ name: r.name, key: r.key, count: r.count, share: r.share }));
  const travelRows: HBarRow[] = routeRows
    .filter((r) => r.family === 'travel')
    .sort((a, b) => b.count - a.count)
    .map((r) => ({ name: r.name, key: r.key, count: r.count, share: r.share, color: 'var(--seq3)' }));

  /* ------------------------------ exports ------------------------------ */
  function exportCsv(dataset: string, rows: DatasetRow[], suffix: string): void {
    if (!rows.length) {
      showToast({ title: 'Nothing to export', body: `This run has no ${dataset} rows.`, tone: 'bad' });
      return;
    }
    const filename = `${dataset}_${suffix}.csv`;
    const n = exportRowsAsCsv(rows, filename);
    showToast({
      title: `Exported ${filename}`,
      body: `${n.toLocaleString('en-GB')} rows from ${dataset}.`,
      tone: 'good',
    });
  }

  async function exportPng(svg: SVGSVGElement | null, filename: string): Promise<void> {
    if (!svg) {
      showToast({ title: 'Nothing to export', body: 'The chart is not rendered yet.', tone: 'bad' });
      return;
    }
    try {
      await exportSvgAsPng(svg, filename);
      showToast({ title: `Exported ${filename}`, tone: 'good' });
    } catch (err) {
      showToast({
        title: 'Export failed',
        body: err instanceof Error ? err.message : 'The chart could not be rasterized.',
        tone: 'bad',
      });
    }
  }

  function epiCsv(): void {
    const rows = data.raw.daily_epidemic ?? [];
    exportCsv('daily_epidemic', rows, dayWindowSuffix(0, lastDay));
  }

  function routesCsv(): void {
    // Export exactly the table the ranking was built from.
    const derived = data.availability.routeSource === 'transmission_events';
    const dataset = derived ? 'transmission_events' : 'daily_route';
    const all = (derived ? data.raw.transmission_events : data.raw.daily_route) ?? [];
    const cutoff = data.dates[day];
    const rows =
      routeWin === 'day'
        ? all.filter((r) => r.date === cutoff)
        : all.filter((r) => typeof r.date === 'string' && r.date <= cutoff);
    exportCsv(dataset, rows, routeWin === 'day' ? dayWindowSuffix(day, day) : dayWindowSuffix(0, day));
  }

  async function routesPng(): Promise<void> {
    const bars: BarSpec[] = [...residentRows, ...travelRows].map((r) => ({
      name: r.name,
      count: r.count,
      share: r.share,
      color: r.color,
    }));
    const svg = buildBarsSvg(
      `Where infections happened · ${routeWin === 'day' ? `day ${day} only` : `up to day ${day}`}`,
      bars,
    );
    svg.style.position = 'fixed';
    svg.style.left = '-10000px';
    document.body.appendChild(svg);
    try {
      await exportPng(svg, `transmission-routes_${routeWin === 'day' ? dayWindowSuffix(day, day) : dayWindowSuffix(0, day)}.png`);
    } finally {
      svg.remove();
    }
  }

  /* ------------------------------ travel ------------------------------ */
  const travel = data.travel;
  const travelStats = useMemo(() => {
    if (!travel) return null;
    const pts = travel.points;
    const pt = pts[day];
    const dash = '—';
    const sumTo = (pick: (p: (typeof pts)[number]) => number): number => {
      let total = 0;
      for (let d = 0; d <= day; d += 1) total += pts[d] ? pick(pts[d]) : 0;
      return total;
    };
    const cumVisitor = sumTo((p) => p.visitorInfections);
    const cumResident = sumTo((p) => p.residentInfections);
    const cumV2R = sumTo((p) => p.visitorToResident);
    const cumR2V = sumTo((p) => p.residentToVisitor);
    const cumTravelLocal = sumTo((p) => p.travelLocalInfections);
    const cumReturning = sumTo((p) => p.returningAcquisitions);

    const tiles: Array<[string, string, string]> = [
      ['Arrivals today', travel.hasArrivals && pt ? fmt(pt.arrivals) : dash, 'air + ferry'],
      [
        'Active visitors',
        travel.hasActiveVisitors && pt ? fmt(pt.activeVisitors) : dash,
        'on-island now',
      ],
      [
        'Returning residents infected abroad',
        travel.hasReturning ? fmt(cumReturning) : dash,
        travel.hasReturning ? 'cumulative' : 'not in this run’s tables',
      ],
    ];
    if (travel.hasFlows) {
      tiles.push(
        ['Visitor → resident infections', fmt(cumV2R), 'cumulative, travel routes'],
        ['Resident → visitor infections', fmt(cumR2V), 'cumulative, travel routes'],
        [
          'Local infections on travel routes',
          fmt(cumTravelLocal),
          'cumulative, daily_travel_route',
        ],
      );
    } else if (travel.hasLegacyLinked) {
      tiles.push(
        ['Visitor-linked infections', fmt(cumVisitor), 'cumulative'],
        ['Resident-linked infections', fmt(cumResident), 'cumulative'],
        [
          'Visitor share of infections',
          cumVisitor + cumResident > 0
            ? `${((100 * cumVisitor) / (cumVisitor + cumResident)).toFixed(1)}%`
            : dash,
          'cumulative',
        ],
      );
    }
    return { cumVisitor, cumResident, cumV2R, cumR2V, cumTravelLocal, cumReturning, tiles };
  }, [travel, day]);

  const travelSeries = useMemo(() => {
    if (!travel) return [];
    const series: Array<{ pts: Array<[number, number]>; cls?: string }> = [];
    if (travel.hasArrivals) {
      series.push({ pts: travel.points.map((t, d) => [d, t.arrivals] as [number, number]), cls: 'base' });
    }
    if (travel.hasActiveVisitors) {
      series.push({ pts: travel.points.map((t, d) => [d, t.activeVisitors] as [number, number]) });
    }
    return series;
  }, [travel]);

  const travelFlows: HBarRow[] = ((): HBarRow[] => {
    if (!travel || !travelStats) return [];
    const rows: Array<[string, number]> = travel.hasFlows
      ? [
          ['Visitor → resident', travelStats.cumV2R],
          ['Resident → visitor', travelStats.cumR2V],
          ['Returning residents infected abroad', travelStats.cumReturning],
        ]
      : travel.hasLegacyLinked
        ? [
            ['Visitor-linked infections', travelStats.cumVisitor],
            ['Resident-linked infections', travelStats.cumResident],
          ]
        : [];
    const total = rows.reduce((s, [, v]) => s + v, 0) || 1;
    return rows.map(([name, count]) => ({
      name,
      count,
      share: count / total,
      color: 'var(--seq3)',
    }));
  })();

  /* --------------------------- interventions --------------------------- */
  const ivSpark = useMemo(
    () => [{ pts: data.epi.map((p) => [p.day, p.active] as [number, number]) }],
    [data.epi],
  );

  const provenance = [
    `scenario ${shortHash(data.job.scenario_hash)}`,
    `latent ${shortHash(data.job.latent_hash)}`,
    `bundle ${shortHash(data.job.bundle_hash)}`,
    `${data.seeds} ${data.seeds === 1 ? 'seed' : 'seeds'}`,
    `engine ${data.job.engine_git_commit ?? 'unknown'}${data.job.dirty_worktree_flag ? ' (dirty)' : ' (clean)'}`,
    `denominator ${fmt(data.population)} from ${data.populationSource}`,
    `routes from ${data.availability.routeSource ?? 'none'}`,
    `detection from ${data.availability.detectedSource ?? 'none'}`,
    `datasets: ${data.datasetNames.join(' · ') || 'none'}`,
  ].join(' · ');

  return (
    <div className="card ws-tabs">
      <div className="tabbar" role="tablist" aria-label="Analysis charts">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ---------------- epidemic curve ---------------- */}
      <div className={`tabpane${tab === 'epi' ? ' active' : ''}`} role="tabpanel">
        <div className="chart-head">
          <h3>{EPI_TITLE[epiMetric]}</h3>
          <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
            <Seg
              label="Curve metric"
              value={epiMetric}
              onChange={setEpiMetric}
              options={[
                { value: 'active' as EpiMetric, label: 'Infectious' },
                { value: 'cum' as EpiMetric, label: 'Cumulative' },
                ...(data.availability.detected
                  ? [{ value: 'detected' as EpiMetric, label: 'Detected' }]
                  : []),
              ]}
            />
            <span className="legend">
              <span>
                <span className="sw" style={{ background: 'var(--accent)' }} />
                {multiSeed ? 'Ensemble median' : 'Single replicate'}
              </span>
              {multiSeed && (
                <span>
                  <span className="swb" style={{ background: 'var(--band)' }} />
                  Replicate range
                </span>
              )}
            </span>
            <ExportMenu
              label="epidemic curve"
              onCsv={epiCsv}
              onPng={() =>
                void exportPng(
                  epiRef.current?.querySelector('svg') ?? null,
                  `epidemic-curve_${dayWindowSuffix(0, lastDay)}.png`,
                )
              }
            />
          </div>
        </div>
        <div ref={epiRef}>
          <LineChart series={epiSeries} marker={day} days={data.dayCount} formatDay={formatDay} />
        </div>
        <p className="chart-note" style={{ margin: '6px 4px 8px' }}>
          {!data.availability.detected && 'Detection is not published by this run, so there is no detected/reported curve. '}
          {epiMetric === 'detected' && data.availability.detectedSource === 'detection_events'
            ? 'Detected is a running count of detection_events rows by detection date. '
            : ''}
          {multiSeed
            ? `Band spans the lower–upper replicate quantiles of ${data.seeds} seeds. It is a stochastic spread under fixed assumptions, not a confidence interval.`
            : 'A single replicate — one stochastic realisation under fixed assumptions, with no spread to show. Run an ensemble for a replicate range.'}
        </p>
      </div>

      {/* ---------------- routes ---------------- */}
      <div className={`tabpane${tab === 'routes' ? ' active' : ''}`} role="tabpanel">
        <div className="chart-head">
          <h3>Where infections happened</h3>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <Seg
              label="Route window"
              value={routeWin}
              onChange={setRouteWin}
              options={[
                { value: 'cum', label: 'Up to selected day' },
                { value: 'day', label: 'Selected day only' },
              ]}
            />
            <ExportMenu label="transmission routes" onCsv={routesCsv} onPng={() => void routesPng()} />
          </div>
        </div>
        {data.routes.length === 0 ? (
          <p className="chart-note">
            This run published no route attribution — daily_route has no rows and no
            transmission_events table was available to attribute from.
          </p>
        ) : (
          <div className="routes-2col">
            <HBar rows={residentRows} />
            <div>
              <div className="label" style={{ marginBottom: 8 }}>
                Travel &amp; visitor routes
              </div>
              {travelRows.length ? (
                <HBar rows={travelRows} />
              ) : (
                <p className="chart-note">No travel routes in this run.</p>
              )}
              <p className="chart-note" style={{ marginTop: 14, maxWidth: '48ch' }}>
                {data.availability.routeNote ??
                  'Counts are simulated infection events attributed to the route where transmission occurred.'}{' '}
                Shares are of all attributed infections in the window.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* ---------------- ages ---------------- */}
      <div className={`tabpane${tab === 'ages' ? ' active' : ''}`} role="tabpanel">
        <div className="chart-head">
          <h3>Cumulative infections by age band</h3>
          <span className="chart-note">
            Risk strata are targeting metadata — no clinical severity is modelled
          </span>
        </div>
        {data.ages.length === 0 ? (
          <p className="chart-note">
            {data.availability.ageNote ?? 'This run published no age breakdown.'}
          </p>
        ) : (
          <>
            <div className="age-grid">
              {(() => {
                const totalAge = data.ages.reduce((s, a) => s + (a.cum[day] ?? 0), 0) || 1;
                return data.ages.map((a) => {
                  const inf = a.cum[day] ?? 0;
                  const atk = a.pop ? inf / a.pop : 0;
                  const share = inf / totalAge;
                  return (
                    <div className="card age-card" key={a.band}>
                      <div className="k">AGE {a.band}</div>
                      <div className="v">{fmt(inf)}</div>
                      <div className="s">
                        {data.availability.agePopulations
                          ? `${(atk * 100).toFixed(1)}% of ${fmt(a.pop)}`
                          : `${(share * 100).toFixed(1)}% of infections`}
                      </div>
                      <div className="age-bar">
                        <i
                          style={{
                            width: `${Math.min(100, (data.availability.agePopulations ? atk * 400 : share * 100))}%`,
                          }}
                        />
                      </div>
                    </div>
                  );
                });
              })()}
            </div>
            {data.availability.ageNote && (
              <p className="chart-note" style={{ marginTop: 10 }}>
                {data.availability.ageNote}
              </p>
            )}
          </>
        )}
      </div>

      {/* ---------------- travel ---------------- */}
      <div className={`tabpane${tab === 'travel' ? ' active' : ''}`} role="tabpanel">
        {!travelStats || !travel ? (
          <p className="chart-note">
            This run published no travel tables, so there is nothing to show here.
          </p>
        ) : (
          <>
            <div className="travel-stats">
              {travelStats.tiles.map(([k, v, s]) => (
                <div className="tstat" key={k}>
                  <div className="k">{k}</div>
                  <div className="v num">{v}</div>
                  <div className="s">{s}</div>
                </div>
              ))}
            </div>
            <div className="travel-2col">
              <div>
                <div className="chart-head">
                  <h3>Arrivals &amp; active visitors</h3>
                  <span className="legend">
                    <span>
                      <span className="sw" style={{ background: 'var(--accent)' }} />
                      Active visitors
                    </span>
                    <span>
                      <span className="sw" style={{ background: 'var(--ink-3)' }} />
                      Arrivals / day
                    </span>
                  </span>
                </div>
                <LineChart
                  series={travelSeries}
                  marker={day}
                  days={data.dayCount}
                  height={170}
                  width={640}
                  formatDay={formatDay}
                />
              </div>
              <div>
                <div className="label" style={{ marginBottom: 8 }}>
                  Cross-population transmission · up to selected day
                </div>
                {travelFlows.length ? (
                  <HBar rows={travelFlows} />
                ) : (
                  <p className="chart-note">
                    This run published no cross-population transmission counts.
                  </p>
                )}
                <p className="chart-note" style={{ marginTop: 14, maxWidth: '44ch' }}>
                  Visitor volumes derive from observed 2025 annual passenger movements; composition
                  and contact values are scenario assumptions. Read from {travel.source}.
                </p>
              </div>
            </div>
          </>
        )}
      </div>

      {/* ---------------- interventions ---------------- */}
      <div className={`tabpane${tab === 'iv' ? ' active' : ''}`} role="tabpanel">
        <div className="chart-head">
          <h3>Interventions against the outbreak</h3>
          <span className="chart-note">Hatched = detection-triggered, per-agent</span>
        </div>
        <div style={{ margin: '0 0 6px 182px' }}>
          <LineChart
            series={ivSpark}
            marker={day}
            days={data.dayCount}
            height={90}
            width={800}
            formatDay={formatDay}
          />
        </div>
        {interventions.length === 0 ? (
          <p className="chart-note" style={{ padding: '6px 0 10px 182px' }}>
            No interventions in this scenario — it is a baseline.
          </p>
        ) : (
          <div>
            {interventions.map((iv) => (
              <div className="gantt-row" key={iv.id}>
                <span className="nm" title={`${iv.name} · ${iv.detail}`}>
                  {iv.name}
                </span>
                <span className="gantt-track">
                  <span
                    className={`gantt-bar${iv.triggered ? ' dashed' : ''}`}
                    style={{
                      left: `${(100 * iv.from) / Math.max(1, lastDay)}%`,
                      width: `${(100 * Math.max(1, iv.to - iv.from)) / Math.max(1, lastDay)}%`,
                      background: iv.color,
                    }}
                    title={iv.detail}
                  />
                  <span
                    className="gantt-cursor"
                    style={{ left: `${(100 * day) / Math.max(1, lastDay)}%` }}
                  />
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div
        className="sci-only sci-note"
        style={{ padding: '9px 18px', borderTop: '1px solid var(--line)' }}
      >
        {provenance}
      </div>
    </div>
  );
}
