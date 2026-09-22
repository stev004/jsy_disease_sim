ROLE: Independent bounded numerical reviewer, gpt-5.6-sol @ high. Author Luna; director Astra. Read-only clone; no implementation.
GOAL: Decide whether the G30 exact-decimal recovery correction resolves the filed numerical defect without changing protected scientific or blind-fit contracts.
SCOPE: Clone /home/steven/jos-g30-review-readonly at 367f0324685437c4d2ed4aa0ae4878229da09839; compare only b5ef032e29c577bce634ce0933b2d7d316ac562e..367f0324685437c4d2ed4aa0ae4878229da09839. Expected files phase0_campaign.py and test_phase0_campaign.py only. Read full diff and surrounding execution paths, plus appended declaration and original Sol numerical report. Source tree is chmod read-only; no edits, commits, pushes or subagents.
CONTEXT: G30 explicitly extended three exhausted attempts by one implementation plus this one review. Original defect falsely excluded 0.40−0.25 <= 0.15 and contaminated signed-error cancellation. Proposal uses Decimal(str()) only on direct declared grid values/truth/thresholds; exact arithmetic through recovery/bias comparison, float conversion at serialized boundaries. Computed objectives/profile-gap rules are excluded; do not retune or invent their numerical semantics. No campaign or real-data fit has run. G29 remains a separate model-owner ruling. The director local verification gate is PASS at this exact candidate under the predeclared known-base-flake rule, and is filed before this review launch; uv0.11.30 matches CI tool pin. Raw full-suite result is 1 failed/443 passed/4 skipped; exact known job-ordering failure reproduced on unchanged base. Remaining steps all PASS. Do not claim all-tests-green. Verify this exception against the appended report and live plan Operational notes. Filed gate: docs/runs/2026-09-22-phase0-g30-verification-gate.md; raw full/remainder/base transcripts referenced there. Prior worker full-suite output is not used as final-byte proof.
ACCEPTANCE:
1. Verify exact candidate and ancestry; inspect every hunk for scope and meaning. Confirm the recovery arithmetic remains truth-joined after blind estimates have been persisted/hashed.
2. Read failing-before and passing-after behavioral evidence; independently run focused numerical tests on the candidate using the external environment. Verify upper asymptomatic endpoint, every declared dimension endpoint, marginal/joint coverage including decisive 3/5, exact cancellation, missing/nonidentified evidence handling and fixed denominators. Do not accept mere import errors as baseline failure.
3. Check exact arithmetic survives through error sums/means/inclusive predicates; Decimal objects do not leak into existing output schema or hashes. No epsilon, rounding, threshold relaxation, changes to grids/seeds/configs/objective/profile definitions or hidden dependency.
4. Inspect tests for weakened assertions or tautologies. Confirm blind hashes and declaration/config hashes are demonstrably unchanged from base. Explicitly report limits; a green code review is not a scientific gate PASS.
5. Report substantive defects with file:line and minimal corrective scope, or PASS for the bounded correction. Mention the still-open computed-objective profile boundary question separately, not as a newly fixed behavior.
VERIFY: GIT_OPTIONAL_LOCKS=0 git rev-parse HEAD; git status --porcelain at start/end; git diff base..HEAD --stat and full diff; use external venv /home/steven/jos-g30-verify/.venv/bin/python -m pytest -p no:cacheprovider tests/test_phase0_campaign.py with PYTHONDONTWRITEBYTECODE=1 and PYTHONPATH set to this clone's src. Do not install in or write to the clone. Existing focused tests mock campaign execution; no real simulator/campaign API calls beyond those tests. Read director mirror transcript, do not repeat full suite unnecessarily. No dependency updates.
TIMEBOX: 15 minutes. Return partial review and unreviewed scope on expiry. This is the one G30 independent review.
FORBIDDEN: Any source/test/config/doc modifications, new thresholds, campaigns/pilots/observation runs outside faithful mocked tests, real-data fitting, full-scale runs, git commits/pushes, external messages, filter evasion. Do not authorize another correction attempt or merge.
REPORT: First line G30 NUMERICAL CORRECTION: PASS or G30 NUMERICAL CORRECTION: BLOCKED. Findings by severity with exact references, independently reproduced results, scope/evidence limits, final SHA and clean-tree attestation. Director files report under docs/audits; final response only.
STANDING: 
# DIRECTOR.md — standing orders for the JOS director agent (foreman)

*The director's constitution for this repo. Re-read in full at the top of EVERY iteration — never work from memory of it. Hard rules refreshed 2026-09-01 post-release (V1.1 released, V1.2 cycle open). Distilled 2026-08-31 from Sol's cold-start handoff (`docs/handoff/2026-08-31-sol-handoff.md`, binding in full) and the foreman architecture (`StevOS/projects/pages/foreman.md`).*

## Roles

