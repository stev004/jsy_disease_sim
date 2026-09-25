import { useId } from 'react';

/** [dayIndex, value] */
export type Point = [number, number];

export type SeriesRole = 'epi' | 'baseline' | 'intervention' | 'travel' | 'neutral';

export interface HatchWindow {
  /** First active day, inclusive. */
  startDay: number;
  /** Last active day, inclusive. */
  endDay: number;
  /** Intervention family color, normally a `var(--iv-*)` token. */
  color?: string;
}

export interface Series {
  pts: Point[];
  /** Plain-language legend label for this rendered series. */
  label: string;
  /** Semantic line colour role. */
  role: SeriesRole;
  /** Explicit line colour, normally a CSS custom property such as `var(--epi)`. */
  color?: string;
  /** Draw an artifact-published band behind the line. */
  band?: { low: Point[]; high: Point[] };
  /** Extra class on the polyline, e.g. `"base"` for the dashed baseline. */
  cls?: string;
}

export interface LineChartProps {
  series: Series[];
  /** Shade intervention-minus-baseline areas in comparison charts. */
  comparisonAreas?: boolean;
  /** Day index of the vertical "current day" marker. */
  marker?: number | null;
  /** Number of day slots on the x axis (default 60). */
  days?: number;
  /** SVG user-space height (default 210) and width (default 980). */
  height?: number;
  width?: number;
  /** Force the y-axis maximum. */
  max?: number;
  /** Format the y axis as percentages. */
  pct?: boolean;
  /** Map a day index to an axis tick label. */
  formatDay?: (day: number) => string;
  /** Format a y value (default: en-GB thousands). */
  formatValue?: (value: number) => string;
  /** Optional intervention windows drawn behind the data. */
  hatchWindows?: HatchWindow[];
  className?: string;
}

const defaultFormatValue = (n: number): string => Math.round(n).toLocaleString('en-GB');

const ROLE_COLORS: Record<SeriesRole, string> = {
  epi: 'var(--epi)',
  baseline: 'var(--base-line)',
  intervention: 'var(--div-neg)',
  travel: 'var(--ink-2)',
  neutral: 'var(--ink-2)',
};

export function lineSeriesColor(series: Series): string {
  if (series.color) return series.color;
  return ROLE_COLORS[series.role];
}

export function isLineSeriesRendered(series: Series): boolean {
  return series.pts.length > 1;
}

