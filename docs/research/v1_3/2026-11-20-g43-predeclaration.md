# G43 multi-library synthetic study predeclaration: six independent R = 12 candidate libraries on one shared target panel (FROZEN 2026-11-20)

<!-- Drafted by the design author and drafter (Claude Fable 5.2, claude-fable-5-2, @ high), foreman run g43-predecl, brief docs/runs/2026-11-20-g43-predecl-draft-brief.md.txt (committed-bytes sha256 c69a7a4ed8e22777149de140bf73c029fcc1afa56052d8b5202e185f5e619ebc, commit 55c03c9); draft committed at 55bb491 (committed-bytes sha256 709bc9f3503d392886366ac59c8be205066386a52a22175e868cae1fd367f590). Owner-ruled (gpt-6.2-sol @ high, ACCEPT WITH AMENDMENTS A1–A10) and mechanically frozen by the director's implementer, 2026-11-20. Every value left open in the draft was filled mechanically from filed evidence, never chosen by hand. -->

## 1. Status and lineage

**Status:** FROZEN (owner ruling ACCEPT WITH AMENDMENTS A1–A10 applied; §18). This document is not a Phase 0c, not a V1.3 gate, not a second G35-B campaign and not the rejected G41 confirmatory study. Status phrase until this text is frozen: "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B FAIL, i PASS, ii FAIL, iii FAIL". From the freeze until a campaign completes, the phrase in §7.11 applies. Real-data fitting stays STOPPED (G34 A+B) whatever the outcome.

**Authority.**
- G41 was resolved B by Steven on 2026-11-19. The owner REJECTED the one-library confirmatory design as uninformative (`2026-11-20-g41-owner-ruling.md` §3) and returned one question to Steven.
- G42 was resolved B2 by Steven on 2026-11-20 (`.claude/GATES.md`, Resolved): several independent R = 12 libraries on the same fresh targets, the frozen arm-(i) gate unchanged per library, the R = 3 batches as a concurrent reference, and the across-library reading declared in advance.
- G43 was resolved F on 2026-11-20 by the director under Steven's delegation (`.claude/GATES.md`, Resolved; trail row `g43-F`): the Fable 5.2 design goes forward to this draft.
- None of these authorizes implementation or a campaign. Both are later Steven gates (§12).

**Seat disclosure.** The owner ruling on this draft is assigned to gpt-6.2-sol @ high, which proposed the rival design (22 libraries, a 0.80 reliability standard). The drafter is the author of design F. §7.5 and §7.6 are written to be ruled on by a reader who prefers the rival design.

**Designed after the results were seen.** This study was designed after Phase 0, Phase 0b, the ridge diagnostic, the complete G35-B campaign, its exit audit and the G41 rejection. Every choice below is argued from structure, from frozen text, or from grid-independent arithmetic. No threshold, level, L, N, seed or reading rule is taken from any retained G35-B number, including the owner's EXPLORATORY table in the G41 ruling §2. Retained results appear only in the lineage block.

**What any outcome authorizes:** nothing beyond input to a separate, later gate decided by Steven. In particular:
- **No outcome licenses:** real Jersey fitting; reopening G34; a claim that Phase 0, Phase 0b or G35-B arm B passed; satisfying the V1.3 plan's Phase-0 gate; nominal coverage; Jersey calibration; named-pathogen validation; or a pass rate, reliability figure or interval for any design.
- **Carried forward from G35-B amendment A1:** this study is synthetic. Neither it nor any successor synthetic study can reopen G34, satisfy the V1.3 plan's Phase-0 gate, or license real-data fitting; reopening real-data fitting would require Steven's explicit chat decision on a new gate and a new owner-ruled predeclaration of its own.
- **No outcome changes any earlier verdict.** Phase 0 FAIL, Phase 0b FAIL and G35-B "B FAIL, i PASS, ii FAIL, iii FAIL" stand. G35-B arm i stays a screening pass only.

**Lineage block** (copied verbatim into `campaign_summary.json` and the exit audit, kept apart from G43 results). SHA-256 values marked † were recomputed by this draft from committed bytes at HEAD `3e44979a6c87dfdc3d393527c4e3cf15c4070b9b` (`git show HEAD:<path> | sha256sum`). The others are carried from the frozen G35-B §1 and the CONFIRMED exit audit and were not recomputed here.

| Item | Value |
|---|---|
| Phase-0 verdict / audit | `phase0_verdict: FAIL` · `docs/audits/2026-09-24-phase0-exit-audit-sol-FAIL.md` |
| Phase-0 bundle `SHA256SUMS` digest | `72cd9a568598530923e08ce20b013d60eb7a3b26553b87c31685ad623f3faa80` |
| Phase-0 predeclaration SHA-256 | `ef67fe49903c3984ca98679eb0470878bc25523baca3bc23a63e4ae7d983a104` |
| Phase-0b verdict / audit | `phase0b_verdict: FAIL` · `docs/audits/2026-09-26-phase0b-exit-audit-sol-FAIL.md` |
| Phase-0b bundle `SHA256SUMS` digest | `a319c5557ffa77c56baebb8341b5fc2e1432f367bdb9d0b34169aa079659032a` |
| Phase-0b predeclaration SHA-256 | `ec8df64630dd50c83b0866a096fba4980453c34232d18114129587274f257451` |
| Ridge diagnostic SHA-256 (binding, committed bytes; G35-B clarification 1) | `8cf4c76612434cbd90c5de4ca9dfd1326422b94a72bd4a63ccff71e95f34908a` |
| G35-B predeclaration | `docs/research/v1_3/2026-10-22-g35b-predeclaration.md`, commit `3972190bd7cde523860fe303b41427c1c95c57eb`, SHA-256 † `2e8358abd9e275a5cf04a58b4ad76313c10964f2da06d46cd0f8a7190733216e` |
| G35-B owner ruling | `docs/research/v1_3/2026-10-22-g35b-owner-ruling-ACCEPTED.md`, SHA-256 † `f84738a9594312f3371f4bb469c5cfaafed265dc5d233ee34f1f0be564d99643` |
| G35-B clarification 1 / 2 | SHA-256 † `2b1d4a5ee6bbab965a32e2abcdc4d00cab769d7d994a015fcf3bf5b0df0346d5` / † `ccae8721871b78b22d84451202ff541cb5836f06f402e176fe97308e296215e0` |
| G35-B harness code SHA | `0c9c3711b4e1be3fa90e9ef7f1e8e883dbdb48d8`. `g35b_design_study.py` † `f133ff3af74395955ad01d8e7f70e8474a020c4addcfd26135ec1b586d3f27f0`; `g35b_constants.py` † `bc766a31ce85e57f824a48ea046adeb0efad148c26133c268ba5f78e5923c494`; `configs/calibration/v13_g35b_design_study.yaml` † `4259c45f01cf122521f6853dba5059415a0ca6317a02d3f883be18e3263105d0` |
| G35-B bundle | `/home/steven/jos-g35b-campaign-20261022T234254Z` (immutable, read-only), `SHA256SUMS` digest `e6649a4b32289ad32cec7862ed79ea75a5123d0231178bebf0db78f0fd54c8fc` |
| G35-B exit audit | `docs/audits/2026-11-19-g35b-campaign-exit-audit-opus-CONFIRMED.md`, last changed at commit `141295f`, SHA-256 † `cf758f26a50986f04c7549ffbb855387d515230739f4f0cd9a27372bec617595`; verdict `JOS G35-B CAMPAIGN EXIT AUDIT: CONFIRMED` |
| G35-B results (final) | B FAIL (P5, P8), i PASS, ii FAIL (P5, P6), iii FAIL (P5, P8) |
| G35-B arm-(i) counts | hits beta/offset/sym/asym 10/8/8/10; joint 6/10; boundary 0/2/0/0; four-batch offset agreement 0/10 (descriptive). Four counts sit exactly at their inclusive thresholds (exit audit O5) |
| G41 rejected draft | `docs/research/v1_3/2026-11-19-g41-confirmatory-design-opus-DRAFT.md`, commit `e8a2401`, SHA-256 † `d46c46a92790934bd9dd19b31e619c2dae016a4ebe8036a8aa2306bd357c033e`. Never frozen; its seed series were never built |
| G41 owner ruling | `docs/research/v1_3/2026-11-20-g41-owner-ruling.md`, SHA-256 † `211646270378a45c83f54ed72350c13b371a92472e5d108455d0b6a6e6e9c77d`; verdict `G41 OWNER RULING: REJECT`; §4 binds successors |
| G42 consults | `2026-11-20-g42-b2-consult-fable52.md` † `691b567d078f2062257b12029427c963352e622c0306f01f4f7c5664d146fd73`; `…-astra62.md` † `361f7f015e707c52f75f07cbd65f0b3799cc25a13c65884076c753be37e38ab9`; `…-sol62.md` † `58c075a467e00026b761060c82aa6c524e800fc693fd2075fece9304cebf57b6`; `…-comparison.md` † `30896351a8114431ad33d8ad5bcabee10e80174ca5c3b28f5ef507df82208de1` (all in `docs/research/v1_3/`, commit `47e90bd`) |
| G42 / G43 resolutions | G42 = B2, Steven, chat, 2026-11-20 (trail row `g42-B2`). G43 = F, director under Steven's delegation, 2026-11-20 (trail row `g43-F`, commits `55c03c9`, `3e44979`) |
| Owner ruling on this draft | `docs/research/v1_3/2026-11-20-g43-owner-ruling.md`, commit `f2062d524c53a52d16837c2c7fe2ca8be6715510`, committed-bytes SHA-256 `ba442e94e4791d9c0a502d4656e580c591c4eed2c8ece50fbaecd6a655cd117c`; gpt-6.2-sol @ high; verdict `G43 OWNER RULING: ACCEPT WITH AMENDMENTS`; no substitution under §12 |

## 2. Question, estimand and scope

**Question.** At R = 12 candidate replicates per grid cell, does the frozen G35-B arm-(i) gate verdict, computed on one fresh shared target panel, depend on which independent candidate library was drawn?

**Estimand.** For the frozen arm-(i) design the gate verdict is a function of two random draws: the candidate library (twelve process/observation pairs in four batches of three) and the target panel. This study holds the panel fixed and shared, and observes the verdict under L = 6 independently drawn libraries. The primary datum is **k**, the number of the six libraries whose frozen gate is PASS on the same N = 20 targets. The supporting data are the per-library predicate vectors and the target × library matrices (§7.9).

**What is not estimated.** The observed count is `k` of six. The library pass probability on this panel remains unknown. The count is not a pass rate, not a reliability figure and not an interval, and no bound on that probability is reported.

**Why the study is worth running where G41 was not.** The owner rejected G41 because one library is one draw of the thing that varies, and because neither outcome would have changed the next decision (ruling §3.1, §3.3). Here every reading class changes it:

| Class (§7.3) | What Steven's next gate has in hand |
|---|---|
| CONSISTENT-PASS | No flip in six draws. Enough to ask whether a reliability study with its own ruled standard, or a second panel, is worth commissioning. Not enough to reopen anything. |
| MIXED | A direct observation that the verdict changes with the library on identical targets. The "more replicates at R = 12" route is answered by measurement in place of an unknown. |
| CONSISTENT-FAIL | No library reproduced recovery. The G35-B arm-(i) pass stands alone as a screening result. |
| NO-READING | Nothing learned about library dependence; the cause is named. |

**Design rules.**
- One fixed campaign. No sequential or two-stage design, no early stopping at the first opposite pair.
- No gated baseline, no gated R = 3 arm, no pooled gate, no combined factor.
- G35-B results are lineage only. They are never pooled with G43 data: the targets differ, and the G35-B library was seen before this design.
- Synthetic only. No real Jersey data enter. The frozen Jersey 2020 serosurvey table (`covid_serosurvey_2020`) is not read, imported or used. No serosurvey is modelled.
- No horizon probe. The window is the frozen 30 days, so the only pre-freeze action on study seeds is the builds-only pre-check (§8).
- Research harness only. Nothing is written through `CalibrationArtifactManifest` or `write_calibration_artifact`.

## 3. What is held fixed, and what changes (brief item a)

**Held fixed, verbatim from frozen G35-B §3, §4.1, §6 and §7.1:**

| Item | Value |
|---|---|
| Dimensions, truths, grids, tolerances, bias limits | the table below, as decimal strings with exact decimal arithmetic |
| Grid | 625 cells, all scored before selection |
| Latent scenario | `ci` mode, 3,000 residents, start `2025-01-06`, exactly 30 latent days. Initial seeds 0. Ten import attempts at `start_date + offset`; background import rate 0; no other imports. All eleven route multipliers `1.0`. Symptomatic probability `0.6`. Constant latent duration 2 days and infectious duration 5 days. Waning disabled. No seasonality or interventions |
| Truth cell | beta `0.08`, offset `2`, symptomatic detection `0.75`, asymptomatic detection `0.25` |
| Observation | two channels (symptomatic, asymptomatic) from `observation_events` `report_date` and `symptomatic`; detection delay 0, reporting delay 2, weekday factors `1.0`, four-day tail, 34 zero-filled dates `2025-01-06` to `2025-02-08` (T = 34) |
| Objective | frozen G35-B §6 at R = 12, T = 34 (§6 below) |
| Candidate structure per library | R = 12 as four independent batches of three, each evaluated at all 625 cells; nesting batch 1 ⊂ batches 1∪2 (6) ⊂ all four (12); replicate order in every sum is batch 1, 2, 3, 4, ascending position within a batch |
| Pairing | network and outbreak seeds match within each process run; one candidate observation config ID across cells (common random numbers within a replicate); candidate latent runs reused across the 25 detection pairs; target runs never serve as candidates |
| Tie and identification rules | τᵢ = 10⁻¹² · max(1, L_min); profile by minimizing over the other three dimensions; identified = unique profile minimum within τᵢ and relative gap ≥ 0.05 with denominator max(P_min, 10⁻¹²); a tied global minimum fails; ordinary float inclusive comparisons for computed gaps; exact decimal arithmetic for signed error, tolerance and bias; no epsilons, and no reinterpretation of equality at `0.05` or `1e-12` |
| Predicates | P1–P10 with the same meaning and the same threshold fractions (4/5, 3/5, ≤ 1/5), integer arithmetic (§7.1) |
| Forbidden | optimizer seed, post-freeze replacement, retry, adaptive grid, pruning, early stopping |

| Dimension | Truth | Grid | Tolerance | Bias limit |
|---|---:|---|---:|---:|
| beta | `0.08` | `0.04, 0.06, 0.08, 0.10, 0.12` | `0.02` | `0.01` |
| offset (days) | `2` | `0, 1, 2, 3, 4` | `1` | `0.5` |
| symptomatic detection | `0.75` | `0.50, 0.625, 0.75, 0.875, 1.00` | `0.125` | `0.0625` |
| asymptomatic detection | `0.25` | `0.10, 0.175, 0.25, 0.325, 0.40` | `0.075` | `0.0375` |

**Changes against G35-B arm (i):**

| Item | G35-B arm (i) | G43 | Why |
|---|---|---|---|
| Seeds | targets `82001–82010`; candidates `83001–83012` | all fresh (§8) | Fresh draws are the point |
| Candidate libraries | one | **six**, independent, each gated separately | G42 = B2 |
| Number of targets N | 10 | **20**, byte-shared across all six libraries | §7.7; within "same pass/fail rules" by G41 ruling §4 |
| Integer thresholds | 8 / 6 / ≤ 2 of 10 | **16 / 12 / ≤ 4 of 20** | Same fractions (§7.1) |
| Batch 1 | byte-shared with the gated B arm | fresh in every library; no gated B arm | No baseline is needed for this question |
| Study-level output | readings table against B | reading class from the six verdicts (§7.3) | G42 = B2; this is the new study-level rule |
| R = 3 / R = 6 | B gate plus descriptives | descriptive reference evaluations only (§7.8) | No second verdict family |
| Retained latent truth | not retained (exit audit O4) | target latent truth retained (§10) | Lets the exit audit recompute P2 and P3 inputs |
| Wall-time disclosure | two sources that disagreed (O1) | one source (§9) | Disclosure hygiene |
| Reviewer line | trail and review only (O3) | also in `campaign_summary.lineage` (§10) | Disclosure |
| Seats | named after the fact (clarification 2) | named in advance (§12) | No later clarification needed |

