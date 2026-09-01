Implemented B03 and M02 on `codex/v1.1-release-corrections`.

Version table:

| Family | Version | Authority |
|---|---:|---|
| M5 outbreak | `1.2` | [outbreak_schemas.py](/private/tmp/jsy-repair-wt/src/jersey_outbreak/outbreak_schemas.py) |
| M6 observation | `1.4` | [observation_schemas.py](/private/tmp/jsy-repair-wt/src/jersey_outbreak/observation_schemas.py) |
| M6 ensemble | `1.4` | [ensemble_schemas.py](/private/tmp/jsy-repair-wt/src/jersey_outbreak/ensemble_schemas.py) |
| M7 intervention | `2.1` | [intervention_artifacts.py](/private/tmp/jsy-repair-wt/src/jersey_outbreak/intervention_artifacts.py) |
| M8 travel | `2.2` | [travel_artifacts.py](/private/tmp/jsy-repair-wt/src/jersey_outbreak/travel_artifacts.py) |

`/capabilities` now imports these constants, labels them as current write versions, and keeps `package_version` separate. The frontend mock matches all five values with backend authority documented.

M02 now snapshots resident IDs before travel/slot setup, checks exact sequence and set equality afterward, and derives status from all resident and inactive-slot predicates. See [travel.py](/private/tmp/jsy-repair-wt/src/jersey_outbreak/travel.py:2378).

Verification:

- Backend: `229 passed`
- Frontend tests: `15 passed`, 6 skipped
- Typecheck: passed
- Build: passed
- Ruff check/format: passed
- Capability literal grep: clean
- `git diff --check`: clean
- Reverted M02 behavior: both regression tests failed; restored behavior: 3 focused tests passed
- Diff: 11 files, 152 insertions, 14 deletions
- No commit created.