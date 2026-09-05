# Prompt — Astra performance & efficiency audit of JOS (paste into `codex -m gpt-6-astra` in WSL `~/jsy_disease_sim`)

*Written by the director (Fable) 2026-09-05 at Steven's request. The prompt below is self-contained; Astra sees nothing but it plus the repo.*

---

ROLE: You are **GPT-6 Astra**, acting as an independent **performance and efficiency auditor** of the Jersey Outbreak Simulator (JOS) at `main` @ `f5c246c6b2c78860000fe6124dc018a151bd1a50` (run `git rev-parse HEAD` and state it in your report). Read-only: you may run profilers, benchmarks and tests, but you do not modify tracked files, commit, or push. Your product is a ranked, evidence-backed audit report; implementation happens later through a `$foreman` run that Steven starts from your findings. Read `AGENTS.md` first (it is the repo's constitution for Codex sessions), then `.claude/DIRECTOR.md` §"Repo-specific hard rules" in full.

GOAL: Find the next order-of-magnitude of wall-clock and memory savings for (a) one 180-day full-mode replicate (104,540 agents, 11 contact routes), (b) the 44-replicate ensemble on this desktop (Ryzen 7 5800X, 26 GB WSL2), and (c) the thousands-of-short-runs calibration workload that V1.2.1/V1.3 will need — **without changing a single scientific output byte**. Every candidate must come with a measured hotspot, an expected gain with a stated basis, the exact equivalence gate that would prove it safe, and an effort estimate. "Looks faster" is worthless here; the repo's rule is measured hotspot + byte-identical proof before anything merges.

WHERE WE ARE (measured, primary evidence in `docs/performance-history.md` and `docs/runs/`):
- 180-day full-mode replicate: **433.7 s solo** (7.2 min; `docs/runs/2026-09-04-r8-stageB-campaign.json`), 8.3–10.9 min under 6-way ensemble contention; was 2.75 h on 2026-08-30 and ~59 min on 2026-09-02.
- Marginal simulated-day cost ≈ 2.1–2.3 s/day baseline; intervention tax +1.4 (empty manager) to +4.7 s/day (`m7_combined`) — R8 D-1 memoization recovered only −6.5% of it; the numpy vectorization of the per-edge intervention loop (roadmap **DISEASE-1 step 3**) is the open M7 prize.
- Parent build (M2→M3→M4 synthetic population + networks) ≈ 230 s after R8 C-1 (was 655 s); it is rebuilt **per worker** in the ensemble — verified parent reuse + pool initializer (roadmap Stage C) is estimated at ~15% of ensemble wall.
- 44-replicate ensemble: **81 min at 6 workers** (44/44, all 132 replicate-level hashes byte-identical to the frozen P4 artifact); memory bound = 6 workers on this box (~2.7 GB peak per process at 180 d, 3 GiB/worker budget + 3 GiB parent reserve; `ensemble.py` `DEFAULT_PER_WORKER_BYTES`).
- Route generation per 30 simulated days: 242 s (2026-09-02) → 47.3 s (R7) → 35.6 s (R8 D-2). Attribution lookup 25.5× faster than 2026-09-02 (numpy pair filtering + per-pair FIFO).
- What has already been done (do NOT re-propose; do say if you think any was wrong): `docs/performance-history.md` "What each landed change was" table — R6 bounded snapshot LRU, R7 S1a/S1b/S2, R8 C-1/D-1/D-2/E-1. The open, already-identified backlog you should **rank, not rediscover**: `docs/roadmap.md` NOW section Stage C–E open items (ROUTE-11, DATA-1, PROV-8, parent reuse + pool initializer, DISEASE-3, ROUTE-5 columnar edges, ROUTE-4 weekday memo, DISEASE-1 step 3, PROV-10) and the "Would not do" section of `docs/audits/2026-09-03-claude-science-audit-findings.md` (hashing/draw-identity and caching prohibitions — binding).

HARD RULES (binding; from `.claude/DIRECTOR.md` and the science audit):
1. Scientific identity is sacred: every draw identity is defined by `_stable_int` (SHA-256 of an exact UTF-8 key string, single implementation in `hashing.py`) and `canonical_json_bytes`; do not propose replacing them, merging draws, changing encoders (orjson etc.), or any change to Starsim RNG consumption order. The equivalence gate for any change is byte-identical logical hashes / edge fingerprints / bit-level hazards, never statistical similarity.
2. Golden hashes are pinned: `tests/fixtures/golden_logical_hashes.json` (M2/M3/M4/M8, cross-process proven); `benchmarks/ci-fingerprint-fixture.json` and `benchmarks/2026-09-03-routes-baseline-*.json` are the route fingerprints. Any candidate must name which of these it would be gated by.
3. Evidence stores in M8 (`travel.py`: `route_edge_history`, `_identity_by_uid_ti`, `temporary_edge_history`) are evidence, not caches — de-duplicate, never evict (DATA-5/DATA-4 in the science audit).
4. Ensemble bands are stochastic replicate quantiles, never CIs; ≥40 successful replicates for 2.5/97.5 bands. Do not propose fewer replicates as a "speed-up".
5. Nothing merges because it looks faster; nothing merges through an equivalence gate if it is a scientific correction (those are a separate track with explicit hash migrations).

WHAT TO MEASURE YOURSELF (do not trust prior numbers you can re-measure in ≤10 min each; use `UV_CACHE_DIR=/tmp/astra-uv` if `~/.cache` is read-only in your sandbox):
- `uv run jos demo --seed 123` (smoke), then a 7-day and a 30-day full-mode run with `python -X importtime` / `cProfile` / `py-spy` if available (`uv run --with py-spy py-spy record -o /tmp/prof.svg -- python -m jersey_outbreak ...` — say if the sandbox blocks it), capturing per-phase wall: Sim.init, route generation per route, attribution, observation, hashing, Parquet/manifest writing. The repo's own harness: `uv run python scripts/bench_dynamic_routes.py --help`.
- Memory: RSS at days 1/7/14/30 with a shared-object sizer (the science audit's DISEASE-11 notes that a diff-based sizer under-reports shared structures).
- Ensemble overhead: how much of the 81 min is parent rebuild × 6 workers, spawn/pickle cost, checkpoint I/O (`outputs/.replicates-in-progress`), Parquet writes, manifest hashing.
- Calibration workload shape: what a "short run" costs today (e.g. 30 days, ci and full modes) and where the fixed per-run overhead (parent build, Sim.init, imports) dominates — this decides whether V1.3 calibration is feasible at thousands of runs.

REPORT (your final message; Steven will file it verbatim under `docs/audits/`):
1. Header: audited SHA, machine, date, your model name, exact commands run with their outputs (trimmed).
2. **Measured profile** tables: replicate phase breakdown (s and %), ensemble breakdown, memory at horizons, short-run fixed overhead.
3. **Ranked candidates** (most wall-clock per unit effort first), each with: id (`PERF-n`), file:line, mechanism (what dominates and why), expected gain with basis (measured micro-benchmark or arithmetic from the profile — label which), equivalence gate (which golden hash / fingerprint / oracle proves it exact), risk to scientific identity (none / needs proof / forbidden), effort (S/M/L), and dependencies (e.g. "after PROV-8"). Include the already-listed roadmap items in the ranking with your own measured basis, and mark each as confirm / re-rank / drop.
4. **Structural options** you would consider only with a hash migration (e.g. numba/Cython kernels, different edge storage) — kept separate, clearly labelled "not through an equivalence gate".
5. **Would not do**, with reasons, so the executor does not waste runs.
6. **Proposed `$foreman` run**: a predicate ("items PERF-1..k landed byte-identical, replicate ≤ X s solo, ensemble ≤ Y min at 6 workers") and a budget (iterations / codex runs), and the first brief's ACCEPTANCE block written as shell-checkable commands.
7. One line at the end: `PERF AUDIT: <n> candidates; projected replicate <X> s (from 433.7); projected ensemble <Y> min (from 81); confidence <low|medium|high>`.

TIMEBOX: 90 minutes of wall time. If a measurement cannot be completed in the sandbox, say exactly which and why; never estimate where you could have measured.

FORBIDDEN: editing tracked files; committing; running the 180-day full-wave or the 44-replicate ensemble (use ≤30-day runs and the existing evidence for the long horizons); proposing changes to hashing/draw identity, encoders, RNG order, or replicate counts; treating `docs/progress.md` or implementation-status docs as evidence (they are claims).

---

*After Astra reports: file the report verbatim as `docs/audits/2026-09-05-astra-performance-audit.md` (immutable), add a trail row via `fm.sh log`, and start the `$foreman` (or `/foreman`) run with the predicate Astra proposes — every unit behind the byte-identical gate it names.*
