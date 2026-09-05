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
  brief_text="$(cat "$brief")"
  first_line="$(head -1 "$brief")"
  case "$first_line" in
    TASK:*) task_label="${first_line#TASK: }"; prompt="$brief_text" ;;
    *)
      goal="$(sed -n 's/^GOAL:[[:space:]]*//p' "$brief" | head -1)"
      [ -n "$goal" ] || goal="delegated Codex task"
      task_label="$(basename "$wd") · $goal"
      task_label="${task_label:0:96}"
      printf -v prompt 'TASK: %s\n%s' "$task_label" "$brief_text"
      ;;
  esac
  role="$(sed -n 's/^ROLE:[[:space:]]*//p' "$brief" | head -1)"
  [ -n "$role" ] || role="worker"
  echo "Launching: $task_label | $role | $model@$effort | $wd | log=${stem}.log"
  nohup "$CODEX_BIN" exec --sandbox workspace-write \
    -c sandbox_workspace_write.network_access=true \
    -m "$model" -c model_reasoning_effort="$effort" \
    -o "${stem}.last.md" \
    "$prompt" < /dev/null > "${stem}.log" 2>&1 &
  pid=$!
  sleep 5
  if kill -0 "$pid" 2>/dev/null && [ -f "${stem}.log" ]; then
    echo "launched task=$task_label pid=$pid log=${stem}.log"; exit 0
  else
    echo "LAUNCH FAILED — log tail:"; tail -5 "${stem}.log" 2>/dev/null; exit 1
  fi
fi

if [ "$cmd" = "tokens" ]; then
  # fm tokens <log-stem> — total tokens the codex exec run reported ("tokens used" trailer in <stem>.log); prints 0 if absent
  stem="${2:?log-stem}"
  n="$( { grep -A1 -E '^tokens used' "${stem}.log" 2>/dev/null || true; } | tail -1 | tr -d ', ')"
  case "$n" in ''|*[!0-9]*) n=0 ;; esac
  echo "$n"; exit 0
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
  log)    # fm log <repo> <phase> <decision> <why> <evidence> <result> [tokens] — append trail row, commit, push
    # tokens = executor tokens this row paid for (from `fm.sh tokens <stem>`); director-side tokens are recorded once per run in the digest
    ensure_wt
    ts="$(date +%Y-%m-%dT%H:%M)"
    tok="${8:-}"
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$ts" "$3" "$4" "$5" "$6" "$7" "$tok" | tr -d '\r' >> "$wt/.claude/decisions.tsv"
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
  *) echo "unknown cmd: $1 (state|log|sync|exec|tokens)"; exit 1 ;;
esac
