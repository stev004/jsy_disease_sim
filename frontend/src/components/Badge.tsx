/** Provenance status of a parameter or dataset value. */
export type Provenance = 'observed' | 'derived' | 'literature' | 'calibrated' | 'assumption';

const LABEL: Record<Provenance, string> = {
  observed: 'Observed',
  derived: 'Derived',
  literature: 'Literature prior',
  calibrated: 'Calibrated',
  assumption: 'Assumption',
};

export const PROVENANCE_MEANING: Record<Provenance, string> = {
  observed: 'From a frozen official Jersey source',
  derived: 'Computed from observed controls',
  literature: 'Generic value from published literature',
  calibrated: 'Fitted on synthetic truth only',
  assumption: 'A scenario choice you can change',
};

export function Badge({ kind, children }: { kind: Provenance; children?: React.ReactNode }) {
  return <span className={`badge ${kind}`}>{children ?? LABEL[kind]}</span>;
}
