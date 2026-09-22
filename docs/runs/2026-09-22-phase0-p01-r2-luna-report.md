IMPLEMENTATION READY FOR REVIEW

Implemented strict namespace evidence validation in [phase0_campaign.py](/home/steven/jos-p0-1-wt/src/jersey_outbreak/phase0_campaign.py:1868):

- Missing, malformed, mismatched configs/RNG diagnostics now fail closed.
- Validates returned config objects, linked latent result, namespace keys, and fingerprint.
- Aggregate evaluation fails when namespace evidence is incomplete.
- Corrected bundle error wording to “must be empty before writing.”
- Strengthened mocked adapter tests with real constructors, exact seeds/calendars, blind fitter checks, persistence ordering, and write-failure behavior.

Evidence:

- Before correction: assertion failure, `assert True is False` for missing metadata.
- After correction: same regression test passed.
- Phase-0 tests: `22 passed`.
- Dry-run: SHA `ef67fe...3a104`; 198 cells, 59 latent calls, 599 transforms.
- Full suite: `432 passed, 4 skipped, 15 warnings`.
- Pinned mypy: success on 15 files.
- Relocation check: verifier success.
- Ruff, format, compileall, lock, and diff checks passed.

Transcript: [`/tmp/jos-p0-1-r2-evidence.log`](</tmp/jos-p0-1-r2-evidence.log>)

Changed files:

- `src/jersey_outbreak/phase0_campaign.py`
- `tests/test_phase0_campaign.py`

Diff: `203 insertions, 98 deletions`. YAML unchanged. No campaign, pilot, real-data fit, or full-scale run was executed.