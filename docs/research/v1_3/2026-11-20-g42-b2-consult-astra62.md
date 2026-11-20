<!-- G42-B2 design consult, one of three independent consultants on one shared brief (docs/runs/2026-11-20-g42-b2-consult-brief.md.txt) at main 6708ad238860872a5ea548943fc004a0424cb261. Consultant: gpt-6.2-astra @ high via codex-cli 0.170.0 in WSL, read-only sandbox, clone ~/jos-g42-astra-ro. Tokens 76,404. Raw log docs/runs/2026-11-20-g42-b2-consult-astra.log. Report (.last.md) filed verbatim by the director; links point into the consultant's WSL clone. CONSULT ONLY — not a ruling, not frozen. -->

gpt-6.2-astra @ high

## 1. Estimand

I recommend **22 independent R = 12 libraries crossed with the same 20 fresh synthetic targets**. The primary quantity is \(p_T\), the probability that a fresh candidate library passes the complete arm-(i) gate on the particular target panel \(T\), under the declared seed and build rules. The observable is \(K\), the number of the 22 libraries that pass. This directly addresses what G35-B sampled only once.

I propose that **stable** mean a gate-pass probability above 0.80 on this panel. In practical terms, a method whose verdict fails to reproduce on one library draw in five is too draw-sensitive for a positive confirmation. That is a proposed **owner judgment**. The 0.80 has a different denominator and justification from P5’s four-fifths target threshold. Its value cannot be learned from G35-B.

A **yes** means the study supports stability by that definition. A **no** means it supports a pass probability below the benchmark. **Can’t tell** means the observed count cannot distinguish the two sides at the declared evidential standard. In every case, report whether changing the library actually changed a verdict. Uniform failure and mixed verdicts answer different questions, even when both rule out stable recovery. All readings apply to this synthetic scenario, grid, objective and target panel. [Owner ruling §§3–5](/home/steven/jos-g42-astra-ro/docs/research/v1_3/2026-11-20-g41-owner-ruling.md)

## 2. Number of libraries and targets

**L = 22** is the smallest fixed design that can tolerate one failing library and still give a positive reading with at most a 5% chance of doing so when \(p_T\leq0.80\). For independent library draws at the benchmark, the probability of at most one failure is \(0.8^L+L(0.2)0.8^{L-1}\). It is 0.0576 at 21 libraries and 0.0480 at 22. Allowing one exception is deliberate. A single draw can demonstrate sensitivity without settling how common it is. The benchmark, one-exception allowance and directional error budget are the owner’s choices. Together they determine \(L\), without an assumed pass rate or bootstrap estimate.

**N = 20** gives each target five percentage points of weight in a count predicate. It is the smallest multiple of five that halves the leverage of a single target relative to G35-B. All three threshold fractions remain exact. Each additional target costs one build, one latent run and one transform, plus scoring against every library and sub-library. More targets improve the resolution of a library’s gate but cannot substitute for another library draw. They also increase the opportunity for a single truth-viability failure or global tie to defeat an all-target predicate.

The owner requires disclosure to Steven of how changing \(N\) changes the gate’s behavior. The following is **design arithmetic** for hypothetical independent target hits conditional on one library. Each entry gives the probability of meeting the indicated count threshold at **N = 10 → N = 20**. These are single-predicate probabilities.

| Hypothetical target hit rate | P5, at least 4/5 | P6, at least 3/5 |
|---|---:|---:|
| 0.5 | .055 → .006 | .377 → .252 |
| 0.6 | .167 → .051 | .633 → .596 |
| 0.7 | .383 → .238 | .850 → .887 |
| 0.8 | .678 → .630 | .967 → .990 |
| 0.9 | .930 → .957 | .998 → 1.000 |

For P8, use the P5 column with the probability of a non-boundary selection. Enlarging the panel improves discrimination away from a threshold and leaves substantial uncertainty at the threshold. [G41 draft §7.3](/home/steven/jos-g42-astra-ro/docs/research/v1_3/2026-11-19-g41-confirmatory-design-opus-DRAFT.md)

## 3. Independent libraries and shared targets

Generate the 20 target process/observation pairs once. Give every library the **same observed target bytes**, verified by hash. A verdict difference between two complete libraries can then be attributed to changing the candidate draw on those targets.

