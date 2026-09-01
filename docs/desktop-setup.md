# Desktop setup — running JOS and its orchestration loop on a second machine

Everything needed is in the repo except toolchains and credentials. `fm.sh` is bash: on Windows use WSL2 (Ubuntu) and clone inside the WSL filesystem, not `/mnt/c`.

## 1. Toolchains
- git · **uv** (`curl -LsSf https://astral.sh/uv/install.sh | sh`) · Python 3.12 (uv installs it on `uv sync`) · **Node 20** + npm (frontend gate) · **gh** (`gh auth login`; CI watching) · **Codex CLI** (`npm i -g @openai/codex`, then `codex login`; the executor) · **Claude Code** (the director).

## 2. Clone and smoke
```bash
git clone git@github.com:stev004/jsy_disease_sim.git && cd jsy_disease_sim
uv sync --locked
uv run --locked jos demo --seed 123
uv run --locked pytest -q tests/test_v12_carry_ins.py tests/test_v12_bundle_selftest.py
(cd frontend && npm ci && npm run test && npm run typecheck && npm run build)
```
Full gate (what CI runs): see `.github/workflows/ci.yml`.

## 3. Install the skills
```bash
scripts/install_skills.sh
```
Symlinks `.claude/skills/{foreman,closeout,dev-delegate}` into `~/.claude/skills/` so `/foreman`, `/closeout`, `/dev-delegate` and the `~/.claude/skills/foreman/scripts/fm.sh` paths in `.claude/*.md` resolve. Prints which prerequisite binaries are missing. `fm.sh` finds `codex` on `PATH` (override with `CODEX_BIN=`).

The vendored copies are the source of truth for this repo; if the global skills change on the Mac, re-copy them here (`cp -R ~/.claude/skills/{foreman,closeout,dev-delegate} .claude/skills/`) and commit.

## 4. Start work
Open Claude Code in the repo. `CLAUDE.md` routes to `.claude/FRONTIER.md` (one next action), `GATES.md` (decisions), `DIRECTOR.md` (rules). For the P4 ensemble: `jos ensemble run --help` (`--workers` ≈ 12 on a 32 GB / 16-thread box; ~1.8 GB per replicate).

Off-repo, Mac-only, immutable: `~/Documents/JOS_v1*_full_scale_evidence/` (comparators; copy read-only if needed, never regenerate into them).
