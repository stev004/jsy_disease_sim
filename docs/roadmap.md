# JOS consolidated roadmap

*The single living backlog. Consolidates the Sol Pro deep audit (2026-09-01, §9–11 = long-term authority), the R7 performance consult (2026-09-03), and the Claude Science audit (2026-09-03, 51 findings — detail in `docs/audits/2026-09-03-claude-science-audit-findings.md` + `.csv`). Updated at every session closeout (`.claude/CLOSEOUT.md` owns the cadence). FRONTIER.md points at the current item; this file holds everything else. Done items move to the log at the bottom with their evidence link.*

**Status legend:** ☐ open · ◐ in flight · ☑ done (with date + evidence)

---

## NOW — R8 cycle: Claude Science audit, Stages A→E (Steven, 2026-09-03: "foreman a to e")

### Stage A — restore the gates (nothing else merges first)
- ☑ **PROV-1** (2026-09-03/04, codex/r8-stageA @ a9c76f0) Excise `workers`/memory fields from the M6 ensemble logical hash (schema 1.4→1.5); unit test: hash invariant under execution fields.
- ☑ **DISEASE-2** (2026-09-03/04, codex/r8-stageA @ a9c76f0) Re-point the attribution oracle at the shipped lookup (extract to pure function); mutation-proof with the three named mutants; extend oracle past candidate construction.
- ☑ **ROUTE-2** (2026-09-03/04, codex/r8-stageA @ a9c76f0) Harness fixes: all 11 routes, Starsim `p1/p2/beta/dur` fingerprints, declared route list in meta, uninstrumented timing, date-major cache mode, term-boundary window, committed ci fixture.
- ☑ **ROUTE-10** (2026-09-03/04, codex/r8-stageA @ a9c76f0) One `_stable_int` in `hashing.py` (4 copies today), pinned-digest test, ≥10⁶-key cross-process equality proof before consolidation.

### Stage B — re-measure on the production configuration, then re-rank
- ☑ **CROSS-1/CROSS-2 campaign** (2026-09-04, `docs/runs/2026-09-04-r8-stageB-campaign.json`: 180d = 433.7 s confirmed; M2 = 78% of parent build; intervention tax +1.4 to +4.7 s/day; memory flat ceiling, 6-7 workers fit): 7/14/30/60-day + one real 180-day replicate with per-phase timers (M2/M3/M4 decomposed, Sim.init, routes, attribution, post-processing, hashing, Parquet, observation); 30-day runs under `m7_community_indoor` and `m7_combined` (the missing intervention measurement); DISEASE-11 memory campaign (shared-object sizer at 7 horizons). Deliverable: three-parameter cost model; confirm/refute the 7.5-min projection.
- ◐ **DATA-6** (codex in flight) Golden logical hashes for M2/M3/M4/M8 committed + asserted in CI, cross-process/cross-machine baseline (hard blocker on all generator changes).

### Stage C — the overhead block (~33% of ensemble wall)
- ☐ **ROUTE-11** Diagnostics switch for run/ensemble paths (hash-neutral by construction) + incremental M4 hash.
- ☐ **DATA-2** M2 rebalancing loop-invariant hoist (sandbox 1,429× on one comprehension; instrument first).
- ☐ **DATA-1** M3 secondary-job loop (3 exact transformations; numpy-pinned equivalence check first).
- ☐ **PROV-8** One parent build implementation (4 today), one scenario normalisation — prerequisite for reuse.
- ☐ Verified M2/M3 parent reuse + pool initializer (R7 lead 4, now ~15% of ensemble wall).
- ☐ **DISEASE-3** Grid built once not twice; memory is the real prize (~0.6–1.1 GB parent budget).

### Stage D — kernel remainder, in measured order
- ☐ **DISEASE-1** (1)+(2) memoise run-constant adherence predicate + hoist str()/skip no-op copies (10.2× sandbox; the only item touching the production M7 path). (3) numpy arrays gated separately, after.
- ☐ **ROUTE-1** prefix-hoisted `_stable_int` (~271 ms/day) — after ROUTE-10.
- ☐ **ROUTE-3** ordered merge replaces re-dedup (~157 ms/day).
- ☐ **ROUTE-7** two-line dead-sort deletion (~41 ms/day; the persistence *question* is in Scientific corrections).
- ☐ **ROUTE-9** community preamble pre-index (~73 ms/day).
- ☐ **DISEASE-7** `np.isin` size dispatch (removes the 8.9× step at ~58 successes).
- ☐ **ROUTE-5** columnar edges (largest structural item; three-phase gate; ROUTE-4 weekday memo after it, bus excluded).

### Stage E — robustness (parallel, independent)
- ☐ **DISEASE-6** per-replicate result persistence + resume (broken pool must not lose completed replicates).
- ☐ **DISEASE-5** honest worker bound (parent reserve, affinity-based CPU count, horizon-matched per-worker bytes; corrected bound 4–5).
- ☐ **PROV-2/PROV-9/PROV-7** job-layer liveness lock, publication ordering, submit ordering.
- ☐ **PROV-10** scheduler idle polling + heartbeat authorship; **ROUTE-12** school-calendar horizon validation at config time; **PROV-6** verification_archive portable paths; **PROV-12** M8 verifier id binding; **PROV-3** API dataset label; **PROV-5** one git-provenance helper; **PROV-11** metric type registry; **PROV-13** self-test hash volatility.

