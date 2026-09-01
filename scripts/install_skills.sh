#!/usr/bin/env bash
# Install the JOS orchestration skills (foreman, closeout, dev-delegate) into ~/.claude/skills so the
# absolute paths used throughout .claude/*.md (e.g. ~/.claude/skills/foreman/scripts/fm.sh) resolve.
#
#   scripts/install_skills.sh            # link (Linux/macOS/WSL) or copy (Git Bash on Windows), keep existing
#   scripts/install_skills.sh --force    # replace existing non-link installs with the repo version
#   INSTALL_MODE=copy|link               # override auto-detection
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
dest="${HOME}/.claude/skills"; mkdir -p "$dest"
force="${1:-}"
os="$(uname -s 2>/dev/null || echo unknown)"
mode="${INSTALL_MODE:-}"
if [ -z "$mode" ]; then
  case "$os" in MINGW*|MSYS*|CYGWIN*) mode=copy ;; *) mode=link ;; esac
fi
is_wsl=0; grep -qi microsoft /proc/version 2>/dev/null && is_wsl=1
echo "os=$os mode=$mode wsl=$is_wsl repo=$here"
case "$here" in /mnt/[a-z]/*) echo "WARNING: repo is on the Windows filesystem ($here); clone inside WSL (e.g. ~/jsy_disease_sim) for sane I/O speed" ;; esac

# vendored fm.sh must parse and be executable before anything is installed
bash -n "$here/.claude/skills/foreman/scripts/fm.sh"
chmod +x "$here/.claude/skills/foreman/scripts/fm.sh"

install_one() {
  local skill="$1" src="$here/.claude/skills/$1" tgt="$dest/$1"
  if [ -L "$tgt" ]; then
    if [ "$mode" = link ]; then ln -sfn "$src" "$tgt"; echo "relinked $skill"; else rm -f "$tgt"; cp -R "$src" "$tgt"; echo "copied   $skill (replaced link)"; fi
  elif [ -e "$tgt" ]; then
    if [ "$force" = "--force" ]; then rm -rf "$tgt"; if [ "$mode" = link ]; then ln -s "$src" "$tgt"; echo "replaced $skill (link)"; else cp -R "$src" "$tgt"; echo "replaced $skill (copy)"; fi
    else echo "kept     $skill (existing $tgt; pass --force to replace with the repo copy)"; fi
  else
    if [ "$mode" = link ]; then ln -s "$src" "$tgt"; echo "linked   $skill"; else cp -R "$src" "$tgt"; echo "copied   $skill"; fi
  fi
  [ -f "$tgt/SKILL.md" ] || { echo "ERROR: $tgt/SKILL.md missing after install" >&2; exit 1; }
}
for skill in foreman closeout dev-delegate; do install_one "$skill"; done
chmod +x "$dest/foreman/scripts/fm.sh" 2>/dev/null || true

echo "--- prerequisites ---"
missing=0
for bin in git uv python3 node npm gh codex claude; do
  if command -v "$bin" >/dev/null 2>&1; then echo "ok      $bin ($(command -v "$bin"))"; else echo "MISSING $bin"; missing=1; fi
done
node -v 2>/dev/null | grep -Eq '^v(2[0-9]|[3-9][0-9])' || echo "WARNING: node 20+ required for the frontend gate"
gh auth status >/dev/null 2>&1 && echo "ok      gh auth" || echo "TODO    gh auth login"
if command -v codex >/dev/null 2>&1; then codex login status >/dev/null 2>&1 && echo "ok      codex login" || echo "TODO    codex login"; fi
[ "$mode" = copy ] && echo "NOTE: copy mode — re-run this script after pulling skill changes."
[ $missing -eq 0 ] && echo "install complete" || { echo "install complete with missing prerequisites (see docs/desktop-setup.md)"; exit 2; }
