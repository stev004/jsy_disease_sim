G41 OWNER RULING: REJECT

<!-- Author: Fable model-owner subagent, acting under Steven's standing delegation of model-owner science rulings (GATES.md, "Scientific-corrections rulings", 2026-09-19: "make decisions for me on model-owner science rulings"; used for G35-B on 2026-10-22). Brief: docs/runs/2026-11-20-g41-owner-ruling-brief.md.txt. Read-only ruling on docs/research/v1_3/2026-11-19-g41-confirmatory-design-opus-DRAFT.md (commit e8a2401, committed-bytes sha256 d46c46a92790934bd9dd19b31e619c2dae016a4ebe8036a8aa2306bd357c033e, verified by `git show e8a2401:<path> | sha256sum`). This file is the only file written. No commit, simulation, build, fit or test was run. -->

## 1. What is rejected, and what is not

**Rejected:** running the confirmatory study *as designed* in the draft, and therefore freezing the draft. No pre-check, freeze, implementation or campaign follows from this ruling.

**Not rejected:**
- Steven's G41 = B decision. It stands as his decision. This ruling returns one question to him (§5), because the draft produced information he did not have when he chose B.
- The draft's workmanship. It is faithful to frozen G35-B arm (i), it changes only what it says it changes, and its exploratory numbers reproduce (§2). The defect is in what the design can tell anyone, and the draft itself names it (§7.3 "one library draw", §15).

**This ruling changes no science.** No grid, truth, tolerance, bias limit, threshold, seed, objective, level, predicate or verdict is altered, in G35-B or anywhere else. The G41 seed series (84xxx, 85xxx, 96xxx, 97xxx) stay unused and unbuilt.

**Status phrase:** unchanged from DIRECTOR.md: "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B FAIL, i PASS, ii FAIL, iii FAIL". No G41 token is added, because no G41 study is declared. Arm i remains a screening pass only. Real-data fitting stays STOPPED (G34 A+B).

## 2. Basis

Read in full: the draft; the frozen G35-B predeclaration; my 2026-10-22 ruling and clarifications 1 and 2; the G35-B exit audit (CONFIRMED); `.claude/DIRECTOR.md`; `.claude/GATES.md` G41 (Resolved); `.claude/RUN.md`. Repo HEAD at reading: `d0a5519d2e4aaf98df2f968a386db66dd7c4bdf6`; `git diff --stat 0c9c371 HEAD -- src configs tests scripts` empty.

**Independent check of the draft's exploratory numbers.** I re-scored the retained, read-only G35-B arm-(i) records (`arm_i/blind_estimates/*.json` and `arm_i/descriptive_estimates/{A,B_prime,C_prime,D_prime,A_union_B_prime}/*.json` in `/home/steven/jos-g35b-campaign-20261022T234254Z`) with my own stdlib script, applying predicates 4–8 with exact decimal arithmetic. Nothing was written to the bundle. Results, all labelled **EXPLORATORY, not gate inputs**:

| G35-B library | R | Hits b/o/s/a | Joint | Boundary b/o/s/a | Mean offset bias | Predicates 4–8 |
|---|---:|---|---:|---|---:|---|
| A | 3 | 10/7/9/10 | 7 | 0/3/0/0 | +0.1 | not met |
| B′ | 3 | 8/6/7/8 | 5 | 0/2/0/0 | −0.4 | not met |
| C′ | 3 | 8/6/7/6 | 5 | 0/3/1/0 | +0.1 | not met |
| D′ | 3 | 8/8/8/8 | 7 | 0/0/0/0 | +0.3 | met |
| A∪B′ | 6 | 8/3/7/7 | 3 | 0/3/0/0 | −0.6 | not met |
| all 12 | 12 | 10/8/8/10 | 6 | 0/2/0/0 | −0.2 | met |

- Every cell equals the draft's table. Library A and "all 12" equal the exit audit's B and i rows.
- The draft's crude bootstrap (target outcome vectors resampled with replacement, 20,000 resamples, seed 20261119) reproduces: 0.417 / 0.357 / 0.331 for the ten all-12 vectors at N = 10 / 20 / 30, and 0.243 / 0.131 / 0.081 for the forty R = 3 batch vectors. These are resampling frequencies. They are not probabilities of any real design, not power estimates and not intervals, and they ignore that all targets share one library.
- The draft's binomial table (§7.3) recomputes exactly.
- One arithmetic error in the draft, unrelated to the verdict: §9 says the pre-check builds "N + 22" process seeds. The correct count is N + 28 (N targets + 10 target reserves + 12 candidates + 6 candidate reserves; 48 at N = 20, as the §17 list correctly shows).

## 3. Why the study as designed is not worth running

The reasons are in order of weight. The first two are structural and do not depend on any bootstrap number.