export function isLineSeriesBandRendered(series: Series): boolean {
  return Boolean(series.band && series.band.low.length > 1 && series.band.high.length > 1);
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** Default tick label: day index offset from the supported 6 Jan 2025 start. */
function defaultFormatDay(d: number): string {
  const dt = new Date(Date.UTC(2025, 0, 6));
  dt.setUTCDate(dt.getUTCDate() + d);
  return `${dt.getUTCDate()} ${MONTHS[dt.getUTCMonth()]}`;
}

/**
 * Hand-rolled SVG line chart: 4 gridlines, mono axis text, optional band fill
 * and a day marker. Ported from the mockup's `lineChart`.
 */
export function LineChart({
  series,
  comparisonAreas = false,
  marker = null,
  days = 60,
  height = 210,
  width = 980,
  max,
  pct = false,
  formatDay = defaultFormatDay,
  formatValue = defaultFormatValue,
  hatchWindows = [],
  className,
}: LineChartProps) {
  const patternId = `chart-hatch-${useId().replace(/:/g, '')}`;
  const W = width;
  const H = height;
  const padL = 52;
  const padR = 14;
  const padT = 12;
  const padB = 26;

  const renderedSeries = series.filter(isLineSeriesRendered);
  const allValues = renderedSeries.flatMap((s) => s.pts.map((p) => p[1]));
  const yMax =
    (max ?? (allValues.length ? Math.max(...allValues) * 1.08 : 1)) || 1;

  const X = (d: number): number => padL + ((W - padL - padR) * d) / Math.max(1, days - 1);
  const Y = (v: number): number => padT + (H - padT - padB) * (1 - v / yMax);

  const gridValues = [0, 1, 2, 3].map((i) => (yMax * i) / 3);

  const comparisonAreaPolygons = comparisonAreas
    ? buildComparisonAreaPolygons(renderedSeries, X, Y)
    : [];

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      style={{ width: '100%', height: 'auto', display: 'block' }}
      className={className}
    >
      {gridValues.map((v, i) => (
        <g key={`grid-${i}`}>
          <line className="gridline" x1={padL} x2={W - padR} y1={Y(v)} y2={Y(v)} />
          <g className="axis">
            <text x={padL - 8} y={Y(v) + 3.5} textAnchor="end">
              {pct ? `${(v * 100).toFixed(0)}%` : formatValue(v)}
            </text>
          </g>
        </g>
      ))}

      {Array.from({ length: Math.ceil(days / 10) }, (_, i) => i * 10).map((d) => (
        <g className="axis" key={`tick-${d}`}>
          <text x={X(d)} y={H - 8} textAnchor="middle">
            {formatDay(d)}
          </text>
        </g>
      ))}

      {hatchWindows.length > 0 && (
        <defs>
          <pattern id={patternId} width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <path d="M 0 0 V 8" stroke="var(--hatch)" strokeWidth="2" />
          </pattern>
        </defs>
      )}

      {hatchWindows.map((window, i) => {
        const start = Math.max(0, Math.min(days - 1, window.startDay));
        const end = Math.max(0, Math.min(days - 1, window.endDay));
        if (end < start) return null;
        const slotWidth = (W - padL - padR) / Math.max(1, days - 1);
        const x = Math.max(padL, X(start) - slotWidth / 2);
        const right = Math.min(W - padR, X(end) + slotWidth / 2);
        const width = right - x;
        return (
          <g key={`hatch-${i}`}>
            <rect x={x} y={padT} width={width} height={H - padT - padB} fill={`url(#${patternId})`} opacity={0.7} />
            <rect x={x} y={padT} width={width} height={3} fill={window.color ?? 'var(--ink-2)'} />
          </g>
        );
      })}

      {comparisonAreaPolygons.map((area, index) => (
        <polygon
          key={`comparison-area-${index}`}
          className="chart-area"
          points={area.points}
          fill={area.positive ? 'var(--div-pos)' : 'var(--div-neg)'}
          fillOpacity={0.14}
        />
      ))}

      {renderedSeries.map((sr, i) => (
        <g className="line-series" key={`series-${i}`}>
          {isLineSeriesBandRendered(sr) && sr.band && (
            <polygon
              className="bandfill"
              points={
                sr.band.high.map(([d, v]) => `${X(d)},${Y(v)}`).join(' ') +
                ' ' +
                [...sr.band.low]
                  .reverse()
                  .map(([d, v]) => `${X(d)},${Y(v)}`)
                  .join(' ')
              }
            />
          )}
          <polyline
            className={`curve curve-draw${sr.cls ? ` ${sr.cls}` : ''}${i === 1 ? ' treated arm-secondary' : ''}`}
            style={{ stroke: lineSeriesColor(sr) }}
            pathLength={1}
            points={sr.pts.map(([d, v]) => `${X(d)},${Y(v)}`).join(' ')}
          />
        </g>
      ))}

      {marker != null && (
        <g>
          <line
            className="day-cursor-line"
            x1={X(marker)}
            x2={X(marker)}
            y1={padT}
            y2={H - padB}
            stroke="var(--seq5)"
            strokeWidth={1}
            opacity={0.9}
          />
          {(() => {
            const median = renderedSeries.find((item) => item.cls !== 'base') ?? renderedSeries[0];
            const value = median?.pts.find(([day]) => day === marker)?.[1];
            return value == null ? null : (
              <circle className="day-cursor-dot" cx={X(marker)} cy={Y(value)} r={5} fill="var(--seq5)" />
            );
          })()}
          <g className="axis">
            <text
              x={X(marker)}
              y={padT + 2}
              dy={-2}
              textAnchor="middle"
              style={{ fontWeight: 600, fill: 'var(--seq5)' }}
            >
              Day {marker}
            </text>
          </g>
        </g>
      )}
    </svg>
  );
}

interface ComparisonAreaPolygon {
  points: string;
  positive: boolean;
}

function buildComparisonAreaPolygons(
  series: Series[],
  x: (day: number) => number,
  y: (value: number) => number,
): ComparisonAreaPolygon[] {
  const baseline = series.find((item) => item.role === 'baseline');
  const intervention = series.find((item) => item.role === 'intervention');
  if (!baseline || !intervention) return [];

  const baselineByDay = new Map(baseline.pts);
  const interventionByDay = new Map(intervention.pts);
  const days = [...baselineByDay.keys()]
    .filter((day) => interventionByDay.has(day))
    .sort((a, b) => a - b);
  const polygons: ComparisonAreaPolygon[] = [];

  for (let index = 0; index < days.length - 1; index += 1) {
    const day0 = days[index];
    const day1 = days[index + 1];
    // Do not shade across unpublished days.
    if (day1 !== day0 + 1) continue;
    const base0 = baselineByDay.get(day0);
    const base1 = baselineByDay.get(day1);
    const treated0 = interventionByDay.get(day0);
    const treated1 = interventionByDay.get(day1);
    if (base0 == null || base1 == null || treated0 == null || treated1 == null) continue;

    const difference0 = treated0 - base0;
    const difference1 = treated1 - base1;
    const crossing = difference0 * difference1 < 0
      ? difference0 / (difference0 - difference1)
      : null;
    const stops = crossing == null ? [0, 1] : [0, crossing, 1];

    for (let piece = 0; piece < stops.length - 1; piece += 1) {
      const start = stops[piece];
      const end = stops[piece + 1];
      const middle = (start + end) / 2;
      const middleDifference = difference0 + (difference1 - difference0) * middle;
      if (middleDifference === 0) continue;

      const interpolate = (from: number, to: number, t: number) => from + (to - from) * t;
      const points = [
        `${x(interpolate(day0, day1, start))},${y(interpolate(base0, base1, start))}`,
        `${x(interpolate(day0, day1, end))},${y(interpolate(base0, base1, end))}`,
        `${x(interpolate(day0, day1, end))},${y(interpolate(treated0, treated1, end))}`,
        `${x(interpolate(day0, day1, start))},${y(interpolate(treated0, treated1, start))}`,
      ].join(' ');
      polygons.push({ points, positive: middleDifference > 0 });
    }
  }

  return polygons;
}