No grid, truth, tolerance, bias limit, threshold fraction, objective, R, T, tie rule or identification rule changes.

## 4. Design

**Shared target panel.** Twenty fresh target process seeds. Each is run once at the truth cell with its paired fresh observation seed, config ID `v13-g43-target`. The twenty observed target tables are generated once and used, byte-identical and hash-verified, by every library and every sub-library. Sharing is what makes a verdict difference between two libraries attributable to the library alone.

**Six libraries.** Library ℓ (ℓ = 1…6) has twelve fresh candidate process/observation pairs. Each of the twelve process seeds runs at all 25 (beta, offset) latent tuples, and each latent run is observed at all 25 detection pairs with its paired observation seed, config ID `v13-g43-fit`. No seed appears in two libraries or in the target panel.

**Batches.** Positions 1–3, 4–6, 7–9 and 10–12 of a library are its batches 1–4. Membership is fixed by the §8 seed table before the pre-check. Re-partitioning the 72 replicates into other libraries or batches is excluded (§7.10).

**Why R = 12 and four batches of three are not re-argued.** R is the level under study. Its justification is frozen G35-B §4.1 as amended by A2, and is unchanged: R = 12 is the smallest multiple of the baseline replicate count that halves the Monte-Carlo SD of every candidate mean, and each batch has the baseline replicate count, so each is an independent draw of a Phase-0b-shaped objective at every fixed tuple. Any other R is excluded.

**What "library variation" bundles.** The process seed draws the population and network as well as the epidemic, and the observation seed draws reporting. Library-to-library variation therefore mixes population, epidemic and observation noise. This study does not separate them.

## 5. Observation model

Verbatim G35-B §5.1: two channels from `observation_events` `report_date` and `symptomatic`, zero-filled over the 34-date calendar. Reports come solely from `observation_events`. No serosurvey.

## 6. Objective and blind boundary

For target i, library ℓ, cell θ, channel c, date t and the twelve candidate replicates j of library ℓ in the declared order:

\[
m^{(\ell)}_{\theta ct}=\frac1{12}\sum_{j=1}^{12}\sqrt{x^{(\ell)}_{j\theta ct}+3/8},\qquad
L^{(\ell)}_i(\theta)=\frac{1}{2\cdot 34}\sum_{c=1}^{2}\sum_{t=1}^{34}\Big(\sqrt{y_{ict}+3/8}-m^{(\ell)}_{\theta ct}\Big)^2 .
\]

This is frozen G35-B §6 at R = 12, T = 34, computed by the unchanged function `g35b_design_study.loss`. It is not a likelihood. Sub-library fits use the same function with R = 3 (one batch) or R = 6 (batches 1∪2).

**Blind boundary.** The fitter receives only a target's observed tables, the declared grid and one candidate library. Each blind estimate, gate and descriptive alike, is hashed, persisted and read back before any truth join. **All generation and all blind fits for all six libraries complete before any truth join**, so no library can react to another library's results and no truth diagnostic can influence any fit.

## 7. Predicates, reading classes and descriptives

### 7.1 Per-library recovery gate (brief item a)

The G35-B predicates apply to each library separately, with N = 20 in place of 10.

**Integer thresholds and their derivation.** The frozen ten-target counts are 8/10, 6/10 and ≤ 2/10. As fractions they are 4/5, 3/5 and 1/5. The frozen integer tests are hits·5 ≥ 4·N, joint·5 ≥ 3·N and boundary·5 ≤ 1·N. At N = 20:

| Predicate | Frozen count at 10 | Fraction | Integer test at N = 20 | Count at 20 |
|---|---:|---:|---|---:|
| P5, per dimension | ≥ 8 | 4/5 | hits·5 ≥ 80 | **hits ≥ 16** |
| P6, joint | ≥ 6 | 3/5 | joint·5 ≥ 60 | **joint ≥ 12** |
| P8, per dimension | ≤ 2 | 1/5 | boundary·5 ≤ 20 | **boundary ≤ 4** |

Equality at every inclusive endpoint qualifies. P7 divides the exact decimal sum of the twenty signed errors by 20. P2's "ten inoculation acquisitions" is the scenario's ten import attempts and does not scale with N.

`G43 LIBRARY ℓ RECOVERY GATE: PASS` only if all of:
1. All 20 target runs, all 625 candidate cells of library ℓ and all 12 replicates per cell complete without replacement.
2. Each truth run realizes all ten inoculation acquisitions, at least one local secondary infection, reports in both channels, and at least three nonzero combined-report dates.
3. Observation chronology and latent-incidence conservation pass for every truth run.
4. No target has a numerically tied global minimum under library ℓ.
5. Every dimension is identified and within tolerance for ≥ 16/20 targets.
6. ≥ 12/20 targets are identified and within tolerance jointly in all four dimensions.
7. Every dimension's absolute twenty-target mean bias is ≤ its limit (exact decimal). The mean is defined only when all twenty targets have a selected cell; otherwise the predicate is not met.
8. No dimension is selected at an outermost grid value for more than 4/20 targets. This is computed by its own code path. On these grids every outermost value lies outside tolerance, so predicate 8 is implied by predicate 5; the per-dimension count is still reported.
9. Seeds, namespaces, grid, objective, dates, fixed parameters, read-back and blind provenance match this declaration, and every build reproduces its frozen M2/M3/M4 logical hashes.
10. Measured work equals the §9 caps: the shared-panel counts and library ℓ's own counts.

**Status and failure rules (verbatim G35-B):**
- `software_status` and `scientific_status` are kept separate.
- An extinct or uninformative truth fails predicate 2 and is never resampled.
- A poor or extinct candidate is scored.

### 7.2 Three groups of predicates

The frozen gate is a conjunction, and nothing here changes it. For the study-level reading the ten predicates are grouped by what they can depend on.

| Group | Predicates | Depends on the candidate library? |
|---|---|---|
| **Shared-panel** | P2, P3, and the target-side components of P1 (20 target runs complete), P9 (target seeds, namespaces, truth cell, dates, fixed parameters, target build hashes) and P10 (shared-panel work counts) | No. Evaluated once on the shared panel; the same value enters all six gates. |
| **Library-integrity** | the library-side components of P1 (625 cells × 12 replicates; 625 scored cells per target fit), P9 (library seeds, namespaces, read-back, blind provenance, candidate build hashes) and P10 (library work counts) | Yes, but they describe whether the work was done as declared, not whether recovery occurred. |
| **Recovery** | P4, P5, P6, P7, P8 | Yes. These are the recovery criteria. |

For library ℓ define two booleans:
- `nonrecovery_ok_ℓ` = P1 ∧ P2 ∧ P3 ∧ P9 ∧ P10;
- `recovery_met_ℓ` = P4 ∧ P5 ∧ P6 ∧ P7 ∧ P8.

The gate verdict is PASS if and only if both are true, which is the frozen conjunction.

**Attribution note.** The evaluator reports each condition of P2 and P3 as its own field, computed from its own inputs. The G35-B implementation's `TruthDiagnostics.viable` (`phase0_campaign.py:641–653`) also folds chronology, conservation and namespace evidence into its P2 value. That affects only which predicate is named as failed, never a gate verdict or a class, because P2, P3 and P9 are all in the conjunction and all in the non-recovery group.

**Predicate evidence (owner amendment A9).** Compute P2 from acquisitions, local secondaries, the two channel totals and the number of nonzero combined-report dates. Do not use `TruthDiagnostics.viable` as P2. P3 is the conjunction of its four existing input checks. Completion is checked under P1 and namespace evidence under P9. P10 reads the operational work ledger, including required descriptive scoring and record counts. Descriptive results and disclosure copies never feed P10.

### 7.3 Across-library reading classes (brief item b; mechanical)

There is **no study-level gate, no study-level PASS/FAIL token and no k-of-L cut**. The study reports the six verdicts, k, and exactly one class word, selected by the first matching row.

**Precedence rule (owner amendment A3).** "A campaign exception, an established departure from the declaration, or any false P1, P9 or P10 component makes the campaign VOID. A VOID campaign has no library verdict lines, counts `k`, `k′`, `m`, or `m_ℓ`, class, or reading. Seal the available evidence. For an intact campaign, any false P2 or P3 produces NO-READING, with cause `shared_panel` and all failed target conditions listed. All six gates are FAIL in that case. Report `k = 0` and the descriptive `k′`, `m`, and `m_ℓ`. Otherwise classify by `k`: six CONSISTENT-PASS, one through five MIXED, zero CONSISTENT-FAIL."

| Order | Condition (all exact, no judgment) | Class |
|---:|---|---|
| 1 | Campaign status is VOID under §12: a campaign exception, an established departure from the declaration, or any false P1, P9 or P10 component | **VOID** (campaign status; no class, no reading) |
| 2 | Intact campaign and P2 or P3 is false | **NO-READING** |
| 3 | k = 6 | **CONSISTENT-PASS** |
| 4 | 1 ≤ k ≤ 5 | **MIXED** |
| 5 | k = 0 | **CONSISTENT-FAIL** |

Here k = the number of ℓ with gate PASS. In rows 3–5 every `nonrecovery_ok_ℓ` is true, so k equals **k′** = the number of ℓ with `recovery_met_ℓ` true. k′ is computed and reported in every row except VOID.

**Boundary cases, stated so that none is left to judgment:**
- k = 5 is MIXED. k = 1 is MIXED. The words "nearly", "almost", "majority", "most", "typical" and "best library" are forbidden in every reading and summary.
- Equality meets the applicable count predicate. A library passes only when all ten predicates are met. A library's count margin is reported (§7.9, D1) and cannot change the class.
- **NO-READING, shared-panel cause.** If P2 or P3 is false in an intact campaign, all six gates are FAIL by the frozen conjunction, whatever the libraries did. The cause is recorded as `shared_panel`, with the target seeds and all failed target conditions. Example: one truth run with no local secondary infection. `k = 0` is reported with the descriptive `k′`, `m` and `m_ℓ`.
- In NO-READING the six per-library verdicts stand as computed. No FAIL is reclassified, no target is removed, the panel is not regenerated, and no library is rescored.

**Why NO-READING is defined on P2 and P3 after the VOID rules, and not on "which predicates failed".** A rule of the form "every library failed and only shared predicates failed" has a hole: a shared P2 failure together with a P5 failure in some libraries would be read as CONSISTENT-FAIL although every verdict was forced before recovery was assessed. Row 2 has no such hole. This tightens the common-cause rule in the consult (§17).

### 7.4 Readings (brief items b, i; verbatim, descriptive statements separate from the gate vocabulary)

Angle-bracket fields are filled mechanically from the evaluation. No other word may be added to a reading.

**CONSISTENT-PASS.** "All six independently drawn R = 12 candidate libraries passed the frozen G35-B arm-(i) recovery gate on the same 20 shared synthetic targets. In six draws on this one target panel, the gate verdict was not observed to depend on which library was drawn. This is a count, not a pass rate, not a reliability finding and not an interval: six passes in six draws do not rule out that a substantial fraction of libraries, for example one in five or three in ten, would fail on this panel, and nothing is shown for any other target panel, scenario, grid, objective or level of R. Smallest count margin across the six libraries: <d> target(s); libraries with at least one count exactly at its inclusive threshold: <n> of 6. This authorizes no real-data fitting. It is no more than input to a later gate decided by Steven."

**MIXED.** "<k> of six independently drawn R = 12 candidate libraries passed the frozen G35-B arm-(i) recovery gate and <6 − k> failed it, on byte-identical targets. On this target panel the gate verdict depended on which candidate library was drawn. This is a direct observation, not a statistical inference. Four-dimensional recovery under this gate is therefore not shown to be a property of the level R = 12 on this panel. The observed count is <k> of six. The library pass probability on this panel remains unknown. Failing libraries and their failed predicates: <ℓ: predicates with counts>. Smallest count margin among the passing libraries: <d> target(s). The G35-B arm-(i) PASS remains a screening result only."

**CONSISTENT-FAIL.** "None of six independently drawn R = 12 candidate libraries passed the frozen G35-B arm-(i) recovery gate on the same 20 shared synthetic targets, with every shared-panel and integrity predicate satisfied. In six draws on this one target panel, R = 12 did not produce four-dimensional recovery, and no dependence of the verdict on the library was observed. Failed predicates per library: <ℓ: predicates with counts>. None of these six libraries reproduced the G35-B recovery result. The campaigns differed in libraries, target draws and panel size. This comparison does not identify which difference mattered. Zero of six is a count, not a pass rate and not an interval, and it says nothing about other levels of R. The G35-B arm-(i) PASS remains a screening result only and its verdict is not changed."

**NO-READING.** "No reading on library dependence is issued. <Cause sentence.> The six per-library verdicts stand as computed and are not reclassified; no target is removed and the panel is not regenerated. Predicates 4–8 were met by <k′> of six libraries; this is reported descriptively and licenses nothing."
- Cause sentence, `shared_panel`: "All six library gates are FAIL because a predicate that does not involve the candidate library failed on the shared panel (<target seeds: failed conditions>), so this panel could not discriminate among candidate-library draws by gate outcome."

**VOID.** No reading. §12 VOID rules apply. A VOID campaign has no library verdict lines, counts `k`, `k′`, `m`, or `m_ℓ`, class, or reading; the available evidence is sealed (§7.3).

**What each class does and does not license:**

| Class | Licenses | Does not license |
|---|---|---|
| CONSISTENT-PASS | The statement "no library dependence of the verdict was observed in six draws on this panel", as input to a later Steven gate | Any pass rate, reliability claim or interval; any claim for another panel; reopening G34; real-data fitting; "confirmed" or "validated" |
| MIXED | The statement "the verdict depended on the library drawn, on this panel" | Any rate; any claim that R = 12 "usually" or "rarely" recovers; any claim about other levels of R; any change to a G35-B verdict |
| CONSISTENT-FAIL | The statement "R = 12 did not produce recovery under any of six libraries on this panel" | Proof that R = 12 cannot recover on another panel; proof of the ridge hypothesis; any change to the G35-B arm-(i) verdict |
| NO-READING | Nothing about library dependence | Reading k′ as if it were k; removing the failing target; a rerun without Steven |
| VOID | Nothing | Anything |

The R = 3 reference disclosure sentences (§7.8) are written after the reading under their own key. They never alter, qualify or replace the class.

### 7.5 Why no k-of-L cut is declared

This is the point on which the consultants split.

The study records whether the verdict changed among the six declared library draws on this panel. A reliability decision would require a separately commissioned standard and error budget. The six verdicts, predicate vectors and target-by-library matrices are published for a later Steven decision.

**What CONSISTENT-PASS at L = 6 cannot rule out, stated plainly.** EXPLORATORY DESIGN ARITHMETIC under a hypothetical model in which library verdicts are independent Bernoulli(π) given the panel; π is unknown and is not estimated:

| Hypothetical π | P(k = 6): CONSISTENT-PASS | P(k = 0): CONSISTENT-FAIL | P(MIXED) |
|---:|---:|---:|---:|
| 0.1 | 0.0000 | 0.5314 | 0.4686 |
| 0.3 | 0.0007 | 0.1176 | 0.8816 |
| 0.5 | 0.0156 | 0.0156 | 0.9688 |
| 0.6 | 0.0467 | 0.0041 | 0.9492 |
| 0.7 | 0.1176 | 0.0007 | 0.8816 |
| 0.8 | 0.2621 | 0.0001 | 0.7378 |
| 0.9 | 0.5314 | 0.0000 | 0.4686 |
| 0.95 | 0.7351 | 0.0000 | 0.2649 |

- A design whose libraries fail three times in ten still gives six passes in six about one time in eight. One that fails one time in five gives it about one time in four.
- The table also shows the cost of unanimity: at π = 0.9 the class is MIXED 47% of the time. That is intended. Such a design does depend on the draw, and k/6 is reported.
- All of this is conditional on one target panel. A hard or easy panel pushes all six libraries the same way. No statement about another panel is licensed.

