import type { ReactNode } from 'react';

export interface MetricTileProps {
  /** Uppercase key line. */
  k: string;
  /** Headline value (tabular numerals). */
  v: ReactNode;
  /** Sub-line, e.g. an ensemble range. */
  u?: ReactNode;
  /** Availability note shown as a tooltip when the value is missing. */
  availabilityNote?: string;
}

/** One headline metric (`.m4`). Wrap four in `<MetricTileGrid>`. */
export function MetricTile({ k, v, u, availabilityNote }: MetricTileProps) {
  const missing = v == null;
  return (
    <div className="m4">
      <div className="k">{k}</div>
      <div className="v" title={missing ? availabilityNote ?? 'This value is unavailable in the published data.' : undefined}>
        {missing ? '—' : v}
      </div>
      {u != null && <div className="u">{u}</div>}
    </div>
  );
}

/** 2x2 hairline grid of metric tiles (`.metrics4`). */
export function MetricTileGrid({ children }: { children: ReactNode }) {
  return <div className="metrics4">{children}</div>;
}
