<!-- Filed by the director (Claude Opus 5.5, desktop session) on 2026-11-19 under G40 (Steven, chat: "Yes, run audit"). The auditor was a fresh Claude Opus 5.5 @ high subagent dispatched from the Claude desktop app (Agent tool), NOT `claude -p` in WSL as RUN.md's recipe named; the brief gave paths only, no director conclusions. Auditor tokens: 234,898; 34 tool uses; 706 s. Report body below is the auditor's, verbatim except that the script appendix is replaced by a pointer to the filed scripts and outputs (docs/runs/2026-11-19-g40-exit-audit/). -->

# JOS G35-B campaign exit audit (§12 step 9)

| Item | Value |
|---|---|
| Auditor | Claude Opus 5.5 @ high (fresh instance; not the implementer, which was gpt-6.1-sol, and not the step-7 reviewer, which was gpt-6-astra) |
| Date | 2026-11-19 |
| Bundle | `/home/steven/jos-g35b-campaign-20261022T234254Z` (read-only, 13,927 files + `SHA256SUMS`) |
| `SHA256SUMS` sha256 | `e6649a4b32289ad32cec7862ed79ea75a5123d0231178bebf0db78f0fd54c8fc` |
| Code SHA | `0c9c3711b4e1be3fa90e9ef7f1e8e883dbdb48d8` (`campaign_summary.source.git_head`; campaign clone HEAD; `worktree_clean: true`) |
| Predeclaration hash verified | **yes**. `git show 3972190:docs/research/v1_3/2026-10-22-g35b-predeclaration.md \| sha256sum` = `2e8358abd9e275a5cf04a58b4ad76313c10964f2da06d46cd0f8a7190733216e`, byte-identical to `frozen_inputs/` |
| Method | Pure-stdlib recomputation from the raw `target_tables/` and `candidate_tables/` JSON and `serosurvey_samples.json`. No project imports were used in the gate path. No simulation was run and no seed was touched. |

## Lineage block (§1; clarification 1; clarification 2 Item 3(c))

| Item | Value |
|---|---|
| Phase-0 verdict / audit | `phase0_verdict: FAIL` · `docs/audits/2026-09-24-phase0-exit-audit-sol-FAIL.md` |
| Phase-0 bundle `SHA256SUMS` digest | `72cd9a568598530923e08ce20b013d60eb7a3b26553b87c31685ad623f3faa80` |
| Phase-0 predeclaration SHA-256 | `ef67fe49903c3984ca98679eb0470878bc25523baca3bc23a63e4ae7d983a104` |
| Phase-0b verdict / audit | `phase0b_verdict: FAIL` · `docs/audits/2026-09-26-phase0b-exit-audit-sol-FAIL.md` |
| Phase-0b bundle `SHA256SUMS` digest | `a319c5557ffa77c56baebb8341b5fc2e1432f367bdb9d0b34169aa079659032a` |
| Phase-0b predeclaration SHA-256 | `ec8df64630dd50c83b0866a096fba4980453c34232d18114129587274f257451` |
| Phase-0b failing predicates | P0-1 predicates 5, 6, 8. Offset selections `4, 4, 0, 2, 0` against truth 2; boundary 4/5; joint 1/5 |
| Ridge diagnostic SHA-256 (binding, committed bytes, clarification 1) | `8cf4c76612434cbd90c5de4ca9dfd1326422b94a72bd4a63ccff71e95f34908a` (CRLF alias `de13913b…`, non-binding) |
| G34-B memo | `docs/research/v1_3/2026-09-29-successor-offset-design-memo-DRAFT.md`; Option 2 withdrawn |
| **Step-7 reviewer** | **gpt-6-astra @ high, substituted under clarification 2 Item 3.** The reason was that Opus 5.5 was unavailable: the claude CLI was not authenticated on Windows or WSL (trail rows `g37-mirror-pass`, `g37-review-BLOCKED`, `g37-rereview-PASS`). No Opus attempt was made, so no filtered attempt exists and no filtered-attempt token count applies. The first review was BLOCKED (F1–F4), the corrective commit `0c68982` followed, and the bounded re-review PASSED before step 8. |
| Exit-auditor disclosure | This auditor is the same model family as the run's director (Claude Opus 5.5). It is independent of the implementer and of the step-7 reviewer, as clarification 2 requires. |

