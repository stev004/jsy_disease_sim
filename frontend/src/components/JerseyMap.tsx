import { JERSEY_LABELS, JERSEY_PATHS, MAP_VIEWBOX, PARISHES, type ParishId } from '../map/geometry';

export interface JerseyMapProps {
  /** Fill for each parish; return any CSS color (e.g. `seqColor(t)`). */
  colorFor: (parishId: ParishId) => string;
  selected?: ParishId | null;
  /** Parish receiving the current-day new-infection ripple. */
  pulse?: ParishId | null;
  /** Animate the two ripple rings while day playback is running. */
  pulsePlaying?: boolean;
  onSelect?: (parishId: ParishId) => void;
  /** Parish name labels (default true). */
  labels?: boolean;
  /** 2-mile scale bar (default true). */
  scalebar?: boolean;
  /** Accessible name for the figure. */
  ariaLabel?: string;
  className?: string;
}

const COAST_CONTOURS: Array<[number, number]> = [
  [38, 0.12],
  [26, 0.18],
  [14, 0.24],
];

const PARISH_IDS = Object.keys(JERSEY_PATHS) as ParishId[];

/**
 * The island: three offshore coast contours, parish fills, haloed labels,
 * optional current-day ripple and a 2-mile scale bar.
 */
export function JerseyMap({
  colorFor,
  selected = null,
  pulse = null,
  pulsePlaying = false,
  onSelect,
  labels = true,
  scalebar = true,
  ariaLabel = 'Map of Jersey parishes',
  className,
}: JerseyMapProps) {
  const interactive = Boolean(onSelect);
  return (
    <svg
      viewBox={MAP_VIEWBOX}
      role="img"
      aria-label={ariaLabel}
      className={['jersey-map', className].filter(Boolean).join(' ')}
    >
      {COAST_CONTOURS.map(([w, op]) =>
        PARISH_IDS.map((id) => (
          <path
            key={`contour-${w}-${id}`}
            d={JERSEY_PATHS[id]}
            fill="none"
            stroke="var(--coast)"
            strokeWidth={w}
            strokeLinejoin="round"
            opacity={op}
          />
        )),
      )}

      {PARISHES.map((p) => (
        <path
          key={`fill-${p.id}`}
          className={`parish${selected === p.id ? ' sel' : ''}`}
          d={JERSEY_PATHS[p.id]}
          fill={colorFor(p.id)}
          tabIndex={interactive ? 0 : -1}
          role={interactive ? 'button' : undefined}
          aria-label={p.name}
          style={interactive ? undefined : { cursor: 'default' }}
          onClick={interactive ? () => onSelect?.(p.id) : undefined}
          onKeyDown={
            interactive
              ? (e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelect?.(p.id);
                  }
                }
              : undefined
          }
        >
          <title>{p.name}</title>
        </path>
      ))}

      {pulse && (() => {
        const [cx, cy] = JERSEY_LABELS[pulse];
        return pulsePlaying ? (
          <g className="map-pulse" aria-hidden="true" pointerEvents="none">
            <circle className="map-pulse-ring map-pulse-ring-first" cx={cx} cy={cy} r={6} fill="none" stroke="var(--seq5)" />
            <circle className="map-pulse-ring map-pulse-ring-second" cx={cx} cy={cy} r={6} fill="none" stroke="var(--seq5)" />
          </g>
        ) : (
          <circle className="map-pulse-ring map-pulse-ring-paused" cx={cx} cy={cy} r={24} fill="none" stroke="var(--seq5)" aria-hidden="true" />
        );
      })()}

      {labels &&
        PARISHES.map((p) => {
          const [x, y] = JERSEY_LABELS[p.id];
          return (
            <text key={`label-${p.id}`} className="parish-label" x={x} y={y}>
              {p.name}
            </text>
          );
        })}

      {scalebar && (
        <g style={{ font: "500 9px 'IBM Plex Mono', monospace" }} fill="var(--ink-2)" opacity={0.75}>
          <line x1={46} y1={410} x2={126} y2={410} stroke="var(--ink-2)" strokeWidth={1} />
          <line x1={46} y1={406} x2={46} y2={410} stroke="var(--ink-2)" strokeWidth={1} />
          <line x1={126} y1={406} x2={126} y2={410} stroke="var(--ink-2)" strokeWidth={1} />
          <text x={50} y={404}>
            2 mi
          </text>
        </g>
      )}
    </svg>
  );
}
