TRAIL AUDIT: ATTENTION (9 items)

Auditor: **GPT-6 Astra, high reasoning; Codex family**, independent of the Claude director. Scope: decisions.tsv rows **323–355**, at `4bcf9648c91e7704c503325802f1367d3230d7c4`. All times below are BST. No files changed; no tests, simulations, commits, pushes or subagents.

1. **HIGH — `popgen-fix-audit-launch`, `popgen-fix-accepted`: the recorded mirror is incomplete.**  
   The [popgen mirror](docs/runs/2026-09-26-popgen-fix-ci-mirror.log) genuinely records **468 passed, 4 skipped**, plus formatting/checking two files, mypy over one source file, and ten focused tests. It does **not document the complete verify-job gate** required by DIRECTOR.md: lock check, compileall, repository-wide Ruff, the pinned mypy module list, demo/generator CLI checks, relocation and final cleanliness checks. The preceding Phase-0b mirrors document that broader surface; they cover an earlier revision.  
   **Reconcile:** describe this as partial verification, retain any missing transcript if one exists, and complete the required mirror before treating the protected-module change as fully verified.

2. **HIGH — `ui-integration`, `popgen-fix-audit-launch`, `g33-merged`: filing-order violations.**  
   The initial UI integration review launched at **18:24:02 on September 25**, using `/home/steven/jos-ui-integ-mirror.log`; that mirror was never filed in the audited git history. The popgen audit launched at **10:08:36 on September 26**, but its mirror was first filed at **10:12:45**, in `15d273dc801c9c9b3bcc0803026eb1b6402de501`. G33’s merge mirror was first filed in `59842cb7aa797ffbb3d32be22c6eeaf46f44ade0`, together with a receipt already showing the merge published on `main`.  
   These are **filing-order failures**, not evidence that tests ran after review/push: the WSL mirrors had completed beforehand.  
   **Reconcile:** acknowledge the exceptions explicitly; preserve the distinction between “PASS existed locally” and “PASS was filed before the action.”

3. **MEDIUM — `phase0b-exit-FAIL`: current-state files contradict the completed trail.**  
   [RUN.md](.claude/RUN.md) still opens with “Phase 0b: not run — frozen, implementation next,” retains implementation **0/3**, and says main code remains the September 21 baseline. [FRONTIER.md](.claude/FRONTIER.md) retains that obsolete baseline and an open G31 despite its newer live override. [REPO-MAP.md](.claude/REPO-MAP.md) says the harness merge is still mirroring. [GATES.md](.claude/GATES.md) says both “not run” and “FAIL” in its opening paragraph; closed G32/G33 remain under “Open” with unreconciled instructions.  
   Git establishes the latest code merge on main as `862e440cfc311bd2b4f87b2af4b6ab145ddb2a14`; subsequent main changes are state/documents.  
   **Reconcile:** rewrite the active state consistently, separating historical gate text from current instructions.

4. **MEDIUM — `phase0b-exit-FAIL`: the failure-mode document adds an unsupported causal conclusion.**  
   The [failure-mode document](docs/research/v1_3/2026-09-26-phase0b-failure-mode.md) says “nothing here is new analysis,” but adds **“Grid resolution alone is ruled out as the explanation for the Phase-0 failure.”** That conclusion is absent from the exit audit. G34 similarly says “a finer grid made it worse.” Fresh seeds, tighter absolute tolerances and fallback-generated populations prevent isolating grid resolution as the cause of the difference between campaigns.  
   The numerical summaries otherwise agree with the audits, including the all-dimension identification failure for seed 62003.  
   **Reconcile:** retain the observed results; label possible explanations as hypotheses and remove the causal exclusion. Cite the original Phase-0 audit separately for its numbers.

5. **MEDIUM — `popgen-fix-accepted`: the identity evidence does not cover every explicitly promised pin.**  
   [G32-A](.claude/GATES.md) requests unchanged M2/M3 hashes including **full-mode and validation pins**. The documented sweep covers 166 CI seeds; the golden-hash tests cover CI/scaled cases. I found no retained full-mode/validation-pin comparison in the inspected evidence. Sol’s success-path reasoning supports general preservation, but does not document those specific comparisons.  
   **Reconcile:** distinguish the demonstrated CI/scaled coverage from the broader claim, and file the promised pin evidence or explicitly disposition that outstanding acceptance requirement. This is an evidence gap, not an observed regression.