The `campaign_summary.json` lineage block carries every §1 item verbatim, including the clarification-1 binding ridge digest and `ridge_digest_source`.

## 1. Integrity checks

| Check | Result |
|---|---|
| `sha256sum -c SHA256SUMS` | **ALL OK** (13,927 entries) |
| Files on disk vs listed | 13,927 vs 13,927; no unlisted or missing file |
| Writable files or directories in the bundle | none (all `r--`/`r-x`) |
| `frozen_inputs/` vs committed git bytes | All 7 equal: predeclaration at `3972190`; owner ruling, clarification 1, probe record, pre-check record and config at `0c9c371`; ridge diagnostic at `3972190`. Each matches `campaign_summary.frozen_input_sha256`. |
| Owner ruling sha256 | `f84738a9…d99643` = frozen §16 value |
| Probe record / pre-check record | `03ac0906…46a3d7` / `9d15beb0…614f5` = frozen §4.2 / §8 values |
| `source_and_config_sha256` (90 files) vs `git show 0c9c371:<path>` | 0 mismatches; every tracked `.py/.yaml/.json` under `src/jersey_outbreak` and `configs` is covered |
| Campaign clone | HEAD `0c9c371…`, clean after the run; exit file `0` |
| Number of campaigns | One output directory matching `jos-g35b-campaign-*`. One `CAMPAIGN_START`/`CAMPAIGN_END` pair (rc=0). The launch script refuses to start if an exit marker exists. Trail rows `g39-campaign-launch` and `g39-campaign-done` are the only campaign rows. |
| Retries / reruns | Latent-call ledger: B 85 distinct of 85, i 225 of 225, ii 85 of 85, iii 0. No duplicated (seed, beta, offset) call. No replicate file is duplicated. |
| Director's filed copies (`docs/runs/2026-10-23-g35b-campaign-*`) | `SHA256SUMS.txt` is byte-identical after CRLF normalisation. `campaign_summary` and the four `recovery_evaluation` copies are JSON-identical; they differ only by a trailing newline. |

## 2. Seed ledger and replacement rule (§8)

- **Ledger:** 61 rows. B has 10 targets + 3 A; i has 10 + 12 (A, B′, C′, D′); ii has 10 + 3 A; iii has 10 + 3 A.
- **Process seeds:** exactly `82001–82010` and `83001–83012`. No reserve was used (`82011–82015` and `83013–83017` are absent).
- **Pairing:** observation seeds are `92001–92010` (`v13-g35b-target`) and `93001–93012` (`v13-g35b-fit`). Serosurvey seeds are `94001–94010` (`v13-g35b-sero-target`) and `95001–95003` (`v13-g35b-sero-fit`). Every pairing is in order, with 0 violations. Every candidate file and target provenance record carries `run_config.seed == process_seed`.
- **Disjointness:** no overlap with the Phase 0 sets (`42/52/43/53`), the Phase 0b sets (`62/72/63/73`) or the retired probe seeds (`81001–81006`, `91001–91003`).
- **Replacement:** none. This matches the frozen "Every primary seed built, so the replacement rule was not triggered."
- **M2/M3/M4 lineage:** every target and candidate record equals the frozen §8 hash table. Fallback flags are TRUE only on `82003` (M2) and `82007` (M3), as frozen. The per-arm descriptive counts read targets 2, candidates 0.
- **Builds:** 22 parent directories are retained (B 13, i 9, ii 0, iii 0).

## 3. Fixed scenario and calendars (predicate 9 inputs)

