# Desktop transfer — DESKTOP-KQTC6VL — 2026-09-02 — mode: WSL2

Executed per `docs/desktop-setup.md` §1 (native probe) → §3 (WSL2 fallback). Windows checkout and WSL clone both at `340647e77d275a690016d94fa7dbd2e9e50d737e` (`main`).

## Native probe (§1.3) — FAIL → WSL2 route

`scripts/probe-native.sh` verbatim output (Git Bash, native Windows):

```
ok       git
ok       uv
ok       node
ok       npm
ok       gh
ok       codex
ok       claude
ok       gh auth
ok       codex login
FAIL     codex sandboxed exec did not write a file natively
FAIL     fm.sh exec: LAUNCH FAILED — log tail:
Reading additional input from stdin...
Not inside a trusted directory and --skip-git-repo-check was not specified.
FAIL     fm.sh: no .last.md within 3 min
FAIL     uv sync / jos demo
ok       frontend npm ci + typecheck
NATIVE_PROBE FAIL -> follow the WSL2 section of docs/desktop-setup.md
```

The codex-sandbox and fm.sh lines failed — the designated WSL2 trigger (§1.3), not a fixable-item case.

## WSL2 setup (§3, agent-executed; no elevation/reboot needed — WSL2 feature was already enabled via docker-desktop)

- `~/.wslconfig` written: memory=27GB (31 GB physical − 4), processors=16, swap=8GB. WSL sees 26 GB total / 25 free (`free -g`).
- Ubuntu 26.04 LTS installed non-elevated (`wsl --install -d Ubuntu --no-launch`); user `steven` (uid 1000, sudo NOPASSWD), `/etc/wsl.conf` default user.
- Toolchain in WSL: git, build-essential, curl, bubblewrap, nodejs **v22.22.1** + npm 9.2.0 via apt (deviation from the doc's Node 20 nodesource pin: Node 20 is past EOL and nodesource has no Ubuntu 26.04 repo), gh 2.46.0, codex-cli 0.152.1, claude 2.1.258 (npm -g), uv 0.12.9.
- Logins carried from the Windows profile (no re-auth needed): `gh auth login --with-token` from the Windows keyring token (verified `Logged in to github.com account stev004`); `~/.codex/auth.json` and `~/.claude/.credentials.json` copied, chmod 600; installer reports `gh auth` and `codex login` ok.
- Repo cloned to `~/jsy_disease_sim` (WSL filesystem, not /mnt/c) @ `340647e77d275a690016d94fa7dbd2e9e50d737e`; `scripts/install_skills.sh` → `install complete`, exit 0 (link mode).

## Codex sandbox smoke in WSL — PASS

`codex exec --sandbox workspace-write` in a throwaway WSL git dir wrote the requested file (`SANDBOX_SMOKE: WSL_SANDBOX_OK`) — the exact capability that failed natively.

## Full gate (§1.4) in WSL — PASS

```
uv run --locked pytest -q   → 235 passed, 5 warnings in 452.36s (0:07:32)
uv run ruff check .         → All checks passed!
frontend npm run test       → Test Files 2 passed | 1 skipped (3); Tests 15 passed | 6 skipped (21)
frontend npm run build      → ✓ built in 921ms (dist/assets/index-CB6W13kw.js 323.57 kB │ gzip: 103.91 kB)
```

## Versions / machine

uv 0.12.9 (WSL) / 0.12.8 (Windows) · node v22.22.1 (WSL) / v24.13.0 (Windows) · codex-cli 0.152.1 (both) · claude 2.1.258 (both) · gh 2.46.0 (WSL) / 2.87.3 (Windows) · Windows free memory at setup: 18,561,172 KB free of 33,478,184 KB total.

## P4 readiness

The loop runs in the WSL clone (`~/jsy_disease_sim` in Ubuntu). G8 remains open in `GATES.md` (default: ≥40 replicates, `--workers 12`, launch only after ≥24 GB free check). Evidence dirs for new runs go under `~/Documents/JOS_v1_2_*` (WSL home).
