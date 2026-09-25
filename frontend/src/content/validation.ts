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
      arms: [
        {
          id: 'p0-1',
          name: 'P0-1 synthetic recovery',
          verdict: 'FAIL',
          summary:
            '19/20 predicates pass; inoculation offset at a grid boundary for 2/5 targets (limit 1/5); selections 0, 2, 2, 2, 4',
        },
        {
          id: 'p0-2a',
          name: 'P0-2A wrong reporting delay',
          verdict: 'PASS',
          summary: 'detected 5/5 (D=5, U=0; threshold 3)',
        },
        {
          id: 'p0-2b',
          name: 'P0-2B wrong ascertainment',
          verdict: 'PASS',
          summary: 'detected 5/5 (D=5, U=0; threshold 4)',
        },
        {
          id: 'p0-3',
          name: 'P0-3 negative control',
          verdict: 'PASS',
          summary: 'NON_IDENTIFIED_STRUCTURAL; factor estimate null',
        },
      ],
      citations: ['docs/audits/2026-09-24-phase0-exit-audit-sol-FAIL.md'],
    },
    {
      id: 'v13-phase0b',
      title: 'V1.3 Phase 0b — redesigned synthetic recovery',
      verdict: 'NOT RUN',
      date: null,
      summary: 'Frozen predeclaration; one campaign pending review.',
      arms: ['P0-1', 'P0-2A', 'P0-2B', 'P0-3'].map((name) => ({
        id: name.toLowerCase(),
        name,
        verdict: 'NOT RUN' as const,
        summary: 'frozen; campaign pending review',
      })),
      citations: ['docs/research/v1_3/2026-09-25-phase0b-predeclaration.md'],
    },
  ],
  note: 'No real Jersey data are fitted until a Phase-0 gate passes.',
};