### 7.6 Number of libraries: L = 6 (brief item c; owner-ruled, §18 Q3)

**What L controls.** It is the number of draws of the thing that varies. It is the only lever on the "one draw" defect (G41 ruling §3.1). The reading rule in §7.3 does not depend on L; L only sets how strict unanimity is and what the study costs.

**Argument for 6 (anchored on a frozen precedent, not on a tuned pass rate).** Frozen G35-B §7.3 chose ten targets because they cut the chance that a coin-flip recovery passes the hits predicate to 0.055, and the owner accepted that argument as grid-independent and result-independent. The analogous error here is a coin-flip library verdict (π = 0.5) producing a unanimous class, because both unanimous classes say "no dependence observed". Its probability is 2 · 0.5^L (EXPLORATORY DESIGN ARITHMETIC; same hypothetical model as §7.5):

| L | 2 · 0.5^L | P(k = L) at π = 0.7 / 0.8 / 0.9 | Builds 12L + 20 | Latent calls 300L + 20 | Transforms 7,500L + 20 |
|---:|---:|---|---:|---:|---:|
| 4 | 0.1250 | 0.240 / 0.410 / 0.656 | 68 | 1,220 | 30,020 |
| 5 | 0.0625 | 0.168 / 0.328 / 0.591 | 80 | 1,520 | 37,520 |
| **6** | **0.0312** | **0.118 / 0.262 / 0.531** | **92** | **1,820** | **45,020** |
| 7 | 0.0156 | 0.082 / 0.210 / 0.478 | 104 | 2,120 | 52,520 |
| 8 | 0.0078 | 0.058 / 0.168 / 0.430 | 116 | 2,420 | 60,020 |

L = 6 is the smallest L at which 2 · 0.5^L is at or below the 0.055 the project has already accepted for the analogous target-count error (L = 5 gives 0.0625). The 0.055 is a precedent, not a law.

**Side effect.** L = 6 yields 24 independent R = 3 batches for the reference (§7.8).

### 7.7 Number of targets: N = 20 (brief item c)

**Authority.** G41 ruling §4, which binds successors: a fraction-preserving change of N honours "same pass/fail rules", and "must be disclosed to Steven as a change of N, with the binomial table, whenever it is used". This section is that disclosure.

**What N controls.** It does not add library draws. It sets gate granularity and how much one unusual target can move a verdict.
At N = 20 each target contributes five percentage points to a count fraction, compared with ten at N = 10. One target can still flip a verdict at an endpoint. Twenty doubles the G35-B panel, following the earlier 5-to-10 design precedent, and preserves exact integer cutoffs.

**Binomial table (EXPLORATORY DESIGN ARITHMETIC; grid-independent; per-target success treated as Bernoulli(p) for one fixed library):**

| Per-target rate p | P(hits ≥ 4N/5): N = 10 → 20 | P(joint ≥ 3N/5): N = 10 → 20 |
|---:|---|---|
| 0.5 | 0.055 → 0.006 | 0.377 → 0.252 |
| 0.6 | 0.167 → 0.051 | 0.633 → 0.596 |
| 0.7 | 0.383 → 0.238 | 0.850 → 0.887 |
| 0.8 | 0.678 → 0.630 | 0.967 → 0.990 |
| 0.9 | 0.930 → 0.957 | 0.998 → 1.000 |

The boundary predicate at per-target boundary rate q mirrors the hits column at p = 1 − q.

**Reading of the table.** Discrimination away from a threshold improves. The table describes single count predicates under hypothetical per-target rates. The operating characteristics of the composite gate are unknown. These are single-predicate figures; the composite gate also depends on correlations among predicates and on the shared library, which are unknown.

**Costs and risks of N = 20.**
- One build, one latent call and one transform per extra target, plus scoring against every library and sub-library.
- The all-target predicates (P2, P3, P4) have twice as many chances to bind. One unviable truth run forces NO-READING (§7.3). The rate of unviable truth runs in this scenario is unknown and is not estimated; no viability check of study targets is run before the campaign, because that would be a look at truth.

**Why not 30.** Nothing structural selects it, and at-threshold behaviour does not sharpen (0.607 at p = 0.8).

### 7.8 The R = 3 concurrent reference (brief item e)

**What it is.** Each library contains four batches of three. The 4 × 6 = 24 batches are 24 independent R = 3 candidate libraries, each a Phase-0b-shaped objective, scored against the same twenty targets from tables already generated. In addition, batches 1∪2 of each library give six R = 6 libraries, the frozen nested step.

**How it is read.** For each of the 24 batches and each of the six R = 6 sub-libraries, the predicate 4–8 computation is applied at N = 20 with the §7.1 thresholds. Each record reports per-dimension hit counts, the joint count, per-dimension boundary counts, exact mean biases, the tie count and a boolean `criteria_4_to_8_met`.
- Vocabulary is "met / not met", never PASS/FAIL. These records never enter the status phrase, a verdict line or a class.
- **m** = the number of the 24 batches with `criteria_4_to_8_met`. **m_ℓ** = the number among library ℓ's four batches. Both are reported beside k′, and each m_ℓ is shown beside its parent library's verdict.
- The comparison uses k′ (predicates 4–8), so that the R = 12 and R = 3 sides are the same computation.

**Disclosure sentences, each triggered by an exact integer comparison with no threshold:**
- **S1, exactly when m > 0 and 4·k′ ≤ m:** "On this panel the six R = 12 libraries did not meet predicates 4–8 proportionally more often than their own twenty-four R = 3 batches (R = 12: <k′> of 6; R = 3: <m> of 24)."
- **S2, exactly when m = 24:** "Every R = 3 batch also met predicates 4–8 on this panel; R = 12 is not shown to be necessary here."

For CONSISTENT-PASS, MIXED and CONSISTENT-FAIL, emit S1 exactly when `m > 0 and 4*k′ ≤ m`, and S2 exactly when `m == 24`. Emit S1 then S2 when both apply. Emit neither for NO-READING or VOID. If neither sentence is emitted, no sentence is written; k′, m and every m_ℓ are still reported for every intact campaign. The count of libraries with `recovery_met_ℓ` false and m_ℓ ≥ 1 is reported as `libraries_not_met_with_a_batch_met`, without a sentence.

**Why it is ungated.**
- The batches are nested in the libraries. Each batch contributes one quarter of its parent's transformed candidate mean at each cell, channel and date. The loss squares the residual after forming that mean. The 24 are not an independent control arm against the six.
- A second verdict family would recreate the readings table and the multiplicity that G35-B §7.4 warned about, and would let the R = 12 reading depend on how a short library happened to score.
- Any rule on the difference between k′/6 and m/24 needs a margin, which would be an invented number. S1 and S2 need none.

### 7.9 Descriptives (brief item f; reported, never gated)

Every record carries `label: stochastic_replicate_variation` or `label: descriptive_not_a_gate`. Spreads are stochastic replicate variation, never confidence intervals. No descriptive can change a verdict or a class; the exit audit confirms this by recomputing every verdict and the class with no descriptive input.

- **D1. Per-library predicate vector and margins.** All ten predicates; hit, joint and boundary counts; exact mean biases. Count margins in targets: hits_d − 16 for each dimension, joint − 12, and 4 − boundary_d for each dimension (nine integers; a margin ≥ 0 means the count predicate is met). `min_count_margin` is the smallest of the nine, and `at_threshold` is true when any of the nine is 0. The bias margin, limit − |mean bias|, is an exact decimal string per dimension.
- **D2. Target × library matrices (20 × 6).** Selected cell; joint hit; per-dimension hit; per-dimension identified flag; per-dimension boundary flag; global-tie flag; and the R = 12 re-profiled offset.
- **D3. Per-target row summaries.** The number of libraries with a joint hit (0…6); the number with an offset hit; the number of distinct selected offsets; and `all_six_offsets_agree`, true if and only if all six R = 12 re-profiled offsets are non-null and equal. These show whether misses follow targets (rows) or libraries (columns).
- **D4. Batch descriptives per library, verbatim G35-B §7.2(b).**
  - The re-profiled offset per target under each of batches 1–4 (three replicates each), batches 1∪2 (six) and all twelve.
  - Per fixed tuple, the range and median of the four batch objectives. The median is the arithmetic mean of the middle two of the four sorted values.
  - The count of targets whose four batch offsets agree. **Agreement rule, stated here so that no brief has to add one (DIRECTOR lesson 2026-10-22, G37 F3):** a fit's re-profiled offset is the unique offset whose profiled objective lies within τ = 10⁻¹² · max(1, minimum profiled objective) of that minimum, or null if more than one does. Four batches agree if and only if all four re-profiled offsets are non-null and equal. A global numerical tie in a batch's fit does not by itself make the batch disagree. This is the rule as implemented and reviewed in G35-B (`_offset_descriptive`, `batch_offset_agreement`, `g35b_design_study.py:1202–1233` at `0c9c371`). D3's six-library flag uses the same rule.
- **D5. R = 3 and R = 6 reference evaluations** (§7.8), with m, m_ℓ, k′ and the S1/S2 trigger values.
- **D6. Disclosures.** Per-target and per-candidate `population_fallback_m2` and `population_fallback_m3`; descriptive counts of fallback-built targets and of fallback-built candidates per library; measured counters; wall time. These are disclosures and never gate or subset (G35-B A10 as read by clarification 1 item 2).

**Pooled reference.** The campaign excludes the pooled R = 72 reference. For later EXPLORATORY use of the retained bundle, the definition is library order 1–6, then position 1–12, `loss(target, predictions, 72, 34)`, and P4–P8 at N = 20, reported as met or not met with label `pooled_reference_not_a_tested_level`.

### 7.10 Explicit exclusions (no forking paths)

- any k-of-L cut, majority rule, or pooled-rate criterion;
- any study-level PASS/FAIL token;
- re-partitioning the 72 replicates into other libraries or batches;
- library subsetting, target subsetting (including by fallback status, viability or influence), or any "best library" or "best batch";
- pooling hits across libraries into one gate;
- pooling with G35-B data;
- a gated R = 3 or R = 6 arm, or any rule on the difference between k′ and m;
- the pooled R = 72 reference (§7.9);
- the two-block target descriptive (predicates 4–8 on the first and last ten targets);
- alternative thresholds, re-weightings, alternative R, T, L or N after the freeze;
- any sequential, staged or early-stopped execution;
- any rerun, extension or additional library without Steven's explicit chat decision and a new owner-ruled text.

### 7.11 Status phrase (brief item i)

The existing phrase is kept intact and extended. Status vocabularies never mix: PASS/FAIL are per-library recovery-gate verdicts, VOID is a campaign status under §12, and the class word and readings are descriptive text that never appears in the phrase.

- Until this text is frozen: "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B FAIL, i PASS, ii FAIL, iii FAIL".
- From the freeze until a campaign completes: "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B FAIL, i PASS, ii FAIL, iii FAIL; G43: not run".
- After an intact campaign: "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B FAIL, i PASS, ii FAIL, iii FAIL; G43: L1 <PASS|FAIL>, L2 <PASS|FAIL>, L3 <PASS|FAIL>, L4 <PASS|FAIL>, L5 <PASS|FAIL>, L6 <PASS|FAIL>".
- After a VOID campaign: "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B FAIL, i PASS, ii FAIL, iii FAIL; G43: VOID".

There is one campaign, so VOID is recorded once, at campaign level, with no per-library tokens. The G43 tokens are final only after the exit audit returns CONFIRMED; until then state files append "(exit audit pending)" outside the phrase. The class word may be written beside the phrase in prose, never inside it.

## 8. Seeds and replacement rule (brief item d)

**Disjointness.** All seeds are fresh and mutually disjoint. They are also disjoint from every earlier set below, which the harness holds as an independent module constant, never derived from the supplied config:
- Phase 0: `42001–42005`, `52001–52005`, `43001–43003`, `53001–53003`;
- Phase 0b: `62001–62005`, `72001–72005`, `63001–63003`, `73001–73003`;
- G35-B probe (retired): `81001–81006`, `91001–91003`;
- G35-B study, including the built but unused reserves: `82001–82015`, `83001–83017`, `92001–92010`, `93001–93012`, `94001–94010`, `95001–95003`;
- the never-built G41 series in the rejected draft, retired here for unambiguous lineage: `84001–84030`, `84101–84110`, `85001–85012`, `85101–85106`, `96001–96030`, `97001–97012`.

The G43 series lie in the 86, 87, 98 and 99 thousand-blocks, outside every block above. A `git grep` at HEAD `3e44979` over `src configs tests scripts docs .claude` found none of the G43 seeds listed in §19. Seeds are reproducibility identifiers, not parameters.

**How seeds map to work.** The process seed is the population/network build seed (`build_parent(root, "ci", seed, …)`), and outbreak and network seeds match. Observation seeds build nothing. The effective observation stream is keyed by the latent seed, the observation seed and the config ID (`observation_scheduler.py:61–69`), so one fit config ID across all libraries keeps common random numbers across cells within a replicate, while libraries stay independent through their seeds.

**Seed table.** In the formulas, ℓ is the library number written as one digit.

| Role | Primary process seeds | Paired observation seeds / config ID | Reserve (process only) |
|---|---|---|---|
| Target panel | `86001–86020` | `98001–98020`, `v13-g43-target`, paired in order | `86101–86110` (10) |
| Library ℓ, batch 1 | `87ℓ01–87ℓ03` | `99ℓ01–99ℓ03`, `v13-g43-fit` | `87ℓ51–87ℓ56` (6), one pool per library |
| Library ℓ, batch 2 | `87ℓ04–87ℓ06` | `99ℓ04–99ℓ06`, `v13-g43-fit` | as above |
| Library ℓ, batch 3 | `87ℓ07–87ℓ09` | `99ℓ07–99ℓ09`, `v13-g43-fit` | as above |
| Library ℓ, batch 4 | `87ℓ10–87ℓ12` | `99ℓ10–99ℓ12`, `v13-g43-fit` | as above |

Written out for the six libraries:

| Library | Candidate process seeds | Candidate observation seeds | Reserves |
|---:|---|---|---|
| 1 | `87101–87112` | `99101–99112` | `87151–87156` |
| 2 | `87201–87212` | `99201–99212` | `87251–87256` |
| 3 | `87301–87312` | `99301–99312` | `87351–87356` |
| 4 | `87401–87412` | `99401–99412` | `87451–87456` |
| 5 | `87501–87512` | `99501–99512` | `87551–87556` |
| 6 | `87601–87612` | `99601–99612` | `87651–87656` |

The campaign ID is `v13-g43` and the optimizer seed is `null`. Observation seeds are paired with process seeds in ascending order within each role.

**Reserve sizes.** Ten target reserves and six per library, the sizes the owner accepted for the G41 draft (contingent ruling 8). They are a declared margin, not an estimate of the build failure rate, which is unknown; one failure in 38 builds in G35-B is not a rate. Each library has its own pool, so a replacement never moves a seed between libraries or between the panel and a library. Exhaustion of any pool returns the draft to the owner; a pool is never widened or shared.