6. **MEDIUM — eight UI completion phases: 1,295,185 tokens are omitted.**  
   Each following row records **0**, while its corresponding `/home/steven/jos-*.log` has a `tokens used` trailer:

   | Row phase | Log stem | Tokens |
   |---|---|---:|
   | `ui-u1-corrective-kept` | `jos-ui-u1r2` | 73,969 |
   | `ui-u4-kept` | `jos-ui-u4` | 191,898 |
   | `ui-u2-kept-u3-launch` | `jos-ui-u2` | 202,748 |
   | `ui-u4-corrective-kept` | `jos-ui-u4r1` | 85,076 |
   | `ui-u3-kept` | `jos-ui-u3` | 227,603 |
   | `ui-integration` | `jos-ui-u5` | 179,799 |
   | `ui-integration-corrective-kept` | `jos-ui-integfix` | 275,861 |
   | `ui-integration-corrective2-kept` | `jos-ui-integfix2` | 58,231 |

   The scoped token column totals **2,533,174**; including these completions gives **3,828,359**. Nonzero recorded values match their corresponding trailers. Launch-row zeros are not additional omissions when completion usage is recorded later.  
   **Reconcile:** append token-correction rows with session/log references.

7. **MEDIUM — UI acceptance/write-backs: durable evidence is incomplete.**  
   The UI implementers’ `.last.md` reports survive in WSL but were not filed under `docs/runs/`. Unit mirrors likewise remain outside git. The `ui-u4-accepted` claim of fresh typecheck/test/build on `9cb9e4051f3f147dc7eff9b1764d3ad69fc5efd4` has no retained matching transcript identified; the available U4 corrective mirror covers its parent. Later integration verification mitigates the final-code risk but does not substantiate that earlier claim. Browser checks are self-attested without cited captures; the G33 gate’s “each … both themes” wording is broader than the trail’s explicit coverage. The two disclosed silent WSL launch failures also lack corresponding incident evidence in the scoped trail.  
   **Reconcile:** archive surviving reports/transcripts, narrow unsupported verification wording, and record the failed-launch circumstances without inventing timings.

8. **MEDIUM — `ui-u1-retry1`, `ui-u2-kept-u3-launch`, `ui-integration-legend-fix`: director implementation exceeded the standing role boundary.**  
   The trail expressly discloses director fixes of three, two and seven lines. The last is confirmed by the three-file diff at `474bb53b9e4fdfccfc84720eeff938564481bb27`. DIRECTOR.md permits only a **one-line obvious fix**. The final change received an independent PASS, so author/judge separation was ultimately preserved; the implementation-role exception remains unreconciled.  
   **Reconcile:** acknowledge the exceptions and account for the director corrective in the implementation history. Do not classify reviews automatically as budgeted “peer consults”; I found no established implementation-attempt or timebox overrun in this scoped run.

9. **LOW — `ui-u1-review-BLOCKED`, `phase0b-execute-aborted`, `ui-integration`: incomplete immutable identifiers.**  
   Evidence cells abbreviate filing commits as `3589959` and `18f52b0`; these resolve to `3589959959cf19741d51e870d665711ef2ee10cb` and `18f52b09ea01b7b37319c3130690852bd89f24e8`. The integration row identifies U5 only by its branch; the later receipt resolves it to `9424ca7ca969065ad21ebbde306cf9029df32cfe`.  
   **Reconcile:** append the full identifiers, consistent with the trail’s “abbreviate nothing” rule.

**Verified clean:**

- All **33 scoped rows have seven columns and `[skip ci]` in the decision**. Every concrete evidence path checked exists; all supplied full commit SHAs resolve.
- GitHub `ls-remote` matches all six UI branch receipts, the Phase-0b implementation branch and the popgen branch. GitHub main matches the audited HEAD and contains the G33 merge.
- The final UI PASS was filed at **19:11:46**, before the **19:11:58** UI receipt. Phase-0b and popgen PASS filing commits likewise precede their receipt commits. Those latter receipts lack embedded timestamps, so they provide weaker independent timing evidence.
- The UI review chain ends in PASS at `474bb53b9e4fdfccfc84720eeff938564481bb27`. Its final frontend mirror and the G33 merge mirror record **15 passed, 6 skipped**, typecheck and build success.
- `/home/steven/jos-idsweep.log` matches its filed copy byte-for-byte: **133 IDENTICAL, 19 FALLBACK, 14 BOTH-FAIL**, with no DIFFERENT or REGRESSION entry. Sol’s raw audit log independently records **133 matching M2 comparisons** and **zero normalized comparison errors**, closing the disclosed M2 omission for that sample.
- The two Luna identity stops and director commit are accurately disclosed. The rerun log preserves all four fallback disclosures with M2 IDs and diagnostic digests.
- The rerun records **exit 0, 578 seconds, 4,044 files and checksum verification**. Its log was filed at **10:24:36**, before the exit-audit launch at **10:24:43**. The audit’s 4,043 checksum-listed files are consistent with 4,044 including `SHA256SUMS`.
- The filed exit audit exactly matches its WSL final report. It supports determinate **FAIL**, the accepted same-seed lineage, and G34’s **default STOP**. G34’s options grant no implied permission for another campaign or real-data fitting.
- Every inspected pushed head carries **`[skip ci]`**. That supports the intended suppression of push CI; **it does not establish that no GitHub Actions runs occurred**.