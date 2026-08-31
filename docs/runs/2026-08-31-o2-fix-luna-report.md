     monkeypatch, m6_network, m6_base_config, m6_parameters, testing_enabled

tokens used
140,177
Implemented the O2 fix.

- Changed only the diagnostics denominator descriptor in [travel.py](/private/tmp/jsy-o2-fix-wt/src/jersey_outbreak/travel.py:2712).
- Added the staggered-arrival regression test in [test_m8_travel.py](/private/tmp/jsy-o2-fix-wt/tests/test_m8_travel.py:339).
- Alias computation and arrival logic unchanged.

Failing-then-passing evidence:

```text
Base: 1 failed, 12 deselected in 10.38s
AssertionError: assert 2 == 'arrived visitor identities by date'
```

```text
Fixed: 1 passed, 12 deselected in 3.93s
```

Verification:

```text
215 passed, 4 warnings in 694.55s
All checks passed!
105 files already formatted
```

`git diff --name-only` contains only:

```text
src/jersey_outbreak/travel.py
tests/test_m8_travel.py
```

`git diff --stat`:

```text
 src/jersey_outbreak/travel.py |  2 +-
 tests/test_m8_travel.py       | 21 +++++++++++++++++++++
 2 files changed, 22 insertions(+), 1 deletion(-)
```

`uv sync --locked` completed successfully. No commit made.