**Pre-freeze build pre-check and replacement rule** (deterministic and outcome-blind; G35-B §8 and ruling condition 2). It is applied once, by the director, **after the owner-ruling commit exists on `main`** (DIRECTOR lesson 2026-10-22), on a code tree identical to `0c9c3711b4e1be3fa90e9ef7f1e8e883dbdb48d8` for `src configs tests scripts`, and before any epidemic simulation of any study seed:
- The host's free disk is checked (`df /mnt/c`, ≥ 5 GB) and logged first.
- Every process seed in the §19 flat list, primaries and reserves, is built with `build_parent` at mode `ci`. **Builds only:** no latent run, no observation, no loss, no truth diagnostic. The G35-B pre-check script (`docs/runs/2026-10-22-g35b-seed-precheck.py.txt`) is the template; the G43 script, log and record are filed under `docs/runs/` with run-unique names, the script as `*.py.txt`.
- The record lists, per process seed: build outcome; exception class if any; presence of `private_assignment_residual_fallback` and `destination_reassignment_fallback`; and M2/M3/M4 logical hashes.
- Record all build exceptions, including those on unused reserves.
- A primary whose build raises any exception is excluded. Within each pool, visit failed primary positions in ascending order. For each, consume the lowest-numbered successful reserve that has not already been used in that pool. The replacement inherits the position, paired observation seed and batch membership. Exhaustion stops the freeze and returns the draft to the owner.
- Known failure classes include the adult-supply and household-capacity residual classes, which have no owner rule (G36).
- A build that succeeds through a reviewed fallback (M2 `private_assignment_residual_fallback` or M3 `destination_reassignment_fallback`) is **not** a failure. It is kept, and its fallback diagnostics are recorded as lineage and disclosed (D6).
- An exhausted pool returns the draft as NEEDS OWNER INPUT.
- The frozen text lists final seeds, excluded seeds with their error class and replacement, and each final seed's M2/M3/M4 logical hashes. The campaign verifies that its builds reproduce them exactly (predicate 9), from an independent module constant.
- After freezing there is no replacement of any kind. A build failure at execution fails predicate 1.

**Frozen pre-check outcome** (filled mechanically at freeze):
- Pre-check commit and tree attestation: ruling commit `f2062d524c53a52d16837c2c7fe2ca8be6715510`; `git diff --stat 0c9c3711b4e1be3fa90e9ef7f1e8e883dbdb48d8 f2062d524c53a52d16837c2c7fe2ca8be6715510 -- src configs tests scripts` = empty
- Host disk at pre-check: `C:\  466G  452G  14G  98% /mnt/c`
- Outcome: 135 BUILT / 3 FAILED of 138; replacement triggered: yes (87301 → 87351 and 87305 → 87352 in library 3; 87506 → 87551 in library 5; all `DataBuildError`, adult-supply class). No reserve build failed.
- Record: `docs/runs/2026-11-20-g43-seed-precheck.json`, committed-bytes SHA-256 `015c8b6b0d24da99fffd4b0908979199aef756757acaf1612de1e3305cf5a379`; replacements `docs/runs/2026-11-20-g43-seed-replacements.json`, SHA-256 `6c9b2ae2013be31296297b1e697723766844868856295e4a4e809b03fc18bc9a`; script `docs/runs/2026-11-20-g43-seed-precheck.py.txt`, SHA-256 `3ebdcbb45d07f532db220dd4a15fe63d33c5ee0b2795f2f0c49b672a3b8b8f8d`; log `docs/runs/2026-11-20-g43-seed-precheck.log`, SHA-256 `846ef1818b39ee03c562d56453127260ae48a50d21935bac9f00b240833de739`; all filed at commit `f4054f6590524bc5bd06d04622df8afabc16b8dc`. Two earlier launcher attempts aborted on director script errors before any complete run (r1: no build; r2: built 86001 only); their logs are `docs/runs/2026-11-20-g43-seed-precheck-abortedr1.log` and `docs/runs/2026-11-20-g43-seed-precheck-abortedr2.log`.
- Final seed table, unused reserves and exclusions: below; all reserves are retired after the freeze, used or not.

### Exclusions and replacements

| Pool | Position | Excluded primary | Error class | Replacement |
|---|---:|---:|---|---:|
| library3 | 1 | 87301 | DataBuildError (adult-supply class, G36) | 87351 |
| library3 | 5 | 87305 | DataBuildError (adult-supply class, G36) | 87352 |
| library5 | 6 | 87506 | DataBuildError (adult-supply class, G36) | 87551 |

### Final seed table (92 seeds)

