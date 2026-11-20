# G41 confirmatory synthetic-recovery predeclaration: arm-(i) factor, fresh seeds (DRAFT 2026-11-19)

<!-- DRAFT by the design consultant (Claude Opus 5.5 @ high), foreman run g41-predecl unit 1, brief docs/runs/2026-11-19-g41-design-brief.md.txt (committed-bytes sha256 216f500d9bede46a5df4592d0a30beeb98bca169fdbc9931549fb751289c887b, commit 11ab4ca). Not ruled, not frozen. Every value marked <PLACEHOLDER: ...> is filled mechanically by the director at freeze, never chosen by hand. -->

## 1. Status and lineage

**Status:** DRAFT for the model-owner ruling. This document is not a Phase 0c, not a V1.3 gate, and not a second G35-B campaign. It is the "separately owner-ruled, fresh-seed confirmatory predeclaration" that frozen G35-B §1 and §7.4 require before any decision may rely on the G35-B arm-(i) screening PASS. Status phrase until a G41 campaign completes: **"Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B FAIL, i PASS, ii FAIL, iii FAIL; G41: not run"**. Real-data fitting stays STOPPED (G34 A+B).

**Authority:** G41 was resolved B by Steven in chat on 2026-11-19 ("B — Confirmatory study"; `.claude/GATES.md`, Resolved). That resolution commissions an owner-ruled predeclaration on fresh, pre-checked seeds. It does not authorize implementation or a campaign. Both are later Steven gates (§12).

**Designed after the results were seen.** This study was designed after Phase 0, Phase 0b, the ridge diagnostic, and the complete G35-B campaign and its exit audit had all been seen. Every choice below is argued from structure, from the frozen G35-B text, or from the grid-independent binomial table. Where retained G35-B results are quoted (§7.3), they are labelled EXPLORATORY and are not gate inputs. No threshold, grid, level, tolerance or bias limit is taken from them.

**What any outcome authorizes:** nothing beyond input to a separate, later decision by Steven. In particular:
- **No outcome licenses:** real Jersey fitting; reopening G34; a claim that Phase 0, Phase 0b or G35-B arm B passed; satisfying the V1.3 plan's Phase-0 gate; nominal coverage; Jersey calibration; or named-pathogen validation.
- **A G41 PASS** is a confirmatory *synthetic* result for one factor at one level (R = 12) on one scenario. At most it is input to Steven opening a separate gate. Reopening real-data fitting would require Steven's explicit chat decision on a new gate and a new owner-ruled predeclaration of its own (G35-B A1, carried forward).
- **A G41 FAIL** leaves the G35-B arm-(i) PASS as a screening result only. It changes no G35-B verdict.

**Lineage block** (copied verbatim into `campaign_summary.json` and the exit audit, kept apart from G41 results). Every SHA-256 is of committed bytes (`git show <commit>:<path> | sha256sum`; DIRECTOR lesson 2026-10-22), recomputed by this consult at HEAD `89a328c83982615a9fc67e30c138012ebc4844b8`.

| Item | Value |
|---|---|
| Phase-0 verdict / audit | `phase0_verdict: FAIL` · `docs/audits/2026-09-24-phase0-exit-audit-sol-FAIL.md` |
| Phase-0 bundle `SHA256SUMS` digest | `72cd9a568598530923e08ce20b013d60eb7a3b26553b87c31685ad623f3faa80` |
| Phase-0 predeclaration SHA-256 | `ef67fe49903c3984ca98679eb0470878bc25523baca3bc23a63e4ae7d983a104` |
| Phase-0b verdict / audit | `phase0b_verdict: FAIL` · `docs/audits/2026-09-26-phase0b-exit-audit-sol-FAIL.md` |
| Phase-0b bundle `SHA256SUMS` digest | `a319c5557ffa77c56baebb8341b5fc2e1432f367bdb9d0b34169aa079659032a` |
| Phase-0b predeclaration SHA-256 | `ec8df64630dd50c83b0866a096fba4980453c34232d18114129587274f257451` |
| Phase-0b failing predicates | P0-1 predicates 5, 6, 8; offset selections `4, 4, 0, 2, 0` against truth 2; boundary 4/5; joint 1/5 |
| Ridge diagnostic SHA-256 (binding, committed bytes; G35-B clarification 1) | `8cf4c76612434cbd90c5de4ca9dfd1326422b94a72bd4a63ccff71e95f34908a` (`docs/research/v1_3/2026-09-29-phase0b-ridge-diagnostic-EXPLORATORY.md`; CRLF alias `de13913b…`, non-binding) |
| G35-B predeclaration | `docs/research/v1_3/2026-10-22-g35b-predeclaration.md`, commit `3972190bd7cde523860fe303b41427c1c95c57eb`, SHA-256 `2e8358abd9e275a5cf04a58b4ad76313c10964f2da06d46cd0f8a7190733216e` |
| G35-B owner ruling | `docs/research/v1_3/2026-10-22-g35b-owner-ruling-ACCEPTED.md`, SHA-256 `f84738a9594312f3371f4bb469c5cfaafed265dc5d233ee34f1f0be564d99643` |
| G35-B clarification 1 / 2 | SHA-256 `2b1d4a5ee6bbab965a32e2abcdc4d00cab769d7d994a015fcf3bf5b0df0346d5` / `ccae8721871b78b22d84451202ff541cb5836f06f402e176fe97308e296215e0` |
| G35-B harness code SHA | `0c9c3711b4e1be3fa90e9ef7f1e8e883dbdb48d8` (G38 merge; `g35b_design_study.py` sha256 `f133ff3a…27f0`, `g35b_constants.py` `bc766a31…c494`, config `4259c45f…05d0`) |
| G35-B bundle | `/home/steven/jos-g35b-campaign-20261022T234254Z` (read-only), `SHA256SUMS` digest `e6649a4b32289ad32cec7862ed79ea75a5123d0231178bebf0db78f0fd54c8fc` |
| G35-B exit audit | `docs/audits/2026-11-19-g35b-campaign-exit-audit-opus-CONFIRMED.md`, commit `fec245b`, SHA-256 `595221768bb55b1459ef0f3c2938580cc1208ec8743c8071dbbd0fdc65713599`; verdict `JOS G35-B CAMPAIGN EXIT AUDIT: CONFIRMED` |
| G35-B results (final) | B FAIL (P5, P8), i PASS, ii FAIL (P5, P6), iii FAIL (P5, P8) |
| G35-B arm-(i) counts | hits beta/offset/sym/asym 10/8/8/10; joint 6/10; boundary 0/2/0/0; four-batch offset agreement 0/10 (descriptive). Four counts sit exactly at their inclusive thresholds (exit audit O5) |
| G41 resolution | Steven 2026-11-19, chat: "B — Confirmatory study" (trail row `g41-run-start`) |

## 2. Question and scope