All 13,125 candidate files and all 40 target provenance records were checked:
- `ci` mode, start `2025-01-06`;
- duration 30 for B, i and iii, and **49** for ii;
- 10 imports at `start + offset` (the truth file reads `2025-01-08`), import rate 0, initial seeds 0;
- all 11 route multipliers 1.0, symptomatic probability 0.6, constant latent 2 d and infectious 5 d, waning off;
- detection delay 0, reporting delay 2, four-day tail, weekday factors 1.0;
- cell beta and detection values equal the observation and run configs.

There were 0 violations. The calendars are 34 dates for B, i and iii, and 53 dates for ii (`2025-01-06` to `2025-02-27` = H + 4).

Byte-sharing holds as declared:
- the target tables are identical between B and i, and between B and iii;
- batch-A candidate tables (and `table_sha256`) are identical between B and i, and between B and iii.

Arm-(ii) report counts on dates ≤ 2025-02-04 equal B's for 10 of 10 targets and 1,875 of 1,875 candidate replicates. This independently corroborates the frozen prefix-identity result.

## 4. Per-arm recomputation (§6, §7.1)

How each piece was recomputed:
- **Loss:** recomputed for all 625 cells × 10 targets × 4 arms (25,000 gate evaluations) from the raw tables, using the frozen formula with R = 3 or 12 and T = 34 or 53.
- **Arm (iii):** adds (z(k_i) − z̄_θ)² inside the bracket, with z the Anscombe binomial transform, n = 400, and k taken from the stored everInfected flags.
- **Tie and identification:** τ = 1e‑12·max(1, L_min). A dimension is identified when it has a unique profile minimum within τ and a relative gap ≥ 0.05, using max(P_min, 1e‑12).
- **Errors, tolerances and bias:** computed in exact `Decimal` on the declared grid strings. Every selected value mapped onto exactly one declared grid string.
- **Integer gates:** hits·5 ≥ 40; joint·5 ≥ 30; boundary·5 ≤ 10.

Agreement with the stored surfaces:
- **B, i, ii:** bit-identical (max |Δ| = 0.0).
- **iii:** max |Δ| = 1.8e‑15. The implementation sums L^rep + S/(2T), which is the frozen U4 acceptance form; I summed (Σ+S)/(2T). Every selection and identification flag agrees. The smallest decision margin in arm iii is 1.6e‑2 relative (best vs second cell) and 6.4e‑3 (|gap − 0.05|).

Smallest margins in the other arms:

| Arm | Best vs second cell (relative) | \|gap − 0.05\| | Location |
|---|---|---|---|
| B | 2.7e‑3 | 8.8e‑4 | 82001 symptomatic gap 0.04912, not identified; the gate is unaffected either way |
| i | 9.2e‑3 | 5.7e‑3 | — |
| ii | 2.5e‑3 | 1.9e‑3 | — |

No decision is float-fragile.

### Gate predicates

Frozen thresholds (§7.1):
- P1: "All 10 target runs, all 625 candidate cells and all R replicates per cell complete without replacement."
- P2: "realizes all ten inoculation acquisitions, at least one local secondary infection, reports in both channels, and at least three nonzero combined-report dates."
- P3: "Observation chronology and latent-incidence conservation pass."
- P4: "No target has a numerically tied global minimum."
- P5: "Every dimension is identified and within tolerance for ≥ 8/10 targets" (hits·5 ≥ 4·10).
- P6: "≥ 6/10 targets are identified and within tolerance jointly" (joint·5 ≥ 3·10).
- P7: "Every dimension's absolute ten-target mean bias is ≤ its limit (exact decimal)."
- P8: "No dimension is selected at an outermost grid value for more than 2/10 targets" (boundary·5 ≤ 1·10).
- P9: "Seeds, namespaces, grid, objective, dates, fixed parameters, H (arm ii), serosurvey design (arm iii), read-back and blind provenance match this declaration."
- P10: "Measured work equals the §9 caps."

