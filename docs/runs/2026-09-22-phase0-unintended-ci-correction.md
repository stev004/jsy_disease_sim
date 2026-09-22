# Director correction: unintended GitHub CI triggers

Read-only GitHub run-list and per-run job queries confirmed 12 automatic Actions runs for early Phase-0 state pushes (2026-09-21T22:44:14Z through 23:06:23Z). This violated the user instruction not to use GitHub CI. Earlier blanket statements of no GitHub CI were incorrect. The director omitted skip markers on these early state commits; later writes use [skip ci]. No further CI was launched for this check, and historical runs are already complete. Billing cost is unknown. Local mirror remains the acceptance gate; remote success does not resolve the numerical hold or scientific predicate.

Primary evidence: `docs/runs/2026-09-22-phase0-unintended-ci-runs.json` contains IDs, exact SHAs, URLs and job conclusions fetched with `gh run view <id> --json ...jobs...`. No commits/history were rewritten and workflows were not changed. This correction supplements the Terra audit, whose immutable snapshot predates the discovery.
