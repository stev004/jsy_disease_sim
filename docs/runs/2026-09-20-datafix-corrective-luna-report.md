Implemented and verified.

- Added `daily_high_risk` content hash to M8 bundle identity.
- Verifier recomputes and validates the persisted hash.
- Added same-root stale-reuse regression test.
- A/B confirms IDs differ and head total is 3 persisted/computed; latent/M4 hashes unchanged.
- Gates pass: 27 targeted, 405 full-suite, Ruff, format, pinned mypy.

Report: [jos-dfcorr.last.md](/home/steven/jos-datafix-wt/jos-dfcorr.last.md)

No commit made.