Dimension order in the tables below: beta / offset / symptomatic / asymptomatic.

| Predicate | **B** recomputed | **i** recomputed | **ii** recomputed | **iii** recomputed |
|---|---|---|---|---|
| P1 complete | 625 cells × 3 reps, 10 targets: PASS | 625 × 12, 10: PASS | 625 × 3, 10: PASS | 625 × 3, 10, 75+10 samples: PASS |
| P2 viability | acquisitions 10 each; secondaries 1999–2152; sym/asym > 0; nonzero dates 26–29: PASS | same targets as B: PASS | acquisitions 10; secondaries 2257–2321; nonzero dates 41–45: PASS | same as B: PASS |
| P3 chronology / conservation | recorded TRUE ×10: PASS | PASS | PASS | PASS |
| P4 no tie | 0 ties: PASS | 0: PASS | 0: PASS | 0: PASS |
| P5 hits | 10 / **7** / 9 / 10: **FAIL** | 10 / **8** / **8** / 10: PASS (at threshold) | 10 / **5** / 9 / 9: **FAIL** | 9 / **7** / 9 / 9: **FAIL** |
| P6 joint | 7: PASS | **6**: PASS (at threshold) | **5**: **FAIL** | 7: PASS |
| P7 mean bias (limits 0.01 / 0.5 / 0.0625 / 0.0375) | 0.002 / 0.1 / −0.0125 / −0.0075: PASS | 0.00 / −0.2 / 0.00 / 0.00: PASS | 0.002 / 0.4 / −0.0125 / −0.0075: PASS | 0.002 / 0.1 / −0.0125 / −0.0075: PASS |
| P8 boundary | 0 / **3** / 0 / 0: **FAIL** | 0 / **2** / 0 / 0: PASS (at threshold) | 0 / 2 / 0 / 0: PASS | 0 / **3** / 0 / 0: **FAIL** |
| P9 provenance | §2–3 checks, read-back §5: PASS | PASS | PASS (H = 49, T = 53) | PASS (serosurvey design and A5 ordering, §6) |
| P10 caps | 625 / 85 / 1885 / 0 / 13: PASS | 625 / 225 / 5625 / 0 / 9: PASS | 625 / 85 / 1885 / 0 / 0: PASS | 625 / 0 / 0 / 85 / 0: PASS |
| **Gate** | **FAIL** (P5, P8) | **PASS** | **FAIL** (P5, P6) | **FAIL** (P5, P8) |
| Matches bundle claim? | yes, all 10 predicates and the status | yes | yes | yes |

How P2 and P3 were checked: the report-channel half of P2 was recomputed from the target tables, and the recorded report sums equal the table sums. Inoculation acquisitions, secondary infections and the P3 flags come from the retained truth diagnostics; see Observation O4. Totals are 22 builds, 395 latent calls, 9,395 transforms and 85 serosurvey samples, all matching §9.

The per-target recovery CSVs (40 rows per arm) match my recomputation in every row: estimate, signed error, identified, within-tolerance, boundary flag and joint.

### Per-target selected cells

Each cell is (beta, offset, symptomatic, asymptomatic). "id" lists the identified dimensions in order beta/offset/symptomatic/asymptomatic (I = identified, - = not). A `*` marks a joint hit.

| Target | B | i | ii | iii |
|---|---|---|---|---|
| 82001 | 0.10, **0**, 0.625, 0.175 (id I--I) | 0.08, **0**, .75, .25 (IIII) | 0.10, 3, 0.625, 0.175 (I--I) | 0.10, **0**, 0.625, 0.175 (----) |
| 82002 | truth* | truth (II-I) | truth (I-II) | truth* |
| 82003 | truth* | truth* | truth* | truth* |
| 82004 | truth* | truth (II-I) | truth* | truth* |
| 82005 | truth* | truth* | truth (I-I-) | truth* |
| 82006 | off **4** | off 3* | off **4** | off **4** |
| 82007 | truth* | truth* | truth* | truth* |
| 82008 | off 1* | off **0** (I-II) | off 1* | off 1* |
| 82009 | off **4** | off 3* | off **4** | off **4** |
| 82010 | truth* | truth* | truth* | truth* |

