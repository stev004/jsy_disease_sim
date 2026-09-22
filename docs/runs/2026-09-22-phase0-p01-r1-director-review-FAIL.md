# P0-1 corrective attempt 2 — director acceptance FAIL

This is the director's implementation acceptance review, not the independent Sol scientific exit verdict. The candidate is NOT KEPT and has not been pushed. No campaign ran.

Checkpoint: `289429cbdd40645aa8c4fcc2d3da498876f004a7`, parent `1fe0b970ba834bd0e5ae69d5ee244e609a41445a`, branch `codex/v13-p0-1-recovery`.
Source SHA256: `a02d188b22776e25c40b81ceee83e4b8b0b16dc227fd18d67a285891b2ce4c8a`.
Test SHA256: `df1fcba97493aa79f801565e7dd0b2e04ab5c4ae58bbd48c444abb165bc924f0`.

Scope is two modified files, +1120/-36 lines; YAML unchanged. Full modified code and tests were inspected. The adapter, strict declaration checks, measured aggregate evidence, persistence flow, portable input and immutable bundle creation materially improve attempt 1.

## Remaining blocker

`_namespace_passes(object(), object(), actual_run_config, actual_observation_config)` returns **True**. Missing `result.config` is replaced with requested configuration; missing `observation_rng` diagnostics is accepted. Required evidence is therefore assumed instead of measured. The final correction must require actual result metadata and existing RNG diagnostics, returning failure for missing, mismatched or malformed metadata. Its mocks must represent the real result contract.

An interim concern about passing CampaignConfig (which contains truth and target seeds) into the fitter was closed by Luna before returning. The director re-probed the final source: `BLIND_FITTER_ACCEPTS_FULL_CONFIG False`. It is NOT an outstanding finding. Preserve that fix and opaque candidate hashes.

Actual OutbreakRunConfig and ObservationConfig constructors completed in a director probe without parent generation, simulation or observation transforms. The executor orchestration test substitutes those constructors; strengthen it to exercise real constructors with expensive operations mocked, and assert per-target persistence before truth join.

## Dependency and minor wording

P01CampaignResult omits the locally created candidate latent cache. The P0-2 brief explicitly owns exposing/reusing it, without extra latent runs. Do not implement P0-2 in this correction.

Bundle creation correctly rejects nonempty output, but its error says the destination 'must be nonempty'. Correct the reversed wording only.

## Verification limits

Director final-byte verification: **21 focused tests passed**, plus the namespace probe above and clean diff check. Executor transcript: two full runs, each **430 passed / 4 skipped / 15 warnings**, final static/mypy/relocation checks PASS. The first full run interleaved a diagnostic transcript; the second completed in 825.48 seconds. The full runs preceded the final fitter-signature removal and test additions. Contrary to the report's phrase 'test-only additions', the late change also touched source. Final 21-test/static checks cover those bytes; do not attribute the earlier full suite to the final checkpoint.

Initial failing-before evidence is a collection error importing a new ExecutionEvidence symbol, not per-defect behavioral proof. Original director probes remain filed for attempt 1. The next correction must demonstrate an actual failing assertion for the remaining namespace defect before changing implementation.

Primary evidence: `docs/runs/2026-09-22-phase0-p01-r1-evidence.log`, `...-r1-director-probes.log`, `...-r1-director-probes.txt`, `...-r1-luna-report.md`. Session `01a0c660-467d-7612-b485-c73a57eed9bc`; tokens **505682**.

Next: final P0-1 implementation attempt 3/3, same isolated worktree and unchanged scientific declaration. No campaign authorization, numerical retuning, main code merge or filter retry.