Each library gets 12 fresh process/observation pairs in four predetermined batches of three. Allocate both seed streams independently of outcomes under one documented pseudorandom allocation rule. Use disjoint seed pools across libraries, targets, roles and earlier campaigns, including retired probes and reserves. I would leave the rejected G41 seed series unused for unambiguous lineage. Within a replicate, preserve the matched network/outbreak seed, fixed candidate observation namespace across cells, latent reuse across detection pairs, and frozen summation order. Reusing the process seed while changing only the observation seed would miss part of the variation of interest.

Commit the owner ruling and allocation rule before any builds-only pre-check. Give each library its own ordered process reserves and the targets a separate pool. Replace only pre-freeze build exceptions, in declared order, preserving the observation seed and batch position. Keep successful fallback builds and disclose them. Reserve exhaustion returns to the owner. Freeze final seeds and M2/M3/M4 logical hashes before execution. Score poor candidates and keep uninformative targets. The binomial reading assumes the resulting libraries behave as independent draws under this common procedure, conditional on \(T\).

## 4. Per-library gate and across-library reading

Apply **P1–P10 conjunctively to each library**. Preserve the 625-cell grid, 34 report dates, square-root objective, tie rule, profile-gap identification rule, tolerances and exact decimal bias limits. P1–P3 check completion, every target’s viability, chronology and conservation. P4 requires zero global ties. P5 requires at least 16 identified, within-tolerance targets **in each dimension**. P6 requires at least 12 targets meeting all four dimensions jointly. P7 uses the absolute mean signed error in each dimension. P8 independently counts at most four outer-grid selections per dimension. P9 checks frozen provenance and blind read-back. P10 checks exact measured work, with shared target work counted once in the campaign ledger. Equality at every inclusive endpoint qualifies. [Frozen G35-B §§6–7](/home/steven/jos-g42-astra-ro/docs/research/v1_3/2026-10-22-g35b-predeclaration.md)

For a complete, audited campaign, freeze this second-level reading:

| R = 12 libraries passing | Reading on the shared panel |
|---|---|
| **21–22 of 22** | **Yes.** Supports \(p_T>0.80\). At 21, explicitly report the library that failed and its failed predicates. |
| **14–20 of 22** | **Can’t tell** which side of 0.80 is supported. Both verdicts occurred, so sensitivity to the draw was directly observed. |
| **0–13 of 22** | **No.** Supports \(p_T<0.80\). At 1–13, the verdict changed with the draw. At zero, recovery failed throughout. State whether a shared target predicate forced that result. |

These are exact one-sided binomial decisions with a maximum 5% error **in each direction**. At \(p_T=0.80\), \(P(K\ge21)=0.0480\), \(P(K\le13)=0.0201\), and \(P(K\le14)=0.0561\). Hence 14 belongs in the middle and 21 in the upper row. The middle is a substantive result. There is no tie-break, extension or substitution.

Publish all 22 verdicts and predicate vectors. Only the count of complete library PASS verdicts enters the table. Pooling hits across libraries could manufacture a passing average when every library fails a different predicate. Steven’s B2 decision permits a new study-level reading, and the owner must rule on its exact form before freeze. A software exception or independently established defect invokes the campaign VOID procedure. A scientific FAIL stands. A partial denominator has no reading.

## 5. Concurrent R = 3 reference

For each library, reprofile its four R = 3 batches on the same 20 targets. Report each batch’s ties, dimension hits, joint hits, signed mean biases, boundary counts and P4–P8 **met / not met**. Beside the parent library, show how many of its four batches met those criteria and which targets changed offset or joint-hit status. Retain the frozen A∪B′ R = 6 descriptive, fixed-tuple batch range and median, and four-batch offset agreement. Agreement uses four equal, non-null reprofiled offsets. This measures a different property from identification or recovery of the true offset.

The reference shows whether a full-library result also occurs among its thirds and whether aggregation moves the same targets toward or away from recovery. The 88 batches share targets, and each contributes to its parent’s objective. Counting them as independent controls against the 22 parents would misrepresent that pairing. Keep them descriptive. They supply neither a second gate nor a means of rescuing or vetoing the first. Spreads describe stochastic replicate variation. [G35-B scorer and agreement rule](/home/steven/jos-g42-astra-ro/src/jersey_outbreak/g35b_design_study.py:1190)

## 6. What I would change in the framing

