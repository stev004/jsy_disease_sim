#!/usr/bin/env bash
# Install the JOS orchestration skills (foreman, closeout, dev-delegate) into ~/.claude/skills
# so that the absolute paths used throughout .claude/ (e.g. ~/.claude/skills/foreman/scripts/fm.sh) resolve.
# Idempotent: symlinks repo copies; existing non-link dirs are left alone unless --force.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
dest="${HOME}/.claude/skills"; mkdir -p "$dest"
force="${1:-}"
for skill in foreman closeout dev-delegate; do
  src="$here/.claude/skills/$skill"; tgt="$dest/$skill"
  if [ -L "$tgt" ]; then ln -sfn "$src" "$tgt"; echo "relinked $skill"
  elif [ -e "$tgt" ]; then
    if [ "$force" = "--force" ]; then rm -rf "$tgt"; ln -s "$src" "$tgt"; echo "replaced $skill"
    else echo "kept existing $tgt (pass --force to replace with the repo copy)"; fi
  else ln -s "$src" "$tgt"; echo "linked $skill"; fi
done
chmod +x "$here/.claude/skills/foreman/scripts/fm.sh"
for bin in git uv node npm gh codex claude; do command -v "$bin" >/dev/null 2>&1 && echo "ok   $bin" || echo "MISSING $bin"; done
