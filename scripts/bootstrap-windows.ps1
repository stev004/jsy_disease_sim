# JOS desktop bootstrap (Windows, native). Run from the clone (the repo is private, so it is cloned first — see
# docs/desktop-setup.md §0):   Set-ExecutionPolicy -Scope Process Bypass -Force; .\scripts\bootstrap-windows.ps1
# Installs the remaining toolchains via winget/npm, (clones if somehow absent), installs the skills, then tells you
# the one sentence to say to Claude Code. Idempotent: re-run safely.
$ErrorActionPreference = "Stop"
function Need($cmd) { -not (Get-Command $cmd -ErrorAction SilentlyContinue) }
$pkgs = @(
  @{cmd="git";  id="Git.Git"},
  @{cmd="node"; id="OpenJS.NodeJS.LTS"},
  @{cmd="gh";   id="GitHub.cli"},
  @{cmd="uv";   id="astral-sh.uv"}
)
foreach ($p in $pkgs) { if (Need $p.cmd) { Write-Host "installing $($p.id)"; winget install --id $p.id -e --accept-source-agreements --accept-package-agreements --silent } else { Write-Host "ok $($p.cmd)" } }
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
if (Need "codex")  { npm install -g @openai/codex } else { Write-Host "ok codex" }
if (Need "claude") { try { irm https://claude.ai/install.ps1 | iex } catch { npm install -g @anthropic-ai/claude-code } } else { Write-Host "ok claude" }
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
$repo = Join-Path $env:USERPROFILE "jsy_disease_sim"
if (-not (Test-Path $repo)) {
  if (Need "gh") { throw "gh missing after install; open a new PowerShell and re-run" }
  gh auth status 2>$null; if ($LASTEXITCODE -ne 0) { gh auth login --web --git-protocol https }
  gh repo clone stev004/jsy_disease_sim $repo
} else { Write-Host "ok repo at $repo" }
$bash = Join-Path (Split-Path (Split-Path (Get-Command git).Source)) "bin\bash.exe"
& $bash -lc "cd '$($repo -replace '\\','/')' && scripts/install_skills.sh"
Write-Host ""
Write-Host "=============================================================="
Write-Host "Now run:   cd $repo ; claude"
Write-Host "and say:   set up this machine per docs/desktop-setup.md, then report"
Write-Host "=============================================================="
