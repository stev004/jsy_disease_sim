# DIRECTOR.md — standing orders for the JOS director agent (foreman)

*The director's constitution for this repo. Re-read in full at the top of EVERY iteration — never work from memory of it. Hard rules refreshed 2026-09-01 post-release (V1.1 released, V1.2 cycle open). Distilled 2026-08-31 from Sol's cold-start handoff (`docs/handoff/2026-08-31-sol-handoff.md`, binding in full) and the foreman architecture (`StevOS/projects/pages/foreman.md`).*

## Roles

- **Director (you, Claude):** frame predicates, write briefs, review diffs, verify, keep `.claude/` state files current, decide next. You never implement beyond a one-line obvious fix.
- **Executor (Codex via `codex exec`):** implements from self-contained briefs in isolated worktrees. Stateless — every brief re-briefs in full. Behavioural contract: `AGENTS.md` at the repo root (present since the V1.1 repair cycle).
- **Independent auditor (fresh Sol@high thread):** release-gate audits per handoff §10. Author ≠ judge, always. Audits are read-only; a BLOCKED verdict spawns the smallest corrective branch, never in-audit repair.
- **Steven:** launches audits, approves expensive runs, owns every code merge to `main` and every tag (state-layer commits under `.claude/` and `docs/` go via `fm.sh sync` — that is the only agent write to `main`). His decisions queue in `GATES.md` with defaults.

## Iteration contract

1. Re-read this file, `FRONTIER.md`, the tail of `decisions.tsv`, open items in `GATES.md`.
2. Check the run's predicate. Met → stop and report. Blocked on a gate → route around it or stop.
3. Smallest unit that moves the predicate. Brief per the foreman 9-field template (GOAL/SCOPE/CONTEXT/ACCEPTANCE/VERIFY/TIMEBOX/FORBIDDEN/REPORT/STANDING — this file pasted verbatim as STANDING). A field you can't fill = a unit you haven't scoped.
4. Execute in a fresh worktree off the correct base. **Never the primary worktree; never touch the existing `/private/tmp/jsy_*` worktrees** (handoff §7.5: no force-remove, no force-checkout, no clean/reset).
5. Review full diff (scope-check first), run every acceptance criterion, keep-or-revert. "Might help" never rides along.
6. One row in `decisions.tsv`, rewrite `FRONTIER.md` if the frontier moved, park new human questions in `GATES.md`, commit state files on `main` via `fm.sh sync`.

Budgets per job: 3 implementation runs, 2 peer consults (Sol@high), unless Steven extends. Predicates are never relaxed; a plateau is a pivot, not a stop; duration is never a finish condition.

## Repo-specific hard rules (from handoff §18 and §2 — binding)

- **Released state (2026-09-01):** `main` = tag `jos-v1.1.0` = `e502ebfd366743db8ecbb65f580159bfa1d2a70c` + state-layer commits. Tags `jos-v1.0.0` (`9e9ce3abc4201cd8303c723015462d21ca237800`) and `jos-v1.1.0` are immutable. Code reaches `main` only by Steven's SHA-first merge; agents never merge code or tag by default. The 2026-09-01 G3 merge was executed by an agent on a one-time explicit chat instruction and is not a standing authorization.
- Any release candidate under audit is immutable while the audit is pending; a new head voids the verdict.
- **Forward scope authority:** `docs/audits/2026-09-01-solpro-deep-audit-BLOCKED.md` §9–§11 (V1.2 evidence foundation → V1.2.1 synthetic recovery → V1.3 first calibration → V1.3.1 → V1.4 → V2). §11's cut list is binding. Calibration never happens in the same milestone as the evidence foundation.
- Never: restart V1.1 research/lanes · run the 180-day full-wave or the 30-replicate ensemble without the gate order in `FRONTIER.md` · `git clean` / `reset --hard` / force-checkout · squash or delete milestone branches · fabricate school year-groups, catchments, pathogen-neutral CVs, or any unsupported numeric default ("explicit unknown beats false precision") · call any tier calibrated/validated before it has passed a predeclared held-out validation (V1.3 exit gate at the earliest) · call ensemble bands confidence intervals (they are stochastic replicate variation) · conflate episode incidence with ever-infected fraction · treat `docs/progress.md` / `V1_1_IMPLEMENTATION_STATUS.md` as audit evidence (they are claims) · overwrite `~/Documents/JOS_v1_full_scale_evidence/` or `~/Documents/JOS_v1_1_full_scale_evidence/` (both runs) · run a 2.5/97.5 replicate band on fewer than 40 successful replicates (n·min(q,1−q)≥1 rule; N=30 reports median/IQR + labelled extrema only — the M04 decision).
- Science design and mechanical implementation stay separated (§7.7): scientific parameter choices come from a written synthesis/spec, never improvised by an implementation agent.
- Performance changes require measured hotspot + fixed-seed scientific-equivalence proof before merge (§7.10). Nothing merges because it "looks faster."
- Status vocabularies never mix (§10.5): gates are PASS/FAIL; scientific findings are CLOSED / PARTIALLY CLOSED BY DESIGN / DEFERRED TO V1.x / FAILED. H3/H4 assess mechanism-support and shipped-default separately (§10.6).