Ask **“How reliably does a fresh library pass on these targets?”** and report separately **“Which targets change their four-dimensional recovery when the library changes?”** Two passing libraries can recover different targets. A target-by-library matrix of joint hits and selected offsets makes that visible without adding a predicate.

I would use one fixed campaign. G35-B’s four threshold-equality counts and 0/10 batch agreement motivate measuring this variation. They do not establish its rate at R = 12. The exploratory Phase-0b diagnostic also found both offsets that moved under replicate deletion and boundary choices that persisted. A mixed B2 result could establish draw sensitivity while leaving the underlying timing–detection tradeoff unresolved. If Steven needs a claim that generalizes to *another target panel*, he should commission replication over panels as a separate estimand. G34 remains STOPPED. [Confirmed exit audit, O5](/home/steven/jos-g42-astra-ro/docs/audits/2026-11-19-g35b-campaign-exit-audit-opus-CONFIRMED.md) · [Exploratory ridge diagnostic, Q3–Q5](/home/steven/jos-g42-astra-ro/docs/research/v1_3/2026-09-29-phase0b-ridge-diagnostic-EXPLORATORY.md)

## 7. Compute and work caps

| Proposed exact campaign cap | Calculation | Count |
|---|---:|---:|
| Parent builds | \(20+22(12)\) | 284 |
| 30-day latent calls | \(20+22(12)(25)\) | 6,620 |
| Two-channel report transforms | \(20+22(12)(625)\) | 165,020 |
| Gate loss evaluations | \(22(20)(625)\) | 275,000 |
| Descriptive loss evaluations, four thirds plus fixed R = 6 | \(5(22)(20)(625)\) | 1,375,000 |

Each library must account for 625 complete cells. Before freeze, specify a separate exact pre-check cap of 284 primary process builds plus every declared process reserve. No horizon probe is needed. Enforce counts before dispatch and reconcile measured totals. Wall time is a disclosure.

**EXPLORATORY planning estimate.** G35-B’s roughly 14½ minutes for arm (i) bought **nine** incremental candidates because B had already supplied three candidates and the targets. Scaling its candidate work by \(22\times12/9\) gives roughly **seven hours serial**. That is an order-of-magnitude estimate. Scoring more targets, retention, host I/O, sealing and independent audit have different costs. The old harness also hard-codes ten target seeds and requires a completed B generation. Budget for a numerical declaration/evaluator unit and a generation/retention unit, independent implementation review, Steven’s merge and campaign decisions, and an independent exit audit. [Campaign timing disclosures](/home/steven/jos-g42-astra-ro/docs/runs/2026-10-23-g35b-campaign-summary.json) · [Existing evaluator](/home/steven/jos-g42-astra-ro/src/jersey_outbreak/g35b_design_study.py:481)

## 8. Biggest risk and predeclaration guard

**One shared target can make 22 failures look like 22 pieces of evidence about candidate libraries.** For example, if one truth fails P2, every library fails regardless of its candidate surface. Freeze the required reading for that case: “All libraries failed the complete gate. The shared target condition forced every verdict, so this panel could not discriminate among candidate draws by gate outcome.” Preserve the scientific failures and report the per-library P4–P8 results descriptively. Never remove the target or regenerate the panel.

Retain shared target latent events, report tables and diagnostics, all candidate tables with seed lineage, and all blind surfaces. Hash, persist and read back every blind fit before any truth join. Require the exit auditor to identify which P2/P3 fields can be reconstructed from raw records and which can only be checked for consistency. This directly addresses the prior audit’s O4 limitation. Freeze the across-library wording, count boundaries and target-by-library display before execution. [Exit audit, O4](/home/steven/jos-g42-astra-ro/docs/audits/2026-11-19-g35b-campaign-exit-audit-opus-CONFIRMED.md)

## Where I expect other designers to differ

The consequential disagreement is how much reliability Steven needs. Fewer libraries and a unanimity rule cost less but give one exception decisive weight. A looser majority rule answers whether recovery is usual and can accept substantial draw sensitivity. My 22-library proposal spends compute to allow one exception while requiring evidence of high reliability. Its price is a wide inconclusive region: even if \(p_T=0.90\), the probability of a yes is only 0.339. **The owner should accept that tradeoff explicitly before freeze.**

Consult basis was detached HEAD `6708ad238860872a5ea548943fc004a0424cb261`, matching local `main`. All work was read-only.