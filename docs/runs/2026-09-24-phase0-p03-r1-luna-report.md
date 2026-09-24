**Implementation verdict: PASS.** The BLOCKING and MINOR findings are addressed in the two authorized files. This is an implementation result, not a scientific Phase-0 verdict. No real campaign was run.

### Findings

- **BLOCKING — bundle retention:** [phase0_campaign.py](/home/steven/jos-p0-3-wt/src/jersey_outbreak/phase0_campaign.py:3840) copies the 15 persisted blind estimate records byte-for-byte, retains all target and candidate observation tables with table digests, and adds raw P0-1 truth diagnostics. The bundle index maps outputs and retained files to recomputation tasks. Publication remains staged and atomic; `SHA256SUMS` now covers nested files and verifies exact file coverage. P0-3 publishes vectors for all nine cells. The mocked all-arms test independently recomputes a full P0-1 surface and tie record, P0-2B \(E_i\), P0-3 ridge hashes, and the P0-1 truth gate from bundle files. **Test:** `test_p0_3_all_arms_mocked_execute_reuses_builds_and_rejects_corrupt_blind_readback`; focused module output: **42 passed**.

- **MINOR — transform count:** [phase0_campaign.py](/home/steven/jos-p0-3-wt/src/jersey_outbreak/phase0_campaign.py:60) defines the planned P0-3 transform count as 27, exposes it through `WorkloadPlan`, and checks measured transforms against that field at [line 4217](/home/steven/jos-p0-3-wt/src/jersey_outbreak/phase0_campaign.py:4217). **Test:** `test_p0_1_config_and_workload_are_exact`; the focused module passed 42/42.

- **MAJOR — ruling flag:** No code change was needed. The missing-ruling error plainly names `--ruling`; `test_execute_requires_both_verified_authority_files` asserts the message `execute requires a verified G29 ruling supplied with --ruling`. Any step-6 execution command must include `--ruling /tmp/g29-ruling.md`; no campaign command was run.

### Mocked bundle contents

The all-arms test bundle at `/tmp/jos-p0-3-r1-cold/test_p0_3_all_arms_mocked_exec0/all-arms-bundle` contains **633 files**: 19 root files and 614 nested files. `SHA256SUMS` has 632 entries and the cold test verifies there are no unlisted or missing files.

The root files are:

`SHA256SUMS`, `blind_estimate_manifest.json`, `bundle_index.json`, `campaign_config.sha256`, `campaign_config.yaml`, `campaign_summary.json`, `candidate_loss_surfaces.json`, `g29_ruling.md`, `g29_ruling.sha256`, `input_hashes.json`, `p0_1_candidate_provenance.json`, `p0_1_recovery.csv`, `p0_1_truth_diagnostics.json`, `p0_2_loss_surfaces.json`, `p0_2_misspecification.csv`, `p0_2_provenance.json`, `p0_3_profile.json`, `predeclaration.sha256`, `seed_ledger.json`.

Nested files comprise:

- `blind_estimates/{p0_1,p0_2a,p0_2b}/<target_seed>.json`: **15 total**, five per arm.
- `observed_tables/p0_1`: **248** files, including five targets and 243 candidate tables.
- `observed_tables/p0_2a`: **243** candidate tables.
- `observed_tables/p0_2b`: **81** candidate tables.
- `observed_tables/p0_3`: **27** candidate tables.

### Verification

- Dry run reported **198 cells, 59 latent calls, 599 observation transforms, 8 builds**, including **27 planned P0-3 transforms**.
- Ruff check and format check passed; mypy reported no issues; compileall succeeded.
- Hash comparison against the module loaded from `git show 29f43d1` found identical hashes: P0-1 target **5/5**, P0-1 candidate **81/81**, P0-2A **81/81**, P0-2B **27/27**, P0-3 cell **9/9**, and P0-3 ridge prediction **3/3**. The blind estimate hash remains `2ebc1f18a5dac62ec1432fc696e8c885c63cd53e818b8d8fbce0bcf7dad7421a`.
- Full suite: **452 passed, 4 skipped, 15 warnings** in 823.15 seconds. The known job-ordering flake did not occur.
- `git diff --check` passed. Diff: **2 files changed, 917 insertions(+), 35 deletions(-)**. HEAD remains `29f43d131f568868259d64a459f889e027d31e21`; only the two authorized files are modified. No commit or push was made.

Sequential evidence log: [jos-p0-3-r1-evidence.log](/tmp/jos-p0-3-r1-evidence.log).