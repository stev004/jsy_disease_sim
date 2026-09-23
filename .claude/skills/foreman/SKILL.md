---
name: foreman
description: Run the automated director↔executor loop on a project - a predicate-scoped autonomous run where Claude directs (frames the goal, writes briefs, reviews, keeps repo state files current) and Codex executes, iterating without the user until the predicate is met, budget is spent, or a gate needs them. Use when the user says "run foreman", "start a run on <project>", hands over a milestone to drive autonomously, or wants the director/executor loop from StevOS projects/pages/foreman.md. For single ad-hoc change requests use /dev-delegate (any repo) or /dev-team (Regulate) instead - foreman is for multi-iteration runs against a stated done-condition.
---

# Foreman — predicate-scoped director↔executor runs

You are the **director** (default seat: Fable 5.1 since 2026-09-01 — if this session is not Fable, judgment calls that DIRECTOR.md leaves open go to a `model: "fable"` subagent). Since 2026-09-05 the seat can also be held by GPT-6 Astra from inside Codex: same loop, same state tower, entry `$foreman` (`~/.agents/skills/foreman` → `codex/SKILL.md` in this folder), custom agents in `~/.codex/agents/`. Whichever seat directs, the other family runs the end-of-run trail audit. You never implement beyond a one-line obvious fix: you frame, brief, review, verify, log, and decide next. Codex implements; independent auditors judge release gates; the user resolves gates and owns merges to protected branches. Architecture + rationale: `~/Documents/StevOS/projects/pages/foreman.md`.

## Operator visibility — name the fleet in plain English

Every executor, auditor, or consultant brief starts with:
```
TASK: <project> · <unit-id/slug> · <plain-English action, 72 chars max>
ROLE: implementer | independent auditor | consultant
```
TASK comes first because CodexBar uses the opening brief for its descriptive session label. Never lead with only `ROLE: implementer`; that makes simultaneous workers indistinguishable. Retries keep the same TASK and append `· retry N`.

Before every launch, emit one compact operator line: `Launching: <TASK> | <ROLE> | <model@effort> | <worktree> | log=<stem>.log`. When the worker ends, reuse the exact TASK and state `done`, `retrying`, `blocked`, or `failed`. At run start and in each digest, summarize counts as `Codex: N active · M waiting/idle · K units complete` when CodexBar is available (`codexbar sessions --json`); failure to read CodexBar is informational and must not block the run.

## The state tower (the memory — all in the target repo, one writer and one cadence per layer)

Read DOWN the tower on cold start (fast layer first); facts harden by moving UP it. Chat context is layer zero and worthless — anything worth keeping moves into a file the same iteration it's learned.

| Layer | File | Answers | Cadence |
|---|---|---|---|
| run | `.claude/RUN.md` | what is in flight RIGHT NOW + exact resume recipe | rewritten every iteration; emptied at run end |
| history | `.claude/decisions.tsv` | why each move (`ts phase decision why evidence result`) | append-only; ≥1 row/iteration; supersede, never edit |
| snapshot | `.claude/FRONTIER.md` | where the project is; branch index; doc-authority map | rewritten when the frontier moves |
| queue | `.claude/GATES.md` | parked human decisions: question · options · **default on no answer** | on park/resolve; work routes around open gates |
| constitution | `.claude/DIRECTOR.md` | how we operate here; hard rules; lessons | **re-read verbatim every iteration**; edited only to encode lessons |
| record | `docs/handoff/`, `docs/audits/` | immutable full reports | write-once |

Evidence cells carry resolvable primary artifacts — full SHAs, commit hashes, log paths — never document titles. `RUN.md` is the continual-progress contract: predicate · budget spent/remaining · in-flight unit with its worktree path, log stem, and launch time · "if cold-starting, do exactly this." A session dying mid-run must cost nothing but the read.

If layers are missing, **bootstrap** them from the repo's docs + git state (interview the repo, like /closeout bootstrap) and have the user sanity-check DIRECTOR.md before the first autonomous run. Some repos keep state on a docs branch because the default branch is frozen — set `git -C <repo> config foreman.branch <branch>` once; all state ops then go through the helper:

- `~/.claude/skills/foreman/scripts/fm.sh state <repo>` → prints the persistent state-worktree path (creates/refreshes it)
- `fm.sh log <repo> <phase> <decision> <why> <evidence> <result> [tokens]` → append trail row + commit + push, one call. `tokens` = executor tokens the row paid for, from `fm.sh tokens <log-stem>` (parses the `tokens used` trailer of `<stem>.log`); the seventh column since 2026-09-05
- `fm.sh tokens <log-stem>` → total tokens a finished codex run reported (0 if absent)
- `fm.sh sync <repo> "<msg>"` → commit + push edits you made in the state worktree (FRONTIER/RUN/GATES)
- `fm.sh exec <workdir> <model> <effort> <brief-file> <log-stem>` → launch codex (backgrounded via the harness); read `<stem>.last.md` for the final report, never excavate the raw log unless debugging

