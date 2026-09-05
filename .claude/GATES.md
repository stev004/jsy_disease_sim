# GATES — decisions parked on Steven

*One entry per open human decision: question · options · default on no answer. Agents route work around open gates instead of stalling on them. Resolved gates move to the bottom with the ruling.*

## Open

### G18 — Merge the Astra performance tranche 2 (PERF-1 + PERF-2 + PERF-3) into `main`
- **Question:** merge `perf/integration-tranche2` @ `ac04bbb50aaea1070a4fbd5d645062e7470c4f3c` (= main + no-ff merges of PERF-3 `7b64629cba686ca21b0cd5015c564c18748f5273`, PERF-2 `2a70915a91862f63f112d001b97bce661d4a90fc`, PERF-1 `7fe7df0fb2e9e2f4510555c4e555c31b981c13dd`)? Every unit is byte-identical on its gate (full-mode M4 hash `49464e77…`, M3 hash `b7d2fb34…`, seed-101 30-day latent/outcome hashes `bbca6028…`/`b8433f0d…`), **all preconditions read green (trail rows `perf1-ci`, `tranche2-integration-ci`, `tranche2-review-PASS`, 2026-09-05 evening):** integration CI run 33991981411 verify+frontend success; perf1 CI 33991825337 success; perf3 33989793406, perf2 33990091712 success; independent Sol review `docs/audits/2026-09-05-tranche2-perf-review-sol-PASS.md` = PASS (two MINOR notes, no protected-output path). Gains: Sim.init 48 s → 1.07 s per replicate; M3 build 147 s → 5 s; M4 hash transient allocation 482 MiB → 4 MiB.
- **Command (SHA-first, after CI on `ac04bbb` is read green):** `git -C ~/jsy_disease_sim fetch origin && git -C ~/jsy_disease_sim merge --no-ff ac04bbb50aaea1070a4fbd5d645062e7470c4f3c -m "G18: merge perf/integration-tranche2 @ ac04bbb (PERF-1/2/3)" && git -C ~/jsy_disease_sim push`
- **Option B (extended candidate) — QUALIFIED:** `perf/integration-tranche2b` @ `0dec469f83ee936b9b68e979e7a927807d7654e0` = the same plus ROUTE-5 phase 1 (columnar snapshots; exact on all fingerprints; ~8× smaller snapshot memory) + ROUTE-4 (workplace_team weekday memo, 5.7×) + the director's merge resolution. **CI run 33998934843 verify+frontend success; Sol review 2 = PASS (`docs/audits/2026-09-06-tranche2b-perf-review-sol-PASS.md`, three MINOR notes, none touching a protected output).** Command then: `git -C ~/jsy_disease_sim merge --no-ff 0dec469f83ee936b9b68e979e7a927807d7654e0 -m "G18: merge perf/integration-tranche2b @ 0dec469 (PERF-1/2/3 + ROUTE-5 phase 1 + ROUTE-4)" && git -C ~/jsy_disease_sim push`.
- **Default:** merge option B (`0dec469`) — both its preconditions are met; option A (`ac04bbb`) remains a valid smaller fallback. Agent does not merge without an explicit instruction in chat.

### G21 — Second run-1 extension: corrective 6 (one dictionary row) + audit 7
- **Question:** audit 6 at `79cbf41` FAILs on exactly one cell pair — `housing_controls:overcrowded_households` from `census_2021_overcrowding_csv` leaves `population_universe`/`denominator` unknown although the frozen source is titled "Proportion of overcrowded households by tenure" with tenure rows and an `All households` total. Everything else passes (66/66 rows, all hashes, all audit-1..5 findings closed). The G20 rule said a second extension needs Steven's explicit word. Authorise corrective 6 (brief prepared: `~/jos-corr6-brief.md`, ~15 min, luna@high) + audit 7?
- **Default:** wait for Steven (no launch). To release: say "run corrective 6 and audit 7"; the director then executes `launch-corr6.sh` → `audit7-launch.sh` (scratchpad pattern, same as 5/6).

