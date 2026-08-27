# Verification archive

The repository keeps generated simulation outputs outside Git. A C3 verification
archive is the compact index that makes that policy auditable. It records:

- the Git commit and whether the worktree was dirty;
- parent M2, M3 and M4/C2 logical hashes;
- source-manifest hashes and layer hashes;
- exact command results and benchmark metadata;
- an external-retention policy; and
- SHA-256/size records for retained archive summaries.

`write_verification_archive()` requires a clean worktree by default. It writes
`manifest.json` plus `verification_summary.json` under an archive ID and refuses
to reuse that ID for different content. `verify_verification_archive()` checks
the retained files and can enforce expected parent hashes and an expected Git
commit.

The archive is not a replacement for retaining the full generated M2/M3/M4/M5,
ensemble and calibration directories. Those directories may be ignored by Git,
but the archive, the generated-output bundle, the dependency lock and the
repository commit must be retained together for reproducibility. Runtime,
peak-memory and process-pool measurements are benchmark metadata, not logical
simulation content.
