#!/bin/bash
# fm — foreman state helper. One command per bookkeeping op, to conserve director context.
# Per-repo setup (once): git -C <repo> config foreman.branch <state-branch>   (default: repo's default branch)
set -euo pipefail

cmd="${1:?usage: fm.sh <cmd> ...}"

if [ "$cmd" = "exec" ]; then
  # fm exec <workdir> <model> <effort> <brief-file> <log-stem> — launch codex; prints confirmation once the log exists
  wd="${2:?workdir}"; model="${3:?model}"; effort="${4:?effort}"; brief="${5:?brief-file}"; stem="${6:?log-stem}"
  cd "$wd"
  CODEX_BIN="${CODEX_BIN:-$(command -v codex 2>/dev/null || echo /opt/homebrew/bin/codex)}"
  nohup "$CODEX_BIN" exec --sandbox workspace-write \
    -c sandbox_workspace_write.network_access=true \
    -m "$model" -c model_reasoning_effort="$effort" \
    -o "${stem}.last.md" \
    "$(cat "$brief")" < /dev/null > "${stem}.log" 2>&1 &
  pid=$!
  sleep 5
  if kill -0 "$pid" 2>/dev/null && [ -f "${stem}.log" ]; then
    echo "launched pid=$pid log=${stem}.log"; exit 0
  else
    echo "LAUNCH FAILED — log tail:"; tail -5 "${stem}.log" 2>/dev/null; exit 1
  fi
fi

repo="${2:?usage: fm.sh <cmd> <repo> ...}"
branch="$(git -C "$repo" config foreman.branch 2>/dev/null || git -C "$repo" symbolic-ref --short HEAD)"
wt="${FM_STATE_ROOT:-${TMPDIR:-/tmp}}/fm-$(basename "$repo")-state"
# State branch checked out in the repo itself (the normal case once state lives on main): work in place, no worktree.
if [ "$(git -C "$repo" symbolic-ref --short HEAD 2>/dev/null)" = "$branch" ]; then wt="$repo"; fi

ensure_wt() {
  [ "$wt" = "$repo" ] && return 0
  if [ ! -d "$wt/.git" ] && [ ! -f "$wt/.git" ]; then
    git -C "$repo" worktree prune
    git -C "$repo" worktree add "$wt" "$branch" >/dev/null 2>&1
  fi
  git -C "$wt" pull --ff-only --quiet 2>/dev/null || true
}

case "${1:?}" in
  state)  # fm state <repo> — ensure the persistent state worktree, print its path
    ensure_wt; echo "$wt" ;;
  log)    # fm log <repo> <phase> <decision> <why> <evidence> <result> — append trail row, commit, push
    ensure_wt
    ts="$(date +%Y-%m-%dT%H:%M)"
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$ts" "$3" "$4" "$5" "$6" "$7" | tr -d '\r' >> "$wt/.claude/decisions.tsv"
    git -C "$wt" add .claude/decisions.tsv
    git -C "$wt" commit -q -m "trail: $3 — ${4:0:60}"
    git -C "$wt" push -q
    echo "logged @ $(git -C "$wt" rev-parse --short HEAD)" ;;
  sync)   # fm sync <repo> <message> — commit+push all state edits made in the worktree
    ensure_wt
    git -C "$wt" add -A
    git -C "$wt" commit -q -m "$3" || { echo "nothing to commit"; exit 0; }
    git -C "$wt" push -q
    echo "synced @ $(git -C "$wt" rev-parse --short HEAD)" ;;
  *) echo "unknown cmd: $1 (state|log|sync|exec)"; exit 1 ;;
esac