| Role | Library | Batch | Position | Process seed | Observation seed | Build | Fallback disclosure | M2 logical hash | M3 logical hash | M4 logical hash |
|---|---:|---:|---:|---:|---:|---|---|---|---|---|
| target | – | – | 1 | 86001 | 98001 | BUILT | none | `0a7dc3365035d2e324b892b922fe20604b11a52f3027bccfb316c762ffe26a0c` | `294633beb097dc0f560a90dc7bdc8f38d6837bb04f17049602e254ec4bd87d13` | `5262b2482b0bc5ad61642f41fd975e960f3020b156aec08b1f52f8f1444434b0` |
| target | – | – | 2 | 86002 | 98002 | BUILT | none | `1ec684e539b8a750641d32a71a0dfb25378ad327c8765c7a95cf85f895c7ce63` | `886c90a7b4742a141bef3ce1e0ba6875f3ad577cc88492e02177c73354a1add1` | `94bb992adb294264cd84aa37326f93247ace569d2650af3d168164f42b3cf6b7` |
| target | – | – | 3 | 86003 | 98003 | BUILT | none | `3686fe82c9b688b07e666d223706f0cb0f7057f61167eccd63eb1e3a68de0365` | `332ce1beb3e3e7aedfdc59208635e5e1e76fe554383cb7b89b9d44710f842c3b` | `89a082081bbb68afb2c96ea4283a12c070172d817ec319a3f1cf20f0c70d73c9` |
| target | – | – | 4 | 86004 | 98004 | BUILT | none | `f3aa63e4b45d353cb61412b17ebe9d34b16f029d78c88e6d0b7818511a485077` | `fcf5a6a30441916047016508237848e9902da84f97a887e4214ad6ed3e348f58` | `4e7ce6413e57dfb1e8ce3e8a3f76437f0c68198627a491ba49c6c43dc3897a50` |
| target | – | – | 5 | 86005 | 98005 | BUILT | none | `73f00e38d23ccb93bf077c6f3fb4b2bc20443ce1ba3a81c9645ea929ee85863f` | `2553566b1f2effe336e62e47a190c66e05b5dbb872ced7c0c1beab3c95ff26c4` | `d14328f597a0d1fcba26c86d1b9449ae1aad5c12d0a952047d91a0b09ad6bbc3` |
| target | – | – | 6 | 86006 | 98006 | BUILT | none | `6f6d51256df9a9c27882548f1485f6f3af1a9547b46bd283a81ab42632b9dd41` | `bca2132e7e6705c39de75e26f92f0669d8923dfe5cc978e76becd72640961def` | `978d950df49bf3595aa18464dd57a8a9cc70c3c7e8ed0e821e9671da132fac70` |
| target | – | – | 7 | 86007 | 98007 | BUILT | none | `a94598afc760d317c67306fd54adeaa7c14fa33bca764fb5ef6cb148f07b3a2c` | `556766e20db1e54621d8dfd814526a5ad5dbb46e2af792c06f46548f0654c607` | `b691be14a645cfac04e8ac511657159eab8f4c47850af896d1b78eca3f42f0f0` |
| target | – | – | 8 | 86008 | 98008 | BUILT | none | `0b9fdf0fd43cf7ae5853065281f1e401fb9ee3f4e682b8e7752aedd6dca69b7e` | `9649446857a0821388d914e5f0d36159a024ad6a47f698a1e3cac8e0c8dc9bb6` | `6df6ee32634d298aa3ca429b8de3c4a4b7b9977d5d5ca1b724691f603e051923` |
| target | – | – | 9 | 86009 | 98009 | BUILT | none | `a8d20a000b77b25f6234c7b971d0bc7ff3b81342e24daba000a1ff00ed12b055` | `46035c14dd7d01527c050e0fb9505365d9d23b3dea5b44f93b01098adfddbda9` | `05257871a4e6ba243ec750ef5face1b865a74cb0903e89a1c4b1b8938a0c1d29` |
| target | – | – | 10 | 86010 | 98010 | BUILT | none | `7f6c97279ce3014cd5f8bf5ddb3a1b7e352b5a0e03852b578d4d1bee7187bad6` | `e4f428942e7e67c5145205604c00f566a7f1a11bae9feab588e54ac71a945c87` | `653e356207254f7ce09cb254f0550a35591bc29e31a98b233a10d37a5145d5be` |
| target | – | – | 11 | 86011 | 98011 | BUILT | none | `cfdf285d8b6fe7d0664699cbff2e75452948a8e87f5e3436d9cdcca4570dc38c` | `5732d403c79b7bf476bd7122295567e18fef58396fbaafa2311c89c271c75e8a` | `d8afe969911127e494c140e00cf100333b81f3f566b1b2336e5ae650fb28b19e` |
| target | – | – | 12 | 86012 | 98012 | BUILT | private_assignment_residual_fallback | `32790229b5ebc81943a837411a66b79cd7882e6d9e0fbcd037d4f06e3227b1b5` | `d0d9a64abab095e21887ce609da78e145c15b7ea282927210002a7dcfadd4ba2` | `c28703898dd128b10e4921eb62818d5d3ba2dc6f25aa1abbea7af72763cba74d` |
| target | – | – | 13 | 86013 | 98013 | BUILT | private_assignment_residual_fallback | `0c76e2787e8b633bf3bfc5f083e7869b60a7c6856f9435c1c8cf81f273d8c05a` | `731e6d53eb4353c3cd1b2066befa726345b6b0f1580126dd37d24b6d572d375a` | `571bcfe7fe3bf8f36e0455647344c1a6afb2d99140a5317b309ba21a507a633f` |
| target | – | – | 14 | 86014 | 98014 | BUILT | none | `53a4b3a47cb75481f1635680d0d59aad252feaa5489e1e4ee051093e218bfefd` | `965b30beddeeff8e95abe282ad35a7149bfe49fdc5ca74c28f990a40bdc8628b` | `696a5640082bbd9545296514a2d8b0573c817ee2d8b4ee19dfa2715d76bfecaa` |
| target | – | – | 15 | 86015 | 98015 | BUILT | none | `c57210ca4db449b28c773a8629321ae4a96db7723dc55e7e96b8ac9526505c64` | `de6047fd786150df55b2207c420f12586e43b8cca0e73435c6185e6881288611` | `20b1f05e728154faba10129761f82cd5ac57feda813ec9341eb5561702d34e9f` |
| target | – | – | 16 | 86016 | 98016 | BUILT | private_assignment_residual_fallback | `bcd1cd2b8f80cb741687f8ce2bc559e369a2b6ff2e87d314c89b5cb02d4d8475` | `8b38deff0c7f0ad252b2fec9d6a23b5b38094cebd08388b858e0a835696cac82` | `ec5cdc4de176021a2842f4fb0026c17da9a6fb2f3b276da7ce711f9c6d1f8b18` |
| target | – | – | 17 | 86017 | 98017 | BUILT | private_assignment_residual_fallback | `02c94abe5562b5546189dc5299e4147f57c1c7088c8f878a2de487cc46b00b73` | `4aa200eece57e77868e7962c8877f32a117ddf23cd10a78f169b85e0df62b731` | `1e493f554fc690561a028ef30c39419d52f9bda3aaeb412f476fb964ec64edbc` |
| target | – | – | 18 | 86018 | 98018 | BUILT | none | `9d23f5a571752c13d87332e149d209cdb852f157317ceefcc6ac35718f752717` | `e0c1817e39dbaea934f459aef37401a2e80a12ae75b2f67c61b752b53463c63a` | `e006df0a5677af3e5d6ecb8f655e95c3ac68a6b3ab89271faac35f586a4c3103` |
| target | – | – | 19 | 86019 | 98019 | BUILT | private_assignment_residual_fallback | `292de90824de49fa43abc70401c338ed8adac163241a3982bb7d12bb88f7ce70` | `ae1d9ce4d6b472ddc02635a29ab17b8b7a0156b077c26b06a17fbca11945826d` | `24c632534b4213af30e21083b1d75f5a50a9c7201e3232ceb5ca0d5ce9ac206b` |
| target | – | – | 20 | 86020 | 98020 | BUILT | none | `725893c910253ea370328adc97066a362bb1acaf3fef055c05dd8b9314f81f58` | `caf673cc293749bc34074896035ce12588e655902de132addcdba66720258b89` | `0de7fd029b259e32afb51c0e650e90ce5c01e6bb4344e744091540bec753b730` |
| candidate | 1 | 1 | 1 | 87101 | 99101 | BUILT | none | `2ee365bb660e402ddda4f9f31e9e15078baaa2d1e4c24a2888af6f96cc42c058` | `f729c8f0da02d9503e2dab2c53b56fe33234fe46c3085b4cd0630dd5189e7d97` | `356c02861ec6b0b693530ce592c61d418d6c0c603dc946a7c05de3d70bcb67d5` |
| candidate | 1 | 1 | 2 | 87102 | 99102 | BUILT | none | `1036be9ef5be7d32aea7352c3afac1e1f953fbf97b9379047c802576c464c031` | `ae914785a4f23e84e736de10894871d55f51303eecfca7f81df79d9e3660ee0a` | `f1c4449b311378c32d23db26cda9ea88a222bc7c7917e5f51583d47a991cb00c` |
| candidate | 1 | 1 | 3 | 87103 | 99103 | BUILT | none | `a0e9364cd1818389de9e546426604922d84c8d730695df048d57918f7b24c11a` | `b691b8d9595aeb8d485b36132dc43e68a7656dea5b10eb662c3ce422a3d9b6f6` | `af9b7dbc6dd2552f4e8e4b1418c2c4fcda8e175c7190846bbae3bf6244cba6d7` |
| candidate | 1 | 2 | 4 | 87104 | 99104 | BUILT | none | `3d6a04542c4be9be1d4f16e88842d548f6bf0375716523eb201094376981abaf` | `83f03337d8f538d0349c75a72f702d5f8d2930729d582265c50d695fec92fadc` | `156bfa41d7e7cdae66d3fd8deb2c13488547aed42bdffa62c2dbb96fb1bc9962` |
| candidate | 1 | 2 | 5 | 87105 | 99105 | BUILT | private_assignment_residual_fallback | `9f238acdec890605507fac9f0cd2e9061871f8549c5cdb861656cd0e83b29121` | `061151b4297d082afc44728372edcfb77d64d6ec75767ecf2af30d728b34983d` | `6d493cbd7f874210a8b8da26ef64164a9b90c7be86c1adf07be61ddf8635864c` |
| candidate | 1 | 2 | 6 | 87106 | 99106 | BUILT | none | `ba09120d5eedfab99fc89ae674c410119ef3d3277a7ba9f4f1be207c4a27cf4e` | `70f09d6a98c8565e88c2f62a14af26b8bd5aad4a158d14fe0e07894d53e70cdb` | `8209c29bc505617972fc61d08ba1898725544c1bccda2778e3f04b2b3c3ca5d4` |
| candidate | 1 | 3 | 7 | 87107 | 99107 | BUILT | none | `edea9811815b16d4d87821a254825cb5d27b5673fabd1e89f214c102de19c309` | `09c8c273326c11307000febc1d7512302134d170bffbb8fea54c500949db0611` | `31d5de85368d5eae81770070c981826eb9dfa0dbf1653af3fe91532379510734` |
| candidate | 1 | 3 | 8 | 87108 | 99108 | BUILT | none | `8e59571d828e4569dd8118d5a31493ea8f1c09b1c220833ef006afb50c2e88e9` | `77075b3a93ebba248d0002d4e3ea8e9a8d493dc2fcf2cd4bd78d962d7ee49fa1` | `9ecfd6299332a92962e7ca4be824e64a7436b2119a1d684f41f9e4cb3aa55898` |
| candidate | 1 | 3 | 9 | 87109 | 99109 | BUILT | none | `66ae76bc28037edfc31b75c000e47540870072e2e27b3ef8f9f21ca22c364ee2` | `6724a2961a2e7c3639e7b8a4d9b263a4be7678038dc4e16342dd74430b48a544` | `2fad47a308e102845502ccacfd5f6160ed5b3a4df2a2a7cb4d986d816126438b` |
| candidate | 1 | 4 | 10 | 87110 | 99110 | BUILT | none | `0d9063b210c7ca0da213ea3b44c4414acfe4404a0e9b3538d3a65f91bee5753f` | `72de8fd07ec9683810a9e66b3459973351d276ba94483516eabd677c00168571` | `40a6e326c3b005595cb9e22074c9859118ee3acc625bde66c04e4803a26ead6d` |
| candidate | 1 | 4 | 11 | 87111 | 99111 | BUILT | none | `a2d7ee65823b998328f82b4962a60b52ed65ea870808f1dc9bc0720a9cab2515` | `85af40640345c34a27721692437eb82357802454fe4e1e613e4a2e45d3aa146b` | `971dc45a4afdc88b2b1f6315b151cce306ef232864aa280107b61b99d7546c12` |
| candidate | 1 | 4 | 12 | 87112 | 99112 | BUILT | none | `41c49e6fa48b36e69690250502044ae9ccfa70e65fdbaebf70c9978743fe87ad` | `aeb55f476a92f43eadb4648a48289361cf2a27a4b203ce6d6c5b5331431a6e3d` | `8f4bd4b07635e81a1a6460ededba7e2c477978531d7db037be876bd24cd44d87` |
| candidate | 2 | 1 | 1 | 87201 | 99201 | BUILT | none | `cd208843b8bfcd288a0dc76c049c9b4ea9f69fc7787338e3e39a0daef655621a` | `f48805e4bc24fdb088336d7148f1a6979c507adc78d76303de9d24c590d580a5` | `bbaae1a3a913af707afdacfa0e4fd07cd6757eea0d3e065a4cbbdf94c0134939` |
| candidate | 2 | 1 | 2 | 87202 | 99202 | BUILT | none | `6d4c3d4de0bfc0c8cda59cfc7814329f7d92569dfbf3a445b0a71cf8420e22a3` | `1448a4088cdf3e7aabb3d476c3ddcfdff505d1753b8fb940a48225074a2de5f4` | `0c1820856d9240a5b641e2a3ff3a30344d8fa34fe9ceb36556270f9a53752a0a` |
| candidate | 2 | 1 | 3 | 87203 | 99203 | BUILT | none | `d66b26b9f64d3a8619b78c9679dea88f088b71678f41f16f672bf9a100823c1d` | `5623edc23942ee07aaa92fb823bfdb7570e8afed3e73d440bbd5fb505a47c9a8` | `e49bcfdd080a8300a54fb678a7d25a72acd23ac06fc3f26cb4997bee07734a65` |
| candidate | 2 | 2 | 4 | 87204 | 99204 | BUILT | none | `98abbbd83d3fa9705b257e9ffebccaf72f31304538aa67cae722e5496609b925` | `4bba9df99a813bd3bbf0b76a7738fe04c8e14f2f82a66ec0787c584115fd7929` | `6eab8f617063ef5d17f5575f23c4d50976e39ff6a6aa71648f72091b61e57bf5` |
| candidate | 2 | 2 | 5 | 87205 | 99205 | BUILT | none | `05c3b60e1535e2d421c302cf5f34e5fbd54fb5edbd4eedd18b6f32d7df72932e` | `8c33e5d16391713acae567ac3bc6eedc97e3d67c4787ca8e6c3dcd551484d2c6` | `ff71e292024195fe798bad2b4dc17c8a7808d99172f3729fd7e0139c0ef2b624` |
| candidate | 2 | 2 | 6 | 87206 | 99206 | BUILT | private_assignment_residual_fallback | `644f20e5961f5266f74434e928b87f83796f20e63369d3f384cab76a05dad3c6` | `d71c123dd07e0ff703437c2f8f8ffc3eb50876c393e4529dd57b5b8a7d98a100` | `52dbfa3c5da7969eb8952ed114162d4429969cd50596bdfe6b04d36451d46d3d` |
| candidate | 2 | 3 | 7 | 87207 | 99207 | BUILT | none | `deb9739560dff5508febda39096675b906c11511f282a3e9b6867f397a05efaa` | `f298006b6168e5190edec4ee8258cadcd9d5c52d6686599f43f99a955dc5b1a6` | `bf4014b92767fde0e4492f62b2c3e814a1211a44499716ca00af822098153c3c` |
| candidate | 2 | 3 | 8 | 87208 | 99208 | BUILT | none | `1ba965abca9aa7da1e3aa78535193d3b0a428f0e9ad6919160fa728391c077fe` | `ad543cf7d655799b187fe505426c6f189ebf7b23fd3ef91963b887314375827f` | `b5f4007157e9ca10b51414a377b0bc6ab0b9ffcf403f64e74b41b1a9b3fae961` |
| candidate | 2 | 3 | 9 | 87209 | 99209 | BUILT | none | `0f0e1b47d94109ec25b2b87386e1884cdc801aa18667d11d91288e9562df6ea0` | `bcfcc7dacd163e4e5a26855f74214fc56fb34554e698ecf678d3b33be3295873` | `b0209ab0f51f9f0ecfcb20dd3fe220cadd07bdf25f2c90f95087618e935ef282` |
| candidate | 2 | 4 | 10 | 87210 | 99210 | BUILT | none | `e7c445b781f39b76f9424cd63fbd061126509469917f25e7e95a0cc475fa99a4` | `d884df85af6808f08cb9627c756142b3db6f5ea0ba007459e3b5770f84c8db03` | `ccdb67b9ddabb8431108321fa6d5778eced75000ccb3ea052aa6470ae7170539` |
| candidate | 2 | 4 | 11 | 87211 | 99211 | BUILT | none | `f69f5e5020fb1e67aa74471dd41c4899d6bd331c935fbafd7e085835d4c3e585` | `b1f7326e9bd349c8214c8a112154d9aa75e1c8a462d737f37bf0e619f2e9d6f9` | `8739de9dd2b9f31075f5b56bfdff306608cc19492dee7142cb9ea717ea9b8994` |
| candidate | 2 | 4 | 12 | 87212 | 99212 | BUILT | none | `1e2861cdeaf55f569106bdc201a84d5585628a31364ea263acdac57fbb186b84` | `f18eccf271d89b02730c6d97dfd8dcdc9e4fa5659d13dfb51398bf5672f118ac` | `51b21bcc3510495379c17bfe8c4b52771504e90ae28153bd4a430d2894ddef68` |
| candidate | 3 | 1 | 1 | 87351 (replacement) | 99301 | BUILT | destination_reassignment_fallback | `eb18e4ad5d6b402a4407a7909309bd709ed47621753ec0b911fc60160a22ceb2` | `bd4b49eaf9f5b9c2cf600d1e78f30522319743d9c16d7889f688ee311c082e92` | `e95a5d6ebe57157af245ba302a52d98665b28df7c116bd298bcf56f7b85d0279` |
| candidate | 3 | 1 | 2 | 87302 | 99302 | BUILT | destination_reassignment_fallback | `496f86edc8e5b2f3ec6b31fef05b2d0427915a02d145d3c5e143fa7f38cb9484` | `7e4bc36740e422896be060308e313f07c91ba120f1cf63088116ee1b96a32b89` | `2183d19d597abc907b2285b52ddcb436a4fb9cd4acf6848d311ce1d769ac378c` |
| candidate | 3 | 1 | 3 | 87303 | 99303 | BUILT | none | `c693bbfec2536bbeeac6fa0f60e78eb2e4c44277f07f4d1751bfbb4d451702fc` | `753c4a563ffff502ddc6d352df28f6b1510a67b7f53c295d92fc4593abd53247` | `5ffab2ccaaccb4c571856163d5002f914fb14173f24fb2e4eba7dac6fa587c41` |
| candidate | 3 | 2 | 4 | 87304 | 99304 | BUILT | none | `f57ca21237d33ae25c8317840f4fdbf7bd0d940e360c6993a9ab9a8937b9fe53` | `662a82f3fdd6373169b4c73abe6709123860eb1800f6e18ac3a40d8b4b9c25af` | `bdbd14cd895eda7960bd54b4539bc5221090452b146ad7f71542a8fc15f39974` |
| candidate | 3 | 2 | 5 | 87352 (replacement) | 99305 | BUILT | none | `a70616a16ac219147ab34e238f1653ce81f53129fa206d355043a87f06e34c48` | `d066cdaf3c0845a9107dc31c0a7d0d19cd876a3c3b00e0af075ab32720a59a87` | `2eaa28d5d28c26de233d6cbf929a875319b09b76a1cca3c7d44a2a44227ca293` |
| candidate | 3 | 2 | 6 | 87306 | 99306 | BUILT | destination_reassignment_fallback | `7ad0915018f5e0185ccc3fa68fe460877fea1509a5766b4547b417c3eb1cc31b` | `344e5470e9a4deeaa9a911fbea05313545dde1656c7650f06512a1f45262fc54` | `f459a5860f12af5d9582d500ce0639f6de63c947cd6fffb577877ed106e8169f` |
| candidate | 3 | 3 | 7 | 87307 | 99307 | BUILT | private_assignment_residual_fallback | `04b4f3504647c8cae09006d8b2bee523be9bdea99a1e497c17f35bf857b28d6f` | `f977544909b1b73f8574d4bc556f22bb48668c1c84e4216eaf29e2f7da2c62f3` | `3f62ff10773fb7aea0446ce122fd406ea25db6c49ff30c84ba1b229ab2fc8dd2` |
| candidate | 3 | 3 | 8 | 87308 | 99308 | BUILT | none | `be59fd398c164883f432a2279d10c1244dbc8d5650f3dc6d4ca9b7a785041bab` | `73622e6de80f4d2752872758b2d9720e0d2bcb3b22d7226d7b5950ecfe780d57` | `2cc29eb6995ee31aab6d1876a4ef6dc30234d4eb217c643a64228fb413ec7f06` |
| candidate | 3 | 3 | 9 | 87309 | 99309 | BUILT | none | `8b3e5c9dcd7387c0bc5c5f335e10cb9ce76464f5326a78e355d9784028c5287a` | `1a0e7968a09f0e3de51eabee4f9add411c714b9e1605a7b393e057b6423d6f03` | `b3ef5bb7ae59b2ff1a6199fef2bc2ce1e28c8e4c31df549782d06c3b41070cbc` |
| candidate | 3 | 4 | 10 | 87310 | 99310 | BUILT | none | `ec96b1074279a823a7fcb49263305c6cbb0f8b7f554806cd6412c6c98c2b84fc` | `eb065021469d7b1a4958edcf59ad6adb98261e95bfed3f0f690ded910ced91f5` | `d85b9fca078fc236bfbefcb24a58570e9b3acd682a31277d20efe775a32ee380` |
| candidate | 3 | 4 | 11 | 87311 | 99311 | BUILT | none | `e56094a2ef1929b9e9dcc7c4cc6e3fae13c37b1fbccdb0c6d681b408856bafc1` | `56ca6d1615d87bd6870dfc26dc7358c67a5cb2a93a532a28d69d74dc253cbaec` | `6f79c2664f0219060762eb2501f8349cdf1a1a849059f5e61f70322ba33565be` |
| candidate | 3 | 4 | 12 | 87312 | 99312 | BUILT | none | `1ebc64f7ef97f269dcd755a6f6a0aa9644b3a7c88e1433e439b730e36fb8c62e` | `b1c871410885ea4c0ffa95045a0bbdb5d5f5715b523c4125ab9926ab4dc111e8` | `348c275b56fc1908d35549233b7d34760e2b3f0042643c9283d1b113349ec09f` |
| candidate | 4 | 1 | 1 | 87401 | 99401 | BUILT | none | `4ddf498b2e2b90811c3a6af188cfa0df5f14a401a8783a80a5fde7269041192c` | `04b50b618c75c0cdcec701afe009c2649a831dab7b152eef5471a52c5a6db6be` | `b478f6eadb430038114d947ee920a2b6167e859ac99b497c57ba1f06984db790` |
| candidate | 4 | 1 | 2 | 87402 | 99402 | BUILT | none | `bbd1e5b183f0661dd2ad90776d31859848fdd17fe6ad23e1ad3f897112f9afdb` | `fc54dbb8caa279ffbfd33ed92598cb7693495c1c1404b868f380b44d4e36a7c0` | `39845179943f29427890a2541a2fac4c5c158ba357bce3bc12fb7ad2510080d1` |
| candidate | 4 | 1 | 3 | 87403 | 99403 | BUILT | private_assignment_residual_fallback | `69d2596bf29529ee76b43c7bd74fb7df020871b80d06aa37b3331305b323fd4a` | `6e3074799ce5f35d0d1e165990015db432eee86977b538c552997b3c0f95d4a0` | `26fdbdd1a17a4cbb8de99865b59c8859e157bdaf9008d18e7fb6956ff2b78271` |
| candidate | 4 | 2 | 4 | 87404 | 99404 | BUILT | none | `7b1ced0853b33b2ba1a7f88ce1395f36c90b29685c92b9d30ff8549dbbc96748` | `743fe2dff0fad439c1dabd740101475032351026c6940e678e6ffd029cfa9bb4` | `49101cae25e34bd56ae559ba1c6f36889658ea52bc69509ee67d12ca3ee090e9` |
| candidate | 4 | 2 | 5 | 87405 | 99405 | BUILT | none | `f34261078d42461b7e9b7272172ff468bd5795cb857f6749f6375757271aa157` | `8016d74e2dccb9bf256f9e3170b5a536ce5181681cea9a3e41dcc937ec040d59` | `3a6caa452746ef162fb051159b5368ef376bc5d6629c00ddaae6158c440d6fed` |
| candidate | 4 | 2 | 6 | 87406 | 99406 | BUILT | none | `212a7d66d931cbef7c6c3cd5fcdce5d2bda34d86657a24b04de22ab89273be83` | `493da6b6ceb6167f1b36b62abdf1f6b0c14aacdea266dd8364b9334425631f03` | `247f4556332c38bc62c9f64207626347fad5da538109a09c5558b80d31383a64` |
| candidate | 4 | 3 | 7 | 87407 | 99407 | BUILT | none | `92963bfd94fcf9f7c47986096dd0a8aa96fc31703c768a163446529412fa3abf` | `2cdfed0260fee9dd7bc3e074775f588ba69690e38871648e150e5babca6c36d4` | `882b6bec21959b87d04dabe726773f77e8219a0a825bcd1ee261caafd30c5c9a` |
| candidate | 4 | 3 | 8 | 87408 | 99408 | BUILT | none | `e532e4ebbd1db3e47cb21c874fb713a1188a8d12522d19694996c4467360d49c` | `71d34637e0af6db93c3b8c5dcbd3f5b45625810266995cfceb37683d711a6efe` | `70e1a039205b7fc73869732f215f5272c9fa667118b78f18b6315d260b4352ca` |
| candidate | 4 | 3 | 9 | 87409 | 99409 | BUILT | none | `29e307b20600275d74511468cad5ed986c52b712371dffba7e140cbdc2137624` | `4e50cba4f3cb069d72efa4a15891f788d8f4d532a2c8b2a0d08c645705362a77` | `238aca5f3c83fda4c3fe23e90ff4189084ea209f2680130c47b8474466cdf95f` |
| candidate | 4 | 4 | 10 | 87410 | 99410 | BUILT | none | `f7b4778b75110d1764ac4c968ed84b29adff2339a353f2ff3ef2ca3ff5770175` | `ce33508c7856b0f68cbcc1e6de73991c4389d33175525325c1fcfd44ab2b0efe` | `12c8b01fbe8fdd767bd4cbe57136babff7358f15c04eb8d2f0799e7d3f4a1dc4` |
| candidate | 4 | 4 | 11 | 87411 | 99411 | BUILT | none | `68d2cf3bcc9ce8879f4ae3a0ac9f5d5b67409bf605cfce719b7c44da7cdf053a` | `5b2e9a115cb6bcb1a5ef52904b0637847537778c566c9eae69fcbc913c0f8c39` | `9491866a4cd0f4d28321acb9d502de250a8b72841a668be2d5a36644572df90e` |
| candidate | 4 | 4 | 12 | 87412 | 99412 | BUILT | none | `d7e8512832507ad34318397f0b459491de858dbc4708eb1a54b4bd776ea81570` | `97aa5dd9d370afac5e6b68aa5d91cfcb47b39a23b8e3a3e49f43c7d490cc0659` | `3d3fa00b763edb5d05de9d8155f6c860fe2edbf16e9bd5e4fa0050706656df08` |
| candidate | 5 | 1 | 1 | 87501 | 99501 | BUILT | none | `68d23c5c2e4bd6a7c891b38a704846fc2d29a2688789ee4257de634345fa7852` | `6eb04e94224710d3462ed69272b80241167b94f55f89fd38fad591c0feeb4171` | `6aabce5d79374121293e3b4159104884c86e3cd49f7eeab66a5684fe7b2191d9` |
| candidate | 5 | 1 | 2 | 87502 | 99502 | BUILT | none | `f41bab93841691c3eab7f92b9d9c519f7fb3b86839ae040ce56a1b15015e4f86` | `bba462d883c83008b5e978a227c4f1ec086bd85ffcf823bf9024d0700bd24f3b` | `12cc7c1d17f4c32093d14cec22edcd0e1786a949a6de7871d6e5a8c69c52915e` |
| candidate | 5 | 1 | 3 | 87503 | 99503 | BUILT | none | `774b755bbe65061ebacc57dfe9c014dec0d81ca6b5eedba4a3184404b950ba9f` | `e7cf8a0dfcc8f077658c1958d2a954db5efa96b05bc4f3d285f56b13d57d400e` | `d19375f8f3081d775f8ef01d3e2911a5103121d21bf06fbfe1de27eec9bac88b` |
| candidate | 5 | 2 | 4 | 87504 | 99504 | BUILT | none | `2bde8076ebda6cc0331767b7d9d87215bf855ee2d2a3bf8728f5c883e940497d` | `6aaa8a72ad88e9c6dcbdac314565a26a000a16023bdaa078ecd8d40161ecf4e6` | `191f52c2c8724872042bb3c2c55cef64537ce52cbde21ffafbcc484673cd940d` |
| candidate | 5 | 2 | 5 | 87505 | 99505 | BUILT | none | `d1f4ec7204583b22a5b9dd32139a6ab221bac621b7fa0c872f85eedda92bb841` | `a4ef7d2a1d166f33c3eda54c05558a8c8ae4c3c769d3dc6b58dbe273f29298e1` | `590912b076c0312f8e23b4a1c8070ddfe0e405a57d96ad4314429137afff6c08` |
| candidate | 5 | 2 | 6 | 87551 (replacement) | 99506 | BUILT | none | `e99c60315995dbce02f238194f9b33c12734c700f0bc912327bd0ebaf0d088b5` | `ed06b8c250e063e758410bad4d40c81a2f30abee2089bcf9f5c863c2433d82d6` | `ad1e181abf022aae8bc58330cfe616df1568301cd2d2e5fd21d357271ad249a5` |
| candidate | 5 | 3 | 7 | 87507 | 99507 | BUILT | none | `7f1e7a2b8278a871fb5516aa0bf5781ef63fd12091e8e3045dd20a5e94661049` | `155d2955e584a8d7c0a9f7f122a7f0c85b09eb7fc48f10deba2ec3cfac369880` | `9dbbcaa6dc4a809d5eef5804fd8f0af0f355e3dcc1c88483e6d171f7eb9e024a` |
| candidate | 5 | 3 | 8 | 87508 | 99508 | BUILT | none | `555b971ddb2f9f2ffc225993c13aa56305228d1f1afb475f84060793eccf14c3` | `8444637e190e84cfabc494fa845bf19363685747c0f8527d81b362291869f028` | `faccc483b75a2e862e6dc3b69ccb59ce8aaf61ed5b7475c96e474345d3febaa4` |
| candidate | 5 | 3 | 9 | 87509 | 99509 | BUILT | none | `8d2e194b15770d23093bc2609d389692cdd53b743e14b1cb3eee1329a0448995` | `27de8d4016ade3c6f1ac69dbfff87359318157c4920aa8bc883b6e41346d584d` | `3f6ca2ad3df2f53beed299cdd22256894023e4fa52d065a370e967fc0f47dad1` |
| candidate | 5 | 4 | 10 | 87510 | 99510 | BUILT | none | `1741b212f2487077a9001a7c81410c5feb50db3bdf53b923678c813a557c9365` | `3e9cf16dda8045b886580c6c6e76ed301052e14b35300721e4982947bb06a841` | `26d7cb7d1e5bc6cd0af6d8afb70289f3c8c8dcc82489ee4eea3d541127ba3934` |
| candidate | 5 | 4 | 11 | 87511 | 99511 | BUILT | none | `38742657ffa104189a3f57de9f84781b4234a8c14681bc6f94ac5bd58d489125` | `df76f1a83a61f1cf9c27cfdb35ba8428161e97b99bddf60f325ce9915f171288` | `cc540ce2f58903d7ead9fd31e45cc6dcad5e344006f09c64f87e5696174beeff` |
| candidate | 5 | 4 | 12 | 87512 | 99512 | BUILT | none | `77ad1acc588a111406b28bbd7e61d0bd6115fc6a8226c2357416c530086d4faa` | `312d5027cfdc875470c1543c314a7d2622a5977436e131c8f09cd51f4d77b811` | `e44f09d08c1e1ba6e370a497f4d8bcd64dae22e3f218b8b52980bd01bd9c3b68` |
| candidate | 6 | 1 | 1 | 87601 | 99601 | BUILT | none | `8c21dc545ff4c7fc514037d0db7852aca9be8b349f77e3caac1a23bed3e6e8d8` | `16836d6ba2d757612bfe32b4b1759713cbda11ba335c568d0181a386ced48fcb` | `2b14cbe3760e90b158ecf3065d02b19254f79f63450742062bb5cc2804c667bc` |
| candidate | 6 | 1 | 2 | 87602 | 99602 | BUILT | private_assignment_residual_fallback | `739452970946804dea2afead694ab0cbfbeaa2ff88f14687d4e421fc591ee2be` | `3121d82e14a6a9e30a1f9bc93639da39ca9930918c3754ce7d9cb9a15908f148` | `a4d52778ed18fc1154102fbbc31199939fc047e01996757e15a680f6fbcd471d` |
| candidate | 6 | 1 | 3 | 87603 | 99603 | BUILT | private_assignment_residual_fallback | `c5c15e5ae210bf7c9e677a006d1e6149046bbe643540db597b410dd757a809fa` | `b228a4f976be4d2ee721b772536b94ad9a6499915fee0371f5c08b2406f0c744` | `6a62c293ccc9232f766722ae61e09da6ee3515354e19e94ae3bce910ca116d0f` |
| candidate | 6 | 2 | 4 | 87604 | 99604 | BUILT | none | `0ea999e13a5370e2e41690f0def6cf6d22534ec9abd8da8634447f768ca8c794` | `fb4dec3746f618e8988037db73e429d2515d8dbb78c528d97be455b3c56c8968` | `a48bfe1f4062e5943a7ccaaaa6d5acf161269d49eda554e7ac71939190f83ac0` |
| candidate | 6 | 2 | 5 | 87605 | 99605 | BUILT | private_assignment_residual_fallback | `c06cdda6e75a8cce246f08846485d1a9a1bebc6908ff90fbe0422c1fac9386e8` | `3b8f0a8ef431d0cc2b18174235d57578e0c0c14f139b49f79775aaba3b347cff` | `01fe54cb2aa3f9add9ba05232c2d80f910d3dbd16fea095c7e8c9a5c9f15a7f4` |
| candidate | 6 | 2 | 6 | 87606 | 99606 | BUILT | none | `eda73752afe7cc758b761e247b49f5d11e98ed410d749492692737398396bc4f` | `daaa7d5d24f1d3998cf7a287a23aa089cb07205637c177d4dfaad6d3c59ddb88` | `4cd1c646e1b9dc7aac6919094a9321801a78eb1cd0e69af0cf61bdb5f669afe8` |
| candidate | 6 | 3 | 7 | 87607 | 99607 | BUILT | none | `b841a1133472be97a9d6a385b8d2808487074a56975559f88e63328925173311` | `53a7d56af0a6222e035f5b13368b747ad3770054e22423f11b0311faf2a45311` | `be4f6e16ffb163c4dd3a9cf35fce4abeb4069ba409f8e37c48d314be218d3e1e` |
| candidate | 6 | 3 | 8 | 87608 | 99608 | BUILT | private_assignment_residual_fallback | `504f5f503ba9d9cf4dd0dd4dcff77267fd19e43b60520d41fdb6b488c7ee3249` | `a6b92228b233ab13138a5f07cabb33265c9ff394d19a5a822b440a74ff2c1d10` | `d47e311a794b0d3f64ba0777569f66b36d76e60d4d0969b8602e843fc6ed330d` |
| candidate | 6 | 3 | 9 | 87609 | 99609 | BUILT | destination_reassignment_fallback | `2745084d7b27357d750daeb34acb51d698b9bd8c14ffc8f647f6a168ca1e9efe` | `a3391b401d2eb41c5f17f797a0bddc16d52b99ec95cbd437de0e6f9092291211` | `e4201591e0921c59806641a23016c1e58bb79b687f84e8a9ff34a39483d44d85` |
| candidate | 6 | 4 | 10 | 87610 | 99610 | BUILT | none | `f4db661a35536b1b2d7c9465d18fa484035dd8cfa3db74250abf72ad7874deb0` | `2ff4cb8a78321536ff8d58d1300406d35935f59d3c146007f355b807867fc32d` | `397069b44d32744b75ecec84c8f9106b7c1c722bcfb1186988787a364322c41d` |
| candidate | 6 | 4 | 11 | 87611 | 99611 | BUILT | none | `ff5f82f8703c9a4b5a0c00a4c8de4277724b3e35b456580231561884ced6a87c` | `ff61ef38ed3064735c2fae7acd08fcd3f84addd95f7f250981d8b33852556ebc` | `31cd51d822541343825106c47968e7d0a0ceb209844d98bbd16551d9211e9e91` |
| candidate | 6 | 4 | 12 | 87612 | 99612 | BUILT | none | `0e3403bc511f1c38783d9f0c98c8da9e66031c7fb027bb7f679dec6dc6d0a31d` | `78300321868c26e7d25c03665320300576bb93fcd4ce37939280a598841d1642` | `c18df6d5f33372e8c1242bd02d24aab40fc41c86a357c38a13a50a4de2c8d224` |