**Single question.** At the declared level R = 12, on target and candidate seeds never used before, does the G35-B arm-(i) design recover all four dimensions (beta, inoculation-day offset, symptomatic detection, asymptomatic detection) under the frozen G35-B arm-(i) gate (predicates P1–P10, §7)?

**One gated arm.** The study has exactly one gated arm, called `i` (R = 12). There is no gated baseline and no other factor. Arms (ii) and (iii) failed and are not revisited. Because only one gate is evaluated, there is no within-study multiplicity (§7.4).

**Synthetic only.** No real Jersey data enter. The frozen Jersey 2020 serosurvey table (`covid_serosurvey_2020`) is not read, imported or used. No serosurvey is modelled in this study.

**No probe.** The window is the frozen 30 days, so no horizon probe or other pre-freeze simulation is needed; the only pre-freeze action on study seeds is the builds-only pre-check (§8). G35-B A3–A7 (probe and serosurvey) therefore have no counterpart here; A1, A2 and A8–A11 are carried forward in §1, §4, §7.4, §7.2(d)/§10 and §12.

**Research harness only.** Nothing is written through `CalibrationArtifactManifest` or `write_calibration_artifact`.

## 3. What is held fixed, and what changes (brief item a)

**Rule.** A confirmatory study changes only what it must: the seeds. Every other change below is either forced by "one arm on fresh seeds", or is a retention/disclosure fix that the G35-B exit audit asked for and that cannot move any gate. The target count is the one scientific choice, and it is the owner's (§7.3).

**Held fixed, verbatim from frozen G35-B §3, §4.1, §6 and §7.1:**

| Item | Value |
|---|---|
| Dimensions, truths, grids, tolerances, bias limits | the table below, as decimal strings with exact decimal arithmetic |
| Grid | 625 cells, all scored before selection |
| Latent scenario | `ci` mode, 3,000 residents, start `2025-01-06`, exactly 30 latent days. Initial seeds 0. Ten import attempts at `start_date + offset`; background import rate 0; no other imports. All eleven route multipliers `1.0`. Symptomatic probability `0.6`. Constant latent duration 2 d, infectious duration 5 d. Waning disabled. No seasonality, no interventions |
| Observation | two channels (symptomatic, asymptomatic) from `observation_events` `report_date` and `symptomatic`; detection delay 0, reporting delay 2, weekday factors `1.0`, four-day tail, 34 zero-filled dates (T = 34) |
| Objective | frozen G35-B §6 with R = 12, T = 34 (§6 below) |
| Candidate structure | R = 12 as four independent batches of three (A, B′, C′, D′), each evaluated at all 625 cells; nesting A ⊂ A∪B′ (6) ⊂ all (12); replicate order in every sum A, B′, C′, D′, ascending seed within a batch |
| Pairing | network and outbreak seeds match within each process run; one candidate observation config ID across cells (common random numbers); candidate latent runs reused across detection probabilities; target runs never serve as candidates |
| Tie and identification rules | τᵢ = 10⁻¹² · max(1, L_min); profile by minimizing over the other three dimensions; identified = unique profile minimum within τᵢ and relative gap ≥ 0.05 with denominator max(P_min, 10⁻¹²); a tied global minimum fails; ordinary float inclusive comparisons for computed gaps; exact decimal arithmetic for signed error, tolerance and bias; no epsilons, no reinterpretation at `0.05` or `1e-12` |
| Predicates | P1–P10 with the same meaning and the same threshold *fractions* (4/5, 3/5, ≤ 1/5), integer arithmetic (§7.1) |
| Forbidden | optimizer seed, post-freeze replacement, retry, adaptive grid, pruning, early stopping |

| Dimension | Truth | Grid | Tolerance | Bias limit |
|---|---:|---|---:|---:|
| beta | `0.08` | `0.04, 0.06, 0.08, 0.10, 0.12` | `0.02` | `0.01` |
| offset (days) | `2` | `0, 1, 2, 3, 4` | `1` | `0.5` |
| symptomatic detection | `0.75` | `0.50, 0.625, 0.75, 0.875, 1.00` | `0.125` | `0.0625` |
| asymptomatic detection | `0.25` | `0.10, 0.175, 0.25, 0.325, 0.40` | `0.075` | `0.0375` |

**Changes vs G35-B arm (i), and why none moves the goalposts:**

| Item | G35-B arm (i) | G41 | Why |
|---|---|---|---|
| Seeds | targets `82001–82010`; candidates `83001–83012`; obs `92/93` | all fresh (§8) | The purpose of a confirmatory study |
| Number of targets N | 10 | **owner option; default 20** (§7.3) | Same threshold fractions. A design whose true rates sit exactly at the thresholds is slightly *less* likely to pass at 20 than at 10, so the change cannot be read as tuned to confirm arm (i) |
| Batch A | byte-shared with the B gate arm | fresh; no gated B arm | One gated arm (§2, §7.5) |
| R = 3 / R = 6 references | B gate (R = 3) plus descriptives | descriptive sub-library references only (§7.2c) | No multiplicity; uses tables already generated, so no extra simulation |
| Retained latent truth | not retained (exit audit O4) | target latent truth retained (§10) | Lets the exit audit recompute P2/P3 from raw data. It changes no computation |
| Wall-time disclosure | two sources that disagreed (O1) | one source (§9) | Disclosure hygiene only |
| Readings text | template word "Factor X" (O2) | arm named literally (§7.4) | Text only |
| Step-7 reviewer line | in the trail and the review only (O3) | also in `campaign_summary.lineage` (§10) | Disclosure only |
| Seats | named after the fact (G35-B clarification 2, G40) | named in advance (§12) | No later clarification needed |

No grid, truth, tolerance, bias limit, threshold fraction, objective, R, T, tie rule or identification rule changes.

## 4. The arm

**Arm `i` (R = 12), gated.**
- **Targets:** N fresh target process seeds, each run once at the truth cell (beta 0.08, offset 2, sym 0.75, asym 0.25) with its paired fresh observation seed, config ID `v13-g41-target`.
- **Candidates:** twelve fresh candidate process/observation pairs in four batches of three. Each of the 12 process seeds runs at all 25 (beta, offset) latent tuples. Each latent run is observed at all 25 detection pairs with the paired observation seed, config ID `v13-g41-fit`.
- **Gate objective:** all 12 replicates.

**Why R = 12 is not re-argued.** R is the factor under confirmation. Its G35-B justification stands unchanged (G35-B §4.1 as amended by A2): it is the smallest multiple of 3 that halves the candidate-mean Monte-Carlo SD, and each batch is an independent draw of a Phase-0b-shaped objective. Changing R now would test a different factor, so any other R is excluded (§7.2).

## 5. Observation model

Verbatim G35-B §5.1: two channels from `observation_events` `report_date` and `symptomatic`, zero-filled over the 34-date calendar (`2025-01-06` to `2025-02-08`). Reports come only from `observation_events`. No serosurvey.

