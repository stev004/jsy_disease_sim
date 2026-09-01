Implemented B02 in the bounded scope.

Contract:

- Added `cohort_detected_infections`
- Added `cohort_ascertainment_fraction`
- Added `cohort_ascertainment_censored`
- Added `cohort_detection_window_end_date`
- Censored cohort fractions are explicitly `null`; detection window is infection/symptom anchor plus maximum detection delay.
- Removed daily `ascertainment_fraction`.
- Preserved aggregate diagnostic `ascertainment_fraction` as horizon-wide detected/infected ratio.
- Parish/age tables have no analogous ratio.
- Observation manifest schema bumped `1.3 → 1.4`; older versions remain readable.

Verification:

- Full backend: `227 passed`, 4 pre-existing warnings.
- Focused regressions: `15 passed`.
- Ruff check: passed.
- Ruff format check: passed.
- `git diff --check`: passed.
- Consumer grep `frontend/src` and `src/jersey_outbreak/api.py`: no legacy-field matches; no frontend changes/tests required.
- Diff: 5 allowed files, `143 insertions / 47 deletions`.
- No commit made.