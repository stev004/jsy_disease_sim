# G43 multi-library synthetic study predeclaration: six independent R = 12 candidate libraries on one shared target panel (DRAFT 2026-11-20)

<!-- DRAFT by the design author and drafter (Claude Fable 5.2, claude-fable-5-2, @ high), foreman run g43-predecl, brief docs/runs/2026-11-20-g43-predecl-draft-brief.md.txt (committed-bytes sha256 c69a7a4ed8e22777149de140bf73c029fcc1afa56052d8b5202e185f5e619ebc, commit 55c03c9). Not ruled, not frozen. Every value marked <PLACEHOLDER: ...> is filled mechanically by the director at freeze, never chosen by hand. -->

## 1. Status and lineage

**Status:** DRAFT for the model-owner ruling. This document is not a Phase 0c, not a V1.3 gate, not a second G35-B campaign and not the rejected G41 confirmatory study. Status phrase until this text is frozen: "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B FAIL, i PASS, ii FAIL, iii FAIL". From the freeze until a campaign completes, the phrase in §7.11 applies. Real-data fitting stays STOPPED (G34 A+B) whatever the outcome.

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
| Owner ruling on this draft | `<PLACEHOLDER: ruling path, commit, committed-bytes sha256, model @ effort, and any substitution under §12>` |

## 2. Question, estimand and scope

**Question.** At R = 12 candidate replicates per grid cell, does the frozen G35-B arm-(i) gate verdict, computed on one fresh shared target panel, depend on which independent candidate library was drawn?

**Estimand.** For the frozen arm-(i) design the gate verdict is a function of two random draws: the candidate library (twelve process/observation pairs in four batches of three) and the target panel. This study holds the panel fixed and shared, and observes the verdict under L = 6 independently drawn libraries. The primary datum is **k**, the number of the six libraries whose frozen gate is PASS on the same N = 20 targets. The supporting data are the per-library predicate vectors and the target × library matrices (§7.9).

**What is not estimated.** The probability π that a fresh library passes on this panel is unknown and stays unknown. k/6 is a count in six draws. It is not a pass rate, not a reliability figure and not an interval, and no bound on π is reported.

**Why the study is worth running where G41 was not.** The owner rejected G41 because one library is one draw of the thing that varies, and because neither outcome would have changed the next decision (ruling §3.1, §3.3). Here every reading class changes it:

| Class (§7.3) | What Steven's next gate has in hand |
|---|---|
| CONSISTENT-PASS | No flip in six draws. Enough to ask whether a reliability study with its own ruled standard, or a second panel, is worth commissioning. Not enough to reopen anything. |
| MIXED | A direct observation that the verdict changes with the library on identical targets. The "more replicates at R = 12" route is answered by measurement in place of an unknown. |
| CONSISTENT-FAIL | No library reproduced recovery. The G35-B arm-(i) pass stands alone as a screening result. |
| NO-READING | Nothing learned about library dependence; the cause is named. |

**EXPECTATION (not a design input).** G35-B arm (i) passed with four counts exactly at their inclusive thresholds. The drafter expects MIXED or CONSISTENT-FAIL to be more likely than CONSISTENT-PASS. No number is attached to that expectation, and nothing in the design depends on it. STOP (G42 option A) remains fully defensible; that is Steven's call and he has chosen B2.

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

### 7.3 Across-library reading classes (brief item b; mechanical)

There is **no study-level gate, no study-level PASS/FAIL token and no k-of-L cut**. The study reports the six verdicts, k, and exactly one class word, selected by the first matching row:

| Order | Condition (all exact, no judgment) | Class |
|---:|---|---|
| 1 | Campaign status is VOID under §12 | **VOID** (campaign status; no class, no reading) |
| 2 | `nonrecovery_ok_ℓ` is false for at least one ℓ | **NO-READING** |
| 3 | k = 6 | **CONSISTENT-PASS** |
| 4 | 1 ≤ k ≤ 5 | **MIXED** |
| 5 | k = 0 | **CONSISTENT-FAIL** |

Here k = the number of ℓ with gate PASS. In rows 3–5 every `nonrecovery_ok_ℓ` is true, so k equals **k′** = the number of ℓ with `recovery_met_ℓ` true. k′ is always computed and reported, in every row.

