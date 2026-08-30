export interface HBarRow {
  /** Plain-language name shown to everyone. */
  name: string;
  /** Machine route/intervention id — shown only in Scientific detail mode. */
  key?: string;
  count: number;
  /** 0..1 */
  share: number;
  /** Optional bar color override (default `--accent`). */
  color?: string;
}

export interface HBarProps {
  rows: HBarRow[];
  formatCount?: (n: number) => string;
  className?: string;
}

const defaultFormat = (n: number): string => Math.round(n).toLocaleString('en-GB');

/**
 * Ranked horizontal bars (`.drv` / `.drv-row`), widths relative to the largest
 * row. The `key` renders in a `.sci-only` mono span, so it appears only when
 * the Scientific detail level is on.
 */
export function HBar({ rows, formatCount = defaultFormat, className }: HBarProps) {
  const maxC = Math.max(...rows.map((r) => r.count), 1);
  return (
    <div className={['drv', className].filter(Boolean).join(' ')}>
      {rows.map((r) => (
        <div className="drv-row" key={r.key ?? r.name}>
          <span className="nm" title={r.name}>
            {r.name}
            {r.key && (
              <small
                className="mono sci-only"
                style={{ color: 'var(--ink-3)', fontSize: '10px' }}
              >
                {' '}
                {r.key}
              </small>
            )}
          </span>
          <span className="bar">
            <i
              style={{
                width: `${Math.max(2, (100 * r.count) / maxC)}%`,
                ...(r.color ? { background: r.color } : {}),
              }}
            />
          </span>
          <span className="val">
            {formatCount(r.count)} <small>· {(r.share * 100).toFixed(1)}%</small>
          </span>
        </div>
      ))}
    </div>
  );
}