### Unused reserves (retired)

| Pool | Unused reserve | Build | Fallback disclosure |
|---|---:|---|---|
| target | 86101 | BUILT | private_assignment_residual_fallback |
| target | 86102 | BUILT | none |
| target | 86103 | BUILT | private_assignment_residual_fallback |
| target | 86104 | BUILT | none |
| target | 86105 | BUILT | none |
| target | 86106 | BUILT | none |
| target | 86107 | BUILT | destination_reassignment_fallback |
| target | 86108 | BUILT | none |
| target | 86109 | BUILT | none |
| target | 86110 | BUILT | none |
| library1 | 87151 | BUILT | none |
| library1 | 87152 | BUILT | none |
| library1 | 87153 | BUILT | none |
| library1 | 87154 | BUILT | none |
| library1 | 87155 | BUILT | none |
| library1 | 87156 | BUILT | none |
| library2 | 87251 | BUILT | none |
| library2 | 87252 | BUILT | none |
| library2 | 87253 | BUILT | none |
| library2 | 87254 | BUILT | none |
| library2 | 87255 | BUILT | none |
| library2 | 87256 | BUILT | none |
| library3 | 87353 | BUILT | none |
| library3 | 87354 | BUILT | private_assignment_residual_fallback |
| library3 | 87355 | BUILT | none |
| library3 | 87356 | BUILT | destination_reassignment_fallback |
| library4 | 87451 | BUILT | private_assignment_residual_fallback |
| library4 | 87452 | BUILT | destination_reassignment_fallback |
| library4 | 87453 | BUILT | destination_reassignment_fallback |
| library4 | 87454 | BUILT | none |
| library4 | 87455 | BUILT | destination_reassignment_fallback |
| library4 | 87456 | BUILT | none |
| library5 | 87552 | BUILT | destination_reassignment_fallback |
| library5 | 87553 | BUILT | none |
| library5 | 87554 | BUILT | private_assignment_residual_fallback |
| library5 | 87555 | BUILT | none |
| library5 | 87556 | BUILT | none |
| library6 | 87651 | BUILT | none |
| library6 | 87652 | BUILT | none |
| library6 | 87653 | BUILT | none |
| library6 | 87654 | BUILT | none |
| library6 | 87655 | BUILT | none |
| library6 | 87656 | BUILT | none |

## 9. Workload and fail-closed caps (brief item j)

Each parent is built once per process seed. Each candidate latent run is reused across the 25 detection pairs. With L = 6 and N = 20:

| Quantity | Shared panel | Per library | Formula | **Total** |
|---|---:|---:|---|---:|
| Builds | 20 | 12 | N + 12L | **92** |
| Latent calls (30 days) | 20 | 12 × 25 = 300 | N + 300L | **1,820** |
| Report transforms | 20 | 12 × 625 = 7,500 | N + 7,500L | **45,020** |
| Candidate cells | — | 625 | 625L | **3,750** |
| Gate loss evaluations | — | 625 × 20 = 12,500 | 625·N·L | **75,000** |
| Gate blind records | — | 20 | N·L | **120** |
| Descriptive loss evaluations (four batches + batches 1∪2) | — | 5 × 12,500 = 62,500 | 5·625·N·L | **375,000** |
| Descriptive blind records | — | 5 × 20 = 100 | 5·N·L | **600** |
| Serosurvey samples | 0 | 0 | — | **0** |

The reference evaluations of §7.8 reuse the descriptive surfaces and add no loss evaluation.

Predicate 10 reads the operational work ledger, including required descriptive scoring and record counts. Descriptive results and disclosure copies never feed P10 (§7.2, owner amendment A9).

**Dry-run must enforce exact equality** to the Total column and to the shared and per-library columns separately:
- builds 92 (20 + 6 × 12); latent calls 1,820 (20 + 6 × 300); transforms 45,020 (20 + 6 × 7,500);
- 625 cells per library;
- gate loss evaluations 75,000 and descriptive loss evaluations 375,000; blind records 120 and 600;
- latent duration exactly 30 and calendar exactly 34 dates;
- mode `ci`; serosurvey samples 0.

It also rejects: seed overlap within the study or with any earlier set (§8); retries, replacement and adaptive work; any predicted or measured breach. Every call is reserved against its cap before dispatch, and an exception consumes its slot.

**Outside the campaign.** The pre-check builds 138 process seeds: 20 targets + 10 target reserves + 72 candidates + 36 candidate reserves. It runs no latent call.

**Wall time (unmeasured for this design; disclosure only, never a cap).** EXPLORATORY planning arithmetic from the G35-B `campaign_summary.json` arm-(i) disclosures (15.1 s for 9 builds, 215.9 s for 225 latent calls, 612.5 s for 5,625 transforms, 3.5 s scoring): about 1.7 s per build, 0.96 s per latent call and 0.11 s per transform. Scaling linearly, which is unreliable, gives roughly two hours, plus scoring and retention I/O that were not measured at this scale. The campaign records per-phase `time.perf_counter()` totals (build, latent, transform, scoring, retention) for the shared panel and for each library, and every latent call's `runtime_seconds`. **All wall-time figures come from one source,** `campaign_summary.json.disclosures`; any per-library disclosure file copies them byte-for-byte or omits them (exit-audit O1).

**Retained size and host disk (unmeasured; estimate).**
- The bundle holds about 45,000 candidate table files, 20 target tables, 720 blind records and the latent-truth files: of the order of 46,000–47,000 files.
- EXPLORATORY estimate: 0.5–1 GB. It is scaled from the G35-B arm-(i) directory and has no precision.
- The disk used by 92 retained or transient parent builds, and the peak memory of holding one library's latent results, are **unknown**. U3 measures both on a non-study seed (§13) and the director adds them to the estimate before asking Steven for the campaign.
- **Host-disk rule (DIRECTOR lesson 2026-09-02).** The bundle is written inside the WSL VHD, which grows on the Windows host drive. Before launch the director checks `df /mnt/c` and logs it. The launcher refuses to start unless host free space is at least 5 GB plus the upper size estimate as updated by U3's measurement. The measured bundle size is disclosed afterwards.