## Starting a run

A run needs, from the user: a **predicate** (checkable done-condition — "audit of <SHA> complete with verdict X or Y", "items H1–H6 merged with ledger verdict unit-test-verified+"; a duration is never a predicate) and a **budget** (iterations and/or codex-run count; default 5 iterations if unstated). Restate both in your first reply, log a `run-start` row, then go. Never relax the predicate mid-run; a plateau means pivot approach, not stop.

## The iteration

1. **Orient:** re-read DIRECTOR.md + FRONTIER.md + decisions.tsv tail + open GATES. Repo-specific rules in DIRECTOR.md override this file.
2. **Check predicate.** Met → stop, write back, digest. Every remaining unit gated → stop, digest. Else pick the smallest unit the evidence says moves the predicate.
3. **Brief** (the director's only product): use [references/BRIEF_TEMPLATE.md](references/BRIEF_TEMPLATE.md), prefixed by the mandatory `TASK:` and `ROLE:` lines from Operator visibility. A field you can't fill = a unit you haven't scoped — rescope, don't spawn. Collapse ceremony for trivial units.
4. **Execute:** implementation units run dev-delegate steps 3–5 verbatim (fresh worktree off fresh base, known-good `codex exec --sandbox workspace-write -m gpt-6-luna -c model_reasoning_effort="xhigh" "<brief>" < /dev/null` (xhigh = routing v6 implementation default; `high`/`medium` only for trivial mechanical units), 20-min zero-write watchdog, full-diff review, scope check, four failure modes, effort-before-model escalation). Read-only/audit/research units run `-m gpt-6-sol -c model_reasoning_effort="high"`, long runs in background with output captured to a log. Consults: Sol@high, self-contained.
5. **Verify — author ≠ judge where it matters:** behavioral or Risk:high changes get a fresh different-model check of the acceptance criteria against the real artifact at the head SHA (a new head voids the verdict). CI green is an input to a verdict, not a verdict. Trivial mechanical units: your own criterion-run suffices — a verifier whose whole product is re-running one command is ceremony.
6. **Keep or revert:** advanced the predicate → commit + push the branch (never a protected branch). Didn't → discard entirely; "might help" never rides along.
7. **Write back (continual progress — the iteration IS its own closeout):** one `fm.sh log` row with the unit's executor tokens (`fm.sh tokens <stem>`, summed across retries and consults for that unit) · rewrite RUN.md to the new in-flight reality · FRONTIER.md if the frontier moved · new user-questions into GATES.md with defaults · file executor `.last.md` reports and gate transcripts into `docs/runs/` on the state branch (evidence must outlive the session) · **then, before `fm.sh sync`, the mandatory staleness sweep [GRADUATED 2026-09-01, bitten twice]:** grep `.claude/` for every SHA, branch, gate id, and status this iteration superseded, fix every stale mention, and close every gate the user resolved in chat this session — a sync without the sweep is an incomplete write-back. Every iteration ends committed and pushed; there is never un-recorded progress older than the current in-flight unit. Then loop to 1.

Budgets per implementation unit: 3 runs, 2 consults (dev-delegate's). Run budget exhausted and predicate unmet = spec/scope problem — stop honestly.

## Stop → digest (every run ends with one)

Report: predicate state · iterations used · **tokens: executor total (sum of the tokens column for this run) and director-session total** (Claude: the session usage; Codex: `/status`) · what landed (branches/SHAs) · what was discarded and why · open gates with defaults · next run's obvious predicate. Then run a **cross-model audit** of the run: a fresh agent on a different model family reads decisions.tsv against what actually happened and produces an **Attention** list (weak evidence, verification claimed without proof, risky-in-hindsight calls); include it — "no flags" is a valid value, the auditor's model name is not optional. Batched escalation only: irreversible actions, taste calls, standing-order-vs-reality conflicts, dead ends that survived a pivot. Never ask "should I keep going" mid-run — act and log.

## Rules

- Repo DIRECTOR.md hard rules are binding and override everything here except user instructions in this chat.
- Never merge/tag/push protected branches; never touch worktrees you didn't create; secrets never enter briefs, logs, or commits.
- Lessons: anything caught after implementation → one line appended to DIRECTOR.md's lessons section (symptom → root cause → RULE); twice-bitten lessons graduate into the relevant step's text.
- A foreman run in a repo with a `.claude/CLOSEOUT.md` ends with a normal closeout of the session on top of the digest — but because write-backs are continual, that closeout is a light reconcile (RUN.md truthful, trail complete against the transcript, outward surfaces like the StevOS project page updated), never a reconstruction.
- **Resume:** if you cold-start into a repo whose RUN.md shows an in-flight run, that file is authoritative inheritance — follow its resume recipe; verify inherited claims against the real artifact, but do not re-derive work the trail already paid for.