## 6. Objective

For target i, cell θ, channel c, date t and the R = 12 candidate replicates j in the declared order:

\[
m_{\theta ct}=\frac1{12}\sum_{j=1}^{12}\sqrt{x_{j\theta ct}+3/8},\qquad
L_i(\theta)=\frac{1}{2\cdot 34}\sum_{c=1}^{2}\sum_{t=1}^{34}\Big(\sqrt{y_{ict}+3/8}-m_{\theta ct}\Big)^2 .
\]

This is G35-B §6 at R = 12, T = 34, and it is computed bit-for-bit as `g35b_design_study.loss` computes it. It is not a likelihood. The tie and identification rules are exactly those in §3.

**Blind boundary.** The fitter receives only the target's observed tables, the declared grid and the candidate library. Each blind estimate, gate and descriptive alike, is hashed, persisted and read back before any truth join. All generation and all blind fits complete before any truth join.

## 7. Predicates, descriptives and readings

### 7.1 Recovery gate (brief item a)

These are the G35-B predicates with N in place of 10, evaluated with exact integer arithmetic: hits·5 ≥ 4·N; joint·5 ≥ 3·N; boundary·5 ≤ 1·N. At the default N = 20, the thresholds are **hits ≥ 16/20, joint ≥ 12/20, boundary ≤ 4/20**. At N = 10 they are 8/10, 6/10 and ≤ 2/10.

`G41 RECOVERY GATE: PASS` only if all of:
1. All N target runs, all 625 candidate cells and all 12 replicates per cell complete without replacement.
2. Each truth run realizes all ten inoculation acquisitions, at least one local secondary infection, reports in both channels, and at least three nonzero combined-report dates.
3. Observation chronology and latent-incidence conservation pass.
4. No target has a numerically tied global minimum.
5. Every dimension is identified and within tolerance for at least 4N/5 targets.
6. At least 3N/5 targets are identified and within tolerance jointly in all four dimensions.
7. Every dimension's absolute N-target mean bias is at most its limit (exact decimal; the sum of signed errors divided by N).
8. No dimension is selected at an outermost grid value for more than N/5 targets. This is computed by its own code path. On these grids every outermost value lies outside tolerance, so predicate 8 is implied by predicate 5 at any N. The per-dimension count is still reported.
9. Seeds, namespaces, grid, objective, dates, fixed parameters, read-back and blind provenance match this declaration, and every build reproduces its frozen M2/M3/M4 logical hashes.
10. Measured work equals the §9 caps.

**Status and failure rules (verbatim G35-B):**
- `software_status` and `scientific_status` are kept separate.
- An extinct or uninformative truth fails predicate 2 and is never resampled.
- A poor or extinct candidate is scored.

### 7.2 Comparisons and descriptives (brief items c, e)

**Primary comparison: none.** The only verdict is the single gate. There are no arm-versus-arm comparisons and no comparison with G35-B, which is lineage only.

**Explicitly excluded:**
- any gated R = 3 or R = 6 arm;
- pooling G41 with G35-B targets;
- target subsetting, for example excluding fallback populations;
- alternative thresholds, re-weightings, alternative R, alternative T or alternative N after freeze;
- any "best batch".

**Secondary descriptives** (reported, never gated; each record carries `label: stochastic_replicate_variation` or `label: descriptive_not_a_gate`; spreads are stochastic replicate variation, never confidence intervals):
- **(a) Gate rows.** Offset hits and boundary counts, per-target profiles, and per-target selected cells.
- **(b) Batch descriptives, repeated verbatim from G35-B §7.2(b).**
  - The re-profiled offset per target under each of A, B′, C′, D′ (3 replicates each), A∪B′ (6) and all 12.
  - The range and median of the four batch objectives at each fixed tuple. The median is the arithmetic mean of the middle two of the four sorted values.
  - The count of targets whose four batch offsets agree. **Agreement rule, stated here so no brief has to add one (DIRECTOR lesson 2026-10-22, G37 F3):** a batch's re-profiled offset is the unique offset value whose profiled objective lies within τ = 10⁻¹² · max(1, min profiled objective) of that minimum, or null if more than one value does. A target's four batches agree if and only if all four re-profiled offsets are non-null and equal. A global numerical tie in a batch's fit does not by itself make the batch disagree. This is the rule as implemented and accepted in G35-B (`batch_offset_agreement`, `_offset_descriptive` at `0c9c371`).
- **(c) Sub-library reference evaluations (new; replaces a concurrent control).** For each of the five sub-libraries A, B′, C′, D′ (R = 3) and A∪B′ (R = 6), apply the predicate 4–8 computation to that sub-library's blind fits on the same N targets. Report per-dimension hit counts, the joint count, per-dimension boundary counts, mean biases, the tie count, and a boolean `criteria_4_to_8_met`.
  - These records use the words "met / not met", never PASS/FAIL. They never enter the status phrase, the verdict lines or any reading. They are computed from surfaces the batch descriptives already score, so they add no loss evaluation.
- **(d) Disclosures.** Per-target `population_fallback_m2` and `population_fallback_m3`, a descriptive count of fallback-built targets and candidates, measured counters, and wall time (G35-B A10 as read by clarification 1 item 2). These are disclosures and never gate or subset.

### 7.3 Number of targets (brief item b; owner option, default N = 20)

**Options:** N = 10 (literal G35-B), **N = 20 (recommended default)**, or N = 30. In every option the thresholds are the frozen fractions, written as integer counts now: 8/6/2, 16/12/4 or 24/18/6.

**Grid-independent argument (the only gate-relevant argument).** Treat per-target success on a predicate as Bernoulli(p). The probability of meeting the threshold is:

| Per-target rate | P(≥ 4N/5 hits): N = 10 / 20 / 30 | P(≥ 3N/5 joint): N = 10 / 20 / 30 |
|---:|---|---|
| 0.5 | 0.055 / 0.006 / 0.001 | 0.377 / 0.252 / 0.181 |
| 0.6 | 0.167 / 0.051 / 0.017 | 0.633 / 0.596 / 0.578 |
| 0.7 | 0.383 / 0.238 / 0.160 | 0.850 / 0.887 / 0.916 |
| 0.8 | 0.678 / 0.630 / 0.607 | 0.967 / 0.990 / 0.997 |
| 0.9 | 0.930 / 0.957 / 0.974 | 0.998 / 1.000 / 1.000 |

The boundary predicate (≤ N/5) at per-target boundary rate q is the mirror image: q = 0.1 gives 0.930 / 0.957 / 0.974, q = 0.2 gives 0.678 / 0.630 / 0.607, and q = 0.3 gives 0.383 / 0.238 / 0.160.

