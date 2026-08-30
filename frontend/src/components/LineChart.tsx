/** [dayIndex, value] */
export type Point = [number, number];

export interface Series {
  pts: Point[];
  /** Draw an artifact-published band behind the line. */
  band?: { low: Point[]; high: Point[] };
  /** Extra class on the polyline, e.g. `"base"` for the dashed baseline. */
  cls?: string;
}

export interface LineChartProps {
  series: Series[];
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
  className?: string;
}

const defaultFormatValue = (n: number): string => Math.round(n).toLocaleString('en-GB');

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
  marker = null,
  days = 60,
  height = 210,
  width = 980,
  max,
  pct = false,
  formatDay = defaultFormatDay,
  formatValue = defaultFormatValue,
  className,
}: LineChartProps) {
  const W = width;
  const H = height;
  const padL = 52;
  const padR = 14;
  const padT = 12;
  const padB = 26;

  const allValues = series.flatMap((s) => s.pts.map((p) => p[1]));
  const yMax =
    (max ?? (allValues.length ? Math.max(...allValues) * 1.08 : 1)) || 1;

  const X = (d: number): number => padL + ((W - padL - padR) * d) / Math.max(1, days - 1);
  const Y = (v: number): number => padT + (H - padT - padB) * (1 - v / yMax);

  const gridValues = [0, 1, 2, 3].map((i) => (yMax * i) / 3);

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

      {series.map((sr, i) => (
        <g key={`series-${i}`}>
          {sr.band && sr.band.low.length > 0 && sr.band.high.length > 0 && (
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
            className={`curve${sr.cls ? ` ${sr.cls}` : ''}`}
            points={sr.pts.map(([d, v]) => `${X(d)},${Y(v)}`).join(' ')}
          />
        </g>
      ))}

      {marker != null && (
        <g>
          <line
            x1={X(marker)}
            x2={X(marker)}
            y1={padT}
            y2={H - padB}
            stroke="var(--ink)"
            strokeWidth={1.5}
            opacity={0.5}
          />
          <g className="axis">
            <text
              x={X(marker)}
              y={padT + 2}
              dy={-2}
              textAnchor="middle"
              style={{ fontWeight: 600, fill: 'var(--ink)' }}
            >
              Day {marker}
            </text>
          </g>
        </g>
      )}
    </svg>
  );
}
