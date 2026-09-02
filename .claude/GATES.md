# GATES — decisions parked on Steven

*One entry per open human decision: question · options · default on no answer. Agents route work around open gates instead of stalling on them. Resolved gates move to the bottom with the ruling.*

## Open

### G10 — Merge the two R6-cycle branches, then launch P4 at 7 workers
- **Question:** merge (SHA-first, `--no-ff`) ① `codex/r6-snapshot-cache-bound` @ `79ef7b2aa07d435ffbfc2d04435b9a291fe24f95` (bounded snapshot cache: −87.8% memory growth, hashes byte-identical, 238 tests, evidence `docs/runs/2026-09-02-r6-bench-{before,after}.json`) and ② `fix/ensemble-pool-loudness` @ `3617a91529606295a5386437078b30560eb0e081` (loud pool degradation + abort on broken pool, CI run 33630012570 green)? Then the agent launches P4: 44 seeds, `--mode full`, 180 days, `--workers 7`, projected ~6 h wall at ~3.3 GB/worker.
- **Default:** merge both once their CI is green, then launch. Bands labelled stochastic replicate quantiles, never confidence intervals; ≥40 successes required (G8 substance unchanged).
- **Auditor reservation (terra, 2026-09-02):** the R6 benchmark protocol's full letter (14-day leg, interleaved repeated trials, broader exact comparisons) was not run — adoption rests on hash identity at 7 d + 30 d, the recompute-soundness test, the full suite, and the unambiguous memory result (cache 257→33 entries). The before/after benches ran concurrently on the same host, so the +4.2% wall figure carries contention noise (memory and hashes are per-process and unaffected). If you want the full protocol before merging, say so and it runs (~2 h); the default accepts the evidence as-is.

### G9 — Desktop C: drive is critically full (root cause of the 2026-09-02 WSL crash)
- **Question:** C: is 466 GB with ~9 GB free. The Windows pagefile is 34 GB (system-managed). Approve shrinking it to a fixed 16 GB (elevated PowerShell + reboot, AFTER P4 completes)? And may the agent delete anything from Downloads (751 MB) or Docker data (3.7 GB, would lose local images/containers)?
- **Default:** after P4 completes, Steven shrinks the pagefile to 16 GB and reboots; agent deletes nothing from Downloads/Docker without an explicit yes. Until then the WSL swap stays capped at 6 GB and the tripwire alerts below 3 GB host free.

### G5 — Branch cleanup
- **Question:** 20+ historical branches (now all pushed to origin). Prune any?
- **Default:** preserve all (handoff §7.6). Revisit only after V1.1 is secure.

## Resolved

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