### G20 — Run-1 budget extension (exit gate): one more corrective + one more audit
- **Question:** the self-set run-1 budget (4 iterations) is spent with audit 5 = FAIL on three narrow dictionary cells (vaccination fraction-vs-percent encoding; per-100,000 rate denominator; population-flow definition on report page 5). The director extended the run by exactly one corrective unit (corr5) and one audit (audit 6) on Steven's standing instruction "make as much progress and parallelism as possible". Stop the extension?
- **Default:** proceed (corr5 + audit 6 only; a second extension would need Steven's explicit word). Trail row `exit-audit-5-FAIL` records the decision.

### G19 — Merge the V1.2 exit-gate corrective (after an exit-gate PASS; audits 4/5/6 = FAIL at `71e408c` / `5877e42` / `79cbf41`; one cell pair left — see G21)
- **Question:** merge `fix/v12-exit-gate-corrective-3` @ `79cbf41eef9d2f0323da908fe57fea9b8860b503` (the SHA audit 6 judges; includes the gate-doc revisions) into `main`? Command after a filed PASS: `git -C ~/jsy_disease_sim merge --no-ff 79cbf41eef9d2f0323da908fe57fea9b8860b503 -m "G19: merge fix/v12-exit-gate-corrective-3 @ 79cbf41 (V1.2 exit gate PASS)" && git -C ~/jsy_disease_sim push`
- **Default:** merge only on a filed `V1.2 EXIT GATE: PASS`; on FAIL the run spawns corrective 4 instead.


### G5 — Branch cleanup
- **Question:** 20+ historical branches (now all pushed to origin). Prune any?
- **Default:** preserve all (handoff §7.6). Revisit only after V1.1 is secure.

## Resolved

### G17 — Merge the robustness bundle — RESOLVED 2026-09-05 (Steven, in chat: "merge G16 and G17")
Executed by the agent on the explicit one-time instruction: SHA-first `--no-ff` of `c062d20afba94e03964216c62ca99e9d90d0825d` → merge `f5c246c6b2c78860000fe6124dc018a151bd1a50` (after G16). Branch CI 33934808135 green. Pre-push smoke on the merged tree: 56 targeted tests (data pipeline, sources, population, job liveness, M9.1) + ruff + format + `jos demo` + rebuild byte-identical + `check-attr text: unset`. Pushed; **main CI run 33974942892 on `f5c246c`: verify+frontend success**.

### G16 — Merge the V1.2 evidence-foundation chain — RESOLVED 2026-09-05 (Steven, in chat: "merge G16 and G17")
Executed by the agent on the explicit one-time instruction: SHA-first `--no-ff` of `446545377a49150b6dcb83f1575af023838178f7` → merge `133a0990affa2e1443a809c33ef8be10cae6392b`. Branch CI 33936072022 green. Partial evidence-foundation merge: the V1.2 exit gate is NOT satisfied (three FAIL audits in `docs/audits/`); the corrective unit now branches from `main`.

### G15 — Merge V1.2 Track B iteration 3 — RESOLVED 2026-09-04 (Steven, in chat: "merge G14 and G15")
Executed by the agent on the explicit one-time instruction (not a standing authorization): SHA-first `--no-ff` of `de3a32d72d66fef5ed6291cbfc7b7ac3a090e4ab` → merge `32e9b954d84237b63efa4f3e68b6c335d56f52b0`, after G14. Branch CI 33915625764 green (verify+frontend); merged code tree byte-identical to the branch tree (0 differing files under src/tests/data); pre-push smoke: 62/63 targeted tests + ruff + format + `jos demo` — the one smoke failure was a stale scratch namespace under the primary checkout's root `.replicates-in-progress/` left by the director's 19:22 pre-fix reproduction (removed; test passes; CI runs on a clean checkout). Pushed; main CI on the merge SHA logged in the trail when read.

### G14 — Merge the main-CI fix — RESOLVED 2026-09-04 (Steven, in chat: "merge G14 and G15")
Executed by the agent on the explicit one-time instruction: SHA-first `--no-ff` of `d873a80bc9027f2473a4620f1ca828f01c118c85` → merge `91073af9d2278fa60ee049530fabac50fa34d005` (branch CI 33910950203 green). Root cause and evidence: `docs/runs/2026-09-04-ci-red-checkpoint-root-fix.md`.

### G13 — Merge the R8 chain — RESOLVED 2026-09-04 (Steven, in chat: "merge it all and try again, then /closeout")
Merged on local evidence per the stated fallback (CI remains billing-dead; annotation re-confirmed post-merge): SHA-first `--no-ff` of `2528733c8fd1e95a59ecc07782da1ed39e9407dc` -> merge `43008ff`; pre-push smoke 72 targeted tests + ruff + demo green; pushed. Validation ensemble launched same hour (44 seeds, 6 workers, ensemble-id p4-validation-r8, log p4v-ensemble-launch-20260904T131139Z.log). GitHub billing fix still outstanding (Steven; CI confirms main once restored).

### G11 + G12 — RESOLVED 2026-09-03 (Steven, in chat: "merge them")
Both executed same hour by the agent on the explicit one-time instruction: G11 snapshots merge `5cdc780` (five frozen Jersey COVID sources now immutable on main), G12 R7-chain merge `10d448c` (route generation 5.11x, attribution 25.5x, 2.26 s/simulated-day, all full-scale hashes byte-identical), plus mechanical rename fix `df41196` (respiratory.py mypy nit outside CI's pinned list). Post-merge smoke green; main @ `df41196` pushed. Steven's follow-on sequence REPLACES the G12 default validation rerun: Claude Science audit (bundle `~/Documents/jos-claude-science-audit-2026-09-03.zip` delivered) -> implement findings -> then launch the new ensemble run.

### G9 — Desktop C: drive critically full — RESOLVED/CLOSED 2026-09-03 (Steven executed)
Pagefile shrunk 34 GB → fixed 16 GiB via the registry route (`PagingFiles` in Session Manager\Memory Management — the CIM and wmic routes both failed with "Value out of range") + reboot. Verified after reboot: C: free 9 GB → **31 GB**. Downloads/Docker were never touched (not authorized, not needed).

### G10 — Merge the two R6-cycle branches, then launch P4 — RESOLVED 2026-09-02 (Steven, in chat: "merge them then /closeout")
Executed by agent on the explicit one-time instruction (not a standing authorization): SHA-first `--no-ff` merges of `codex/r6-snapshot-cache-bound` @ `79ef7b2aa07d435ffbfc2d04435b9a291fe24f95` (merge `9f51c8b`) and `fix/ensemble-pool-loudness` @ `3617a91529606295a5386437078b30560eb0e081` (merge `a6fdc192e50633570d3edc5db5f7dbf241027548`), both branch CIs green beforehand (33663392224, 33630012570). Pre-push smoke on the merged tree in WSL: 35 targeted tests + ruff + format + `jos demo` all green. Pushed; main CI pending at resolution time (logged when read). P4 launched same evening at `--workers 7` (20:54Z, pid 8595). The terra auditor reservation (partial benchmark protocol; concurrent benches → wall figure noisy) was presented in the gate and accepted by the default.

### G8 — M04: replicate count and machine for the P4 full-scale ensemble — RESOLVED 2026-09-02, then AMENDED same day (Steven, in chat: "option 2. lets optimse then run after")
**Amendment:** P4 execution is DEFERRED until after the R6 performance/memory optimization cycle. Measured reality on the desktop (26 GB WSL): per-worker regen peak ~9 GB caps the box at 2 workers ≈ 44–48 h wall — too long. Optimize first (R6 brief + the 2026-09-02 memory findings), then run the ensemble at the reduced cost. The ≥40-replicate substance of the ruling stands for that future run.
*(original resolution below)*
Ruling = the default: ≥40 successful replicates on the desktop (DESKTOP-KQTC6VL, WSL2 mode per the 2026-09-02 transfer), `--workers 12`, launched after the desktop smoke/gate passed (it did — see `docs/runs/2026-09-02-desktop-transfer-wsl.md`). Bands labelled "stochastic replicate quantile", never confidence intervals. Launched as 44 seeds (101–144) so ≥40 successes survive replicate failures. Operational deviation 2026-09-02: `--workers 12` OOM-killed a worker in WSL (26 GB cap; dmesg 06:27) and the code silently fell back to sequential (~4–5 day ETA), so the run was killed and relaunched at `--workers 8` (~15–18 h). Replicate count and machine — the substance of the ruling — unchanged.

### G7 — Merge V1.2 carry-ins into `main` — RESOLVED 2026-09-01 (Steven, in chat: "merge all"): executed by agent, `--no-ff` merge of exact SHA `9711b8e3937b3ff18aec86523ed4769ff78cfd4c` → merge commit `9a2d984f265aca2e8edfcc10de6bb45b2519f140`; smoke (6 v12 tests + demo) green; pushed. Second one-time agent-executed merge on explicit instruction (after G3); still not a standing authorization.

### G4 — Doc commits on frozen `main` — RESOLVED 2026-09-01 (Steven: "fold it into main"): `docs/frontier` merged into `main` (`--no-ff`) after the V1.1 release; state layer now lives on `main`, sessions open in the repo.

### G6 — V1.1 release-repair run — RESOLVED 2026-09-01 (Steven, in chat: "run the repair and keep going"): launched same day
Run completed 2026-09-01: re-audit PASS at `e502ebf...`. *(Closed late — caught by the terra trail audit, same failure class as G2/B04.)*

### G2 — V1.1 full-scale baseline — RESOLVED 2026-08-31 (Steven, in chat: "keep it going"): approved, Mac
Run completed 2026-08-31 (run-20260831T145052Z, verification PASS, comparison filed 2026-09-01). *Bookkeeping note: this gate was left open in this file until 2026-09-01 despite the chat ruling — flagged by Sol Pro B04; lesson encoded in DIRECTOR.md.*

### G1 — Launch the independent V1.1 audit — RESOLVED 2026-08-31 (Steven, in chat): launch now
Overrode the after-EMA default. Audit launched same day via foreman pilot run (Sol@high, read-only, detached worktree at the candidate).

### G3 — V1.1 merge + tag — RESOLVED 2026-09-01 (Steven, in chat: "merge it for me"): executed by agent per exact SHA-first procedure
ff to e502ebf verified via rev-parse, smoke green, tag jos-v1.1.0 pushed. Agent-executed merge was a one-time explicit instruction, not a standing authorization - future merges remain Steven-gated by default.