**Boundary cases, stated so that none is left to judgment:**
- k = 5 is MIXED. k = 1 is MIXED. The words "nearly", "almost", "majority", "most", "typical" and "best library" are forbidden in every reading and summary.
- A library whose every count sits exactly at its inclusive threshold has PASS, exactly as in G35-B. Its margin is reported (§7.9, D1) and cannot change the class.
- **NO-READING, shared-panel cause.** If any shared-panel component is false, all six gates are FAIL by the frozen conjunction, whatever the libraries did. The cause is recorded as `shared_panel`, with the target seeds and the failed conditions. Example: one truth run with no local secondary infection.
- **NO-READING, library-integrity cause.** If every shared-panel component is true and a library-integrity component is false for some library, the cause is recorded as `library_integrity`, with the library and component. That library's FAIL is not a recovery verdict, and a reduced denominator has no reading. The harness is fail-closed, so this is expected to surface as a software exception and VOID first; the row exists so that the partition is complete.
- If both causes are present, both are recorded.
- In NO-READING the six per-library verdicts stand as computed. No FAIL is reclassified, no target is removed, the panel is not regenerated, and no library is rescored.

**Why NO-READING is defined on the non-recovery group and not on "which predicates failed".** A rule of the form "every library failed and only shared predicates failed" has a hole: a shared P2 failure together with a P5 failure in some libraries would be read as CONSISTENT-FAIL although every verdict was forced before recovery was assessed. Row 2 has no such hole. This tightens the common-cause rule in the consult (§17).

### 7.4 Readings (brief items b, i; verbatim, descriptive statements separate from the gate vocabulary)

Angle-bracket fields are filled mechanically from the evaluation. No other word may be added to a reading.

**CONSISTENT-PASS.** "All six independently drawn R = 12 candidate libraries passed the frozen G35-B arm-(i) recovery gate on the same 20 shared synthetic targets. In six draws on this one target panel, the gate verdict was not observed to depend on which library was drawn. This is a count, not a pass rate, not a reliability finding and not an interval: six passes in six draws do not rule out that a substantial fraction of libraries, for example one in five or three in ten, would fail on this panel, and nothing is shown for any other target panel, scenario, grid, objective or level of R. Smallest count margin across the six libraries: <d> target(s); libraries with at least one count exactly at its inclusive threshold: <n> of 6. This authorizes no real-data fitting. It is no more than input to a later gate decided by Steven."

**MIXED.** "<k> of six independently drawn R = 12 candidate libraries passed the frozen G35-B arm-(i) recovery gate and <6 − k> failed it, on byte-identical targets. On this target panel the gate verdict depended on which candidate library was drawn. This is a direct observation, not a statistical inference. Four-dimensional recovery under this gate is therefore not shown to be a property of the level R = 12 on this panel. <k>/6 is a count in six draws, not a pass rate and not an interval. Failing libraries and their failed predicates: <ℓ: predicates with counts>. Smallest count margin among the passing libraries: <d> target(s). The G35-B arm-(i) PASS remains a screening result only."

**CONSISTENT-FAIL.** "None of six independently drawn R = 12 candidate libraries passed the frozen G35-B arm-(i) recovery gate on the same 20 shared synthetic targets, with every shared-panel and integrity predicate satisfied. In six draws on this one target panel, R = 12 did not produce four-dimensional recovery, and no dependence of the verdict on the library was observed. Failed predicates per library: <ℓ: predicates with counts>. The G35-B arm-(i) PASS is not reproduced by any library here; that is consistent with a favourable draw of library, of targets, or both in G35-B, and this study cannot separate those. Zero of six is a count, not a pass rate and not an interval, and it says nothing about other levels of R. The G35-B arm-(i) PASS remains a screening result only and its verdict is not changed."

**NO-READING.** "No reading on library dependence is issued. <Cause sentence.> The six per-library verdicts stand as computed and are not reclassified; no target is removed and the panel is not regenerated. Predicates 4–8 were met by <k′> of six libraries; this is reported descriptively and licenses nothing."
- Cause sentence, `shared_panel`: "All six library gates are FAIL because a predicate that does not involve the candidate library failed on the shared panel (<target seeds: failed conditions>), so this panel could not discriminate among candidate-library draws by gate outcome."
- Cause sentence, `library_integrity`: "The declared work or provenance of library <ℓ> was not as declared (<components>), so its gate verdict is not a recovery verdict and six comparable verdicts do not exist."

**VOID.** No reading. §12 VOID rules apply.

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

This is the point on which the consultants split, so the argument is set out in full.

