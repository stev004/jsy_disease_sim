# RUN — R8 foreman run: CLOSED 2026-09-04 (digest below in trail; awaiting Steven on G13 + GitHub billing)

**Chain complete:** `codex/r8-stageA` @ `2528733c8fd1e95a59ecc07782da1ed39e9407dc` = Stage A (PROV-1, DISEASE-2, ROUTE-2, ROUTE-10) + C-0 golden hashes + C-1 M2 memoization (510→78 s, hash-identical) + D-1 intervention memoization (honest −6.5%) + D-2 exact route tranche (+1.30×) + E-1 persistence/worker-budget + terra-flagged namespace fix. All director-gated: suites 253–284 green per unit, fingerprints/hashes byte-identical at full scale everywhere applicable. Evidence: `docs/runs/2026-09-0{3,4}-r8-*`; terra trail audit filed (`2026-09-04-r8-trail-audit-terra.md`) — stale-state and evidence-location flags fixed; the 6-worker-bound caveat and CROSS-1 residue acknowledged in roadmap.md; the 78%→76% M2-share correction recorded.

## Blocked on Steven
1. **GitHub Actions billing** — CI cannot run on ANY branch ("recent account payments have failed or your spending limit needs to be increased" — GitHub Settings → Billing & plans). G13's default merge condition needs it.
2. **G13** (GATES.md) — merge the R8 chain tip.

## Remaining R8 items (open on roadmap.md, next run)
DISEASE-1 step 3 (numpy intervention vectorization — the M7 prize), ROUTE-5/4 columnar edges, PROV-2/3/5/6/7/9/10/11/12/13 cluster, ROUTE-11/DATA-1/DISEASE-3/PROV-8 + parent reuse, Stage-B residue (fine-grained timers, per-worker footprint), and the whole **scientific-corrections track** (DISEASE-4 fabricated zeros, CROSS-3 erratum, ROUTE-6/7 model decisions, DATA-7/8/9/10, DISEASE-10 — several need Steven's model-owner decisions).

## Cold-start
`docs/roadmap.md` NOW section → GATES.md (G13, G5) → decisions.tsv tail. V1.2 Track B iteration 3 (canonical epi tables) remains ready to run independently.
