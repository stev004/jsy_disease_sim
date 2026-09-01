# Desktop setup — JOS on the Windows desktop (WSL2)

**Run JOS inside WSL2 (Ubuntu), not native Windows.** Reasons: `fm.sh` is bash; Codex's sandbox is first-class on Linux and experimental on native Windows; Git Bash cannot symlink. WSL2 CPU speed is near-native. The one trap is memory: WSL2 defaults to 50% of RAM, which would cut the P4 parallel replicates from ~12 to ~6 — `scripts/setup-windows.ps1` fixes that.

## 1. Windows host (once, elevated PowerShell)
```powershell
Set-ExecutionPolicy -Scope Process Bypass; .\scripts\setup-windows.ps1
```
Installs WSL2 + Ubuntu if absent and writes `%USERPROFILE%\.wslconfig` (memory = RAM − 4 GB, all logical processors, 8 GB swap). Reboot if it asks, run it again, then open **Ubuntu**. (If you have not cloned yet, get the script by downloading it from GitHub, or run the two lines it contains by hand: write `.wslconfig`, `wsl --install -d Ubuntu`.)

## 2. Ubuntu toolchains (inside WSL)
```bash
sudo apt update && sudo apt install -y git build-essential curl
curl -LsSf https://astral.sh/uv/install.sh | sh                      # uv (installs Python 3.12 on uv sync)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs   # node 20 + npm
(type -p wget >/dev/null || sudo apt install -y wget) && sudo mkdir -p -m 755 /etc/apt/keyrings && wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null && sudo apt update && sudo apt install -y gh
sudo npm i -g @openai/codex @anthropic-ai/claude-code                 # executor + director
exec $SHELL                                                            # reload PATH
gh auth login && codex login
```
Codex's sandbox on Linux needs `bwrap`/landlock; on Ubuntu 22.04+ it works out of the box. If `codex exec --sandbox workspace-write` complains, `sudo apt install -y bubblewrap`.

## 3. Clone INSIDE the WSL filesystem and smoke
```bash
cd ~ && git clone git@github.com:stev004/jsy_disease_sim.git && cd jsy_disease_sim   # ~/…, never /mnt/c/…
uv sync --locked
uv run --locked jos demo --seed 123
uv run --locked pytest -q tests/test_v12_carry_ins.py tests/test_v12_bundle_selftest.py
(cd frontend && npm ci && npm run test && npm run typecheck && npm run build)
```
(SSH key: `ssh-keygen -t ed25519` then add the public key at github.com/settings/keys, or use `gh auth login` with HTTPS and `gh repo clone stev004/jsy_disease_sim`.)

## 4. Install the skills
```bash
scripts/install_skills.sh
```
Symlinks `.claude/skills/{foreman,closeout,dev-delegate}` into `~/.claude/skills/` (copies on Git Bash), verifies the vendored `fm.sh` parses, and reports missing prerequisites and logins. Exit 0 = ready. `fm.sh` finds `codex` on `PATH` (override `CODEX_BIN=`), state worktrees go under `$TMPDIR`/`/tmp` (override `FM_STATE_ROOT=`).

The vendored copies are the source of truth for this repo. If the global skills change on the Mac: `cp -R ~/.claude/skills/{foreman,closeout,dev-delegate} .claude/skills/ && git commit`.

## 5. Start work
`claude` in the repo. `CLAUDE.md` routes to `.claude/FRONTIER.md` (one next action), `GATES.md` (decisions — G8 is the P4 replicate/machine call), `DIRECTOR.md` (rules).

**P4 sizing on this box (5800X 8c/16t, 32 GB, WSL memory ≈ 28 GB):** replicates are single-process, ~1.8 GB peak each → `--workers 12` leaves headroom; check `free -g` inside WSL shows ~28 GB before launching. `jos ensemble run --help` for the flags. The RTX 3070 is unused by this workload.

Off-repo, Mac-only, immutable comparators: `~/Documents/JOS_v1*_full_scale_evidence/` — copy read-only if a comparison needs them; never regenerate into them.