1. **A cut needs numbers that have no source.** Any rule "at least c of L" with c < L is a claim about the pass probability π. To choose c and L one must first choose a standard π₀ and an error budget α. Neither appears in any frozen document, and neither follows from the structure of the study. The consults that proposed a cut say so themselves: the 0.80 standard, the 5% budget and the one-exception allowance are flagged there as owner judgments, and 0.80 "cannot be learned from G35-B". DIRECTOR's rule is that explicit unknown beats false precision and that parameters are never invented. All / some / none is the only partition of the six verdicts that needs no chosen number.
2. **The cut does not buy a decision.** DESIGN ARITHMETIC under a hypothetical model in which library verdicts are independent Bernoulli(π) given the panel: with 22 libraries and the 21-of-22 rule, the positive reading occurs with probability 0.339 at π = 0.90 and 0.698 at π = 0.95. A study that most likely ends in "can't tell" unless π is very high has the defect G41 was rejected for (ruling §3.3).
3. **At L = 6 a cut would be a weak test presented as a strong one.** Same arithmetic: a 5-of-6 rule would give a positive reading with probability 0.109 at π = 0.5, 0.420 at π = 0.7 and 0.655 at π = 0.8. Unanimity is the conservative end of every possible cut, and it is the only one that is not a choice.
4. **Nothing is hidden by declining a cut.** k, the six predicate vectors and the full target × library matrices are published. A later owner-ruled reliability study remains possible and would be better specified after this one. If the class is MIXED or CONSISTENT-FAIL, the larger study is unnecessary. If it is CONSISTENT-PASS, the reading itself says a reliability study is the next thing to consider. G43 data could never be pooled into such a study, because they will have been seen before it is designed.
5. **The asymmetry is conservative.** The only class that could feed a later gate toward reliance requires every library to pass.

**What CONSISTENT-PASS at L = 6 cannot rule out, stated plainly.** Same hypothetical model; π is unknown and is not estimated:

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
- For comparison with the rival proposals' 5% convention only: six of six would exclude, at that convention, only π ≤ 0.607. No such bound is reported in any reading.
- No affordable L separates π = 0.9 from π = 1.0.
- The table also shows the cost of unanimity: at π = 0.9 the class is MIXED 47% of the time. That is intended. Such a design does depend on the draw, and k/6 is reported.
- All of this is conditional on one target panel. A hard or easy panel pushes all six libraries the same way. No statement about another panel is licensed.

### 7.6 Number of libraries: L = 6 (brief item c; owner's call, range 5–8)

**What L controls.** It is the number of draws of the thing that varies. It is the only lever on the "one draw" defect (G41 ruling §3.1). The reading rule in §7.3 does not depend on L; L only sets how strict unanimity is and what the study costs.

**Structural floor.** Two libraries can show a flip but cannot show a non-unanimous majority; three is the minimum for that.

**Argument for 6 (anchored on a frozen precedent, not on a tuned pass rate).** Frozen G35-B §7.3 chose ten targets because they cut the chance that a coin-flip recovery passes the hits predicate to 0.055, and the owner accepted that argument as grid-independent and result-independent. The analogous error here is a coin-flip library verdict (π = 0.5) producing a unanimous class, because both unanimous classes say "no dependence observed". Its probability is 2 · 0.5^L:

| L | 2 · 0.5^L | P(k = L) at π = 0.7 / 0.8 / 0.9 | Builds 12L + 20 | Latent calls 300L + 20 | Transforms 7,500L + 20 |
|---:|---:|---|---:|---:|---:|
| 4 | 0.1250 | 0.240 / 0.410 / 0.656 | 68 | 1,220 | 30,020 |
| 5 | 0.0625 | 0.168 / 0.328 / 0.591 | 80 | 1,520 | 37,520 |
| **6** | **0.0312** | **0.118 / 0.262 / 0.531** | **92** | **1,820** | **45,020** |
| 7 | 0.0156 | 0.082 / 0.210 / 0.478 | 104 | 2,120 | 52,520 |
| 8 | 0.0078 | 0.058 / 0.168 / 0.430 | 116 | 2,420 | 60,020 |

L = 6 is the smallest L at which 2 · 0.5^L is at or below the 0.055 the project has already accepted for the analogous target-count error (L = 5 gives 0.0625). The 0.055 is a precedent, not a law. If the owner prefers the single-direction form (0.5^L ≤ 0.055), L = 5 follows; if the owner wants unanimity stricter, 7 or 8. Every count in §8–§9 follows mechanically from the formulas given there, and the seed formula in §8 is defined for ℓ ≤ 8.

**Side effect.** L = 6 yields 24 independent R = 3 batches for the reference (§7.8).

### 7.7 Number of targets: N = 20 (brief item c)

**Authority.** G41 ruling §4, which binds successors: a fraction-preserving change of N honours "same pass/fail rules", and "must be disclosed to Steven as a change of N, with the binomial table, whenever it is used". This section is that disclosure.

**What N controls.** It does not add library draws. It sets gate granularity and how much one unusual target can move a verdict.
- At N = 10 every count threshold is one target wide, so a single target-by-library flip can change a verdict, and MIXED could be reached by the coarsest possible flicker. At N = 20 each target carries five percentage points.
- 20 is the smallest multiple of five above ten, so every threshold stays an exact integer. It follows the G35-B doubling precedent (5 → 10, owner decision 3).

