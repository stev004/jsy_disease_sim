# RUN — no autonomous run in flight (R6 foreman run CLOSED 2026-09-02)

The R6 performance/memory foreman run ended 2026-09-02 late evening with its predicate met: both optimization branches merged to `main` @ `a6fdc192e50633570d3edc5db5f7dbf241027548` (G10, Steven-instructed) and P4 launched. Digest + terra trail audit: decisions.tsv rows `run-start` → `r6-ci` + `g10-merge`; evidence in `docs/runs/2026-09-02-r6-*`.

## In flight (operational, not a foreman run): P4 full-scale ensemble, attempt 6
- Launched 2026-09-02 20:54Z on DESKTOP-KQTC6VL/WSL2, `main` @ `a6fdc19`: 44 seeds (101–144), `--mode full`, 180 days, `--workers 7`, pid 8595, log `~/Documents/JOS_v1_2_full_scale_evidence/p4-ensemble-launch-20260902T205417Z.log`, pid file `p4-ensemble.pid`. Projected ~6 h (done early 2026-09-03).
- Watch: `~/p4_tripwire.sh` (OOM / silent-serialization / thrash / host-disk<3GB / completion), polled by the session monitor while a session lives; otherwise run it manually.
- On completion: verify ≥40 successful replicates and `execution_mode=process_pool_spawn` / `actual_workers=7` in the artifact diagnostics; summary bands are stochastic replicate quantiles (never CIs); file the run report in `docs/runs/`; flip FRONTIER to V1.2 evidence foundation; refresh `docs/desktop-setup.md` §2 memory notes (1.8 GB figure is wrong; see FRONTIER memory model).
- Kill hygiene if ever needed: `pkill -f 'jos ensemble run'` AND `pkill -f 'multiprocessing.spawn'` (children outlive the parent pattern — bitten 2026-09-02).

## Cold-start pointer
Read `.claude/FRONTIER.md` (P4 IN FLIGHT block) → `.claude/GATES.md` (open: G5, G9) → decisions.tsv tail.
