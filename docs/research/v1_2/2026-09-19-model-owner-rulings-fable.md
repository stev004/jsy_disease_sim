# Model-owner rulings — scientific corrections (2026-09-19)

**Authority:** Steven, chat 2026-09-19: "make decisions for me on model-owner science rulings as idk the best thing to do." Ruled by Fable (director) under that delegation; recorded here as the written synthesis required by handoff §7.7 (scientific choices come from a written spec, never improvised by an implementation agent). Any of these can be reversed by Steven's word; none is merged without his SHA-first instruction.

**Governing principles applied:** explicit unknown beats false precision · mechanism support and default activation are assessed separately (§10.6) · scientific corrections are their own release track with explicit hash migrations, never smuggled through an equivalence gate · no dynamics change without a written scientific basis (that is V1.3 calibration territory).

---

## Ruling 1 — DISEASE-4: fabricated zeros in incidence bands

**Finding:** ensemble incidence-band summaries emit `0` beyond a replicate's metric horizon (120 such rows in the frozen P4 summary) — a fabricated value where the truth is "not computed".

**Ruling: FIX — never emit a fabricated zero.** Rows beyond a metric's horizon become explicitly missing (null/absent with a `not_computed` status, whichever fits the existing suppression vocabulary from the V1.2 observation work — the same family as `not_reported`). This is a versioned change to the M6 summary schema (manifest schema bump), a declared hash migration: summary/manifest hashes change by design; replicate-level latent/M4/observation hashes must be untouched. The frozen P4 artifacts are immutable and stay as they are; the fix applies to all future ensembles, and the run report for the first post-fix ensemble notes the band difference against frozen evidence. Rationale: this is the hard rule "explicit unknown beats false precision" applied literally; a zero incidence claim the model never computed is the exact failure class the project prohibits.

## Ruling 2 — ROUTE-6: `activity_cv` inert on 2 of 4 declared routes

**Ruling: make the declaration truthful; do not extend the mechanism.** Route metadata and diagnostics must declare `activity_cv` only on the routes where it demonstrably reaches the transmission path; on the two inert routes the declaration is removed (or marked `declared_inactive` if the schema needs the key). Wiring `activity_cv` into the two inert routes is REFUSED for now: it would change transmission dynamics with no written scientific basis or calibration to justify a value — that is inventing a parameter's reach, the same failure class as inventing the parameter. Whether those routes *should* carry activity heterogeneity is parked as a V1.3 calibration-design question (docs/roadmap.md LONG-TERM), to be decided against data, not defaults. Mechanism-support vs shipped-default separation (§10.6) applies: the mechanism exists; its activation surface shrinks to what is real.

## Ruling 3 — ROUTE-7 (science half): workplace `persistence_days` never reaches Starsim

**Finding:** workplace route metadata carries `persistence_days`, but `dur=1` is always passed — edges refresh daily; the weekly-persistence claim is dead metadata.

**Ruling: daily refresh is the shipped behaviour; remove the inert metadata.** `persistence_days` is deleted from the route metadata (or, if removal breaks a frozen schema, set to the truthful value `1` with a note), and route documentation states daily regeneration explicitly. Implementing weekly persistence now is REFUSED: it changes contact-network dynamics and there is no evidence-backed reason to prefer 7-day persistence over the daily-refresh behaviour every audited artifact was produced under. If V1.3 calibration shows contact-duration structure matters for the COVID fit, persistence returns as a designed, calibrated mechanism — not as a resurrected default. Rationale: truthful metadata over silent implication; the released lineage keeps the dynamics it was audited with.

## Ruling 4 — iteration-3 subgroup cuts (`covid19_vaccination_pcr_insights_pdf`)

**Ruling: freeze and canonicalise age-band cuts only** (dose × age band, matching the existing `population_denominators_by_age_band` bands so every subgroup rate has a real denominator). Occupational, parish, or other cuts without frozen denominators are excluded and listed as known gaps — a rate whose denominator we would have to invent fails the false-precision rule. `TestsTotalNegativeTests` stays excluded: all 917 cells are SharePoint `float;#` render corruption; a reverse-engineered decode rule would be invented data. The exclusion is documented in the measure dictionary, not silently dropped.

## Explicitly NOT ruled here

CROSS-3 (P4 report erratum), DATA-7/8/9/10, DISEASE-10 stay open on the roadmap's scientific-corrections list — they were not in Steven's delegation and several are mechanical rather than model-owner calls.

## Implementation route

Rulings 1–3 are delegated as one implementation unit (isolated worktree, off code baseline `08960b8`), reviewed against these rulings; ruling 4 folds into the iteration-3 follow-up when that work opens. The corrections branch merges only on Steven's SHA-first instruction, and only after the 2026-09-19 validation run has its verdict filed (so the exact-lineage measurement is not contaminated).