## 5. Read-back and blind boundary

- Every blind record's sha256 and `estimate_hash` equal `blind_readback_hashes.json` (B 10, i 60, ii 10, iii 10; 0 failures). Gate estimate hashes equal the CSV `estimate_hash` column.
- By file modification time, the last blind record of any arm was written 3.0 s before the first recovery CSV of any arm. This is consistent with the global "all generation before any truth join" barrier. Modification times are supporting evidence, not proof of order.
- Arm-(i) batch-A descriptive estimate hashes equal B's gate estimate hashes.

## 6. Serosurvey (arm iii)

- For all 85 samples, the sampled IDs equal the first 400 residents of the retained `residents.parquet` (3,000 agents) ordered by the A5 SHA-256 string. The survey date is `2025-02-04` and n = 400.
- For every sample, k equals the count of stored flags.
- Each candidate seed has one sample shared across all 25 (beta, offset) runs, so the common-random-numbers rule holds.
- The design record states sensitivity "1", specificity "1", lag 0, survey day 29.
- The z values recompute exactly.
- The serosurvey term's share of L at each selected cell recomputes exactly (0.00017–0.111).

## 7. Descriptives (§7.2): reported, and not used as gates

Recomputing every gate without any descriptive input reproduces every gate, so no descriptive feeds a verdict.

- **(a)** Offset hits and boundary counts per arm are in the table above. Per-target profiles are retained in every blind record.
- **(b) Arm i:**
  - re-profiled offsets per batch A/B′/C′/D′, A∪B′ and all 12 recompute identically for all 10 targets;
  - the four-batch agreement count is **0/10**, recomputed equal;
  - the range and median of the four batch objectives (6,250 tuples) recompute with max |Δ| = 0;
  - every entry is labelled `stochastic_replicate_variation`.
- **(c) Arm ii:**
  - prefix identity is identical for 10 of 10 targets (both hash pairs equal; corroborated from the tables in §3);
  - latent peak days are 21–26, all ≤ H − 8 = 41, so the manipulation check reads "factor delivered for 10/10 targets".
- **(d) Arm iii:**
  - ever-infected fraction is 0.670–0.721 for every target, so `n_criterion_premise_met` is TRUE ×10;
  - k/n − F ranges from −0.020 to +0.031.

## 8. Readings and labels (§7.4)

- **Status phrase:** `Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B FAIL, i PASS, ii FAIL, iii FAIL`. This matches A9 exactly. No reading appears inside the phrase.
- **i** (B FAIL, X PASS): the frozen reading plus the multiplicity paragraph, verbatim. It is labelled "Screening result only." No best factor is declared. This is correct.
- **ii and iii** (FAIL, FAIL): the frozen reading including "Arms (ii)/(iii): that factor did not break the ridge at this level." This is correct.
- **Overall:** one factor arm passed, so it is reported individually with the caveat. This is correct.
- "confidence", "interval", "credible" and "significan" do not appear anywhere in `campaign_summary.json` or the descriptives files. Spreads are labelled stochastic replicate variation.
- No FAIL was reclassified.

## 9. Discrepancies, defects and departures

**No discrepancy and no defect under the frozen text or the §12 VOID rule.** Observations (none of them gate, and none departs from a frozen obligation):

