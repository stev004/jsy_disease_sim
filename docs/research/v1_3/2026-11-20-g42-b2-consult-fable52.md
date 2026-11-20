<!-- G42-B2 design consult, one of three independent consultants on one shared brief (docs/runs/2026-11-20-g42-b2-consult-brief.md.txt) at main 6708ad238860872a5ea548943fc004a0424cb261. Consultant: Claude Fable 5.2 (claude-fable-5-2) @ high, Claude subagent dispatched by the director (Claude Opus 5.5) on 2026-11-20. Tokens 159,120; 10 tool uses; 167 s. Filed verbatim by the director. CONSULT ONLY — not a ruling, not frozen. -->

**Claude Fable 5.2 (`claude-fable-5-2`), reasoning effort: high**

Read-only consult. I wrote no file and ran no simulation, build, fit or test. I read the owner ruling, the rejected G41 draft, the exit audit, the ridge diagnostic and `.claude/DIRECTOR.md` in full, the frozen G35-B predeclaration to line 475 (§1–§12 and the start of §13), and the function index of `g35b_design_study.py`. The only bundle access was `campaign_summary.json` disclosures and a `du`/file count, and anything derived from them is labelled EXPLORATORY.

## 1. Estimand

**What is measured.** For the frozen arm-(i) design, the gate verdict is a function of two random draws: the candidate library (12 process/observation pairs, four batches of three) and the target set. The study measures the across-library distribution of the frozen gate verdict and its underlying counts, with the target set held fixed and shared. The primary datum is k, the number of L independent libraries whose frozen gate is PASS on the same N targets. The supporting data are the L × N per-target outcome matrices.

**Three answers, defined logically rather than by a tuned cut:**
- **Yes (CONSISTENT-PASS), k = L.** Every drawn library passed, so no library dependence of the verdict was observed in L draws on these targets. This is "not observed to depend", not "proved stable".
- **No.** There are two distinct forms:
  - **MIXED, 0 < k < L.** Two libraries gave opposite verdicts on byte-identical targets. That is a direct demonstration, not a statistical inference, that the verdict depends on the library draw.
  - **CONSISTENT-FAIL, k = 0.** R = 12 did not produce recovery under any drawn library, and the G35-B arm-(i) PASS reads as a favourable draw.
- **Can't tell.** VOID, or a common-cause failure (§4): every library fails on a predicate that does not involve the library (P2, P3, P9, P10). No reading on library dependence is issued.

**Limit that must be in the frozen text.** All three readings are conditional on one target set, one scenario, one grid and one objective. They authorize nothing beyond input to a later Steven gate.

## 2. L and N

