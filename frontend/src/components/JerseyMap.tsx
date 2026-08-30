import { JERSEY_LABELS, JERSEY_PATHS, MAP_VIEWBOX, PARISHES, type ParishId } from '../map/geometry';

export interface JerseyMapProps {
  /** Fill for each parish; return any CSS color (e.g. `seqColor(t)`). */
  colorFor: (parishId: ParishId) => string;
  selected?: ParishId | null;
  onSelect?: (parishId: ParishId) => void;
  /** Parish name labels (default true). */
  labels?: boolean;
  /** 2-mile scale bar (default true). */
  scalebar?: boolean;
  /** Accessible name for the figure. */
  ariaLabel?: string;
  className?: string;
}

const HALO_RINGS: Array<[number, number]> = [
  [26, 0.35],
  [13, 0.6],
];

const PARISH_IDS = Object.keys(JERSEY_PATHS) as ParishId[];

/**
 * The island: two-ring offshore shallows halo, parish fills, coastline
 * overlay, haloed labels and a 2-mile scale bar — the mockup's `renderMap`.
 */
export function JerseyMap({
  colorFor,
  selected = null,
  onSelect,
  labels = true,
  scalebar = true,
  ariaLabel = 'Map of Jersey parishes',
  className,
}: JerseyMapProps) {
  const interactive = Boolean(onSelect);
  return (
    <svg viewBox={MAP_VIEWBOX} role="img" aria-label={ariaLabel} className={className}>
      {HALO_RINGS.map(([w, op]) =>
        PARISH_IDS.map((id) => (
          <path
            key={`halo-${w}-${id}`}
            d={JERSEY_PATHS[id]}
            fill="var(--map-halo)"
            stroke="var(--map-halo)"
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

      {PARISH_IDS.map((id) => (
        <path
          key={`coast-${id}`}
          d={JERSEY_PATHS[id]}
          fill="none"
          stroke="var(--coast)"
          strokeWidth={0.9}
          strokeLinejoin="round"
          opacity={0.55}
          pointerEvents="none"
        />
      ))}

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