**Binomial table (grid-independent; per-target success treated as Bernoulli(p) for one fixed library):**

| Per-target rate p | P(hits ≥ 4N/5): N = 10 → 20 | P(joint ≥ 3N/5): N = 10 → 20 |
|---:|---|---|
| 0.5 | 0.055 → 0.006 | 0.377 → 0.252 |
| 0.6 | 0.167 → 0.051 | 0.633 → 0.596 |
| 0.7 | 0.383 → 0.238 | 0.850 → 0.887 |
| 0.8 | 0.678 → 0.630 | 0.967 → 0.990 |
| 0.9 | 0.930 → 0.957 | 0.998 → 1.000 |

The boundary predicate at per-target boundary rate q mirrors the hits column at p = 1 − q.

**Reading of the table.** Discrimination away from a threshold improves. A design sitting exactly at the threshold passes slightly less often at 20 than at 10 (0.678 → 0.630), so the change cannot be read as making any PASS easier. These are single-predicate figures; the composite gate also depends on correlations among predicates and on the shared library, which are unknown.

**Costs and risks of N = 20.**
- One build, one latent call and one transform per extra target, plus scoring against every library and sub-library.
- The all-target predicates (P2, P3, P4) have twice as many chances to bind. One unviable truth run forces NO-READING (§7.3). The rate of unviable truth runs in this scenario is unknown and is not estimated; no viability check of study targets is run before the campaign, because that would be a look at truth.

**Why not 30.** Nothing structural selects it, and at-threshold behaviour does not sharpen (0.607 at p = 0.8). It remains the owner's option; target seeds are `86001…86000+N` and counts follow from §9.

### 7.8 The R = 3 concurrent reference (brief item e)

**What it is.** Each library contains four batches of three. The 4 × 6 = 24 batches are 24 independent R = 3 candidate libraries, each a Phase-0b-shaped objective, scored against the same twenty targets from tables already generated. In addition, batches 1∪2 of each library give six R = 6 libraries, the frozen nested step.

**How it is read.** For each of the 24 batches and each of the six R = 6 sub-libraries, the predicate 4–8 computation is applied at N = 20 with the §7.1 thresholds. Each record reports per-dimension hit counts, the joint count, per-dimension boundary counts, exact mean biases, the tie count and a boolean `criteria_4_to_8_met`.
- Vocabulary is "met / not met", never PASS/FAIL. These records never enter the status phrase, a verdict line or a class.
- **m** = the number of the 24 batches with `criteria_4_to_8_met`. **m_ℓ** = the number among library ℓ's four batches. Both are reported beside k′, and each m_ℓ is shown beside its parent library's verdict.
- The comparison uses k′ (predicates 4–8), so that the R = 12 and R = 3 sides are the same computation.

**Disclosure sentences, each triggered by an exact integer comparison with no threshold:**
- **S1, if 4·k′ ≤ m:** "On this panel the six R = 12 libraries did not meet predicates 4–8 proportionally more often than their own twenty-four R = 3 batches (R = 12: <k′> of 6; R = 3: <m> of 24)."
- **S2, if m = 24:** "Every R = 3 batch also met predicates 4–8 on this panel; R = 12 is not shown to be necessary here."

If neither condition holds, no sentence is written; k′, m and every m_ℓ are still reported. The count of libraries with `recovery_met_ℓ` false and m_ℓ ≥ 1 is reported as `libraries_not_met_with_a_batch_met`, without a sentence.

**Why it is ungated.**
- The batches are nested in the libraries. Each batch contributes a quarter of its parent's objective, so the 24 are not an independent control arm against the six.
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

**Pooled reference (owner option; recommended default: not computed).** The consult offered a pooled R = 72 reference: all 72 replicates scored as one library. This draft recommends leaving it out of the declared outputs (§17 gives the reason). If the owner includes it, its definition is fixed here: replicate order is library 1…6, position 1…12; `loss(target, predictions, 72, 34)`; predicates 4–8 at N = 20 reported as "met / not met"; label `pooled_reference_not_a_tested_level`; and the fixed sentence "This is one draw of an R = 72 library, not a tested level; it has no reading and cannot separate the level from the draw." It would add 12,500 loss evaluations and 20 blind records to §9 and nothing else. If it is not included, any later use of the retained bundle for this purpose must use this definition and be labelled EXPLORATORY.

### 7.10 Explicit exclusions (no forking paths)

