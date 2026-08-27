# Verification archive

The repository keeps generated simulation outputs outside Git. A milestone
verification archive is the compact index that makes that policy auditable. It records:

- the Git commit and whether the worktree was dirty;
- parent M2, M3 and M4/C2 logical hashes;
- source-manifest hashes and layer hashes;
- exact command results and benchmark metadata;
- an external-retention policy; and
- SHA-256/size records for retained archive summaries.

`write_verification_archive()` requires a clean worktree by default and records
the declared milestone (`C3`, `C4`, or a later bounded gate). It writes
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

## Latest verified C3 record

The final C3 archive was created from a clean worktree at Git commit
`658364c7f02cf44f9392116e7db44c94bdb3175a`. Its archive logical hash is
`32627c432c65e89250ee40d68a9382bb9b463f5076015dd6be5e62acab70bba4`.
The record was checked with the expected current commit and parent logical
hashes, including:

- M2: `bc1e30281edc211dd860cd515450029e2e549cf2b33297d679b9c4b6b975296a`
- M3: `b445ee6eb8f366bd07157a1ca8d3f5757892609a5067bf33d5df061b86aad9b7`
- M4/C2: `6ef553d4c640baf0d441e57bcc70322aa622dd69c2429ab6a9d13843b274cfb6`
- source registry: `2a2a10811a5472b97695bda0dd520599e752207a4679696cdf04b16c94e5d13d`

The retained local verification bundle used for this check was
`/private/tmp/jos-c3-verification/jos-c3-final-658364c-v2/`. It is intentionally
outside the repository and must be copied to durable external retention if the
verification record is to be reproduced on another machine. The CLI check is:

```bash
uv run jos verify archive-check \
  --archive /private/tmp/jos-c3-verification/jos-c3-final-658364c-v2 \
  --expected-commit 658364c7f02cf44f9392116e7db44c94bdb3175a
```
