# Desktop handoff — agent runbook for the Windows desktop

**Audience: the Claude Code agent running on the desktop.** Steven does the three items in §0 and nothing else; every other step here is yours to execute, verify, and write back. Do not ask Steven to run shell commands you can run yourself; ask him only for logins, reboots, and the G8 decision.

## §0 — What Steven does (three things)
1. Open **PowerShell** (Start → type PowerShell) and paste this whole block (the repo is private, so it logs into GitHub first; click through the browser prompts for GitHub, then later Codex and Claude):
   ```powershell
   winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements --silent
   winget install --id GitHub.cli -e --accept-source-agreements --accept-package-agreements --silent
   $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
   gh auth login --web --git-protocol https
   gh repo clone stev004/jsy_disease_sim "$env:USERPROFILE\jsy_disease_sim"
   Set-ExecutionPolicy -Scope Process Bypass -Force; & "$env:USERPROFILE\jsy_disease_sim\scripts\bootstrap-windows.ps1"
   ```
   The bootstrap installs node/uv/codex/claude and the skills, then prints the next command.
2. `cd ~\jsy_disease_sim` then `claude` (log in when the browser opens).
3. Say: **"set up this machine per docs/desktop-setup.md, then report."** Later, decide G8 when asked.

## §1 — Agent procedure (native first, WSL only on proven need)
Native Windows = Git Bash under Claude Code. It is the easiest path *if* Codex's sandbox and the background launcher work here; that is a fact to probe, not assume.

1. **Orient.** Read `CLAUDE.md` → `.claude/FRONTIER.md`, `GATES.md`, `DIRECTOR.md`. Confirm `git rev-parse HEAD` is on `main` and `git status` is clean.
2. **Skills.** `scripts/install_skills.sh` (copy mode on Git Bash). Must end `install complete`, exit 0. Fix anything it reports (missing tool → install it with `winget install --id <id> -e`; login → ask Steven once, in one message, for all logins at once).
3. **Probe.** `scripts/probe-native.sh`. It checks tools/logins, runs a real sandboxed `codex exec`, launches one unit through `fm.sh exec` and waits for its report, and smokes `uv`/`jos demo`/frontend.
   - `NATIVE_PROBE PASS` → **this box runs the loop natively.** Go to §2.
   - `NATIVE_PROBE FAIL` on the codex-sandbox or fm.sh lines → go to §3 (WSL2). Any other FAIL line → fix that item and re-probe; do not jump to WSL for a missing login.
4. **Full gate once, locally:** `uv run --locked pytest -q` (≈10 min), `uv run ruff check .`, `(cd frontend && npm run test && npm run build)`. Paste the last lines in your report.
5. **Write back** (`fm.sh log` + `fm.sh sync`): one trail row `desktop-transfer` with the probe verdict, tool versions (`uv --version`, `node -v`, `codex --version`, `claude --version`), and free memory (`wmic OS get FreePhysicalMemory` or `systeminfo | findstr Memory`). Update FRONTIER "Off-repo assets → Desktop transfer" from **not done** to done with the date and mode (native|wsl).
6. **Report to Steven** in ≤8 lines: mode, gate results, and the G8 question with its default (≥40 replicates, `--workers 12`).

## §2 — Running P4 here (native)
- Memory check before launch: ≥ 24 GB free. Each replicate ≈ 1.8 GB peak, single process; `--workers 12` on the 5800X/32 GB.
- `uv run --locked jos ensemble run --help`; the run itself is gated on G8 in `GATES.md` — do not launch it without the ruling recorded there.
- Background long runs the same way `fm.sh exec` does (`nohup … &`, then prove the pid is alive); never fire-and-forget (DIRECTOR lesson 2026-09-01).
- Evidence dirs go under `~/Documents/JOS_v1_2_*` (new; never the Mac's immutable `JOS_v1*` dirs, which are not on this machine anyway).

## §3 — WSL2 fallback (only if §1.3 said so)
WSL2 is a Linux environment Microsoft ships inside Windows; one install command and a reboot. Use it only because a Linux-first tool (Codex sandbox or the bash launcher) failed natively.
1. Ask Steven to run, in an **elevated** PowerShell: `Set-ExecutionPolicy -Scope Process Bypass; ~\jsy_disease_sim\scripts\setup-windows.ps1` (installs Ubuntu, writes `.wslconfig` = RAM−4 GB / all cores — WSL's default 50 % RAM cap would halve the P4 workers) and reboot if told. Then Steven opens **Ubuntu** from the Start menu and pastes this block (it ends by launching `claude` inside WSL):
   ```bash
   sudo apt update && sudo apt install -y git build-essential curl bubblewrap
   curl -LsSf https://astral.sh/uv/install.sh | sh
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs
   sudo mkdir -p -m 755 /etc/apt/keyrings && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null && sudo apt update && sudo apt install -y gh
   sudo npm i -g @openai/codex @anthropic-ai/claude-code && exec $SHELL
   gh auth login && codex login
   cd ~ && gh repo clone stev004/jsy_disease_sim && cd jsy_disease_sim && scripts/install_skills.sh && claude
   ```
   Clone inside the WSL filesystem (`~/…`), never `/mnt/c/…` (slow I/O; the installer warns).
2. In the WSL `claude` session: repeat §1 steps 1–2 and 4–6 (skip the probe; it is Linux). Memory check: `free -g` should show ≈ 28 GB.

## §4 — Facts the agent must not get wrong
- The RTX 3070 is unused: the workload is CPU numpy, single process per replicate; never propose GPU work (R6 profile, FRONTIER note).
- Bands from the ensemble are stochastic replicate variation, never confidence intervals; ≥40 successful replicates for 2.5/97.5.
- Merges to `main` and tags are Steven's (SHA-first); state-layer commits via `fm.sh sync` are the only agent writes to `main`.
- Vendored skills in `.claude/skills/` are the source of truth here; `install_skills.sh` copies them into `~/.claude/skills/` on Windows, so re-run it after `git pull` changes them.