**3.1 The verdict would be one more draw of the thing that varies.** Every target is scored against the same 12-replicate candidate library, so the campaign delivers one library draw, however many targets it has. The retained records show that the library draw, not the target set, is what moves the result:
- four independent R = 3 libraries on the same ten targets gave joint counts 7, 5, 5, 7 and offset hits 7, 6, 6, 8; one of them met predicates 4–8;
- the R = 6 library (A∪B′) did worse than either of its halves (joint 3; offset hits 3; offset bias −0.6, beyond the 0.5 limit);
- four-batch offset agreement was 0/10.

The result is not monotone in R across these nested libraries, and the library-to-library variation at R = 12 is **unknown**: G35-B contains exactly one R = 12 library. G41 as designed would add a second and stop. Two draws cannot separate "R = 12 helps" from "this library happened to land well or badly", and raising N does not help, as the draft says.

**3.2 The gate is being asked about a design that sits at its threshold.** Arm (i) passed on four counts exactly at their inclusive limits. For a design whose true per-target rates are at the limits, the binomial table alone gives a single-predicate pass chance of 0.68 at N = 10 and 0.63 at N = 20, before the other predicates and the shared library are counted. So on the most favourable reading that the retained data support, the outcome is close to a coin toss weighted toward FAIL. The study has a high chance of PASS only if the true rates are near 0.9, and nothing retained supports that.

**3.3 Neither outcome would carry the weight it is meant to carry.** Illustratively, using the crude resampling frequencies and nothing stronger:
- FAIL is the more frequent outcome both for an "arm-(i)-like" design (about 0.64 at N = 20) and for an "R = 3-like" design (about 0.87). A FAIL therefore says almost nothing about whether R is the factor. It would be recorded as "not confirmed", which is the position the project is already in.
- PASS occurs at a non-trivial frequency for an "R = 3-like" design (about 0.13 at N = 20, 0.24 at N = 10). Steven's option text makes a G41 PASS the condition for reconsidering real-data fitting. As model owner I would not advise reopening that question on a second threshold-level pass that is conditional on one library draw, and the draft's own PASS reading concedes the condition. A PASS would lead straight to a request for the multi-library evidence this design omits.

A campaign whose likelier outcome is uninterpretable and whose other outcome is insufficient for its stated purpose is uninformative in the sense that matters: it would not change the next decision.

**3.4 Cost is not the objection, and that points to the remedy.** Campaign compute is small: G35-B arm (i) measured about 14 minutes for 225 latent calls and 5,625 transforms. The real cost is two numerical implementation units, an independent review, a merge gate, a campaign gate and an exit audit, plus the fresh seeds and Steven's attention, all spent on one draw. The same machinery could carry several independent libraries for minutes more compute each (unmeasured for that design; linear scaling is unreliable). The missing piece is a declared way to read several library results, and that is a change to the pass/fail rules, which is Steven's call (§4).

## 4. Ruling on target count N and "same pass/fail rules" (brief item 4)

- **A fraction-preserving change of N honours Steven's option text "same pass/fail rules" and does not need his separate decision.** The predicates, the threshold fractions (4/5, 3/5, ≤ 1/5), their inclusive reading and the integer arithmetic are unchanged; only the number of targets they are applied to changes. This follows G35-B owner decision 3 (5 → 10). Moving from 10 to 20 never makes a PASS easier for a design at or below the thresholds, so it cannot be read as tuned toward confirmation. It must be disclosed to Steven as a change of N, with the binomial table, whenever it is used.
- **Scoring more than one candidate library, with any rule that combines or selects among their results, does not honour "same pass/fail rules" and "one campaign" as written.** It needs Steven's own decision, and then an owner-ruled predeclaration of its own.

This ruling stands for any successor design. It is the only part of this document that binds beyond the rejection.

## 5. What Steven should decide instead (for the director to park as a gate)

**Question:** G41 = B commissioned a confirmatory study under "one campaign, same pass/fail rules". The owner has rejected that design as uninformative: one candidate library gives one draw, a FAIL is the likelier result whether or not replicates matter, and a PASS would not be enough to reconsider real-data fitting. What follows?

- **B2 — Redesign to measure library-to-library variation (owner recommendation if the calibration path is still wanted).** Commission a new design draft in which several independent R = 12 candidate libraries are scored against the same fresh targets, the frozen arm-(i) gate is computed unchanged per library, the R = 3 batches inside those libraries serve as a concurrent reference, and the reading of the across-library counts is declared in advance. This changes "same pass/fail rules" at the study level, which is why it is Steven's decision. **Explicit unknowns, not chosen here:** the number of libraries, the number of targets, and the rule for reading the library results. They must be argued structurally by the design consultant and ruled by the owner; none may be taken from the §2 table. Synthetic only; outcomes authorize nothing beyond input to a later Steven gate.
- **A — STOP.** Record G35-B as the final synthetic design study. The offset non-identifiability finding stands; arm i stays a screening result only. This is the original G41 default and is fully defensible on the evidence in hand.
- **B1 — Run the draft as designed anyway.** Steven may overrule this rejection. If he does, the contingent rulings in §6 apply and no second owner pass is needed. The owner's advice is against it for the reasons in §3.
- **C — Labelled demo**, as in the original G41 option text.