### Scientific corrections — own release track, explicit hash migrations (never through an equivalence gate)
- ☐ **DISEASE-4** incidence bands: fabricated zeros beyond metric horizon (120 rows in frozen P4 summary) — versioned fix + schema bump.
- ☐ **CROSS-3** P4 report erratum: 184-date grid stated as "180 points"; re-read tail-date cell semantics from the frozen artifact first.
- ☐ **ROUTE-6** `activity_cv` inert on 2 of 4 declared routes — model-owner decision + diagnostics correction.
- ☐ **ROUTE-7 (science half)** is workplace weekly refresh intended? `persistence_days` never reaches Starsim (`dur=1` always) — decide, then either implement or remove the metadata.
- ☐ **DATA-10** resident arrival-test detections silently dropped from high-risk strata — fix + M8 diagnostics schema bump.
- ☐ **DATA-7** travel arrival totals stamped `observed` unconditionally — tie to canonical M1 table, fail closed.
- ☐ **DATA-8/DATA-9** calibration: degenerate held-out gate, identifiability profile that doesn't re-minimize, delay recovery at beta=0 undisclosed — restate + real 2-D profile.
- ☐ **DISEASE-10** observation agreement diagnostic tri-state + corrected declared RNG key inputs.

---

## NEXT — V1.2 evidence + observation foundation (Track B, foreman run open)
- ☑ Iteration 1: Jersey data-source inventory, 27/28 verified (2026-09-03, `docs/research/v1_2/2026-09-03-jersey-data-source-inventory.md`).
- ☑ Iteration 2a: five priority sources frozen + registered, merged to main (G11, `5cdc780`).
- ☐ Iteration 3: canonical epidemiology tables (daily cases/tests, weekly vaccination by age band, serosurvey parameters) extending `data_pipeline.py` conventions; explicit suppression semantics (`<5` stays `<5`); sentinel handling for the daily CSV's blank/-1 cells and the current CSV's undated cumulative row.
- ☐ Remaining freezes: JHU first-wave series, census denominators refresh into epi tables, respiratory surveillance PDFs (rolling URL — snapshot each season).
- ☐ Exit gate: cold-start auditor reproduces every calibration input from frozen snapshots. Calibration itself excluded.

## THEN — after R8 + V1.2 land
- ☐ **New full-scale ensemble** on the final code (Steven's sequence: audit → implement → run): 44 seeds; replicate hashes must match the frozen P4 artifact *if code is still hash-equivalent*, else it is the first artifact of the corrected-science lineage (DISEASE-4 changes the summary hash by design — decide which side of that line the run sits on before launching).
- ☐ Update `docs/desktop-setup.md` + FRONTIER memory model from Stage-B measurements.

## LONG-TERM (authority: Sol Pro audit §9–§11; §11 cut list binding)
- ☐ **V1.2.1** — any R8 leftovers; performance polish for thousands-of-short-runs calibration workloads.
- ☐ **V1.3** — first named-pathogen Jersey calibration: COVID era, predeclared holdouts, serology-constrained (the 2020 serosurvey anchors first-wave ascertainment); NPI timing reconstructed by hand (OWID has no Jersey stringency data). Constraint discovered 2026-09-03: island-level only — parish-level cases were never published, so sub-island spatial calibration has no data.
- ☐ **V1.3.1 → V1.4 → V2** per Sol Pro §10.
- ☐ Parked: G5 branch cleanup (default: preserve all).

---

## Done log (newest first, with evidence)
- ☑ 2026-09-03 **R7 chain merged** (G12, `10d448c`): routes 5.11×, attribution 25.5×, 2.26 s/day marginal, hashes byte-identical — `docs/runs/2026-09-03-r7-chain-hash-gate.json`.
- ☑ 2026-09-03 **Five Jersey COVID sources frozen** (G11, `5cdc780`) — `docs/research/v1_2/…inventory.md`.
- ☑ 2026-09-03 **Claude Science audit** received + filed — `docs/audits/2026-09-03-claude-science-audit-findings.md`.
- ☑ 2026-09-03 **P4 44-replicate ensemble** complete, M04 closed — `docs/runs/2026-09-03-p4-full-scale-ensemble-report.md` (CROSS-3 erratum pending).
- ☑ 2026-09-02 **R6 bounded snapshot cache** merged (G10) — memory growth −87.8%.
- ☑ 2026-09-02 **Desktop transfer** (WSL2 mode) — `docs/runs/2026-09-02-desktop-transfer-wsl.md`.
- ☑ 2026-09-01 **V1.1 released** (`jos-v1.1.0`), V1.2 carry-ins merged (G7).