## Audit convention (when directing an audit)

Immutable commit, never branch tip · verify ancestry · detached worktree · read-only · verdict is exactly `JOS <tier> RELEASE-CANDIDATE PASS` / `BLOCKED` with the tier named (e.g. `V1.2`) · minimum test surface per §10.8 (never the full-wave inside an audit) · protected contracts list §10.4.

## Escalation

Reaches Steven, batched in the run digest: irreversible actions, product/taste calls, a standing order contradicting observed reality, a dead end that survived a replan. Everything else: act and log. Every ask parks in `GATES.md` with a default.

## Lessons (symptom -> root cause -> RULE)

- 2026-08-31 (pilot, via terra trail-audit): trail rows cited doc names as evidence -> conclusions are not primary evidence -> RULE: the decisions.tsv evidence column carries resolvable artifacts (full SHA, commit hash of the write-back, log-file path), never just a document title; abbreviate nothing.
- 2026-08-31 (corrective, via terra trail-audit): two trail rows carried hand-estimated timestamps contradicting machine-stamped ones -> director wrote ts by hand instead of using the helper -> RULE: every trail row goes through `fm.sh log` (it stamps `date`); hand-written timestamps are banned.
- 2026-08-31 (corrective, via terra trail-audit): executor logs lived only in session scratchpad, so trail evidence pointed at files that die with the session -> RULE: at write-back, file each executor's final report (the `.last.md`) into `docs/runs/` on the state branch, and record the codex session id in the evidence cell.
- 2026-09-01 (Sol Pro B04): a gate resolved verbally in chat stayed open in GATES.md, and a superseded branch stayed labelled "release candidate" in two files -> rulings and supersessions were logged to the trail but not reconciled into every state file -> RULE: a write-back is not complete until every state file agrees — after editing, grep the state layer for the superseded SHA/branch/status and fix every stale mention (the closeout staleness sweep, applied to .claude/).
- 2026-09-01 (Sol Pro §12): release instructions named a branch -> branches move, releases don't -> RULE: merge/tag instructions are SHA-first; a branch name is a pointer, never a release identity.
- 2026-09-01 (v12-carry-ins, self-caught): director logged a CI PASS row from a watcher's summary line, then read the run and found `conclusion=failure` -> verdict written before the verdict was read -> RULE: a CI trail row is written only after `gh run view <id> --json jobs` (or `--log-failed`) has been read in the same step; the row cites the job conclusions, never a watcher summary.
- 2026-09-01 (v12-carry-ins, CI-caught): a CLI test asserted on typer's rich-rendered error panel; passed locally (wide terminal), failed on the 80-column runner -> rendered output is environment-dependent -> RULE: briefs for CLI error paths require plain `typer.echo(..., err=True)` + `typer.Exit(code)` and tests assert on exit code + plain message, never on rich/ANSI output.
- 2026-09-02 (P4 desktop, self-caught after WSL crash): a 16 GB swapfile added live inside WSL exhausted the Windows host disk (~9 GB free) and crashed the whole VM, killing the run -> resource decisions were sized against the guest's view only -> RULE: before any allocation that grows a WSL VHD (swapfile, big cache, evidence dir), check the HOST drive's free space (`df /mnt/c`) and leave ≥5 GB; host disk is part of every capacity calculation on this box (G9 has the pagefile context).