**Reading of the table:**
- **Discrimination improves with N.** A design clearly below threshold (p = 0.7) passes the hits predicate 38% of the time at N = 10 but 24% at N = 20. A design clearly above (p = 0.9) passes more often.
- **A design that sits exactly at the threshold** (p = 0.8, q = 0.2) passes slightly *less* often as N grows (0.678 → 0.630). G35-B arm (i) observed counts exactly at threshold, so moving from 10 to 20 makes confirming a design that truly behaves like arm (i) marginally harder. The change cannot be read as tuned to make arm (i) pass.
- **Doubling N is the smallest step** that keeps every threshold an exact integer, follows the G35-B precedent (5 → 10, owner decision 3, ruled direction-neutral), and cuts the hits-predicate false-pass rate from 0.167 to 0.051 at p = 0.6 and from 0.055 to 0.006 at p = 0.5.

**Cost.** Targets are cheap; candidates dominate. Each extra target costs 1 build, 1 latent call, 1 report transform and 6 × 625 scorings. N = 20 adds 10 builds, 10 latent calls and 10 transforms to N = 10's 310 latent calls and 7,510 transforms (§9).

**What more targets cannot fix: the shared candidate library.** All N targets are scored against one 12-replicate library. Library-draw noise is common to every target, and more targets do not average it away. The binomial table therefore overstates how independent the target outcomes are. A G41 verdict is conditional on one library draw. Requiring several independent R = 12 libraries would change the gate and is excluded. It is listed as an owner question and a limitation (§15).

**Why 20 rather than 30.** Nothing in hand selects between them. 20 is the G35-B doubling precedent applied once more, and it keeps the reserve pool, the pre-check and the bundle small. If the owner prefers 30, every count in §8–§9 follows mechanically from the formulas given there.

**Steven's G41 wording.** The G41 option text reads "same pass/fail rules". Every option keeps the frozen predicates and threshold fractions; only N changes. The owner should rule explicitly that a fraction-preserving N counts as "the same pass/fail rules", as the G35-B ruling did for 5 → 10. If the owner rules that it does not, N = 10 applies.

**EXPLORATORY illustration (not a gate input; no threshold, level or N is chosen from it).** These numbers were computed by this consultant from the retained, read-only G35-B arm-(i) records, using the Python standard library only. The inputs were `arm_i/descriptive_estimates/{A,B_prime,C_prime,D_prime,A_union_B_prime}/*.json` and `arm_i/blind_estimates/*.json`. Each sub-library's selections were re-evaluated with the predicate 4–8 rules on the ten G35-B targets. Batch A reproduces the B gate counts exactly, which checks the script.

| G35-B library | R | Hits b/o/s/a | Joint | Boundary b/o/s/a | Mean bias offset | Predicates 4–8 met |
|---|---:|---|---:|---|---:|---|
| A (= B gate) | 3 | 10/7/9/10 | 7 | 0/3/0/0 | 0.1 | no |
| B′ | 3 | 8/6/7/8 | 5 | 0/2/0/0 | −0.4 | no |
| C′ | 3 | 8/6/7/6 | 5 | 0/3/1/0 | 0.1 | no |
| D′ | 3 | 8/8/8/8 | 7 | 0/0/0/0 | 0.3 | **yes** |
| A∪B′ | 6 | 8/3/7/7 | 3 | 0/3/0/0 | −0.6 | no |
| all 12 (arm i gate) | 12 | 10/8/8/10 | 6 | 0/2/0/0 | −0.2 | yes |

What this suggests, descriptively, about one campaign on ten shared targets:
- One of the four independent R = 3 batches would also have met predicates 4–8.
- The R = 6 nesting did worse than either of its R = 3 halves.

The G35-B contrast "B FAIL, i PASS" is therefore within the batch-to-batch variation of R = 3 libraries on these targets. This is exactly why a confirmatory test is needed, and why descriptive (c) is declared.

A crude bootstrap shows the same thing. It resampled target outcome vectors with replacement (20,000 resamples, seed 20261119) and ignored the shared-library correlation, so it overstates independence. Under it:
- an "arm-(i)-like" design (the ten all-12 vectors) meets predicates 4–8 with frequency ≈ 0.42 / 0.36 / 0.33 at N = 10 / 20 / 30;
- an "R = 3-like" design (the forty batch vectors) meets them with frequency ≈ 0.24 / 0.13 / 0.08.

These are resampling frequencies, not probabilities of any real design and not intervals. They are not gate inputs. Their only use is to warn every reader in advance that **a G41 FAIL is the more likely single outcome even if R = 12 behaves exactly as it did in G35-B**. The readings in §7.4 are worded accordingly.

### 7.4 Readings (brief item h; descriptive statements, separate from the gate vocabulary)

| G41 gate | Reading (verbatim) |
|---|---|
| PASS | "At the declared level (R = 12, four batches of three), on fresh target and candidate seeds, the candidate-replicate factor coincided with four-dimensional recovery under the frozen G35-B arm-(i) gate in this one confirmatory synthetic campaign of N targets. The G35-B arm-(i) screening result is confirmed at this level. This does not show that R = 12 is necessary or sufficient beyond this scenario, grid and objective; it is conditional on one candidate-library draw; and it authorizes no real-data fitting. At most it is input to Steven opening a separate gate." |
| FAIL | "At the declared level (R = 12, four batches of three), on fresh target and candidate seeds, the candidate-replicate factor did not reproduce four-dimensional recovery under the frozen G35-B arm-(i) gate in this one confirmatory synthetic campaign of N targets. The G35-B arm-(i) PASS is not confirmed and remains a screening result only. Monte-Carlo noise at three replicates is not shown to be the sole cause of the Phase-0/0b offset failure. This says nothing about other levels of R." |
| VOID | No reading. §12 VOID rules apply. |

N in each reading is replaced by the frozen integer. The sub-library reference descriptives (§7.2c) never alter, qualify or appear in a reading. No reading claims calibration, validation, coverage, a rate estimate, or that any spread is an interval.

**Multiplicity.** One gated arm means no within-study multiplicity, and the thresholds are not adjusted. The selection effect, that this factor was chosen because it passed among three, is what the fresh seeds address: no G41 datum took part in that selection.

**Status phrase (brief item h).** The existing phrase is kept intact and extended:
- before the campaign: "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B FAIL, i PASS, ii FAIL, iii FAIL; G41: not run";
- afterwards: "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B FAIL, i PASS, ii FAIL, iii FAIL; G41: <PASS|FAIL|VOID>".

PASS/FAIL is the recovery-gate verdict. VOID is a campaign status under §12. The §7.4 readings are descriptive text and never appear in the status phrase. The G41 token is final only after the exit audit returns CONFIRMED. Until then, state files append "(exit audit pending)" outside the phrase.

### 7.5 Why no concurrent gated control (brief item c)