- **Director (you - Claude via `/foreman`, or GPT-6 Astra via `$foreman` inside Codex since 2026-09-05):** frame predicates, write briefs, review diffs, verify, keep `.claude/` state files current, decide next. You never implement beyond a one-line obvious fix. Whichever family directs, the end-of-run trail audit runs on the other family.
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
- 2026-09-03 (R7 chain, CI-caught): S1b passed the director's local gates (full suite, ruff, format, fingerprint compare) but failed CI on 3 mypy errors — the local gate list did not mirror CI's verify job, which also runs mypy over a pinned module list -> RULE: the director's pre-push gate for any src/ change is the CI verify job's exact step list (read `.github/workflows/` once per cycle and mirror it: uv lock check, compileall, pytest, ruff check+format, mypy over the pinned modules, relocation check where applicable), not a remembered subset.
- 2026-09-05 (v12-run2 iteration 2, director-caught in review): the executor transcribed the brief's illustrative phrasing for a gov.je `Date` column into the measure dictionary as a sourced fact -> a brief that gives an EXAMPLE value for a transcription/citation field will be copied verbatim -> RULE: in briefs for transcription fields (dictionaries, fixtures, provenance notes), never give example content that is not itself a frozen-source fact; give the rule and the literal `unknown` fallback only, and make "every non-unknown cell cites a frozen locator" an acceptance criterion the executor must grep.
- 2026-09-05 (perf-v12-run3, self-caught): RUN.md carried hand-written clock times up to two hours off the machine clock (the director inferred times from elapsed waits) -> only `fm.sh log` stamps are trustworthy -> RULE: RUN.md and GATES.md cite trail-row phases ("ts: trail row <phase>") instead of hand-written clock times; a time that did not come from `date` or a trail row is not written.
- 2026-09-06 (perf-v12-run3, self-caught at digest time): every trail row of the run lacked its tokens column although the director passed the value -> the WSL-installed `fm.sh` predated the tokens column (the repo's vendored copy was equally old; only the Windows `~/.claude` copy was current) and silently ignored the eighth argument -> RULE: at run start the director diffs the installed `~/.claude/skills/foreman/scripts/fm.sh` against the repo's vendored `.claude/skills/foreman/scripts/fm.sh` and against the newest copy on any machine, reinstalls with `scripts/install_skills.sh --force` if they differ, and checks the first trail row of the run has all seven columns (`awk -F'	' '{print NF}'`).
- 2026-09-09 (run 4 retries, self-caught): cherry-picking a `main` docs commit into two executor worktrees to hand them a review report conflicted on `.claude/RUN.md`/`GATES.md` (the commit carried state-file edits too) and left both worktrees mid-cherry-pick while executors were already running -> state-layer commits are never branch-clean -> RULE: hand context to an executor by copying the file into the worktree (untracked) or quoting it in the brief; never `cherry-pick` a commit that touches `.claude/` into a feature worktree, and never launch an executor in a worktree whose `git status` is not clean apart from intended files.
- 2026-09-12 (v121-run5, self-caught): four executors launched through `wsl -d Ubuntu -- bash -c '... fm.sh exec ...'` from the desktop app all died within a minute, exactly when that wsl.exe invocation returned (log mtimes 17:19:14–17:19:20 vs launch 17:18:50; no `.last.md`, no error text) -> WSL tears down the process tree of a finished `wsl.exe` invocation, `nohup` notwithstanding; earlier runs survived only because the director held an interactive terminal session -> RULE: on this box any process that must outlive a director tool call (codex executors, long measurements) is started from a detached hidden `wsl.exe` session (`Start-Process wsl.exe -ArgumentList '-d','Ubuntu','--','bash','/tmp/<script>.sh' -WindowStyle Hidden`, the script ending in `sleep infinity`), and the director verifies `pgrep -f 'codex exec'` ≥ 60 s after launch before logging the launch row. Corollary: never pass shell variables or `/tmp` paths inline through `wsl -- bash -c` from PowerShell/Git Bash — write a script file under the scratchpad, copy via `/mnt/c`, run it by path.
- 2026-09-12 (v121-run5, terra trail audit Attention 4/5/8): the integration branch was pushed and the independent review launched before the director's own full CI mirror had finished, the mirror's first pass failed on a director-script invocation error, and a quick-gate number was logged without a saved transcript -> the director treated the reviewer's mirror as the gate and its own as optional, and trusted session output as evidence -> RULE: the director's full CI mirror (exact verify-job step list, module lists deduplicated) runs to `PASS` on the integration head BEFORE the push and BEFORE the review launch, its log is filed under `docs/runs/` in the same write-back, and every test count cited in a trail row points at a filed transcript, never at tool-call output that dies with the session.
- 2026-09-12 (v121-run6, terra trail audit Attention 4/5): first-attempt executor briefs carried a `· retry 1` label because the launcher appended it unconditionally, and the mirror-before-push claim had no retained push receipt -> provenance noise and an unverifiable ordering claim -> RULE: a retry label is added only when a previous attempt log for that unit exists; after every push that a trail row relies on, the row's evidence cell carries `git ls-remote origin <branch>` output (SHA + branch) captured in the same step.

- 2026-09-22 (Phase 0, director acceptance review): a no-campaign-execution brief yielded pure scoring utilities without the simulator adapter needed by later units -> implementation and execution authorization were conflated -> RULE: campaign briefs explicitly require implementing and mock-testing the generation/orchestration path while separately keeping real execution gated.

- 2026-09-22 (Phase 0 P0-1 correction, director review): defaulting missing result metadata to requested configs let namespace evidence pass -> test fakes omitted the real result fields -> RULE: evidence checks require returned metadata and reject absence; adapter tests use real config constructors and faithful result metadata, mocking only expensive execution.

- 2026-09-22 (Phase 0 numerical review): binary subtraction excluded a declared inclusive decimal endpoint despite green tests -> endpoints were not exercised -> RULE: declared finite-decimal recovery predicates need exact arithmetic and endpoint/cancellation regressions; never repair by inventing epsilon or retuning thresholds.

- 2026-09-22 (Phase 0 closeout): state-only pushes triggered 12 prohibited Actions runs -> push workflows ignore file intent -> RULE: under no-GitHub-CI instruction, every fm log decision and sync commit message includes [skip ci] before any push; never claim no remote runs without evidence.

- 2026-09-22 (Terra trail audit): local shared-clone origin refs were mistaken for GitHub push evidence -> remote name was treated as identity -> RULE: audit remote URLs before inferring publication; use retained ls-remote output from the actual destination.

## Original declaration
# READY FOR IMPLEMENTATION

This is a specification-readiness verdict, not the independent Phase 0 exit verdict. No simulations, fits, pilot runs, or campaign-generating tests were run during this consult.

I recommend filing this report as:

`docs/research/v1_3/2026-09-21-phase0-predeclaration.md`

The specification must be committed before implementation or execution. None of its grids, thresholds, seeds, or predicates may be relaxed after results are seen.

## 1. Scope and code findings

The governing plan requires joint recovery over 3–5 effective dimensions, at least five process seeds, misspecification injection, and a negative control ([V1.3 plan](/home/steven/jos-p0-design-readonly/docs/research/v1_3/2026-09-21-v13-plan.md:7); [audit authority](/home/steven/jos-p0-design-readonly/docs/audits/2026-09-01-solpro-deep-audit-BLOCKED.md:633)).

The current implementation cannot represent that campaign directly:

- `CalibrationConfig.hidden_parameter` permits only reporting delay or beta ([calibration_schemas.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/calibration_schemas.py:13)).
- The calibration manifest stores one scalar parameter name, recovered value, and truth ([calibration_schemas.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/calibration_schemas.py:87)).
- Existing beta recovery is one-dimensional, despite its two-dimensional sensitivity surfaces ([calibration.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/calibration.py:432)).
- DATA-9 correctly recomputes beta argmins per nuisance factor, but the production path hard-codes nuisance factors `(0.5, 1.0)` and has no non-identification classifier ([calibration.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/calibration.py:40), [calibration.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/calibration.py:606)).

Therefore Phase 0 should use a standalone research campaign harness. It must not extend the existing calibration manifest, hashes, artifact IDs, or observation schemas.

## 2. P0-1 predeclared recovery campaign

### Joint fitted dimensions

All four dimensions are exercised jointly in one exhaustive `3 × 3 × 3 × 3 = 81`-cell grid.

| Dimension | Synthetic truth | Candidate grid | Recovery tolerance | Absolute mean-bias limit |
|---|---:|---|---:|---:|
| Global transmission `beta` | `0.08` | `0.04, 0.08, 0.12` | `0.04` | `0.02` |
| One-off inoculation day offset | `2` | `0, 2, 4` days | `2` days | `1` day |
| Symptomatic detection probability | `0.75` | `0.50, 0.75, 1.00` | `0.25` | `0.125` |
| Asymptomatic detection probability | `0.25` | `0.10, 0.25, 0.40` | `0.15` | `0.075` |

The beta and symptomatic-detection truths reproduce the demonstration assumptions at [respiratory_seirs_demo.yaml](/home/steven/jos-p0-design-readonly/configs/diseases/respiratory_seirs_demo.yaml:33) and [observation_demo.yaml](/home/steven/jos-p0-design-readonly/configs/observation/observation_demo.yaml:4).

The inoculation offset and asymptomatic truth `0.25` are explicitly synthetic campaign assumptions, not Jersey estimates or pathogen defaults. The higher asymptomatic probability is used only to make both observed symptom-status channels informative at CI scale. It must never replace the shipped demonstration value `0.05`.

### Fixed latent scenario

- Mode: `ci`, using the default 3,000 synthetic residents ([population_schemas.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/population_schemas.py:43)).
- Start: `2025-01-06`.
- Latent duration: `30` days.
- Initial seed count: `0`.
- One-off inoculation: exactly 10 scheduled import attempts on `start_date + inoculation_day_offset`.
- Background import rate: `0`.
- Import schedule: empty except for that one inoculation.
- Route multipliers: all `1.0`.
- Symptomatic probability: `0.6`.
- Latent duration: constant `2` days.
- Infectious duration: constant `5` days.
- Waning: disabled.
- Seasonality and interventions: absent.

These are scenario assumptions from the existing pathogen-neutral demonstration configuration, not named-pathogen evidence ([respiratory_seirs_demo.yaml](/home/steven/jos-p0-design-readonly/configs/diseases/respiratory_seirs_demo.yaml:4)). No natural-history parameter is fitted.

Using `import_schedule` for the inoculation is supported by the existing run contract ([outbreak_schemas.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/outbreak_schemas.py:128)) and scheduled-import implementation ([respiratory.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/respiratory.py:523)).

### Observation generation

For every latent infection:

- detection probabilities are the fitted symptomatic/asymptomatic values;
- detection delay is fixed at `0`;
- reporting delay is fixed at `2` days;
- weekday effects are all `1.0`;
- observation horizon tail is explicitly `4` days;
- no real Jersey data enter any calculation.

Two observed channels are derived from `ObservationRunResult.observation_events`:

1. daily reported symptomatic cases;
2. daily reported asymptomatic cases.

Dates are zero-filled over the common latent horizon plus the four-day tail. These channels use already-generated observation events; they do not expose latent counts to the fitter.

The observation RNG is independently namespaced by latent seed, observation seed, and configuration ID ([observation_scheduler.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/observation_scheduler.py:61)). Within each fitting arm, keep one configuration ID across candidates so common random numbers isolate parameter changes, matching the existing calibration convention. Persist the full config hash for each cell.

### Seed schedules

Target truth:

- Process/network seeds: `42001, 42002, 42003, 42004, 42005`.
- Observation seeds: `52001, 52002, 52003, 52004, 52005`, paired in order.
- Observation config ID: `v13-phase0-target`.

Candidate prediction library:

- Process/network seeds: `43001, 43002, 43003`.
- Observation seeds: `53001, 53002, 53003`, paired in order.
- Observation config ID: `v13-phase0-fit`.

The sets are disjoint. Network and outbreak seeds must match because the outbreak runner enforces that invariant ([outbreak_runner.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/outbreak_runner.py:195)).

There is no optimizer seed: every grid cell is evaluated. Candidate simulations may be reused across the five target fits, but target simulations may never be reused as candidate predictions.

### Blind fitting rule

The fitter receives only:

- the two observed target tables;
- the predeclared candidate grid;
- the candidate prediction library.

It must not receive truth values, latent target events, target process seeds, or target latent hashes. Truth metadata is joined only after the selected estimates and their hash have been written.

The fact that the truth lies on the predeclared regular grid is not candidate selection. No grid pruning, refinement, early stopping, or truth-distance tie breaking is permitted.

### Objective

For target process seed \(i\), candidate \(\theta\), channel \(c\), date \(t\), and fitting replicate \(j\), let \(y_{ict}\) be the target count and \(x_{j\theta ct}\) the candidate count.

Define:

\[
m_{\theta ct}=\frac{1}{3}\sum_{j=1}^{3}\sqrt{x_{j\theta ct}+3/8}
\]

\[
L_i(\theta)=\frac{1}{2T}\sum_{c=1}^{2}\sum_{t=1}^{T}
\left(\sqrt{y_{ict}+3/8}-m_{\theta ct}\right)^2
\]

This is a predeclared minimum-distance loss, not a likelihood. It gives the two channels equal weight and prevents a single large stochastic realization from dominating.

All 81 cells must be scored before selection.

### Identifiability

For dimension \(d\), profile over all other dimensions:

\[
P_{i,d}(v)=\min_{\theta:\theta_d=v}L_i(\theta)
\]

Numerical ties use:

\[
\tau_i=10^{-12}\max(1,L_{i,\min})
\]

A dimension is practically identified for target \(i\) only when:

- its profiled minimum is unique within \(\tau_i\); and
- the relative gap to the second-best profile value is at least `0.05`:

\[
\frac{P_{\text{second}}-P_{\min}}{\max(P_{\min},10^{-12})}\ge0.05
\]

The 5% value is a bounded machinery threshold against near-flat grid profiles. It is not a precision or inferential statement.

An exact tied global minimum makes P0-1 fail. No lexicographic estimate may conceal it.

### Descriptive recovery and bias

For dimension \(d\):

- signed error: \(\hat\theta_{i,d}-\theta_d^\*\);
- absolute error: its absolute value;
- descriptive tolerance coverage:

\[
C_d=\frac{1}{5}\sum_i
1\{\text{identified and absolute error}\le\text{tolerance}_d\}
\]

- bias: arithmetic mean signed error across the five target process seeds;
- joint coverage: fraction of target seeds for which all four dimensions are identified and within tolerance.

These are five-seed descriptive hit rates. They do not estimate nominal statistical coverage and must not be presented with confidence-interval language.

### P0-1 aggregate PASS predicate

P0-1 is `PASS` only if all conditions hold:

1. All five target runs and all predeclared candidate cells complete. No replacement seeds.
2. Every truth run realizes all 10 inoculation acquisitions, at least one local secondary infection, at least one report in each symptom channel, and at least three non-zero combined report dates.
3. Observation chronology and latent-incidence conservation diagnostics pass.
4. No global loss minimum has a numerical tie.
5. Each dimension has descriptive tolerance coverage at least `4/5`.
6. Joint four-dimensional coverage is at least `3/5`.
7. Each absolute mean bias is no larger than the tabled half-step limit.
8. No dimension is selected at its grid boundary for more than `1/5` target seeds.
9. Every target and candidate uses the declared seed namespace, grid, objective, dates, and fixed parameters.
10. The workload counters remain within the declared caps below.

A candidate extinction is a valid, usually poor candidate score. A truth extinction or uninformative truth run is a gate failure; it is not resampled.

The one-grid-step tolerances allow one discrete stochastic displacement. The half-step bias limits prevent systematic one-direction error from passing merely through marginal hit rates.

## 3. P0-2 misspecification injections

Both arms reuse the P0-1 target observations, latent candidate runs, seed schedules, grid order, and scoring rule.

Software completion and scientific behavior are reported separately:

- `software_status`: whether the arm executed according to contract;
- `misspecification_detection`: whether the predeclared degradation predicate passed.

A scientifically poor fit under misspecification is expected and does not constitute software failure.

For target \(i\), define relative loss degradation against the correctly specified arm:

\[
R_i=\frac{L^{wrong}_{i,\min}-L^{correct}_{i,\min}}
{\max(L^{correct}_{i,\min},10^{-9})}
\]

### P0-2A: wrong reporting delay

- Truth delay: fixed `2` days.
- Fitted delay: forced to fixed `0` days.
- All four P0-1 fitted dimensions and grids remain unchanged.
- Detection probabilities, process seeds, observation seeds, and common-random-number namespace remain unchanged.

A target seed detects the wrong delay if at least one holds:

- recovered inoculation day is `4`, the declared two-day compensating shift;
- at least one fitted dimension is outside its P0-1 recovery tolerance;
- `R_i ≥ 0.25`.

P0-2A detection is `PASS` when at least `3/5` targets detect it.

### P0-2B: wrong ascertainment regime

Truth retains separate probabilities:

- symptomatic: `0.75`;
- asymptomatic: `0.25`.

The fitted model incorrectly imposes one common probability for both symptom statuses:

- common probability grid: `0.25, 0.50, 0.75`;
- beta and inoculation grids remain unchanged;
- grid size: `3 × 3 × 3 = 27`.

For the selected wrong-model candidate, define channel-total error:

\[
E_i=\max_c
\frac{|\overline{N}^{wrong}_{ic}-N^{target}_{ic}|}
{\max(1,N^{target}_{ic})}
\]

A target detects the wrong regime if at least one holds:

- `R_i ≥ 0.25`;
- `E_i ≥ 0.25`;
- beta or inoculation timing is outside its P0-1 tolerance.

P0-2B detection is `PASS` when at least `4/5` targets detect it.

P0-2 is `PASS` only when both arms have `software_status=PASS` and `misspecification_detection=PASS`. If a wrong model recovers apparently well and evades these predicates, Phase 0 fails scientifically; thresholds must not be relaxed.

## 4. P0-3 negative control

### Non-identified parameter

The negative control is a global multiplier applied uniformly to all 11 route multipliers while beta remains free.

This factor is forbidden as an actual fitted Phase 0 parameter. It is perturbed only for the negative control and otherwise remains fixed at `1.0`.

Fix inoculation timing and ascertainment at the P0-1 truths. Evaluate:

- beta: `0.04, 0.08, 0.16`;
- global route factor: `0.5, 1.0, 2.0`;
- full `3 × 3 = 9` surface.

The three pairs:

- `(beta=0.16, factor=0.5)`;
- `(beta=0.08, factor=1.0)`;
- `(beta=0.04, factor=2.0)`;

all produce route beta `0.08`. Because the runner computes route transmission as `beta × route_multiplier` ([outbreak_runner.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/outbreak_runner.py:240)), this is a deliberately structural non-identifiability.

### DATA-9 use and thresholds

Use the existing DATA-9 surface logic to report:

- complete objective surface;
- beta argmin for every factor;
- signed beta shift from the factor-1 reference;
- profiled minima.

Additionally, the campaign wrapper must classify structural equivalence. P0-3 is `PASS` only if:

1. The predicted two-channel vectors for all three equal-product pairs agree within `1e-12` elementwise.
2. Their objective spread is no greater than `10^-12 × max(1, minimum objective)`.
3. The report contains every per-factor beta argmin and signed shift.
4. The factor is reported as `NON_IDENTIFIED_STRUCTURAL`.
5. `factor_estimate` is `null`; no standard error, interval, or coverage value is emitted.
6. Changing only decomposition between beta and factor leaves the target-independent prediction hash identical for the three ridge cells.

The existing DATA-9 computational instrument is sufficient for profiling and per-factor argmins. Its current hard-coded factor set, one-dimensional campaign path, and scalar artifact schema are not sufficient for this control. The standalone wrapper supplies the factor grid and classification without changing DATA-9 or its artifacts.

## 5. Workload and fail-closed budget

Exact planned maximum:

| Work | Maximum |
|---|---:|
| P0-1 grid cells | 81 |
| P0-2 wrong-delay cells | 81 |
| P0-2 wrong-regime cells | 27 |
| P0-3 cells | 9 |
| Total cells across arms | 198 |
| Truth latent outbreak calls | 5 |
| P0-1/P0-2 candidate latent calls | 27 |
| P0-3 latent calls | 27 |
| Total latent outbreak calls | 59 |
| Observation transforms | 599 |
| Distinct population/network seed builds | 8 |
| Duration per outbreak | 30 days |
| Mode | `ci` only |

Before the first simulation, dry-run planning must calculate these counts. Execution fails closed if:

- mode is not `ci`;
- duration exceeds 30 days;
- any grid exceeds its declared cells;
- predicted outbreak calls exceed 59;
- predicted observation transforms exceed 599;
- seeds overlap;
- any undeclared retry, adaptive grid, or replacement seed is requested.

This is not a 30-replicate ensemble and produces no empirical 2.5/97.5 bands. No 180-day run is authorized.

## 6. Outputs and protected contracts

Write the research bundle outside the clone, containing:

- frozen campaign config and SHA-256;
- predeclaration document SHA-256;
- input source/config hashes;
- seed ledger;
- all candidate loss surfaces;
- `p0_1_recovery.csv`;
- `p0_2_misspecification.csv`;
- `p0_3_profile.json`;
- `campaign_summary.json`;
- file-level `SHA256SUMS`.

Do not route this through `CalibrationArtifactManifest` or `write_calibration_artifact`; those contracts are scalar and would misrepresent the joint campaign ([calibration_artifacts.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/calibration_artifacts.py:154)).

Any proposal to alter existing calibration/observation schemas, artifact hashes, artifact IDs, or verification rules requires a separate explicitly declared migration brief. It is not authorized here.

## 7. Unit order and dependencies

1. Director files and commits this predeclaration.
2. Implement P0-1 harness, pure scoring, blind fit boundary, dry-run budget check, and unit tests.
3. Implement both P0-2 arms without running them.
4. Implement P0-3 surface and non-identification classifier without running it.
5. Independent code review verifies the implementation against the committed specification.
6. Run one all-arms CI-mode campaign.
7. Independent fresh Sol inspects the immutable result bundle and authors the exit verdict.

No campaign arm may be run before all three arms and predicates are implemented. This prevents P0-2/P0-3 choices from reacting to P0-1 results.

## 8. Implementation briefs

### P0-1 — nine-field Luna brief

**GOAL:** Implement the predeclared four-dimensional CI-mode synthetic-recovery harness, blind scoring boundary, descriptive recovery table, profile-identifiability diagnostics, budget enforcement, and standalone research output.

**SCOPE:** Add only `src/jersey_outbreak/phase0_campaign.py`, `configs/calibration/v13_phase0_synthetic.yaml`, and `tests/test_phase0_campaign.py`. The director-filed predeclaration is read-only. Do not edit existing calibration, observation, outbreak, artifact, hashing, or CLI modules.

**CONTEXT:** Baseline code is `3ff37348f88750470be9f1ccda193b3ff31fb9c3`; consult clone is detached at `94f7f9116f27be0b7604906c774a1e03663c768e`. Current calibration is scalar. Implement the exact P0-1 contract above as a standalone research harness. Fitter-facing functions must not accept truth metadata.

**ACCEPTANCE:** Exact dimensions, grids, seeds, fixed parameters, observation channels, objective, tie rule, 5% profile-gap rule, recovery tolerances, bias thresholds, boundary accounting, truth viability, and aggregate predicate are encoded without substitutions. Dry-run reports 81 cells, 5 target seeds, 3 fitting seeds, 32 latent calls through P0-1, and 248 observation transforms. Unit tests prove seed disjointness, no truth field crosses the fitter interface, complete-grid scoring, tie failure, budget failure, coverage/bias arithmetic, and fixed target/candidate date grids.

**VERIFY:** Run the P0-1 commands in section 9, inspect the implementation, report actual output, changed files, and diff stat.

**TIMEBOX:** 75 minutes. If the existing APIs cannot support the contract without editing a protected module, stop and report the exact conflict.

**FORBIDDEN:** Campaign execution; real data; pilot fitting; adaptive grids; new dependencies; schema/hash migrations; changes to natural history, route semantics, existing artifacts, or existing calibration behavior; tracked result files; commits or pushes.

**REPORT:** Verdict first; per-criterion evidence; dry-run budget table; exact commands and output; files changed; diff stat; unresolved conflicts. Do not claim the scientific gate passed.

**STANDING:** Apply the repository `AGENTS.md` and the exact `DIRECTOR.md` standing block supplied with this task. Smallest root-cause change, no destructive git, no protected-contract change, no invented scientific defaults, and no status-vocabulary drift.

### P0-2 bounded brief

**GOAL:** Add the fixed-zero-delay and common-probability ascertainment misspecification arms and their predeclared detection predicates.

**SCOPE:** Modify only the three P0-1 files. Reuse target observations and latent candidate cache. No core observation changes.

**CONTEXT:** Depends on accepted P0-1 implementation. The arms test scientific sensitivity; poor recovery is expected and is distinct from software failure.

**ACCEPTANCE:** Exact 81- and 27-cell arms; isolated interventions; `R_i` and `E_i` definitions; `3/5` and `4/5` detection thresholds; separate software/detection statuses; no threshold derived from results.

**VERIFY:** Run the P0-2 commands in section 9 and confirm dry-run cumulative totals remain within 198 cells, 59 latent calls, and 599 transforms.

**TIMEBOX:** 45 minutes.

**FORBIDDEN:** Running the campaign, changing P0-1 predicates, adding a temporal-regime observation API, or editing existing schemas/artifacts.

**REPORT:** Per-arm implementation evidence, invariant tests, budget totals, changed files, diff stat, and blockers.

**STANDING:** Same standing orders as P0-1.

### P0-3 bounded brief

**GOAL:** Implement the nine-cell beta × global-route-factor negative control using the DATA-9 per-factor profiler and emit an explicit structural non-identification result.

**SCOPE:** Modify only the P0-1 files. Import/reuse the existing profiling helper; do not change existing DATA-9 constants or production calibration output.

**CONTEXT:** The route factor is a negative-control nuisance only. It remains fixed everywhere outside P0-3.

**ACCEPTANCE:** Exact beta/factor grids; complete surface; three equal-product ridge cells; `1e-12` vector and objective thresholds; per-factor argmins and shifts; `NON_IDENTIFIED_STRUCTURAL`; null factor estimate; failure if false precision is emitted.

**VERIFY:** Run the P0-3 commands in section 9 and inspect the exact equivalence assertions.

**TIMEBOX:** 30 minutes.

**FORBIDDEN:** Campaign execution, fitting route multipliers in P0-1/P0-2, changing DATA-9 semantics, or migrating calibration artifacts.

**REPORT:** Surface/classifier unit evidence, proof that no factor point estimate can be serialized, files changed, diff stat, and blockers.

**STANDING:** Same standing orders as P0-1.

## 9. Exact acceptance commands

Implementation checks:

```bash
git rev-parse HEAD
git status --porcelain

UV_CACHE_DIR=/tmp/uv-cache uv run python -m jersey_outbreak.phase0_campaign dry-run \
  --config configs/calibration/v13_phase0_synthetic.yaml \
  --predeclaration docs/research/v1_3/2026-09-21-phase0-predeclaration.md

UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_phase0_campaign.py \
  -k 'p0_1 or blind or budget'

UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_phase0_campaign.py -k p0_2
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_phase0_campaign.py -k p0_3

UV_CACHE_DIR=/tmp/uv-cache uv run python -m compileall -q src
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check \
  src/jersey_outbreak/phase0_campaign.py tests/test_phase0_campaign.py
UV_CACHE_DIR=/tmp/uv-cache uv run ruff format --check \
  src/jersey_outbreak/phase0_campaign.py tests/test_phase0_campaign.py
UV_CACHE_DIR=/tmp/uv-cache uv run mypy --ignore-missing-imports \
  src/jersey_outbreak/phase0_campaign.py

UV_CACHE_DIR=/tmp/uv-cache uv run pytest
git diff --check
git status --porcelain
```

Only after the implementation review passes, the authorized campaign command is:

```bash
UV_CACHE_DIR=/tmp/uv-cache STARSIM_INSTALL_FONTS=0 MPLCONFIGDIR=/tmp/mpl-cache \
uv run python -m jersey_outbreak.phase0_campaign execute \
  --config configs/calibration/v13_phase0_synthetic.yaml \
  --predeclaration docs/research/v1_3/2026-09-21-phase0-predeclaration.md \
  --output-dir /tmp/jos-v13-phase0-campaign
```

## 10. Limitations and unresolved risks

- Five target seeds support only a descriptive machinery check. They cannot establish nominal statistical coverage.
- Three fitting seeds give a bounded candidate prediction library, not a stable characterization of process uncertainty.
- The two symptom-status case channels are supported by the current observation event model, but they are not the later V1.3 cases/tests/positivity/serology objective. If Phase 2 materially changes the objective or adds streams, its objective requires a new deterministic fixture and synthetic-recovery check before real fitting.
- The disease configuration is pathogen-neutral and synthetic. Passing cannot be described as Jersey calibration or named-pathogen validation.
- The `0.25` asymptomatic ascertainment truth is challenge-only and must not become a default.
- P0-3 establishes deliberate structural confounding in the implemented route-beta product. It does not establish real-data identifiability for beta or any route effect.

No scope-owner ruling is required for the default standalone-harness route. A ruling would be required only if the director wants Phase 0 results incorporated into the existing versioned calibration artifact contract.

## 11. Repository attestation

- Inspected HEAD: `94f7f9116f27be0b7604906c774a1e03663c768e`
- Declared code baseline is an ancestor: `3ff37348f88750470be9f1ccda193b3ff31fb9c3`
- Initial `git status --porcelain`: empty
- Final `git status --porcelain`: empty
- Final `git diff --stat`: empty
- Final `git diff --check`: clean
- Tracked files edited: none
- Simulations/fits/campaign tests executed: none
## Original numerical report
NUMERICAL CONTRACT: BLOCKED

This is a numerical implementation defect, not a scientific campaign failure. No campaign has run, so no Phase-0 scientific verdict is available.

## Findings

At exact detached HEAD `b5ef032e29c577bce634ce0933b2d7d316ac562e`, YAML decimal values are converted to binary `float` ([phase0_campaign.py:203](/home/steven/jos-p01-numeric-readonly/src/jersey_outbreak/phase0_campaign.py:203)). Recovery error is then calculated by direct float subtraction ([phase0_campaign.py:421](/home/steven/jos-p01-numeric-readonly/src/jersey_outbreak/phase0_campaign.py:421)).

Consequently, the declared inclusive asymptomatic endpoint is rejected:

```text
estimate 0.40 - truth 0.25
float absolute error: 0.15000000000000002
declared tolerance:   0.15
current comparison:   False
exact decimal result: 0.15 <= 0.15, True
```

The frozen specification explicitly requires `absolute error <= tolerance` ([predeclaration.md:157](/home/steven/jos-p01-numeric-readonly/docs/research/v1_3/2026-09-21-phase0-predeclaration.md:157)), with the relevant values declared at [predeclaration.md:30](/home/steven/jos-p01-numeric-readonly/docs/research/v1_3/2026-09-21-phase0-predeclaration.md:30) and [v13_phase0_synthetic.yaml:25](/home/steven/jos-p01-numeric-readonly/configs/calibration/v13_phase0_synthetic.yaml:25).

Affected paths are:

- Descriptive coverage: `error <= tolerance` at [phase0_campaign.py:1371](/home/steven/jos-p01-numeric-readonly/src/jersey_outbreak/phase0_campaign.py:1371) falsely excludes an identified `0.40` estimate.
- Joint coverage: `error > tolerance` at [phase0_campaign.py:1417](/home/steven/jos-p01-numeric-readonly/src/jersey_outbreak/phase0_campaign.py:1417) falsely rejects the entire recovery row.
- Signed error and emitted recovery data record `0.15000000000000002`, not the declared-decimal difference.
- Bias aggregation at [phase0_campaign.py:1395](/home/steven/jos-p01-numeric-readonly/src/jersey_outbreak/phase0_campaign.py:1395) inherits this asymmetry. For one `0.40` and one `0.10` estimate plus three truths, the mathematically cancelling errors produce `5.551115123125783e-18`, not zero.
- The bias predicate at [phase0_campaign.py:1403](/home/steven/jos-p01-numeric-readonly/src/jersey_outbreak/phase0_campaign.py:1403) is not observed to flip for this frozen campaign: exhaustive enumeration of all `3^5` selections for each dimension found that none of the four half-step bias endpoints is reachable on the declared five-seed grids, and no bias-pass mismatches occurred. The descriptive value is nevertheless contaminated.

The other frozen recovery endpoints currently classify correctly. In particular, `0.10−0.25` happens to yield `-0.15`, while `0.40−0.25` yields the larger representation. Beta’s upper error yields `0.039999999999999994` and passes. This asymmetry confirms that relying on incidental binary rounding is not a valid contract implementation.

Boundary counting itself is unaffected: [phase0_campaign.py:1316](/home/steven/jos-p01-numeric-readonly/src/jersey_outbreak/phase0_campaign.py:1316) compares selected values copied directly from the same grid. The `4/5` and `3/5` aggregate comparisons also reproduce identical floats on each side.

A related coverage gap exists at the profile-gap predicate ([phase0_campaign.py:1050](/home/steven/jos-p01-numeric-readonly/src/jersey_outbreak/phase0_campaign.py:1050)): hand-entered decimal values `0.100` and `0.105` produce a float relative gap of `0.049999999999999906`, which fails the inclusive `>= 0.05` test. Unlike the recovery grid, production objective values are computed from square roots and have no frozen exact-decimal representation. I therefore do not recommend silently applying decimal-string semantics there; its exact-boundary meaning remains an untested numerical-specification question, not a demonstrated campaign failure.

## Smallest correct remedy

Keep simulation inputs, objective calculations, schemas, hashes, and candidate cells unchanged. At the truth-joined recovery layer only:

1. Convert selected grid value, truth, tolerance, and bias limit using `Decimal(str(value))`.
2. Compute signed errors, absolute errors, sums, means, and inclusive recovery/bias comparisons in `Decimal`.
3. Convert descriptive values to ordinary floats only when emitting the existing output fields.

This exactly implements the frozen finite-decimal grid without epsilon inflation, altered tolerances, or rounding. `Decimal(str(...))` is appropriate here because selected estimates and truths are direct members of the frozen decimal grid. It is not a generic repair for arbitrary computed floats: for values produced by optimizers, transforms, or irrational objective arithmetic, the original decimal intent cannot be recovered from `str(float)`.

A genuinely obvious one-line director fix does not suffice. Fixing only the coverage comparison leaves joint coverage and bias arithmetic inconsistent. Centralizing corrected subtraction in `signed_error` would still require a new exact representation/import and regression coverage; keeping exact arithmetic through the bias predicate is the robust bounded correction.

The bounded Luna correction should touch only:

- the recovery/error arithmetic within `phase0_campaign.py`;
- focused tests in `test_phase0_campaign.py`.

It must not alter the YAML, predeclaration, declaration hash, blind-fit objective/profile definitions, estimate/config hashes, schemas, seeds, statuses, or campaign orchestration.

## Required regressions

Failing before and passing after:

1. `selected asymptomatic=0.40`, truth `0.25`: exact absolute error is `0.15` and is inside the inclusive `0.15` tolerance.
2. Five identified rows containing one `0.40` and four `0.25` selections: asymptomatic coverage and joint coverage both remain `1.0`, not `0.8`.
3. Exactly three intended joint hits, one using `0.40`, with two independently non-identified rows: joint coverage is exactly `3/5` and its predicate passes. This directly detects the current false `2/5`.
4. Selections `0.40, 0.10, 0.25, 0.25, 0.25`: mean signed asymptomatic bias is exactly zero.
5. Table-driven checks for both endpoints of every frozen dimension, preserving inclusive behavior and preventing one-sided regressions.
6. Confirm blind estimate hashes and declaration/config hashes are unchanged, since recovery arithmetic occurs only after truth join.

## Existing test coverage

There are 21 test functions, with one two-case parametrization, giving 22 focused cases statically.

The closest test is [test_phase0_campaign.py:333](/home/steven/jos-p01-numeric-readonly/tests/test_phase0_campaign.py:333). It exercises beta’s upper endpoint, but that endpoint rounds downward and therefore does not expose the defect. Its asymptomatic selections all equal truth. Its bias assertion uses `pytest.approx(0.032)` and checks only a clearly failing limit, not cancellation or an inclusive endpoint.

[test_phase0_campaign.py:366](/home/steven/jos-p01-numeric-readonly/tests/test_phase0_campaign.py:366) checks beta’s lower error with `pytest.approx`, again not the asymmetric `0.40−0.25` case. No focused test covers the asymptomatic upper endpoint, a joint-coverage threshold made decisive by that endpoint, exact signed-error cancellation, or the exact 5% profile-gap boundary.

Per the brief, I did not run pytest or independently verify the reported 22/432 pass results or CI transcript.

## Probe evidence and attestation

Pure arithmetic probes used `/usr/bin/python3` outside the clone. Relevant verbatim output:

```text
beta
  0.04 0.04 True True
  0.08 0.0 True True
  0.12 0.039999999999999994 True True
  bias_boundary_reachable False bias_predicate_mismatches 0
inoculation_day_offset
  0 2.0 True True
  2 0.0 True True
  4 2.0 True True
  bias_boundary_reachable False bias_predicate_mismatches 0
symptomatic_detection_probability
  0.50 0.25 True True
  0.75 0.0 True True
  1.00 0.25 True True
  bias_boundary_reachable False bias_predicate_mismatches 0
asymptomatic_detection_probability
  0.10 0.15 True True
  0.25 0.0 True True
  0.40 0.15000000000000002 False True
  bias_boundary_reachable False bias_predicate_mismatches 0
decimal_to_float_remedy 0.15 True
```

Additional exact probe output:

```text
errors ['0.15000000000000002', '-0.15', '0.0', '0.0', '0.0']
mean_bias 5.551115123125783e-18
profile_gap_at_declared_endpoint 0.049999999999999906
profile_gap_passes False
coverage_endpoint_passes True
joint_endpoint_passes True
```

Start and end verification:

```text
GIT_OPTIONAL_LOCKS=0 git rev-parse HEAD
b5ef032e29c577bce634ce0933b2d7d316ac562e

GIT_OPTIONAL_LOCKS=0 git status --porcelain
<empty>
```

Final `git diff --check` and `git diff --stat` were empty. No files were written, no dependencies installed, and no simulations, observation transforms, fits, pilots, campaigns, commits, pushes, or external messages occurred.
## Director checkpoint (executor timebox interruption)
# G30 director checkpoint — verification pending

Candidate 367f0324685437c4d2ed4aa0ae4878229da09839, branch codex/v13-p01-numeric-fix, base b5ef032e29c577bce634ce0933b2d7d316ac562e. Scope: two files, +168/-15; full final source/test diff read by director. Decimal arithmetic remains confined to truth-joined recovery and bias; existing float reporting retained. YAML/declaration unchanged. No objective/profile/grid/seed/schema/dependency changes. No push, campaign or scientific verdict.

The Luna xhigh extension (session 01a0c9a6-5649-7d82-9af9-0a245ea20b6d) was terminated at its timebox after about 26 minutes including director detection latency; exact machine receipt `docs/runs/2026-09-22-phase0-g30-timebox-stop.txt`. No final executor report or final token tally was available. Saved raw output: `...-g30-executor-interrupted.log`. The log includes 444 passed/4 skipped, but repeated full-suite sessions and formatting make final-byte coverage insufficiently clear; this checkpoint does NOT use that result as final acceptance. Earlier commentary stating full-suite completion is qualified by this coverage limitation.

Director independently ran the final new tests against imported base source and corrected source: base 5 failed/7 passed/22 deselected; corrected 12 passed/22 deselected. Import paths and exact failures are retained in `...-g30-director-before.log` and `...-g30-director-after.log`; exact commands `...-g30-before-after-commands.txt`. These are real assertion failures, not collection errors. Cases include both endpoints, marginal/joint coverage, decisive 3/5, cancellation and pinned blind/config/declaration hashes.

Final source SHA-256 66b4153fd030ff39f68aa2f49ddf1fa87510768808a0ffeb80225bc34112ce24; test SHA-256 dd26ac6574917d474fde0f0305ad5550e6b80348ff3dff45e563f10991b07bb6.

Director clean-clone mirror now runs at the exact candidate with uv0.11.30, CI verify command list plus the new-module mypy. Independent bounded Sol review remains unspent and cannot launch before a filed mirror PASS. G30 authorizes no further implementation retry. G29 remains pending. Prior main code/evidence unchanged.

Evidence outside clone, read-only: /home/steven/jsy_disease_sim/docs/runs/2026-09-22-phase0-g30-director-before.log, ...-g30-director-after.log, ...-g30-before-after-commands.txt, ...-g30-ci-mirror.log. No final executor report exists; do not infer one. Final token usage unknown. The director read the full final diff and independently verified before/after behavior. Do not repeat full suite; the fresh clean mirror is the director gate.

## Final director verification gate
# G30 local verification gate: PASS under the predeclared base-flake rule

Exact source 367f0324685437c4d2ed4aa0ae4878229da09839, clean detached clone `/home/steven/jos-g30-verify`; uv0.11.30 matches CI setup. This is not an all-tests-green result and is not a scientific exit verdict.

- Full suite: **1 failed, 443 passed, 4 skipped**, 15 warnings, 1097.94s. The sole failure is `tests/test_prov_job_ordering.py::test_missing_head_request_fails_alone_and_scheduler_continues`, line176, RUNNING versus SUCCEEDED at its five-second deadline. Raw mirror exit1/FAIL remains preserved in `docs/runs/2026-09-22-phase0-g30-ci-mirror.log`.
- Confirmed on unchanged base b5ef032e29c577bce634ce0933b2d7d316ac562e with the same assertion: one failed in5.94s, exit1. `...-g30-known-flake-base.log` and commands companion. Job implementation and this test have zero diff between base/head. No artificial delay or test alteration was used.
- Authority: live V1.3 plan Operational notes predeclare this exact timing flake, Steven's won't-fix-now ruling, and confirm-on-base then disregard in reviews. This is the existing exception, not a new waiver or hidden failure.
- Remaining verify steps completed separately after the pytest stop: ruff/check+format, pinned15-module mypy, demo, ci population/structure/network generation, relocation check, new-module mypy, diff check, clean tree and exact SHA. Exit0; `MIRROR_REMAINDER=PASS SHA=367f0324685437c4d2ed4aa0ae4878229da09839`. Transcript `...-g30-ci-remainder.log`; commands companion. Initial lock/sync/compile steps are in the full mirror transcript. No full suite was rerun merely to seek green.
- Director focused before/after proof: five base assertion failures versus all12 new cases passing on head. Existing/new Phase-0 tests: all34 passed within full suite. Frozen config/declaration and blind estimate/config hashes unchanged.

The local pre-review gate is PASS with this explicitly disclosed, reproduced predeclared flake. Independent Sol numerical review remains required before feature push. No campaign, code merge or new GitHub CI run is authorized.

## Authoritative existing flake rule
 for the incoming director (Astra)

- Cold start: `.claude/REPO-MAP.md` → `CLAUDE.md` → `.claude/FRONTIER.md` → `.claude/RUN.md` → `.claude/GATES.md` → `.claude/DIRECTOR.md` (binding) → this plan.
- Machine facts: WSL loop home `~/jsy_disease_sim`; detached-session launch pattern and the `wsl -- bash -c` quoting rules in RUN.md/DIRECTOR lessons; local CI mirror is the gate. GitHub CI remains prohibited by Steven. Correction 2026-09-22: 12 early state pushes unintentionally triggered Actions; evidence and costs-unknown disclosure are in `docs/runs/2026-09-22-phase0-unintended-ci-correction.md`. Every state log/sync commit must include `[skip ci]`.
- Codex auth: rotated 2026-09-20; WSL copy synced. Do not run Windows and WSL codex concurrently.
- Known flake: `test_prov_job_ordering::test_missing_head_request_fails_alone…` (timing race; Steven ruled won't-fix-now). Confirm-on-base then disregard in reviews.
- Filter handling update 2026-09-22: Steven reported repeated Codex biological-content display warnings. Worker logs did not establish their cause. The earlier retry advice is superseded: do not bypass or disguise content to evade a filter. Preserve status, inspect the notice and use only a supported recovery path. This run's implementation retries corrected reproduced code defects; the recorded budgets remain authoritative.