- any k-of-L cut, majority rule, or pooled-rate criterion;
- any study-level PASS/FAIL token;
- re-partitioning the 72 replicates into other libraries or batches;
- library subsetting, target subsetting (including by fallback status, viability or influence), or any "best library" or "best batch";
- pooling hits across libraries into one gate;
- pooling with G35-B data;
- a gated R = 3 or R = 6 arm, or any rule on the difference between k′ and m;
- alternative thresholds, re-weightings, alternative R, T, L or N after the freeze;
- any sequential, staged or early-stopped execution;
- any rerun, extension or additional library without Steven's explicit chat decision and a new owner-ruled text.

### 7.11 Status phrase (brief item i)

The existing phrase is kept intact and extended. Status vocabularies never mix: PASS/FAIL are per-library recovery-gate verdicts, VOID is a campaign status under §12, and the class word and readings are descriptive text that never appears in the phrase.

- Until this text is frozen: "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B FAIL, i PASS, ii FAIL, iii FAIL".
- From the freeze until a campaign completes: "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B FAIL, i PASS, ii FAIL, iii FAIL; G43: not run".
- Afterwards: "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B FAIL, i PASS, ii FAIL, iii FAIL; G43: L1 <PASS|FAIL|VOID>, L2 <PASS|FAIL|VOID>, L3 <PASS|FAIL|VOID>, L4 <PASS|FAIL|VOID>, L5 <PASS|FAIL|VOID>, L6 <PASS|FAIL|VOID>".

There is one campaign, so VOID applies to all six tokens or to none. The G43 tokens are final only after the exit audit returns CONFIRMED; until then state files append "(exit audit pending)" outside the phrase. The class word may be written beside the phrase in prose, never inside it.

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
- A primary whose build raises any exception is excluded. It is replaced by the lowest-numbered reserve of the same pool that built. The replacement takes the failed seed's position, paired observation seed and batch membership.
- Known failure classes include the adult-supply and household-capacity residual classes, which have no owner rule (G36).
- A build that succeeds through a reviewed fallback (M2 `private_assignment_residual_fallback` or M3 `destination_reassignment_fallback`) is **not** a failure. It is kept, and its fallback diagnostics are recorded as lineage and disclosed (D6).
- An exhausted pool returns the draft as NEEDS OWNER INPUT.
- The frozen text lists final seeds, excluded seeds with their error class and replacement, and each final seed's M2/M3/M4 logical hashes. The campaign verifies that its builds reproduce them exactly (predicate 9), from an independent module constant.
- After freezing there is no replacement of any kind. A build failure at execution fails predicate 1.

**Frozen pre-check outcome** (filled mechanically at freeze):
- Pre-check commit and tree attestation: `<PLACEHOLDER: ruling commit SHA; git diff --stat 0c9c3711b4e1be3fa90e9ef7f1e8e883dbdb48d8 <commit> -- src configs tests scripts = empty>`
- Host disk at pre-check: `<PLACEHOLDER: df output line>`
- Outcome: `<PLACEHOLDER: b BUILT / f FAILED of 138>`; replacement triggered: `<PLACEHOLDER: yes/no, with each exclusion → replacement and error class>`
- Record: `<PLACEHOLDER: docs/runs/<date>-g43-seed-precheck.json, committed-bytes sha256>`, script `<PLACEHOLDER: …py.txt, sha256>`, log `<PLACEHOLDER: ….log>`
- Final seed table: `<PLACEHOLDER: per final seed: role, library, batch, position, build, fallback disclosure, M2, M3, M4 logical hashes>`
- Unused reserves: `<PLACEHOLDER: per reserve: build outcome, fallback disclosure>`; all reserves are retired after the freeze, used or not.

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
| Pooled reference, only if the owner includes it | — | — | 625·N evaluations; N records | 12,500; 20 |

The reference evaluations of §7.8 reuse the descriptive surfaces and add no loss evaluation.

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
  - **target latent truth (fixes exit-audit O4).** Per target: the complete `transmission_events` (all rows, all fields); the complete `daily_epidemic`; the latent diagnostics `natural_history` and `states` payloads; the complete `observation_events`; and the observation diagnostics keys used by P3;
  - `truth_diagnostics.json`, written after the truth join, with each P2 and P3 condition as its own field per target;
  - `auditor_recompute_notes.json`, naming which P2 and P3 inputs are recomputable from the retained raw rows and which are only internally checkable, each with its code locator. **Explicit unknown:** this draft did not establish whether `natural_history.chronology_passed` and `states.conserved` can be recomputed from the retained fields alone. U3 must establish it and test the recomputable ones against the harness flags.
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