**Default on no answer: HOLD.** Nothing is pre-checked, frozen, implemented or run. STOP is not the default, because that would reverse Steven's B by silence.

**Owner's order of preference:** B2 if Steven still wants to know whether more replicates can make the offset recoverable; otherwise A. B1 last. Which goal the project pursues is Steven's product decision, not a science ruling.

## 6. Contingent rulings (INACTIVE)

These take effect **only** on Steven's explicit chat decision for B1. Until then the director must not act on them, and nothing in this section authorizes a pre-check or a freeze. If activated, the verdict for the draft becomes ACCEPT WITH AMENDMENTS, with the following and nothing else.

**The nine questions:**
1. **N = 20**, thresholds 16/20, 12/20, ≤ 4/20. Fraction-preserving N is within "same pass/fail rules" (§4).
2. **Control: option (A).** No gated control; the R = 3 and R = 6 sub-library references are descriptive, in "met / not met" vocabulary.
3. **One library draw: accepted only as a declared limitation**, with amendment A3.
4. **Seats: the draft's default and its §12 substitution list are accepted** (implementer gpt-6.1-sol @ high; reviewer Claude Opus 5.5 @ high; exit auditor gpt-6-astra @ high). The lineage block must disclose that the reviewer shares a model with the design consultant and the director.
5. **Retention: accepted.** Target latent truth retained, candidate latent truth not. The recomputability of the P3 flags is accepted as an explicit unknown for U1 to establish.
6. **Status token: accepted** ("G41: <PASS|FAIL|VOID>" appended; "G41: not run" from the freeze until the campaign completes).
7. **Retired G35-B reserves** (`82011–82015`, `83013–83017`): excluded as earlier sets.
8. **Reserve sizes** (10 target, 6 candidate): accepted as a declared margin, not an estimate. Exhaustion returns to the owner.
9. **Exploratory §7.3 material: move it out** (amendment A2).

**Amendments:**
- **A1. §9, "Outside the campaign"** — replace "the pre-check builds N + 22 process seeds (48 at N = 20)" with "the pre-check builds N + 28 process seeds (48 at N = 20)".
- **A2. §7.3** — delete everything from "**EXPLORATORY illustration (not a gate input…**" to the end of §7.3, and replace it with: "An exploratory re-scoring of retained G35-B records is filed separately as `<PLACEHOLDER: EXPLORATORY note path, committed-bytes sha256>`. It is not a gate input and no value here is taken from it. It warns that a FAIL is the more frequent outcome under crude resampling even for a design behaving as G35-B arm (i) did." The director files the deleted text verbatim as that note, labelled EXPLORATORY, before the freeze. In §7.5, replace the bullet beginning "The exploratory table in §7.3 shows…" with: "One R = 3 library is a single noisy comparator. Four descriptive R = 3 references are more informative than one gated control and cost no simulation." In §15, replace "Exploratory numbers in §7.3" with "Exploratory numbers in the cited note".
- **A3. §7.4, both readings** — append to the PASS and the FAIL reading alike: "One candidate-library draw cannot separate the factor from library-to-library variation, which this campaign does not measure."

**Pre-freeze order if activated:** Steven's B1 decision recorded in the trail → commit of this ruling (if not already committed) → builds-only seed pre-check of the §17 list on that commit, with the host-disk check → mechanical freeze with A1–A3 applied verbatim. Nothing before the commit that authorizes it.

**Changed by these contingent amendments:** one workload count (A1, a correction), the location of exploratory text (A2), and two reading sentences (A3). No grid, threshold, seed, objective, level or predicate.

## 7. Director obligations now

1. File and commit this ruling via `fm.sh sync` `[skip ci]`; record its committed-bytes SHA-256 in the trail.
2. Park the §5 gate in `GATES.md` with default HOLD, quoting the options as written. Add no option, default or rule of your own.
3. Do **not** run the seed pre-check and do not freeze. Run `g41-predecl`'s predicate (an owner-ruled, frozen predeclaration) is not met and cannot be met without Steven's answer; report it as stopped on a gate, not as failed work.
4. Keep the status phrase exactly as in §1.

## 8. Limits of this ruling

- The §2 table and the resampling frequencies come from ten shared targets and one campaign. They are illustrations and carry no precision. The rejection rests on §3.1 and §3.2, which hold without them.
- Library-to-library variation at R = 12 is unknown. This ruling does not claim R = 12 does not help; it says the drafted study could not show whether it does.
- No statement here is a calibration, validation or coverage claim, and no spread quoted is a confidence interval.