## 10. Bundle (brief item j)

One fresh, immutable bundle in a new, empty destination outside the repo. It must let the exit audit recompute every predicate, every reference evaluation, k, k′, m and the class from raw tables with the Python standard library only.

- **`frozen_inputs/`:** this predeclaration (frozen), the owner ruling, any clarification, the config and the pre-check record, each as committed bytes with its SHA-256; plus source and config hashes for every tracked `.py/.yaml/.json` under `src/jersey_outbreak` and `configs`.
- **`seed_ledger.json`:** every role, library, batch and position, with pairing and replacement status.
- **`targets/`:**
  - the 20 target tables and `target_provenance.json` (returned and requested run and observation configs, `observation_rng`, population lineage);
  - **target latent truth (fixes exit-audit O4).** Per target: the complete `transmission_events` (all rows, all fields); the complete `daily_epidemic`; the latent diagnostics `natural_history` and `states` payloads; the complete `observation_events`; the complete `daily_observed_cases`; the actual `benchmark.n_agents`; and the observation diagnostics keys used by P3;
  - `truth_diagnostics.json`, written after the truth join, with each P2 and P3 condition as its own field per target;
  - `auditor_recompute_notes.json`, naming which P2 and P3 inputs are recomputable from the retained raw rows and which are only internally checkable, each with its code locator. Independently recompute the four existing P3 inputs from the retained evidence. Use `transmission_events` for `natural_history.chronology_passed`, `daily_epidemic` and `benchmark.n_agents` for `states.conserved`, `observation_events` for `no_report_before_infection`, and `daily_observed_cases` summed over `latent_infections` minus the length of `observation_events` for `latent_incidence_conservation`. Use the existing source expressions. U3 records the source locators and tests agreement with the returned flags.
  - Candidate latent truth is not retained, because no predicate uses it.
- **`library_<ℓ>/`, for ℓ = 1…6:**
  - the two-channel table for every (cell, replicate), with its process seed, observation seed, batch, position, `table_sha256`, population lineage (M2/M3/M4 logical hashes and both fallback flags) and `observation_rng`;
  - 20 gate blind records and 100 descriptive blind records with read-back hashes, plus `blind_readback_hashes.json`;
  - `g43_L<ℓ>_recovery.csv`, with every per-target predicate value, the boundary flag computed by its own code path, and `population_fallback_m2` / `population_fallback_m3` (disclosures only);
  - `recovery_evaluation.json`, with the ten predicates, the three groups of §7.2, `nonrecovery_ok`, `recovery_met`, the counts, the biases and the D1 margins;
  - `g43_L<ℓ>_descriptives.json` (D4) and `reference_evaluations.json` (D5), labelled.
- **`g43_matrices.json`:** D2 and D3.
- **`g43_across_library.json`:** the six verdicts, k, k′, m, every m_ℓ, the S1 and S2 trigger values, the class word, the NO-READING cause record if any, and the reading text.
- **`campaign_summary.json`:** the §1 lineage block; a `seats` block naming the implementer, the reviewer and any substitution under §12 with the stopped attempt's token count or `not applicable` (fixes O3); `software_status`; the six `scientific_status` values; the class and reading; the S1/S2 sentences under their own key; the status phrase; measured-versus-planned work; and the disclosures.
- **`SHA256SUMS`** covering every other file, with write bits removed and the bundle re-verified after sealing.

**Verdict lines.** The exit audit writes `G43 LIBRARY <1…6> RECOVERY GATE: PASS|FAIL` six times, then `G43 ACROSS-LIBRARY READING: CONSISTENT-PASS|MIXED|CONSISTENT-FAIL|NO-READING (k = <k> of 6)`, then the §7.4 reading and any §7.8 sentence. The audit's own verdict is `JOS G43 CAMPAIGN EXIT AUDIT: CONFIRMED | DISCREPANCY | VOID`. A VOID exit audit writes the audit verdict and cause, with no library or reading lines.

## 11. Protected contracts

**No change to any of:**
- `outbreak_runner.py`, `respiratory.py`, `observation.py`, `observation_scheduler.py`, `observation_schemas.py`, `population_*`, `parent_build.py`, `starsim_adapter.py`, `calibration*.py`, `hashing.py`, `scientific_hashes.py`;
- any artifact schema or identity/persistence contract;
- the handoff §10.4 list.

**`phase0_campaign.py`, `g35b_design_study.py` and `g35b_constants.py` stay byte-unchanged.** The Phase-0, Phase-0b and G35-B dry-runs must still report 198/59/599/8, 1,334/107/4,007/8 and 2,500/395/9,395/85/22.

**No performance change.** If the campaign cannot run within host memory or disk as measured by U3, that is a stop returned to the director and Steven, never a reason to alter generation, batching semantics or retention.

**Stop condition:** any need to modify a protected module, any of the three files above, or a contract stops the unit. It requires a separate owner-rulable brief.

## 12. Order, seats and VOID/FAIL rules (brief item h)

**Order:**
0. **Owner ruling** on this draft: gpt-6.2-sol @ high (G43). If a provider classifier stops it, the unchanged brief goes to a fresh Claude Opus 5.5 subagent (G43); it is never rephrased or resubmitted to the same provider.
1. **Director pre-freeze actions** (no study simulation):
   - commit the ruling via `fm.sh sync` `[skip ci]`; record its committed-bytes SHA-256 in the trail; attest that `git diff --stat 0c9c3711b4e1be3fa90e9ef7f1e8e883dbdb48d8 HEAD -- src configs tests scripts` is empty;
   - check and log host disk;
   - run the builds-only pre-check of the §19 list on that tree, then the replacement rule;
   - fill the §8 placeholders and the §1 ruling row mechanically, apply the ruling's amendments verbatim, and commit the frozen predeclaration via `fm.sh sync` `[skip ci]`; record its committed-bytes SHA-256 in the trail.

   No pre-freeze action may start before the commit that authorizes it exists on `main`. An exhausted reserve pool returns the draft to the owner. Every SHA-256 written into the frozen text is computed from committed bytes.
2. **Steven authorizes implementation** (a new GATES item, default HOLD).
3. **U1, U2, U3** (§13), each `Class: numerical`, implemented by **gpt-6.2-sol @ high** (subject to the seat table below). The director re-accepts each unit and runs the full CI verify-job mirror to PASS on the integration head; the log is filed under `docs/runs/` before any push or review launch. Unit keeps commit locally or to `review/<run>`; the feature branch is pushed once, after the review PASS is filed on `main`.
4. **Independent implementation review** of the complete implementation against the frozen text, by a model that authored none of it. It is given the frozen predeclaration, the ruling, any clarification and the complete implementation (code, config, tests, dry-run and cap evidence). It runs no study simulation and touches no seed. A defect it names returns the implementation to the executor before step 5.
5. **Steven's SHA-first merge** of the reviewed head (default HOLD).
6. **Steven authorizes the single campaign** (default HOLD). It runs at the merge commit, in a fresh clean clone, into a new empty directory outside the repo, from a detached WSL session (DIRECTOR lesson 2026-09-12). The launcher refuses to start if an exit marker exists or if the host-disk rule of §9 is not met. Every precondition and every push uses explicit `|| die`.
7. **Fresh independent exit audit**, by a model that is neither the implementer nor the step-4 reviewer. It recomputes every predicate, k, k′, m and the class from the raw bundle with the Python standard library only, checks the reading and the S1/S2 sentences against §7.4 and §7.8, confirms that no descriptive feeds a verdict, and returns `JOS G43 CAMPAIGN EXIT AUDIT: CONFIRMED | DISCREPANCY | VOID`. Only after CONFIRMED do the G43 tokens become final.
8. **Trail audit** at the end of each run, on the family other than the director's (DIRECTOR Roles).

**Seats, named in advance (owner amendment A10; G43-specific routing):**

| Seat | Default | Fallbacks in order |
|---|---|---|
| 0 · Owner ruling | `gpt-6.2-sol @ high`, this ruling | Fresh Claude Opus 5.5 @ high |
| 1 · Director | Claude Opus 5.5 in the standing director role | Standing director handoff |
| 3 · Numerical implementation | `gpt-6.2-sol @ high` in separate executor sessions | Claude Opus 5.5 @ high in an isolated worktree |
| 4 · Implementation review | Fresh Claude Opus 5.5 @ high | Fresh `gpt-6.2-astra @ high` |
| 7 · Exit audit | Fresh `gpt-6.2-astra @ high` | Fresh Claude Opus 5.5 @ high, then fresh Claude Fable 5.1 @ high |
| 8 · Trail audit, Claude-directed run | Fresh `gpt-6.2-astra @ high` | Fresh `gpt-6-astra @ high` on operational unavailability only |
| 8 · Trail audit, OpenAI-directed run | Fresh Claude Opus 5.5 @ high | Fresh Claude Fable 5.1 @ high |

**Routing rules.** Apply author ≠ judge to the actual work and skip ineligible substitutes. Steps 4 and 7 exclude Claude Fable 5.2, the ruling model, and every implementation author’s model. Step 7 also excludes the step-4 reviewer’s model. A fresh Opus instance may review or audit when eligible, independently of the director session. Disclose shared model or family with the director, the drafter, or another recorded seat, including the Sol owner and executor pairing and Astra’s prior rival-design consult. Preserve the DIRECTOR rule against rephrasing or resubmitting classifier-stopped content to the same provider. File stops and substitutions with the reason and attempt token count, or `not applicable` when no attempt ran. If no eligible seat remains, hold at that step and return to the owner. An exit audit awaiting an eligible seat leaves the results provisional.

**VOID and FAIL rules (G35-B §12, carried forward):**
- A software exception during the campaign stops all work, seals a partial bundle with `software_status` VOID, and makes the campaign VOID. VOID is recorded once at campaign level (§7.11); there are no library verdict lines, no counts `k`, `k′`, `m` or `m_ℓ`, no class and no reading. There is no retry, replacement or resume.
- A step-4 defect blocks progression until corrected and independently reviewed. An established campaign defect makes the campaign VOID. DISCREPANCY denotes unresolved verification without an established departure. An intact campaign’s tokens become final only on CONFIRMED. No campaign retry or resume is allowed. A corrected rerun after VOID requires Steven’s explicit chat decision and a new owner-ruled text, using the same frozen seeds.
- A scientific FAIL is never reclassified. NO-READING is a reading class, not a status, and leaves the six verdicts as computed.
- No second campaign, no additional library and no additional target without Steven's explicit chat decision.
- Any later inconsistency in the frozen text is a stop resolved only by a filed clarification ruling that changes no grid, threshold, seed, objective, level, predicate or reading class.

## 13. Implementation approach and units (brief item g)

**Approach: a new standalone module that imports the G35-B pure functions unchanged.** Config-only reuse of the G35-B harness is not possible without editing frozen code, because the harness binds G35-B constants:
- `validate_frozen_payload` compares the config to `g35b_constants`, including seeds, the predeclaration digest, caps and process hashes;
- `evaluate_recovery` requires exactly the ten G35-B target seeds and divides bias sums by a literal 10 (`g35b_design_study.py:481–585`);
- `verify_parent` checks builds against `g35b_constants.PROCESS_HASHES`, and `WorkCounter` reads the G35-B caps;
- `arm_i` requires a completed gated B generation;
- readings and status text are G35-B-specific.

**Imported unchanged:** `loss`, `fit_blind`, `_fit_scored_grid`, `_offset_descriptive`, `batch_offset_agreement`, `batch_objective_spread`, the blind-estimate persistence and read-back helpers, `committed_document_bytes`, and the Phase-0 config constructors and table builders. The generation adapter may be reused only if it accepts a G43 counter and config without edits; otherwise it is re-implemented in the new module and tested for equal outputs on fixtures.

**New files:**
- `src/jersey_outbreak/g43_multilibrary.py`
- `src/jersey_outbreak/g43_constants.py`: independent; holds every earlier seed set from §8, this document's committed-bytes digest, the final seeds and the M2/M3/M4 hashes
- `configs/calibration/v13_g43_multilibrary.yaml`: decimal strings, every seed listed
- `tests/test_g43_multilibrary.py`

**Units (each `Class: numerical`; implementer gpt-6.2-sol @ high, subject to the §12 seat table):**
- **U1: declaration, evaluator and reading logic.**
  - Constants, config, strict frozen-payload validation, and a dry-run that reports the §9 counts exactly, shared and per library.
  - The N-target evaluator with integer predicates and the three groups of §7.2. Endpoint regressions at 16/20, 15/20, 12/20, 11/20, 4/20 and 5/20, plus decimal endpoint and cancellation regressions for the twenty-target bias.
  - **Independent source of truth:** run at N = 10 on a fixture derived from the retained G35-B blind records, with the source files' SHA-256 recorded in the fixture, the evaluator reproduces the CONFIRMED exit-audit counts for arm B (FAIL; hits 10/7/9/10, joint 7, boundary 0/3/0/0) and arm i (PASS; 10/8/8/10, joint 6, boundary 0/2/0/0). For the U1 historical fixture, supply the retained truth diagnostics and CONFIRMED completion, provenance and work evidence alongside the blind records when asserting full historical verdicts.
  - The class function of §7.3 as a pure function, with a table-driven test over the complete partition: VOID (campaign exception, established departure, or any false P1, P9 or P10 component, shared or library-side, including one detected without an exception); NO-READING with cause `shared_panel` (P2 false, P3 false, both); and k = 0, 1, 2, 3, 4, 5, 6.
  - Readings, S1/S2 triggers and the status phrase as pure functions. Trigger endpoint tests at 4k′ = m, 4k′ = m + 1, m = 24 and m = 23, at k′ = m = 0 (S1 suppressed), and for class eligibility (S1 and S2 emitted only for CONSISTENT-PASS, MIXED and CONSISTENT-FAIL, S1 before S2; neither for NO-READING or VOID). A test that each forbidden word of §7.3 is absent from every generated reading.
  - The G35-B, Phase-0 and Phase-0b dry-runs unchanged.
- **U2: generation, blind barrier, descriptives and reference evaluations.**
  - The shared-panel generation path and the six-library generation path, implemented and mock-tested with real config constructors and faithful result metadata (DIRECTOR lessons 2026-09-22). Evidence checks reject absent metadata.
  - Byte-sharing of target tables across libraries, verified by hash from an independent re-read.
  - Four batches at identical tuples, the nested 3/6/12 fits, D1–D5, and the reference evaluations reusing the descriptive surfaces.
  - The global barrier: every blind record of every library is persisted and read back before any truth join.
  - Work counters with reserve-before-dispatch and exact-equality checks.
- **U3: retention, bundle and summary.**
  - Target latent-truth retention (including `daily_observed_cases` and `benchmark.n_agents`) and `auditor_recompute_notes.json`; U3 records the source locators of the four P3 inputs and tests agreement of their independent recomputation (§10) with the returned flags.
  - Measured-equals-planned checks, the single-source wall-time disclosure, sealing and `verify_bundle`.
  - A stdlib-only recomputation script for the exit audit's use, tested against the evaluator on a mocked bundle.
  - Real-object smokes only on non-study seeds (for example the CI seed 123), never on a G43 study seed. One smoke measures the disk used by one parent build and the peak memory of one replicate's 25 latent runs, and reports both.
  - No campaign execution.

Every brief quotes the governing frozen sentence verbatim with its line number. Any director elaboration is labelled as a mechanical consequence with its derivation, or as an open owner question; it never enters as a requirement (DIRECTOR lesson 2026-10-22, G37 F3). Every brief requires changed-file and diff-stat reporting, formatting, lint, type checks and focused regressions before the full suite, the full suite once on final bytes, and a stop on any protected-contract conflict. Budget: three implementation runs including correctives, unless Steven extends. No implementation brief authorizes a campaign.

## 14. Acceptance commands (proposed gates; not run in this draft)