**Options:**
- **(A) Recommended default:** no gated control; the R = 3 and R = 6 sub-library reference evaluations are descriptive (§7.2c).
- **(B)** A gated R = 3 co-primary arm on batch A, with a 2 × 2 readings table as in G35-B.
- **(C)** No R = 3 evaluation at all.

**Why A:**
- The question (§2) is whether R = 12 recovers. It is answered by one gate without a control.
- A gated control would reintroduce two verdicts and a readings table whose cells (for example "control PASS, i PASS") would invite exactly the forking interpretation that G35-B's multiplicity paragraph warned about.
- The exploratory table in §7.3 shows that one R = 3 library is a noisy comparator: R = 3 libraries ranged from 5 to 7 joint hits on the same targets. A single gated control would be a weak contrast. Four descriptive R = 3 references are more informative and cost no simulation.

**Why not C:** the references are free (the batch surfaces are already scored), and without them a G41 PASS could not be set beside the R = 3 behaviour on the same targets at all.

## 8. Seeds and replacement rule (brief item d)

**Disjointness.** All seeds are fresh and mutually disjoint. They are also disjoint from every earlier set, held as an independent module constant and never derived from the supplied config:
- Phase 0: `42001–42005`, `52001–52005`, `43001–43003`, `53001–53003`;
- Phase 0b: `62001–62005`, `72001–72005`, `63001–63003`, `73001–73003`;
- G35-B probe (retired): `81001–81006`, `91001–91003`;
- G35-B study, including the built but unused reserves, which are also retired: `82001–82015`, `83001–83017`, `92001–92010`, `93001–93012`, `94001–94010`, `95001–95003`.

The G41 series (84xxx, 85xxx, 96xxx, 97xxx) lie wholly outside the 42–43, 52–53, 62–63, 72–73, 81–83 and 91–95 thousand-blocks. A repository grep at HEAD `89a328c` found none of `84001`, `85001`, `96001`, `97001` in `src`, `configs`, `docs` or `.claude`. Seeds are reproducibility identifiers, not parameters.

**How seeds map to work.** The process seed is the population/network build seed (`build_parent(root, "ci", seed, …)`), and outbreak and network seeds match. Observation seeds build nothing.

**Seed table, written for any N** (default N = 20). Reserves sit in a separate block, so the choice of N never moves them:

| Role | Primary seeds | Paired observation seeds / config ID | Reserve (process only) |
|---|---|---|---|
| Target process | `84001` … `84000+N` (default `84001–84020`) | `96001` … `96000+N`, `v13-g41-target`, paired in order | `84101–84110` (10) |
| Candidate batch A | `85001–85003` | `97001–97003`, `v13-g41-fit` | `85101–85106` (6), one pool shared by all candidate batches |
| Candidate batch B′ | `85004–85006` | `97004–97006`, `v13-g41-fit` | as above |
| Candidate batch C′ | `85007–85009` | `97007–97009`, `v13-g41-fit` | as above |
| Candidate batch D′ | `85010–85012` | `97010–97012`, `v13-g41-fit` | as above |

The campaign ID is `v13-g41` and the optimizer seed is `null`.

**Why these reserve sizes.** G35-B saw 1 build failure in 38 (reserve 82011, adult-supply class), and Phase 0b needed a popgen fix. Ten target and six candidate reserves are a declared margin, not an estimate of the failure rate, which is unknown. Exhaustion returns the draft to the owner; the pool is never widened.

**Pre-freeze build pre-check and replacement rule** (deterministic and outcome-blind; G35-B §8 and ruling condition 2, verbatim in substance). It is applied once, by the director, **after the owner-ruling commit exists on `main`** (DIRECTOR lesson 2026-10-22), on a code tree identical to `0c9c3711b4e1be3fa90e9ef7f1e8e883dbdb48d8` for `src configs tests scripts`, and before any epidemic simulation of any study seed:
- Every process seed in the flat list (§17), primaries and reserves, is built with `build_parent` at mode `ci`. **Builds only:** no latent run, no observation, no loss.
- The record lists, per process seed: build outcome; exception class if any; presence of `private_assignment_residual_fallback` and `destination_reassignment_fallback`; and M2/M3/M4 logical hashes.
- A primary whose build raises any exception is excluded. It is replaced by the lowest-numbered reserve of the same role pool that built. The replacement takes the failed seed's position, paired observation seed and batch membership.
- Known failure classes include the adult-supply and household-capacity residual classes, which have no owner rule (G36).
- A build that succeeds through a reviewed fallback (M2 `private_assignment_residual_fallback` or M3 `destination_reassignment_fallback`) is **not** a failure. It is kept, and its fallback diagnostics are recorded as lineage and disclosed per §7.2(d).
- An exhausted pool returns the draft as NEEDS OWNER INPUT.
- The host's free disk is checked (≥ 5 GB, `df /mnt/c`) and logged before the pre-check.
- The frozen text lists final seeds, excluded seeds with their error class, and each final seed's M2/M3/M4 logical hashes. The campaign verifies that its builds reproduce them exactly (predicate 9), as an independent source of truth.
- After freezing there is no replacement of any kind. A build failure at execution fails predicate 1.

**Frozen pre-check outcome** (filled mechanically at freeze):
- Pre-check commit / tree attestation: `<PLACEHOLDER: ruling commit SHA; git diff --stat 0c9c3711b4e1be3fa90e9ef7f1e8e883dbdb48d8 HEAD -- src configs tests scripts = empty>`
- Outcome: `<PLACEHOLDER: k BUILT / m FAILED of 48 (at N = 20)>`; replacement triggered: `<PLACEHOLDER: yes/no, with each exclusion → replacement>`
- Record: `<PLACEHOLDER: docs/runs/2026-11-XX-g41-seed-precheck.json, committed-bytes sha256>`, with script `<PLACEHOLDER: …py.txt>` and log `<PLACEHOLDER: ….log>`
- Final-seed hash table: `<PLACEHOLDER: per seed: role, build, fallback disclosure, M2, M3, M4 logical hashes>`

## 9. Workload and fail-closed caps (brief item i)

Each parent is built once per process seed. Each candidate latent run is reused across the 25 detection pairs. With N targets:

| Quantity | Formula | N = 10 | **N = 20 (default)** | N = 30 |
|---|---|---:|---:|---:|
| Gate cells | 625 | 625 | **625** | 625 |
| Builds | N + 12 | 22 | **32** | 42 |
| Latent calls (30 d) | N + 12 × 25 | 310 | **320** | 330 |
| Report transforms | N + 625 × 12 | 7,510 | **7,520** | 7,530 |
| Gate loss evaluations | 625 × N | 6,250 | **12,500** | 18,750 |
| Descriptive loss evaluations (A, B′, C′, D′, A∪B′) | 5 × 625 × N | 31,250 | **62,500** | 93,750 |
| Sub-library reference evaluations (§7.2c) | 0 extra (reuse descriptive surfaces) | 0 | **0** | 0 |

