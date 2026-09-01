#!/usr/bin/env bash
# Decide whether the foreman loop can run natively on this Windows box (Git Bash) or needs WSL2.
# Exit 0 = native OK. Exit 1 = a required piece failed (details printed) -> use the WSL2 path in docs/desktop-setup.md.
set -uo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"; fail=0
say(){ printf '%-8s %s\n' "$1" "$2"; }
for bin in git uv node npm gh codex claude; do command -v "$bin" >/dev/null 2>&1 && say ok "$bin" || { say FAIL "$bin missing"; fail=1; }; done
for t in nohup ps kill date sleep mktemp; do command -v "$t" >/dev/null 2>&1 || { say FAIL "shell tool $t missing (not Git Bash?)"; fail=1; }; done
gh auth status >/dev/null 2>&1 && say ok "gh auth" || { say FAIL "gh not logged in (gh auth login)"; fail=1; }
codex login status >/dev/null 2>&1 && say ok "codex login" || { say FAIL "codex not logged in (codex login)"; fail=1; }
# 1. codex sandboxed exec works natively?
probe="$(mktemp -d)"; ( cd "$probe" && timeout 180 codex exec --sandbox workspace-write -c model_reasoning_effort=low 'create a file named probe.txt containing the word ok and stop' >/dev/null 2>&1 < /dev/null )
[ -f "$probe/probe.txt" ] && say ok "codex exec --sandbox workspace-write (native)" || { say FAIL "codex sandboxed exec did not write a file natively"; fail=1; }
# 2. fm.sh exec launch path works (nohup/background/pid check)?
brief="$probe/brief.md"; echo 'print the word ready and stop' > "$brief"
out="$("$here/.claude/skills/foreman/scripts/fm.sh" exec "$probe" gpt-5.6-luna low "$brief" "$probe/fmprobe" 2>&1)" && say ok "fm.sh exec launch ($out)" || { say FAIL "fm.sh exec: $out"; fail=1; }
for _ in $(seq 1 60); do [ -f "$probe/fmprobe.last.md" ] && break; sleep 3; done
[ -f "$probe/fmprobe.last.md" ] && say ok "fm.sh report file appeared" || { say FAIL "fm.sh: no .last.md within 3 min"; fail=1; }
# 3. python/frontend gate smoke
( cd "$here" && uv sync --locked >/dev/null 2>&1 && uv run --locked jos demo --seed 123 >/dev/null 2>&1 ) && say ok "uv sync + jos demo" || { say FAIL "uv sync / jos demo"; fail=1; }
( cd "$here/frontend" && npm ci --silent >/dev/null 2>&1 && npm run typecheck --silent >/dev/null 2>&1 ) && say ok "frontend npm ci + typecheck" || { say FAIL "frontend gate"; fail=1; }
rm -rf "$probe"
[ $fail -eq 0 ] && echo "NATIVE_PROBE PASS" || echo "NATIVE_PROBE FAIL -> follow the WSL2 section of docs/desktop-setup.md"
exit $fail