**Verdict lines.** The exit audit writes `G43 LIBRARY <1…6> RECOVERY GATE: PASS|FAIL` six times, then `G43 ACROSS-LIBRARY READING: CONSISTENT-PASS|MIXED|CONSISTENT-FAIL|NO-READING (k = <k> of 6)`, then the §7.4 reading and any §7.8 sentence. The audit's own verdict is `JOS G43 CAMPAIGN EXIT AUDIT: CONFIRMED | DISCREPANCY | VOID`.

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
3. **U1, U2, U3** (§13), each `Class: numerical`, implemented by **gpt-6.1-sol @ high**. The director re-accepts each unit and runs the full CI verify-job mirror to PASS on the integration head; the log is filed under `docs/runs/` before any push or review launch. Unit keeps commit locally or to `review/<run>`; the feature branch is pushed once, after the review PASS is filed on `main`.
4. **Independent implementation review** of the complete implementation against the frozen text, by a model that authored none of it. It is given the frozen predeclaration, the ruling, any clarification and the complete implementation (code, config, tests, dry-run and cap evidence). It runs no study simulation and touches no seed. A defect it names returns the implementation to the executor before step 5.
5. **Steven's SHA-first merge** of the reviewed head (default HOLD).
6. **Steven authorizes the single campaign** (default HOLD). It runs at the merge commit, in a fresh clean clone, into a new empty directory outside the repo, from a detached WSL session (DIRECTOR lesson 2026-09-12). The launcher refuses to start if an exit marker exists or if the host-disk rule of §9 is not met. Every precondition and every push uses explicit `|| die`.
7. **Fresh independent exit audit**, by a model that is neither the implementer nor the step-4 reviewer. It recomputes every predicate, k, k′, m and the class from the raw bundle with the Python standard library only, checks the reading and the S1/S2 sentences against §7.4 and §7.8, confirms that no descriptive feeds a verdict, and returns `JOS G43 CAMPAIGN EXIT AUDIT: CONFIRMED | DISCREPANCY | VOID`. Only after CONFIRMED do the G43 tokens become final.
8. **Trail audit** at the end of each run, on the family other than the director's (DIRECTOR Roles).

**Seats, named in advance:**

| Seat | Default | Substitutes, in order |
|---|---|---|
| Owner ruling (step 0) | gpt-6.2-sol @ high | fresh Claude Opus 5.5 @ high |
| Implementer (step 3) | gpt-6.1-sol @ high | Claude Opus 5.5 @ high in an isolated worktree |
| Implementation reviewer (step 4) | Claude Opus 5.5 @ high, fresh instance | gpt-6.2-astra @ high |
| Exit auditor (step 7) | gpt-6.2-astra @ high (never `ultra`) | Claude Opus 5.5 @ high, fresh instance; then Claude Fable 5.1 @ high, fresh instance |

**Seat rules:**
- **Author ≠ judge.** The reviewer is never the implementer's model. The exit auditor is never the implementer's model or the reviewer's model. A substitute that would break either rule is skipped.
- **Excluded from steps 4 and 7 in every case:** Claude Fable 5.2 (author and drafter of this design) and the model that issued the owner ruling on this draft.
- **Classifier stop or unavailability.** Never rephrase or resubmit stopped content to the same provider (DIRECTOR lesson 2026-10-22). The unchanged brief goes to the next seat in the row that belongs to the other model family and satisfies the rules above. The stop is logged with its token count and disclosed in the trail, the affected report and `campaign_summary.seats` as "<seat>: <model @ effort>, substituted under G43 §12".
- **Disclosures.** If Claude Opus 5.5 holds a seat, the lineage block states that it is the same model as the run's director. gpt-6.1-sol (implementer) and gpt-6.2-sol (owner) are the same family; that is disclosed.
- **If no eligible seat remains** for a step, that step is not satisfied and the next step does not open. The matter returns to the owner. No campaign is authorized on a review by the implementer's model, a director self-review, or no review. If the exit audit has no seat, the results stay "not final".

**VOID and FAIL rules (G35-B §12, carried forward):**
- A software exception during the campaign stops all work, seals a partial bundle with `software_status` VOID, and makes the campaign VOID. All six tokens read VOID, there is no class and no reading. There is no retry, replacement or resume.
- A defect named by the independent reviewer or the exit auditor makes the campaign VOID. A corrected rerun uses the same frozen seeds, and only with Steven's authorization.
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

**Units (each `Class: numerical`; implementer gpt-6.1-sol @ high):**
- **U1: declaration, evaluator and reading logic.**
  - Constants, config, strict frozen-payload validation, and a dry-run that reports the §9 counts exactly, shared and per library.
  - The N-target evaluator with integer predicates and the three groups of §7.2. Endpoint regressions at 16/20, 15/20, 12/20, 11/20, 4/20 and 5/20, plus decimal endpoint and cancellation regressions for the twenty-target bias.
  - **Independent source of truth:** run at N = 10 on a fixture derived from the retained G35-B blind records, with the source files' SHA-256 recorded in the fixture, the evaluator reproduces the CONFIRMED exit-audit counts for arm B (FAIL; hits 10/7/9/10, joint 7, boundary 0/3/0/0) and arm i (PASS; 10/8/8/10, joint 6, boundary 0/2/0/0).
  - The class function of §7.3 as a pure function, with a table-driven test over the complete partition: VOID; NO-READING with each cause and with both; and k = 0, 1, 2, 3, 4, 5, 6.
  - Readings, S1/S2 triggers and the status phrase as pure functions. Trigger endpoint tests at 4k′ = m, 4k′ = m + 1, m = 24 and m = 23. A test that each forbidden word of §7.3 is absent from every generated reading.
  - The G35-B, Phase-0 and Phase-0b dry-runs unchanged.