**Dry-run must enforce exact equality** to the frozen column:
- cells 625;
- builds, latent calls and transforms as above;
- gate and descriptive loss evaluations as above;
- latent duration exactly 30 and calendar exactly 34 dates;
- mode `ci`.

It also rejects:
- seed overlap within the study or with any earlier set (§8);
- retries, replacement and adaptive work;
- any predicted or measured breach.

**Outside the campaign:** the pre-check builds N + 22 process seeds (48 at N = 20). It runs no latent call.

**Wall time (unmeasured for this design; disclosure only, never a cap).** G35-B arm (i) per-phase totals (`campaign_summary.disclosures.i.phase_wall_time_seconds`) imply ≈ 0.96 s per latent call, ≈ 0.11 s per transform and ≈ 1.7 s per build. Scaling linearly, which is unreliable, gives roughly 20 min at N = 20. The campaign records per-phase `time.perf_counter()` totals (build, latent, transform, scoring) and every latent call's `runtime_seconds`. **All wall-time figures come from one source,** `campaign_summary.json.disclosures`; any per-arm disclosure file copies them byte-for-byte or omits them (fixes exit-audit O1).

**Retained size.** Unknown; this consult did not measure the G35-B bundle on disk. Rough order: 7,520 candidate and target tables at ≈ 3.9 KB (the Phase-0b figure) ≈ 30 MB, plus blind records, N target latent-truth files and the parents. The director checks host free disk (≥ 5 GB) before execution and discloses the measured bundle size.

## 10. Bundle (brief item i)

One fresh, immutable bundle in a new, empty destination outside the repo, containing:
- **Frozen inputs:** this predeclaration (frozen), the owner ruling, any clarification, the config, and the pre-check record. Each is stored as committed bytes with its SHA-256, plus source and config hashes for every tracked `.py/.yaml/.json` under `src/jersey_outbreak` and `configs`.
- **Seed ledger** for every role, with pairing, batch and replacement status.
- **Target tables** (N) and **target provenance:** returned and requested run and observation configs, `observation_rng`, and population lineage.
- **Target latent truth (new; fixes exit-audit O4).** Per target:
  - the complete `transmission_events` (all rows, all fields);
  - the complete `daily_epidemic`;
  - the latent diagnostics `natural_history` and `states` payloads;
  - the complete `observation_events` and the observation diagnostics keys used by P3.

  This lets the exit audit recompute P2 (imports, local secondaries, channel sums, nonzero dates) and as much of P3 as the retained fields determine.
  - **Explicit unknown:** this consult did not establish whether `natural_history.chronology_passed` and `states.conserved` can be recomputed from these retained fields alone. U1 must establish it, write an `auditor_recompute_notes.json` naming which P2/P3 inputs are recomputable from raw rows and which are only internally checkable (each with its code locator), and test the recomputable ones against the harness flags.
  - Candidate latent truth is not retained, because no predicate uses it.
