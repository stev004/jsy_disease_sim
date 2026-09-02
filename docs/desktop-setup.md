# Desktop handoff — agent runbook for the Windows desktop

**Audience: the Claude Code agent running on the desktop.** Steven does the three items in §0 and nothing else; every other step here is yours to execute, verify, and write back. Do not ask Steven to run shell commands you can run yourself; ask him only for logins, reboots, and the G8 decision.

## §0 — What Steven does (two things)
1. Clone `stev004/jsy_disease_sim` in the Claude Code app and open it. (Codex CLI and GitHub CLI are already installed on this desktop; the app brings git.)
2. Say: **"set up this machine per docs/desktop-setup.md, then report."** Later, decide G8 when asked.

Everything else below is the agent's job, including installing whatever tools are missing. `scripts/bootstrap-windows.ps1` remains as an optional all-in-one for a bare machine; on this desktop the agent should just install the gaps.

## §1 — Agent procedure (native first, WSL only on proven need)
Native Windows = Git Bash under Claude Code. It is the easiest path *if* Codex's sandbox and the background launcher work here; that is a fact to probe, not assume.

1. **Orient.** Read `CLAUDE.md` → `.claude/FRONTIER.md`, `GATES.md`, `DIRECTOR.md`. Confirm `git rev-parse HEAD` is on `main` and `git status` is clean.
2. **Tools + skills.** Run `scripts/install_skills.sh` (copy mode on Git Bash). Must end `install complete`, exit 0. Install what it reports missing yourself: `winget install --id astral-sh.uv -e --silent`, `winget install --id OpenJS.NodeJS.LTS -e --silent` (then open a fresh shell or re-read PATH), `npm i -g @openai/codex` only if codex is absent. Logins (`gh auth login`, `codex login`) are Steven's: ask once, in one message, for all of them together, then re-run the installer.
3. **Probe.** `scripts/probe-native.sh`. It checks tools/logins, runs a real sandboxed `codex exec`, launches one unit through `fm.sh exec` and waits for its report, and smokes `uv`/`jos demo`/frontend.
   - `NATIVE_PROBE PASS` → **this box runs the loop natively.** Go to §2.
   - `NATIVE_PROBE FAIL` on the codex-sandbox or fm.sh lines → go to §3 (WSL2). Any other FAIL line → fix that item and re-probe; do not jump to WSL for a missing login.
4. **Full gate once, locally:** `uv run --locked pytest -q` (≈10 min), `uv run ruff check .`, `(cd frontend && npm run test && npm run build)`. Paste the last lines in your report.
5. **Write back** (`fm.sh log` + `fm.sh sync`): one trail row `desktop-transfer` with the probe verdict, tool versions (`uv --version`, `node -v`, `codex --version`, `claude --version`), and free memory (`wmic OS get FreePhysicalMemory` or `systeminfo | findstr Memory`). Update FRONTIER "Off-repo assets → Desktop transfer" from **not done** to done with the date and mode (native|wsl).
6. **Report to Steven** in ≤8 lines: mode, gate results, and any open gate questions with their defaults. *(Historical: the original G8 default said `--workers 12`; superseded by the 2026-09-02 memory measurements — see §2.)*

## §2 — Running P4 here (native)
- Memory check before launch: ≥ 24 GB free. Measured 2026-09-02 on this box (post-R6 bounded snapshot cache, merged `a6fdc19`): a 180-day full-mode replicate ≈ 3.3 GB steady per worker (pre-R6 it grew ~66 MiB/simulated-day to ~10 GB — the old "1.8 GB" figure was wrong); `--workers 7` fits the 26 GB WSL cap with margin. Kill hygiene: `pkill -f 'jos ensemble run'` AND `pkill -f 'multiprocessing.spawn'`.
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
