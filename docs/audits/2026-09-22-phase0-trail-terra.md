TRAIL AUDIT: ATTENTION

- **HIGH — feature branch was pushed despite the recorded hold.** The clone has `refs/remotes/origin/codex/v13-p0-1-recovery` at `b5ef032e29c577bce634ce0933b2d7d316ac562e`. This contradicts [RUN.md](/home/steven/jos-phase0-trail-readonly/.claude/RUN.md:8), [FRONTIER.md](/home/steven/jos-phase0-trail-readonly/.claude/FRONTIER.md:34), [roadmap.md](/home/steven/jos-phase0-trail-readonly/docs/roadmap.md:11), [session_log.md](/home/steven/jos-phase0-trail-readonly/docs/session_log.md:8), and trail rows 274–277, all of which say push held/no feature push. Record this as an unauthorized premature push; do not alter immutable reports or infer acceptance. No retained push/`ls-remote` receipt establishes timing.

- **LOW — several token claims lack independently filed corroboration.** All Phase-0 trail rows have seven columns, but 143088 (spec), 337617 (attempt 1), 30431 (P0-2 consult), and 65384 (numerical consult) appear only in the trail/state, not their corresponding filed reports/attestations. The r1 and r2 totals are corroborated in [r1 director review](/home/steven/jos-phase0-trail-readonly/docs/runs/2026-09-22-phase0-p01-r1-director-review-FAIL.md:31) and [acceptance report](/home/steven/jos-phase0-trail-readonly/docs/runs/2026-09-22-phase0-p01-acceptance-PASS.md:13). The launch receipts contain differing unlabeled terminal numbers, so no discrepancy should be asserted without raw worker receipts.

Verified:

- `HEAD` start/end: `2f7345312b3c4594986f36b4cf7619f9dcfca120`; clean tree at both checks.
- `3ff37348f88750470be9f1ccda193b3ff31fb9c3` is an ancestor; `src`, `configs`, and `tests` are unchanged from it on `main`. `b5ef032…` is not an ancestor of `main`.
- Frozen declaration SHA-256 matches `ef67fe49903c3984ca98679eb0470878bc25523baca3bc23a63e4ae7d983a104`.
- Three P0-1 attempts and the withdrawal are consistently recorded. The saved before/after namespace probe demonstrates the prior acceptance and candidate rejection/acceptance behavior; the later numerical report separately withdraws push readiness.
- Local mirror evidence is retained: `432 passed, 4 skipped`, exact candidate SHA, clean-tree checks, and mirror PASS. It predates the numerical consult in the state chronology. It used uv 0.12.9, while CI setup specifies 0.11.30; this is a local mirror, not GitHub CI.
- G29 and G30 remain open HOLD decisions; P0-2/P0-3, campaign execution, independent code review, scientific exit verdict, and Steven merge gate are unrun/unapproved. The numerical BLOCKED report is not a Phase-0 scientific verdict.
- No tracked campaign result bundle exists. Filed attestations support no campaign/fit/simulation, but cannot prove absence of all external activity.
- State commits form a separate state-layer line and no Phase-0 cherry-pick evidence was found. The exact `fm log/sync` invocation method and destructive-operation absence are not independently reconstructible from retained artifacts.

Closeout should file this audit as a separate immutable report, then reconcile the pushed-branch contradiction in live state without editing earlier reports.