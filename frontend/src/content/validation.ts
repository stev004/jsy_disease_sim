export type ValidationVerdict = 'PASS' | 'FAIL' | 'NOT RUN';

export interface ValidationArm {
  id: string;
  name: string;
  verdict: ValidationVerdict;
  summary: string;
}

export interface ValidationGate {
  id: string;
  title: string;
  verdict: ValidationVerdict;
  date: string | null;
  summary: string;
  arms?: ValidationArm[];
  citations: string[];
}

/** Hand-maintained snapshot; these records are not live or automatically refreshed. */
export const validation: {
  asOf: string;
  gates: ValidationGate[];
  note: string;
} = {
  asOf: '2026-09-25',
  gates: [
    {
      id: 'v13-phase0',
      title: 'V1.3 Phase 0 — synthetic recovery',
      verdict: 'FAIL',
      date: '2026-09-24',
      summary:
        'Inoculation-day estimate hit a grid edge for 2 of 5 targets (limit 1). P0-2 misspecification detection PASS (10/10). P0-3 negative control NON_IDENTIFIED_STRUCTURAL PASS.',
      citations: ['docs/audits/2026-09-24-phase0-exit-audit-sol-FAIL.md'],
    },
    {
      id: 'v13-phase0b',
      title: 'V1.3 Phase 0b — redesigned synthetic recovery',
      verdict: 'NOT RUN',
      date: null,
      summary: 'Frozen predeclaration; one campaign pending review.',
      citations: ['docs/research/v1_3/2026-09-25-phase0b-predeclaration.md'],
    },
  ],
  note: 'No real Jersey data are fitted until a Phase-0 gate passes.',
};