**L = 6 (owner's call; my range is 5–8).**

- **What L controls.** It is the number of draws of the thing that varies. It is the only lever on "one draw" (ruling §3.1).
- **Structural floor.** L = 2 cannot separate anything. L ≥ 3 is needed even to see a non-unanimous majority.
- **Sizing argument.** I use the same grid-independent argument G35-B §7.3 used for targets. Treat a library's verdict as Bernoulli(π), with π unknown and not estimated here. A "coin-flip" design (π = 0.5) yields a unanimous result in either direction with chance 2·0.5^L: 12.5% at L = 4, 6.3% at L = 5, 3.1% at L = 6. G35-B accepted about 6% for the analogous single-direction error, and L = 6 is the smallest L putting each direction under 2%.
- **What L cannot do.** Unanimous PASS at L = 6 still occurs with chance 0.12 at π = 0.7 and 0.26 at π = 0.8. No affordable L separates π = 0.9 from 1.0. The frozen text should print this table instead of implying more.
- **Cost of going higher.** Unanimity gets stricter as L grows: π = 0.9 gives MIXED 47% of the time at L = 6. That is intended, because such a design does depend on the draw, and k/L is always reported.
- **Side benefit.** L = 6 yields 24 independent R = 3 batches for the reference (§5).
- **Cost per library.** Cost is linear: 12 builds, 300 latent calls and 7,500 transforms each (§7).

**N = 20 (fraction-preserving; thresholds 16/20, 12/20, ≤ 4/20). Ruling §4 already holds this within "same pass/fail rules".**

- **What N controls.** It does not add library draws. It controls gate granularity and how much the result depends on one target set.
- **Granularity.** At N = 10 every threshold is one target wide, so a single target-by-library flip changes a verdict. MIXED would then be reached by the coarsest possible flicker. N = 20 halves that.
- **Target-set dependence.** A hard or easy target set pushes all libraries the same way and can manufacture unanimity. More targets dilute this, and the block descriptive in §4 exposes it.
- **Cost.** One build, one latent call and one transform per target, plus scoring, which measured as negligible.
- **Why not 30 or more.** Nothing structural selects it, and at-threshold behaviour does not sharpen with N (0.68 / 0.63 / 0.61 at p = 0.8). It is the owner's option, and all counts follow mechanically.

## 3. Independence and sharing

- **Libraries.** Each library gets 12 fresh process seeds and 12 fresh paired observation seeds in a declared contiguous block, with four batches of three in ascending order. No seed appears in two libraries.
- **Partition is fixed.** Membership is set by the seed table before the pre-check. Re-partitioning the 72 replicates into other R = 12 sets is excluded as a forking path.
- **Observation config.** One candidate observation config ID, as frozen. This keeps common random numbers across cells within a replicate; independence across libraries comes from the seeds.
- **Seed blocks.** Fresh, disjoint from every earlier set and from the never-built G41 series named in the rejected draft, which I would retire. The director assigns blocks mechanically; I choose no numbers.
- **Targets.** N fresh targets, byte-shared across all L libraries, never used as candidates. Sharing is essential: it is what makes a verdict difference attributable to the library alone.
- **Pre-check.** Builds-only, after the ruling commit, with the frozen replacement rule. I recommend one reserve pool per library so that a replacement never moves a seed between libraries. Reserve sizes are a declared margin, not a failure-rate estimate, and the 1-in-38 failure in G35-B is not a rate.
- **Declared limitation.** The process seed also draws the population and network, so "library variation" bundles population, epidemic and observation noise. The study does not separate them.

## 4. Per-library gate and across-library rule

**Per library:** frozen P1–P10 verbatim at N = 20, with integer arithmetic, exact decimal bias, the same tie and identification rules, and the same blind boundary. All generation and all blind fits for all libraries complete before any truth join. Each library gets its own `LIBRARY ℓ RECOVERY GATE: PASS|FAIL` line.

**Across libraries:** there is no study-level gate and no study-level PASS/FAIL token. The study reports k/L and one of four class words: CONSISTENT-PASS (k = L), MIXED, CONSISTENT-FAIL (k = 0), or NO-READING.

Why this is not a disguised change of the pass/fail rules:
- No predicate, threshold or fraction changes, and no k-of-L cut is introduced.
- The classes are the only partition that needs no chosen number: all, some, none. Any "at least L−1" rule would be an invented parameter.
- The asymmetry is conservative. The only class that could feed a later Steven gate requires every library to pass.

**Boundary rule.** k = L−1 is MIXED and k = 1 is MIXED. Wording such as "nearly", "majority" or "best library" is forbidden in readings.

**Common-cause rule.** If every library fails and the only failed predicates are library-independent (P2, P3, P9, P10), the class is NO-READING and predicates 4–8 are still reported. The per-library FAIL tokens stand and are never reclassified.

**Declared descriptives** (never gated; labelled `stochastic_replicate_variation` or `descriptive_not_a_gate`):
- per-library counts and their margin to each threshold, in targets;
- the L × N hit, joint and boundary matrices;
- per-target count of libraries hitting (0…L), which shows whether misses are target-driven rows or library-driven columns;
- the count of targets on which all L libraries select the same offset;
- predicates 4–8 "met / not met" on two declared target blocks of 10 (first and last ten seeds), per library, as a view of target-set dependence at the G35-B granularity.

**Status phrase.** Append "G42: k/L library gates PASS (class word)". It becomes final only after a CONFIRMED exit audit.

## 5. The R = 3 concurrent reference

**Purpose.** It answers "relative to what?". The 4L = 24 batches are 24 independent Phase-0b-shaped objectives on the same targets, built from the same replicates. Without them a CONSISTENT-PASS could not be set beside R = 3 behaviour at all. In G35-B one of four R = 3 batches also met predicates 4–8.

**How it is read.**
- Predicates 4–8 "met / not met" per batch, with m of 24 reported beside k of 6.
- The frozen A∪B′ (R = 6) reference per library, for the non-monotonicity seen in G35-B.
- Two mandatory disclosure sentences, each triggered by exact integer comparison with no threshold:
  - if 4k ≤ m: "R = 12 libraries did not meet the criteria more often than their own R = 3 batches";
  - if m = 4L: "R = 12 is not shown to be necessary".

**Why it is not gated.**
- The batches are nested in the libraries, so they are not an independent arm.
- A second verdict family recreates the reading table and the multiplicity that G35-B warned about.
- Any rule on the difference between k/L and m/4L needs a margin, which would be an invented number.

## 6. What I would change in the framing

- **Say plainly that "no" is the likely answer.** The arm-(i) pass sat exactly at four thresholds, so MIXED is the outcome to expect on structure alone. I still think the study is worth running. Unlike G41, every class changes the next decision: MIXED or CONSISTENT-FAIL closes the "more replicates" route with measured evidence in place of an unknown, and CONSISTENT-PASS is the only route to a Steven gate. If Steven would stop on anything short of CONSISTENT-PASS and already expects that, option A (STOP) is equally defensible. That is his call.
- **Add one free pooled reference (owner's call).** Score all 12L = 72 replicates as a single library, descriptive only, "met / not met". The stability question does not say whether Monte-Carlo noise is the limiting factor at all. If offset misses persist at R = 72, that points away from noise as sole cause; if they vanish, R = 12 is simply too small. It costs scoring only. The risk is that it reads as a new factor level, so it must carry "not a tested level; no reading".
- **No sequential or two-stage design.** Stopping at the first opposite pair would save minutes of compute, break the frozen "no early stopping" and blind-barrier rules, and discard the matrices that explain the result.
- **Do not pool G35-B.** Its targets differ and its library was seen before design. Its R = 12 library stays lineage only.

## 7. Compute and work caps (estimates)

EXPLORATORY arithmetic from G35-B `campaign_summary.disclosures`. Arm i took 869 s: about 1.7 s per build, 0.96 s per latent call, 0.11 s per transform, and 3.5 s of scoring in total. Linear scaling is unreliable.

| Quantity | Formula | L = 6, N = 20 |
|---|---|---:|
| Builds | 12L + N | 92 |
| Latent calls (30 d) | 300L + N | 1,820 |
| Report transforms | 7,500L + N | 45,020 |
| Gate loss evaluations | 625·L·N | 75,000 |
| Sub-library descriptive evaluations | 5 × 625·L·N | 375,000 |
| Pooled reference evaluations (if adopted) | 625·N | 12,500 |
| Pre-check builds | 92 + reserves | about 115–130 |

- **Wall time:** roughly 2 hours, order of magnitude, disclosed and never capped.
- **Bundle:** the arm-i directory was 83 MB and 7,837 files for 5,625 new tables, so expect roughly 0.5–0.8 GB and 60,000 or more files. Host disk check (≥ 5 GB) before launch.
- **Caps:** exact-equality dry-run caps as in G35-B.
- **Human and agent work, which is the real cost:**
  - a new standalone module importing the G35-B pure functions, because the G35-B harness hard-codes ten targets, seeds and caps;
  - two `Class: numerical` units, an independent review, a merge gate, a campaign gate and an exit audit;
  - the exit audit's stdlib recomputation is about six times G35-B arm i and should be budgeted.

## 8. Biggest risk and guard

**Risk: the three-class reading is over-read in either direction because the libraries share one target set and the gate sits at threshold.**
- A hard or easy target set can produce unanimity that looks like library stability.
- A single-target flip can produce MIXED that looks like gross instability.

**Guards in the predeclaration:**
- every reading carries "on these N shared targets" and "in L draws; not a rate, not an interval";
- N = 20, the per-target row counts, the two-block descriptive and the threshold margins are declared in advance so the reader can see which case occurred, while none of them can alter the class;
- the common-cause NO-READING rule;
- an explicit exclusion list: k-of-L cuts, re-partitioning, library or target subsetting, "best library", pooling as a gate, and any post-freeze change of L or N;
- the π table printed with the statement that π is unknown and not estimated.

**Secondary risk.** A CONSISTENT-PASS is treated as licence. Guard: carry G35-B A1 forward verbatim, so that reopening real-data fitting needs Steven's new gate and a new owner-ruled predeclaration.

## Where I expect other designers to differ

- **Reading rule.** Others may propose a k-of-L threshold (for example at least 5 of 6) or a pooled-rate criterion. I reject both as invented cuts. They may think unanimity is too strict.
- **L.** Expect 4–5 on cost grounds, or 8–10 on "measure the distribution" grounds. I chose 6 on the coin-flip unanimity argument.
- **N.** Some will keep N = 10 for literal continuity with arm (i), or use different target sets per library. I think the latter confounds the two sources of variation.
- **R = 3 reference.** Some will gate it as a co-primary control, or declare a difference rule. I keep it descriptive with two integer-triggered disclosure sentences.
- **Staging.** A two-stage design that stops at the first mixed pair is likely to be proposed. I exclude it.
- **Pooled R = 72 reference.** Probably unique to this proposal, and the owner may reasonably strike it as scope creep.
- **Whether to run at all.** A consultant could argue that STOP is better because MIXED is foreseeable. I rate the measured answer as worth about two hours of compute and one implementation cycle, and I flag that this is Steven's decision.