| # | Severity | Observation | Evidence |
|---|---|---|---|
| O1 | Low (disclosure hygiene) | Per-arm disclosure files and the summary disagree on arm wall time. iii reads 0.815 s in `arm_iii/g35b_iii_disclosures.json` against 1.283 s in `campaign_summary.disclosures.iii.arm_wall_time_seconds`; ii reads 382.70 against 383.45. The B and i disclosure files have no `arm_wall_time_seconds` key at all. §4.2 requires the totals in `campaign_summary.json.disclosures`, and they are there. | the files named |
| O2 | Info | Readings keep the literal template word "Factor X". The arm key identifies the factor. The text is the frozen §7.4 wording verbatim. | `campaign_summary.readings` |
| O3 | Info | Clarification 2 is not in `frozen_inputs/`, and `campaign_summary.lineage` has no step-7 reviewer line. Clarification 2 Item 3(c) assigns that disclosure to the trail row, the review report and the exit audit's lineage block. The first two carry it, and this report supplies the third. The review report says "Prior-attempt token count was not supplied." No attempt existed (unavailability, not a filter), so the count is N/A rather than missing. | trail rows 399–404; `docs/audits/2026-10-22-g37-implementation-review-astra-BLOCKED.md:4` |
| O4 | Info (audit limitation) | Latent `transmission_events` and `daily_epidemic` are not retained in the bundle, and §10 does not require them. The auditor therefore could not recompute the following from latent truth, and checked them only for internal consistency: P2 acquisitions and secondary infections, P3 flags, everInfected flags, arm-ii peak days and transmission prefix hashes. The report-side P2 fields, arm-ii report prefix identity, serosurvey sampling order and k all were recomputed independently. | §§3, 6 |
| O5 | Info (interpretation) | Arm (i) PASS rests on four counts exactly at their inclusive thresholds: offset hits 8/10, symptomatic hits 8/10, joint 6/10, offset boundary 2/10. Batch-offset agreement is 0/10 (descriptive). The frozen text applies the thresholds inclusively, so the PASS is correct. It is a screening result only and needs Steven's decision and a new owner-ruled fresh-seed confirmatory predeclaration before any reliance. | §4, §7(b) |

## 10. Exit-audit verdict lines (§10)

```
G35-B ARM B RECOVERY GATE: FAIL
G35-B ARM i RECOVERY GATE: PASS
  Reading: "Factor X, at the declared level, coincided with four-dimensional recovery in this one synthetic campaign." Screening result only. Multiplicity: three arms raise the chance that at least one passes when no factor matters; any later decision relying on it requires Steven's decision and a new owner-ruled, fresh-seed confirmatory predeclaration.
G35-B ARM ii RECOVERY GATE: FAIL
  Reading: "Factor X alone, at the declared level, did not produce recovery." That factor did not break the ridge at this level.
G35-B ARM iii RECOVERY GATE: FAIL
  Reading: "Factor X alone, at the declared level, did not produce recovery." That factor did not break the ridge at this level.
Overall: one factor arm (i) PASS, reported individually with the multiplicity caveat; no "best factor" is declared.
Status: Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B FAIL, i PASS, ii FAIL, iii FAIL
```

No outcome authorizes real-data fitting (G34 stays STOPPED). No outcome changes the Phase-0 or Phase-0b verdict, and none supports any claim of calibration, validation or coverage.

## Appendix: scripts run

The auditor's scripts and their outputs are filed verbatim (copied from WSL `/tmp/g40audit/`, with a `.txt` suffix added) under `docs/runs/2026-11-19-g40-exit-audit/`:
- `s01_integrity.sh`, `s02_tree.sh`: SHA256SUMS check, listed vs on-disk, permissions, tree;
- `s03_recompute.py`: gate recomputation (pure stdlib) with `recompute_results.json`;
- `s04_provenance.py`: seed ledger, truth diagnostics, lineage, frozen inputs vs git, serosurvey order, readings text;
- `s05_descriptives.py`: arm-i batch re-profiling, four-batch agreement, arm-iii shares, decision margins;
- `s06_runs.py`: latent-call ledger duplicates and seed keys;
- `s07_fixed.py`: fixed scenario parameters;
- `s08_readback.py`: blind read-back and write order.

Each `sNN_out.txt` is that script's output. Nothing was written into the bundle.

`JOS G35-B CAMPAIGN EXIT AUDIT: CONFIRMED`
