# DEVTEAM.md — dev-delegate config for jsy_disease_sim (JOS)

## Gates (all must pass before handoff)
- `uv run --locked pytest -q` (~10 min; 235 tests at V1.1+carry-ins baseline)
- `uv run ruff check .` AND `uv run ruff format --check .` (CI's verify job runs both — a lint-clean branch still fails CI on formatting; caught 2026-09-02)
- Frontend, only when `frontend/` is touched: `cd frontend && npm run test && npm run build`

## Merge policy
- **Steven merges, SHA-first, always** (DIRECTOR.md hard rule; agent merges happen only on one-time explicit chat instruction). Deliverable = pushed branch + exact-SHA merge command.
- State-layer commits (`.claude/`, `docs/`) via `fm.sh log|sync` are the only agent writes to `main`.

## Protected branches / refs
- `main` · tags `jos-v1.0.0`, `jos-v1.1.0` (immutable) · all historical `codex/*` and `docs/*` branches (preserve, never squash/delete — handoff §7.6).

## No-touch paths
- `.claude/decisions.tsv` (append-only, via `fm.sh log` only — never by an implementation branch)
- `docs/audits/**` (immutable audit records) · `docs/handoff/**`
- `AGENTS.md` (Codex's constitution — orchestrator edits only, never in a job)
- Off-repo: `~/Documents/JOS_v1*` evidence dirs (immutable), `~/Documents/JOS_v1_2_*` (live run evidence)

## Repo quirks Codex must be told
- Scientific parameter choices come from written syntheses, never improvised (DIRECTOR §7.7); operational/diagnostic changes must not alter scientific trajectories — fixed-seed equivalence is the test.
- CLI error paths: plain `typer.echo(..., err=True)` + `typer.Exit(code)`; tests assert exit code + plain message, never rich/ANSI-rendered output (DIRECTOR lesson 2026-09-01).
- Contract surfaces are cross-checked: `ensemble_schemas.py` ↔ `ensemble_artifacts.py` ↔ `scientific_verification.py` must stay consistent when any default or diagnostic field changes.
- Machine context (2026-09-02): implementation and gates run in WSL Ubuntu on DESKTOP-KQTC6VL (`~/jsy_disease_sim`); codex sandboxed exec does not work on native Windows here (probe evidence in `docs/runs/2026-09-02-desktop-transfer-wsl.md`).

- Anything a job writes must land under `outputs/` (gitignored) or the job-owned directory — never elsewhere under the repo root. The job layer records `git status --porcelain` twice (submission + inside every artifact) and fails finalization on any mismatch, so a file created mid-run in the tree is a provenance defect, not a tidiness issue (CI-red 2026-09-04, `docs/runs/2026-09-04-ci-red-checkpoint-root-fix.md`). Corollary for gates: run the suite from a CLEAN tree at least once (a fresh clone in `/tmp`) — a dirty dev tree masks this whole class.
- The dev-delegate spec file must stay OUTSIDE the worktree (untracked files in the tree trip the format/clean-tree gates).

## Environment
- Passing commands into WSL: `wsl.exe -- bash -c "<inline>"` mangles quoting ($-vars, parens in the interop PATH, redirects) — write a script file, copy it via `/mnt/c/...`, `sed -i 's/\r$//'`, then `wsl.exe -- bash <script>`. From Git Bash, prefix `MSYS_NO_PATHCONV=1` so `/mnt/...` paths survive.
- Long-running launches inside WSL need `setsid nohup … &` (see dev-delegate LESSONS 2026-09-02).
- Worktrees: under the WSL home (`~/jos-<slug>-wt`), branched from `origin/main`. Never the primary checkout, never any existing worktree.
- If a full-scale P4 run is live (check `.claude/FRONTIER.md`), schedule full-gate pytest runs with care: WSL RAM headroom above the run is ~5 GB.
