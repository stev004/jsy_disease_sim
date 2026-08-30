import type { ReactNode } from 'react';

export interface MetricTileProps {
  /** Uppercase key line. */
  k: string;
  /** Headline value (tabular numerals). */
  v: ReactNode;
  /** Sub-line, e.g. an ensemble range. */
  u?: ReactNode;
}

/** One headline metric (`.m4`). Wrap four in `<MetricTileGrid>`. */
export function MetricTile({ k, v, u }: MetricTileProps) {
  return (
    <div className="m4">
      <div className="k">{k}</div>
      <div className="v">{v}</div>
      {u != null && <div className="u">{u}</div>}
    </div>
  );
}

/** 2x2 hairline grid of metric tiles (`.metrics4`). */
export function MetricTileGrid({ children }: { children: ReactNode }) {
  return <div className="metrics4">{children}</div>;
}
