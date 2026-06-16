param(
    [switch]$InstallWsl,
    [switch]$InstallOptionalFusion
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Log = Join-Path $PSScriptRoot "INSTALL_LOG.md"

function Write-InstallLog {
    param([string]$Message)
    $stamp = Get-Date -Format o
    Add-Content -LiteralPath $Log -Value "- [$stamp] $Message"
}

Write-InstallLog "windows_bootstrap.ps1 started from $RepoRoot"

if ($InstallWsl) {
    Write-InstallLog "Attempting Microsoft-supported WSL install: wsl.exe --install"
    & wsl.exe --install 2>&1 | Tee-Object -Variable WslOutput
    Write-InstallLog "WSL command output: $($WslOutput -join ' ')"
} else {
    Write-Host "WSL install not attempted. Re-run elevated with -InstallWsl to call: wsl.exe --install"
    Write-InstallLog "WSL install skipped because -InstallWsl was not passed."
}

$Python = (Get-Command py -ErrorAction SilentlyContinue)
if ($Python) {
    $CreateVenv = "py -3.12 -m venv .venv"
    Write-InstallLog "Creating venv with: $CreateVenv"
    Push-Location $RepoRoot
    py -3.12 -m venv .venv
} else {
    $CreateVenv = "python -m venv .venv"
    Write-InstallLog "Creating venv with: $CreateVenv"
    Push-Location $RepoRoot
    python -m venv .venv
}

$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
Write-InstallLog "Upgrading pip: $VenvPython -m pip install --upgrade pip"
& $VenvPython -m pip install --upgrade pip

Write-InstallLog "Installing MVP package: $VenvPython -m pip install -e .[dev]"
& $VenvPython -m pip install -e ".[dev]"

if ($InstallOptionalFusion) {
    Write-InstallLog "Attempting optional pip fusion tools: freegs torax openfusiontoolkit"
    & $VenvPython -m pip install freegs torax openfusiontoolkit
    Write-InstallLog "Optional pip fusion install command completed."
} else {
    Write-InstallLog "Optional fusion pip packages skipped. Prefer WSL/conda path for heavy stack."
}

Write-InstallLog "Running stack verification."
& $VenvPython install\verify_stack.py
Pop-Location

