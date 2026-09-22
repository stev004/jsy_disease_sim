# G30 local verification gate: PASS under the predeclared base-flake rule

Exact source 367f0324685437c4d2ed4aa0ae4878229da09839, clean detached clone `/home/steven/jos-g30-verify`; uv0.11.30 matches CI setup. This is not an all-tests-green result and is not a scientific exit verdict.

- Full suite: **1 failed, 443 passed, 4 skipped**, 15 warnings, 1097.94s. The sole failure is `tests/test_prov_job_ordering.py::test_missing_head_request_fails_alone_and_scheduler_continues`, line176, RUNNING versus SUCCEEDED at its five-second deadline. Raw mirror exit1/FAIL remains preserved in `docs/runs/2026-09-22-phase0-g30-ci-mirror.log`.
- Confirmed on unchanged base b5ef032e29c577bce634ce0933b2d7d316ac562e with the same assertion: one failed in5.94s, exit1. `...-g30-known-flake-base.log` and commands companion. Job implementation and this test have zero diff between base/head. No artificial delay or test alteration was used.
- Authority: live V1.3 plan Operational notes predeclare this exact timing flake, Steven's won't-fix-now ruling, and confirm-on-base then disregard in reviews. This is the existing exception, not a new waiver or hidden failure.
- Remaining verify steps completed separately after the pytest stop: ruff/check+format, pinned15-module mypy, demo, ci population/structure/network generation, relocation check, new-module mypy, diff check, clean tree and exact SHA. Exit0; `MIRROR_REMAINDER=PASS SHA=367f0324685437c4d2ed4aa0ae4878229da09839`. Transcript `...-g30-ci-remainder.log`; commands companion. Initial lock/sync/compile steps are in the full mirror transcript. No full suite was rerun merely to seek green.
- Director focused before/after proof: five base assertion failures versus all12 new cases passing on head. Existing/new Phase-0 tests: all34 passed within full suite. Frozen config/declaration and blind estimate/config hashes unchanged.

The local pre-review gate is PASS with this explicitly disclosed, reproduced predeclared flake. Independent Sol numerical review remains required before feature push. No campaign, code merge or new GitHub CI run is authorized.
