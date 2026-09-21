# P0-1 director acceptance review — FAIL

This is the director's acceptance review, not the independent Sol exit verdict. Candidate is NOT KEPT. No campaign ran.

Candidate checkpoint: `1fe0b970ba834bd0e5ae69d5ee244e609a41445a`, branch `codex/v13-p0-1-recovery`, not pushed. Before checkpointing, the branch fast-forwarded from `2ab6b10216b46e9599d9cc42c0b00aa9178c0436` to state-only `b78b5bc7071edb3542525c0863dabc661c957ba6`; source/tests/configs were identical between these bases. The checkpoint exists solely to make failing-before/passing-after evidence reproducible.

Final source SHA256: `daaac7517adfa103a69219219dad3f7641fce83ad33b9125ca7b1d1f9eeddfc6`. Final test SHA256: `258d061625b8d2886736724b601305d638cac672fab592b410c380ac4a8855ff`.

Scope: exactly three added paths, 1,778 lines (1,292 module; 129 config; 357 tests). Full source and tests inspected, followed by probes on the final bytes. Executor reports 13 focused tests and 422 full-suite tests passed, four skipped; the transcript shows further declaration/calendar adjustments after the full-suite run, followed by focused/static checks. That suite result is regression evidence, not acceptance of the final candidate.

## Confirmed acceptance gaps

1. **Missing simulator adapter.** The module contains pure scoring/serialization and an always-blocked `execute_campaign`, but no callable target/candidate generation path, actual run-config construction, measured runtime call counters, or end-to-end P0-1 orchestration. Keeping CLI execution blocked is correct; omitting the implementation that later arms must reuse is not. Implement it now and test it through mocks, without running a campaign. The original brief did not distinguish this clearly enough; the corrective makes it explicit.
2. **Incomplete frozen-declaration enforcement and config provenance.** Final code rejects changed dates/horizons (executor closed these during its last pass), but changing `identifiability.profile_gap` or `acceptance.descriptive_coverage_minimum` is still accepted and silently ignored. Other declaration-only sections need the same validation. `candidate_config_hash` manually describes a subset of hypothetical parameters, without actual per-replicate seeds/configs. The record must match what the adapter actually constructs.
3. **Missing evidence can yield PASS.** `evaluate_p01` accepts five undeclared target seeds with default namespace flags and no measured workload, yet emits `PASS`. Required execution evidence must be explicit and verified; missing counters/namespace/calendar/config evidence cannot mean success. Complete-grid count alone does not prove all declared runs completed correctly.
4. **Hashing is not durable pre-join persistence.** `join_truth_evaluation` checks only a hash string; no code writes the blinded estimate before truth is joined. Implement and mock-test the required ordering, with failed persistence preventing truth evaluation.
5. **Tests depend on the director's home directory.** `PREDECLARATION_PATH = Path('/home/steven/jos-p0-predeclaration.md')` makes the tests machine-specific and masks portability in the current environment. The updated branch now includes the committed predeclaration; use repository-relative inputs or temporary fixtures. No external-home dependency.
6. **Bundle overwrite invalidates checksums.** A second `write_research_bundle` into the same directory is accepted; it hashes the prior `SHA256SUMS` into the new file and then overwrites it. Fail closed on nonempty destinations (no new resume mode), preserve existing bytes on failure, and verify every listed checksum from a fresh bundle.

## Final-byte probe output

```
ALTERED_DECLARATION_REJECTED start_date: CampaignError
ALTERED_DECLARATION_REJECTED duration_days: CampaignError
ALTERED_DECLARATION_ACCEPTED profile_gap
ALTERED_DECLARATION_ACCEPTED coverage_minimum
NO_MEASURED_WORKLOAD_UNDECLARED_TARGET_SEEDS_STATUS PASS
REPEATED_BUNDLE_WRITES_ALLOWED True
SECOND_HASH_LIST_INCLUDES_ITS_OLD_SELF True
```

Evidence: `docs/runs/2026-09-22-phase0-p01-attempt1-director-probes.log`, probe source alongside it, and `docs/runs/2026-09-22-phase0-p01-attempt1-evidence.log`. The first provisional inspection's date/horizon findings were closed by the executor before final delivery and are not outstanding.

Disposition: one bounded Luna@xhigh corrective in the same unit/worktree, attempt 2 of 3. Preserve all scientific choices and all protected contracts. No P0-2/P0-3 implementation and no campaign execution in this corrective. Main code remains unchanged; merges stay Steven-gated.