- **U2: generation, blind barrier, descriptives and reference evaluations.**
  - The shared-panel generation path and the six-library generation path, implemented and mock-tested with real config constructors and faithful result metadata (DIRECTOR lessons 2026-09-22). Evidence checks reject absent metadata.
  - Byte-sharing of target tables across libraries, verified by hash from an independent re-read.
  - Four batches at identical tuples, the nested 3/6/12 fits, D1–D5, and the reference evaluations reusing the descriptive surfaces.
  - The global barrier: every blind record of every library is persisted and read back before any truth join.
  - Work counters with reserve-before-dispatch and exact-equality checks.
- **U3: retention, bundle and summary.**
  - Target latent-truth retention and `auditor_recompute_notes.json`.
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
- **Six draws.** k is a count. CONSISTENT-PASS does not exclude a substantial library failure rate (§7.5 table), and no L that is affordable here separates a high pass probability from certainty.
- **A gate at its threshold.** With counts near their thresholds, MIXED can arise from few target-by-library flips. D1–D3 show which happened; they cannot change the class.
- **One level, one scenario.** R = 12 only; the same CI-scale scenario, grid and square-root objective, which is not a likelihood. A change of R can also shift the expected finite-library loss ordering across cells, not only its scatter, so "more replicates" and "less noise" are not the same statement.
- **Bundled noise sources.** Each replicate varies population, epidemic and observation draws together.
- **Nested reference.** The R = 3 batches are parts of their parent libraries and share the panel; m of 24 is not an independent control.
- **All-target predicates.** One unviable truth run in twenty forces NO-READING. Its probability is unknown.
- **Fallback-built populations** are kept and disclosed (G36 point-mass caveat).
- **Explicit unknowns:** π; the truth-viability rate; the build failure rate; wall time, bundle size, parent-build disk use and peak memory for this design; and whether the P3 flags are recomputable from retained fields.
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
| NO-READING if every library fails and the only failed predicates are library-independent (P2, P3, P9, P10) | NO-READING if any library's non-recovery predicates (P1, P2, P3, P9, P10) fail, with a recorded cause (§7.3) | The consult's rule had a hole when a shared failure coincided with recovery failures, and it treated P9 and P10 as wholly library-independent although each has a library-side component. The new rule is a complete partition. |
| Status phrase "G42: k/L library gates PASS (class word)" | Six per-library tokens under "G43:"; the class word never inside the phrase (§7.11) | G35-B amendment A9 and DIRECTOR's rule that status vocabularies never mix: readings do not appear in the status phrase. The gate number is G43. |
| Disclosure sentences compare 4k with m | They compare 4k′ with m (§7.8) | k includes non-recovery predicates and m does not. k′ makes both sides the same computation; in classes 3–5, k′ = k. |
| Pooled R = 72 reference offered as an owner option, leaning to include | Owner option, recommended default not computed; definition fixed if included (§7.9) | Steven's B2 text does not include it. It is one draw of a different level, which is the defect G41 was rejected for, and it could be read as a tested level. The retained bundle allows it later as a labelled EXPLORATORY analysis. |
| Two-block target descriptive (predicates 4–8 on the first and last ten targets) | Dropped | It is predeclared target subsetting and yields twelve gate-shaped sub-results, which conflicts with the exclusion list. D2 and D3 carry the same information without gate-shaped outputs. |
| "The G35-B arm-(i) PASS reads as a favourable draw" under CONSISTENT-FAIL | "consistent with a favourable draw of library, of targets, or both … this study cannot separate those" | G35-B used different targets and N = 10, so the stronger wording was an over-reading. |
| L = 6 "puts each direction under 2%" | L = 6 is the smallest L with 2 · 0.5^L ≤ 0.055, the figure accepted in frozen G35-B §7.3 (§7.6) | The 2% had no source. The precedent figure does, and the section says it is a precedent, not a law. |
| Reserve sizes left to the director | Ten target and six per library, written out (§8) | The brief requires that no seed be left implicit; the sizes are those the owner accepted for G41. |

