# GATES — decisions parked on Steven

*One entry per open human decision: question · options · default on no answer. Agents route work around open gates instead of stalling on them. Resolved gates move to the bottom with the ruling.*

## Open

### G5 — Branch cleanup
- **Question:** 20+ historical branches (now all pushed to origin). Prune any?
- **Default:** preserve all (handoff §7.6). Revisit only after V1.1 is secure.

## Resolved

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
