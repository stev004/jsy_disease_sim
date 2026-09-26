export type RankedBarRole = 'infection' | 'neutral';

export interface RankedBarColor {
  color: 'var(--epi)' | 'var(--ink-2)';
  opacity: number;
}

/** Shared visible/export colour rule for ranked bars. */
export function resolveRankedBarColor(role: RankedBarRole, index: number): RankedBarColor {
  if (role === 'neutral') return { color: 'var(--ink-2)', opacity: 1 };
  return { color: 'var(--epi)', opacity: index === 0 ? 1 : 0.55 };
}