**Adopted from the gpt-6.2-astra and gpt-6.2-sol consults:**
- the target × library matrices of joint hits and selected offsets (D2, D3);
- paired reporting of each library's R = 12 result beside its own four R = 3 batches (m_ℓ);
- the frozen wording for a shared-target failure (§7.4 NO-READING cause sentence) and the rule that the target is never removed and the panel never regenerated;
- "a reduced denominator has no reading" (§7.3);
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
| G41 contingent A2 (exploratory re-scoring kept out of the frozen text) | no retained recovery number is used; the only EXPLORATORY figures are wall-time and size planning estimates in §9 |
| G41 contingent A3 (the one-library sentence) | superseded by six libraries; its analogue is "on this one target panel" in every reading |
| Exit-audit O1–O5 | §9 (O1), §7.4 names things literally (O2), §10 `seats` (O3), §10 latent truth (O4), D1 margins (O5) |

## 18. Decisions the model owner must explicitly accept

1. The study question and estimand; outcomes authorize nothing beyond input to a later Steven gate (§1, §2).
2. Everything in §3 "Held fixed" is verbatim G35-B arm (i); the listed changes are the only changes.
3. The integer thresholds 16 / 12 / ≤ 4 at N = 20 and their derivation (§7.1).
4. The three predicate groups and the two booleans (§7.2).
5. The class table, its order, the boundary cases and both NO-READING causes (§7.3).
6. The five reading texts and the licence table (§7.4).
7. No k-of-L cut, and the stated limits of CONSISTENT-PASS (§7.5).
8. L = 6 (§7.6) and N = 20 (§7.7).
9. The R = 3 reference, k′, m, and sentences S1 and S2 with their triggers (§7.8).
10. Descriptives D1–D6, the agreement rule, and the pooled-reference default (§7.9); the exclusion list (§7.10).
11. The status-phrase extension (§7.11).
12. The seed table, reserve sizes, retired sets, builds-only pre-check and replacement rule; fallback builds count as builds (§8).
13. The exact caps; wall time and size as disclosures; the host-disk rule (§9).
14. The bundle contents, including target latent truth and the auditor notes (§10).
15. A new standalone module; the protected modules and the three named files unchanged (§11, §13).
16. The order, the seats named in advance, the exclusions and the substitution rule (§12).
17. One campaign; the VOID and FAIL rules (§12).

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

If the owner rules a different L (5–8) or N (10 or 30), libraries are added or removed whole by the §8 formula and target seeds become `86001…86000+N` and `98001…98000+N`; nothing else moves.

## Questions for the model owner

1. **Reading rule.** Do you accept the all / some / none classes with no k-of-L cut (§7.3, §7.5)? If you hold that a reliability standard is required, this design cannot supply one at L = 6, and the question returns to Steven, because G43 chose F over the 22-library design.
2. **CONSISTENT-PASS wording.** Is the stated limit ("do not rule out … one in five or three in ten") strong enough, or do you want the §7.5 table values quoted inside the reading itself?
3. **L.** 6 (default), or 5, 7 or 8? Do you accept the 0.055 precedent as the anchor, in its two-direction form?
4. **N.** 20 (default), 10 or 30? Do you accept that an unviable truth run forces NO-READING with no pre-campaign viability check?
5. **NO-READING.** Do you accept the definition on the non-recovery group, including the `library_integrity` cause? The alternative is to rule that any false library-integrity component makes the campaign VOID outright.
6. **R = 3 reference.** Do you accept k′ against m, and sentences S1 and S2 with their exact triggers and wording? Should S1 also be suppressed when k′ = m = 0?
7. **Pooled R = 72 reference.** Not computed (default), or included as defined in §7.9?
8. **Dropped block descriptive.** Do you agree to drop the two-block target descriptive from the consult?
9. **Status phrase.** Six per-library tokens (default), or a compact count such as "G43: <k>/6 PASS", which hides nothing but reads less like the earlier phrase?
10. **Seeds.** The 86/87/98/99 blocks, ten target reserves and six reserves per library, with per-library pools and exhaustion returning to you: accepted? Are the retired G41 ranges as listed sufficient?
11. **Seats.** The table and rules in §12, including the exclusion of the drafter and of the ruling model from the review and exit-audit seats, and Claude Fable 5.1 as the last exit-audit substitute?
12. **Retention.** Target latent truth retained and candidate latent truth not; P3-flag recomputability left as an explicit unknown for U3 to establish?
13. **P2 attribution.** Do you accept reporting each P2 and P3 condition separately, given that the G35-B implementation folds chronology, conservation and namespace into its P2 value (§7.2)?
14. **Implementation gate.** Should implementation after the freeze wait for Steven's separate authorization (default), as written in §12 step 2?