```bash
git rev-parse HEAD; git status --porcelain
UV_CACHE_DIR=/tmp/uv-cache uv run python -m jersey_outbreak.g43_multilibrary dry-run \
  --config configs/calibration/v13_g43_multilibrary.yaml \
  --predeclaration docs/research/v1_3/<frozen-g43-predeclaration>.md           # 92/1,820/45,020; 75,000/375,000
UV_CACHE_DIR=/tmp/uv-cache uv run python -m jersey_outbreak.g35b_design_study dry-run \
  --config configs/calibration/v13_g35b_design_study.yaml \
  --predeclaration docs/research/v1_3/2026-10-22-g35b-predeclaration.md         # 2,500/395/9,395/85/22
UV_CACHE_DIR=/tmp/uv-cache uv run python -m jersey_outbreak.phase0_campaign dry-run \
  --config configs/calibration/v13_phase0_synthetic.yaml \
  --predeclaration docs/research/v1_3/2026-09-21-phase0-predeclaration.md       # 198/59/599/8
UV_CACHE_DIR=/tmp/uv-cache uv run python -m jersey_outbreak.phase0_campaign dry-run \
  --config configs/calibration/v13_phase0b_synthetic.yaml \
  --predeclaration docs/research/v1_3/2026-09-25-phase0b-predeclaration.md      # 1,334/107/4,007/8
# then the CI verify-job step list exactly (read .github/workflows/ once: uv lock check, compileall,
# ruff check + format, mypy over the pinned modules, focused pytest on test_g43/test_g35b/test_phase0*,
# full pytest once on final bytes)
git diff --check; git status --porcelain
```

Only after review, merge and Steven's campaign authorization:

```bash
UV_CACHE_DIR=/tmp/uv-cache STARSIM_INSTALL_FONTS=0 MPLCONFIGDIR=/tmp/mpl-cache \
uv run python -m jersey_outbreak.g43_multilibrary execute \
  --config configs/calibration/v13_g43_multilibrary.yaml \
  --predeclaration docs/research/v1_3/<frozen>.md \
  --owner-ruling docs/research/v1_3/<ruling>.md --output-dir <new empty dir>/jos-g43-campaign-<run-token>
```

## 15. Limitations

- **One target panel.** All six libraries share twenty targets. Every reading is conditional on that panel. A hard or easy panel moves all libraries together and can produce unanimity that looks like stability. Generalization over panels needs several independently drawn panels crossed with libraries, which is a separate estimand and a separate decision.
- **Six draws.** k is a count. CONSISTENT-PASS does not exclude a substantial library failure rate (§7.5 table). The pass probability on this panel remains unknown.
- **A gate at its threshold.** With counts near their thresholds, MIXED can arise from few target-by-library flips. D1–D3 show which happened; they cannot change the class.
- **One level, one scenario.** R = 12 only; the same CI-scale scenario, grid and square-root objective, which is not a likelihood. A change of R can also shift the expected finite-library loss ordering across cells, not only its scatter, so "more replicates" and "less noise" are not the same statement.
- **Bundled noise sources.** Each replicate varies population, epidemic and observation draws together.
- **Nested reference.** The R = 3 batches are parts of their parent libraries and share the panel; m of 24 is not an independent control.
- **All-target predicates.** One unviable truth run in twenty forces NO-READING. Its probability is unknown.
- **Fallback-built populations** are kept and disclosed (G36 point-mass caveat).
- **Explicit unknowns:** π; the truth-viability rate; the build failure rate; and wall time, bundle size, parent-build disk use and peak memory for this design.
- **Replicate spreads** are stochastic replicate variation, never confidence intervals. No statement here is a calibration, validation or coverage claim.

## 16. Attestation

- **Checkout.** Windows checkout at HEAD `3e44979a6c87dfdc3d393527c4e3cf15c4070b9b` on `main`. `git diff --stat 0c9c3711b4e1be3fa90e9ef7f1e8e883dbdb48d8 HEAD -- src configs tests scripts` was empty, and the tree was clean before this file was written.
- **Read in full:** the brief; the three G42 consults and the comparison; the frozen G35-B predeclaration; the G35-B owner ruling and clarifications 1 and 2; the G41 owner ruling and the rejected G41 draft; the G35-B exit audit; the G35-B pre-check script and the head of its log; `.claude/DIRECTOR.md`; and the G42 and G43 entries of `.claude/GATES.md`.
- **Code read:** `g35b_design_study.py` lines 377–600, 606–760, 1190–1260, 1481–1576, 2371–2440, 2621–2700 and 2785–2953, with its function index; `g35b_constants.py`; `phase0_campaign.py` `TruthDiagnostics`, `truth_diagnostics_from_events` and `_truth_diagnostics_from_result`; the seed validators in `outbreak_schemas.py` and `observation_schemas.py`; `observation_scheduler.observation_stream_seed`.
- **G35-B bundle (read-only):** the top-level listing and `campaign_summary.json` `disclosures.i` only, for the §9 planning arithmetic. Nothing was written to it.
- **Computed here:** the SHA-256 values marked † in §1, a `git grep` for the §19 seeds, and the binomial arithmetic in §7.5–§7.7 with the Python standard library.
- **Nothing else changed or run.** This file is the only file written. No commit, no simulation, no build, no fit and no test.

## 17. Changes from the G42 consult, and ideas adopted from the other consults

**Kept from the consult:** the estimand; L = 6; N = 20 with thresholds 16/12/4; shared byte-identical targets; per-library reserve pools; the four classes with k = 5 and k = 1 as MIXED; no k-of-L cut; the ungated R = 3 reference with two integer-triggered sentences; no staging; no pooling with G35-B; a new standalone module.

**Changed, with the reason:**

| Consult | This draft | Reason |
|---|---|---|
| NO-READING if every library fails and the only failed predicates are library-independent (P2, P3, P9, P10) | NO-READING if P2 or P3 fails in an intact campaign, with cause `shared_panel`; any false P1, P9 or P10 component makes the campaign VOID (§7.3, owner amendment A3) | The consult's rule had a hole when a shared failure coincided with recovery failures, and it treated P9 and P10 as wholly library-independent although each has a library-side component. The owner ruled the precedence (A3); the rule is a complete partition. |
| Status phrase "G42: k/L library gates PASS (class word)" | Six per-library tokens under "G43:"; the class word never inside the phrase (§7.11) | G35-B amendment A9 and DIRECTOR's rule that status vocabularies never mix: readings do not appear in the status phrase. The gate number is G43. |
| Disclosure sentences compare 4k with m | They compare 4k′ with m (§7.8) | k includes non-recovery predicates and m does not. k′ makes both sides the same computation; in classes 3–5, k′ = k. |
| Pooled R = 72 reference offered as an owner option, leaning to include | Excluded from the campaign (owner amendment A6); definition fixed for later EXPLORATORY use (§7.9) | Steven's B2 text does not include it. It is one draw of a different level, which is the defect G41 was rejected for, and it could be read as a tested level. The retained bundle allows it later as a labelled EXPLORATORY analysis. |
| Two-block target descriptive (predicates 4–8 on the first and last ten targets) | Dropped | It is predeclared target subsetting and yields twelve gate-shaped sub-results, which conflicts with the exclusion list. D2 and D3 carry the same information without gate-shaped outputs. |
| "The G35-B arm-(i) PASS reads as a favourable draw" under CONSISTENT-FAIL | "None of these six libraries reproduced the G35-B recovery result. The campaigns differed in libraries, target draws and panel size. This comparison does not identify which difference mattered." (owner amendment A4) | G35-B used different targets and N = 10, so the stronger wording was an over-reading. |
| L = 6 "puts each direction under 2%" | L = 6 is the smallest L with 2 · 0.5^L ≤ 0.055, the figure accepted in frozen G35-B §7.3 (§7.6) | The 2% had no source. The precedent figure does, and the section says it is a precedent, not a law. |
| Reserve sizes left to the director | Ten target and six per library, written out (§8) | The brief requires that no seed be left implicit; the sizes are those the owner accepted for G41. |

**Adopted from the gpt-6.2-astra and gpt-6.2-sol consults:**
- the target × library matrices of joint hits and selected offsets (D2, D3);
- paired reporting of each library's R = 12 result beside its own four R = 3 batches (m_ℓ);
- the frozen wording for a shared-target failure (§7.4 NO-READING cause sentence) and the rule that the target is never removed and the panel never regenerated;
- "a reduced denominator has no reading" (§7.3; carried by the VOID rule of owner amendment A3);
- shared target work counted once in the work ledger (§7.1 predicate 10, §9);
- the requirement that the exit auditor be told which P2 and P3 fields are recomputable from raw records (§10);
- the remark that R can shift the expected loss ordering and not only its scatter (§15);
- the statement that panel generalization is a separate estimand (§15).

**Not adopted:** L = 22 and the 0.80 / 5% / one-exception reading rule (§7.5).

**Earlier amendments and where they are carried:**

| Source | Carried at |
|---|---|
| G35-B A1 (a synthetic result licenses nothing; reopening needs Steven and a new predeclaration) | §1 |
| G35-B A2 (no observed scatter in a justification; no false "minimum" claims) | §4, §7.6 |
| G35-B A3–A7 (probe and serosurvey) | no counterpart; no probe and no serosurvey here |
| G35-B A8 (no over-reading of a pass as a replication) | §7.4 CONSISTENT-FAIL and CONSISTENT-PASS wording |
| G35-B A9 (status phrase carries verdicts only) | §7.11 |
| G35-B A10 and clarification 1 item 2 (fallback columns as disclosures) | §7.9 D6, §10 |
| G35-B A11 and ruling conditions 1–6 (ruling → pre-check → freeze; host disk; committed-bytes digests; clarification-only repairs) | §8, §12 |
| G35-B clarification 1 item 1 (committed-bytes SHA-256) | §1, §12 |
| G35-B clarification 2 (who reviews; substitution) | §12 seats, named in advance |
| G41 ruling §4 (N; multi-library rules need Steven and an owner-ruled text) | §1 authority, §7.7 |
| G41 contingent A1 (pre-check count arithmetic) | §9: 138 with its derivation |
| G41 contingent A2 (exploratory re-scoring kept out of the frozen text) | no retained recovery number is used; the EXPLORATORY figures are the design arithmetic of §7.5–§7.7 (owner amendment A1) and the wall-time and size planning estimates in §9 |
| G41 contingent A3 (the one-library sentence) | superseded by six libraries; its analogue is "on this one target panel" in every reading |
| Exit-audit O1–O5 | §9 (O1), §7.4 names things literally (O2), §10 `seats` (O3), §10 latent truth (O4), D1 margins (O5) |

## 18. Owner rulings applied

Ruling `docs/research/v1_3/2026-11-20-g43-owner-ruling.md` (gpt-6.2-sol @ high, `G43 OWNER RULING: ACCEPT WITH AMENDMENTS`). The draft's questions Q1–Q14 are settled as follows.

| Q | Outcome | Applied at |
|---|---|---|
| Q1 Reading rule | CONSISTENT-PASS at six, MIXED at one through five, CONSISTENT-FAIL at zero, under the A3 precedence; no reliability standard; no study-level recovery gate | A1, A3; §7.3, §7.5 |
| Q2 CONSISTENT-PASS wording | One-in-five and three-in-ten examples kept; the table stays in §7.5, not in the reading | §7.4 (unchanged), §7.5 (A1) |
| Q3 L | L = 6 with the two-direction 0.055 precedent as a design anchor; alternatives deleted | A1; §7.6 |
| Q4 N | N = 20 with the §7.7 table; 16 / 12 / ≤ 4 with equality qualifying; one unviable truth run forces NO-READING; the pre-check does not assess viability | A2; §7.1, §7.7 |
| Q5 NO-READING | Only for shared P2 or P3 failure after integrity passes; any false P1, P9 or P10 component makes the campaign VOID; `library_integrity` cause removed | A3; §7.3, §7.4, §12, §13, §17 |
| Q6 R = 3 reference | `k′` against `m` and each `m_ℓ` accepted; nested R = 6 descriptives retained; S1 suppressed at zero–zero; wording kept | A5; §7.8, §13 |
| Q7 Pooled R = 72 | Excluded from the campaign; later use only as EXPLORATORY with the fixed definition | A6; §7.9, §7.10, §9, §17 |
| Q8 Block descriptive | Two-block target descriptive excluded | §7.10 |
| Q9 Status phrase | Six per-library PASS/FAIL tokens for an intact campaign; VOID once at campaign level; classes outside the phrase | A3; §7.11, §12 |
| Q10 Seeds | All listed ranges, ten target reserves and six per library in separate pools accepted; successful fallback builds kept and disclosed | A7; §8 |
| Q11 Seats | Ruling seat table and routing rules adopted; Claude Fable 5.1 last exit-audit substitute; drafter and ruling model excluded from review and exit audit | A10; §12, §13 |
| Q12 Retention | Target latent truth retained, candidate latent truth not; P3 inputs independently recomputable from retained evidence | A8; §10, §13, §15 |
| Q13 P2 attribution | P2 and P3 conditions computed and reported separately; completion under P1, namespace under P9; historical conjunction preserved | A9; §7.2, §9, §13 |
| Q14 Implementation gate | Freeze may proceed; implementation requires Steven's separate authorization, default HOLD | §12 step 2 (unchanged) |

## 19. Full flat seed list for the pre-check (L = 6, N = 20)

**Process (build) seeds; build-check all 138 at mode `ci` on the attested tree:**

Target panel, primaries (20): 86001, 86002, 86003, 86004, 86005, 86006, 86007, 86008, 86009, 86010, 86011, 86012, 86013, 86014, 86015, 86016, 86017, 86018, 86019, 86020

Target panel, reserves (10): 86101, 86102, 86103, 86104, 86105, 86106, 86107, 86108, 86109, 86110

Library 1, primaries (12): 87101, 87102, 87103, 87104, 87105, 87106, 87107, 87108, 87109, 87110, 87111, 87112 · reserves (6): 87151, 87152, 87153, 87154, 87155, 87156

Library 2, primaries (12): 87201, 87202, 87203, 87204, 87205, 87206, 87207, 87208, 87209, 87210, 87211, 87212 · reserves (6): 87251, 87252, 87253, 87254, 87255, 87256

Library 3, primaries (12): 87301, 87302, 87303, 87304, 87305, 87306, 87307, 87308, 87309, 87310, 87311, 87312 · reserves (6): 87351, 87352, 87353, 87354, 87355, 87356

Library 4, primaries (12): 87401, 87402, 87403, 87404, 87405, 87406, 87407, 87408, 87409, 87410, 87411, 87412 · reserves (6): 87451, 87452, 87453, 87454, 87455, 87456

Library 5, primaries (12): 87501, 87502, 87503, 87504, 87505, 87506, 87507, 87508, 87509, 87510, 87511, 87512 · reserves (6): 87551, 87552, 87553, 87554, 87555, 87556

Library 6, primaries (12): 87601, 87602, 87603, 87604, 87605, 87606, 87607, 87608, 87609, 87610, 87611, 87612 · reserves (6): 87651, 87652, 87653, 87654, 87655, 87656

**Non-building seeds (disjointness check only; 92):**

Target observation (20): 98001, 98002, 98003, 98004, 98005, 98006, 98007, 98008, 98009, 98010, 98011, 98012, 98013, 98014, 98015, 98016, 98017, 98018, 98019, 98020

Library 1 observation (12): 99101, 99102, 99103, 99104, 99105, 99106, 99107, 99108, 99109, 99110, 99111, 99112

Library 2 observation (12): 99201, 99202, 99203, 99204, 99205, 99206, 99207, 99208, 99209, 99210, 99211, 99212

Library 3 observation (12): 99301, 99302, 99303, 99304, 99305, 99306, 99307, 99308, 99309, 99310, 99311, 99312

Library 4 observation (12): 99401, 99402, 99403, 99404, 99405, 99406, 99407, 99408, 99409, 99410, 99411, 99412

Library 5 observation (12): 99501, 99502, 99503, 99504, 99505, 99506, 99507, 99508, 99509, 99510, 99511, 99512

Library 6 observation (12): 99601, 99602, 99603, 99604, 99605, 99606, 99607, 99608, 99609, 99610, 99611, 99612