- **Candidate replicates:** the two-channel table for every (cell, replicate), with its process seed, observation seed, batch, `table_sha256`, population lineage (M2/M3/M4 logical hashes and both fallback flags) and `observation_rng`.
- **Gate blind records** (N) and **descriptive blind records** (5 × N), each with read-back hashes, plus `blind_readback_hashes.json`.
- **`g41_recovery.csv`:** every per-target predicate value, the boundary flag computed by its own code path, `population_fallback_m2` and `population_fallback_m3` (disclosures only).
- **`g41_descriptives.json`:** §7.2(b) and (c), labelled.
- **`campaign_summary.json`:** the §1 lineage block, plus a `step7_reviewer` line (model @ effort, and any substitution under §12 with the filtered attempt's token count or `not applicable`; fixes O3). It also carries `software_status`, `scientific_status`, the gate verdict, the §7.4 reading, the status phrase, measured-versus-planned work and the disclosures.
- **`SHA256SUMS`** covering every other file, with write bits removed and the bundle re-verified after sealing.

The exit-audit verdict lines read `G41 RECOVERY GATE: PASS|FAIL`, followed by the §7.4 reading. The audit's own verdict is `JOS G41 CAMPAIGN EXIT AUDIT: CONFIRMED | DISCREPANCY | VOID`.

## 11. Protected contracts

No change to any of:
- `outbreak_runner.py`, `respiratory.py`, `observation.py`, `observation_scheduler.py`, `observation_schemas.py`, `population_*`, `parent_build.py`, `starsim_adapter.py`, `calibration*.py`, `hashing.py`, `scientific_hashes.py`;
- any artifact schema or identity/persistence contract;
- the handoff §10.4 list.

**`phase0_campaign.py`, `g35b_design_study.py` and `g35b_constants.py` stay byte-unchanged.** The Phase-0, Phase-0b and G35-B dry-runs must still report 198/59/599/8, 1,334/107/4,007/8, and 2,500/395/9,395/85/22 respectively.

**Stop condition:** any need to modify a protected module, any of these three files, or a contract stops the unit. It requires a separate owner-rulable brief.

## 12. Unit order, seats and VOID/FAIL rules (brief items f, g)

**Implementation approach (item f).** "Reuse the existing harness with a new config" is not possible without editing frozen code. The G35-B harness hard-codes:
- the G35-B declaration: `validate_frozen_payload` compares the config to `g35b_constants`, including seeds, the predeclaration digest, caps and process hashes;
- ten targets and the G35-B target seeds in `evaluate_recovery`;
- G35-B caps in `WorkCounter`;
- a completed gated B generation as the precondition of `arm_i`;
- G35-B-specific readings and status text.

The smallest change that keeps the frozen semantics is therefore a **new standalone module that imports the G35-B pure functions unchanged**:
- `loss`, `fit_blind` and `_fit_scored_grid`;
- `_offset_descriptive`, `batch_offset_agreement` and `batch_objective_spread`;
- `committed_document_bytes` and `verify_parent`;
- the generation adapter, where its interface accepts a G41 counter and config;
- the Phase-0 config constructors.

It adds only:
- a G41 declaration and an independent constants module;
- an N-target generalization of `evaluate_recovery`;
- the single-arm generation path;
- retention;
- readings.

Files:
- `src/jersey_outbreak/g41_confirmatory.py`
- `src/jersey_outbreak/g41_constants.py`: independent; holds every earlier seed set from §8, this document's committed-bytes digest, the final seeds and the M2/M3/M4 hashes
- `configs/calibration/v13_g41_confirmatory.yaml`: decimal strings, every seed listed
- `tests/test_g41_confirmatory.py`

**Units (both `Class: numerical`):**
- **U1: declaration and gate.**
  - Constants, config, strict frozen-payload validation, and a dry-run that reports the §9 counts exactly.
  - The N-target evaluator with integer predicates. Endpoint regressions at 16/20, 12/20 and 4/20 (or the frozen N's), plus decimal endpoint and cancellation regressions for bias at N.
  - **Independent source of truth:** at N = 10, the evaluator reproduces the CONFIRMED G35-B exit-audit counts for B (FAIL; 10/7/9/10, joint 7, boundary 0/3/0/0) and for i (PASS; 10/8/8/10, joint 6, boundary 0/2/0/0). It does so from a fixture derived from the retained G35-B blind records, with the source files' SHA-256 recorded in the fixture.
  - `loss` at R = 12 equals the G35-B function bit-for-bit on fixtures.
  - Readings and status phrase as pure functions, with a table-driven test over PASS/FAIL/VOID.
  - The G35-B, Phase-0 and Phase-0b dry-runs unchanged.
- **U2: generation, descriptives, retention and bundle.**
  - The single-arm generation path, mock-tested with real config constructors and faithful result metadata (DIRECTOR lessons 2026-09-22).
  - Four batches at identical tuples, the nested 3/6/12 descriptives, and the §7.2(c) references reusing the descriptive surfaces.
  - The global "all blind fits before any truth join" barrier.
  - Target latent-truth retention and `auditor_recompute_notes.json`.
  - Measured-equals-planned checks, the single-source wall-time disclosure, sealing and `verify_bundle`.
  - Real-object smokes only on non-study seeds (for example the CI seed 123), never on a G41 study seed.
  - No campaign execution.

Every brief quotes the governing frozen sentence verbatim with its line number. Any director elaboration is labelled as a mechanical consequence with its derivation, or as an open owner question; it never enters as a requirement (DIRECTOR lesson 2026-10-22, G37 F3). Unit keeps commit locally, or to `review/<run>`. The feature branch is pushed once, after the review PASS is filed on `main` (DIRECTOR lesson 2026-10-22, g37 trail audit). Budget: 3 implementation runs including correctives, unless Steven extends.

**Order:**
0. **Owner ruling** on this draft (Fable 5.1 model-owner seat, under Steven's delegation, as in run `g41-predecl` unit 2).
1. **Director pre-freeze actions** (no study simulation):
   - commit the ruling via `fm.sh sync` `[skip ci]`; record its committed-bytes SHA-256 in the trail; attest that `git diff --stat 0c9c3711b4e1be3fa90e9ef7f1e8e883dbdb48d8 HEAD -- src configs tests scripts` is empty;
   - check and log host disk;
   - run the builds-only pre-check of §17 on that tree, then the replacement rule;
   - fill the final seeds and hashes mechanically into §8; commit the frozen predeclaration via `fm.sh sync` `[skip ci]`; record its committed-bytes SHA-256 in the trail.

   No pre-freeze action may start before the commit that authorizes it exists on `main`. An exhausted reserve pool returns the draft to the owner.
2. **Steven authorizes implementation** (a new GATES item, default HOLD).
3. **U1, then U2,** implemented by **gpt-6.1-sol @ high**. The director re-accepts each unit and runs the full CI verify-job mirror to PASS on the integration head; the log is filed under `docs/runs/` before any push or review launch.
4. **Independent implementation review** of the complete U1–U2 implementation against the frozen text, by **Claude Opus 5.5 @ high**, a fresh instance that authored no part of this study's code. It is given the frozen predeclaration, the ruling, any clarification, and the complete implementation (code, config, tests, dry-run and cap evidence). It runs no study simulation and touches no seed. A defect it names returns the implementation to the executor before step 5.
5. **Steven's SHA-first merge** of the reviewed head (default HOLD).
6. **Steven authorizes the single campaign** (default HOLD). It runs at the merge commit, in a fresh clean clone, into a new empty directory outside the repo. The launcher refuses to start if an exit marker exists. Every precondition and every push uses explicit `|| die`, with `git ls-remote` checked after any push (DIRECTOR lesson 2026-10-23).
7. **Fresh independent exit audit** by **gpt-6-astra @ high** (never `ultra`). It recomputes every predicate from the raw bundle using the Python standard library only, checks the readings against §7.4, and returns `JOS G41 CAMPAIGN EXIT AUDIT: CONFIRMED | DISCREPANCY | VOID`. Only after CONFIRMED does the status phrase become final.
8. **Trail audit** at the end of each run, on the family other than the director's (DIRECTOR Roles).

**Seat rule for unavailability or a classifier stop** (decided now, so no clarification is needed later):
- **Never rephrase or resubmit filtered content to the same provider** (DIRECTOR lesson 2026-10-22). Every stop is logged with its token count and disclosed in the trail, the affected report and `campaign_summary.lineage`, as "<seat>: <model @ effort>, substituted under G41 §12".
- **Implementer:** gpt-6.1-sol @ high. If it is filtered or unavailable, the unchanged brief goes to Claude Opus 5.5 @ high in an isolated worktree.
- **Reviewer (step 4):** the first available of [Claude Opus 5.5 @ high, gpt-6-astra @ high] that is not the implementer's model. After any OpenAI classifier stop on this study's content, the reviewer is taken from the Claude family only.
- **Exit auditor (step 7):** the first available of [gpt-6-astra @ high, Claude Opus 5.5 @ high, Claude Fable 5.1 @ high, a fresh instance that issued no ruling on this study] that is neither the implementer's model nor the reviewer's model. After any OpenAI classifier stop on this study's content, OpenAI seats are skipped.
- **If no eligible seat remains** for a step, that step is not satisfied and the next step does not open. The matter returns to the owner, and no campaign is authorized on a Sol review, a director self-review, or no review. If the exit audit has no seat, the results stay "not final".

**VOID and FAIL rules (G35-B §12, carried forward):**
- A software exception during the campaign seals a partial bundle with `software_status` FAIL and campaign status VOID.
- A defect named by the independent reviewer or exit auditor makes the campaign VOID. A corrected rerun uses the same frozen seeds, and only with Steven's authorization.
- A scientific FAIL is never reclassified.
- No second campaign without Steven's explicit chat decision.

## 13. Acceptance commands (proposed; not run in this consult)

```bash
git rev-parse HEAD; git status --porcelain
UV_CACHE_DIR=/tmp/uv-cache uv run python -m jersey_outbreak.g41_confirmatory dry-run \
  --config configs/calibration/v13_g41_confirmatory.yaml \
  --predeclaration docs/research/v1_3/<frozen-g41-predeclaration>.md          # §9 frozen column
UV_CACHE_DIR=/tmp/uv-cache uv run python -m jersey_outbreak.g35b_design_study dry-run \
  --config configs/calibration/v13_g35b_design_study.yaml \
  --predeclaration docs/research/v1_3/2026-10-22-g35b-predeclaration.md        # 2,500/395/9,395/85/22
UV_CACHE_DIR=/tmp/uv-cache uv run python -m jersey_outbreak.phase0_campaign dry-run \
  --config configs/calibration/v13_phase0_synthetic.yaml \
  --predeclaration docs/research/v1_3/2026-09-21-phase0-predeclaration.md      # 198/59/599/8
UV_CACHE_DIR=/tmp/uv-cache uv run python -m jersey_outbreak.phase0_campaign dry-run \
  --config configs/calibration/v13_phase0b_synthetic.yaml \
  --predeclaration docs/research/v1_3/2026-09-25-phase0b-predeclaration.md     # 1,334/107/4,007/8
# then the CI verify-job step list exactly (read .github/workflows/ once; ruff check+format, mypy pinned list,
# compileall, focused pytest on test_g41/test_g35b/test_phase0*/test_phase0b*, full pytest once on final bytes)
git diff --check; git status --porcelain
```

## 14. Questions the frozen text must not leave open (checked)

| Item | Where fixed |
|---|---|
| R, T, batches, order of summation | §3, §6 |
| N and integer thresholds | §7.1, §7.3 (owner option; default 20 → 16/12/4) |
| Agreement-descriptive rule | §7.2(b) |
| Reference descriptives vocabulary | §7.2(c) |
| Seeds, reserves, config IDs, replacement | §8 |
| Caps | §9 |
| Latent-truth retention | §10 |
| Seats and fallbacks | §12 |
| Readings and status phrase | §7.4 |

## 15. Limitations

- **One library draw.** All targets share one 12-replicate library. A verdict is conditional on that draw, and more targets cannot average library noise away (§7.3).
- **N targets give a screen of per-target rates, not a rate estimate.** At N = 20 a design near the 0.8 threshold passes about as often as it fails.
- **One level, one scenario.** R = 12 only; the same CI-scale scenario, grid and square-root objective (not a likelihood); no interactions with window length or anchors.
- **Process and observation noise are not separated.** Each replicate varies both streams.
- **Populations built through reviewed fallbacks** are kept and disclosed (G36 point-mass caveat).
- **Exploratory numbers in §7.3** come from ten shared G35-B targets and one campaign. They are illustrations, not estimates, and the bootstrap ignores library correlation.
- **Replicate spreads** are stochastic replicate variation, never confidence intervals.

## 16. Attestation

- **Checkout.** Windows checkout at HEAD `89a328c83982615a9fc67e30c138012ebc4844b8`. `git diff --stat 0c9c3711b4e1be3fa90e9ef7f1e8e883dbdb48d8 HEAD -- src configs tests scripts` was empty, and `git status --porcelain` was empty before this file was written.
- **Read in full:** G35-B predeclaration, owner ruling, clarifications 1–2, exit audit, ridge diagnostic, `.claude/DIRECTOR.md`, `RUN.md`, and the G35-B config. Also the harness sections `g35b_design_study.py:71–600, 654–930, 1162–1480, 2371–2480, 2600–2800`, `g35b_constants.py`, and `phase0_campaign.truth_diagnostics_from_events` and `_truth_diagnostics_from_result`.
- **G35-B bundle** (read-only): top-level listing; `arm_i/g35b_i_descriptives.json`; `campaign_summary.json` (keys and wall-time disclosures); `arm_i/descriptive_estimates/*/*.json`; `arm_i/blind_estimates/*.json`; `B/blind_estimates/*.json`. These were read by stdlib Python on stdin, and nothing was written.
- **Nothing else changed or run.** This file is the only file written. No commit, no simulation, no build, no fit, no test.

## Decisions the model owner must explicitly accept

1. G41 is one gated arm (R = 12) on fresh seeds; outcomes authorize nothing beyond input to a later Steven decision (§1, §2).
2. Everything in §3 "Held fixed" is verbatim G35-B arm (i); the listed changes are the only changes (§3).
3. N (default 20) with the frozen fractions as integer counts, and the ruling that this is "the same pass/fail rules" (§7.3).
4. No gated control; the R = 3 and R = 6 sub-library references are descriptive, in "met / not met" vocabulary (§7.2c, §7.5).
5. The agreement-descriptive rule as written (§7.2b).
6. The seed table, reserve sizes, builds-only pre-check and replacement rule; fallback builds count as builds (§8).
7. The exact caps; wall time and size as disclosures only (§9).
8. The bundle additions, especially target latent truth and the auditor recompute notes (§10).
9. A new standalone module; `phase0_campaign.py`, `g35b_design_study.py`, `g35b_constants.py` and the protected modules unchanged (§11, §12).
10. The unit order, the seats named in advance and the substitution rule (§12).
11. The readings, the status-phrase extension and the VOID/FAIL rules (§7.4, §12).

## 17. Full flat seed list for the pre-check (at default N = 20)

**Process (build) seeds; build-check all 48 at mode `ci` on the attested tree:**
84001, 84002, 84003, 84004, 84005, 84006, 84007, 84008, 84009, 84010, 84011, 84012, 84013, 84014, 84015, 84016, 84017, 84018, 84019, 84020, 84101, 84102, 84103, 84104, 84105, 84106, 84107, 84108, 84109, 84110, 85001, 85002, 85003, 85004, 85005, 85006, 85007, 85008, 85009, 85010, 85011, 85012, 85101, 85102, 85103, 85104, 85105, 85106

**Non-building seeds (disjointness check only; 32):**
96001, 96002, 96003, 96004, 96005, 96006, 96007, 96008, 96009, 96010, 96011, 96012, 96013, 96014, 96015, 96016, 96017, 96018, 96019, 96020, 97001, 97002, 97003, 97004, 97005, 97006, 97007, 97008, 97009, 97010, 97011, 97012

At N = 10 or 30, the target primaries and target observation seeds become `84001…84000+N` and `96001…96000+N`; everything else is unchanged.

## Questions for the model owner

1. **N:** 10, 20 (default) or 30 targets? Does a fraction-preserving N count as Steven's "same pass/fail rules"?
2. **Control:** is (A) descriptive sub-library references with no gated control (default) acceptable, or do you want (B) a gated R = 3 co-primary?
3. **One library draw:** do you accept a verdict conditional on one 12-replicate library (default), or do you require several independent libraries? Requiring them would change the gate and the cost.
4. **Seats:** reviewer Opus 5.5 @ high and exit auditor gpt-6-astra @ high (default), or the G35-B arrangement as executed (reviewer astra, auditor Opus)? Do you accept the substitution list in §12?
5. **Retention:** target latent truth retained, candidate latent truth not (default)? And do you accept that the P3-flag recomputability is an explicit unknown for U1 to establish?
6. **Status token:** is "G41: <PASS|FAIL|VOID>" appended to the existing phrase acceptable?
7. **Retired G35-B reserves** (82011–82015 and 83013–83017, built but unused): excluded as earlier sets (default)?
8. **Reserve sizes** of 10 target and 6 candidate seeds, with exhaustion returning to you: accepted?
9. **Exploratory §7.3 material:** keep it in the frozen text as labelled illustration (default), or move it to a separate EXPLORATORY note cited by hash?
