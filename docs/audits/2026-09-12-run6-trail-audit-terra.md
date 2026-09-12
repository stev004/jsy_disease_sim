1. Confirmed — audit clone is exactly `f6bf7ca1748c8cac6a213ae963f364ac25b0b391`.

2. Confirmed — all cited refs resolve. `integration-run6` first-parent chain is exactly:

```text
84b9676 → 2905512 (jobkw) → 3f0fc68 (trav) → 7439b9d (r8c)
```

Each merge has the declared unit as second parent. Direct unit diffs match report file lists:
- jobkw: `job_registry.py`
- trav: `travel.py`, `test_m8_travel.py`, fixture
- r8c: `network_generator.py`, `network_artifacts.py`, `test_networks.py`

Important qualification: trav and r8c are directly parented by `c7d3876`, not `84b9676`; only jobkw is directly based on run-5 integration.

3. Confirmed — all five filed reports/logs exist at audit HEAD; the fixture exists on `v121/travel-exactness` as specified, not state-only `main`. Raw logs corroborate claimed 16/365/370/397 test counts, replay counts, store sizes, and cited example hashes. Focused independent checks in a disposable Git clone passed:

```text
2 passed in 3.34s
8 passed, 19 deselected in 5.37s
```

The 35-test job/API/liveness group did not finish before this environment’s 30-second execution cutoff, so I do not independently claim that subgroup’s summary; the filed 397-test mirror covers it.

4. Confirmed, with a limit — sequencing is correct in recorded evidence. Mirror log says:

```text
MIRROR_RESULT=PASS 2026-09-12T19:37:26Z
```

`/tmp/launch-review6.sh.out` mtime is `20:38:15+01:00` (19:38:15Z), after the mirror; the review launch follows the mirror row. The trail also orders mirror → push → review. No independent push receipt/timestamp was retained, so the physical push instant is not independently provable.

5. Confirmed — token trailers exactly match kept-row tokens:

```text
jobkw  78,325
trav   294,979
r8c    297,186
review 188,278
```

All run-6 trail rows have seven TSV fields.

6. Confirmed mechanically — `git merge-tree --write-tree` for all three integration merges exited 0 and generated the exact recorded commit tree. Thus no merge conflict resolution altered code. Git cannot prove who typed code, only that director-side integration was clean merging.

7. Confirmed — fixture provenance. A disposable Git checkout at actual base `c7d3876` generated the fixture mapping exactly:

```text
fixture_exact_match= True
episode_count= 2 identity_rows= 6
```

8. Not confirmed — state-file consistency. [FRONTIER.md](/home/steven/jos-trail6-wd/.claude/FRONTIER.md:5) still says it was updated for run-5, despite describing run-6. [RUN.md](/home/steven/jos-trail6-wd/.claude/RUN.md:5) says “Remaining: terra trail audit + digest + closeout” and retains a resume recipe for already-kept units, while FRONTIER says nothing further is director-autonomous. GATES correctly leaves G25/G26 open.

9. Run-5 lessons: partially followed. The central new rule was followed: a persisted one-pass full mirror passed before review launch, with matching raw log and timestamp evidence. Filed reports and token fields also exist. However, the required current-state/staleness discipline was not fully followed, and no durable evidence shows the required ≥60-second `pgrep` launch verification.

## Attention

1. `trav` and `r8c` were developed from `c7d3876` (code baseline `6e9b0e4`), not the reviewed run-5 head. This is disclosed in RUN’s unit table and the Sol review, but obscured by shorthand such as “`84b9676` + … units.” The final integration is validly based on `84b9676` and was exactness-reviewed, but G25 reversal would require reconstructing/reviewing the integration; only jobkw is directly dependent on run-5.

2. The new `_build_snapshot_cache_capacity()` `ValueError` is vacuous: `max(3, snapshot_count) * routes` is necessarily at least `snapshot_count * routes`. It is harmless but provides no fail-fast protection.

3. DATA-5 is only partially closed as disclosed: `route_edge_history` remains an unbounded retained evidence store. The reviewer’s 30-day RSS observation is also slightly higher on head (441,028 KB vs 437,344 KB), so no whole-run memory-improvement conclusion is supported.

4. First attempts were cosmetically labelled `· retry 1`. The trail clarifies the real count and tokens support one attempt each, but this is avoidable provenance noise.

5. The claimed “filed BEFORE push” condition lacks a retained push receipt. Trail order plus mirror/launch timing supports the intended sequence, but not the exact push time.

6. State-file cleanup is incomplete: FRONTIER’s run identifier and RUN’s active-work/resume wording are stale or contradictory after `g26-parked`.

Auditor model: gpt-5.6-terra@high