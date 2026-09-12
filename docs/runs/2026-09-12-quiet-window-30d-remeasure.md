# 2026-09-12 — quiet-window 30-day full-mode remeasure on `main` (owed since G18)

**Director:** Fable (foreman run `v121-run5`). **Tree:** `main` state head `0bfc3c690475f3ad80b0aa25a1c239ce8bf2bbd5`, code baseline `6e9b0e4a301c3821adab0a52528357657894456e` (G18+G19+G22+G23 merged). **Box:** WSL2 Ubuntu on DESKTOP-KQTC6VL, 16 CPUs, 27,055 MB, freshly booted (`up 0 min`, load 0.14) — no executor or other run active during the three repeats.

## Command (three sequential repeats, identical)

```
uv run jos outbreak run --mode full --seed 101 --duration-days 30 \
  --reuse-from ~/jos-astra-perf-evidence-20260905/full --output-dir ~/jos-remeasure-20260912/runN
```
Parents reused (verified reuse, PERF-9 path): M2 `jos-population-m2-full-seed-101-cd24533b8dd9`, M3 `jos-structure-m3-full-seed-101-bfc68acfaf9d` (Astra's cached full-mode seed-101 parents). Timing by `/usr/bin/time -f "wall=%e s maxrss=%M KB"` wrapping the whole CLI process (interpreter start, M4 network build, 30 simulated days, artifact write).

| repeat | wall (s) | max RSS (KB) | user (s) | sys (s) | exit |
|---|---|---|---|---|---|
| 1 (cold cache) | 68.99 | 2,430,824 | 66.77 | 3.62 | 0 |
| 2 | 61.92 | 1,521,696 | 62.40 | 1.72 | 0 |
| 3 | 59.24 | 1,531,288 | 59.78 | 1.64 | 0 |

Window: 2026-09-12T16:15:35Z → 16:18:46Z. Raw files: WSL `~/jos-remeasure-20260912/{meta.txt,timeN.txt,runN.log,runN/}`.

## Equivalence

All three runs produced artifact `jos-outbreak-m5-full-seed-101-bbca602849da` with `logical_content_hash = bbca602849da80aa04bd2c3bb770d3d5c4486f007d0e14666df4c5087a6e8c81` — byte-equal to the seed-101 full-mode 30-day latent hash pinned in the PERF-1 brief and proof (`docs/runs/2026-09-05-perf1-proof.json`), i.e. the merged perf chain is still exact on this fingerprint.

## Reading

- Previous figures for the same command: Astra unloaded prototype 53.9 s (PERF-1 only, 2026-09-05); PERF-1 executor 73.2 s on a loaded box. Quiet-window steady state on the fully merged tree: **~60 s** (59–62 s warm; 69 s first run includes cold page cache). The cold/warm gap and the 2.4 GB vs 1.5 GB RSS gap on run 1 are the parent-artifact page-cache effect, not code.
- This does not replace the authorised validation run (solo 180-day ≤390 s; 44-replicate ensemble ≤75 min at six workers) — that stays gated on Steven (RUN.md next actions). It is the owed 30-day measurement only.
- Not a benchmark of any single unit; it is the whole-CLI wall on the merged tree, comparable to the 73.2 s / 53.9 s numbers only in the sense that all three time the same command.
