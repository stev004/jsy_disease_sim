# One-shot Windows host preparation for JOS on WSL2. Run once in an elevated PowerShell:
#   Set-ExecutionPolicy -Scope Process Bypass; .\scripts\setup-windows.ps1
# Installs WSL2 + Ubuntu and writes %USERPROFILE%\.wslconfig so WSL can use most of the RAM/cores
# (default WSL2 caps memory at 50% of RAM, which would halve the parallel replicate count).
$ErrorActionPreference = "Stop"
$totalGB = [math]::Floor((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
$cores   = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
$memGB   = [math]::Max(8, $totalGB - 4)          # leave ~4 GB for Windows
$cfg = @"
[wsl2]
memory=${memGB}GB
processors=$cores
swap=8GB
localhostForwarding=true
"@
$path = Join-Path $env:USERPROFILE ".wslconfig"
if (Test-Path $path) { Copy-Item $path "$path.bak" -Force }
Set-Content -Path $path -Value $cfg -Encoding ASCII
Write-Host "Wrote $path (memory=${memGB}GB processors=$cores)"
if (-not (Get-Command wsl -ErrorAction SilentlyContinue) -or -not (wsl -l -q 2>$null | Select-String -Quiet "Ubuntu")) {
  Write-Host "Installing WSL2 + Ubuntu (a reboot may be required, then run this script again)..."
  wsl --install -d Ubuntu
} else {
  wsl --shutdown
  Write-Host "Ubuntu present; WSL restarted with the new config. Next: open Ubuntu and follow docs/desktop-setup.md section 2."
}
